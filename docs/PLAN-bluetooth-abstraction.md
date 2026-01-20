# Multi-Printer Bluetooth Architecture Plan

## Executive Summary

This document outlines a plan to:
1. Abstract the Bluetooth communication layer for cross-platform support (Windows, Linux/Pi, macOS)
2. Create a device abstraction layer to support multiple printer types (Canon Ivy 2, Kodak, etc.)
3. Provide a simple, unified API for end users

---

## Research Findings

### Bluetooth Platform Support

| Platform | Option | Status | Notes |
|----------|--------|--------|-------|
| **Windows** | Python `socket` module | ✅ Verified | Native `AF_BLUETOOTH` + `BTPROTO_RFCOMM` |
| **Linux/Pi** | Python `socket` module | ✅ Should Work | Same API as Windows |
| **Linux/Pi** | PyBluez | ✅ Current | Works but unmaintained |
| **macOS** | PyObjC + IOBluetooth | ⚠️ Future | Requires Objective-C bridge |

### Printer Protocol Comparison

| Printer | Transport | Packet Size | Image Format | Protocol Complexity |
|---------|-----------|-------------|--------------|---------------------|
| Canon Ivy 2 | BT RFCOMM | 34 bytes | 640x1616 JPEG, rotated 180° | Medium - session, status, settings |
| Kodak/Prinics Zink | BT SPP or WiFi | 8+ bytes | Unknown | Simple header + data |
| Thermal/Cat Printers | BLE GATT | Varies | 1-bit bitmap | Command-based |

Key insight: Each printer family has completely different protocols, image requirements, and communication patterns.

---

## Proposed Architecture

### Three-Layer Design

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER APPLICATION                               │
│                                                                         │
│   printer = get_printer("canon_ivy2", "XX:XX:XX:XX:XX:XX")              │
│   printer.connect()                                                     │
│   printer.print("photo.jpg")                                            │
│   status = printer.get_status()                                         │
│   printer.disconnect()                                                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      LAYER 1: PRINTER INTERFACE                         │
│                         (devices/base.py)                               │
│                                                                         │
│   class Printer(ABC):                                                   │
│       def connect() -> None                                             │
│       def disconnect() -> None                                          │
│       def print(image_path: str, **options) -> None                     │
│       def get_status() -> PrinterStatus                                 │
│       def get_info() -> PrinterInfo                                     │
│       @property                                                         │
│       def is_connected -> bool                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│  LAYER 2: DEVICE  │   │  LAYER 2: DEVICE  │   │  LAYER 2: DEVICE  │
│   IMPLEMENTATIONS │   │   IMPLEMENTATIONS │   │   IMPLEMENTATIONS │
│                   │   │                   │   │                   │
│  CanonIvy2Printer │   │  KodakSnapPrinter │   │  FuturePrinter    │
│                   │   │                   │   │                   │
│  - Protocol logic │   │  - Protocol logic │   │  - Protocol logic │
│  - Image prep     │   │  - Image prep     │   │  - Image prep     │
│  - Status parsing │   │  - Status parsing │   │  - Status parsing │
└───────────────────┘   └───────────────────┘   └───────────────────┘
            │                       │                       │
            └───────────────────────┼───────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    LAYER 3: BLUETOOTH TRANSPORT                         │
│                       (bluetooth/base.py)                               │
│                                                                         │
│   class BluetoothTransport(ABC):                                        │
│       def connect(address: str, port: int) -> None                      │
│       def disconnect() -> None                                          │
│       def send(data: bytes) -> int                                      │
│       def recv(size: int) -> bytes                                      │
│       def set_blocking(blocking: bool) -> None                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│  NativeTransport  │   │  PyBluezTransport │   │  MacOSTransport   │
│    (socket.*)     │   │    (fallback)     │   │    (future)       │
│                   │   │                   │   │                   │
│  Windows + Linux  │   │   Linux legacy    │   │   IOBluetooth     │
└───────────────────┘   └───────────────────┘   └───────────────────┘
```

---

## Unified Data Models

### PrinterStatus (Common across all printers)

```python
@dataclass
class PrinterStatus:
    """Normalized status across all printer types."""
    battery_level: int          # 0-100 percentage
    is_ready: bool              # Can accept print job
    error: Optional[str]        # None if no error

    # Optional fields (not all printers support these)
    paper_remaining: Optional[int] = None
    is_cover_open: Optional[bool] = None
    is_charging: Optional[bool] = None
