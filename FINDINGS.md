# Kodak Step Printer Connection Analysis

## Summary

I've built prototype tooling to communicate with the Kodak Step Zink printer based on the Canon Ivy 2 protocol documentation. The tooling is ready, but we've encountered a Windows Bluetooth connectivity issue that needs to be resolved before testing can proceed.

## What Was Built

### 1. Core Files Created

- **[kodak_step.py](kodak_step.py)** - Main printer class with full protocol implementation
- **[client_windows.py](client_windows.py)** - Windows Bluetooth socket client (AF_BLUETOOTH/RFCOMM)
- **[client_serial.py](client_serial.py)** - Windows COM port serial client (alternative approach)
- **[test_kodak_serial.py](test_kodak_serial.py)** - Interactive test script for COM port connection
- **[find_kodak_port.py](find_kodak_port.py)** - Auto-scanner to find which COM port the printer uses
- **[bt_scan.py](bt_scan.py)** - Bluetooth RFCOMM port scanner
- **[bt_service_info.ps1](bt_service_info.ps1)** - PowerShell script to query Bluetooth device info
- **[bt_reconnect.ps1](bt_reconnect.ps1)** - PowerShell script to refresh Bluetooth connection

### 2. Protocol Implementation

Based on [docs/PROTOCOL.md](docs/PROTOCOL.md), implemented:

- ✅ Message format (34-byte commands, big-endian)
- ✅ START_SESSION command (0x0000)
- ✅ GET_STATUS command (0x0101)
- ✅ SETTING_ACCESSORY command (0x0103)
- ✅ PRINT_READY command (0x0301)
- ✅ Image preparation pipeline (JPEG, 640×1616, rotated 180°)
- ✅ Chunked image transfer (990-byte chunks)
- ✅ Response parsing and ACK validation

## Current Status: Connection Blocked

### Device State
- **Device**: KODAK STEP (72:D4)
- **MAC Address**: A4:62:DF:A9:72:D4
- **Windows Status**: Paired (OK)
- **Last Connected**: 8/23/2025 9:00:03 AM (has been connected before)

### Available COM Ports
- COM3, COM4, COM5, COM6, COM10 (all Bluetooth SPP)

### Issue Discovered

