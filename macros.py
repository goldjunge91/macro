import time
import threading
import ctypes
from pynput import keyboard
from input_control import (
    Input_I,
    MouseInput,
    KeyBdInput,
    Input,
    SendInput,
    click_mouse_fast,
    keyboard_controller,
    mouse,
    move_mouse_horizontal,
)
from pynput.mouse import Button


def run_throw_macro(state):
    if not state["config"].get("throw_enabled", True):
        return

    print(">> THROW MACRO: STARTING")
    start_time = time.perf_counter()

    c = state["config"]
    KEY_START_SETTLE_DELAY = c.get("throw_start_settle_delay", 0.03)
    KEY_PRE_DRAG_DELAY = c.get("throw_pre_drag_delay", 0.06)
    KEY_TAB_DELAY_AFTER_DRAG = c.get("throw_tab_delay_after_drag", 0.3)
    KEY_FINAL_SETTLE_DELAY = c.get("throw_final_settle_delay", 0.05)
    KEY_PRE_SPAM_DELAY = c.get("throw_pre_spam_delay", 0.0)
    KEY_CLUMSY_HOTKEY_E_START_DELAY = 0.0
    KEY_POST_TAB_TO_E_SPAM_DELAY = c.get("throw_post_tab_to_spam_delay", 0.004)

    POST_CLUMSY_TAP_DELAY = c.get("throw_post_clumsy_tap_delay", 0.021)
    POST_TAB_TAP_DELAY = c.get("throw_post_tab_tap_delay", 0.021)
    CLUMSY_DEACTIVATE_AFTER_SPAM = c.get("throw_clumsy_deactivate_after_spam", 0.20)

    KEY_TAB_DWELL = c.get("throw_tab_dwell", 0.02)
    KEY_E_DWELL = c.get("throw_e_dwell", 0.0389)

    KEY_SPAM_DURATION = c.get("throw_spam_duration", 2.25)
    KEY_E_PERIOD = c.get("throw_e_period", 0.0219)

    KEY_DRAG_TIME = c.get("throw_drag_time", 0.5)
    KEY_DRAG_LEFT_PIXELS = c.get("throw_drag_left_pixels", -2000)

    # Importiere Clumsy-Hotkey-Funktion und Maus-/Tastatur-Helfer
    from network import send_clumsy_hotkey
    from input_control import move_mouse_horizontal, tap_tab

    # Lese konfigurierten Clumsy-Hotkey
    clumsy_hotkey = state["config"].get("clumsy_hotkey", "8")
    # KeyCode für die E-Taste vorbereiten
    E_KEY = keyboard.KeyCode.from_char("e")

    # ===== PHASE 1: Initial Settle + Clumsy Hotkey Press =====
    # Kurze Pause zum Stabilisieren
    time.sleep(max(0.0, KEY_START_SETTLE_DELAY))

    # Clumsy einmal kurz toggeln (send_clumsy_hotkey enthält bereits eigenes Timing)
    send_clumsy_hotkey(clumsy_hotkey)
    # Kurzer Puffer nach dem Clumsy-Hotkey
    time.sleep(POST_CLUMSY_TAP_DELAY)

    # ===== PHASE 2: PRE-DRAG DELAY =====
    # Kurzer Delay vor dem Drag
    time.sleep(max(0.0, KEY_PRE_DRAG_DELAY))

    # ===== PHASE 3: Mouse Drag mit Button Down =====
    # Linke Maustaste drücken (halten)
    mouse.press(Button.left)

    # Horizontalen Drag ausführen (links, 2000px, 0.5s)
    move_mouse_horizontal(KEY_DRAG_LEFT_PIXELS, duration=KEY_DRAG_TIME, steps=50)

    # Maustaste nach dem Drag loslassen
    mouse.release(Button.left)

    # ===== PHASE 4: Tab Press =====
    # Wartezeit nach Drag, bevor Tab gesendet wird
    time.sleep(max(0.0, KEY_TAB_DELAY_AFTER_DRAG))

    # Tab drücken (kurzer Tap)
    tap_tab(dwell=KEY_TAB_DWELL)
    # Mini-Post-Delay nach Tab
    time.sleep(POST_TAB_TAP_DELAY)

    # Sicherheitshalber Tab loslassen
    keyboard_controller.release(keyboard.Key.tab)

    # ===== PHASE 5: E-SPAM DELAYS =====
    # Sofort weiter (kein zusätzlicher Delay)
    time.sleep(max(0.0, KEY_PRE_SPAM_DELAY))
    # Kurzer Delay zwischen Tab und Spam
    time.sleep(max(0.0, KEY_POST_TAB_TO_E_SPAM_DELAY))
    # Delay bis Clumsy wieder getoggelt wird
    time.sleep(max(0.0, KEY_CLUMSY_HOTKEY_E_START_DELAY))

    # ===== PHASE 6: E-SPAM =====
    # Spam-Startzeit merken
    spam_start_time = time.perf_counter()
    # Spam-Endzeit berechnen
    spam_end = spam_start_time + KEY_SPAM_DURATION
    # Flag: Clumsy schon deaktiviert?
    clumsy_deactivated = False

    while time.perf_counter() < spam_end:
        # E drücken
        keyboard_controller.press(E_KEY)
        # E gehalten lassen für dwell-Zeit
        time.sleep(KEY_E_DWELL)
        # E loslassen
        keyboard_controller.release(E_KEY)

        # Clumsy nach 0.20s Spam toggeln (späteres Deaktivieren)
        if (
            not clumsy_deactivated
            and (time.perf_counter() - spam_start_time) >= CLUMSY_DEACTIVATE_AFTER_SPAM
        ):
            send_clumsy_hotkey(clumsy_hotkey)
            clumsy_deactivated = True

        # Pause bis zum nächsten E-Press
        time.sleep(KEY_E_PERIOD)

    # ===== PHASE 7: Cleanup =====
    # Abschluss-Delay
    time.sleep(max(0.0, KEY_FINAL_SETTLE_DELAY))

    # Abschluss-Log mit Gesamtdauer
    print(f">> THROW MACRO: COMPLETE ({time.perf_counter() - start_time:.3f}s)")


