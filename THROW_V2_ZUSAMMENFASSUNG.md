# Throw Macro V2 - Zusammenfassung

## Was wurde erstellt?

Eine zweite Version des Throw-Macros, die die robusten Input-Methoden aus dem `run_complex_macro` verwendet.

## Hauptunterschiede

### Throw Macro V1 (Original - F4)
- Verwendet `pynput.keyboard.Controller` und `pynput.mouse.Controller`
- Ruft `send_clumsy_hotkey()` direkt auf
- Einfach und leichtgewichtig
- Originalimplementierung

### Throw Macro V2 (Neu - F7)
- Verwendet Windows `SendInput` API via ctypes
- Nutzt `disconnect_net()` und `reconnect_net()` Wrapper
- Robuster und näher am nativen Windows-Input
- Gleiche Sequenz wie V1
- Bessere Integration mit State-Management

## Gleiche Abfolge

Beide Versionen führen die gleiche Sequenz aus:

1. **Start Settle** → Stabilisierung
2. **Clumsy aktivieren** → Network disconnect
3. **Pre-Drag Delay** → Kurze Pause
4. **Drag** → Maus nach links ziehen (Button gedrückt)
5. **Drag complete** → Button loslassen
6. **Tab Delay** → Wartezeit nach Drag
7. **Tab drücken** → Tab-Taste mit Dwell-Time
8. **E-Spam starten** → E-Taste spammen
9. **Clumsy deaktivieren** → Nach 0.20s während Spam
10. **E-Spam fortsetzen** → Bis zur vollen Dauer
11. **Final Settle** → Abschluss

## Verwendete Methoden aus run_complex_macro

### Maus-Button Drücken/Loslassen
```python
# Button Down (0x0002)
ii_ = Input_I()
ii_.mi = MouseInput(0, 0, 0, 0x0002, 0, ctypes.pointer(extra))
SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))

# Button Up (0x0004)
ii_.mi = MouseInput(0, 0, 0, 0x0004, 0, ctypes.pointer(extra))
SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(0), ii_)), ctypes.sizeof(Input))
```

### Tastendruck (E und Tab)
```python
# Key Down
ii_ = Input_I()
ii_.ki = KeyBdInput(KEYCODE, 0, 0, 0, ctypes.pointer(extra))
SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input))

# Key Up (0x0002 flag)
ii_.ki = KeyBdInput(KEYCODE, 0, 0x0002, 0, ctypes.pointer(extra))
SendInput(1, ctypes.pointer(Input(ctypes.c_ulong(1), ii_)), ctypes.sizeof(Input))
```

### Network Control
```python
# Clumsy aktivieren
disconnect_net()  # Wrapper-Funktion mit State-Management

# Clumsy deaktivieren  
reconnect_net()   # Wrapper-Funktion mit State-Management
```

### Maus-Bewegung
```python
# Verwendet move_mouse_horizontal() aus input_control.py
move_mouse_horizontal(KEY_DRAG_LEFT_PIXELS, duration=KEY_DRAG_TIME, steps=50)
```

## Integration

### Config (config.py)
- Neuer Key: `key_throw_v2_trigger` (Standard: "Key.f7")
- Neues Flag: `throw_v2_enabled` (Standard: True)
- Teilt alle Timing-Parameter mit V1

### GUI (gui.py)
- Neues Combobox-Feld für V2 Trigger-Key
- Speichert V2 Trigger in Config
- Info-Text: "Uses robust input method (SendInput)"

### Hotkeys (hotkeys.py)
- Neuer Parameter `run_throw_macro_v2`
- Prüft `key_throw_v2_trigger`
- Startet V2 in eigenem Thread

### Main (main.py)
- Importiert `run_throw_macro_v2`
- Wrapper-Funktion für V2 mit allen Abhängigkeiten
- Übergibt state, update_overlay, disconnect_net, reconnect_net

### Macros (macros.py)
- Neue Funktion `run_throw_macro_v2()`
- Verwendet KeyBdInput und MouseInput
- Verwendet TAB_KEYCODE (0x09) und E_KEYCODE (0x45)
- Console-Logs mit ">> THROW V2:" Präfix

## Vorteile von V2

1. **Robustere Eingabe**: SendInput ist die empfohlene Windows-API
2. **Besseres State-Management**: Nutzt disconnect/reconnect Wrapper
3. **Konsistent mit Timeline Macro**: Gleiche Input-Methoden
4. **Netzwerk-Methoden-agnostisch**: Funktioniert mit Clumsy und netsh
5. **Bessere Integration**: Ins State-Management-System eingebunden

## Trigger-Keys Übersicht

| Taste | Makro | Methode |
|-------|-------|---------|
| F3 | Timeline Macro | SendInput (3 Threads) |
| F4 | Throw V1 | pynput |
| F7 | Throw V2 | SendInput (sequentiell) |
| F5 | Record | - |
| F6 | Playback | - |

## Console-Ausgabe

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

## Konfiguration

Alle Timing-Parameter werden in den Settings (⚙ Gear Icon) unter dem "Throw Macro" Tab konfiguriert und gelten für beide Versionen (V1 und V2).

## Testen

1. Anwendung starten
2. F7 drücken (oder konfigurierten V2 Trigger)
3. Console-Ausgabe beobachten
4. Sequenz sollte identisch zu F4 ablaufen
5. Timing-Parameter in Settings anpassen falls nötig

## Dateien

- **THROW_MACRO_V2.md** - Detaillierte technische Dokumentation (Englisch)
- **THROW_V2_ZUSAMMENFASSUNG.md** - Diese Datei (Deutsch)
- **IMPLEMENTATION_SUMMARY.md** - Aktualisiert mit V2 Info
- **QUICK_START.md** - Aktualisiert mit V2 Info
