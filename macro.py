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

# --- DEPENDENCY CHECK ---
def check_dependencies():
    missing = []
    try: import pynput
    except ImportError: missing.append("pynput")
    if missing:
        root = tk.Tk(); root.withdraw()
        if messagebox.askyesno("Missing Dependencies", f"Install {', '.join(missing)}?"):
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            os.execv(sys.executable, [sys.executable] + sys.argv)
        sys.exit()

check_dependencies()
from pynput import keyboard

# --- CONFIGURATION ---
CONFIG_FILE = "macro_config.json"
DEFAULT_CONFIG = {
    "click_cps": 22.88,
    "key_macro_trigger": "Key.f3",
    "net_interface": "Auto-Detect",
    "network_method": "netsh",
    "clumsy_hotkey": "[",
    "macro_disconnect_mode": "Before Click Start",
    "macro_hold_start": 0.0,
    "macro_hold_len": 0.9,
    "macro_net_start": 0.0,
    "macro_net_len": 2.01,
    "macro_spam_start": 2.01,
    "macro_spam_len": 1.85,
    "macro_bracket_offset": 1.61,
    "macro_bracket_hold": 0.004,
    "macro_click_hold": 0.03,
    "overlay_enabled": True,
    "overlay_x": 20,
    "overlay_y": 20
}

state = {
    "is_lagging": False,
    "is_running_macro": False,
    "wifi_profile": None,
    "overlay_ref": None,
    "config": DEFAULT_CONFIG.copy()
}

# --- SYSTEM FUNCTIONS ---
def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

def run_as_admin():
    if is_admin(): return True
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    return False

def detect_wifi_interface():
    try:
        res = subprocess.run('netsh wlan show interfaces', shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            match = re.search(r'^\s*Name\s*:\s*(.+)$', res.stdout, re.MULTILINE)
            if match: return match.group(1).strip()
    except: pass
    return "WiFi"

def get_current_wifi_profile():
    try:
        res = subprocess.run('netsh wlan show interfaces', shell=True, capture_output=True, text=True)
        if res.returncode == 0:
            match = re.search(r'^\s*(?:Profile|Profil)\s*:\s*(.+)$', res.stdout, re.MULTILINE | re.IGNORECASE)
            if match: return match.group(1).strip()
    except: pass
    return None

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                state["config"].update(json.load(f))
        except: pass
    
    if state["config"]["net_interface"] == "Auto-Detect":
        state["config"]["net_interface"] = detect_wifi_interface()

def save_config():
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(state["config"], f, indent=4)
    except: pass

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
            SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input))
            time.sleep(0.02)
        
        # Key down
        ii_ = Input_I()
        ii_.ki = KeyBdInput(vk, 0, 0, 0, ctypes.pointer(extra))
        SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input))
        time.sleep(0.1)  # Länger halten für zuverlässige Erkennung
        
        # Key up
        ii_.ki = KeyBdInput(vk, 0, 0x0002, 0, ctypes.pointer(extra))  # KEYEVENTF_KEYUP
        SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input))
        
        # Release shift if needed
        if shift_state & 1:
            time.sleep(0.02)
            ii_.ki = KeyBdInput(0x10, 0, 0x0002, 0, ctypes.pointer(extra))  # VK_SHIFT up
            SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input))
        
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
        hotkey  = state["config"].get("clumsy_hotkey", "[")
        print(f">> ACTIVATING CLUMSY (Hotkey: {hotkey})")
        success = send_clumsy_hotkey(hotkey)
        if success:
            state["is_lagging"] = True
            print(">> CLUMSY: Toggle-Signal send (should now be active)")
            return

    else:
        state["is_lagging"] = True
        iface = state["config"]["net_interface"]
        profile = get_current_wifi_profile()
        if profile: state["wifi_profile"] = profile
    
        print(f">> KILLING NETWORK: {iface}")
        res = subprocess.run(f'netsh wlan disconnect interface="{iface}"', shell=True, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"!! ERROR: {res.stderr.strip() or res.stdout.strip()}")

    update_overlay()

def reconnect_net():
    if not state["is_lagging"]:
        print(">> WARNING: Not lagging, skipping reconnect")
        return

    method = state["config"].get("network_method", "netsh")
    
    if method == "Clumsy":
        hotkey = state["config"].get("clumsy_hotkey", "[")
        print(f">> DEACTIVATING CLUMSY (Hotkey: {hotkey})")
        time.sleep(0.1)  # Kurze Pause vor dem Deaktivieren
        success = send_clumsy_hotkey(hotkey)
        if success:
            state["is_lagging"] = False
            print(">> CLUMSY: Toggle-Signal gesendet (sollte jetzt inaktiv sein)")
        else:
            print("!! ERROR: Clumsy Hotkey konnte nicht gesendet werden")
            state["is_lagging"] = False  # Status trotzdem zurücksetzen
    else:
        state["is_lagging"] = False
        iface = state["config"]["net_interface"]
        prof = state["wifi_profile"]
        
        print(">> RESTORING NETWORK...")
        cmd = f'netsh wlan connect interface="{iface}" name="{prof}"' if prof else f'netsh wlan connect interface="{iface}"'
        subprocess.Popen(cmd, shell=True)
    
    update_overlay()

