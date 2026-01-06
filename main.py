import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
import importlib.util


def check_dependencies():
    missing = []
    try:
        if not importlib.util.find_spec("pynput"):
            missing.append("pynput")
    except Exception:
        pass
    try:
        if not importlib.util.find_spec("psutil"):
            missing.append("psutil")
    except Exception:
        pass
    if missing:
        root = tk.Tk()
        root.withdraw()
        if messagebox.askyesno(
            "Missing Dependencies", f"Install {', '.join(missing)}?"
        ):
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            import os

            os.execv(sys.executable, [sys.executable] + sys.argv)
        sys.exit()


check_dependencies()

from pynput import keyboard
from pynput.mouse import Listener as MouseListener

from config import state, load_config, save_config, check_config_reload
from network import (
    run_as_admin,
    auto_detect_interface,
    get_active_network_interfaces,
    disconnect_net,
    reconnect_net,
)
from recording import (
    load_recording,
    start_recording,
    stop_recording,
    record_action,
    playback_recording,
)
from macros import run_complex_macro, run_throw_macro, run_throw_macro_v2
from gui import App, update_overlay
from hotkeys import on_key_press, on_key_release, on_mouse_click, on_mouse_move


def create_disconnect_net_wrapper():
    def wrapper():
        disconnect_net(state, lambda: update_overlay(state))

    return wrapper


def create_reconnect_net_wrapper():
    def wrapper():
        reconnect_net(state, lambda: update_overlay(state))

    return wrapper


def create_run_complex_macro_wrapper():
    def wrapper():
        run_complex_macro(
            state,
            lambda: update_overlay(state),
            create_disconnect_net_wrapper(),
            create_reconnect_net_wrapper(),
        )

    return wrapper


def create_run_throw_macro_wrapper():
    def wrapper():
        run_throw_macro(state)

    return wrapper


def create_run_throw_macro_v2_wrapper():
    def wrapper():
        run_throw_macro_v2(
            state,
            lambda: update_overlay(state),
            create_disconnect_net_wrapper(),
            create_reconnect_net_wrapper(),
        )

    return wrapper


def create_start_recording_wrapper():
    def wrapper():
        start_recording(state, lambda: update_overlay(state))

    return wrapper


def create_stop_recording_wrapper():
    def wrapper():
        stop_recording(state, lambda: update_overlay(state))

    return wrapper


def create_playback_recording_wrapper():
    def wrapper():
        playback_recording(state)

    return wrapper


def create_record_action_wrapper():
    def wrapper(action_type, **kwargs):
        record_action(state, action_type, **kwargs)

    return wrapper


def create_on_key_press_wrapper():
    def wrapper(key):
        on_key_press(
            key,
            state,
            create_run_complex_macro_wrapper(),
            create_run_throw_macro_wrapper(),
            create_run_throw_macro_v2_wrapper(),
            create_start_recording_wrapper(),
            create_stop_recording_wrapper(),
            create_playback_recording_wrapper(),
            create_record_action_wrapper(),
        )

    return wrapper


def create_on_key_release_wrapper():
    def wrapper(key):
        on_key_release(key, state, create_record_action_wrapper())

    return wrapper


def create_on_mouse_click_wrapper():
    def wrapper(x, y, button, pressed):
        on_mouse_click(x, y, button, pressed, state, create_record_action_wrapper())

    return wrapper


def create_on_mouse_move_wrapper():
    def wrapper(x, y):
        on_mouse_move(x, y, state, create_record_action_wrapper())

    return wrapper


if __name__ == "__main__":
    if not run_as_admin():
        sys.exit(0)

    load_config()
    load_recording(state)

    if state["config"]["net_interface"] == "Auto-Detect":
        interface_name, interface_type = auto_detect_interface()
        state["config"]["net_interface"] = interface_name
        state["config"]["net_interface_type"] = interface_type

    keyboard.Listener(
        on_press=create_on_key_press_wrapper(),
        on_release=create_on_key_release_wrapper(),
    ).start()

    MouseListener(
        on_click=create_on_mouse_click_wrapper(), on_move=create_on_mouse_move_wrapper()
    ).start()

    app = App(state, save_config, get_active_network_interfaces)
    
    def check_reload():
        if check_config_reload():
            print(">> CONFIG: Configuration reloaded!")
        app.after(1000, check_reload)
    
    app.after(1000, check_reload)
    app.mainloop()
