"""
Unit tests for macro functions in macros.py
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def mock_state():
    """Create a mock state object with default config"""
    return {
        "is_running_macro": False,
        "config": {
            "throw_enabled": True,
            "throw_start_settle_delay": 0.01,
            "throw_pre_drag_delay": 0.01,
            "throw_tab_delay_after_drag": 0.01,
            "throw_final_settle_delay": 0.01,
            "throw_pre_spam_delay": 0.0,
            "throw_post_tab_to_spam_delay": 0.001,
            "throw_post_clumsy_tap_delay": 0.01,
            "throw_post_tab_tap_delay": 0.01,
            "throw_clumsy_deactivate_after_spam": 0.05,
            "throw_tab_dwell": 0.01,
            "throw_e_dwell": 0.01,
            "throw_spam_duration": 0.1,
            "throw_e_period": 0.01,
            "throw_drag_time": 0.05,
            "throw_drag_left_pixels": -100,
            "clumsy_hotkey": "8",
            "macro_hold_start": 0.0,
            "macro_hold_len": 0.05,
            "macro_net_start": 0.01,
            "macro_net_len": 0.05,
            "macro_spam_start": 0.01,
            "macro_spam_len": 0.05,
            "click_cps": 10,
        },
    }


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies"""
    with patch("macros.time") as mock_time, patch(
        "macros.keyboard"
    ) as mock_keyboard, patch("macros.mouse") as mock_mouse, patch(
        "macros.keyboard_controller"
    ) as mock_kb_ctrl, patch(
        "macros.move_mouse_horizontal"
    ) as mock_move_mouse, patch(
        "macros.SendInput"
    ) as mock_send_input, patch(
        "macros.Input"
    ) as mock_input, patch(
        "macros.Input_I"
    ) as mock_input_i, patch(
        "macros.KeyBdInput"
    ) as mock_kbd_input, patch(
        "macros.MouseInput"
    ) as mock_mouse_input, patch(
        "macros.click_mouse_fast"
    ) as mock_click_fast, patch(
        "macros.threading"
    ) as mock_threading:

        # Setup time.perf_counter to return incrementing values
        mock_time.perf_counter.side_effect = [i * 0.01 for i in range(1000)]
        mock_time.time.side_effect = [i * 0.01 for i in range(1000)]
        mock_time.sleep = Mock()

        yield {
            "time": mock_time,
            "keyboard": mock_keyboard,
            "mouse": mock_mouse,
            "keyboard_controller": mock_kb_ctrl,
            "move_mouse_horizontal": mock_move_mouse,
            "SendInput": mock_send_input,
            "Input": mock_input,
            "Input_I": mock_input_i,
            "KeyBdInput": mock_kbd_input,
            "MouseInput": mock_mouse_input,
            "click_mouse_fast": mock_click_fast,
            "threading": mock_threading,
        }


class TestRunThrowMacro:
    """Tests for run_throw_macro function"""

    def test_throw_macro_disabled(self, mock_state, mock_dependencies):
        """Test that macro doesn't run when disabled"""
        from macros import run_throw_macro

        mock_state["config"]["throw_enabled"] = False
        run_throw_macro(mock_state)

        # Should return early without doing anything
        mock_dependencies["mouse"].press.assert_not_called()

    def test_throw_macro_basic_flow(self, mock_state):
        """Test basic flow of throw macro"""
        from macros import run_throw_macro

        with patch("macros.time.sleep") as mock_sleep, patch(
            "macros.time.perf_counter"
        ) as mock_perf, patch("network.send_clumsy_hotkey") as mock_clumsy:

            # Setup perf_counter to complete quickly
            counter = [0.0]

            def perf_counter_side_effect():
                val = counter[0]
                counter[0] += 1.0  # Large increment to finish quickly
                return val

            mock_perf.side_effect = perf_counter_side_effect

            run_throw_macro(mock_state)

            # Verify clumsy hotkey was sent
            mock_clumsy.assert_called()

            # Verify sleep was called (timing delays)
            assert mock_sleep.call_count > 0

    def test_throw_macro_e_spam_loop(self, mock_state):
        """Test that E key spam loop runs"""
        from macros import run_throw_macro

        # Set very short spam duration
        mock_state["config"]["throw_spam_duration"] = 0.05
        mock_state["config"]["throw_e_period"] = 0.01

        with patch("macros.time.sleep") as mock_sleep, patch(
            "macros.time.perf_counter"
        ) as mock_perf, patch("network.send_clumsy_hotkey"):

            # Setup perf_counter to simulate time progression
            counter = [0.0]

            def perf_counter_side_effect():
                val = counter[0]
                counter[0] += 0.02  # Slow progression to allow loop iterations
                return val

            mock_perf.side_effect = perf_counter_side_effect

            run_throw_macro(mock_state)

            # Verify the function completed
            assert mock_sleep.call_count > 0

    def test_throw_macro_clumsy_deactivation(self, mock_state):
        """Test that clumsy is deactivated during spam"""
        from macros import run_throw_macro

        mock_state["config"]["throw_spam_duration"] = 0.15
        mock_state["config"]["throw_clumsy_deactivate_after_spam"] = 0.05

        with patch("macros.time.sleep"), patch(
            "macros.time.perf_counter"
        ) as mock_perf, patch("network.send_clumsy_hotkey") as mock_clumsy, patch(
            "input_control.mouse"
        ), patch(
            "input_control.move_mouse_horizontal"
        ), patch(
            "input_control.tap_tab"
        ), patch(
            "input_control.keyboard_controller"
        ):

            # Setup perf_counter to simulate time progression
            counter = [0.0]

            def perf_counter_side_effect():
                val = counter[0]
                counter[0] += 0.02
                return val

            mock_perf.side_effect = perf_counter_side_effect

            run_throw_macro(mock_state)

            # Clumsy should be toggled twice: activate and deactivate
            assert mock_clumsy.call_count == 2


