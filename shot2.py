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
    "shot_active": False
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
    """Perform a single mouse click as fast as possible"""
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    
    # Mouse down
    ii_.mi = MouseInput(0, 0, 0, 0x0002, 0, ctypes.pointer(extra))
    SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))
    
    # Robust hold time (20ms - 40ms)
    time.sleep(0.02 + (time.time() % 0.02))
    
    # Mouse up
    ii_.mi = MouseInput(0, 0, 0, 0x0004, 0, ctypes.pointer(extra))
    SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))

# --- SHOT MACRO ---
def run_shot_macro():
    """Clicks as fast as possible while Alt is held"""
    print(">> SHOT MACRO: ACTIVATED")
    click_count = 0
    cps = 10  # 10 clicks per second - reliable rate
    interval = 1.0 / cps
    
    while state["shot_active"]:
        click_mouse_fast()
        click_count += 1
        time.sleep(max(0, interval - 0.03))  # Subtract time for click execution
    
    print(f">> SHOT MACRO: DEACTIVATED (Total: {click_count})")

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
        self.geometry("300x200")
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
            text="Hold LEFT ALT to click\nas fast as possible!", 
            font=("Consolas", 10), 
            bg="#0a0a0a", 
            fg="white",
            justify="center"
        ).pack(pady=10)
        
        self.status_label = tk.Label(
            self, 
            text="Status: WAITING", 
            font=("Consolas", 10, "bold"), 
            bg="#0a0a0a", 
            fg="#00ff41"
        )
        self.status_label.pack(pady=20)
        
        # Update status periodically
        self.update_status()
    
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
