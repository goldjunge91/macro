## Plan: Python-Skript für EXE-Kompilierung erstellen

Erstelle ein Build-Skript mit PyInstaller, um macro.py in eine eigenständige .exe zu kompilieren, wobei Abhängigkeiten wie pynput, tkinter, ctypes und subprocess behandelt werden, mit Optionen für One-File-Ausgabe, versteckte Imports und Daten-Dateien für die Windows-Verteilung. Die exe soll macro_config.json lesen können, und das Skript soll ein virtuelles venv am Ausführungsort erstellen.

### Schritte
1. Erstelle ein virtuelles Environment am Ausführungsort und installiere PyInstaller und Abhängigkeiten über pip.
2. Erstelle [build_exe.py](build_exe.py) mit PyInstaller-API-Aufrufen für macro.py, einschließlich macro_config.json als Daten für das Lesen.
3. Füge versteckte Imports für pynput hinzu.
4. Führe build_exe.py aus, um macro.exe im dist-Ordner zu generieren.
5. Teste die exe auf einem sauberen Windows-Rechner auf Funktionalität, stelle sicher, dass sie macro_config.json lesen kann.

### Weitere Überlegungen
1. Verwende --windowed für GUI, um die Konsole zu verbergen.
2. Stelle sicher, dass Administratorrechte für Systemoperationen in der exe vorhanden sind.
3. Option A: PyInstaller / Option B: cx_Freeze bei Problemen.
