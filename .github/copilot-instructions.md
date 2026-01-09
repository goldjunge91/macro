# ARC Dupe Macro - AI Coding Agent Instructions

## Project Overview

ARC Dupe Macro is a Windows-based automation tool that records and replays game input sequences with precise timing control. It provides specialized macros for network lag simulation and complex sequential actions (e.g., precise "throw" mechanics in games).

**Key Purpose**: Automate repetitive game actions with sub-millisecond timing precision and network state manipulation.

## Architecture & Data Flow

### Modular Structure
- **main.py** → Entry point; checks dependencies, requests admin, initializes system
- **config.py** → Centralized state management (loaded from `macro_config.json`)
- **input_control.py** → Low-level Windows API (ctypes/SendInput) and pynput wrappers
- **network.py** → Network interface detection, disconnect/reconnect via netsh/Clumsy
- **macros.py** → Timeline-based macro execution (throw macro, complex macro)
- **recording.py** → Record/playback input sequences to CSV
- **hotkeys.py** → Keyboard event handlers; triggers macros from pynput listeners
- **gui.py** → Tkinter UI with overlay, settings window, status display

### State Flow
1. `config.py` maintains shared `state` dict passed to all modules
2. Hotkey listeners in **hotkeys.py** detect triggers (F3, F4, F5, F6, F7)
3. Macro/recording functions update `state["is_recording"]`, timing parameters
4. Network operations (`network.py`) modify system state via netsh/Clumsy
5. GUI reflects state changes in real-time

### Critical Dependencies
- **pynput** (7.6+) - Cross-platform keyboard/mouse listeners and control
- **psutil** (5.9+) - Network interface detection (required for admin privilege check)
- **pyinstaller** (6.0+) - Builds standalone .exe (build process: `build_exe.py`)

## Key Patterns & Conventions

### Timing-Critical Operations
The **throw macro** is timeline-based; each parameter defines a delay offset:
```python
throw_start_settle_delay = 0.03      # Initial pause after F4 press
throw_tab_delay_after_drag = 0.3     # After mouse drag completes
throw_spam_duration = 2.25            # Total e-key repetition time
```
**Pattern**: Config values are millisecond-level delays extracted in macro functions. When modifying timings, preserve the offset-based structure—don't refactor into absolute timestamps without coordination.

### Network Manipulation Methods
- **"Clumsy" mode**: External tool; hotkey triggers `send_clumsy_hotkey()` (config: `clumsy_hotkey`)
- **"netsh" mode**: Direct command-line network disconnect/reconnect
- **Config field**: `network_method` selects strategy; mock in tests

### Configuration Pattern
All editable settings live in `macro_config.json` with defaults in `config.py::DEFAULT_CONFIG`. When adding features:
1. Add key to `DEFAULT_CONFIG` with sensible default
2. Access via `state["config"].get("key_name", fallback)`
3. Reload detection: `check_config_reload()` watches file mtime

### Input Recording Format
CSV files in `recordings/` with columns: `[action_type, key_or_button, x, y, timestamp]`
- **Example row**: `key_press, a, , , 0.05` (key 'a' pressed 50ms into recording)
- **Conversion**: `keycode_to_key_string()` converts pynput KeyCode → JSON-safe strings

### Mocking for Testing
Tests run cross-platform via comprehensive mocks in `tests/conftest.py`:
- pynput's keyboard/mouse listeners can't run on headless Linux; mocked to avoid X11 dependency
- Windows ctypes APIs (SendInput, windll) mocked to prevent platform failures
- **Run tests**: `python run_tests.py` or `pytest tests/ -v`
- **All 55 tests passing**: config (15), macros (13), recording (27)

## Developer Workflows

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python main.py          # Will request admin privileges

# Run test suite (55 tests)
python run_tests.py     # Or: pytest tests/ -v
```

### Building Standalone .exe
```bash
# Creates dist/macro.exe
python build_exe.py
```

### Configuration Management
- Edit `macro_config.json` directly (app auto-detects changes via `check_config_reload()`)
- Settings window (GUI) modifies config JSON; changes persist immediately

### Adding New Macros
1. Define timing parameters in `DEFAULT_CONFIG` (config.py)
2. Implement `run_new_macro(state)` in macros.py
3. Add hotkey trigger in hotkeys.py (`on_key_press()`)
4. Write tests in `tests/test_macros.py` using mocks

## Platform Requirements & Constraints

- **Windows-only**: Uses netsh, ctypes.windll, Windows-specific APIs
- **Admin privileges required**: Network operations demand elevated permissions
- **Timing precision**: Sub-50ms accuracy needed; respect sleep/threading limits
- **GUI**: Tkinter (cross-platform but tested on Windows)

## Code Output Guidelines

**Never create Markdown documentation files** for task summaries, INTEGRATION summarys,  comparisons, refactoring summaries, change logs, or similar unless explicitly requested. Focus on direct code implementation and inline comments. Examples of files NOT to create:
- Task summary reports
- Integration summaries
- Refactoring documentation
- Before/after comparisons
- Change analysis files

## Common Modifications

### Adjusting Macro Timing
Modify delays in `macro_config.json`; app reloads automatically. Don't hardcode timestamps in macros.py—use config lookups.

### Adding a New Hotkey
1. Add config key in `DEFAULT_CONFIG` (e.g., `"new_trigger": "Key.f8"`)
2. Parse key in `on_key_press()` (hotkeys.py) using `parse_key_string()`
3. Call your function in a thread: `threading.Thread(target=run_new_macro).start()`

### Recording Files Location
All recordings saved to `recordings/` directory as CSV. Playback reads from same directory.

## Testing Strategy

- **Isolation**: Each test is independent; fixtures reset state between tests
- **Mocking**: All platform-specific code mocked to run anywhere
- **Coverage**: Normal flows, edge cases, error handling tested
- **Speed**: Complete suite runs in <0.15 seconds

## File References for Key Patterns

- [config.py](config.py) - State management and config defaults
- [macros.py](macros.py#L1-L50) - Timeline-based macro structure
- [input_control.py](input_control.py#L1-L50) - Windows ctypes definitions
- [tests/conftest.py](tests/conftest.py) - Mocking strategy
- [hotkeys.py](hotkeys.py#L1-L40) - Hotkey parsing and threading pattern
