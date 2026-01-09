# Macro Test Suite

This directory contains comprehensive unit tests for the macro application.

## Test Coverage

### test_config.py (15 tests)
Tests for configuration management:
- Loading and saving configuration
- Merging with default values
- Configuration file modification detection
- State initialization

### test_macros.py (13 tests)
Tests for macro functions:
- `run_throw_macro()` - Throw macro v1 functionality
- `run_throw_macro_v2()` - Throw macro v2 functionality
- `run_complex_macro()` - Complex macro with timing
- Configuration handling and custom values

### test_recording.py (27 tests)
Tests for recording and playback:
- Key and mouse button conversion utilities
- Recording start/stop functionality
- Action recording and tracking
- Saving and loading recordings
- Playback functionality

## Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run specific test file:
```bash
pytest tests/test_macros.py
```

### Run with verbose output:
```bash
pytest tests/ -v
```

### Run specific test:
```bash
pytest tests/test_macros.py::TestRunThrowMacro::test_throw_macro_basic_flow
```

## Requirements

- pytest >= 9.0.2
- pytest-mock >= 3.15.1

These are automatically installed when you run:
```bash
pip install -r requirements.txt
```

## Test Design

The tests use mocking to isolate functionality and avoid dependencies on:
- Display server (X11) for pynput
- Windows-specific APIs (SendInput, ctypes.windll)
- Network operations

This allows tests to run on any platform including CI/CD environments.

## Notes

- Tests mock external dependencies to ensure they can run in headless environments
- Configuration tests use temporary files to avoid affecting real config
- Recording tests use temporary directories for test data
- All tests are independent and can run in any order
