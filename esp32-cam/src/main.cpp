/**
 * Main compilation test file for PlatformIO
 * This is a simplified version of the examples for compilation testing
 */

#include <Arduino.h>
#include "KodakStepPrinter.h"
#include "ESP32CameraHelper.h"

KodakStepPrinter printer;
ESP32CameraHelper camera;

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("ESP32-CAM Kodak Step Printer - Compilation Test");

    // Initialize camera
    if (!camera.begin(FRAMESIZE_VGA, 10)) {
        Serial.println("Camera init failed");
        return;
    }

    // Initialize Bluetooth
    if (!printer.begin("ESP32-Test")) {
        Serial.println("Bluetooth init failed");
        return;
    }

    Serial.println("Initialization complete");
}

void loop() {
    delay(1000);
}
