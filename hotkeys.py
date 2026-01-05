import threading
from pynput import keyboard


def parse_key_string(k_str):
    if k_str.startswith("Key."):
        attr = k_str.split(".")[1]
        return getattr(keyboard.Key, attr, None)
    return k_str


def on_key_press(key, state, run_complex_macro, run_throw_macro, start_recording, stop_recording, playback_recording, record_action):
    try:
        if state["is_recording"]:
            record_action("key_press", key=key)

        if not state["config"].get("macro_enabled", True):
            return
        target = parse_key_string(state["config"].get("key_macro_trigger", "Key.f3"))
        if key == target or (hasattr(key, "char") and key.char == target):
            threading.Thread(target=run_complex_macro).start()

        throw_target = parse_key_string(
            state["config"].get("key_throw_trigger", "Key.f4")
        )
        if key == throw_target or (hasattr(key, "char") and key.char == throw_target):
            threading.Thread(target=run_throw_macro).start()

        record_trigger = parse_key_string(
            state["config"].get("key_record_trigger", "Key.f5")
        )
        if key == record_trigger or (
            hasattr(key, "char") and key.char == record_trigger
        ):
            if state["is_recording"]:
                stop_recording()
            else:
                start_recording()

        playback_trigger = parse_key_string(
            state["config"].get("key_playback_trigger", "Key.f6")
        )
        if key == playback_trigger or (
            hasattr(key, "char") and key.char == playback_trigger
        ):
            threading.Thread(target=playback_recording).start()
    except Exception:
        pass


def on_key_release(key, state, record_action):
    try:
        if state["is_recording"]:
            record_action("key_release", key=key)
    except Exception:
        pass


def on_mouse_click(x, y, button, pressed, state, record_action):
    try:
        if state["is_recording"]:
            if pressed:
                record_action("mouse_press", button=button, x=x, y=y)
            else:
                record_action("mouse_release", button=button, x=x, y=y)
    except Exception:
        pass


def on_mouse_move(x, y, state, record_action):
    import time
    try:
        if state["is_recording"]:
            current_time = time.time()
            if current_time - state["last_mouse_move_time"] >= 0.02:
                record_action("mouse_move", x=x, y=y)
                state["last_mouse_move_time"] = current_time
    except Exception:
        pass
