import os
import sys
import subprocess


def main():
    # Schritt 1: Virtuelles Environment erstellen, falls nicht vorhanden
    if not os.path.exists("venv"):
        print("Erstelle virtuelles Environment...")
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])

    # Pfad zum venv Python
    venv_python = (
        os.path.join("venv", "Scripts", "python.exe")
        if os.name == "nt"
        else os.path.join("venv", "bin", "python")
    )

    # Installiere PyInstaller und Abhängigkeiten
    print("Installiere PyInstaller und pynput...")
    subprocess.check_call(
        [venv_python, "-m", "pip", "install", "pyinstaller", "pynput"]
    )

    # Schritt 2-3: PyInstaller ausführen mit Optionen
    print("Kompiliere macro.py zu exe...")
    args = [
        "macro.py",
        "--onefile",
        "--windowed",
        "--name",
        "macro",
        "--distpath",
        "./dist",
        "--workpath",
        "./build",
        "--hidden-import",
        "pynput.keyboard",
        "--hidden-import",
        "pynput.mouse",
    ]

    # Füge macro_config.json als Daten hinzu, falls vorhanden
    if os.path.exists("macro_config.json"):
        args.extend(["--add-data", "macro_config.json;."])

    # Führe PyInstaller aus
    subprocess.check_call([venv_python, "-m", "PyInstaller"] + args)

    print("EXE erfolgreich erstellt in ./dist/macro.exe")


if __name__ == "__main__":
    main()