# --- INPUT DRIVER ---
SendInput = ctypes.windll.user32.SendInput
PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure): _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort), ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]
class HardwareInput(ctypes.Structure): _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_ushort), ("wParamH", ctypes.c_ushort)]
class MouseInput(ctypes.Structure): _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]
class Input_I(ctypes.Union): _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]
class Input(ctypes.Structure): _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]

def click_mouse_fast():
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, 0, 0x0002, 0, ctypes.pointer(extra)) # Down
    SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))
    
    # Robust hold time (20ms - 40ms)
    time.sleep(0.02 + (time.time() % 0.02))
    
    ii_.mi = MouseInput(0, 0, 0, 0x0004, 0, ctypes.pointer(extra)) # Up
    SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))

# --- MACRO ENGINE ---
def run_complex_macro():
    if state["is_running_macro"]: return
    state["is_running_macro"] = True
    print(">> MACRO: STARTING TIMELINE")
    update_overlay()
    
    c = state["config"]
    
    # Exakte Timings aus MacroUI.exe
    CLICK_PERIOD = 0.0437  # 22.88 CPS
    HOLD_TIME = 0.03
    PHASE2_DURATION = 1.85
    BRACKET_OFFSET = 1.61
    PHASE1_TOTAL = 2.01
    
    hold_start = 0.0
    hold_len = 0.9
    bracket_offset = float(c.get("macro_bracket_offset", BRACKET_OFFSET))
    bracket_hold = float(c.get("macro_bracket_hold", 0.004))
    spam_len = float(c.get("macro_spam_len", PHASE2_DURATION))
    click_hold = float(c.get("macro_click_hold", HOLD_TIME))

    # Phase 1: Initial Hold + Bracket Press
    def task_phase1():
        phase1_start = time.perf_counter()
        
        extra = ctypes.c_ulong(0); ii_ = Input_I()
        ii_.mi = MouseInput(0, 0, 0, 0x0002, 0, ctypes.pointer(extra))
        SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))
        
        # Wait 0.9s
        while time.perf_counter() < phase1_start + 0.9:
            time.sleep(0.001)
        
        ii_.mi = MouseInput(0, 0, 0, 0x0004, 0, ctypes.pointer(extra))
        SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))
        
        # Wait 0.05s more
        while time.perf_counter() < phase1_start + 0.95:
            time.sleep(0.001)
        
        # Bracket key (simulated with keyboard module would be better, but keeping it simple)
        # User should press [ manually or we use keyboard library
        
        # Wait until ~1s passed
        while time.perf_counter() < phase1_start + 1.0:
            time.sleep(0.001)
    
    # Phase 2: Fast Clicks + Bracket Spam
    def task_phase2():
        p2_start = time.perf_counter()
        p2_end = p2_start + PHASE2_DURATION
        bracket_time = p2_start + bracket_offset
        
        bracket_done = False
        next_click_time = p2_start
        
        extra = ctypes.c_ulong(0)
        
        while True:
            now = time.perf_counter()
            
            if now >= p2_end:
                break
            
            # Bracket spam at right moment
            if not bracket_done and now >= bracket_time:
                # Simulate 4 quick bracket presses
                # In real implementation, use keyboard library
                bracket_done = True
            
            # Fast clicks
            if now >= next_click_time:
                # Resync if too far behind
                if now - next_click_time > CLICK_PERIOD * 2:
                    next_click_time = now
                
                # Mouse press
                ii_ = Input_I()
                ii_.mi = MouseInput(0, 0, 0, 0x0002, 0, ctypes.pointer(extra))
                SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))
                
                # Hold for HOLD_TIME
                hold_until = time.perf_counter() + click_hold
                while time.perf_counter() < hold_until:
                    time.sleep(0.001)
                
                # Mouse release
                ii_.mi = MouseInput(0, 0, 0, 0x0004, 0, ctypes.pointer(extra))
                SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))
                
                next_click_time += CLICK_PERIOD
            else:
                # Wait for next event
                next_event = min(next_click_time, p2_end)
                if not bracket_done:
                    next_event = min(next_event, bracket_time)
                
                remaining = next_event - time.perf_counter()
                if remaining > 0:
                    time.sleep(min(0.005, remaining))

    # Execute - Run sequentially like original
    print(">> MACRO: Starting (MacroUI.exe timings)")
    task_phase1()
    task_phase2()
    
    state["is_running_macro"] = False
    print(">> MACRO: Complete")
    update_overlay()

