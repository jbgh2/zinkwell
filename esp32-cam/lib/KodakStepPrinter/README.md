# KodakStepPrinter Library

Arduino library for communicating with Kodak Step series Zink printers via Bluetooth Classic SPP.

## Supported Printers

- Kodak Step
- Kodak Step Touch
- Kodak Step Slim
- Kodak Step Touch Snap 2

## Requirements

- ESP32 with Bluetooth Classic support
- Arduino framework
- PlatformIO or Arduino IDE

## Installation

### PlatformIO

Copy the `KodakStepPrinter` folder to your project's `lib/` directory.

### Arduino IDE

Copy the `KodakStepPrinter` folder to your Arduino libraries folder (usually `~/Documents/Arduino/libraries/`).

## Usage

```cpp
#include <KodakStep.h>

KodakStepPrinter printer;

void setup() {
    Serial.begin(115200);

    // Initialize Bluetooth
    if (!printer.begin("MyESP32")) {
        Serial.println("Bluetooth init failed");
        return;
    }

    // Connect to printer by name (searches for "Step" in device names)
    if (!printer.connectByName("Step")) {
        Serial.println("Failed to connect");
        return;
    }

    // Initialize printer protocol
    if (!printer.initialize()) {
        Serial.println("Init failed: " + String(printer.getLastError()));
    }

    // Check battery
    uint8_t battery;
    if (printer.getBatteryLevel(&battery)) {
        Serial.printf("Battery: %d%%\n", battery);
    }

    // Check charging status
    bool charging;
    if (printer.getChargingStatus(&charging)) {
        Serial.printf("Charging: %s\n", charging ? "Yes" : "No");
    }
}

void printImage(uint8_t* jpegData, size_t jpegSize) {
    if (printer.printImage(jpegData, jpegSize, 1)) {
        Serial.println("Print started!");
    } else {
        Serial.println("Print failed: " + String(printer.getLastError()));
    }
}
```

## API Reference

### KodakStepPrinter Class

#### Connection Methods

| Method | Description |
|--------|-------------|
| `begin(deviceName)` | Initialize Bluetooth with given device name |
| `connect(address)` | Connect to printer by Bluetooth address |
| `connectByName(name)` | Scan and connect to printer containing name |
| `disconnect()` | Disconnect from printer |
| `isConnected()` | Check if printer is connected |

#### Printer Operations

| Method | Description |
|--------|-------------|
| `initialize(isSlim)` | Initialize printer protocol (required after connect) |
| `getBatteryLevel(&level)` | Get battery percentage (0-100) |
| `getChargingStatus(&charging)` | Get charging status (true/false) |
| `checkPaperStatus()` | Verify paper is loaded |
| `getPrintCount(&count)` | Get total print count |
| `getAutoPowerOff(&minutes)` | Get auto power-off setting |

#### Printing

| Method | Description |
|--------|-------------|
| `printImage(data, size, copies)` | Print JPEG image data |

#### Status

| Method | Description |
|--------|-------------|
| `getStatus()` | Get PrinterStatus struct |
| `getLastError()` | Get last error message |

### Error Codes

| Code | Name | Description |
|------|------|-------------|
| 0x00 | SUCCESS | No error |
| 0x01 | PAPER_JAM | Paper jam detected |
| 0x02 | NO_PAPER | Out of paper |
| 0x03 | COVER_OPEN | Printer cover is open |
| 0x04 | PAPER_MISMATCH | Wrong paper type |
| 0x05 | LOW_BATTERY | Battery too low to print |
| 0x06 | OVERHEATING | Printer overheating |
| 0x07 | COOLING | Printer in cooling mode |
| 0x08 | MISFEED | Paper misfeed |
| 0x09 | BUSY | Printer busy |

## Image Requirements

- Format: JPEG
- Recommended resolution: 640x960 pixels (2:3 aspect ratio)
- Maximum file size: Limited by ESP32 memory

## Protocol Documentation

See `docs/KODAK_STEP_PROTOCOL.md` for detailed protocol specification.

## License

MIT License
