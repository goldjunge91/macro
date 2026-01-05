import os
import sys
import subprocess
import shutil
import json
from pathlib import Path


class BuildConfig:
    """Configuration für den Build-Prozess"""

    PROJECT_ROOT = Path(__file__).parent
    ENTRY_POINT = "main.py"
    APP_NAME = "macro"
    CONFIG_FILE = "macro_config.json"


def get_venv_python():
    """Gibt den Pfad zum venv Python Interpreter zurück"""
    venv_dir = BuildConfig.PROJECT_ROOT / "venv"
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    else:
        return venv_dir / "bin" / "python"


def validate_prerequisites():
    """Validiert, dass Entry Point und Config-Datei vorhanden sind"""
    print("[1/5] Validiere Projekt...")

    entry = BuildConfig.PROJECT_ROOT / BuildConfig.ENTRY_POINT
    if not entry.exists():
        print(f"✗ Entry Point nicht gefunden: {entry}")
        return False
    print(f"✓ Entry Point validiert: {entry}")

    config_path = BuildConfig.PROJECT_ROOT / BuildConfig.CONFIG_FILE
    if config_path.exists():
        try:
            with open(config_path) as f:
                json.load(f)
            print(f"✓ Config-Datei validiert")
        except json.JSONDecodeError as e:
            print(f"✗ Config-Datei ist ungültiges JSON: {e}")
            return False
    else:
        print(f"⚠ Config-Datei nicht gefunden: {config_path}")

    return True


def clean_build_artifacts():
    """Bereinigt alte Build-Artefakte"""
    print("[2/5] Bereinige alte Artefakte...")
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        dir_path = BuildConfig.PROJECT_ROOT / dir_name
        if dir_path.exists():
            try:
                if dir_path.is_dir():
                    shutil.rmtree(dir_path)
                    print(f"✓ Gelöscht: {dir_name}/")
            except Exception as e:
                print(f"⚠ Konnte nicht löschen {dir_name}: {e}")


def create_venv():
    """Erstellt virtuelles Environment mit Error-Handling"""
    print("[3/5] Richte Python-Umgebung ein...")
    venv_dir = BuildConfig.PROJECT_ROOT / "venv"
    if venv_dir.exists():
        print("✓ Virtuelles Environment existiert bereits")
        return True

    try:
        print("→ Erstelle virtuelles Environment...")
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)], timeout=30)
        print("✓ Virtuelles Environment erstellt")
        return True
    except subprocess.TimeoutExpired:
        print("✗ Fehler: venv-Erstellung hat zu lange gedauert")
        return False
    except Exception as e:
        print(f"✗ Fehler beim Erstellen von venv: {e}")
        return False


def install_dependencies(venv_python):
    """Installiert Abhängigkeiten mit Error-Handling"""
    print("[4/5] Installiere Abhängigkeiten...")

    try:
        subprocess.check_call(
            [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], timeout=60
        )

        subprocess.check_call(
            [
                str(venv_python),
                "-m",
                "pip",
                "install",
                "pyinstaller>=6.0.0",
                "pynput>=1.7.6",
                "psutil>=5.9.0",
            ],
            timeout=120,
        )
        print("✓ Abhängigkeiten installiert")
        return True
    except subprocess.TimeoutExpired:
        print("✗ Fehler: Installation hat zu lange gedauert")
        return False
    except subprocess.CalledProcessError as e:
        print(f"✗ Fehler beim Installieren: {e}")
        return False


def build_with_pyinstaller(venv_python):
    """Führt PyInstaller mit erweiterten Optionen aus"""
    print("[5/5] Kompiliere mit PyInstaller...")

    args = [
        str(BuildConfig.PROJECT_ROOT / BuildConfig.ENTRY_POINT),
        "--onefile",
        "--windowed",
        "--name",
        BuildConfig.APP_NAME,
        "--distpath",
        "./dist",
        "--workpath",
        "./build",
        "--hidden-import=pynput.keyboard",
        "--hidden-import=pynput.mouse",
        "--hidden-import=psutil",
    ]

    # Config-Datei hinzufügen
    config_path = BuildConfig.PROJECT_ROOT / BuildConfig.CONFIG_FILE
    if config_path.exists():
        args.extend(["--add-data", f"{BuildConfig.CONFIG_FILE}{os.pathsep}."])

    try:
        print(f"→ Starte PyInstaller mit Entry Point: {BuildConfig.ENTRY_POINT}")
        subprocess.check_call(
            [str(venv_python), "-m", "PyInstaller"] + args,
            cwd=BuildConfig.PROJECT_ROOT,
            timeout=300,
        )
        print(f"✓ EXE erfolgreich erstellt: ./dist/{BuildConfig.APP_NAME}.exe")
        return True
    except subprocess.TimeoutExpired:
        print("✗ Fehler: PyInstaller-Prozess hat zu lange gedauert")
        return False
    except subprocess.CalledProcessError as e:
        print(f"✗ Fehler: PyInstaller hat Fehler zurückgegeben (Code: {e.returncode})")
        return False


def main():
    """Hauptablauf mit vollständiger Error-Behandlung"""
    print("=" * 60)
    print("ARC Dupe Macro - Build-Prozess")
    print("=" * 60)
    print()

    if not validate_prerequisites():
        return False
    print()

    clean_build_artifacts()
    print()

    if not create_venv():
        return False
    print()

    venv_python = get_venv_python()
    if not install_dependencies(venv_python):
        return False
    print()

    if not build_with_pyinstaller(venv_python):
        return False

    print()
    print("=" * 60)
    print("✓ Build-Prozess erfolgreich abgeschlossen!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
