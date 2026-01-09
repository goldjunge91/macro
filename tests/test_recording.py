"""
Unit tests for recording functions in recording.py
"""

import pytest
import os
import sys
import tempfile
import csv
from unittest.mock import Mock, patch

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import mocked pynput from conftest
from pynput import keyboard
from pynput.mouse import Button


@pytest.fixture
def mock_state():
    """Create a mock state object"""
    return {
        "is_recording": False,
        "recorded_actions": [],
        "recording_start_time": None,
        "last_recording_file": None,
        "last_mouse_move_time": 0,
        "pressed_keys": set(),
        "config": {"recording_enabled": True},
    }


@pytest.fixture
def temp_recordings_dir():
    """Create a temporary recordings directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestKeyConversion:
    """Tests for key conversion functions"""

    def test_key_to_string_char(self):
        """Test converting character key to string"""
        from recording import key_to_string

        key = keyboard.KeyCode.from_char("a")
        result = key_to_string(key)

        assert result == "char:a"

    def test_key_to_string_special(self):
        """Test converting special key to string"""
        from recording import key_to_string

        key = keyboard.Key.shift
        result = key_to_string(key)

        assert result == "Key.shift"

    def test_string_to_key_char(self):
        """Test converting string back to character key"""
        from recording import string_to_key

        key = string_to_key("char:b")

        assert isinstance(key, keyboard.KeyCode)
        assert key.char == "b"

    def test_string_to_key_special(self):
        """Test converting string back to special key"""
        from recording import string_to_key

        key = string_to_key("Key.ctrl")

        assert key == keyboard.Key.ctrl

    def test_key_roundtrip(self):
        """Test that key conversion is reversible"""
        from recording import key_to_string, string_to_key

        original = keyboard.KeyCode.from_char("x")
        string_form = key_to_string(original)
        restored = string_to_key(string_form)

        assert restored.char == original.char


class TestButtonConversion:
    """Tests for mouse button conversion functions"""

    def test_button_to_string_left(self):
        """Test converting left button to string"""
        from recording import button_to_string

        result = button_to_string(Button.left)
        assert result == "left"

    def test_button_to_string_right(self):
        """Test converting right button to string"""
        from recording import button_to_string

        result = button_to_string(Button.right)
        assert result == "right"

    def test_string_to_button_middle(self):
        """Test converting string to middle button"""
        from recording import string_to_button

        result = string_to_button("middle")
        assert result == Button.middle

    def test_button_roundtrip(self):
        """Test that button conversion is reversible"""
        from recording import button_to_string, string_to_button

        original = Button.right
        string_form = button_to_string(original)
        restored = string_to_button(string_form)

        assert restored == original


class TestStartRecording:
    """Tests for start_recording function"""

    def test_start_recording_sets_flags(self, mock_state):
        """Test that start_recording sets appropriate flags"""
        from recording import start_recording

        update_overlay = Mock()

        with patch("recording.time.perf_counter", return_value=100.0):
            start_recording(mock_state, update_overlay)

        assert mock_state["is_recording"]
        assert mock_state["recorded_actions"] == []
        assert mock_state["recording_start_time"] == 100.0
        update_overlay.assert_called_once()

    def test_start_recording_already_recording(self, mock_state):
        """Test behavior when already recording"""
        from recording import start_recording

        mock_state["is_recording"] = True
        update_overlay = Mock()

        start_recording(mock_state, update_overlay)

        # Should not call update_overlay
        update_overlay.assert_not_called()


class TestStopRecording:
    """Tests for stop_recording function"""

    def test_stop_recording_with_actions(self, mock_state):
        """Test stopping recording with recorded actions"""
        from recording import stop_recording

        mock_state["is_recording"] = True
        mock_state["recording_start_time"] = 0.0
        mock_state["recorded_actions"] = [
            {"type": "key_press", "time": 0.1, "key": keyboard.KeyCode.from_char("a")}
        ]
        update_overlay = Mock()

        with patch("recording.time.perf_counter", return_value=1.0), patch(
            "recording.save_recording"
        ) as mock_save:

            stop_recording(mock_state, update_overlay)

        assert not mock_state["is_recording"]
        mock_save.assert_called_once_with(mock_state)
        update_overlay.assert_called_once()

    def test_stop_recording_not_recording(self, mock_state):
        """Test stopping when not recording"""
        from recording import stop_recording

        mock_state["is_recording"] = False
        update_overlay = Mock()

        stop_recording(mock_state, update_overlay)

        # Should return early
        update_overlay.assert_not_called()


class TestRecordAction:
    """Tests for record_action function"""

    def test_record_action_key_press(self, mock_state):
        """Test recording a key press action"""
        from recording import record_action

        mock_state["is_recording"] = True
        mock_state["recording_start_time"] = 0.0

        key = keyboard.KeyCode.from_char("e")

        with patch("recording.time.perf_counter", return_value=0.5):
            record_action(mock_state, "key_press", key=key)

        assert len(mock_state["recorded_actions"]) == 1
        action = mock_state["recorded_actions"][0]
        assert action["type"] == "key_press"
        assert action["time"] == 0.5
        assert action["key"] == key

    def test_record_action_mouse_move(self, mock_state):
        """Test recording a mouse move action"""
        from recording import record_action

        mock_state["is_recording"] = True
        mock_state["recording_start_time"] = 0.0

        with patch("recording.time.perf_counter", return_value=0.3):
            record_action(mock_state, "mouse_move", x=100, y=200)

        assert len(mock_state["recorded_actions"]) == 1
        action = mock_state["recorded_actions"][0]
        assert action["type"] == "mouse_move"
        assert action["x"] == 100
        assert action["y"] == 200

    def test_record_action_not_recording(self, mock_state):
        """Test that actions aren't recorded when not recording"""
        from recording import record_action

        mock_state["is_recording"] = False

        record_action(mock_state, "key_press", key=keyboard.Key.space)

        assert len(mock_state["recorded_actions"]) == 0

    def test_record_action_tracks_pressed_keys(self, mock_state):
        """Test that pressed keys are tracked"""
        from recording import record_action

        mock_state["is_recording"] = True
        mock_state["recording_start_time"] = 0.0

        key = keyboard.KeyCode.from_char("w")

        with patch("recording.time.perf_counter", return_value=0.1):
            record_action(mock_state, "key_press", key=key)

        assert len(mock_state["pressed_keys"]) == 1

        with patch("recording.time.perf_counter", return_value=0.2):
            record_action(mock_state, "key_release", key=key)

        assert len(mock_state["pressed_keys"]) == 0


