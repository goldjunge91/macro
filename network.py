import subprocess
import sys
import ctypes
import re
import psutil
import time
import os


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run_as_admin():
    if is_admin():
        return True
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    return False


def sanitize_interface_name(name):
    """
    Sanitize interface or profile name to prevent command injection.
    Only allows alphanumeric characters, spaces, hyphens, underscores, dots, and parentheses.
    Returns the sanitized name or raises ValueError if the name is invalid.
    """
    if not name or not isinstance(name, str):
        raise ValueError("Interface name must be a non-empty string")

    allowed_pattern = re.compile(r"^[a-zA-Z0-9\s\-_.()]+$")

    if not allowed_pattern.match(name):
        raise ValueError(f"Interface name contains invalid characters: {name}")

    return name


def test_internet_connectivity(timeout=1, interface_ip=None):
    """Test if internet is reachable via ping"""
    try:
        cmd = ["ping", "-n", "1", "-w", str(timeout * 1000)]

        if interface_ip:
            cmd.extend(["-S", interface_ip])

        cmd.append("8.8.8.8")

        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout + 1,
        )
        return result.returncode == 0
    except Exception:
        return False


def detect_interface_type(interface_name):
    """Detect if interface is WiFi or Ethernet based on name patterns"""
    name_lower = interface_name.lower()
    wifi_patterns = ["wi-fi", "wifi", "wlan", "wireless"]
    ethernet_patterns = ["ethernet", "eth", "local area connection", "lan"]

    for pattern in wifi_patterns:
        if pattern in name_lower:
            return "WiFi"
    for pattern in ethernet_patterns:
        if pattern in name_lower:
            return "Ethernet"

    try:
        res = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if res.returncode == 0 and interface_name in res.stdout:
            return "WiFi"
    except Exception:
        pass

    return "Unknown"


def get_active_network_interfaces():
    """Get list of active network interfaces with internet connectivity"""
    active_interfaces = []
    addrs = {}

    try:
        interfaces = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()

        for iface_name, stats in interfaces.items():
            if not stats.isup or "loopback" in iface_name.lower():
                continue

            if iface_name in addrs:
                has_ip = any(addr.family == 2 for addr in addrs[iface_name])
                if has_ip:
                    iface_type = detect_interface_type(iface_name)
                    active_interfaces.append({"name": iface_name, "type": iface_type})
    except Exception as e:
        print(f"!! ERROR detecting interfaces: {e}")

    connected_interfaces = []
    for iface in active_interfaces:
        if iface["name"] in addrs:
            ipv4_addr = None
            for addr in addrs[iface["name"]]:
                if addr.family == 2:
                    ipv4_addr = addr.address
                    break

            if ipv4_addr and test_internet_connectivity(
                timeout=1, interface_ip=ipv4_addr
            ):
                connected_interfaces.append(iface)

    return connected_interfaces


def auto_detect_interface():
    """Auto-detect and return the first active network interface"""
    try:
        active_interfaces = get_active_network_interfaces()
        if active_interfaces and len(active_interfaces) > 0:
            first_interface = active_interfaces[0]
            if (
                isinstance(first_interface, dict)
                and "name" in first_interface
                and "type" in first_interface
            ):
                return first_interface["name"], first_interface["type"]
    except Exception as e:
        print(f"!! ERROR in auto_detect_interface: {e}")

    return "WiFi", "WiFi"


def get_current_wifi_profile():
    try:
        res = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True
        )
        if res.returncode == 0:
            match = re.search(
                r"^\s*(?:Profile|Profil)\s*:\s*(.+)$",
                res.stdout,
                re.MULTILINE | re.IGNORECASE,
            )
            if match:
                return match.group(1).strip()
    except Exception:
        pass
    return None


def send_clumsy_hotkey(key_char):
    """Send a keyboard key press to trigger Clumsy"""
    from input_control import Input, Input_I, KeyBdInput, SendInput

    try:
        VkKeyScan = ctypes.windll.user32.VkKeyScanA
        result = VkKeyScan(ord(key_char))

        if result == -1:
            print(f"!! ERROR: Cannot map character '{key_char}' to virtual key")
            return False

        vk = result & 0xFF
        shift_state = (result >> 8) & 0xFF

        extra = ctypes.c_ulong(0)

        if shift_state & 1:
            ii_ = Input_I()
            ii_.ki = KeyBdInput(0x10, 0, 0, 0, ctypes.pointer(extra))
            SendInput(
                1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input)
            )
            time.sleep(0.02)

        ii_ = Input_I()
        ii_.ki = KeyBdInput(vk, 0, 0, 0, ctypes.pointer(extra))
        SendInput(
            1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input)
        )
        time.sleep(0.1)

        ii_.ki = KeyBdInput(vk, 0, 0x0002, 0, ctypes.pointer(extra))
        SendInput(
            1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input)
        )

        if shift_state & 1:
            time.sleep(0.02)
            ii_.ki = KeyBdInput(0x10, 0, 0x0002, 0, ctypes.pointer(extra))
            SendInput(
                1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input)
            )

        time.sleep(0.05)
        return True
    except Exception as e:
        print(f"!! ERROR sending Clumsy hotkey: {e}")
        return False