def parse_key_string(k_str):
    if k_str.startswith("Key."):
        attr = k_str.split(".")[1]
        return getattr(keyboard.Key, attr, None)
    return k_str

def on_key_press(key):
    try:
        target = parse_key_string(state["config"].get("key_macro_trigger", "Key.f3"))
        if key == target or (hasattr(key, 'char') and key.char == target):
            threading.Thread(target=run_complex_macro).start()
    except: pass

# --- UI ---
THEME = {"bg": "#0a0a0a", "fg": "#00ff41", "warning": "#ff3333", "font_main": ("Consolas", 10), "font_header": ("Consolas", 14, "bold"), "font_mono": ("Consolas", 9)}

class HackerButton(tk.Button):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.config(bg="black", fg=THEME["fg"], activebackground=THEME["fg"], activeforeground="black", font=THEME["font_main"], bd=1, relief="solid")

class Overlay(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True, "-alpha", 0.85)
        self.config(bg="black")
        self.lbl_status = tk.Label(self, text="NET: ONLINE", font=("Consolas", 10, "bold"), bg="black", fg=THEME["fg"])
        self.lbl_status.pack(anchor="w")
        self.lbl_macro = tk.Label(self, text="", font=("Consolas", 10, "bold"), bg="black", fg=THEME["warning"])
        self.lbl_macro.pack(anchor="w")
        self.geometry(f"150x50+{state['config']['overlay_x']}+{state['config']['overlay_y']}")
        self.bind("<Button-1>", self.start_move); self.bind("<B1-Motion>", self.do_move); self.bind("<ButtonRelease-1>", self.stop_move)
    
    def start_move(self, event): self.x = event.x; self.y = event.y
    def do_move(self, event):
        x = self.winfo_x() + (event.x - self.x); y = self.winfo_y() + (event.y - self.y)
        self.geometry(f"+{x}+{y}")
    def stop_move(self, event):
        state["config"]["overlay_x"] = self.winfo_x(); state["config"]["overlay_y"] = self.winfo_y()
        save_config()

