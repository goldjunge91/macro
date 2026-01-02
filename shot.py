import sys
import subprocess
import time
import threading
import ctypes
import tkinter as tk
from tkinter import messagebox

# --- DEPENDENCY CHECK ---
def check_dependencies():
    missing = []
    try: import pynput
    except ImportError: missing.append("pynput")
    if missing:
        root = tk.Tk(); root.withdraw()
        if messagebox.askyesno("Missing Dependencies", f"Install {', '.join(missing)}?"):
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            import os
            os.execv(sys.executable, [sys.executable] + sys.argv)
        sys.exit()

check_dependencies()
from pynput import keyboard, mouse

# --- STATE ---
state = {
    "shot_active": False,
    "delay_ms": 25  # Default: 25ms between clicks (like SteelSeries)
}

# --- SYSTEM FUNCTIONS ---
def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

def run_as_admin():
    if is_admin(): return True
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    return False

# --- INPUT DRIVER ---
SendInput = ctypes.windll.user32.SendInput
PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure): 
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort), ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure): 
    _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_ushort), ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure): 
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union): 
    _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]

class Input(ctypes.Structure): 
    _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]

def click_mouse_fast():
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    
    # Mouse down
    ii_.mi = MouseInput(0, 0, 0, 0x0002, 0, ctypes.pointer(extra))
    SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))
    
    # Robust hold time (20ms - 40ms) - from shot2.py
    time.sleep(0.02 + (time.time() % 0.02))
    
    # Mouse up
    ii_.mi = MouseInput(0, 0, 0, 0x0004, 0, ctypes.pointer(extra))
    SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))

# --- SHOT MACRO ---
def run_shot_macro():
    delay_ms = state["delay_ms"]
    print(f">> SHOT MACRO: START ({delay_ms}ms delay)")
    
    # Convert MS to CPS for interval calculation
    cps = 1000.0 / delay_ms
    interval = 1.0 / cps
    
    while state["shot_active"]:
        click_mouse_fast()
        # Simple sleep with compensation (from shot2.py)
        time.sleep(max(0, interval - 0.03))
    
    print(">> SHOT MACRO: END")

# --- KEYBOARD EVENTS ---
def on_key_press(key):
    try:
        # Start shot macro when Left Alt is pressed
        if key == keyboard.Key.alt_l:
            if not state["shot_active"]:
                state["shot_active"] = True
                threading.Thread(target=run_shot_macro, daemon=True).start()
    except Exception as e:
        print(f"!! Error in on_key_press: {e}")

def on_key_release(key):
    try:
        # Stop shot macro when Left Alt is released
        if key == keyboard.Key.alt_l:
            state["shot_active"] = False
    except Exception as e:
        print(f"!! Error in on_key_release: {e}")

# --- UI ---
class ShotApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SHOT MACRO")
        self.geometry("320x280")
        self.configure(bg="#0a0a0a")
        self.attributes("-topmost", True)
        
        tk.Label(
            self, 
            text="[ SHOT MACRO ]", 
            font=("Consolas", 14, "bold"), 
            bg="#0a0a0a", 
            fg="#00ff41"
        ).pack(pady=20)
        
        tk.Label(
            self, 
            text="Hold LEFT ALT to click", 
            font=("Consolas", 10), 
            bg="#0a0a0a", 
            fg="white",
            justify="center"
        ).pack(pady=5)
        
        # MS Delay Setting
        tk.Label(
            self,
            text="DELAY BETWEEN CLICKS:",
            font=("Consolas", 9, "bold"),
            bg="#0a0a0a",
            fg="#00ff41"
        ).pack(pady=(10, 5))
        
        self.delay_label = tk.Label(
            self,
            text=f"{state['delay_ms']}ms (~{int(1000/state['delay_ms'])} CPS)",
            font=("Consolas", 10, "bold"),
            bg="#0a0a0a",
            fg="#ff3333"
        )
        self.delay_label.pack()
        
        self.delay_slider = tk.Scale(
            self,
            from_=20,
            to=50,
            orient="horizontal",
            bg="#1a1a1a",
            fg="white",
            highlightthickness=0,
            troughcolor="#333",
            activebackground="#00ff41",
            length=260,
            command=self.update_delay,
            showvalue=0
        )
        self.delay_slider.set(state["delay_ms"])
        self.delay_slider.pack(pady=5)
        
        self.status_label = tk.Label(
            self, 
            text="Status: WAITING", 
            font=("Consolas", 10, "bold"), 
            bg="#0a0a0a", 
            fg="#00ff41"
        )
        self.status_label.pack(pady=15)
        
        # Update status periodically
        self.update_status()
    
    def update_delay(self, value):
        state["delay_ms"] = int(float(value))
        cps = int(1000 / state["delay_ms"])
        self.delay_label.config(text=f"{state['delay_ms']}ms (~{cps} CPS)")
    
    def update_status(self):
        if state["shot_active"]:
            self.status_label.config(text="Status: ACTIVE", fg="#ff3333")
        else:
            self.status_label.config(text="Status: WAITING", fg="#00ff41")
        self.after(100, self.update_status)

if __name__ == "__main__":
    if not run_as_admin(): 
        sys.exit(0)
    
    print(">> SHOT MACRO STARTED")
    print(">> Hold LEFT ALT to activate rapid clicking")
    
    # Start keyboard listener
    keyboard.Listener(on_press=on_key_press, on_release=on_key_release).start()
    
    # Start GUI
    ShotApp().mainloop()
