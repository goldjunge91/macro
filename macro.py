import sys
import subprocess
import time
import threading
import json
import os
import ctypes
import re
import tkinter as tk
from tkinter import ttk, messagebox
import math


# --- DEPENDENCY CHECK ---
def check_dependencies():
    missing = []
    try:
        import pynput
    except ImportError:
        missing.append("pynput")
    try:
        import psutil
    except ImportError:
        missing.append("psutil")
    if missing:
        root = tk.Tk()
        root.withdraw()
        if messagebox.askyesno(
            "Missing Dependencies", f"Install {', '.join(missing)}?"
        ):
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            os.execv(sys.executable, [sys.executable] + sys.argv)
        sys.exit()


check_dependencies()
from pynput import keyboard
from pynput.mouse import Controller as MouseController, Button
import psutil

# --- CONFIGURATION ---
CONFIG_FILE = "macro_config.json"
DEFAULT_CONFIG = {
    "click_cps": 18,
    "key_macro_trigger": "Key.f3",
    "net_interface": "WiFi",
    "net_interface_type": "WiFi",
    "network_method": "Clumsy",
    "clumsy_hotkey": "8",
    "macro_disconnect_mode": "Before Click Start",
    "macro_hold_start": 0.0,
    "macro_hold_len": 1.0,
    "macro_net_start": 0.81,
    "macro_net_len": 2.5,
    "macro_spam_start": 0.74,
    "macro_spam_len": 3.0,
    "macro_enabled": True,
    "overlay_enabled": True,
    "overlay_x": -165,
    "overlay_y": 31,
    # Throw macro settings
    "key_throw_trigger": "Key.f4",
    "throw_e_dwell": 0.03,
    "throw_after_e_before_tab_delay": 0.05,
    "throw_tab_dwell": 0.03,
    "throw_after_tab_before_aim_delay": 0.05,
    "throw_aim_angle_deg": 70,
    "throw_aim_up_distance": 250,
    "throw_aim_horizontal_dir": 1,
    "throw_doubleclick_hold": 0.022,
    "throw_doubleclick_gap": 0.055,
    "throw_bracket_offset": 1.61,
    "throw_phase1_total": 2.01,
    "throw_enabled": True,
}

state = {
    "is_lagging": False,
    "is_running_macro": False,
    "wifi_profile": None,
    "overlay_ref": None,
    "config": DEFAULT_CONFIG.copy(),
}

mouse = MouseController()


# --- SYSTEM FUNCTIONS ---
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
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

    # Allow only safe characters: alphanumeric, space, hyphen, underscore, dot, and parentheses
    # This covers most legitimate Windows interface names while preventing injection
    allowed_pattern = re.compile(r"^[a-zA-Z0-9\s\-_.()]+$")

    if not allowed_pattern.match(name):
        raise ValueError(f"Interface name contains invalid characters: {name}")

    return name


def test_internet_connectivity(timeout=1, interface_ip=None):
    """Test if internet is reachable via ping"""
    try:
        cmd = ["ping", "-n", "1", "-w", str(timeout * 1000)]

        # If interface IP is provided, bind to that source address
        if interface_ip:
            cmd.extend(["-S", interface_ip])

        cmd.append("8.8.8.8")

        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout + 1,
        )
        return result.returncode == 0
    except:
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

    # Additional check using netsh for WiFi
    try:
        res = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if res.returncode == 0 and interface_name in res.stdout:
            return "WiFi"
    except:
        pass

    return "Unknown"


