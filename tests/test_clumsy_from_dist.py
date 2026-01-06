#!/usr/bin/env python
"""Test Clumsy startup from dist directory"""

import sys
import os

sys.path.insert(0, "c:\\GIT\\arc-dupe-macro")

from config import state, load_config
from network import start_clumsy
import time

load_config()
print("=== Testing from dist directory ===")
print(f"Current dir: {os.getcwd()}")
print(f'clumsy_exe_path: {state["config"].get("clumsy_exe_path")}')

result = start_clumsy(state)
print(f"Result: {result}")

if state.get("clumsy_process"):
    print(f'Clumsy PID: {state["clumsy_process"].pid}')
    time.sleep(2)
    state["clumsy_process"].terminate()
    print("Terminated")
else:
    print("ERROR: Clumsy not started")
