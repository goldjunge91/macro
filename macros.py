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
    # Verlasse früh, wenn Throw-Makro deaktiviert ist
    if not state["config"].get("throw_enabled", True):
        return

    # Logge Start des Makros
    print(">> THROW MACRO: STARTING")
    # Merke Startzeit für spätere Dauerberechnung
    start_time = time.perf_counter()

    # === TIMING-KONSTANTEN (Original Bytecode Zeile 611-636) ===
    KEY_START_SETTLE_DELAY = 0.03  # Warte zu Beginn für Stabilität
    KEY_PRE_DRAG_DELAY = 0.06  # Kurzer Delay vor dem Drag (verlängert)
    KEY_TAB_DELAY_AFTER_DRAG = 0.3  # Wartezeit nach Drag vor Tab (verlängert)
    KEY_FINAL_SETTLE_DELAY = 0.05  # Abschluss-Delay nach Spam
    KEY_PRE_SPAM_DELAY = 0.0  # Kein extra Delay: Spam soll sofort starten
    KEY_CLUMSY_HOTKEY_E_START_DELAY = (
        0.0  # Kein Delay zwischen Spam-Start und Clumsy-Off
    )
    KEY_POST_TAB_TO_E_SPAM_DELAY = 0.004  # Kurzer Delay zwischen Tab und Spam

    POST_CLUMSY_TAP_DELAY = 0.021  # Puffer nach Clumsy-Hotkey (min 21ms)
    POST_TAB_TAP_DELAY = 0.021  # Puffer nach Tab-Tap (min 21ms)
    CLUMSY_DEACTIVATE_AFTER_SPAM = 0.20  # Clumsy-Toggle nach Spam-Start (s)

    KEY_TAB_DWELL = 0.02  # Tab Haltezeit
    KEY_E_DWELL = 0.0389  # E Haltezeit

    KEY_SPAM_DURATION = 2.25  # Dauer des E-Spams (zurück auf Original)
    KEY_E_PERIOD = 0.0219  # Pause zwischen E-Presses

    KEY_DRAG_TIME = 0.5  # Drag-Gesamtdauer
    KEY_DRAG_LEFT_PIXELS = -2000  # Drag-Distanz nach links

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
