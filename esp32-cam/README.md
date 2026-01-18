# ESP32-CAM Kodak Step Printer

Complete C++ implementation for printing directly from an ESP32-CAM to Kodak Step series printers via Bluetooth.

## Features

- ✅ Full Kodak Step protocol implementation (reverse-engineered from APK)
- ✅ Bluetooth Classic SPP communication
- ✅ ESP32-CAM integration with image capture
- ✅ Support for all Kodak Step printer models
- ✅ Battery level monitoring
- ✅ Paper status checking
- ✅ Comprehensive error handling
- ✅ Ready-to-use examples

## Supported Printers

- Kodak Step
- Kodak Step Touch
- Kodak Step Slim
- Kodak Step Touch Snap 2

## Hardware Requirements

### Required
- **ESP32-CAM** (AI-Thinker module recommended)
- **FTDI USB-to-Serial adapter** (for programming)
- **5V power supply** (camera requires stable power)
- **Kodak Step printer** (any model)

### Optional
- Push button for manual trigger
- External antenna for better Bluetooth range

## Wiring

### ESP32-CAM Programming (via FTDI)

```
ESP32-CAM    FTDI Adapter
─────────────────────────
5V       →   5V (or VCC)
GND      →   GND
U0R      →   TX
U0T      →   RX
IO0      →   GND (for programming mode)
```

**Important:**
- Connect IO0 to GND **only when uploading**. Disconnect after upload to run normally.
- Ensure 5V power supply can provide at least 500mA for stable camera operation.

### Optional Button

```
ESP32-CAM    Button
───────────────────
GPIO14   →   Button → GND
```

## Software Setup

### Option 1: PlatformIO (Recommended)

1. **Install PlatformIO**
   - VS Code: Install PlatformIO IDE extension
   - CLI: `pip install platformio`

2. **Create Project**
   ```bash
   cd esp32-cam
   pio init
   ```

3. **Build and Upload**
   ```bash
   # Build
   pio run

   # Upload (connect IO0 to GND first!)
   pio run --target upload

   # Monitor serial output
   pio device monitor
   ```

### Option 2: Arduino IDE

1. **Install ESP32 Board Support**
   - Open Arduino IDE
   - File → Preferences
   - Add to "Additional Board Manager URLs":
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Tools → Board → Boards Manager → Search "ESP32" → Install

2. **Configure Board**
   - Tools → Board → ESP32 Arduino → AI Thinker ESP32-CAM
   - Tools → Partition Scheme → Huge APP (3MB No OTA)
   - Tools → Upload Speed → 921600

3. **Install Libraries**
   - ESP32 core already includes:
     - BluetoothSerial
     - esp_camera
     - WiFi

4. **Copy Files**
   - Copy `include/` and `src/` files to your sketch folder
   - Open example from `examples/KodakStepPrint.ino`

5. **Upload**
   - Connect IO0 to GND
   - Click Upload
   - When upload starts, press RESET button if needed
   - Disconnect IO0 after upload

## Quick Start

### 1. Test Connection (No Camera)

Use the test example to verify Bluetooth connectivity:

```cpp
// examples/KodakStepTest.ino
const char* PRINTER_NAME = "Step";  // Your printer name
```

Upload and check Serial Monitor (115200 baud) for connection status.

### 2. Capture and Print

Use the full example:

```cpp
// examples/KodakStepPrint.ino

// Configure your printer
const char* PRINTER_NAME = "Step";

// Optional: Use MAC address instead
// const char* PRINTER_ADDRESS = "AA:BB:CC:DD:EE:FF";

#define IS_SLIM_DEVICE false  // true for Slim/Snap 2
```

Upload, open Serial Monitor, and it will automatically capture and print after 3 seconds.

## API Reference

### KodakStepPrinter Class

