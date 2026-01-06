import time
import threading
import ctypes
from pynput import keyboard
from input_control import (
    Input_I,
    MouseInput,
    Input,
    SendInput,
    click_mouse_fast,
    keyboard_controller,
    mouse,
)
from pynput.mouse import Button


def run_throw_macro(state):
    """
    KEY MACRO - 100% Original aus MacroV2.exe Bytecode (Zeilen 611-928)

    Zeitlicher Ablauf (Gesamtdauer: ~3.28s):
    0.000s: Start
    0.030s: Initial Settle Delay
    0.070s: Clumsy Hotkey drücken+loslassen (40ms press + 2ms post)
    0.130s: PRE_DRAG_DELAY (60ms) ← WICHTIG!
    0.130s: Linke Maustaste DOWN
    0.630s: Drag 1300px links in 0.5s (mit Mouse Button down)
    0.930s: TAB_DELAY_AFTER_DRAG (300ms)
    0.950s: Tab drücken+loslassen (20ms + 2ms)
    0.950s: Maus Button sicher loslassen
    0.980s: PRE_SPAM_DELAY (30ms) ← WICHTIG!
    0.984s: POST_TAB_TO_E_SPAM_DELAY (4ms)
    0.984s: CLUMSY_HOTKEY_E_START_DELAY (0ms)
    3.234s: E-Spam für 2.25s @ 45.7Hz (38.9ms down + 21.9ms up)
    3.284s: STOP_DRAG_DELAY (50ms)
    3.284s: Final mouse release check
    """
    if not state["config"].get("throw_enabled", True):
        return

    print(">> THROW MACRO: STARTING")
    start_time = time.perf_counter()

    # === TIMING-KONSTANTEN (Original Bytecode Zeile 611-636) ===
    KEY_START_SETTLE_DELAY = 0.03  # Initial settle nach Start
    KEY_PRE_DRAG_DELAY = 0.03  # WICHTIG: Delay VOR dem Drag
    KEY_TAB_DELAY_AFTER_DRAG = 0.3  # Delay NACH dem Drag
    KEY_STOP_DRAG_DELAY = 0.05  # Delay am Ende
    KEY_PRE_SPAM_DELAY = 0.03  # WICHTIG: Extra delay vor E-Spam
    KEY_CLUMSY_HOTKEY_E_START_DELAY = 0.01  # Zwischen Spam-Start und Clumsy
    KEY_POST_TAB_TO_E_SPAM_DELAY = 0.004  # Zwischen Tab und E-Spam

    KEY_CLUMSY_HOTKEY_DWELL = 0.04  # Clumsy Hotkey press duration
    KEY_TAB_DWELL = 0.02  # Tab press duration
    KEY_E_DWELL = 0.0389  # E press duration (38.9ms)

    KEY_SPAM_DURATION = 2.25  # E-Spam Gesamtdauer
    KEY_E_PERIOD = 0.0219  # Pause zwischen E-Presses (21.9ms)

    KEY_DRAG_TIME = 0.5  # Drag-Dauer
    KEY_DRAG_LEFT_PIXELS = -2000  # Pixel nach links (negativ!)

    from network import send_clumsy_hotkey
    from input_control import move_mouse_horizontal, tap_tab

    clumsy_hotkey = state["config"].get("clumsy_hotkey", "8")
    E_KEY = keyboard.KeyCode.from_char("e")

    # ===== PHASE 1: Initial Settle + Clumsy Hotkey Press =====
    time.sleep(max(0.0, KEY_START_SETTLE_DELAY))  # 30ms

    # Clumsy Hotkey press (NICHT gehalten, nur tap!)
    send_clumsy_hotkey(clumsy_hotkey)
    time.sleep(KEY_CLUMSY_HOTKEY_DWELL)  # 40ms
    time.sleep(0.002)  # post-delay

    # ===== PHASE 2: PRE-DRAG DELAY (WICHTIG!) =====
    time.sleep(max(0.0, KEY_PRE_DRAG_DELAY))  # 60ms

    # ===== PHASE 3: Mouse Drag mit Button Down =====
    # Mouse button down WÄHREND des Drags
    mouse.press(Button.left)

    # Nutze die gesplitten move_mouse_horizontal Funktion
    move_mouse_horizontal(KEY_DRAG_LEFT_PIXELS, duration=KEY_DRAG_TIME, steps=50)

    # ===== PHASE 4: Tab Press =====
    time.sleep(max(0.0, KEY_TAB_DELAY_AFTER_DRAG))  # 300ms

    # Nutze die gesplitten tap_tab Funktion
    tap_tab(dwell=KEY_TAB_DWELL)
    time.sleep(0.002)  # post-delay

    # Tab force release (sicherheitshalber)
    keyboard_controller.release(keyboard.Key.tab)

    # Mouse safe release (mit timeout)
    mouse.release(Button.left)
    time.sleep(0.001)  # kurze Pause für Release

    # ===== PHASE 5: E-SPAM DELAYS (WICHTIG!) =====
    time.sleep(max(0.0, KEY_PRE_SPAM_DELAY))  # 30ms
    time.sleep(max(0.0, KEY_POST_TAB_TO_E_SPAM_DELAY))  # 4ms
    time.sleep(max(0.0, KEY_CLUMSY_HOTKEY_E_START_DELAY))  # 0ms

    # ===== PHASE 6: E-SPAM =====
    spam_end = time.perf_counter() + KEY_SPAM_DURATION
    while time.perf_counter() < spam_end:
        keyboard_controller.press(E_KEY)
        time.sleep(KEY_E_DWELL)  # 38.9ms down
        keyboard_controller.release(E_KEY)
        time.sleep(KEY_E_PERIOD)  # 21.9ms pause

    # ===== PHASE 7: Cleanup =====
    time.sleep(max(0.0, KEY_STOP_DRAG_DELAY))  # 50ms
    mouse.release(Button.left)  # Final mouse release check

    # Clumsy Hotkey wieder zurück
    send_clumsy_hotkey(clumsy_hotkey)

    print(f">> THROW MACRO: COMPLETE ({time.perf_counter() - start_time:.3f}s)")


def run_complex_macro(state, update_overlay, disconnect_net, reconnect_net):
    if state["is_running_macro"]:
        return
    state["is_running_macro"] = True
    print(">> MACRO: STARTING TIMELINE")
    update_overlay()

    c = state["config"]

    hold_start = float(c.get("macro_hold_start"))
    hold_len = float(c.get("macro_hold_len"))
    net_start = float(c.get("macro_net_start"))
    net_len = float(c.get("macro_net_len"))
    spam_start = float(c.get("macro_spam_start"))
    spam_len = float(c.get("macro_spam_len"))
    cps = int(c.get("click_cps"))

    def task_hold():
        if hold_len <= 0:
            return

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

    def task_net():
        if net_len <= 0:
            return
        time.sleep(net_start)
        disconnect_net()
        time.sleep(net_len)
        reconnect_net()

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

    t1 = threading.Thread(target=task_hold)
    t2 = threading.Thread(target=task_net)
    t3 = threading.Thread(target=task_spam)
    t1.start()
    t2.start()
    t3.start()

    def waiter():
        t1.join()
        t2.join()
        t3.join()
        state["is_running_macro"] = False
        print(">> MACRO: FINISHED")
        update_overlay()

    threading.Thread(target=waiter).start()