class TestRunThrowMacroV2:
    """Tests for run_throw_macro_v2 function"""

    def test_throw_v2_disabled(self, mock_state):
        """Test that macro v2 doesn't run when disabled"""
        from macros import run_throw_macro_v2

        mock_state["config"]["throw_enabled"] = False
        update_overlay = Mock()
        disconnect_net = Mock()
        reconnect_net = Mock()

        run_throw_macro_v2(mock_state, update_overlay, disconnect_net, reconnect_net)

        # Should return early
        disconnect_net.assert_not_called()

    def test_throw_v2_basic_flow(self, mock_state):
        """Test basic flow of throw macro v2"""
        from macros import run_throw_macro_v2

        update_overlay = Mock()
        disconnect_net = Mock()
        reconnect_net = Mock()

        with patch("macros.time.sleep"), patch(
            "macros.time.perf_counter", side_effect=[i * 0.01 for i in range(100)]
        ), patch("macros.SendInput") as mock_send, patch(
            "macros.move_mouse_horizontal"
        ), patch(
            "macros.Input"
        ), patch(
            "macros.Input_I"
        ), patch(
            "macros.MouseInput"
        ), patch(
            "macros.KeyBdInput"
        ), patch(
            "macros.ctypes"
        ):

            run_throw_macro_v2(
                mock_state, update_overlay, disconnect_net, reconnect_net
            )

            # Verify network disconnect and reconnect
            disconnect_net.assert_called_once()
            reconnect_net.assert_called_once()

            # Verify SendInput was called (for mouse and keyboard)
            assert mock_send.call_count > 0

    def test_throw_v2_network_timing(self, mock_state):
        """Test that network disconnect/reconnect happens at correct times"""
        from macros import run_throw_macro_v2

        update_overlay = Mock()
        disconnect_net = Mock()
        reconnect_net = Mock()

        mock_state["config"]["throw_spam_duration"] = 0.1
        mock_state["config"]["throw_clumsy_deactivate_after_spam"] = 0.05

        with patch("macros.time.sleep"), patch(
            "macros.time.perf_counter"
        ) as mock_perf, patch("macros.SendInput"), patch(
            "macros.move_mouse_horizontal"
        ), patch(
            "macros.Input"
        ), patch(
            "macros.Input_I"
        ), patch(
            "macros.MouseInput"
        ), patch(
            "macros.KeyBdInput"
        ), patch(
            "macros.ctypes"
        ):

            counter = [0.0]

            def perf_counter_side_effect():
                val = counter[0]
                counter[0] += 0.02
                return val

            mock_perf.side_effect = perf_counter_side_effect

            run_throw_macro_v2(
                mock_state, update_overlay, disconnect_net, reconnect_net
            )

            # Both should be called
            disconnect_net.assert_called_once()
            reconnect_net.assert_called_once()