```

### PrinterInfo (Device metadata)

```python
@dataclass
class PrinterInfo:
    """Static printer information."""
    name: str                   # "Canon Ivy 2"
    model: str                  # "ivy2"
    firmware_version: Optional[str] = None
    serial_number: Optional[str] = None

    # Print specifications
    print_width: int            # pixels
    print_height: int           # pixels
    supported_formats: List[str]  # ["JPEG", "PNG"]
```

### PrinterCapabilities

```python
@dataclass
class PrinterCapabilities:
    """What this printer can do."""
    can_get_status: bool = True
    can_get_battery: bool = True
    can_configure_settings: bool = False
    can_reboot: bool = False
    supports_multiple_copies: bool = False
    min_battery_for_print: int = 0
```

---

## Proposed File Structure

```
zinkwell/
├── __init__.py                    # Package entry point, exports get_printer()
├── factory.py                     # get_printer() factory function
├── exceptions.py                  # All exception types
│
├── models/                        # Data models
│   ├── __init__.py
│   ├── status.py                  # PrinterStatus, PrinterInfo
│   └── capabilities.py            # PrinterCapabilities
│
├── devices/                       # Printer implementations
│   ├── __init__.py                # Device registry
│   ├── base.py                    # Abstract Printer class
│   ├── canon_ivy2/                # Canon Ivy 2 implementation
│   │   ├── __init__.py
│   │   ├── printer.py             # CanonIvy2Printer
│   │   ├── protocol.py            # Tasks, message format
│   │   └── image.py               # Image preparation
│   ├── kodak_snap/                # Kodak implementation (future)
│   │   ├── __init__.py
│   │   ├── printer.py
│   │   ├── protocol.py
│   │   └── image.py
│   └── _template/                 # Template for new printers
│       └── ...
│
├── bluetooth/                     # Transport layer
│   ├── __init__.py                # get_transport() factory
│   ├── base.py                    # Abstract BluetoothTransport
│   ├── native.py                  # Python socket implementation
│   ├── pybluez.py                 # PyBluez fallback
│   └── macos.py                   # Future macOS support
│
└── utils/                         # Shared utilities
    ├── __init__.py
    ├── image.py                   # Common image utilities
    └── threading.py               # Threaded client base class
```

---

## Abstract Interfaces

### Layer 1: Printer Interface

```python
# devices/base.py

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from models import PrinterStatus, PrinterInfo, PrinterCapabilities

class Printer(ABC):
    """Abstract base class for all printer implementations."""

    @property
    @abstractmethod
    def capabilities(self) -> PrinterCapabilities:
        """Return printer capabilities."""
        pass

    @property
    @abstractmethod
    def info(self) -> PrinterInfo:
        """Return static printer information."""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if printer is connected."""
        pass

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to printer."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to printer."""
        pass

    @abstractmethod
    def print(self, image_path: str, **options) -> None:
        """Print an image.

        Args:
            image_path: Path to image file
            **options: Printer-specific options (copies, quality, etc.)
        """
        pass

    @abstractmethod
    def get_status(self) -> PrinterStatus:
        """Get current printer status."""
        pass

    # Optional methods with default implementations
    def get_settings(self) -> Dict[str, Any]:
        """Get printer settings. Override if supported."""
        raise NotImplementedError(f"{self.info.name} does not support settings")

    def set_setting(self, key: str, value: Any) -> None:
        """Set a printer setting. Override if supported."""
        raise NotImplementedError(f"{self.info.name} does not support settings")

    def reboot(self) -> None:
        """Reboot the printer. Override if supported."""
        raise NotImplementedError(f"{self.info.name} does not support reboot")
```

### Layer 3: Bluetooth Transport

```python
# bluetooth/base.py

from abc import ABC, abstractmethod
from typing import Tuple

class BluetoothTransport(ABC):
    """Abstract base class for Bluetooth backends."""

    @abstractmethod
    def connect(self, address: str, port: int) -> None:
        """Connect to a Bluetooth device."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection."""
        pass

    @abstractmethod
    def send(self, data: bytes) -> int:
        """Send data. Returns bytes sent."""
        pass

    @abstractmethod
    def recv(self, size: int) -> bytes:
        """Receive data."""
        pass

    @abstractmethod
    def set_blocking(self, blocking: bool) -> None:
        """Set socket blocking mode."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected."""
        pass

    @abstractmethod
    def get_peer_name(self) -> Tuple[str, int]:
        """Get remote address."""
        pass
