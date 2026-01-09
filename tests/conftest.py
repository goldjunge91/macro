"""
Pytest configuration and fixtures
"""

import sys
from unittest.mock import MagicMock

# Mock pynput before any imports since it requires X display
pynput_mock = MagicMock()
keyboard_mock = MagicMock()
mouse_mock = MagicMock()


# Create a proper KeyCode class that can be instantiated
class MockKeyCode:
    def __init__(self, char=None, vk=None):
        self.char = char
        self.vk = vk

    @classmethod
    def from_char(cls, char):
        return cls(char=char)

    @classmethod
    def from_vk(cls, vk):
        return cls(vk=vk)

    def __repr__(self):
        if self.char:
            return f"KeyCode(char='{self.char}')"
        return f"KeyCode(vk={self.vk})"


# Create a proper Key enum-like class
class MockKey:
    class _KeyType:
        def __init__(self, name):
            self.name = name

        def __repr__(self):
            return f"Key.{self.name}"

    shift = _KeyType("shift")
    ctrl = _KeyType("ctrl")
    alt = _KeyType("alt")
    space = _KeyType("space")
    tab = _KeyType("tab")
    enter = _KeyType("enter")


keyboard_mock.KeyCode = MockKeyCode
keyboard_mock.Key = MockKey


# Create mock classes for mouse
class MockButton:
    left = "left"
    right = "right"
    middle = "middle"


mouse_mock.Button = MockButton

pynput_mock.keyboard = keyboard_mock
pynput_mock.mouse = mouse_mock

sys.modules["pynput"] = pynput_mock
sys.modules["pynput.keyboard"] = keyboard_mock
sys.modules["pynput.mouse"] = mouse_mock

# Mock input_control module which has Windows-specific dependencies
input_control_mock = MagicMock()
input_control_mock.keyboard_controller = MagicMock()
input_control_mock.mouse = MagicMock()
input_control_mock.SendInput = MagicMock()
input_control_mock.Input = MagicMock()
input_control_mock.Input_I = MagicMock()
input_control_mock.KeyBdInput = MagicMock()
input_control_mock.MouseInput = MagicMock()
input_control_mock.click_mouse_fast = MagicMock()
input_control_mock.move_mouse_horizontal = MagicMock()
input_control_mock.tap_tab = MagicMock()

sys.modules["input_control"] = input_control_mock

# Mock network module which may have Windows-specific code
network_mock = MagicMock()
network_mock.send_clumsy_hotkey = MagicMock()
network_mock.disconnect_net = MagicMock()
network_mock.reconnect_net = MagicMock()
network_mock.start_clumsy = MagicMock(return_value=True)
network_mock.stop_clumsy = MagicMock(return_value=True)
network_mock.is_clumsy_running = MagicMock(return_value=False)

sys.modules["network"] = network_mock