def get_active_network_interfaces():
    """Get list of active network interfaces with internet connectivity"""
    active_interfaces = []
    addrs = {}  # Initialize outside try block

    try:
        # Get all network interfaces using psutil
        interfaces = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()

        for iface_name, stats in interfaces.items():
            # Skip interfaces that are down or loopback
            if not stats.isup or "loopback" in iface_name.lower():
                continue

            # Check if interface has a valid IP address
            if iface_name in addrs:
                has_ip = any(
                    addr.family == 2 for addr in addrs[iface_name]  # AF_INET (IPv4)
                )
                if has_ip:
                    iface_type = detect_interface_type(iface_name)
                    active_interfaces.append({"name": iface_name, "type": iface_type})
    except Exception as e:
        print(f"!! ERROR detecting interfaces: {e}")

    # Filter to only interfaces with internet connectivity
    connected_interfaces = []
    for iface in active_interfaces:
        # Get the IPv4 address for this interface
        if iface["name"] in addrs:
            ipv4_addr = None
            for addr in addrs[iface["name"]]:
                if addr.family == 2:  # AF_INET (IPv4)
                    ipv4_addr = addr.address
                    break

            # Test connectivity through this specific interface
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
            # Validate that the interface has the expected keys
            first_interface = active_interfaces[0]
            if (
                isinstance(first_interface, dict)
                and "name" in first_interface
                and "type" in first_interface
            ):
                return first_interface["name"], first_interface["type"]
    except Exception as e:
        print(f"!! ERROR in auto_detect_interface: {e}")

    # Fallback to WiFi if no interfaces detected or error occurred
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
    except:
        pass
    return None


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                state["config"].update(json.load(f))
        except:
            pass

    if state["config"]["net_interface"] == "Auto-Detect":
        # Auto-detect: use first active interface
        interface_name, interface_type = auto_detect_interface()
        state["config"]["net_interface"] = interface_name
        state["config"]["net_interface_type"] = interface_type


def save_config():
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(state["config"], f, indent=4)
    except:
        pass


def send_clumsy_hotkey(key_char):
    """Send a keyboard key press to trigger Clumsy"""
    try:
        # Use VkKeyScan to get the correct VK code for current keyboard layout
        VkKeyScan = ctypes.windll.user32.VkKeyScanA
        result = VkKeyScan(ord(key_char))

        if result == -1:
            print(f"!! ERROR: Cannot map character '{key_char}' to virtual key")
            return False

        vk = result & 0xFF
        shift_state = (result >> 8) & 0xFF

        extra = ctypes.c_ulong(0)

        # Press shift if needed
        if shift_state & 1:  # Shift required
            ii_ = Input_I()
            ii_.ki = KeyBdInput(0x10, 0, 0, 0, ctypes.pointer(extra))  # VK_SHIFT down
            SendInput(
                1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input)
            )
            time.sleep(0.02)

        # Key down
        ii_ = Input_I()
        ii_.ki = KeyBdInput(vk, 0, 0, 0, ctypes.pointer(extra))
        SendInput(
            1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input)
        )
        time.sleep(0.1)  # Länger halten für zuverlässige Erkennung

        # Key up
        ii_.ki = KeyBdInput(vk, 0, 0x0002, 0, ctypes.pointer(extra))  # KEYEVENTF_KEYUP
        SendInput(
            1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input)
        )

        # Release shift if needed
        if shift_state & 1:
            time.sleep(0.02)
            ii_.ki = KeyBdInput(
                0x10, 0, 0x0002, 0, ctypes.pointer(extra)
            )  # VK_SHIFT up
            SendInput(
                1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input)
            )

        time.sleep(0.05)  # Kurze Pause nach dem Senden
        return True
    except Exception as e:
        print(f"!! ERROR sending Clumsy hotkey: {e}")
        return False


# --- NET LOGIC ---
def disconnect_net():
    if state["is_lagging"]:
        # print(">> WARNING: Already lagging, skipping disconnect")
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

        # Sanitize the interface name to prevent command injection
        try:
            iface = sanitize_interface_name(iface)
        except ValueError as e:
            print(f"!! ERROR: Invalid interface name: {e}")
            state["is_lagging"] = False
            return

        if iface_type == "WiFi":
            # Store WiFi profile for reconnection
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
            # Unknown type, try WiFi first, then Ethernet
            print(f">> DISCONNECTING Unknown interface: {iface}")
            res = subprocess.run(
                ["netsh", "wlan", "disconnect", f"interface={iface}"],
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                # Try Ethernet method
                subprocess.run(
                    ["netsh", "interface", "set", "interface", iface, "disable"],
                    capture_output=True,
                    text=True,
                )

    update_overlay()


def reconnect_net():
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

        # Sanitize the interface name to prevent command injection
        try:
            iface = sanitize_interface_name(iface)
        except ValueError as e:
            print(f"!! ERROR: Invalid interface name: {e}")
            return

        if iface_type == "WiFi":
            prof = state.get("wifi_profile")
            print(f">> RECONNECTING WiFi: {iface}")

            if prof:
                # Sanitize the profile name as well
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
                    # Fall back to connecting without profile name
                    subprocess.Popen(["netsh", "wlan", "connect", f"interface={iface}"])
            else:
                subprocess.Popen(["netsh", "wlan", "connect", f"interface={iface}"])

        elif iface_type == "Ethernet":
            print(f">> RE-ENABLING Ethernet: {iface}")
            subprocess.Popen(
                ["netsh", "interface", "set", "interface", iface, "enable"]
            )

        else:
            # Unknown type, try WiFi first
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
                    # Fall back to enabling interface
                    subprocess.Popen(
                        ["netsh", "interface", "set", "interface", iface, "enable"]
                    )
            else:
                subprocess.Popen(
                    ["netsh", "interface", "set", "interface", iface, "enable"]
                )

    update_overlay()


# --- INPUT DRIVER ---
SendInput = ctypes.windll.user32.SendInput
PUL = ctypes.POINTER(ctypes.c_ulong)


class KeyBdInput(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL),
    ]


