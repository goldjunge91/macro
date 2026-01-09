"""
Unit tests for Clumsy integration in network.py
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import with conftest mocks
from network import start_clumsy, stop_clumsy, is_clumsy_running


class TestClumsyFunctions:
    """Tests for Clumsy integration functions"""

    def test_start_clumsy_exists(self):
        """Verify start_clumsy function exists and is callable"""
        assert callable(start_clumsy)

    def test_stop_clumsy_exists(self):
        """Verify stop_clumsy function exists and is callable"""
        assert callable(stop_clumsy)

    def test_is_clumsy_running_exists(self):
        """Verify is_clumsy_running function exists and is callable"""
        assert callable(is_clumsy_running)

    def test_start_clumsy_already_running(self):
        """Test start_clumsy returns True when process already running"""
        mock_process = MagicMock()
        state = {
            "config": {"clumsy_exe_path": "bin/clumsy.exe"},
            "clumsy_process": mock_process,
        }

        # Mock function should return True if already running
        result = start_clumsy(state)
        assert result is True

    def test_stop_clumsy_no_process(self):
        """Test stop_clumsy returns True when no process"""
        state = {"clumsy_process": None}

        # Mock function should return True
        result = stop_clumsy(state)
        assert result is True

    def test_is_clumsy_running_no_process(self):
        """Test is_clumsy_running returns False when no process"""
        state = {"clumsy_process": None}

        # Mock function should return False
        result = is_clumsy_running(state)
        assert result is False