def run_throw_macro_v2(state, update_overlay, disconnect_net, reconnect_net):
    """
    Throw Macro Version 2 - Uses robust input methods from run_complex_macro
    Sequence: Clumsy activate → Drag → Tab → E-spam → Clumsy deactivate
    """
    if not state["config"].get("throw_enabled", True):
        return
    
    print(">> THROW MACRO V2: STARTING")
    start_time = time.perf_counter()
    
    c = state["config"]
    
    KEY_START_SETTLE_DELAY = c.get("throw_start_settle_delay", 0.03)
    KEY_PRE_DRAG_DELAY = c.get("throw_pre_drag_delay", 0.06)
    KEY_TAB_DELAY_AFTER_DRAG = c.get("throw_tab_delay_after_drag", 0.3)
    KEY_FINAL_SETTLE_DELAY = c.get("throw_final_settle_delay", 0.05)
    KEY_POST_TAB_TO_E_SPAM_DELAY = c.get("throw_post_tab_to_spam_delay", 0.004)
    
    POST_TAB_TAP_DELAY = c.get("throw_post_tab_tap_delay", 0.021)
    CLUMSY_DEACTIVATE_AFTER_SPAM = c.get("throw_clumsy_deactivate_after_spam", 0.20)
    
    KEY_TAB_DWELL = c.get("throw_tab_dwell", 0.02)
    KEY_E_DWELL = c.get("throw_e_dwell", 0.0389)
    
    KEY_SPAM_DURATION = c.get("throw_spam_duration", 2.25)
    KEY_E_PERIOD = c.get("throw_e_period", 0.0219)
    
    KEY_DRAG_TIME = c.get("throw_drag_time", 0.5)
    KEY_DRAG_LEFT_PIXELS = c.get("throw_drag_left_pixels", -2000)
    
    E_KEYCODE = 0x45
    TAB_KEYCODE = 0x09
    
    time.sleep(max(0.0, KEY_START_SETTLE_DELAY))
    
    print(">> THROW V2: ACTIVATING CLUMSY")
    disconnect_net()
    time.sleep(0.05)
    
    time.sleep(max(0.0, KEY_PRE_DRAG_DELAY))
    
    print(">> THROW V2: DRAG START")
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, 0, 0x0002, 0, ctypes.pointer(extra))
    SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))
    
    move_mouse_horizontal(KEY_DRAG_LEFT_PIXELS, duration=KEY_DRAG_TIME, steps=50)
    
    ii_.mi = MouseInput(0, 0, 0, 0x0004, 0, ctypes.pointer(extra))
    SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))
    print(">> THROW V2: DRAG COMPLETE")
    
    time.sleep(max(0.0, KEY_TAB_DELAY_AFTER_DRAG))
    
    print(">> THROW V2: TAB PRESS")
    ii_ = Input_I()
    ii_.ki = KeyBdInput(TAB_KEYCODE, 0, 0, 0, ctypes.pointer(extra))
    SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input))
    time.sleep(KEY_TAB_DWELL)
    ii_.ki = KeyBdInput(TAB_KEYCODE, 0, 0x0002, 0, ctypes.pointer(extra))
    SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input))
    
    time.sleep(POST_TAB_TAP_DELAY)
    time.sleep(max(0.0, KEY_POST_TAB_TO_E_SPAM_DELAY))
    
    print(">> THROW V2: E-SPAM START")
    spam_start_time = time.perf_counter()
    spam_end = spam_start_time + KEY_SPAM_DURATION
    clumsy_deactivated = False
    
    while time.perf_counter() < spam_end:
        ii_ = Input_I()
        ii_.ki = KeyBdInput(E_KEYCODE, 0, 0, 0, ctypes.pointer(extra))
        SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input))
        time.sleep(KEY_E_DWELL)
        ii_.ki = KeyBdInput(E_KEYCODE, 0, 0x0002, 0, ctypes.pointer(extra))
        SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input))
        
        if not clumsy_deactivated and (time.perf_counter() - spam_start_time) >= CLUMSY_DEACTIVATE_AFTER_SPAM:
            print(">> THROW V2: DEACTIVATING CLUMSY")
            reconnect_net()
            clumsy_deactivated = True
        
        time.sleep(KEY_E_PERIOD)
    
    print(">> THROW V2: E-SPAM COMPLETE")
    
    time.sleep(max(0.0, KEY_FINAL_SETTLE_DELAY))
    
    print(f">> THROW MACRO V2: COMPLETE ({time.perf_counter() - start_time:.3f}s)")


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
