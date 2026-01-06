"""
Unit tests for configuration functions in config.py
"""

import pytest
import os
import sys
import json
import tempfile
from unittest.mock import patch

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def temp_config_file():
    """Create a temporary config file"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        yield f.name
    # Cleanup
    if os.path.exists(f.name):
        os.unlink(f.name)


class TestLoadConfig:
    """Tests for load_config function"""

    def test_load_config_file_exists(self, temp_config_file):
        """Test loading config when file exists"""
        from config import load_config, state, DEFAULT_CONFIG

        # Create a test config
        test_config = {
            "click_cps": 25,
            "key_macro_trigger": "Key.f2",
        }

        with open(temp_config_file, "w") as f:
            json.dump(test_config, f)

        with patch("config.CONFIG_FILE", temp_config_file):
            load_config()

            # Should load custom values
            assert state["config"]["click_cps"] == 25
            assert state["config"]["key_macro_trigger"] == "Key.f2"

            # Should still have default values for missing keys
            assert "net_interface" in state["config"]

    def test_load_config_file_not_exists(self):
        """Test loading config when file doesn't exist"""
        from config import load_config, state, DEFAULT_CONFIG

        with patch("config.CONFIG_FILE", "/nonexistent/path/config.json"):
            with patch("config.os.path.exists", return_value=False):
                load_config()

                # Should use default config
                assert state["config"] == DEFAULT_CONFIG.copy()

    def test_load_config_invalid_json(self, temp_config_file):
        """Test loading config with invalid JSON"""
        from config import load_config, state, DEFAULT_CONFIG

        # Write invalid JSON
        with open(temp_config_file, "w") as f:
            f.write("{ invalid json }")

        with patch("config.CONFIG_FILE", temp_config_file):
            load_config()

            # Should fall back to default config
            assert state["config"] == DEFAULT_CONFIG.copy()

    def test_load_config_merges_with_defaults(self, temp_config_file):
        """Test that loaded config is merged with defaults"""
        from config import load_config, state, DEFAULT_CONFIG

        # Create partial config
        partial_config = {
            "click_cps": 30,
        }

        with open(temp_config_file, "w") as f:
            json.dump(partial_config, f)

        with patch("config.CONFIG_FILE", temp_config_file):
            load_config()

            # Should have custom value
            assert state["config"]["click_cps"] == 30

            # Should have all default values for missing keys
            for key in DEFAULT_CONFIG:
                assert key in state["config"]


class TestSaveConfig:
    """Tests for save_config function"""

    def test_save_config_creates_file(self, temp_config_file):
        """Test that save_config creates a file"""
        from config import save_config, state

        state["config"] = {
            "click_cps": 20,
            "key_macro_trigger": "Key.f3",
        }

        with patch("config.CONFIG_FILE", temp_config_file):
            save_config()

            # File should exist
            assert os.path.exists(temp_config_file)

            # Should contain the config
            with open(temp_config_file, "r") as f:
                loaded = json.load(f)
                assert loaded["click_cps"] == 20
                assert loaded["key_macro_trigger"] == "Key.f3"

    def test_save_config_updates_mtime(self, temp_config_file):
        """Test that save_config updates the modification time tracking"""
        from config import save_config, state

        state["config"] = {"test": "value"}

        with patch("config.CONFIG_FILE", temp_config_file):
            save_config()

            # Should have updated the mtime
            assert state["config_last_modified"] > 0


