/**
 * ESP32-CAM Kodak Step Printer - Print Test
 * Captures an image and prints it to a connected Kodak Step printer
 */

#include <Arduino.h>
#include "KodakStepPrinter.h"
#include "ESP32CameraHelper.h"

KodakStepPrinter printer;
ESP32CameraHelper camera;
bool printAttempted = false;

void captureAndPrint() {
    Serial.println("\n=== Starting Print Job ===\n");

    // Capture image
    Serial.println("Capturing image...");
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
    bool success = printer.printImage(fb->buf, fb->len, 1);

    // Release frame buffer
    camera.releaseImage(fb);

    if (success) {
        Serial.println("\n=== Print Job Complete ===");
        Serial.println("Check your printer!\n");
        camera.flashBlink(3, 100);
    } else {
        Serial.println("\n=== Print Job Failed ===");
        Serial.print("Error: ");
        Serial.println(printer.getLastError());
        camera.flashBlink(10, 50);
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n\n=================================");
    Serial.println("ESP32-CAM Kodak Step Printer Test");
    Serial.println("=================================\n");

    // Initialize camera
    Serial.println("Initializing camera...");
    if (!camera.begin(FRAMESIZE_VGA, 10)) {
        Serial.println("FATAL: Camera init failed");
        while (1) delay(1000);
    }

    // Initialize Bluetooth
    Serial.println("Initializing Bluetooth...");
    if (!printer.begin("ESP32-Kodak")) {
        Serial.println("FATAL: Bluetooth init failed");
        while (1) delay(1000);
    }

    // Connect to printer by name (searches for "Step" in device name)
    Serial.println("Searching for Kodak Step printer...");
    if (!printer.connectByName("Step")) {
        Serial.println("FATAL: Failed to connect to printer!");
        Serial.print("Error: ");
        Serial.println(printer.getLastError());
        while (1) delay(1000);
    }

    // Initialize printer protocol
    Serial.println("Initializing printer protocol...");
    if (!printer.initialize(false)) {
        Serial.println("FATAL: Failed to initialize printer!");
        Serial.print("Error: ");
        Serial.println(printer.getLastError());
        while (1) delay(1000);
    }

    Serial.println("\n=== Setup Complete ===\n");
    Serial.println("Starting print in 3 seconds...\n");
    delay(3000);

    // Attempt to print
    captureAndPrint();
    printAttempted = true;
}

void loop() {
    if (printAttempted) {
        Serial.println("Print attempt finished. Idling...");
        printAttempted = false;
    }
    delay(5000);
}
