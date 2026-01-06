# Quick Start Guide - New Features

## 🎯 What's New

### Settings Window
- **Access**: Click the gear icon (⚙) in the top-right corner of the main window
- **Features**: 
  - Tabbed interface for organized settings
  - Timeline Macro tab: Configure hold, network, and spam click timings
  - Throw Macro tab: Configure all throw macro timing parameters
  - Recording tab: Placeholder for future recording settings

### Simplified Main UI
The main interface now shows only essential controls:
- Network method and interface selection
- Trigger keys for macros
- Disconnect timing mode
- Clicks per second (CPS) slider
- Enable/Disable toggles for macros
- Basic action buttons

### Live Reload
- The application automatically detects changes to `macro_config.json`
- Changes are reloaded every second
- You'll see a console message when config is reloaded
- Edit the config file directly for quick adjustments

## 📋 How to Use

1. **Configure Basic Settings**
   - Use the main window for network setup and trigger keys
   - Adjust CPS slider for click speed
   - Enable/disable individual macros

2. **Configure Trigger Keys**
   - **F3**: Timeline Macro (default)
   - **F4**: Throw Macro V1 (default)
   - **F7**: Throw Macro V2 (default) - Uses robust SendInput API
   - **F5**: Start/Stop Recording (default)
   - **F6**: Playback Recording (default)

3. **Configure Timing Parameters**
   - Click the gear icon (⚙)
   - Navigate to the appropriate tab
   - Adjust timing values as needed
   - Click "SAVE SETTINGS"

4. **Manual Config Editing**
   - Edit `macro_config.json` directly
   - Application will automatically reload changes
   - Useful for batch updates or version control

## 🔧 Settings Tabs

### Timeline Macro Tab
Configure the 3-phase macro sequence:
- **Hold Click**: Start delay and duration
- **Network**: Start delay and offline time
- **Spam Click**: Start delay and duration

### Throw Macro Tab
Fine-tune throw macro timing:
- **Timing Delays**: Pre/post delays for each phase
- **Tap Timing**: Clumsy and Tab tap delays
- **Key Dwell Times**: How long keys are held
- **Spam Settings**: Duration and period
- **Drag Settings**: Time and distance

**Note**: Both Throw Macro V1 and V2 share the same timing parameters.

### Throw Macro Versions
- **V1 (F4)**: Original implementation using pynput library
- **V2 (F7)**: New implementation using Windows SendInput API (more robust)

See `THROW_MACRO_V2.md` for detailed comparison.

## 💡 Tips

- Keep the settings window open while testing for quick adjustments
- Use live reload to test changes without restarting
- Main UI stays simple - all advanced settings in gear menu
- Settings window is always on top for easy access

## 🐛 Troubleshooting

If settings don't apply:
1. Check console for error messages
2. Verify `macro_config.json` is valid JSON
3. Ensure all timing values are numbers (not text)
4. Click "SAVE SETTINGS" after making changes in settings window

If live reload isn't working:
1. Check file permissions on `macro_config.json`
2. Verify the file exists in the application directory
3. Look for reload messages in the console

## 📝 Configuration Keys

All timing parameters are stored in `macro_config.json`:
- `macro_hold_start`, `macro_hold_len`
- `macro_net_start`, `macro_net_len`
- `macro_spam_start`, `macro_spam_len`
- `throw_*` (14 different throw timing parameters)

See `IMPLEMENTATION_SUMMARY.md` for complete list of configuration keys.