def disconnect_net(state, update_overlay):
    if state["is_lagging"]:
        return

    method = state["config"].get("network_method", "netsh")

    if method == "Clumsy":
        hotkey = state["config"].get("clumsy_hotkey", "[")
        print(f">> ACTIVATING CLUMSY (Hotkey: {hotkey})")
        state["is_lagging"] = True
        update_overlay()
        success = send_clumsy_hotkey(hotkey)
        if success:
            print(">> CLUMSY: Toggle-Signal send (should now be active)")
            time.sleep(0.15)
            return

    else:
        state["is_lagging"] = True
        iface = state["config"]["net_interface"]
        iface_type = state["config"].get("net_interface_type", "Unknown")

        try:
            iface = sanitize_interface_name(iface)
        except ValueError as e:
            print(f"!! ERROR: Invalid interface name: {e}")
            state["is_lagging"] = False
            return

        if iface_type == "WiFi":
            profile = get_current_wifi_profile()
            if profile:
                state["wifi_profile"] = profile

            print(f">> DISCONNECTING WiFi: {iface}")
            res = subprocess.run(
                ["netsh", "wlan", "disconnect", f"interface={iface}"],
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                print(f"!! ERROR: {res.stderr.strip() or res.stdout.strip()}")

        elif iface_type == "Ethernet":
            print(f">> DISABLING Ethernet: {iface}")
            res = subprocess.run(
                ["netsh", "interface", "set", "interface", iface, "disable"],
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                print(f"!! ERROR: {res.stderr.strip() or res.stdout.strip()}")

        else:
            print(f">> DISCONNECTING Unknown interface: {iface}")
            res = subprocess.run(
                ["netsh", "wlan", "disconnect", f"interface={iface}"],
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                subprocess.run(
                    ["netsh", "interface", "set", "interface", iface, "disable"],
                    capture_output=True,
                    text=True,
                )

    update_overlay()


def reconnect_net(state, update_overlay):
    if not state["is_lagging"]:
        print(">> WARNING: Not lagging, skipping reconnect")
        return

    method = state["config"].get("network_method", "netsh")

    if method == "Clumsy":
        hotkey = state["config"].get("clumsy_hotkey", "[")
        print(f">> DEACTIVATING CLUMSY (Hotkey: {hotkey})")
        time.sleep(0.1)
        success = send_clumsy_hotkey(hotkey)
        state["is_lagging"] = False
        update_overlay()
        if success:
            print(">> CLUMSY: Toggle-Signal gesendet (sollte jetzt inaktiv sein)")
        else:
            print("!! ERROR: Clumsy Hotkey konnte nicht gesendet werden")
    else:
        state["is_lagging"] = False
        iface = state["config"]["net_interface"]
        iface_type = state["config"].get("net_interface_type", "Unknown")

        try:
            iface = sanitize_interface_name(iface)
        except ValueError as e:
            print(f"!! ERROR: Invalid interface name: {e}")
            return

        if iface_type == "WiFi":
            prof = state.get("wifi_profile")
            print(f">> RECONNECTING WiFi: {iface}")

            if prof:
                try:
                    prof = sanitize_interface_name(prof)
                    subprocess.Popen(
                        [
                            "netsh",
                            "wlan",
                            "connect",
                            f"interface={iface}",
                            f"name={prof}",
                        ]
                    )
                except ValueError as e:
                    print(f"!! ERROR: Invalid profile name: {e}")
                    subprocess.Popen(["netsh", "wlan", "connect", f"interface={iface}"])
            else:
                subprocess.Popen(["netsh", "wlan", "connect", f"interface={iface}"])

        elif iface_type == "Ethernet":
            print(f">> RE-ENABLING Ethernet: {iface}")
            subprocess.Popen(
                ["netsh", "interface", "set", "interface", iface, "enable"]
            )

        else:
            prof = state.get("wifi_profile")
            print(f">> RECONNECTING Unknown interface: {iface}")

            if prof:
                try:
                    prof = sanitize_interface_name(prof)
                    subprocess.Popen(
                        [
                            "netsh",
                            "wlan",
                            "connect",
                            f"interface={iface}",
                            f"name={prof}",
                        ]
                    )
                except ValueError:
                    subprocess.Popen(
                        ["netsh", "interface", "set", "interface", iface, "enable"]
                    )
            else:
                subprocess.Popen(
                    ["netsh", "interface", "set", "interface", iface, "enable"]
                )

    update_overlay()


def start_clumsy(state):
    """
    Start Clumsy executable if not already running.
    Requires admin privileges. Returns True if started successfully.
    """
    try:
        if state.get("clumsy_process") is not None:
            # Überprüfe, ob der Prozess noch läuft
            if not is_clumsy_running(state):
                print(
                    "!! WARNING: Clumsy process exists but is not running, removing stale reference"
                )
                state["clumsy_process"] = None
            else:
                print(">> CLUMSY: Clumsy already running")
                return True

        clumsy_path = state["config"].get("clumsy_exe_path", "bin/clumsy.exe")

        # Versuche mehrere Pfade:
        # 1. Direkter Pfad (wenn absolut)
        # 2. Relativ zum aktuellen Arbeitsverzeichnis (für dist-Ordner)
        # 3. Relativ zu sys.argv[0] (Skript-Verzeichnis)

        candidates = []

        # Kandidat 1: Absoluter Pfad
        if os.path.isabs(clumsy_path):
            candidates.append(clumsy_path)
        else:
            # Kandidat 2: Relativ zum aktuellen Arbeitsverzeichnis
            candidates.append(os.path.join(os.getcwd(), clumsy_path))

            # Kandidat 3: Nur Dateiname (falls wir bereits im richtigen Verzeichnis sind)
            filename = os.path.basename(clumsy_path)
            candidates.append(os.path.join(os.getcwd(), filename))

            # Kandidat 4: Relativ zum Skript-Verzeichnis
            import sys

            if sys.argv:
                project_root = os.path.dirname(os.path.abspath(sys.argv[0]))
                candidates.append(os.path.join(project_root, clumsy_path))
                candidates.append(os.path.join(project_root, filename))

        # Finde die erste existierende Datei
        abs_path = None
        for candidate in candidates:
            if os.path.exists(candidate):
                abs_path = os.path.abspath(candidate)
                print(f">> CLUMSY: Found clumsy.exe at: {abs_path}")
                break

        if abs_path is None:
            print(f"!! ERROR: Clumsy executable not found")
            print(f"   Searched paths:")
            for i, candidate in enumerate(candidates, 1):
                print(f"   {i}. {candidate}")
            return False

        clumsy_dir = os.path.dirname(abs_path)

        print(f">> CLUMSY: Attempting to start: {abs_path}")

        # Starte Clumsy OHNE neue Konsole zunächst, um Fehler zu erfassen
        try:
            process = subprocess.Popen(
                [abs_path],
                cwd=clumsy_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception as e:
            print(f"!! ERROR: Failed to start process: {e}")
            return False

        # Warte kurz, um dem Prozess Zeit zum Starten zu geben
        time.sleep(0.5)

        # Überprüfe, ob der Prozess noch läuft
        exit_code = process.poll()
        if exit_code is not None:
            # Der Prozess ist bereits beendet
            stdout, stderr = process.communicate()
            print(
                f"!! ERROR: Clumsy process terminated immediately with exit code {exit_code}"
            )
            if stderr:
                print(f">> Error output: {stderr}")
            if stdout:
                print(f">> Output: {stdout}")
            print(">> Überprüfe:")
            print("   - config.txt und presets.ini im selben Ordner?")
            print("   - Sind iup.dll und WinDivert.dll im selben Ordner?")
            print("   - Ist der WinDivert-Treiber installiert?")
            print("   - Läufst du mit Admin-Rechten?")
            return False

        # Starte den Prozess neu mit GUI-Fenster im Hintergrund
        process.terminate()
        time.sleep(0.2)

        process = subprocess.Popen(
            [abs_path], cwd=clumsy_dir, creationflags=subprocess.CREATE_NEW_CONSOLE
        )

        state["clumsy_process"] = process
        print(f">> CLUMSY: Successfully started Clumsy (PID: {process.pid})")
        return True

    except Exception as e:
        print(f"!! ERROR: Failed to start Clumsy: {e}")
        return False


def stop_clumsy(state):
    """
    Stop the running Clumsy process if it exists.
    Returns True if stopped successfully.
    """
    try:
        if state.get("clumsy_process") is None:
            return True

        process = state["clumsy_process"]
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            print(f">> CLUMSY: Terminated Clumsy process (PID: {process.pid})")

        state["clumsy_process"] = None
        return True

    except Exception as e:
        print(f"!! ERROR: Failed to stop Clumsy: {e}")
        return False


def is_clumsy_running(state):
    """
    Check if Clumsy process is currently running.
    """
    try:
        if state.get("clumsy_process") is None:
            return False

        process = state["clumsy_process"]
        return process.poll() is None

    except Exception:
        return False
