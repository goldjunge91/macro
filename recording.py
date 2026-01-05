import os
import time
import csv
from datetime import datetime
from pynput import keyboard
from pynput.mouse import Button
from input_control import keyboard_controller, mouse

RECORDINGS_DIR = "recordings"


def get_recordings_folder():
    """Ensure recordings folder exists and return path"""
    if not os.path.exists(RECORDINGS_DIR):
        os.makedirs(RECORDINGS_DIR)
    return RECORDINGS_DIR


def key_to_string(key):
    """Convert pynput key to string representation"""
    if isinstance(key, keyboard.KeyCode):
        if key.char:
            return f"char:{key.char}"
        else:
            return f"vk:{key.vk}"
    elif isinstance(key, keyboard.Key):
        return f"Key.{key.name}"
    else:
        return str(key)


def string_to_key(key_str):
    """Convert string representation back to pynput key"""
    if key_str.startswith("char:"):
        return keyboard.KeyCode.from_char(key_str[5:])
    elif key_str.startswith("vk:"):
        return keyboard.KeyCode.from_vk(int(key_str[3:]))
    elif key_str.startswith("Key."):
        key_name = key_str[4:]
        return getattr(keyboard.Key, key_name, None)
    return None


def button_to_string(button):
    """Convert mouse button to string"""
    if button == Button.left:
        return "left"
    elif button == Button.right:
        return "right"
    elif button == Button.middle:
        return "middle"
    else:
        return str(button)


def string_to_button(button_str):
    """Convert string to mouse button"""
    if button_str == "left":
        return Button.left
    elif button_str == "right":
        return Button.right
    elif button_str == "middle":
        return Button.middle
    return Button.left


def save_recording(state):
    """Save recorded actions to CSV file with timestamp"""
    if not state["recorded_actions"]:
        print(">> SAVE: No recording to save")
        return False

    try:
        get_recordings_folder()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(RECORDINGS_DIR, f"recording_{timestamp}.csv")

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "type", "key", "button", "x", "y"])

            for action in state["recorded_actions"]:
                time_val = action.get("time", 0)
                action_type = action.get("type", "")

                key_val = ""
                if "key" in action:
                    key_val = key_to_string(action["key"])

                button_val = ""
                if "button" in action:
                    button_val = button_to_string(action["button"])

                x_val = action.get("x", "")
                y_val = action.get("y", "")

                writer.writerow(
                    [time_val, action_type, key_val, button_val, x_val, y_val]
                )

        state["last_recording_file"] = filename
        print(f">> SAVE: Recording saved to {filename}")
        return True
    except Exception as e:
        print(f"!! ERROR saving recording: {e}")
        return False


def load_recording(state, filename=None):
    """Load recorded actions from CSV file"""
    if filename is None:
        filename = state.get("last_recording_file")

    if not filename or not os.path.exists(filename):
        recordings_dir = get_recordings_folder()
        recordings = [f for f in os.listdir(recordings_dir) if f.endswith(".csv")]
        if not recordings:
            return False
        recordings.sort(reverse=True)
        filename = os.path.join(recordings_dir, recordings[0])

    try:
        state["recorded_actions"] = []

        with open(filename, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                action = {"time": float(row["time"]), "type": row["type"]}

                if row["key"]:
                    key = string_to_key(row["key"])
                    if key:
                        action["key"] = key

                if row["button"]:
                    action["button"] = string_to_button(row["button"])

                if row["x"]:
                    action["x"] = int(row["x"])
                if row["y"]:
                    action["y"] = int(row["y"])

                state["recorded_actions"].append(action)

        state["last_recording_file"] = filename
        print(
            f">> LOAD: Recording loaded from {os.path.basename(filename)} ({len(state['recorded_actions'])} actions)"
        )
        return True
    except Exception as e:
        print(f"!! ERROR loading recording: {e}")
        return False


def get_available_recordings():
    """Get list of all available recording files"""
    recordings_dir = get_recordings_folder()
    recordings = [f for f in os.listdir(recordings_dir) if f.endswith(".csv")]
    recordings.sort(reverse=True)
    return [os.path.join(recordings_dir, f) for f in recordings]


def start_recording(state, update_overlay):
    if state["is_recording"]:
        print(">> RECORDING: Already recording")
        return

    state["is_recording"] = True
    state["recorded_actions"] = []
    state["recording_start_time"] = time.perf_counter()
    state["last_mouse_move_time"] = 0
    state["pressed_keys"] = set()
    print(">> RECORDING: STARTED - Press F5 again to stop")
    print(">> RECORDING: Supports simultaneous key presses")
    update_overlay()


def stop_recording(state, update_overlay):
    if not state["is_recording"]:
        return

    state["is_recording"] = False
    total_time = time.perf_counter() - state["recording_start_time"]
    action_count = len(state["recorded_actions"])
    print(
        f">> RECORDING: STOPPED - {action_count} actions recorded in {total_time:.2f}s"
    )

    if action_count > 0:
        save_recording(state)

    update_overlay()


def record_action(state, action_type, **kwargs):
    if not state["is_recording"]:
        return

    timestamp = time.perf_counter() - state["recording_start_time"]
    action = {"type": action_type, "time": timestamp, **kwargs}

    if action_type == "key_press" and "key" in kwargs:
        key_str = key_to_string(kwargs["key"])
        state["pressed_keys"].add(key_str)
    elif action_type == "key_release" and "key" in kwargs:
        key_str = key_to_string(kwargs["key"])
        state["pressed_keys"].discard(key_str)

    state["recorded_actions"].append(action)


def playback_recording(state):
    if not state["config"].get("recording_enabled", True):
        return

    if state["is_recording"]:
        print(">> PLAYBACK: Cannot playback while recording")
        return

    if not state["recorded_actions"]:
        if not load_recording(state):
            print(">> PLAYBACK: No recording available")
            return

    print(f">> PLAYBACK: Starting {len(state['recorded_actions'])} actions")
    print(">> PLAYBACK: Replaying simultaneous inputs...")
    start_time = time.perf_counter()

    action_groups = {}
    for action in state["recorded_actions"]:
        action_time = action["time"]
        time_key = round(action_time, 3)
        if time_key not in action_groups:
            action_groups[time_key] = []
        action_groups[time_key].append(action)

    sorted_times = sorted(action_groups.keys())

    for action_time in sorted_times:
        target_time = start_time + action_time
        while time.perf_counter() < target_time:
            time.sleep(0.0001)

        actions = action_groups[action_time]

        for action in actions:
            action_type = action["type"]

            if action_type == "key_press":
                try:
                    key = action.get("key")
                    if isinstance(key, str):
                        keyboard_controller.press(keyboard.KeyCode.from_char(key))
                    else:
                        keyboard_controller.press(key)
                except Exception as e:
                    print(f"!! ERROR in key_press: {e}")

            elif action_type == "key_release":
                try:
                    key = action.get("key")
                    if isinstance(key, str):
                        keyboard_controller.release(keyboard.KeyCode.from_char(key))
                    else:
                        keyboard_controller.release(key)
                except Exception as e:
                    print(f"!! ERROR in key_release: {e}")

            elif action_type == "mouse_press":
                button = action.get("button", Button.left)
                mouse.press(button)

            elif action_type == "mouse_release":
                button = action.get("button", Button.left)
                mouse.release(button)

            elif action_type == "mouse_move":
                x, y = action.get("x"), action.get("y")
                mouse.position = (x, y)

    print(f">> PLAYBACK: COMPLETE ({time.perf_counter() - start_time:.3f}s)")