class HardwareInput(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_ushort),
        ("wParamH", ctypes.c_ushort),
    ]


class MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL),
    ]


class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]


class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]


def click_mouse_fast():
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, 0, 0x0002, 0, ctypes.pointer(extra))  # Down
    SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))

    # Robust hold time (20ms - 40ms)
    time.sleep(0.02 + (time.time() % 0.02))

    ii_.mi = MouseInput(0, 0, 0, 0x0004, 0, ctypes.pointer(extra))  # Up
    SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))


# === THROW MACRO FUNCTIONS ===
def tap_e(dwell=0.03):
    """Tap E key"""
    keyboard.press(keyboard.KeyCode.from_char("e"))
    time.sleep(dwell)
    keyboard.release(keyboard.KeyCode.from_char("e"))


def tap_tab(dwell=0.03):
    """Tap Tab key"""
    keyboard.press(keyboard.Key.tab)
    time.sleep(dwell)
    keyboard.release(keyboard.Key.tab)


def move_mouse_up_angle(distance, angle_deg=70, horizontal_dir=1, smooth_steps=30):
    """Move mouse at angle"""
    angle_rad = math.radians(angle_deg)
    dx = horizontal_dir * distance * math.cos(angle_rad)
    dy = -distance * math.sin(angle_rad)

    start_x, start_y = mouse.position
    for i in range(smooth_steps + 1):
        t = i / smooth_steps
        x = start_x + dx * t
        y = start_y + dy * t
        mouse.position = (int(x), int(y))
        time.sleep(0.001)


def double_click_left(hold_time=0.022, gap=0.055):
    """Double click left mouse button"""
    mouse.press(Button.left)
    time.sleep(hold_time)
    mouse.release(Button.left)
    time.sleep(gap)
    mouse.press(Button.left)
    time.sleep(hold_time)
    mouse.release(Button.left)


def tap_bracket(dwell=0.006):
    """Tap bracket key"""
    keyboard.press(keyboard.KeyCode.from_vk(219))  # '['
    time.sleep(dwell)
    keyboard.release(keyboard.KeyCode.from_vk(219))


def shift_alt_click_once(shift_dwell=0.018, alt_dwell=0.006):
    """Perform Shift+Alt+Click"""
    keyboard.press(keyboard.Key.shift)
    time.sleep(shift_dwell)
    keyboard.press(keyboard.Key.alt)
    time.sleep(alt_dwell)
    mouse.press(Button.left)
    time.sleep(0.02)
    mouse.release(Button.left)
    keyboard.release(keyboard.Key.alt)
    keyboard.release(keyboard.Key.shift)


def run_throw_macro():
    if not state["config"].get("throw_enabled", True):
        return
    print(">> THROW MACRO: STARTING")
    start_time = time.time()

    c = state["config"]
    # Phase 1: E + Tab + Aim
    tap_e(c.get("throw_e_dwell", 0.03))
    time.sleep(c.get("throw_after_e_before_tab_delay", 0.05))
    tap_tab(c.get("throw_tab_dwell", 0.03))
    time.sleep(c.get("throw_after_tab_before_aim_delay", 0.05))
    move_mouse_up_angle(
        c.get("throw_aim_up_distance", 250),
        c.get("throw_aim_angle_deg", 70),
        c.get("throw_aim_horizontal_dir", 1),
    )

    # Phase 2: Double Click
    double_click_left(
        c.get("throw_doubleclick_hold", 0.022), c.get("throw_doubleclick_gap", 0.055)
    )

    # Phase 3: Bracket
    elapsed = time.time() - start_time
    bracket_offset = c.get("throw_bracket_offset", 1.61)
    if bracket_offset > elapsed:
        time.sleep(bracket_offset - elapsed)
    tap_bracket()

    # Phase 4: Shift+Alt+Click
    elapsed = time.time() - start_time
    phase1_total = c.get("throw_phase1_total", 2.01)
    if phase1_total > elapsed:
        time.sleep(phase1_total - elapsed)
    shift_alt_click_once()

    print(f">> THROW MACRO: COMPLETE ({time.time() - start_time:.3f}s)")


