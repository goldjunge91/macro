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
    if not state["config"].get("throw_enabled", True):
        return
    print(">> THROW MACRO: STARTING")
    start_time = time.perf_counter()

    from network import send_clumsy_hotkey
    from input_control import move_mouse_horizontal

    clumsy_hotkey = state["config"].get("clumsy_hotkey", "8")

    def toggle_clumsy():
        send_clumsy_hotkey(clumsy_hotkey)

    clumsy_thread = threading.Thread(target=toggle_clumsy)
    clumsy_thread.start()

    mouse.press(Button.left)
    move_mouse_horizontal(-2000, duration=0.5, steps=50)

    clumsy_thread.join()

    from input_control import tap_tab

    tap_tab(0.02)
    time.sleep(0.08)
    mouse.release(Button.left)

    period = 0.0219
    dwell = 0.00389
    max_total_time = 2.95
    end_time = start_time + max_total_time
    while time.perf_counter() < end_time:
        keyboard_controller.press(keyboard.KeyCode.from_vk(69))
        time.sleep(dwell)
        keyboard_controller.release(keyboard.KeyCode.from_vk(69))
        time.sleep(period - dwell)

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
