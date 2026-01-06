# Throw Macro V2 - Implementation Details

## Overview
Throw Macro V2 is an alternative implementation of the throw macro that uses the robust input methods from `run_complex_macro` instead of the pynput library methods.

## Key Differences

### Throw Macro V1 (Original)
- Uses `pynput.keyboard.Controller` for keyboard input
- Uses `pynput.mouse.Controller` for mouse input
- Uses `send_clumsy_hotkey()` directly for network control
- Lightweight and simple

### Throw Macro V2 (New)
- Uses Windows `SendInput` API via ctypes for keyboard input
- Uses Windows `SendInput` API via ctypes for mouse input
- Uses `disconnect_net()` and `reconnect_net()` wrapper functions
- More robust and closer to native Windows input
- Better integration with the state management system

## Technical Implementation

### Input Methods
**Keyboard Input (V2):**
```python
# E key press using SendInput
ii_ = Input_I()
ii_.ki = KeyBdInput(E_KEYCODE, 0, 0, 0, ctypes.pointer(extra))
SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input))
# Release
ii_.ki = KeyBdInput(E_KEYCODE, 0, 0x0002, 0, ctypes.pointer(extra))
SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input))
```

**Mouse Input (V2):**
```python
# Mouse button down using SendInput
ii_ = Input_I()
ii_.mi = MouseInput(0, 0, 0, 0x0002, 0, ctypes.pointer(extra))
SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))
# Mouse button up
ii_.mi = MouseInput(0, 0, 0, 0x0004, 0, ctypes.pointer(extra))
SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))
```

**Network Control (V2):**
```python
# Uses the proper state management wrappers
disconnect_net()  # Activates Clumsy or netsh
reconnect_net()   # Deactivates Clumsy or netsh
```

## Sequence Flow

Both versions follow the same sequence:

1. **Initial Settle** (0.03s default)
2. **Network Disconnect** (Clumsy activate)
3. **Pre-Drag Delay** (0.06s default)
4. **Mouse Drag** (0.5s, -2000 pixels left)
5. **Post-Drag Delay** (0.3s default)
6. **Tab Press** (0.02s dwell)
7. **E-Spam Start** (2.25s duration)
8. **Network Reconnect** (0.20s after spam starts)
9. **E-Spam Continue** (until duration complete)
10. **Final Settle** (0.05s default)

## Configuration

### Trigger Key
- **Config Key:** `key_throw_v2_trigger`
- **Default:** `Key.f7`
- **Configurable via GUI:** Main window

### Enable/Disable
- **Config Key:** `throw_v2_enabled` (for future use)
- **Default:** `true`

### Timing Parameters
All timing parameters are shared between V1 and V2:
- `throw_start_settle_delay`
- `throw_pre_drag_delay`
- `throw_tab_delay_after_drag`
- `throw_final_settle_delay`
- `throw_post_tab_to_spam_delay`
- `throw_post_clumsy_tap_delay`
- `throw_post_tab_tap_delay`
- `throw_clumsy_deactivate_after_spam`
- `throw_tab_dwell`
- `throw_e_dwell`
- `throw_spam_duration`
- `throw_e_period`
- `throw_drag_time`
- `throw_drag_left_pixels`

## Advantages of V2

1. **More Robust Input:** SendInput is the recommended Windows API for programmatic input
2. **Better State Management:** Uses existing disconnect/reconnect wrappers with state tracking
3. **Consistent with Timeline Macro:** Uses same input methods as `run_complex_macro`
4. **Network Method Agnostic:** Works with both Clumsy and netsh through wrappers
5. **Better Error Handling:** Integrated with the state management system

## Usage

1. Set trigger key in main GUI (default F7)
2. Configure timing parameters in Settings window (gear icon)
3. Press F7 (or configured key) to execute
4. Monitor console for execution logs

## Console Output

```
>> THROW MACRO V2: STARTING
>> THROW V2: ACTIVATING CLUMSY
>> THROW V2: DRAG START
>> THROW V2: DRAG COMPLETE
>> THROW V2: TAB PRESS
>> THROW V2: E-SPAM START
>> THROW V2: DEACTIVATING CLUMSY
>> THROW V2: E-SPAM COMPLETE
>> THROW MACRO V2: COMPLETE (2.567s)
```

## When to Use Which Version?

**Use V1 (Original) when:**
- You prefer the pynput library methods
- You have compatibility issues with SendInput
- You want minimal overhead

**Use V2 (New) when:**
- You need more robust input simulation
- You want consistency with timeline macro behavior
- You need better integration with state management
- You're experiencing timing or reliability issues with V1

## Future Enhancements

Potential additions for V2:
- Separate enable/disable toggle in GUI
- Independent timing parameters from V1
- Additional phases or sequences
- Multi-threaded execution like timeline macro
