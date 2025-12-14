# CLAUDE.md - Project Guide

## Project Overview

**Ivy2** is a Python API/SDK for controlling the Canon Ivy 2 mini photo printer via Bluetooth. It enables programmatic printing, printer status queries, and configuration management.

## Tech Stack

- **Language:** Python 3
- **Dependencies:**
  - `loguru` (0.6.0) - Structured logging
  - `Pillow` (9.5.0) - Image processing
  - `PyBluez` - Bluetooth communication (installed from git)

## Project Structure

```
├── ivy2.py           # Main printer API - Ivy2Printer class
├── client.py         # Bluetooth communication thread handler
├── task.py           # Protocol task implementations
├── image.py          # Image processing and preparation
├── utils.py          # Utility functions (bit parsing, message parsing)
├── exceptions.py     # Custom exception definitions
├── example.py        # Usage examples
├── assets/
│   └── test_image.jpg
└── old/              # Deprecated code
```

## Architecture

**Layered, protocol-driven design:**

```
User Code
    ↓
Ivy2Printer API (ivy2.py)      → High-level methods: print(), get_status(), etc.
    ↓
Task objects (task.py)          → Protocol message generation (34-byte packets)
    ↓
ClientThread (client.py)        → Queue-based Bluetooth I/O thread
    ↓
Bluetooth RFCOMM                → Port 1 connection to printer
```

### Key Components

| Module | Purpose |
|--------|---------|
| `ivy2.py` | Public API - `Ivy2Printer` class with `connect()`, `print()`, `get_status()`, `get_setting()`, `set_setting()`, `reboot()` |
| `client.py` | `ClientThread` - Threading-based Bluetooth socket manager with queue-based message passing |
| `task.py` | Task classes for each command: `StartSessionTask`, `GetStatusTask`, `GetSettingTask`, `SetSettingTask`, `GetPrintReadyTask`, `RebootTask` |
| `image.py` | `prepare_image()` - Converts images to printer format (1280x1920 → 640x1616, rotated 180°) |
| `exceptions.py` | `LowBatteryError`, `CoverOpenError`, `NoPaperError`, `WrongSmartSheetError`, `ClientUnavailableError`, `ReceiveTimeoutError`, `AckError` |

### Protocol Details

- **Transport:** Bluetooth RFCOMM (port 1)
- **Packet Size:** 34 bytes
- **Start Code:** 17167 (0x430F)
- **Image Chunk Size:** 990 bytes
- **Min Battery:** 30%

## Cheat Sheet

### Setup Commands

```bash
# Install system dependencies (Raspberry Pi)
sudo apt install bluetooth bluez libbluetooth-dev

# Install Python dependencies
pip install -r requirements.txt

# Install PyBluez from source
pip install git+https://github.com/pybluez/pybluez.git#egg=pybluez
```

### Running the Example

```bash
# Set your printer MAC address in example.py, then:
python example.py
```

### Usage in Code

```python
from ivy2 import Ivy2Printer

printer = Ivy2Printer("XX:XX:XX:XX:XX:XX")
printer.connect()

# Check status
status = printer.get_status()

# Print an image
printer.print("path/to/image.jpg")

printer.disconnect()
```

### Image Preview (Development)

```python
from example import preview_image
preview_image("image.jpg")  # Generates preview_image.jpeg
```

### Bluetooth Pairing (Raspberry Pi)

```bash
bluetoothctl
# > scan on
# > pair XX:XX:XX:XX:XX:XX
# > trust XX:XX:XX:XX:XX:XX
# > exit
```

## Development Notes

- No test suite or build scripts - pure Python library
- Image processing uses PIL/Pillow with LANCZOS resampling
- Logging via `loguru` at DEBUG/ERROR levels
- Threading model: single background thread for all Bluetooth I/O
- 30-second auto-disconnect on inactivity