```

---

## Factory Functions

### Main Entry Point

```python
# factory.py

from typing import Optional
from devices.base import Printer
from devices import DEVICE_REGISTRY

def get_printer(
    device_type: str,
    address: str,
    port: int = 1,
    transport: Optional[str] = None
) -> Printer:
    """Create a printer instance.

    Args:
        device_type: Printer type ("canon_ivy2", "kodak_snap", etc.)
        address: Bluetooth MAC address
        port: RFCOMM port (default 1)
        transport: Force specific transport ("native", "pybluez")

    Returns:
        Configured Printer instance

    Example:
        printer = get_printer("canon_ivy2", "AA:BB:CC:DD:EE:FF")
        printer.connect()
        printer.print("photo.jpg")
    """
    if device_type not in DEVICE_REGISTRY:
        available = ", ".join(DEVICE_REGISTRY.keys())
        raise ValueError(f"Unknown device: {device_type}. Available: {available}")

    printer_class = DEVICE_REGISTRY[device_type]
    return printer_class(address=address, port=port, transport=transport)


def list_supported_printers() -> dict:
    """List all supported printer types with their info."""
    return {
        name: cls.get_info()
        for name, cls in DEVICE_REGISTRY.items()
    }
```

### Device Registry

```python
# devices/__init__.py

from .canon_ivy2 import CanonIvy2Printer
# from .kodak_snap import KodakSnapPrinter  # Future

DEVICE_REGISTRY = {
    "canon_ivy2": CanonIvy2Printer,
    # "kodak_snap": KodakSnapPrinter,
}
```

---

## Canon Ivy 2 Implementation (Refactored)

```python
# devices/canon_ivy2/printer.py

from devices.base import Printer
from models import PrinterStatus, PrinterInfo, PrinterCapabilities
from bluetooth import get_transport
from .protocol import (
    StartSessionTask, GetStatusTask, GetSettingTask,
    SetSettingTask, GetPrintReadyTask, RebootTask
)
from .image import prepare_image

class CanonIvy2Printer(Printer):
    """Canon Ivy 2 Mini Photo Printer implementation."""

    PRINT_BATTERY_MIN = 30
    PRINT_DATA_CHUNK = 990

    _info = PrinterInfo(
        name="Canon Ivy 2",
        model="canon_ivy2",
        print_width=640,
        print_height=1616,
        supported_formats=["JPEG", "PNG", "BMP"]
    )

    _capabilities = PrinterCapabilities(
        can_get_status=True,
        can_get_battery=True,
        can_configure_settings=True,
        can_reboot=True,
        min_battery_for_print=30
    )

    def __init__(self, address: str, port: int = 1, transport: str = None):
        self._address = address
        self._port = port
        self._transport = get_transport(transport)
        self._client = None  # ThreadedClient wrapping transport

    @property
    def capabilities(self) -> PrinterCapabilities:
        return self._capabilities

    @property
    def info(self) -> PrinterInfo:
        return self._info

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.alive.is_set()

    def connect(self) -> None:
        # Initialize threaded client with transport
        # Start session, get battery/MTU
        ...

    def disconnect(self) -> None:
        ...

    def print(self, image_path: str, auto_crop: bool = True, **options) -> None:
        # Prepare image using Ivy2-specific processing
        image_data = prepare_image(image_path, auto_crop)

        # Check printer readiness
        self._check_print_worthiness()

        # Send print job
        ...

    def get_status(self) -> PrinterStatus:
        raw = self._perform_task(GetStatusTask())
        error_code, battery, usb, cover_open, no_paper, wrong_sheet = raw

        # Normalize to common PrinterStatus
        error = None
        if cover_open:
            error = "Cover open"
        elif no_paper:
            error = "No paper"
        elif wrong_sheet:
            error = "Wrong smart sheet"
        elif error_code != 0:
            error = f"Error code: {error_code}"

        return PrinterStatus(
            battery_level=battery,
            is_ready=(error is None and battery >= self.PRINT_BATTERY_MIN),
            error=error,
            is_cover_open=cover_open
        )

    # Ivy2-specific methods
    def get_settings(self) -> dict:
        raw = self._perform_task(GetSettingTask())
        auto_off, firmware, tmd, photos, color = raw
        return {
            "auto_power_off": auto_off,
            "firmware_version": firmware,
            "photos_printed": photos
        }

    def set_setting(self, key: str, value) -> None:
        if key == "auto_power_off":
            self._perform_task(SetSettingTask(value))
        else:
            raise ValueError(f"Unknown setting: {key}")

    def reboot(self) -> None:
        self._perform_task(RebootTask())