#### Initialization
```cpp
KodakStepPrinter printer;

// Start Bluetooth
printer.begin("ESP32-Kodak");

// Connect by name (printer must be discoverable)
printer.connectByName("Step");

// Or connect by MAC address
printer.connect("AA:BB:CC:DD:EE:FF");

// Initialize printer communication
printer.initialize(false);  // true for Slim devices
```

#### Printer Operations
```cpp
// Get battery level
uint8_t battery;
printer.getBatteryLevel(&battery);

// Check paper status
printer.checkPaperStatus();

// Print image (JPEG data)
printer.printImage(jpegBuffer, jpegSize, numCopies);

// Get status
KodakStepProtocol::PrinterStatus status = printer.getStatus();

// Disconnect
printer.disconnect();
```

### ESP32CameraHelper Class

#### Camera Setup
```cpp
ESP32CameraHelper camera;

// Initialize camera
camera.begin(FRAMESIZE_VGA, 10);  // Frame size, JPEG quality

// Configure camera
camera.setVFlip(true);      // Vertical flip
camera.setHMirror(true);    // Horizontal mirror
```

#### Image Capture
```cpp
// Capture image
camera_fb_t* fb = camera.captureImage();

// Use image
printer.printImage(fb->buf, fb->len);

// Release frame buffer
camera.releaseImage(fb);
```

#### Flash Control
```cpp
camera.setFlash(true);        // Turn on flash
camera.flashBlink(3, 100);    // Blink 3 times, 100ms each
```

## Configuration Options

### Camera Frame Sizes

```cpp
FRAMESIZE_QQVGA    // 160x120
FRAMESIZE_QVGA     // 320x240
FRAMESIZE_VGA      // 640x480   ← Good for testing
FRAMESIZE_SVGA     // 800x600
FRAMESIZE_XGA      // 1024x768
FRAMESIZE_SXGA     // 1280x1024
FRAMESIZE_UXGA     // 1600x1200 ← Best quality
```

### JPEG Quality

```cpp
0-10   // High quality (larger file)
11-20  // Medium quality
21-63  // Lower quality (smaller file)
```

Lower numbers = better quality but larger files and slower transfer.

## Troubleshooting

### Camera Initialization Failed

**Symptoms:** "Camera init failed with error 0x..."

**Solutions:**
1. Check power supply (needs stable 5V, 500mA+)
2. Verify camera ribbon cable connection
3. Try adding 100μF capacitor between 5V and GND
4. Reset ESP32-CAM

### Bluetooth Connection Failed

**Symptoms:** "Failed to connect to printer"

**Solutions:**
1. Ensure printer is powered on and in pairing mode
2. Check printer name/address is correct
3. Move devices closer together
4. Restart both ESP32-CAM and printer
5. Check printer isn't already connected to another device

### Low Battery Error

**Symptoms:** "Battery too low to print"

**Solutions:**
1. Charge the printer
2. Battery must be ≥30% to print
3. Check battery level: `getBatteryLevel(&level)`

### Paper Errors

**Symptoms:** Print fails with paper-related errors

**Solutions:**
- ERR_NO_PAPER (0x02): Load paper
- ERR_COVER_OPEN (0x03): Close printer cover
- ERR_PAPER_MISMATCH (0x04): Use correct Zink paper
- ERR_MISFEED (0x08): Reload paper

### Print Quality Issues

**Solutions:**
1. Increase camera JPEG quality (lower number)
2. Use larger frame size (UXGA for best quality)
3. Ensure good lighting when capturing
4. Consider using flash: `camera.setFlash(true)`

### Out of Memory

**Symptoms:** ESP32 crashes or resets during operation

**Solutions:**
1. Use smaller frame size
2. Increase JPEG quality number (smaller files)
3. Ensure partition scheme is set to "Huge APP"
4. Free memory after each operation

## Protocol Details

This implementation is based on the reverse-engineered Kodak Step protocol. See `docs/KODAK_STEP_PROTOCOL.md` for complete protocol specification including:

- Packet structure (34 bytes)
- Command codes and parameters
- Response format
- Error codes
- Timing requirements
- Image transfer protocol

