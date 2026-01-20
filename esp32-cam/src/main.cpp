/**
 * ESP32-CAM Kodak Step Printer
 * Captures photos and prints them on a Kodak Step printer via Bluetooth
 */

#include <Arduino.h>
#include <KodakStep.h>
#include "ESP32CameraHelper.h"

// Configuration
const char* PRINTER_SEARCH_NAME = "Step";  // Printer name to search for
const uint8_t NUM_COPIES = 1;

KodakStepPrinter printer;
ESP32CameraHelper camera;

void printStatus() {
    KodakStepProtocol::PrinterStatus status = printer.getStatus();
    Serial.println("\n=== Printer Status ===");
    Serial.print("Connected:   ");
    Serial.println(status.is_connected ? "YES" : "NO");
    Serial.print("Battery:     ");
    Serial.print(status.battery_level);
    Serial.println("%");
    Serial.print("Slim Device: ");
    Serial.println(status.is_slim_device ? "YES" : "NO");
    Serial.print("Error Code:  ");
    Serial.println(status.error_code);
    if (status.error_code != ERR_SUCCESS) {
        Serial.print("Error:       ");
        Serial.println(KodakStepProtocol::getErrorString(status.error_code));
    }
    Serial.println("======================\n");
}

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n\n==========================================");
    Serial.println("ESP32-CAM Kodak Step Printer");
    Serial.println("==========================================\n");

    // Initialize camera
    Serial.println("Initializing camera...");
    if (!camera.begin(FRAMESIZE_VGA, 10)) {
        Serial.println("FATAL: Camera initialization failed");
        return;
    }
    Serial.println("Camera initialized");

    // Initialize Bluetooth
    Serial.println("Initializing Bluetooth...");
    if (!printer.begin("ESP32-Kodak")) {
        Serial.println("FATAL: Bluetooth initialization failed");
        return;
    }

    // Connect to printer by name
    Serial.print("Searching for printer containing '");
    Serial.print(PRINTER_SEARCH_NAME);
    Serial.println("'...");

    if (!printer.connectByName(PRINTER_SEARCH_NAME)) {
        Serial.println("ERROR: Failed to connect to printer");
        Serial.print("Error: ");
        Serial.println(printer.getLastError());
        return;
    }

    // Initialize printer protocol
    Serial.println("Initializing printer...");
    if (!printer.initialize(false)) {
        Serial.println("WARNING: Printer initialization returned error");
        Serial.print("Error: ");
        Serial.println(printer.getLastError());
        // Continue anyway - this might just be a paper status warning
    }

    // Query and display status
    uint8_t battery = 0;
    if (printer.getBatteryLevel(&battery)) {
        Serial.print("Battery level: ");
        Serial.print(battery);
        Serial.println("%");
    }

    printStatus();

    Serial.println("\n=== Ready ===");
    Serial.println("Press the boot button or send 'p' via Serial to capture and print");
    Serial.println("Send 's' to check printer status");
}

void captureAndPrint() {
    Serial.println("\n=== Capture and Print ===");

    // Check connection
    if (!printer.isConnected()) {
        Serial.println("ERROR: Printer not connected");
        return;
    }

    // Capture image
    Serial.println("Capturing image...");
    camera_fb_t* fb = camera.captureImage();
    if (fb == nullptr) {
        Serial.println("ERROR: Failed to capture image");
        return;
    }

    Serial.print("Image captured: ");
    Serial.print(fb->len);
    Serial.println(" bytes");

    // Print the image
    Serial.println("Sending to printer...");
    bool success = printer.printImage(fb->buf, fb->len, NUM_COPIES);

    // Release the frame buffer
    camera.releaseImage(fb);

    if (success) {
        Serial.println("Print job sent successfully!");
    } else {
        Serial.println("Print failed!");
        Serial.print("Error: ");
        Serial.println(printer.getLastError());
    }

    printStatus();
}

void loop() {
    // Check for serial input
    if (Serial.available()) {
        char c = Serial.read();
        if (c == 'p' || c == 'P') {
            captureAndPrint();
        } else if (c == 's' || c == 'S') {
            // Refresh status
            uint8_t battery = 0;
            printer.getBatteryLevel(&battery);
            printStatus();
        }
    }

    // Check boot button (GPIO0 on ESP32-CAM)
    static bool lastButtonState = HIGH;
    bool buttonState = digitalRead(0);
    if (lastButtonState == HIGH && buttonState == LOW) {
        delay(50);  // Debounce
        if (digitalRead(0) == LOW) {
            captureAndPrint();
        }
    }
    lastButtonState = buttonState;

    delay(10);
}