```

---

## Usage Examples

### Simple Usage

```python
from zinkwell import get_printer

# Create and use printer
printer = get_printer("canon_ivy2", "AA:BB:CC:DD:EE:FF")
printer.connect()

# Check status
status = printer.get_status()
print(f"Battery: {status.battery_level}%")
print(f"Ready: {status.is_ready}")

# Print
if status.is_ready:
    printer.print("vacation_photo.jpg")

printer.disconnect()
```

### With Context Manager (Future Enhancement)

```python
from zinkwell import get_printer

with get_printer("canon_ivy2", "AA:BB:CC:DD:EE:FF") as printer:
    printer.print("photo.jpg")
    # Auto-disconnects on exit
```

### Listing Supported Printers

```python
from zinkwell import list_supported_printers

for name, info in list_supported_printers().items():
    print(f"{name}: {info.name} ({info.print_width}x{info.print_height})")
```

---

## Implementation Phases

### Phase 1: Core Infrastructure
1. Create package structure (`zinkwell/`)
2. Implement data models (`models/`)
3. Create abstract base classes (`devices/base.py`, `bluetooth/base.py`)
4. Implement native Bluetooth transport (`bluetooth/native.py`)
5. Add factory functions and device registry

### Phase 2: Canon Ivy 2 Migration
1. Move existing code into `devices/canon_ivy2/`
2. Refactor to implement `Printer` interface
3. Update to use `BluetoothTransport` abstraction
4. Normalize status responses to `PrinterStatus`
5. Test on Windows

### Phase 3: Cross-Platform Testing
1. Test native transport on Linux/Pi
2. Add PyBluez fallback if needed
3. Document platform-specific setup

### Phase 4: Add New Printer (Kodak)
1. Research Kodak protocol (will need device access)
2. Create `devices/kodak_snap/` implementation
3. Implement protocol and image preparation
4. Add to device registry

### Phase 5: Polish
1. Add context manager support
2. Improve error handling and messages
3. Add logging throughout
4. Create comprehensive documentation
5. Consider async support

---

## Design Decisions

### Threading Model: Device-Level with Shared Utilities (Option A)

**Decision:** Each device manages its own threading/concurrency, with a reusable `ThreadedClient` utility class available.

**Rationale:**
- Different printers have different I/O patterns (polling vs request-response, timeouts, etc.)
- Transport layer stays simple - just a thin socket wrapper
- Avoids forcing all printers into one threading model
- Easier to test transport in isolation

**Implementation:**

```
CanonIvy2Printer
    └── ThreadedClient (optional utility - queues, timers, thread management)
            └── BluetoothTransport (raw socket operations only)

SimplePrinter (hypothetical)
    └── BluetoothTransport (direct synchronous usage)
```

**ThreadedClient utility class:**

```python
# utils/threading.py

import queue
import threading
from bluetooth.base import BluetoothTransport

