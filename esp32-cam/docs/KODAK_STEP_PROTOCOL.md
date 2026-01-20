# Kodak Step Printer Communication Protocol

**Version:** 1.1
**Date:** 2026-01-19
**Status:** Reverse-Engineered from Kodak Step Touch APK (com.kodak.steptouch) and verified with hardware testing

## Table of Contents

1. [Overview](#1-overview)
2. [Physical Layer](#2-physical-layer)
3. [Message Format](#3-message-format)
4. [Command Reference](#4-command-reference)
5. [Response Format](#5-response-format)
6. [Printing Flow](#6-printing-flow)
7. [Error Codes](#7-error-codes)
8. [Timing Requirements](#8-timing-requirements)

---

## 1. Overview

This document describes the communication protocol used by Kodak Step series printers. The protocol operates over Bluetooth Classic SPP (Serial Port Profile).

### 1.1 Supported Devices

- Kodak Step
- Kodak Step Touch
- Kodak Step Slim
- Kodak Step Touch Snap 2

---

## 2. Physical Layer

### 2.1 Bluetooth Configuration

| Parameter | Value |
|-----------|-------|
| Protocol | Bluetooth Classic |
| Profile | Serial Port Profile (SPP) |
| UUID | `00001101-0000-1000-8000-00805F9B34FB` |
| Transport | RFCOMM |

### 2.2 UUID Bytes (for implementation)

```
00001101-0000-1000-8000-00805F9B34FB

As byte array (16 bytes, big-endian):
00 00 11 01 00 00 10 00 80 00 00 80 5F 9B 34 FB
```

### 2.3 Device Name Patterns

The printer advertises with names containing `"Step"` or `"STEP"`.

---

## 3. Message Format

### 3.1 Packet Size

All command packets are exactly **34 bytes**.

### 3.2 Packet Header Structure

```
Offset  Size  Value   Name        Description
──────────────────────────────────────────────────────────────
0       1     0x1B    START_1     Start byte (27 decimal, ESC)
1       1     0x2A    START_2     Protocol marker (42 decimal, '*')
2       1     0x43    IDENT_1     'C' (67 decimal)
3       1     0x41    IDENT_2     'A' (65 decimal)
4       1     var     FLAGS_1     Flags byte 1 (usually 0x00)
5       1     var     FLAGS_2     Flags byte 2 (command-specific)
6       1     var     COMMAND     Command code
7       1     var     FLAGS_3     Flags byte 3 (usually 0x00)
8-33    26    var     PAYLOAD     Command-specific data
```

### 3.3 Common Header

All packets begin with these 4 bytes:

```
Hex:     1B 2A 43 41
Decimal: 27 42 67 65
ASCII:   ESC * C A
```

---

## 4. Command Reference

### 4.1 Command Summary Table

| Cmd (Byte 6) | Hex  | Name                 | Description                    |
|--------------|------|----------------------|--------------------------------|
| 1            | 0x01 | GET_ACCESSORY_INFO   | Initialize/handshake **(also returns battery level in byte 12)** |
| 13           | 0x0D | GET_PAGE_TYPE        | Query paper type               |
| 14           | 0x0E | GET_BATTERY_LEVEL    | Query **charging status** (NOT battery %) |
| 15           | 0x0F | GET_PRINT_COUNT      | Query total prints             |
| 16           | 0x10 | GET_AUTO_POWER_OFF   | Query auto power-off setting   |
| 0            | 0x00 | PRINT_READY          | Prepare for print              |

---

### 4.2 GET_ACCESSORY_INFO (Standard)

**Purpose:** Initialize connection and handshake. **MUST be sent first after connecting.**

**Packet (34 bytes):**

```
Offset: 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15
Data:   1B 2A 43 41 00 00 01 00 00 00 00 00 00 00 00 00

Offset: 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33
Data:   00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
```

**Full hex string:** `1B2A434100000100000000000000000000000000000000000000000000000000000000`

**Byte breakdown:**

| Offset | Value | Description |
|--------|-------|-------------|
| 0 | 0x1B | Start byte |
| 1 | 0x2A | Protocol marker |
| 2 | 0x43 | 'C' |
| 3 | 0x41 | 'A' |
| 4 | 0x00 | Flags |
| 5 | 0x00 | Flags |
| 6 | 0x01 | **Command: GET_ACCESSORY_INFO** |
| 7 | 0x00 | Flags |
| 8-33 | 0x00 | Payload (zeros) |

---

### 4.3 GET_ACCESSORY_INFO (Slim variant)

**Purpose:** Same as above, but for Step Slim and Snap 2 devices.

**Packet (34 bytes):**

```
Offset: 00 01 02 03 04 05 06 07 08 09 ...
Data:   1B 2A 43 41 00 02 01 00 00 00 ... (rest zeros)
```

**Difference:** Byte 5 = 0x02 instead of 0x00

**Full hex string:** `1B2A434100020100000000000000000000000000000000000000000000000000000000`

---

### 4.4 GET_BATTERY_LEVEL (Charging Status)

> **IMPORTANT:** This command does NOT return battery percentage. See Section 5.4 for details.
> To get battery percentage, use GET_ACCESSORY_INFO and read byte 12.

**Packet (34 bytes):**

```
Offset: 00 01 02 03 04 05 06 07 08 ...
Data:   1B 2A 43 41 00 00 0E 00 00 ... (rest zeros)
```

**Full hex string:** `1B2A4341000E0000000000000000000000000000000000000000000000000000000000`

| Offset | Value | Description |
|--------|-------|-------------|
| 6 | 0x0E | Command: GET_BATTERY_LEVEL (14) |

**Response:** Returns response type 0x04 (not 0x0E). Byte 8 contains charging status, not battery percentage.

---

### 4.5 GET_PAGE_TYPE

**Packet (34 bytes):**

```
Offset: 00 01 02 03 04 05 06 07 08 ...
Data:   1B 2A 43 41 00 00 0D 00 00 ... (rest zeros)
```

**Full hex string:** `1B2A434100000D00000000000000000000000000000000000000000000000000000000`

| Offset | Value | Description |
|--------|-------|-------------|
| 6 | 0x0D | Command: GET_PAGE_TYPE (13) |

---

### 4.6 GET_PRINT_COUNT

**Packet (34 bytes):**

```
Offset: 00 01 02 03 04 05 06 07 08 ...
Data:   1B 2A 43 41 00 00 00 01 00 ... (rest zeros)
```

**Full hex string:** `1B2A434100000001000000000000000000000000000000000000000000000000000000`

| Offset | Value | Description |
|--------|-------|-------------|
| 6 | 0x00 | Command |
| 7 | 0x01 | Flag (distinguishes from PRINT_READY) |

---

### 4.7 GET_AUTO_POWER_OFF

**Packet (34 bytes):**

```
Offset: 00 01 02 03 04 05 06 07 08 ...
Data:   1B 2A 43 41 00 00 10 00 00 ... (rest zeros)
```

**Full hex string:** `1B2A434100001000000000000000000000000000000000000000000000000000000000`

| Offset | Value | Description |
|--------|-------|-------------|
| 6 | 0x10 | Command: GET_AUTO_POWER_OFF (16) |

---

### 4.8 PRINT_READY

**Purpose:** Notify printer of incoming image and specify copies.

**Packet structure (34 bytes):**

```
Offset: 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 ...
Data:   1B 2A 43 41 00 00 00 00 SS SS SS NN 00 00 00 00 ... (rest zeros)
```

| Offset | Value | Description |
|--------|-------|-------------|
| 0-3 | 1B 2A 43 41 | Header |
| 4-7 | 00 00 00 00 | Flags (all zero) |
| 8 | SS | Image size byte 2 (bits 16-23) |
| 9 | SS | Image size byte 1 (bits 8-15) |
| 10 | SS | Image size byte 0 (bits 0-7) |
| 11 | NN | Number of copies (1-255) |
| 12-15 | 00 00 00 00 | Reserved (zeros) |
| 16-33 | 00... | Payload (zeros) |

**Image size encoding (big-endian, 3 bytes):**

```
For image_size = 50000 bytes (0x00C350):
  Byte 8  = (50000 >> 16) & 0xFF = 0x00
  Byte 9  = (50000 >> 8)  & 0xFF = 0xC3
  Byte 10 = (50000)       & 0xFF = 0x50
```

**Example: Print 50000 bytes, 1 copy:**

```
1B 2A 43 41 00 00 00 00 00 C3 50 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
```

---

### 4.9 START_OF_SEND_ACK

**Purpose:** Acknowledge upload request from printer.

**Packet (34 bytes):**

```
Offset: 00 01 02 03 04 05 06 07 08 09 ...
Data:   1B 2A 43 41 00 00 01 00 02 00 ... (rest zeros)
```

| Offset | Value | Description |
|--------|-------|-------------|
| 6 | 0x01 | Command |
| 8 | 0x02 | ACK type |

---

### 4.10 END_OF_RECEIVED_ACK

**Packet (34 bytes):**

```
Offset: 00 01 02 03 04 05 06 07 08 09 ...
Data:   1B 2A 43 41 00 00 01 01 02 00 ... (rest zeros)
```

| Offset | Value | Description |
|--------|-------|-------------|
| 6 | 0x01 | Command |
| 7 | 0x01 | Flag |
| 8 | 0x02 | ACK type |

---

### 4.11 ERROR_MESSAGE_ACK

**Purpose:** Acknowledge an error from the printer.

**Packet (34 bytes):**

```
Offset: 00 01 02 03 04 05 06 07 08 ...
Data:   1B 2A 43 41 00 00 01 00 EE ... (rest zeros)
```

| Offset | Value | Description |
|--------|-------|-------------|
| 6 | 0x01 | Command |
| 8 | EE | Error code being acknowledged |

---

## 5. Response Format

### 5.1 Response Structure

Responses are also **34 bytes** with similar header structure.

```
Offset  Size  Name        Description
──────────────────────────────────────────────────
0-3     4     HEADER      Same as command (1B 2A 43 41)
4-5     2     FLAGS       Response flags
6       1     COMMAND     Echoed command code
7       1     SUB_TYPE    Response sub-type
8       1     ERROR_CODE  0x00 = success, else error
9-33    25    PAYLOAD     Response-specific data
```

### 5.2 Checking Success

```
IF response[8] == 0x00 THEN success
ELSE error occurred (see error code table)
```

### 5.3 Response Types

| Byte 6 | Byte 7 | Description |
|--------|--------|-------------|
| 0x01 | 0x02 | Accessory info response (contains battery level) |
| 0x04 | 0x00 | Charging status response (from GET_BATTERY_LEVEL command) |
| 0x0D | - | Page type response |
| 0x10 | - | Auto power off response |
| 0x00 | 0x00 | Upload ready from printer |
| 0x00 | 0x02 | Upload request from printer |

### 5.4 Battery Level and Charging Status

> **CORRECTION (v1.1):** The GET_BATTERY_LEVEL command (0x0E) does NOT return battery percentage.
> Instead, it returns a response with type 0x04 containing charging status.

**To get battery percentage:** Use GET_ACCESSORY_INFO and read **byte 12**.

**GET_BATTERY_LEVEL (0x0E) Response:**
```
1B 2A 43 41 01 11 04 00 CS 00 00 00 ...
                  ^^    ^^
                  |     +-- Byte 8: Charging Status (1=charging, 0=not charging)
                  +-------- Byte 6: Response type 0x04 (NOT 0x0E)
```

**GET_ACCESSORY_INFO (0x01) Response:**
```
1B 2A 43 41 01 11 01 02 ER 00 ?? ?? BL 00 00 MA MA MA MA MA MA ...
                        ^^       ^^          ^^^^^^^^^^^^^^^^^
                        |        |           +-- Bytes 15-20: MAC Address
                        |        +-------------- Byte 12: Battery Level (0-100%)
                        +----------------------- Byte 8: Error code
```

| Field | Location | Description |
|-------|----------|-------------|
| Battery Level | GET_ACCESSORY_INFO byte 12 | 0-100% |
| Charging Status | GET_BATTERY_LEVEL byte 8 | 1=charging, 0=not charging |
| MAC Address | GET_ACCESSORY_INFO bytes 15-20 | Printer Bluetooth address |

### 5.5 Accessory Info Response

Full response structure (34 bytes):

```
Offset  Value   Description
──────────────────────────────────────────────────
0-3     Header  1B 2A 43 41
4       0x01    Response flag
5       0x11    Response flag
6       0x01    Response type (echoes command)
7       0x02    Sub-type
8       Error   Error code (0x00 = success)
9       0x00    Reserved
10      ??      Unknown
11      ??      Unknown
12      BL      Battery level (0-100%)
13      0x00    Reserved
14      0x00    Reserved
15-20   MAC     Printer Bluetooth MAC address (6 bytes)
21      0x01    Unknown
22      0x00    Reserved
23      0x06    Unknown
24-25   0x00    Reserved
26      0x07    Unknown
27      0x03    Unknown
28      0xF5    Unknown
29-33   0x00    Reserved
```

---

## 6. Printing Flow

### 6.1 Sequence Diagram

```
    HOST                                    PRINTER
      │                                        │
      │══════ Bluetooth SPP Connect ══════════>│
      │                                        │
      │──── GET_ACCESSORY_INFO ───────────────>│
      │<─────────── Response ──────────────────│
      │      (wait 500ms, verify byte[8]=0)    │
      │                                        │
      │──── GET_BATTERY_LEVEL ────────────────>│
      │<─────────── Response ──────────────────│
      │      (check battery >= 30%)            │
      │                                        │
      │──── GET_PAGE_TYPE ────────────────────>│
      │<─────────── Response ──────────────────│
      │      (verify paper loaded)             │
      │                                        │
      │──── PRINT_READY (size, copies) ───────>│
      │<─────────── Response ──────────────────│
      │      (check for errors)                │
      │                                        │
      │──── Image chunk 1 (4096 bytes) ───────>│
      │      [wait 20ms]                       │
      │──── Image chunk 2 (4096 bytes) ───────>│
      │      [wait 20ms]                       │
      │      ...                               │
      │──── Final chunk (remaining bytes) ────>│
      │                                        │
      │<─────── Print Complete ────────────────│
      │                                        │
```

### 6.2 Step-by-Step Algorithm

```
1. CONNECT via Bluetooth SPP to printer

2. SEND GET_ACCESSORY_INFO packet
   WAIT for 34-byte response
   IF response[8] != 0x00 THEN error, abort
   WAIT 500ms

3. GET BATTERY LEVEL (from accessory info already received)
   battery_level = accessory_response[12]  // Byte 12, NOT byte 8!
   IF battery_level < 30 THEN error "low battery", abort
   // Note: GET_BATTERY_LEVEL (0x0E) returns charging status, not percentage

4. SEND GET_PAGE_TYPE packet
   WAIT for response
   IF error THEN warn "check paper"
   WAIT 100ms

5. PREPARE image data as JPEG (see Image Requirements)

6. SEND PRINT_READY packet with:
   - image_size in bytes 8-10 (big-endian)
   - num_copies in byte 11
   WAIT for response
   IF response[8] != 0x00 THEN error, abort
   WAIT 100ms

7. SEND image data in chunks:
   chunk_size = 4096 bytes
   offset = 0
   WHILE offset < image_size:
       chunk = image_data[offset : offset + chunk_size]
       SEND chunk (raw bytes, no header)
       offset = offset + length(chunk)
       WAIT 20ms

8. DONE - printer will print
```

### 6.3 Retry/Recovery Flow

If printing fails, the official app uses this recovery sequence:

```
1. SAVE failed operation details
2. DISCONNECT socket
3. WAIT 6000ms (6 seconds)
4. RECONNECT to printer
5. SEND GET_ACCESSORY_INFO
6. WAIT for response
7. RETRY the failed operation
```

### 6.4 Device Type Detection

Before sending GET_ACCESSORY_INFO, check device name:

```
IF device_name contains "Slim" OR device_name contains "Snap 2":
    USE Slim variant packet (byte 5 = 0x02)
ELSE:
    USE standard packet (byte 5 = 0x00)
```

---

## 7. Error Codes

### 7.1 Error Code Table

| Code | Hex  | Name            | Description                      |
|------|------|-----------------|----------------------------------|
| 0    | 0x00 | SUCCESS         | No error                         |
| 1    | 0x01 | PAPER_JAM       | Paper jam detected               |
| 2    | 0x02 | NO_PAPER        | Out of paper                     |
| 3    | 0x03 | COVER_OPEN      | Printer cover is open            |
| 4    | 0x04 | PAPER_MISMATCH  | Wrong paper type                 |
| 5    | 0x05 | LOW_BATTERY     | Battery too low to print         |
| 6    | 0x06 | OVERHEATING     | Printer overheating              |
| 7    | 0x07 | COOLING         | Printer in cooling mode          |
| 8    | 0x08 | MISFEED         | Paper misfeed                    |
| 9    | 0x09 | BUSY            | Printer busy                     |
| 254  | 0xFE | NOT_CONNECTED   | Not connected (internal)         |

### 7.2 Error Recovery Actions

| Error | Recommended Action |
|-------|-------------------|
| PAPER_JAM | Clear paper path, retry |
| NO_PAPER | Load paper, retry |
| COVER_OPEN | Close cover, retry |
| PAPER_MISMATCH | Load correct Zink paper |
| LOW_BATTERY | Charge printer |
| OVERHEATING | Wait 5 minutes, retry |
| COOLING | Wait 2 minutes, retry |
| MISFEED | Reload paper, retry |
| BUSY | Wait 10 seconds, retry |

---

## 8. Timing Requirements

### 8.1 Delays

| Operation | Delay |
|-----------|-------|
| After Bluetooth connect | 500 ms |
| After GET_ACCESSORY_INFO | 500 ms |
| Between status commands | 100 ms |
| After PRINT_READY | 100 ms |
| Between image chunks | 20 ms |
| Before reconnect retry | 6000 ms |

### 8.2 Timeouts

| Operation | Timeout |
|-----------|---------|
| Command response wait | 5000 ms |
| Image transfer total | 60000 ms |
| Bluetooth connect | 10000 ms |

### 8.3 Data Transfer

| Parameter | Value |
|-----------|-------|
| Chunk size | 4096 bytes |
| Inter-chunk delay | 20 ms |
| Packet size (commands) | 34 bytes |

---

## Appendix A: Quick Reference - All Packets

### A.1 GET_ACCESSORY_INFO (Standard)
```
1B 2A 43 41 00 00 01 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00
```

### A.2 GET_ACCESSORY_INFO (Slim)
```
1B 2A 43 41 00 02 01 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00
```

### A.3 GET_BATTERY_LEVEL
```
1B 2A 43 41 00 00 0E 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00
```

### A.4 GET_PAGE_TYPE
```
1B 2A 43 41 00 00 0D 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00
```

### A.5 GET_PRINT_COUNT
```
1B 2A 43 41 00 00 00 01 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00
```

### A.6 GET_AUTO_POWER_OFF
```
1B 2A 43 41 00 00 10 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00
```

### A.7 PRINT_READY (template)
```
1B 2A 43 41 00 00 00 00 [SZ] [SZ] [SZ] [CP] 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00

Where:
  [SZ] = 3-byte image size (big-endian)
  [CP] = number of copies
```

### A.8 START_OF_SEND_ACK
```
1B 2A 43 41 00 00 01 00 02 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00
```

### A.9 END_OF_RECEIVED_ACK
```
1B 2A 43 41 00 00 01 01 02 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00
```

### A.10 ERROR_MESSAGE_ACK (template)
```
1B 2A 43 41 00 00 01 00 [EC] 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00

Where:
  [EC] = error code being acknowledged
```

---

## Appendix B: Constants

```
SPP_UUID           = "00001101-0000-1000-8000-00805F9B34FB"
PACKET_SIZE        = 34
CHUNK_SIZE         = 4096
INTER_CHUNK_DELAY  = 20      (milliseconds)
RECONNECT_DELAY    = 6000    (milliseconds)
COMMAND_TIMEOUT    = 5000    (milliseconds)
MIN_BATTERY_LEVEL  = 30      (percent)
```

---

## Appendix C: Comparison with Canon Ivy 2

| Feature | Kodak Step | Canon Ivy 2 |
|---------|------------|-------------|
| Header bytes | `1B 2A 43 41` | `43 0F` |
| Packet size | 34 bytes | 34 bytes |
| Command position | Byte 6 | Bytes 5-6 |
| First command | GET_ACCESSORY_INFO (0x01) | START_SESSION (0x0000) |
| Chunk size | 4096 bytes | 990 bytes |
| SPP UUID | Same | Same |

---

## Revision History

| Version | Date | Description |
|---------|------|-------------|
| 1.1 | 2026-01-19 | Corrected battery level location (byte 12 of GET_ACCESSORY_INFO, not byte 8 of GET_BATTERY_LEVEL). Added charging status documentation. Verified with hardware testing. |
| 1.0 | 2026-01-18 | Initial protocol specification |
