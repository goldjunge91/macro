import json
import os

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
    "key_record_trigger": "Key.f5",
    "key_playback_trigger": "Key.f6",
    "recording_enabled": True,
}

state = {
    "is_lagging": False,
    "is_running_macro": False,
    "wifi_profile": None,
    "overlay_ref": None,
    "config": DEFAULT_CONFIG.copy(),
    "is_recording": False,
    "recorded_actions": [],
    "recording_start_time": None,
    "current_recording_file": None,
    "last_recording_file": None,
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            for k in DEFAULT_CONFIG:
                if k not in loaded:
                    loaded[k] = DEFAULT_CONFIG[k]
            state["config"] = loaded
        except Exception:
            state["config"] = DEFAULT_CONFIG.copy()
    else:
        state["config"] = DEFAULT_CONFIG.copy()


def save_config():
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(state["config"], f, indent=2)