class ThreadedClient(threading.Thread):
    """Reusable threaded I/O wrapper around any BluetoothTransport.

    Provides:
    - Background thread for non-blocking I/O
    - Inbound/outbound message queues
    - Auto-disconnect timer
    - Connection state management

    Devices that need threaded I/O can use this directly.
    Devices with simpler needs can use BluetoothTransport directly.
    """

    def __init__(
        self,
        transport: BluetoothTransport,
        receive_size: int = 4096,
        auto_disconnect_timeout: int = 30
    ):
        super().__init__()
        self.transport = transport
        self.receive_size = receive_size
        self.auto_disconnect_timeout = auto_disconnect_timeout

        self.alive = threading.Event()
        self.outbound_q = queue.Queue()
        self.inbound_q = queue.Queue()
        self.disconnect_timer = None

    def connect(self, address: str, port: int) -> None:
        """Connect and start the I/O thread."""
        self.transport.connect(address, port)
        self.alive.set()
        self._reset_disconnect_timer()
        self.start()

    def disconnect(self, timeout: float = None) -> None:
        """Stop thread and close connection."""
        self.alive.clear()
        if self.disconnect_timer:
            self.disconnect_timer.cancel()
        self.transport.disconnect()
        try:
            self.join(timeout)
        except RuntimeError:
            pass

    def run(self) -> None:
        """Background I/O loop."""
        while self.alive.is_set():
            # Check connection health
            if not self.transport.is_connected():
                self.disconnect()
                break

            # Send outbound messages
            self.transport.set_blocking(True)
            try:
                message = self.outbound_q.get(timeout=0.1)
                self.transport.send(message)
                self._reset_disconnect_timer()
            except queue.Empty:
                pass

            # Receive inbound messages (non-blocking)
            self.transport.set_blocking(False)
            try:
                data = self.transport.recv(self.receive_size)
                if data:
                    self.inbound_q.put(data)
            except (OSError, BlockingIOError):
                pass

    def _reset_disconnect_timer(self) -> None:
        if self.disconnect_timer:
            self.disconnect_timer.cancel()
        self.disconnect_timer = threading.Timer(
            self.auto_disconnect_timeout,
            self.disconnect
        )
        self.disconnect_timer.start()
```

**Usage in Canon Ivy 2:**

```python
class CanonIvy2Printer(Printer):
    def connect(self) -> None:
        transport = get_transport(self._transport_type)
        self._client = ThreadedClient(transport, auto_disconnect_timeout=30)
        self._client.connect(self._address, self._port)
        self._start_session()
```

**Usage in a simpler printer (hypothetical):**

```python
class SimplePrinter(Printer):
    def connect(self) -> None:
        self._transport = get_transport()
        self._transport.connect(self._address, self._port)

    def print(self, image_path: str) -> None:
        data = prepare_image(image_path)
        self._transport.send(data)  # Synchronous, blocks until complete
        response = self._transport.recv(1024)
```

---

### Package Name: `zinkwell`

**Decision:** Name the package `zinkwell` - a play on "inkwell" for Zink (zero-ink) printers.

```python
from zinkwell import get_printer

printer = get_printer("canon_ivy2", "AA:BB:CC:DD:EE:FF")
printer.connect()
printer.print("photo.jpg")
```

### Error Handling: Hybrid Approach (Option C)

**Decision:** Common exception types with printer-specific details attached.

```python
# Common base exceptions
class ZinkwellError(Exception): pass
class ConnectionError(ZinkwellError): pass
class PrintError(ZinkwellError): pass

# PrintError can wrap device-specific issues
class PrintError(ZinkwellError):
    def __init__(self, message: str, device_error: Optional[str] = None):
        super().__init__(message)
        self.device_error = device_error  # e.g., "cover_open", "no_paper"
```

**Rationale:** Users get consistent exception types to catch, but can access device-specific details when needed.

### Image Preparation: Per-Device (Option A)

**Decision:** Each device handles its own image preparation.

**Rationale:**
- Canon Ivy 2 needs 640x1616 JPEG, rotated 180°
- Kodak just needs JPEG at specific size
- Too different to abstract usefully right now

### Device Discovery: Nice-to-Have (Phase 5)

**Decision:** Add discovery to transport layer, implement after core functionality works.

```python
from zinkwell.bluetooth import scan_devices
devices = scan_devices()  # Returns list of (address, name) tuples
```

### Backwards Compatibility: Not Required

**Decision:** No compatibility shim needed - this is a rewrite.

---

## Testing Strategy

### Testing Pyramid

```
                    /\
                   /  \
                  / HW \        ← Few, slow, real printer
                 /------\
                /  Integ \      ← Some, MockTransport
               /----------\
              / Contract   \    ← Interface compliance
             /--------------\
            /     Unit       \  ← Many, fast, isolated
           /------------------\
