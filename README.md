# ARC Raider Macro tool

A simple macro/tool for duplicating Snitch Scanners in ARC Raiders using a network lag simulation technique (disconnect/reconnect timing to interrupt the throw action).
How It Works
This exploits a desync glitch by briefly simulating network issues during the throw animation, causing the server to register the animation but not the item drop—resulting in a duplicate spawning on the ground.

Network Interface Detection
The tool now supports both WiFi and Ethernet connections with automatic detection:

- **Auto-Detection**: Scans for active network interfaces with internet connectivity using psutil
- **Interface Type Recognition**: Automatically identifies WiFi vs Ethernet interfaces
- **Dropdown Selection**: Choose from detected active interfaces in the UI
- **Smart Disconnect/Reconnect**:
  - WiFi: Uses `netsh wlan disconnect` and reconnects to saved SSID
  - Ethernet: Uses `netsh interface disable/enable`
- **Refresh Button**: Manually refresh the list of available interfaces

Setup & Usage

Equip the Snitch Scanner in your hand.
Go in-game to a safe area (or test in practice area).
**Select your active network interface** from the dropdown (auto-detected on first run).
Press the trigger key (default: F3) to run the macro.

Tuning the Timings
You'll need to adjust the Network Start Delay and Network Offline Time for your system and connection:

Recommended starting values: Start Delay = 0.75s, Offline Time = 2.5s
These work well for many, but vary by PC specs, ping, and network type (WiFi vs Ethernet).

Testing Process:

Run the macro a few times.
If the Snitch Scanner fully drops to the floor (and you lose it), timings are too off—reduce offline time or increase delay.
Goal: It should only play the throw animation without actually dropping the item.
Once that's consistent, fine-tune slightly until duplicates appear (two Scanners spawn on the floor).
Success rate is ~90% with perfect timings—always test 2-3 runs per adjustment, as results can vary slightly.

Requirements

- Python 3.7+
- pynput (auto-installed)
- psutil (auto-installed)
- Windows OS with admin privileges (required for network commands)