All connection attempts fail with:
- **COM3, COM5**: Write timeout (port opens but can't send data)
- **COM4, COM6, COM10**: Semaphore timeout (can't open port)
- **Direct RFCOMM socket**: Connection timeout

**Root Cause**: Windows Bluetooth SPP requires the device to be **actively connected** before the COM port becomes usable for data transfer. Simply being "paired" is not enough.

## Critical Protocol Requirements (From Documentation)

### From Canon Ivy 2 Protocol:

1. **Transport**: Bluetooth Classic, Serial Port Profile (SPP), RFCOMM
2. **RFCOMM Channel**: 1 (default)
3. **Buffer Size**: 4096 bytes
4. **Message Size**: Exactly 34 bytes per command
5. **START_CODE**: 0x430F (17167)
6. **Session Init Flags**: FLAGS_1=-1, FLAGS_2=-1

### Pairing Requirements (Linux):

The Canon Ivy 2 documentation states:
```bash
sudo hciconfig 0 sspmode 0  # Disable Secure Simple Pairing
```

This enables **legacy pairing mode**, which Zink printers require. On Windows, we don't have direct control over SSP mode, which may be contributing to connectivity issues.

## Next Steps to Get This Working

### Option 1: Active Bluetooth Connection (Recommended)

**You need to manually connect the printer in Windows:**

1. **Power on the Kodak Step printer**
2. **Enter pairing/discovery mode**:
   - Press and hold the power button for 3-5 seconds
   - Wait for the LED to start blinking
3. **In Windows Settings**:
   - Go to Settings → Bluetooth & devices
   - Find "KODAK STEP (72:D4)"
   - Click "Connect" (not just paired, but actively connected)
   - Wait for status to show "Connected"
4. **Run our test immediately while connected**:
   ```bash
   python find_kodak_port.py
   ```
   This will scan all COM ports and identify which one responds to the protocol.

5. **Once you find the working port** (e.g., COM5):
   ```bash
   python test_kodak_serial.py COM5
   ```
   This will test session initialization, status queries, and offer to print.

### Option 2: Use PyBluez on Linux/Raspberry Pi

The original Canon Ivy 2 code was tested on Raspberry Pi with PyBluez. If Windows continues to be problematic:

1. Move to a Linux environment (Raspberry Pi, WSL2, or Linux VM)
2. Install PyBluez and Bluetooth tools
3. Disable SSP mode: `sudo hciconfig 0 sspmode 0`
4. Pair the printer using `bluetoothctl`
5. Use the original [client.py](client.py) with PyBluez

### Option 3: Bluetooth Packet Sniffing

If the printer connects but doesn't respond to our protocol:

1. **Use Wireshark with Bluetooth capture**:
   - Install Wireshark
   - Enable Bluetooth HCI sniffing
   - Capture traffic while using an official Kodak Step app
   - Compare with Canon Ivy 2 protocol

2. **Check for protocol differences**:
   - Different start codes
   - Different command structure
   - Additional handshake required
   - Different RFCOMM channel

## Protocol Testing Once Connected

When you get a working connection, the test script will:

1. **Send START_SESSION** → Expect battery level and MTU
2. **Send GET_STATUS** → Expect status flags (battery, paper, cover, errors)
3. **Send SETTING_ACCESSORY** → Expect firmware version, photo count
4. **Send PRINT_READY** → Prepare for image transfer
5. **Transfer image data** → Send JPEG in 990-byte chunks
6. **Wait for completion** → Printer should begin printing

## Files Ready for Testing

| File | Purpose |
|------|---------|
| `test_kodak_serial.py COM<N>` | Full protocol test with specified COM port |
| `find_kodak_port.py` | Auto-detect which COM port works |
| `bt_service_info.ps1` | Query Bluetooth device information |
| `bt_reconnect.ps1` | Force device reconnection |

## Expected Output When Working

```
Testing Kodak Step on COM5
============================================================
Connecting to COM5...
  Successfully opened COM5
Connected!

Attempting to start session...
  Session started! Battery: 78%, MTU: 990

Attempting to get status...
  Status retrieved:
    Error Code: 0
    Battery Level: 78%
    USB Connected: False
    Cover Open: False
    No Paper: False
    Wrong Smart Sheet: False

Attempting to get settings...
  Settings retrieved:
    Auto Power Off: 5 minutes
    Firmware Version: 1.0.0
    Photos Printed: 42

Attempt to print test image? (y/n):
```

## Kodak Step vs Canon Ivy 2 Differences

### Unknown Until Tested:
- ✓ Both use Zink (Zero Ink) technology
- ✓ Both should use Bluetooth SPP
- ? Same protocol message format
- ? Same command codes
- ? Same image dimensions (Canon Ivy 2: 640×1616)
- ? Same chunk size (990 bytes)

### Possible Differences:
- Different start code (not 0x430F)
- Different RFCOMM channel (not channel 1)
- Additional authentication/handshake
- Different image dimensions
- Kodak-specific commands

## How to Proceed

1. **First**: Try Option 1 above - actively connect the printer in Windows settings
2. **Then**: Run `find_kodak_port.py` to identify the working COM port
3. **Finally**: Run `test_kodak_serial.py <PORT>` to test the full protocol

If the protocol works, we'll get status information. If it doesn't respond or responds with unexpected data, we'll need to either:
- Sniff the official Kodak app's Bluetooth traffic
- Find existing Kodak Step protocol documentation
- Reverse engineer the protocol through experimentation

---

**Current Blocker**: Need the Kodak Step printer to be powered on and actively connected in Windows Bluetooth settings before the COM port will accept data.