```

### Test Types

| Layer | What It Tests | Speed | When It Runs |
|-------|---------------|-------|--------------|
| **Unit** | Single function in isolation | ms | Every save |
| **Contract** | All implementations behave the same | ms | Every commit |
| **Integration** | Components working together | s | Every commit |
| **Hardware** | Real device behavior | min | Before release |

### What Each Layer Catches

| Layer | Example Bug |
|-------|-------------|
| Unit | `parse_status()` returns wrong battery level |
| Contract | `NativeTransport` raises different exception than `PyBluezTransport` |
| Integration | Printer sends commands in wrong order |
| Hardware | Windows socket behaves differently than Linux |

### Test File Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── mocks.py                    # MockTransport
├── fixtures/
│   ├── images/                 # Test images
│   └── responses/              # Captured printer responses
│
├── unit/
│   ├── bluetooth/
│   │   └── test_native.py
│   ├── devices/canon_ivy2/
│   │   ├── test_protocol.py    # Message encoding/decoding
│   │   └── test_image.py       # Image preparation
│   └── utils/
│       └── test_threading.py
│
├── contract/                   # Interface compliance
│   ├── test_transport.py       # All transports behave same
│   └── test_printer.py         # All printers behave same
│
├── integration/
│   └── test_canon_ivy2.py      # Full flows with MockTransport
│
└── hardware/                   # Real device (CI skips)
    └── test_real_printer.py
```

### Key Test Examples

**Unit - Protocol parsing (pure function, no mocks):**
```python
def test_status_parsing_low_battery():
    raw = bytes([0x00, 0x1E, ...])  # 30% battery
    result = parse_status(raw)
    assert result.battery_level == 30
```

**Contract - All transports behave identically:**
```python
class TransportContractTests:
    @pytest.fixture
    def transport(self):
        raise NotImplementedError

    def test_disconnect_when_not_connected_is_safe(self, transport):
        transport.disconnect()  # Should not raise

    def test_send_when_disconnected_raises(self, transport):
        with pytest.raises(ConnectionError):
            transport.send(b"data")

class TestNativeTransport(TransportContractTests):
    @pytest.fixture
    def transport(self):
        return NativeTransport()
```

**Integration - Full flow with mock:**
```python
def test_print_checks_battery_before_sending():
    mock = MockTransport(responses={
        STATUS_CMD: low_battery_response
    })
    printer = CanonIvy2Printer("AA:BB:...", transport=mock)
    printer.connect()

    with pytest.raises(PrintError, match="battery"):
        printer.print("photo.jpg")

    assert PRINT_CMD not in mock.sent_commands
```

**Hardware - Real device (skipped in CI):**
```python
@pytest.mark.hardware
@pytest.mark.skipif(not PRINTER_ADDRESS, reason="No printer")
def test_real_connection():
    printer = get_printer("canon_ivy2", PRINTER_ADDRESS)
    printer.connect()
    status = printer.get_status()
    assert status.battery_level > 0
```

### MockTransport

```python
class MockTransport(BluetoothTransport):
    """Simulates printer responses for testing."""

    def __init__(self, responses: dict[bytes, bytes]):
        self.responses = responses
        self.sent_commands = []
        self._connected = False
        self._pending = None

    def connect(self, address: str, port: int) -> None:
        self._connected = True

    def send(self, data: bytes) -> int:
        self.sent_commands.append(data)
        cmd = data[:8]  # Command identifier
        self._pending = self.responses.get(cmd)
        return len(data)

    def recv(self, size: int) -> bytes:
        return self._pending or b''

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def set_blocking(self, blocking: bool) -> None:
        pass

    def get_peer_name(self):
        return ("AA:BB:CC:DD:EE:FF", 1)
```

### pytest Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "hardware: tests requiring physical printer (skip in CI)",
]
testpaths = ["tests"]

[tool.coverage.run]
source = ["zinkwell"]
omit = ["tests/*"]
```

### CI Integration

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: pytest -v --ignore=tests/hardware --cov=zinkwell
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Protocol differences larger than expected | High | Keep device implementations isolated, don't over-abstract |
| Native socket BT behaves differently on platforms | Medium | Comprehensive testing, fallback to PyBluez |
| Breaking existing code | Medium | Provide compatibility shim for Ivy2Printer |
| macOS has no easy RFCOMM solution | High | Document as unsupported initially, research PyObjC |
| New printer protocols need reverse engineering | Medium | Document RE process, may need hardware access |

---

## Next Steps

Once this plan is approved:

1. Create the package structure
2. Implement the abstract interfaces
3. Build the native Bluetooth transport
4. Migrate Canon Ivy 2 to the new structure
5. Test on Windows (immediately available)
6. Document Linux/Pi testing requirements

Please review and provide feedback on:
- Overall architecture
- Naming conventions
- Data model design
- Implementation priorities
- Any missing requirements