# --- MACRO ENGINE ---
def run_complex_macro():
    if state["is_running_macro"]:
        return
    state["is_running_macro"] = True
    print(">> MACRO: STARTING TIMELINE")
    update_overlay()

    c = state["config"]
    mode = c.get("macro_disconnect_mode", "Before Click Start")

    hold_start = float(c.get("macro_hold_start"))
    hold_len = float(c.get("macro_hold_len"))
    net_start = float(c.get("macro_net_start"))
    net_len = float(c.get("macro_net_len"))
    spam_start = float(c.get("macro_spam_start"))
    spam_len = float(c.get("macro_spam_len"))
    cps = int(c.get("click_cps"))

    # Task: Hold Click
    def task_hold():
        if hold_len <= 0:
            return

        # In timeline mode, we respect the user's start times.
        # But if "Before Click Start" is selected, we might want to ensure connection is cut.
        # However, for pure flexibility, we just follow the timeline values entered.

        time.sleep(hold_start)
        print(">> HOLD: DOWN")
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.mi = MouseInput(0, 0, 0, 0x0002, 0, ctypes.pointer(extra))
        SendInput(
            1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input)
        )
        time.sleep(hold_len)
        print(">> HOLD: RELEASE")
        ii_.mi = MouseInput(0, 0, 0, 0x0004, 0, ctypes.pointer(extra))
        SendInput(
            1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input)
        )

    # Task: Network
    def task_net():
        if net_len <= 0:
            return
        time.sleep(net_start)
        disconnect_net()
        time.sleep(net_len)
        reconnect_net()

    # Task: Spam
    def task_spam():
        if spam_len <= 0:
            return
        time.sleep(spam_start)
        print(">> SPAM: START")
        end_t = time.time() + spam_len
        interval = 1.0 / cps
        while time.time() < end_t:
            click_mouse_fast()
            time.sleep(max(0, interval - 0.03))
        print(">> SPAM: END")

    # Execute
    t1 = threading.Thread(target=task_hold)
    t2 = threading.Thread(target=task_net)
    t3 = threading.Thread(target=task_spam)
    t1.start()
    t2.start()
    t3.start()

    # Waiter
    def waiter():
        t1.join()
        t2.join()
        t3.join()
        state["is_running_macro"] = False
        print(">> MACRO: FINISHED")
        update_overlay()

    threading.Thread(target=waiter).start()


def parse_key_string(k_str):
    if k_str.startswith("Key."):
        attr = k_str.split(".")[1]
        return getattr(keyboard.Key, attr, None)
    return k_str


def on_key_press(key):
    try:
        if not state["config"].get("macro_enabled", True):
            return
        target = parse_key_string(state["config"].get("key_macro_trigger", "Key.f3"))
        if key == target or (hasattr(key, "char") and key.char == target):
            threading.Thread(target=run_complex_macro).start()

        # Throw macro trigger
        throw_target = parse_key_string(
            state["config"].get("key_throw_trigger", "Key.f4")
        )
        if key == throw_target or (hasattr(key, "char") and key.char == throw_target):
            threading.Thread(target=run_throw_macro).start()
    except:
        pass


# --- UI ---
THEME = {
    "bg": "#0a0a0a",
    "fg": "#00ff41",
    "warning": "#ff3333",
    "font_main": ("Consolas", 10),
    "font_header": ("Consolas", 14, "bold"),
    "font_mono": ("Consolas", 9),
}


class HackerButton(tk.Button):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            bg="black",
            fg=THEME["fg"],
            activebackground=THEME["fg"],
            activeforeground="black",
            font=THEME["font_main"],
            bd=1,
            relief="solid",
        )


