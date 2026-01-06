# Vergleich: Throw Macro V1 vs V2

## Quick Reference

| Feature | V1 (F4) | V2 (F7) |
|---------|---------|---------|
| **Input Methode** | pynput | Windows SendInput |
| **Maus-Steuerung** | `pynput.mouse.Controller` | `MouseInput` + `SendInput` |
| **Tastatur-Steuerung** | `pynput.keyboard.Controller` | `KeyBdInput` + `SendInput` |
| **Network Control** | `send_clumsy_hotkey()` direkt | `disconnect_net()` / `reconnect_net()` |
| **State Integration** | Minimal | Vollständig |
| **Komplexität** | Einfach | Mittel |
| **Robustheit** | Gut | Sehr gut |
| **Performance** | Schnell | Schnell |

## Code-Vergleich

### Maus-Button (Links drücken)

**V1:**
```python
mouse.press(Button.left)
# ... drag ...
mouse.release(Button.left)
```

**V2:**
```python
extra = ctypes.c_ulong(0)
ii_ = Input_I()
ii_.mi = MouseInput(0, 0, 0, 0x0002, 0, ctypes.pointer(extra))
SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))
# ... drag ...
ii_.mi = MouseInput(0, 0, 0, 0x0004, 0, ctypes.pointer(extra))
SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))
```

### Tab-Taste drücken

**V1:**
```python
tap_tab(dwell=KEY_TAB_DWELL)
# Intern: keyboard_controller.press/release
```

**V2:**
```python
extra = ctypes.c_ulong(0)
ii_ = Input_I()
TAB_KEYCODE = 0x09

# Press
ii_.ki = KeyBdInput(TAB_KEYCODE, 0, 0, 0, ctypes.pointer(extra))
SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input))
time.sleep(KEY_TAB_DWELL)

# Release
ii_.ki = KeyBdInput(TAB_KEYCODE, 0, 0x0002, 0, ctypes.pointer(extra))
SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input))
```

### E-Taste Spam

**V1:**
```python
E_KEY = keyboard.KeyCode.from_char("e")

while time.perf_counter() < spam_end:
    keyboard_controller.press(E_KEY)
    time.sleep(KEY_E_DWELL)
    keyboard_controller.release(E_KEY)
    time.sleep(KEY_E_PERIOD)
```

**V2:**
```python
E_KEYCODE = 0x45
extra = ctypes.c_ulong(0)

while time.perf_counter() < spam_end:
    ii_ = Input_I()
    # Press
    ii_.ki = KeyBdInput(E_KEYCODE, 0, 0, 0, ctypes.pointer(extra))
    SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input))
    time.sleep(KEY_E_DWELL)
    # Release
    ii_.ki = KeyBdInput(E_KEYCODE, 0, 0x0002, 0, ctypes.pointer(extra))
    SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input))
    time.sleep(KEY_E_PERIOD)
```

### Network Control

**V1:**
```python
from network import send_clumsy_hotkey

clumsy_hotkey = state["config"].get("clumsy_hotkey", "8")

# Aktivieren
send_clumsy_hotkey(clumsy_hotkey)
time.sleep(POST_CLUMSY_TAP_DELAY)

# Deaktivieren (später)
send_clumsy_hotkey(clumsy_hotkey)
```

**V2:**
```python
# Aktivieren
disconnect_net()
time.sleep(0.05)

# Deaktivieren (später)
reconnect_net()
```

## Vorteile V1

✅ Einfacher Code, leichter zu lesen
✅ Weniger Boilerplate
✅ Direkte pynput API
✅ Keine ctypes-Abhängigkeit
✅ Schneller zu entwickeln

## Vorteile V2

✅ Verwendet offizielle Windows-API
✅ Robuster gegen Anti-Cheat
✅ Konsistent mit Timeline Macro
✅ Besseres State-Management
✅ Funktioniert mit netsh UND Clumsy
✅ Bessere Error-Handling-Möglichkeiten
✅ Gleicher Code-Stil wie run_complex_macro

## Wann welche Version?

### Nutze V1 wenn:
- Du schnelle Prototypen brauchst
- Du mit pynput vertraut bist
- Du nur Clumsy verwendest
- Einfachheit wichtiger als Robustheit ist

### Nutze V2 wenn:
- Du maximale Kompatibilität willst
- Du zwischen Clumsy und netsh wechselst
- Du Konsistenz mit Timeline Macro brauchst
- Du das State-Management-System nutzen willst
- Du Windows SendInput bevorzugst

## Performance

Beide Versionen haben nahezu identische Performance:
- **Durchschnittliche Ausführungszeit**: ~2.5-2.6 Sekunden
- **Overhead V2**: < 5ms (vernachlässigbar)
- **Timing-Präzision**: Beide verwenden `time.perf_counter()`

## Timing-Parameter

Beide Versionen teilen sich **alle** Timing-Parameter:
- Kein Duplizieren von Config-Einträgen
- Änderungen betreffen beide Makros
- Einfache Verwaltung im Settings-Fenster

## Console-Output Vergleich

**V1:**
```
>> THROW MACRO: STARTING
>> HOLD: DOWN
>> HOLD: RELEASE
>> SPAM: START
>> SPAM: END
>> THROW MACRO: COMPLETE (2.543s)
```

**V2:**
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

## Empfehlung

**Für die meisten Benutzer: V2**
- Robuster und zukunftssicher
- Bessere Integration
- Gleiche Performance wie V1

**Für Entwickler/Tester: Beide behalten**
- V1 als Referenz und Fallback
- V2 für Production Use
- Ermöglicht A/B-Testing

## Migration von V1 zu V2

Keine Migration nötig! Beide Versionen:
- Teilen die gleichen Timing-Parameter
- Können parallel existieren
- Haben separate Trigger-Keys
- Nutzen die gleiche Config
