/**
 * Kodak Step Printer Connection Test
 *
 * This simpler example tests the Bluetooth connection and printer
 * communication without requiring the camera.
 *
 * Use this to verify your printer connection before attempting to print.
 */

#include "KodakStepPrinter.h"

// ===== CONFIGURATION =====

// Printer connection
const char* PRINTER_NAME = "Step";  // Part of printer name
const char* PRINTER_ADDRESS = "XX:XX:XX:XX:XX:XX";  // Or use MAC address

// Device type
#define IS_SLIM_DEVICE false

// ===== GLOBAL OBJECTS =====

KodakStepPrinter printer;

// ===== SETUP =====

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n\n=================================");
    Serial.println("Kodak Step Printer Connection Test");
    Serial.println("=================================\n");

    // Initialize Bluetooth
    Serial.println("Initializing Bluetooth...");
    if (!printer.begin("ESP32-Kodak-Test")) {
        Serial.println("FATAL: Bluetooth initialization failed!");
        while (1) delay(1000);
    }

    // Connect to printer
    Serial.println("Connecting to printer...");
    if (!printer.connectByName(PRINTER_NAME)) {
        Serial.println("FATAL: Failed to connect to printer!");
        Serial.println("Error: " + String(printer.getLastError()));
        while (1) delay(1000);
    }

    // Initialize printer
    Serial.println("Initializing printer...");
    if (!printer.initialize(IS_SLIM_DEVICE)) {
        Serial.println("FATAL: Failed to initialize printer!");
        Serial.println("Error: " + String(printer.getLastError()));
        while (1) delay(1000);
    }

    // Get battery level
    uint8_t battery;
    if (printer.getBatteryLevel(&battery)) {
        Serial.print("Battery level: ");
        Serial.print(battery);
        Serial.println("%");
    }

    // Check paper
    if (printer.checkPaperStatus()) {
        Serial.println("Paper status: OK");
    } else {
        Serial.println("Paper status: Check printer");
    }

    Serial.println("\n=== Connection Test Complete ===");
    Serial.println("Printer is ready to use!\n");
}

void loop() {
    // Nothing to do
    delay(1000);
}