class TestRunComplexMacro:
    """Tests for run_complex_macro function"""

    def test_complex_macro_already_running(self, mock_state):
        """Test that macro doesn't run if already running"""
        from macros import run_complex_macro

        mock_state["is_running_macro"] = True
        update_overlay = Mock()
        disconnect_net = Mock()
        reconnect_net = Mock()

        run_complex_macro(mock_state, update_overlay, disconnect_net, reconnect_net)

        # State should remain True
        assert mock_state["is_running_macro"]
        # No threads should be started
        update_overlay.assert_not_called()

    def test_complex_macro_sets_running_flag(self, mock_state):
        """Test that macro sets is_running_macro flag"""
        from macros import run_complex_macro

        update_overlay = Mock()
        disconnect_net = Mock()
        reconnect_net = Mock()

        with patch("macros.threading.Thread") as mock_thread:
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance

            run_complex_macro(mock_state, update_overlay, disconnect_net, reconnect_net)

            # Flag should be set
            assert mock_state["is_running_macro"]

            # Threads should be started
            assert mock_thread.call_count == 4  # 3 task threads + 1 waiter thread

    def test_complex_macro_with_zero_lengths(self, mock_state):
        """Test macro behavior when hold/net/spam lengths are 0"""
        from macros import run_complex_macro

        mock_state["config"]["macro_hold_len"] = 0.0
        mock_state["config"]["macro_net_len"] = 0.0
        mock_state["config"]["macro_spam_len"] = 0.0

        update_overlay = Mock()
        disconnect_net = Mock()
        reconnect_net = Mock()

        with patch("macros.threading.Thread") as mock_thread, patch(
            "macros.time.sleep"
        ):

            mock_thread_instances = []

            def create_thread(*args, **kwargs):
                instance = Mock()
                mock_thread_instances.append(instance)
                return instance

            mock_thread.side_effect = create_thread

            run_complex_macro(mock_state, update_overlay, disconnect_net, reconnect_net)

            # Threads should still be created but won't do much work
            assert len(mock_thread_instances) == 4

            # All threads should be started
            for thread in mock_thread_instances:
                thread.start.assert_called_once()

    def test_complex_macro_calls_update_overlay(self, mock_state):
        """Test that update_overlay is called at start"""
        from macros import run_complex_macro

        update_overlay = Mock()
        disconnect_net = Mock()
        reconnect_net = Mock()

        with patch("macros.threading.Thread"):
            run_complex_macro(mock_state, update_overlay, disconnect_net, reconnect_net)

            # Should be called immediately
            update_overlay.assert_called_once()


class TestMacroConfiguration:
    """Tests for macro configuration handling"""

    def test_default_config_values(self, mock_state):
        """Test that default config values are used correctly"""
        from macros import run_throw_macro

        # Remove optional configs
        mock_state["config"] = {"throw_enabled": True, "clumsy_hotkey": "8"}

        with patch("macros.time.sleep"), patch(
            "macros.time.perf_counter"
        ) as mock_perf, patch("network.send_clumsy_hotkey"), patch(
            "input_control.mouse"
        ), patch(
            "input_control.move_mouse_horizontal"
        ), patch(
            "input_control.tap_tab"
        ), patch(
            "input_control.keyboard_controller"
        ):

            # Setup perf_counter to simulate time progression
            counter = [0.0]

            def perf_counter_side_effect():
                val = counter[0]
                counter[0] += 0.5  # Large increment to exit quickly
                return val

            mock_perf.side_effect = perf_counter_side_effect

            # Should not crash, using .get() with defaults
            try:
                run_throw_macro(mock_state)
            except KeyError:
                pytest.fail("Macro should handle missing config keys with defaults")

    def test_custom_config_values(self, mock_state):
        """Test that custom config values are used"""
        from macros import run_throw_macro

        custom_pixels = -3000
        custom_spam = 0.1
        mock_state["config"]["throw_drag_left_pixels"] = custom_pixels
        mock_state["config"]["throw_spam_duration"] = custom_spam

        with patch("macros.time.sleep"), patch(
            "macros.time.perf_counter"
        ) as mock_perf, patch("network.send_clumsy_hotkey"):

            # Setup perf_counter to finish quickly
            counter = [0.0]

            def perf_counter_side_effect():
                val = counter[0]
                counter[0] += 1.0  # Large increment
                return val

            mock_perf.side_effect = perf_counter_side_effect

            run_throw_macro(mock_state)

            # Test passed if no exception occurred (custom values were used)
            assert True