class TestCheckConfigReload:
    """Tests for check_config_reload function"""

    def test_check_config_reload_file_modified(self, temp_config_file):
        """Test that config is reloaded when file is modified"""
        from config import check_config_reload, load_config, state

        # Initial load
        initial_config = {"click_cps": 10}
        with open(temp_config_file, "w") as f:
            json.dump(initial_config, f)

        with patch("config.CONFIG_FILE", temp_config_file):
            load_config()
            initial_mtime = state["config_last_modified"]

            # Modify file
            import time

            time.sleep(0.01)  # Ensure different mtime
            updated_config = {"click_cps": 20}
            with open(temp_config_file, "w") as f:
                json.dump(updated_config, f)

            # Check reload
            result = check_config_reload()

            # Should have reloaded
            assert result == True
            assert state["config"]["click_cps"] == 20
            assert state["config_last_modified"] > initial_mtime

    def test_check_config_reload_file_not_modified(self, temp_config_file):
        """Test that config is not reloaded when file hasn't changed"""
        from config import check_config_reload, load_config, state

        config = {"click_cps": 15}
        with open(temp_config_file, "w") as f:
            json.dump(config, f)

        with patch("config.CONFIG_FILE", temp_config_file):
            load_config()

            # Check reload without modifying file
            result = check_config_reload()

            # Should not have reloaded
            assert result == False

    def test_check_config_reload_file_not_exists(self):
        """Test check_config_reload when file doesn't exist"""
        from config import check_config_reload

        with patch("config.CONFIG_FILE", "/nonexistent/config.json"):
            with patch("config.os.path.exists", return_value=False):
                result = check_config_reload()

                # Should return False without error
                assert result == False


class TestDefaultConfig:
    """Tests for DEFAULT_CONFIG values"""

    def test_default_config_has_required_keys(self):
        """Test that DEFAULT_CONFIG has all required keys"""
        from config import DEFAULT_CONFIG

        required_keys = [
            "click_cps",
            "key_macro_trigger",
            "net_interface",
            "macro_enabled",
            "throw_enabled",
            "recording_enabled",
        ]

        for key in required_keys:
            assert key in DEFAULT_CONFIG, f"Missing required key: {key}"

    def test_default_config_types(self):
        """Test that DEFAULT_CONFIG values have correct types"""
        from config import DEFAULT_CONFIG

        # Check some key types
        assert isinstance(DEFAULT_CONFIG["click_cps"], int)
        assert isinstance(DEFAULT_CONFIG["macro_hold_start"], (int, float))
        assert isinstance(DEFAULT_CONFIG["macro_enabled"], bool)
        assert isinstance(DEFAULT_CONFIG["key_macro_trigger"], str)


class TestState:
    """Tests for state object"""

    def test_state_initial_values(self):
        """Test that state has correct initial values"""
        from config import state

        assert state["is_lagging"] == False
        assert state["is_running_macro"] == False
        assert state["is_recording"] == False
        assert isinstance(state["config"], dict)
        assert isinstance(state["recorded_actions"], list)

    def test_state_has_required_keys(self):
        """Test that state has all required keys"""
        from config import state

        required_keys = [
            "is_lagging",
            "is_running_macro",
            "config",
            "is_recording",
            "recorded_actions",
        ]

        for key in required_keys:
            assert key in state, f"Missing required key: {key}"


class TestConfigIntegration:
    """Integration tests for config module"""

    def test_save_and_load_roundtrip(self, temp_config_file):
        """Test that save and load work together correctly"""
        from config import save_config, load_config, state

        # Set custom config
        state["config"] = {
            "click_cps": 42,
            "key_macro_trigger": "Key.f9",
            "macro_enabled": False,
        }

        with patch("config.CONFIG_FILE", temp_config_file):
            # Save
            save_config()

            # Modify state
            state["config"]["click_cps"] = 99

            # Load
            load_config()

            # Should have loaded the saved value
            assert state["config"]["click_cps"] == 42
            assert state["config"]["key_macro_trigger"] == "Key.f9"
            assert state["config"]["macro_enabled"] == False

    def test_config_modification_detection(self, temp_config_file):
        """Test that external config modifications are detected"""
        from config import load_config, check_config_reload, state

        initial = {"click_cps": 5}
        with open(temp_config_file, "w") as f:
            json.dump(initial, f)

        with patch("config.CONFIG_FILE", temp_config_file):
            load_config()
            assert state["config"]["click_cps"] == 5

            # Simulate external modification
            import time

            time.sleep(0.01)
            updated = {"click_cps": 15}
            with open(temp_config_file, "w") as f:
                json.dump(updated, f)

            # Should detect and reload
            reloaded = check_config_reload()
            assert reloaded == True
            assert state["config"]["click_cps"] == 15