### Key Protocol Facts

- **Packet Size:** 34 bytes (commands and responses)
- **Header:** `1B 2A 43 41` (ESC * C A)
- **Image Chunk Size:** 4096 bytes
- **Inter-chunk Delay:** 20ms
- **Command Timeout:** 5 seconds

## Project Structure

```
esp32-cam/
├── include/
│   ├── KodakStepProtocol.h      # Protocol packet definitions
│   ├── KodakStepPrinter.h       # High-level printer interface
│   └── ESP32CameraHelper.h      # Camera control
├── src/
│   ├── KodakStepProtocol.cpp
│   ├── KodakStepPrinter.cpp
│   └── ESP32CameraHelper.cpp
├── examples/
│   ├── KodakStepPrint.ino       # Full camera + print example
│   └── KodakStepTest.ino        # Connection test only
├── platformio.ini               # PlatformIO configuration
└── README.md                    # This file
```

## Example Output

```
=================================
ESP32-CAM Kodak Step Printer
=================================

Initializing camera...
Camera initialized successfully

=== Camera Info ===
Sensor PID: 0x26
Frame size: VGA
JPEG quality: 10
===================

Initializing Bluetooth...
Bluetooth initialized as: ESP32-Kodak

Connecting to printer...
Connected to printer

Initializing printer...
Sending GET_ACCESSORY_INFO...
Received response:
[34 bytes]: 1B 2A 43 41 00 00 01 00 00 ...
Printer initialized successfully

=== Setup Complete ===

=== Starting Print Job ===

Printer battery: 87%
Capturing image...
Image captured: 640x480 - 45231 bytes

Sending to printer...
Sending PRINT_READY...
Transferring image data...
Sending chunk 1/12 (4096 bytes)
Sending chunk 2/12 (4096 bytes)
...
Image transfer complete!
Printer should start printing now...

=== Print Job Complete ===
Check your printer!
```

## Advanced Usage

### Custom Image Processing

```cpp
// Capture image
camera_fb_t* fb = camera.captureImage();

// Process image here (resize, filter, etc.)
// ...

// Print processed image
printer.printImage(processedBuffer, processedSize);

camera.releaseImage(fb);
```

### WiFi + Web Interface

You can extend this project to add WiFi and a web interface:

```cpp
#include <WiFi.h>
#include <WebServer.h>

// Setup WiFi AP
WiFi.softAP("ESP32-Printer", "password");

// Add web server to trigger prints remotely
```

### Multiple Printers

```cpp
KodakStepPrinter printer1;
KodakStepPrinter printer2;

printer1.connectByName("Step 1");
printer2.connectByName("Step 2");
```

## Performance

- **Image Capture:** ~1-2 seconds
- **Connection:** ~1-3 seconds
- **Image Transfer:** ~5-15 seconds (depends on size)
- **Total Print Time:** ~10-20 seconds from trigger to printer output

## Power Consumption

- **Idle:** ~80mA
- **Camera Active:** ~200mA
- **Bluetooth + Transfer:** ~150mA
- **Peak:** ~300mA

Use a quality 5V power supply rated for at least 500mA.

## License

This implementation is based on reverse-engineered protocol specification from the Kodak Step Touch APK (com.kodak.steptouch).

## Contributing

Contributions welcome! Areas for improvement:
- Image processing/resizing for optimal print quality
- WiFi web interface
- Multiple printer support
- Battery optimization
- Additional printer models

## References

- Protocol Specification: `docs/KODAK_STEP_PROTOCOL.md`
- ESP32-CAM Documentation: https://github.com/espressif/esp32-camera
- PlatformIO: https://platformio.org/
- Arduino-ESP32: https://github.com/espressif/arduino-esp32

## Acknowledgments

Protocol reverse-engineered from Kodak Step Touch APK version com.kodak.steptouch.

---

**Note:** This is an unofficial implementation and is not affiliated with or endorsed by Kodak.
