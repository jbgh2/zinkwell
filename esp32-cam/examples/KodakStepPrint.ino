/**
 * Kodak Step Printer Example for ESP32-CAM
 *
 * This example demonstrates how to:
 * 1. Initialize the ESP32-CAM
 * 2. Connect to a Kodak Step printer via Bluetooth
 * 3. Capture an image
 * 4. Print the image
 *
 * Hardware: ESP32-CAM (AI-Thinker)
 * Printer: Kodak Step / Step Touch / Step Slim / Step Touch Snap 2
 *
 * Instructions:
 * 1. Update PRINTER_NAME or PRINTER_ADDRESS with your printer's info
 * 2. Upload to ESP32-CAM
 * 3. Open Serial Monitor (115200 baud)
 * 4. The device will connect and print automatically
 */

#include "KodakStepPrinter.h"
#include "ESP32CameraHelper.h"

// ===== CONFIGURATION =====

// Printer connection method - choose one:
// Option 1: Connect by name (printer must be discoverable)
#define USE_PRINTER_NAME true
const char* PRINTER_NAME = "Step";  // Part of the printer name (e.g., "Step", "STEP")

// Option 2: Connect by MAC address
const char* PRINTER_ADDRESS = "XX:XX:XX:XX:XX:XX";  // Replace with your printer's MAC

// Device type
#define IS_SLIM_DEVICE false  // Set to true for Step Slim or Snap 2

// Camera settings
#define CAMERA_FRAME_SIZE FRAMESIZE_VGA   // VGA (640x480) is good for testing
#define CAMERA_JPEG_QUALITY 10             // 0-63, lower = better quality

// Printing settings
#define NUM_COPIES 1

// Button for manual trigger (optional)
#define BUTTON_PIN 14  // GPIO14, set to -1 to disable
#define BUTTON_ACTIVE_LOW true

// ===== GLOBAL OBJECTS =====

KodakStepPrinter printer;
ESP32CameraHelper camera;

// ===== SETUP =====

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n\n=================================");
    Serial.println("ESP32-CAM Kodak Step Printer");
    Serial.println("=================================\n");

    // Initialize button if configured
    if (BUTTON_PIN >= 0) {
        pinMode(BUTTON_PIN, BUTTON_ACTIVE_LOW ? INPUT_PULLUP : INPUT);
        Serial.println("Button configured on GPIO" + String(BUTTON_PIN));
    }

    // Initialize camera
    Serial.println("Initializing camera...");
    if (!camera.begin(CAMERA_FRAME_SIZE, CAMERA_JPEG_QUALITY)) {
        Serial.println("FATAL: Camera initialization failed!");
        Serial.println("Check camera connections and restart.");
        while (1) {
            delay(1000);
        }
    }

    // Initialize Bluetooth
    Serial.println("Initializing Bluetooth...");
    if (!printer.begin("ESP32-Kodak")) {
        Serial.println("FATAL: Bluetooth initialization failed!");
        while (1) {
            delay(1000);
        }
    }

    // Connect to printer
    Serial.println("Connecting to printer...");
    bool connected = false;

#if USE_PRINTER_NAME
    connected = printer.connectByName(PRINTER_NAME);
#else
    connected = printer.connect(PRINTER_ADDRESS);
#endif

    if (!connected) {
        Serial.println("FATAL: Failed to connect to printer!");
        Serial.println("Make sure printer is powered on and in range.");
        Serial.println("Error: " + String(printer.getLastError()));
        while (1) {
            delay(1000);
        }
    }

    // Initialize printer communication
    Serial.println("Initializing printer...");
    if (!printer.initialize(IS_SLIM_DEVICE)) {
        Serial.println("FATAL: Failed to initialize printer!");
        Serial.println("Error: " + String(printer.getLastError()));
        while (1) {
            delay(1000);
        }
    }

    Serial.println("\n=== Setup Complete ===\n");
    Serial.println("Press the button to print, or wait for auto-print...\n");

    // Auto-print after 3 seconds
    delay(3000);
    captureAndPrint();
}

// ===== MAIN LOOP =====

void loop() {
    // Check button press
    if (BUTTON_PIN >= 0) {
        bool buttonPressed = digitalRead(BUTTON_PIN);
        if (BUTTON_ACTIVE_LOW) {
            buttonPressed = !buttonPressed;
        }

        if (buttonPressed) {
            Serial.println("\nButton pressed!");
            delay(50);  // Debounce
            captureAndPrint();

            // Wait for button release
            while (digitalRead(BUTTON_PIN) == (BUTTON_ACTIVE_LOW ? LOW : HIGH)) {
                delay(10);
            }
            delay(200);  // Additional debounce
        }
    }

    delay(100);
}

// ===== HELPER FUNCTIONS =====

void captureAndPrint() {
    Serial.println("\n=== Starting Print Job ===\n");

    // Check printer status
    uint8_t battery;
    if (printer.getBatteryLevel(&battery)) {
        Serial.print("Printer battery: ");
        Serial.print(battery);
        Serial.println("%");

        if (battery < KODAK_MIN_BATTERY_LEVEL) {
            Serial.println("ERROR: Battery too low to print!");
            return;
        }
    } else {
        Serial.println("Warning: Could not read battery level");
    }

    // Capture image
    Serial.println("\nCapturing image...");
    camera_fb_t* fb = camera.captureImage();

    if (fb == nullptr) {
        Serial.println("ERROR: Failed to capture image!");
        return;
    }

    Serial.print("Captured ");
    Serial.print(fb->len);
    Serial.println(" bytes");

    // Print image
    Serial.println("\nSending to printer...");
    bool success = printer.printImage(fb->buf, fb->len, NUM_COPIES);

    // Release frame buffer
    camera.releaseImage(fb);

    if (success) {
        Serial.println("\n=== Print Job Complete ===");
        Serial.println("Check your printer!\n");

        // Flash LED to indicate success
        camera.flashBlink(3, 100);
    } else {
        Serial.println("\n=== Print Job Failed ===");
        Serial.println("Error: " + String(printer.getLastError()));
        Serial.println();

        // Flash LED rapidly to indicate error
        camera.flashBlink(10, 50);
    }
}

void printSystemInfo() {
    Serial.println("\n=== System Info ===");
    Serial.print("ESP32 Chip ID: ");
    Serial.println((uint32_t)ESP.getEfuseMac(), HEX);
    Serial.print("Free Heap: ");
    Serial.print(ESP.getFreeHeap());
    Serial.println(" bytes");
    Serial.print("CPU Frequency: ");
    Serial.print(ESP.getCpuFreqMHz());
    Serial.println(" MHz");
    Serial.println("===================\n");
}
