# Canon Ivy 2 Mini Photo Printer Communication Protocol

**Version:** 1.0
**Date:** 2026-01-03
**Status:** Reverse-Engineered Specification

## Table of Contents

1. [Overview](#1-overview)
2. [Physical Layer](#2-physical-layer)
3. [Message Format](#3-message-format)
4. [Command Reference](#4-command-reference)
5. [Response Format](#5-response-format)
6. [Image Transfer Protocol](#6-image-transfer-protocol)
7. [Status Codes and Flags](#7-status-codes-and-flags)
8. [Operational Sequences](#8-operational-sequences)
9. [Timing Requirements](#9-timing-requirements)

---

## 1. Overview

This document describes the communication protocol used by the Canon Ivy 2 Mini Photo Printer (Zink technology). The protocol operates over Bluetooth RFCOMM and uses a fixed-length command/response message format with variable-length payloads for image data transfer.

### 1.1 Terminology

| Term | Definition |
|------|------------|
| Host | The controlling device (computer, phone, Raspberry Pi) |
| Printer | The Canon Ivy 2 Mini Photo Printer |
| MTU | Maximum Transmission Unit |
| ACK | Acknowledgment code in response messages |

---

## 2. Physical Layer

### 2.1 Bluetooth Configuration

| Parameter | Value |
|-----------|-------|
| Protocol | Bluetooth Classic |
| Profile | Serial Port Profile (SPP) |
| Transport | RFCOMM |
| Port | 1 (default) |
| Device Name Pattern | `Canon (XX:XX) Mini Printer` |

### 2.2 Connection Parameters

| Parameter | Value |
|-----------|-------|
| Receive Buffer Size | 4096 bytes |
| Auto-disconnect Timeout | 30 seconds of inactivity |

### 2.3 Pairing Requirements

The printer requires legacy pairing mode (SSP mode 0). On Linux systems:

```
sudo hciconfig 0 sspmode 0
```

---

## 3. Message Format

All command messages from the host are exactly **34 bytes** in length.

### 3.1 Message Structure

```
Byte Offset   Size    Field Name      Description
─────────────────────────────────────────────────────────────────
0-1           2       START_CODE      Protocol identifier (0x430F)
2-3           2       FLAGS_1         Signed short, session flag
4             1       FLAGS_2         Signed byte, session flag
5-6           2       COMMAND         Command identifier
7             1       FLAGS_3         Command modifier flag
8-33          26      PAYLOAD         Command-specific data
```

### 3.2 Header Fields

#### START_CODE (Bytes 0-1)
- **Value:** `0x430F` (17167 decimal)
- **Encoding:** Big-endian unsigned 16-bit integer
- **Purpose:** Identifies the start of a valid protocol message

#### FLAGS_1 (Bytes 2-3)
- **Type:** Big-endian signed 16-bit integer
- **Values:**
  - `0x0001` (1): Normal operation
  - `0xFFFF` (-1): Session initialization mode

#### FLAGS_2 (Byte 4)
- **Type:** Signed 8-bit integer
- **Values:**
  - `0x20` (32): Normal operation
  - `0xFF` (-1): Session initialization mode

#### COMMAND (Bytes 5-6)
- **Type:** Big-endian unsigned 16-bit integer
- **Purpose:** Identifies the command type (see Section 4)

#### FLAGS_3 (Byte 7)
- **Type:** Unsigned 8-bit integer
- **Values:**
  - `0x00`: Read operation / normal command
  - `0x01`: Write operation / modifier present

### 3.3 Struct Pack Format

```
Format: ">HhbHB" + 26 bytes payload
  >   = Big-endian
  H   = Unsigned short (START_CODE)
  h   = Signed short (FLAGS_1)
  b   = Signed byte (FLAGS_2)
  H   = Unsigned short (COMMAND)
  B   = Unsigned byte (FLAGS_3)
```

---

## 4. Command Reference

### 4.1 Command Summary

| Command Code | Name | ACK Code | Description |
|--------------|------|----------|-------------|
| 0x0000 | START_SESSION | 0x0000 | Initialize connection |
| 0x0101 | GET_STATUS | 0x0101 | Query printer status |
| 0x0103 | SETTING_ACCESSORY | 0x0103 | Get/set printer settings |
| 0x0301 | PRINT_READY | 0x0301 | Prepare for image transfer |
| 0xFFFF | REBOOT | 0xFFFF | Reboot printer |

---

### 4.2 START_SESSION (0x0000)

Initializes the communication session with the printer.

#### Request

```
Header Flags: FLAGS_1 = -1, FLAGS_2 = -1, FLAGS_3 = 0
Payload: Empty (all zeros)
```

| Byte | Value | Description |
|------|-------|-------------|
| 0-1 | 0x430F | START_CODE |
| 2-3 | 0xFFFF | FLAGS_1 (session init) |
| 4 | 0xFF | FLAGS_2 (session init) |
| 5-6 | 0x0000 | COMMAND |
| 7 | 0x00 | FLAGS_3 |
| 8-33 | 0x00... | Payload (zeros) |

#### Response Payload

| Byte Offset | Size | Field | Description |
|-------------|------|-------|-------------|
| 1-2 | 2 | BATTERY_RAW | Battery level (6-bit encoded) |
| 3-4 | 2 | MTU | Maximum Transmission Unit |

**Battery Level Extraction:**
```
raw_value = (data[9] << 8) | data[10]
battery_level = extract_6_bit_reversed(raw_value)
```

---

### 4.3 GET_STATUS (0x0101)

Queries the current printer status including battery, errors, and paper state.

#### Request

```
Header Flags: FLAGS_1 = 1, FLAGS_2 = 32, FLAGS_3 = 0
Payload: Empty (all zeros)
```

#### Response Payload

| Byte Offset | Size | Field | Description |
|-------------|------|-------|-------------|
| 0-1 | 2 | STATUS_COMBINED | Battery and USB status |
| 2 | 1 | ERROR_CODE | Current error code |
| 3 | 1 | (reserved) | - |
| 4-5 | 2 | QUEUE_FLAGS | Paper/cover status flags |

**Field Extraction:**

```
combined = (payload[0] << 8) | payload[1]
battery_level = extract_6_bit_reversed(combined)
usb_connected = (combined >> 7) & 1

queue_flags = (payload[4] << 8) | payload[5]
cover_open       = (queue_flags & 0x01) != 0
no_paper         = (queue_flags & 0x02) != 0
wrong_smart_sheet = (queue_flags & 0x10) != 0
```

---

### 4.4 SETTING_ACCESSORY (0x0103)

Gets or sets printer configuration settings.

#### Get Settings Request

```
Header Flags: FLAGS_1 = 1, FLAGS_2 = 32, FLAGS_3 = 0
Payload: Empty (all zeros)
```

#### Get Settings Response Payload

| Byte Offset | Size | Field | Description |
|-------------|------|-------|-------------|
| 0 | 1 | AUTO_POWER_OFF | Minutes until auto power off (3, 5, or 10) |
| 1 | 1 | FW_MAJOR | Firmware version major |
| 2 | 1 | FW_MINOR | Firmware version minor |
| 3 | 1 | FW_PATCH | Firmware version patch |
| 4 | 1 | (reserved) | - |
| 5 | 1 | TMD_VERSION | TMD version |
| 6-7 | 2 | PHOTO_COUNT | Number of photos printed (big-endian) |
| 8 | 1 | COLOR_ID | Color identifier |

#### Set Settings Request

```
Header Flags: FLAGS_1 = 1, FLAGS_2 = 32, FLAGS_3 = 1
```

| Byte Offset | Size | Field | Description |
|-------------|------|-------|-------------|
| 8 | 1 | AUTO_POWER_OFF | New auto power off value |

**Valid AUTO_POWER_OFF Values:**
- `3` = 3 minutes
- `5` = 5 minutes
- `10` = 10 minutes

---

### 4.5 PRINT_READY (0x0301)

Prepares the printer to receive image data.

#### Request

```
Header Flags: FLAGS_1 = 1, FLAGS_2 = 32, FLAGS_3 = 0
```

| Byte Offset | Size | Field | Description |
|-------------|------|-------|-------------|
| 8 | 1 | LENGTH_B0 | Image length byte 0 (MSB) |
| 9 | 1 | LENGTH_B1 | Image length byte 1 |
| 10 | 1 | LENGTH_B2 | Image length byte 2 |
| 11 | 1 | LENGTH_B3 | Image length byte 3 (LSB) |
| 12 | 1 | UNKNOWN | Always 1 |
| 13 | 1 | MODE | 1 = normal, 2 = alternate |

**Image Length Encoding:**
```
payload[0] = (length >> 24) & 0xFF
payload[1] = (length >> 16) & 0xFF
payload[2] = (length >> 8) & 0xFF
payload[3] = length & 0xFF
```

#### Response Payload

| Byte Offset | Size | Field | Description |
|-------------|------|-------|-------------|
| 2 | 1 | UNKNOWN | Unknown field |
| 3 | 1 | ERROR_CODE | Error code (0 = success) |

---

### 4.6 REBOOT (0xFFFF)

Reboots the printer.

#### Request

```
Header Flags: FLAGS_1 = 1, FLAGS_2 = 32, FLAGS_3 = 1
```

| Byte Offset | Size | Field | Description |
|-------------|------|-------|-------------|
| 8 | 1 | REBOOT_CMD | Always 1 |

---

## 5. Response Format

All responses from the printer follow a consistent structure.

### 5.1 Response Structure

```
Byte Offset   Size    Field Name      Description
─────────────────────────────────────────────────────────────────
0-4           5       HEADER          Mirrors request header
5-6           2       ACK_CODE        Command acknowledgment
7             1       ERROR_CODE      Error status
8+            26      PAYLOAD         Response-specific data
```

### 5.2 Response Parsing

```python
def parse_response(data):
    payload = data[8:]
    ack_code = (data[5] << 8) | data[6]
    error_code = data[7]
    return payload, ack_code, error_code
```

### 5.3 ACK Validation

The response ACK_CODE must match the sent command code. A mismatch indicates a protocol error.

---

## 6. Image Transfer Protocol

### 6.1 Image Specifications

| Parameter | Value |
|-----------|-------|
| Format | JPEG |
| Final Dimensions | 640 × 1616 pixels |
| Quality | 100 (maximum) |
| Orientation | Rotated 180° before transfer |

### 6.2 Image Preparation Pipeline

```
1. Load source image
2. Scale to fit 1280 × 1920 canvas (with optional crop)
3. Center on canvas
4. Resize to 640 × 1616
5. Rotate 180°
6. Encode as JPEG (quality=100)
```

### 6.3 Transfer Parameters

| Parameter | Value |
|-----------|-------|
| Chunk Size | 990 bytes |
| Inter-chunk Delay | 20 ms |
| Transfer Timeout | 60 seconds |

### 6.4 Transfer Sequence

```
┌──────────┐                              ┌─────────┐
│   Host   │                              │ Printer │
└────┬─────┘                              └────┬────┘
     │                                         │
     │──── PRINT_READY (image_length) ────────>│
     │                                         │
     │<──────── PRINT_READY Response ──────────│
     │                                         │
     │──────── Image Chunk 1 (990 B) ─────────>│
     │          [20ms delay]                   │
     │──────── Image Chunk 2 (990 B) ─────────>│
     │          [20ms delay]                   │
     │              ...                        │
     │──────── Image Chunk N (≤990 B) ────────>│
     │                                         │
     │<──────── Transfer Complete ─────────────│
     │                                         │
```

---

## 7. Status Codes and Flags

### 7.1 Error Codes

| Code | Description |
|------|-------------|
| 0x00 | No error |
| Non-zero | Error condition (device-specific) |

### 7.2 Queue Flags (GET_STATUS Response)

| Bit | Mask | Description |
|-----|------|-------------|
| 0 | 0x0001 | Cover open |
| 1 | 0x0002 | No paper loaded |
| 4 | 0x0010 | Wrong smart sheet |

### 7.3 USB Status

| Value | Description |
|-------|-------------|
| 0 | USB not connected |
| 1 | USB connected |

### 7.4 Battery Level

Battery level is encoded as a 6-bit value using bit reversal:

```python
def extract_6_bit_reversed(value):
    bits = ""
    for i in range(6):
        bits += "1" if ((value >> i) & 1) == 1 else "0"
    return int(bits[::-1], 2)
```

**Result Range:** 0-63 (interpreted as percentage)

---

## 8. Operational Sequences

### 8.1 Connection Initialization

```
┌──────────┐                              ┌─────────┐
│   Host   │                              │ Printer │
└────┬─────┘                              └────┬────┘
     │                                         │
     │══════ Bluetooth RFCOMM Connect ════════>│
     │                                         │
     │──────── START_SESSION ─────────────────>│
     │                                         │
     │<──────── Battery, MTU ──────────────────│
     │                                         │
     │         [Connection Ready]              │
```

### 8.2 Print Operation

```
┌──────────┐                              ┌─────────┐
│   Host   │                              │ Printer │
└────┬─────┘                              └────┬────┘
     │                                         │
     │──────── GET_STATUS ────────────────────>│
     │<──────── Status Response ───────────────│
     │    [Validate: battery, paper, cover]    │
     │                                         │
     │──────── SETTING_ACCESSORY (get) ───────>│
     │<──────── Settings Response ─────────────│
     │                                         │
     │──────── PRINT_READY ───────────────────>│
     │<──────── Ready Response ────────────────│
     │                                         │
     │══════ Image Data Transfer ═════════════>│
     │                                         │
     │<──────── Transfer Complete ─────────────│
     │                                         │
     │         [Printer starts printing]       │
```

### 8.3 Pre-Print Validation

Before printing, verify:
1. `error_code == 0`
2. `battery_level >= 30`
3. `cover_open == false`
4. `no_paper == false`
5. `wrong_smart_sheet == false`

---

## 9. Timing Requirements

### 9.1 Timeouts

| Operation | Timeout |
|-----------|---------|
| Command Response | 5 seconds |
| Image Transfer | 60 seconds |
| Auto-disconnect | 30 seconds (idle) |

### 9.2 Delays

| Operation | Delay |
|-----------|-------|
| Post-send delay | 20 ms |
| Receive poll interval | 100 ms |

### 9.3 Retry Recommendations

| Scenario | Recommendation |
|----------|----------------|
| Connection failure | Retry with exponential backoff |
| Timeout | Retry command once |
| ACK mismatch | Abort and reconnect |

---

## Appendix A: Byte Order Reference

All multi-byte integers in the protocol use **big-endian** byte order.

## Appendix B: Example Message Hexdump

### START_SESSION Command

```
43 0F FF FF FF 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00
```

### GET_STATUS Command

```
43 0F 00 01 20 01 01 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00
```

### PRINT_READY Command (for 50000 byte image)

```
43 0F 00 01 20 03 01 00 00 00 C3 50 01 01 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00
```

---

## Revision History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2026-01-03 | Initial protocol specification |