def update_overlay():
    if not state["overlay_ref"] or not state["overlay_ref"].winfo_exists(): return
    ov = state["overlay_ref"]
    if state["config"]["overlay_enabled"]:
        ov.deiconify()
        ov.lbl_status.config(text="NET: OFFLINE" if state["is_lagging"] else "NET: ONLINE", fg=THEME["warning"] if state["is_lagging"] else THEME["fg"])
        ov.lbl_macro.config(text="MACRO: RUNNING" if state["is_running_macro"] else "")
    else: ov.withdraw()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MACRO CONTROLLER"); self.geometry("380x750"); self.configure(bg=THEME["bg"]); self.attributes("-topmost", True)
        
        tk.Label(self, text="[ TIMELINE MACRO ]", font=THEME["font_header"], bg=THEME["bg"], fg=THEME["fg"]).pack(pady=(20,0))
        
        self.frame = tk.Frame(self, bg=THEME["bg"]); self.frame.pack(fill="both", expand=True, padx=20)
        self.build_ui()
        state["overlay_ref"] = Overlay(self); update_overlay()

    def build_ui(self):
        keys = [chr(i) for i in range(97, 123)] + [str(i) for i in range(10)] + [f"Key.f{i}" for i in range(1, 13)]
        
        def add_section(txt): tk.Label(self.frame, text=txt, bg=THEME["bg"], fg="#888", font=("Consolas", 9, "bold")).pack(anchor="w", pady=(10,2))
        def add_entry(txt, key):
            f = tk.Frame(self.frame, bg=THEME["bg"]); f.pack(fill="x", pady=2)
            tk.Label(f, text=txt, bg=THEME["bg"], fg="white", width=18, anchor="w").pack(side="left")
            e = tk.Entry(f, bg="#222", fg="white", font=THEME["font_mono"]); e.insert(0, str(state["config"].get(key, ""))); e.pack(side="left", fill="x", expand=True)
            return e

        # Global Settings
        tk.Label(self.frame, text="NETWORK METHOD:", bg=THEME["bg"], fg=THEME["fg"], font=THEME["font_mono"]).pack(anchor="w")
        self.cb_net_method = ttk.Combobox(self.frame, values=["netsh", "Clumsy"], font=THEME["font_mono"])
        self.cb_net_method.set(state["config"].get("network_method", "netsh"))
        self.cb_net_method.pack(fill="x", pady=2)
        # tk.Label(self.frame, text="NETWORK INTERFACE (netsh):", bg=THEME["bg"], fg=THEME["fg"], font=THEME["font_mono"]).pack(anchor="w", pady=(10,0))
        tk.Label(self.frame, text="NETWORK INTERFACE:", bg=THEME["bg"], fg=THEME["fg"], font=THEME["font_mono"]).pack(anchor="w")
        self.e_iface = tk.Entry(self.frame, bg="#222", fg="white", font=THEME["font_mono"])
        self.e_iface.insert(0, str(state["config"].get("net_interface", "WiFi")))
        self.e_iface.pack(fill="x", pady=2)

        tk.Label(self.frame, text="CLUMSY HOTKEY:", bg=THEME["bg"], fg=THEME["fg"], font=THEME["font_mono"]).pack(anchor="w", pady=(10,0))
        self.e_clumsy_key = tk.Entry(self.frame, bg="#222", fg="white", font=THEME["font_mono"])
        self.e_clumsy_key.insert(0, str(state["config"].get("clumsy_hotkey", "[")))
        self.e_clumsy_key.pack(fill="x", pady=2)

        tk.Label(self.frame, text="TRIGGER KEY:", bg=THEME["bg"], fg=THEME["fg"], font=THEME["font_mono"]).pack(anchor="w", pady=(10,0))
        self.cb_trig = ttk.Combobox(self.frame, values=keys, font=THEME["font_mono"]); self.cb_trig.set(state["config"]["key_macro_trigger"]); self.cb_trig.pack(fill="x", pady=2)
        
        tk.Label(self.frame, text="DISCONNECT TIMING:", bg=THEME["bg"], fg=THEME["fg"], font=THEME["font_mono"]).pack(anchor="w", pady=(10,0))
        self.cb_disc_mode = ttk.Combobox(self.frame, values=["After Click Start", "Before Click Start"], font=THEME["font_mono"])
        self.cb_disc_mode.set(state["config"].get("macro_disconnect_mode", "Before Click Start"))
        self.cb_disc_mode.pack(fill="x", pady=2)
        
        tk.Label(self.frame, text="CLICKS PER SECOND (CPS):", bg=THEME["bg"], fg=THEME["fg"], font=THEME["font_mono"]).pack(anchor="w", pady=(10,0))
        self.s_cps = tk.Scale(self.frame, from_=1, to=30, orient="horizontal", bg=THEME["bg"], fg="white", highlightthickness=0, troughcolor="#222"); self.s_cps.set(state["config"]["click_cps"]); self.s_cps.pack(fill="x")

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

        # Buttons
        f_btn = tk.Frame(self.frame, bg=THEME["bg"]); f_btn.pack(fill="x", pady=20)
        HackerButton(f_btn, text="SAVE SETTINGS", command=self.save).pack(fill="x", pady=2)
        self.btn_ov = HackerButton(f_btn, text="DISABLE OVERLAY", command=self.toggle_ov); self.btn_ov.pack(fill="x", pady=2)
        HackerButton(f_btn, text="RELOAD TOOL", command=lambda: os.execv(sys.executable, [sys.executable] + sys.argv), bg="#330000").pack(fill="x", pady=2)

    def save(self):
        c = state["config"]
        c["key_macro_trigger"] = self.cb_trig.get()
        c["macro_disconnect_mode"] = self.cb_disc_mode.get()
        c["click_cps"] = self.s_cps.get()
        c["net_interface"] = self.e_iface.get()
        c["network_method"] = self.cb_net_method.get()
        c["clumsy_hotkey"] = self.e_clumsy_key.get()
        try:
            c["macro_hold_start"] = float(self.e_h_st.get())
            c["macro_hold_len"] = float(self.e_h_ln.get())
            c["macro_net_start"] = float(self.e_n_st.get())
            c["macro_net_len"] = float(self.e_n_ln.get())
            c["macro_spam_start"] = float(self.e_s_st.get())
            c["macro_spam_len"] = float(self.e_s_ln.get())
        except: pass
        save_config()
        messagebox.showinfo("Saved", "Settings Updated!")

    def toggle_ov(self):
        state["config"]["overlay_enabled"] = not state["config"]["overlay_enabled"]
        self.btn_ov.config(text="DISABLE OVERLAY" if state["config"]["overlay_enabled"] else "ENABLE OVERLAY")
        update_overlay(); save_config()

if __name__ == "__main__":
    if not run_as_admin(): sys.exit(0)
    load_config() # Load before interface detection to see if we have a saved name
    if state["config"]["net_interface"] == "Auto-Detect":
        state["config"]["net_interface"] = detect_wifi_interface()
    
    keyboard.Listener(on_press=on_key_press).start(); App().mainloop()