import ctypes
import time
import math
from pynput import keyboard
from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Controller as MouseController, Button

keyboard_controller = KeyboardController()
mouse = MouseController()

SendInput = ctypes.windll.user32.SendInput
PUL = ctypes.POINTER(ctypes.c_ulong)


class KeyBdInput(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL),
    ]


class HardwareInput(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_ushort),
        ("wParamH", ctypes.c_ushort),
    ]


class MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL),
    ]


class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]


class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]


def click_mouse_fast():
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, 0, 0x0002, 0, ctypes.pointer(extra))
    SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))

    time.sleep(0.02 + (time.time() % 0.02))

    ii_.mi = MouseInput(0, 0, 0, 0x0004, 0, ctypes.pointer(extra))
    SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))


def tap_e(dwell=0.03):
    """Tap E key"""
    keyboard_controller.press(keyboard.KeyCode.from_char("e"))
    time.sleep(dwell)
    keyboard_controller.release(keyboard.KeyCode.from_char("e"))


def tap_tab(dwell=0.03):
    """Tap Tab key"""
    keyboard_controller.press(keyboard.Key.tab)
    time.sleep(dwell)
    keyboard_controller.release(keyboard.Key.tab)


def move_mouse_up_angle(distance, angle_deg=70, horizontal_dir=1, smooth_steps=30):
    """Move mouse at angle"""
    angle_rad = math.radians(angle_deg)
    dx = horizontal_dir * distance * math.cos(angle_rad)
    dy = -distance * math.sin(angle_rad)

    start_x, start_y = mouse.position
    for i in range(smooth_steps + 1):
        t = i / smooth_steps
        x = start_x + dx * t
        y = start_y + dy * t
        mouse.position = (int(x), int(y))
        time.sleep(0.001)


def move_mouse_horizontal(distance, duration=0.5, steps=50):
    """Move mouse horizontally (negative distance = left)"""
    dx = distance
    start_x, start_y = mouse.position
    for i in range(steps + 1):
        t = i / steps
        x = start_x + dx * t
        mouse.position = (int(x), start_y)
        time.sleep(duration / steps)


def double_click_left(hold_time=0.022, gap=0.055):
    """Double click left mouse button"""
    mouse.press(Button.left)
    time.sleep(hold_time)
    mouse.release(Button.left)
    time.sleep(gap)
    mouse.press(Button.left)
    time.sleep(hold_time)
    mouse.release(Button.left)


def tap_bracket(dwell=0.006):
    """Tap bracket key"""
    keyboard_controller.press(keyboard.KeyCode.from_vk(219))
    time.sleep(dwell)
    keyboard_controller.release(keyboard.KeyCode.from_vk(219))