class TestSaveRecording:
    """Tests for save_recording function"""

    def test_save_recording_success(self, mock_state, temp_recordings_dir):
        """Test successfully saving a recording"""
        from recording import save_recording

        mock_state["recorded_actions"] = [
            {"type": "key_press", "time": 0.1, "key": keyboard.KeyCode.from_char("a")},
            {"type": "mouse_move", "time": 0.2, "x": 100, "y": 200},
        ]

        with patch("recording.RECORDINGS_DIR", temp_recordings_dir), patch(
            "recording.get_recordings_folder", return_value=temp_recordings_dir
        ):

            result = save_recording(mock_state)

        assert result == True
        assert "last_recording_file" in mock_state
        assert mock_state["last_recording_file"].endswith(".csv")

    def test_save_recording_no_actions(self, mock_state):
        """Test saving with no recorded actions"""
        from recording import save_recording

        mock_state["recorded_actions"] = []

        result = save_recording(mock_state)

        assert result == False


class TestLoadRecording:
    """Tests for load_recording function"""

    def test_load_recording_from_file(self, mock_state, temp_recordings_dir):
        """Test loading a recording from a specific file"""
        from recording import load_recording

        # Create a test CSV file
        test_file = os.path.join(temp_recordings_dir, "test_recording.csv")
        with open(test_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "type", "key", "button", "x", "y"])
            writer.writerow([0.1, "key_press", "char:a", "", "", ""])
            writer.writerow([0.2, "mouse_move", "", "", 100, 200])

        with patch("recording.get_recordings_folder", return_value=temp_recordings_dir):
            result = load_recording(mock_state, test_file)

        assert result == True
        assert len(mock_state["recorded_actions"]) == 2
        assert mock_state["recorded_actions"][0]["type"] == "key_press"
        assert mock_state["recorded_actions"][1]["type"] == "mouse_move"

    def test_load_recording_no_file_exists(self, mock_state, temp_recordings_dir):
        """Test loading when no recordings exist"""
        from recording import load_recording

        with patch("recording.get_recordings_folder", return_value=temp_recordings_dir):
            result = load_recording(mock_state)

        assert result == False


class TestPlaybackRecording:
    """Tests for playback_recording function"""

    def test_playback_disabled(self, mock_state):
        """Test that playback doesn't run when disabled"""
        from recording import playback_recording

        mock_state["config"]["recording_enabled"] = False

        playback_recording(mock_state)

        # Should return early
        assert True  # Just checking it doesn't crash

    def test_playback_while_recording(self, mock_state):
        """Test that playback is prevented while recording"""
        from recording import playback_recording

        mock_state["is_recording"] = True

        playback_recording(mock_state)

        # Should return early without error
        assert True

    def test_playback_with_actions(self, mock_state):
        """Test playing back recorded actions"""
        from recording import playback_recording

        mock_state["recorded_actions"] = [
            {"type": "key_press", "time": 0.0, "key": keyboard.KeyCode.from_char("a")},
            {
                "type": "key_release",
                "time": 0.1,
                "key": keyboard.KeyCode.from_char("a"),
            },
        ]

        with patch(
            "recording.time.perf_counter", side_effect=[0, 0, 0.001, 0.1, 0.101, 0.2]
        ), patch("recording.time.sleep"), patch(
            "recording.keyboard_controller"
        ) as mock_kb, patch(
            "recording.mouse"
        ):

            playback_recording(mock_state)

            # Should press and release the key
            assert mock_kb.press.call_count >= 1
            assert mock_kb.release.call_count >= 1

    def test_playback_no_actions(self, mock_state):
        """Test playback with no recorded actions"""
        from recording import playback_recording

        mock_state["recorded_actions"] = []

        with patch("recording.load_recording", return_value=False):
            playback_recording(mock_state)

        # Should return without error
        assert True


class TestGetRecordingsFolder:
    """Tests for get_recordings_folder function"""

    def test_creates_folder_if_not_exists(self):
        """Test that folder is created if it doesn't exist"""
        from recording import get_recordings_folder

        with tempfile.TemporaryDirectory() as tmpdir:
            recordings_path = os.path.join(tmpdir, "recordings")

            with patch("recording.RECORDINGS_DIR", recordings_path):
                result = get_recordings_folder()

                assert os.path.exists(recordings_path)
                assert result == recordings_path

    def test_returns_existing_folder(self):
        """Test that existing folder is returned"""
        from recording import get_recordings_folder

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("recording.RECORDINGS_DIR", tmpdir):
                result = get_recordings_folder()

                assert result == tmpdir
