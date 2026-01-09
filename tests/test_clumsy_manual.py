#!/usr/bin/env python
"""Test script for Clumsy startup"""

from config import state, load_config
from network import start_clumsy
import time

load_config()
print(f'clumsy_auto_start: {state["config"].get("clumsy_auto_start")}')
print(f'clumsy_exe_path: {state["config"].get("clumsy_exe_path")}')

# Test start_clumsy
print("\nTesting start_clumsy...")
result = start_clumsy(state)
print(f"start_clumsy result: {result}")

if state.get("clumsy_process"):
    print(f'Clumsy PID: {state["clumsy_process"].pid}')
    # Warte ein bisschen und beende es
    time.sleep(2)
    state["clumsy_process"].terminate()
    print("Clumsy terminated")
else:
    print("ERROR: Clumsy process not started!")