class Overlay(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True, "-alpha", 0.85)
        self.config(bg="black")
        self.lbl_status = tk.Label(
            self,
            text="NET: ONLINE",
            font=("Consolas", 10, "bold"),
            bg="black",
            fg=THEME["fg"],
        )
        self.lbl_status.pack(anchor="w")
        self.lbl_macro = tk.Label(
            self,
            text="",
            font=("Consolas", 10, "bold"),
            bg="black",
            fg=THEME["warning"],
        )
        self.lbl_macro.pack(anchor="w")
        self.geometry(
            f"150x50+{state['config']['overlay_x']}+{state['config']['overlay_y']}"
        )
        self.bind("<Button-1>", self.start_move)
        self.bind("<B1-Motion>", self.do_move)
        self.bind("<ButtonRelease-1>", self.stop_move)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        x = self.winfo_x() + (event.x - self.x)
        y = self.winfo_y() + (event.y - self.y)
        self.geometry(f"+{x}+{y}")

    def stop_move(self, event):
        state["config"]["overlay_x"] = self.winfo_x()
        state["config"]["overlay_y"] = self.winfo_y()
        save_config()


def update_overlay():
    if not state["overlay_ref"] or not state["overlay_ref"].winfo_exists():
        return
    ov = state["overlay_ref"]
    if state["config"]["overlay_enabled"]:
        ov.deiconify()
        ov.lbl_status.config(
            text="NET: OFFLINE" if state["is_lagging"] else "NET: ONLINE",
            fg=THEME["warning"] if state["is_lagging"] else THEME["fg"],
        )
        macro_text = (
            "MACRO: RUNNING"
            if state["is_running_macro"]
            else (
                "MACRO: OFF" if not state["config"].get("macro_enabled", True) else ""
            )
        )
        ov.lbl_macro.config(
            text=macro_text,
            fg="#888" if macro_text == "MACRO: OFF" else THEME["warning"],
        )
    else:
        ov.withdraw()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MACRO CONTROLLER")
        self.geometry("380x950")
        self.configure(bg=THEME["bg"])
        self.attributes("-topmost", True)

        tk.Label(
            self,
            text="[ TIMELINE MACRO ]",
            font=THEME["font_header"],
            bg=THEME["bg"],
            fg=THEME["fg"],
        ).pack(pady=(20, 0))

        self.frame = tk.Frame(self, bg=THEME["bg"])
        self.frame.pack(fill="both", expand=True, padx=20)
        self.build_ui()
        state["overlay_ref"] = Overlay(self)
        update_overlay()

    def build_ui(self):
        keys = (
            [chr(i) for i in range(97, 123)]
            + [str(i) for i in range(10)]
            + [f"Key.f{i}" for i in range(1, 13)]
        )
        clumsy_keys = [chr(i) for i in range(97, 123)] + [str(i) for i in range(10)]

        def add_section(txt):
            tk.Label(
                self.frame,
                text=txt,
                bg=THEME["bg"],
                fg="#888",
                font=("Consolas", 9, "bold"),
            ).pack(anchor="w", pady=(10, 2))

        def add_entry(txt, key):
            f = tk.Frame(self.frame, bg=THEME["bg"])
            f.pack(fill="x", pady=2)
            tk.Label(
                f, text=txt, bg=THEME["bg"], fg="white", width=18, anchor="w"
            ).pack(side="left")
            e = tk.Entry(f, bg="#222", fg="white", font=THEME["font_mono"])
            e.insert(0, str(state["config"].get(key, "")))
            e.pack(side="left", fill="x", expand=True)
            return e

        # Global Settings
        tk.Label(
            self.frame,
            text="NETWORK METHOD:",
            bg=THEME["bg"],
            fg=THEME["fg"],
            font=THEME["font_mono"],
        ).pack(anchor="w")
        self.cb_net_method = ttk.Combobox(
            self.frame, values=["netsh", "Clumsy"], font=THEME["font_mono"]
        )
        self.cb_net_method.set(state["config"].get("network_method", "netsh"))
        self.cb_net_method.pack(fill="x", pady=2)
        self.cb_net_method.bind("<<ComboboxSelected>>", self.on_method_change)

        # Create frames for conditional display
        self.frame_netsh = tk.Frame(self.frame, bg=THEME["bg"])
        self.frame_clumsy = tk.Frame(self.frame, bg=THEME["bg"])

        # Netsh Interface Selection
        self.lbl_iface = tk.Label(
            self.frame_netsh,
            text="NETWORK INTERFACE:",
            bg=THEME["bg"],
            fg=THEME["fg"],
            font=THEME["font_mono"],
        )
        self.lbl_iface.pack(anchor="w")

        # Detect active interfaces
        active_interfaces = get_active_network_interfaces()
        interface_values = []
        for iface in active_interfaces:
            interface_values.append(f"{iface['name']} ({iface['type']})")

        if not interface_values:
            interface_values = ["No active interfaces detected"]

        self.cb_iface = ttk.Combobox(
            self.frame_netsh,
            values=interface_values,
            font=THEME["font_mono"],
            state="readonly",
        )

        # Set current value or default
        current_iface = state["config"].get("net_interface", "")
        current_type = state["config"].get("net_interface_type", "Unknown")

        # Try to find a matching interface in the detected list
        selected = False
        if current_iface:
            for iface_display in interface_values:
                # Check if the interface name matches (handle both formats)
                if current_iface in iface_display:
                    self.cb_iface.set(iface_display)
                    selected = True
                    break

        # If not found, use first available or fallback
        if not selected:
            if (
                interface_values
                and interface_values[0] != "No active interfaces detected"
            ):
                self.cb_iface.set(interface_values[0])
            elif current_iface:
                # Fallback to stored value even if not detected
                self.cb_iface.set(f"{current_iface} ({current_type})")

        self.cb_iface.pack(fill="x", pady=2)

        # Add refresh button
        self.btn_refresh = HackerButton(
            self.frame_netsh,
            text="REFRESH INTERFACES",
            command=self.refresh_interfaces,
            bg="#003333",
        )
        self.btn_refresh.pack(fill="x", pady=2)

        # Clumsy Hotkey
        self.lbl_clumsy = tk.Label(
            self.frame_clumsy,
            text="CLUMSY HOTKEY:",
            bg=THEME["bg"],
            fg=THEME["fg"],
            font=THEME["font_mono"],
        )
        self.lbl_clumsy.pack(anchor="w")
        self.cb_clumsy_key = ttk.Combobox(
            self.frame_clumsy, values=clumsy_keys, font=THEME["font_mono"]
        )
        self.cb_clumsy_key.set(state["config"].get("clumsy_hotkey", "8"))
        self.cb_clumsy_key.pack(fill="x", pady=2)

        # Show appropriate frame based on method
        self.update_method_display()

        tk.Label(
            self.frame,
            text="TRIGGER KEY:",
            bg=THEME["bg"],
            fg=THEME["fg"],
            font=THEME["font_mono"],
        ).pack(anchor="w", pady=(10, 0))
        self.cb_trig = ttk.Combobox(self.frame, values=keys, font=THEME["font_mono"])
        self.cb_trig.set(state["config"]["key_macro_trigger"])
        self.cb_trig.pack(fill="x", pady=2)

        tk.Label(
            self.frame,
            text="DISCONNECT TIMING:",
            bg=THEME["bg"],
            fg=THEME["fg"],
            font=THEME["font_mono"],
        ).pack(anchor="w", pady=(10, 0))
        self.cb_disc_mode = ttk.Combobox(
            self.frame,
            values=["After Click Start", "Before Click Start"],
            font=THEME["font_mono"],
        )
        self.cb_disc_mode.set(
            state["config"].get("macro_disconnect_mode", "Before Click Start")
        )
        self.cb_disc_mode.pack(fill="x", pady=2)

        tk.Label(
            self.frame,
            text="CLICKS PER SECOND (CPS):",
            bg=THEME["bg"],
            fg=THEME["fg"],
            font=THEME["font_mono"],
        ).pack(anchor="w", pady=(10, 0))
        self.s_cps = tk.Scale(
            self.frame,
            from_=1,
            to=30,
            orient="horizontal",
            bg=THEME["bg"],
            fg="white",
            highlightthickness=0,
            troughcolor="#222",
        )
        self.s_cps.set(state["config"]["click_cps"])
        self.s_cps.pack(fill="x")

        # Timeline
        add_section("--- 1. HOLD CLICK ---")
        self.e_h_st = add_entry("Start Delay (s):", "macro_hold_start")
        self.e_h_ln = add_entry("Duration (s):", "macro_hold_len")

        add_section("--- 2. NETWORK ---")
        self.e_n_st = add_entry("Start Delay (s):", "macro_net_start")
        self.e_n_ln = add_entry("Offline Time (s):", "macro_net_len")

        add_section("--- 3. SPAM CLICK ---")
        self.e_s_st = add_entry("Start Delay (s):", "macro_spam_start")
        self.e_s_ln = add_entry("Duration (s):", "macro_spam_len")

        add_section("--- THROW MACRO SETTINGS ---")
        self.cb_throw_trig = ttk.Combobox(
            self.frame, values=keys, font=THEME["font_mono"]
        )
        self.cb_throw_trig.set(state["config"]["key_throw_trigger"])
        tk.Label(
            self.frame,
            text="THROW TRIGGER KEY:",
            bg=THEME["bg"],
            fg=THEME["fg"],
            font=THEME["font_mono"],
        ).pack(anchor="w", pady=(10, 0))
        self.cb_throw_trig.pack(fill="x", pady=2)

        self.e_throw_e_dwell = add_entry("E Dwell (s):", "throw_e_dwell")
        self.e_throw_after_e_tab = add_entry(
            "After E to Tab (s):", "throw_after_e_before_tab_delay"
        )
        self.e_throw_tab_dwell = add_entry("Tab Dwell (s):", "throw_tab_dwell")
        self.e_throw_after_tab_aim = add_entry(
            "After Tab to Aim (s):", "throw_after_tab_before_aim_delay"
        )
        self.e_throw_aim_angle = add_entry("Aim Angle (deg):", "throw_aim_angle_deg")
        self.e_throw_aim_dist = add_entry("Aim Distance:", "throw_aim_up_distance")
        self.e_throw_aim_dir = add_entry("Aim Direction:", "throw_aim_horizontal_dir")
        self.e_throw_dc_hold = add_entry(
            "Double Click Hold (s):", "throw_doubleclick_hold"
        )
        self.e_throw_dc_gap = add_entry(
            "Double Click Gap (s):", "throw_doubleclick_gap"
        )
        self.e_throw_bracket_offset = add_entry(
            "Bracket Offset (s):", "throw_bracket_offset"
        )
        self.e_throw_phase1_total = add_entry(
            "Phase 1 Total (s):", "throw_phase1_total"
        )

        # Buttons
        f_btn = tk.Frame(self.frame, bg=THEME["bg"])
        f_btn.pack(fill="x", pady=20)
        self.btn_macro = HackerButton(
            f_btn, text="DISABLE MACRO", command=self.toggle_macro, bg="#003300"
        )
        self.btn_macro.pack(fill="x", pady=2)
        self.btn_throw = HackerButton(
            f_btn, text="DISABLE THROW", command=self.toggle_throw, bg="#003300"
        )
        self.btn_throw.pack(fill="x", pady=2)
        HackerButton(f_btn, text="SAVE SETTINGS", command=self.save).pack(
            fill="x", pady=2
        )
        self.btn_ov = HackerButton(
            f_btn, text="DISABLE OVERLAY", command=self.toggle_ov
        )
        self.btn_ov.pack(fill="x", pady=2)
        HackerButton(
            f_btn,
            text="RELOAD TOOL",
            command=lambda: os.execv(sys.executable, [sys.executable] + sys.argv),
            bg="#330000",
        ).pack(fill="x", pady=2)

    def save(self):
        c = state["config"]
        c["key_macro_trigger"] = self.cb_trig.get()
        c["macro_disconnect_mode"] = self.cb_disc_mode.get()
        c["click_cps"] = self.s_cps.get()
        c["network_method"] = self.cb_net_method.get()
        c["clumsy_hotkey"] = self.cb_clumsy_key.get()

        # Parse interface selection from dropdown
        iface_selection = self.cb_iface.get()
        if iface_selection and iface_selection != "No active interfaces detected":
            # Extract interface name and type from "Name (Type)" format
            match = re.match(r"^(.+?)\s*\((.+?)\)$", iface_selection)
            if match:
                c["net_interface"] = match.group(1).strip()
                c["net_interface_type"] = match.group(2).strip()
            else:
                c["net_interface"] = iface_selection
                c["net_interface_type"] = "Unknown"

        try:
            c["macro_hold_start"] = float(self.e_h_st.get())
            c["macro_hold_len"] = float(self.e_h_ln.get())
            c["macro_net_start"] = float(self.e_n_st.get())
            c["macro_net_len"] = float(self.e_n_ln.get())
            c["macro_spam_start"] = float(self.e_s_st.get())
            c["macro_spam_len"] = float(self.e_s_ln.get())

            # Throw settings
            c["key_throw_trigger"] = self.cb_throw_trig.get()
            c["throw_e_dwell"] = float(self.e_throw_e_dwell.get())
            c["throw_after_e_before_tab_delay"] = float(self.e_throw_after_e_tab.get())
            c["throw_tab_dwell"] = float(self.e_throw_tab_dwell.get())
            c["throw_after_tab_before_aim_delay"] = float(
                self.e_throw_after_tab_aim.get()
            )
            c["throw_aim_angle_deg"] = float(self.e_throw_aim_angle.get())
            c["throw_aim_up_distance"] = float(self.e_throw_aim_dist.get())
            c["throw_aim_horizontal_dir"] = float(self.e_throw_aim_dir.get())
            c["throw_doubleclick_hold"] = float(self.e_throw_dc_hold.get())
            c["throw_doubleclick_gap"] = float(self.e_throw_dc_gap.get())
            c["throw_bracket_offset"] = float(self.e_throw_bracket_offset.get())
            c["throw_phase1_total"] = float(self.e_throw_phase1_total.get())
        except:
            pass
        save_config()
        messagebox.showinfo("Saved", "Settings Updated!")

    def refresh_interfaces(self):
        """Refresh the list of active network interfaces"""
        active_interfaces = get_active_network_interfaces()
        interface_values = []
        for iface in active_interfaces:
            interface_values.append(f"{iface['name']} ({iface['type']})")

        if not interface_values:
            interface_values = ["No active interfaces detected"]

        self.cb_iface["values"] = interface_values
        if interface_values and interface_values[0] != "No active interfaces detected":
            self.cb_iface.set(interface_values[0])

        messagebox.showinfo(
            "Refresh", f"Found {len(active_interfaces)} active interface(s)"
        )

    def update_method_display(self):
        """Show/hide interface or clumsy settings based on selected method"""
        method = self.cb_net_method.get()

        # Hide both frames first
        self.frame_netsh.pack_forget()
        self.frame_clumsy.pack_forget()

        # Show appropriate frame right after the network method dropdown
        if method == "Clumsy":
            self.frame_clumsy.pack(after=self.cb_net_method, fill="x", pady=2)
        else:  # netsh
            self.frame_netsh.pack(after=self.cb_net_method, fill="x", pady=2)

    def on_method_change(self, event=None):
        """Handle network method change"""
        self.update_method_display()

    def toggle_macro(self):
        state["config"]["macro_enabled"] = not state["config"].get(
            "macro_enabled", True
        )
        enabled = state["config"]["macro_enabled"]
        self.btn_macro.config(
            text="DISABLE MACRO" if enabled else "ENABLE MACRO",
            bg="#003300" if enabled else "#330000",
        )
        update_overlay()
        save_config()

    def toggle_throw(self):
        state["config"]["throw_enabled"] = not state["config"].get(
            "throw_enabled", True
        )
        enabled = state["config"]["throw_enabled"]
        self.btn_throw.config(
            text="DISABLE THROW" if enabled else "ENABLE THROW",
            bg="#003300" if enabled else "#330000",
        )
        save_config()

    def toggle_ov(self):
        state["config"]["overlay_enabled"] = not state["config"]["overlay_enabled"]
        self.btn_ov.config(
            text=(
                "DISABLE OVERLAY"
                if state["config"]["overlay_enabled"]
                else "ENABLE OVERLAY"
            )
        )
        update_overlay()
        save_config()


if __name__ == "__main__":
    if not run_as_admin():
        sys.exit(0)
    load_config()  # Load before interface detection to see if we have a saved name
    if state["config"]["net_interface"] == "Auto-Detect":
        # Auto-detect: use first active interface
        interface_name, interface_type = auto_detect_interface()
        state["config"]["net_interface"] = interface_name
        state["config"]["net_interface_type"] = interface_type

    keyboard.Listener(on_press=on_key_press).start()
    App().mainloop()
