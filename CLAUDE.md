# CLAUDE.md - Zinkwell Project Guide

## Project Overview

**Zinkwell** is a Python SDK for controlling Zink-based mini photo printers via Bluetooth. Currently supports Canon Ivy 2, with architecture designed to support additional printers (Kodak Snap, etc.).

## Tech Stack

- **Language:** Python 3.8+
- **Dependencies:**
  - `loguru` - Structured logging
  - `Pillow` - Image processing
  - Native Python `socket` with `AF_BLUETOOTH` (Windows/Linux)

## Project Structure

```
zinkwell/
├── __init__.py                 # Package entry point, exports get_printer()
├── factory.py                  # get_printer() factory function
├── exceptions.py               # All exception types
├── models/                     # Data models
│   ├── __init__.py
│   ├── status.py               # PrinterStatus, PrinterInfo
│   └── capabilities.py         # PrinterCapabilities
├── devices/                    # Printer implementations
│   ├── __init__.py             # Device registry
│   ├── base.py                 # Abstract Printer class
│   └── canon_ivy2/             # Canon Ivy 2 implementation
│       ├── __init__.py
│       ├── printer.py          # CanonIvy2Printer
│       ├── protocol.py         # Protocol tasks, message format
│       └── image.py            # Image preparation
├── bluetooth/                  # Transport layer
│   ├── __init__.py             # get_transport() factory
│   ├── base.py                 # Abstract BluetoothTransport
│   └── native.py               # Python socket implementation
└── utils/                      # Shared utilities
    ├── __init__.py
    └── threading.py            # ThreadedClient utility

tests/
├── conftest.py
├── mocks.py                    # MockTransport for testing
├── unit/                       # Fast isolated tests
├── contract/                   # Interface compliance tests
├── integration/                # Component interaction tests
└── hardware/                   # Real device tests (skipped in CI)
```

## Architecture

**Three-layer design:**

```
User Code
    ↓
get_printer("canon_ivy2", "AA:BB:CC:DD:EE:FF")
    ↓
┌─────────────────────────────────────────────┐
│  Layer 1: Printer Interface (devices/base)  │
│  - Abstract Printer class                   │
│  - PrinterStatus, PrinterInfo, Capabilities │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  Layer 2: Device Implementations            │
│  - CanonIvy2Printer                         │
│  - Protocol logic, image preparation        │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  Layer 3: Bluetooth Transport               │
│  - NativeTransport (socket.AF_BLUETOOTH)    │
│  - ThreadedClient utility                   │
└─────────────────────────────────────────────┘
```

### Protocol Details (Canon Ivy 2)

- **Transport:** Bluetooth RFCOMM (port 1)
- **Packet Size:** 34 bytes
- **Start Code:** 17167 (0x430F)
- **Image Chunk Size:** 990 bytes
- **Min Battery:** 30%

## Cheat Sheet

### Installation

```bash
# Install dependencies
pip install -e .

# Or manually
pip install loguru pillow
```

### Running Tests

```bash
# Run all tests (except hardware)
pytest tests/ -v --ignore=tests/hardware

# Run with coverage (terminal report)
pytest tests/ --cov=zinkwell --cov-report=term-missing --ignore=tests/hardware

# Run with coverage (HTML report)
pytest tests/ --cov=zinkwell --cov-report=html --ignore=tests/hardware
# Open htmlcov/index.html in browser

# Run with coverage (all reports: terminal, HTML, XML)
pytest tests/ --cov=zinkwell --cov-report=term-missing --cov-report=html --cov-report=xml --ignore=tests/hardware

# Run only unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v
```

### Usage

```python
from zinkwell import get_printer

# Create printer
printer = get_printer("canon_ivy2", "AA:BB:CC:DD:EE:FF")

# Connect and use
printer.connect()
status = printer.get_status()
print(f"Battery: {status.battery_level}%")

if status.is_ready:
    printer.print("photo.jpg")

printer.disconnect()

# Or use context manager
with get_printer("canon_ivy2", "AA:BB:CC:DD:EE:FF") as printer:
    printer.print("photo.jpg")
```

### Listing Supported Printers

```python
from zinkwell import list_supported_printers

for name, info in list_supported_printers().items():
    print(f"{name}: {info.name}")
```

## Platform-Specific Setup

### Windows

Python's native `socket.AF_BLUETOOTH` works out of the box. No additional setup required.

```bash
# Verify Bluetooth support
python -c "import socket; s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM); print('OK')"
```

### Linux/Raspberry Pi

```bash
# Install system dependencies
sudo apt install bluetooth bluez libbluetooth-dev python3-dev

# Ensure Bluetooth service is running
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Pair printer
bluetoothctl
> scan on
> pair XX:XX:XX:XX:XX:XX
> trust XX:XX:XX:XX:XX:XX
> exit
```

### macOS

Not currently supported (requires PyObjC + IOBluetooth bridge).

## Testing on Different Platforms

### Phase 3: Cross-Platform Testing Checklist

To verify the native transport works on Linux/Pi:

1. **Basic connectivity test:**
   ```bash
   pytest tests/unit/bluetooth/test_native.py -v
   ```

2. **Full test suite:**
   ```bash
   pytest tests/ -v --ignore=tests/hardware
   ```

3. **Hardware test (requires paired printer):**
   ```bash
   # Set PRINTER_ADDRESS environment variable
   export PRINTER_ADDRESS="AA:BB:CC:DD:EE:FF"
   pytest tests/hardware/ -v
   ```

### Known Platform Differences

| Feature | Windows | Linux/Pi | macOS |
|---------|---------|----------|-------|
| Native socket BT | ✅ | ✅ | ❌ |
| PyBluez fallback | N/A | ✅ | ❌ |
| BLE support | ❌ | Future | ❌ |

## Development Notes

- **Testing:** 114 tests (unit + contract + integration)
- **Coverage:** 91% (run `pytest --cov=zinkwell` to check)
- **Threading:** Device-level with shared ThreadedClient utility
- **Logging:** `loguru` at DEBUG/ERROR levels
- **Auto-disconnect:** 30 seconds of inactivity

### Coverage Reports

Coverage tracking is configured in `pyproject.toml`. Reports available:
- **Terminal:** `--cov-report=term-missing` (shows missing lines)
- **HTML:** `--cov-report=html` (generates `htmlcov/index.html`)
- **XML:** `--cov-report=xml` (generates `coverage.xml` for CI integration)
