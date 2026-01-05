# ARC Dupe Macro - Refactored

This project has been refactored from a single `macro.py` file into multiple organized modules for better maintainability and code organization.

## File Structure

### Main Entry Point

- **main.py** - Application entry point with dependency checking and initialization

### Core Modules

- **config.py** - Configuration management (loading/saving settings and state)
- **network.py** - Network operations (disconnect/reconnect, interface detection, admin checks)
- **input_control.py** - Low-level keyboard and mouse control using ctypes and pynput
- **macros.py** - Macro execution logic (complex macro and throw macro)
- **recording.py** - Recording and playback functionality for input sequences
- **hotkeys.py** - Hotkey event handlers for triggering macros and recordings
- **gui.py** - GUI components (App window, Overlay, HackerButton, and all UI logic)

## Running the Application

To run the application, use:

```bash
python main.py
```

This will:

1. Check for required dependencies (pynput, psutil)
2. Request admin privileges (required for network operations)
3. Load configuration and recordings
4. Start keyboard and mouse listeners
5. Launch the GUI

## Module Dependencies

```txt
main.py
├── config.py (state management)
├── network.py
│   ├── input_control.py (for ctypes structures)
│   └── psutil
├── input_control.py
│   └── pynput
├── recording.py
│   └── input_control.py
├── macros.py
│   ├── input_control.py
│   └── network.py
├── hotkeys.py
│   └── pynput
└── gui.py
    └── tkinter
```

## Key Features

- **Timeline-based macro system** - Coordinate multiple actions with precise timing
- **Network lag simulation** - Disconnect/reconnect network or use Clumsy
- **Input recording & playback** - Record and replay keyboard/mouse sequences
- **Throw macro** - Specialized macro for specific game actions
- **Overlay status** - Draggable overlay showing macro and network status

## Configuration

Settings are stored in `macro_config.json` and include:

- Hotkey bindings
- Network interface selection
- Macro timing parameters
- Recording settings
- Overlay position

## Notes

- Requires Windows OS (uses netsh and Windows-specific APIs)
- Requires administrator privileges for network operations
- Recording files are saved in the `recordings/` directory
