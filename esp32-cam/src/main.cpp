/**
 * ESP32-CAM Kodak Step Printer - Battery Investigation
 * WiFi endpoint to query printer status without needing paper
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include "KodakStepPrinter.h"
#include "ESP32CameraHelper.h"

// WiFi credentials - using AP mode for easy access
const char* AP_SSID = "ESP32-Kodak";
const char* AP_PASS = "kodaktest";

KodakStepPrinter printer;
ESP32CameraHelper camera;
WebServer server(80);
bool printerConnected = false;

// Store last raw responses for debugging
uint8_t lastBatteryResponse[34];
uint8_t lastAccessoryResponse[34];
bool hasLastResponse = false;
bool hasAccessoryResponse = false;

void handleRoot() {
    String html = "<html><head><title>Kodak Printer Debug</title>";
    html += "<meta http-equiv='refresh' content='5'>";  // Auto-refresh every 5s
    html += "<style>body{font-family:monospace;padding:20px;} pre{background:#f0f0f0;padding:10px;}</style>";
    html += "</head><body>";
    html += "<h1>Kodak Step Printer Debug</h1>";
    html += "<p>Printer connected: " + String(printerConnected ? "YES" : "NO") + "</p>";
    html += "<p><a href='/battery'>Query Battery</a> | <a href='/status'>Full Status</a></p>";
    html += "</body></html>";
    server.send(200, "text/html", html);
}

void handleBattery() {
    String html = "<html><head><title>Battery Query</title>";
    html += "<style>body{font-family:monospace;padding:20px;} pre{background:#f0f0f0;padding:10px;overflow-x:auto;}</style>";
    html += "</head><body>";
    html += "<h1>Battery Query Result</h1>";

    if (!printerConnected || !printer.isConnected()) {
        html += "<p style='color:red'>Printer not connected!</p>";
    } else {
        uint8_t battery = 0;
        bool success = printer.getBatteryLevel(&battery, lastBatteryResponse);
        hasLastResponse = success;

        html += "<p>Query success: " + String(success ? "YES" : "NO") + "</p>";
        html += "<p>Parsed battery level: " + String(battery) + "%</p>";

        if (hasLastResponse) {
            html += "<h2>Raw Response (34 bytes):</h2><pre>";
            for (int i = 0; i < 34; i++) {
                char hex[6];
                sprintf(hex, "%02X ", lastBatteryResponse[i]);
                html += hex;
                if ((i + 1) % 16 == 0) html += "\n";
            }
            html += "</pre>";

            html += "<h2>Byte Analysis:</h2><pre>";
            html += "Byte 0-3 (Header): ";
            for (int i = 0; i < 4; i++) {
                char hex[6]; sprintf(hex, "%02X ", lastBatteryResponse[i]); html += hex;
            }
            html += "\nByte 4-5 (Flags):  ";
            for (int i = 4; i < 6; i++) {
                char hex[6]; sprintf(hex, "%02X ", lastBatteryResponse[i]); html += hex;
            }
            html += "\nByte 6 (Cmd):      " + String(lastBatteryResponse[6], HEX);
            html += "\nByte 7 (Sub):      " + String(lastBatteryResponse[7], HEX);
            html += "\nByte 8 (Data/Err): " + String(lastBatteryResponse[8]) + " (0x" + String(lastBatteryResponse[8], HEX) + ")";
            html += "\nByte 9-15:         ";
            for (int i = 9; i < 16; i++) {
                char hex[6]; sprintf(hex, "%02X ", lastBatteryResponse[i]); html += hex;
            }
            html += "</pre>";

            // Show all bytes that could be battery (looking for value 50-100 range)
            html += "<h2>Potential Battery Bytes (values 30-100):</h2><pre>";
            for (int i = 0; i < 34; i++) {
                uint8_t val = lastBatteryResponse[i];
                if (val >= 30 && val <= 100) {
                    char info[64];
                    sprintf(info, "Byte %2d = %3d (0x%02X)\n", i, val, val);
                    html += info;
                }
            }
            html += "</pre>";

            // Also show interpretation if byte 6 indicates response type
            html += "<h2>Response Analysis:</h2><pre>";
            html += "Response type (byte 6): 0x" + String(lastBatteryResponse[6], HEX);
            if (lastBatteryResponse[6] == 0x04) {
                html += " (general status response, not battery-specific)\n";
                html += "Battery may be in GET_ACCESSORY_INFO response instead.\n";
                html += "Byte 8 value " + String(lastBatteryResponse[8]) + " might be charging status.\n";
            } else if (lastBatteryResponse[6] == 0x0E) {
                html += " (battery response - byte 8 should be level)\n";
            }
            html += "</pre>";

            // Show what we think the battery actually is
            html += "<h2>HYPOTHESIS:</h2><pre>";
            html += "GET_BATTERY_LEVEL returns response type 0x04\n";
            html += "Byte 8 = " + String(lastBatteryResponse[8]) + " might be:\n";
            html += "  - Charging status (1 = charging?)\n";
            html += "  - Or battery level is in GET_ACCESSORY_INFO byte 12\n";
            html += "</pre>";
        }
    }

    html += "<p><a href='/'>Back</a> | <a href='/battery'>Refresh</a></p>";
    html += "</body></html>";
    server.send(200, "text/html", html);
}

void handleStatus() {
    String html = "<html><head><title>Full Status</title>";
    html += "<style>body{font-family:monospace;padding:20px;} pre{background:#f0f0f0;padding:10px;}</style>";
    html += "</head><body>";
    html += "<h1>Full Printer Status</h1>";

    if (!printerConnected || !printer.isConnected()) {
        html += "<p style='color:red'>Printer not connected!</p>";
    } else {
        KodakStepProtocol::PrinterStatus status = printer.getStatus();
        html += "<pre>";
        html += "Connected:    " + String(status.is_connected ? "YES" : "NO") + "\n";
        html += "Battery:      " + String(status.battery_level) + "%\n";
        html += "Slim Device:  " + String(status.is_slim_device ? "YES" : "NO") + "\n";
        html += "Error Code:   " + String(status.error_code) + "\n";
        html += "Last Error:   " + String(printer.getLastError()) + "\n";
        html += "</pre>";

        if (hasAccessoryResponse) {
            html += "<h2>Last Accessory Info Response:</h2><pre>";
            for (int i = 0; i < 34; i++) {
                char hex[6];
                sprintf(hex, "%02X ", lastAccessoryResponse[i]);
                html += hex;
                if ((i + 1) % 16 == 0) html += "\n";
            }
            html += "</pre>";

            html += "<h2>Accessory Info Analysis:</h2><pre>";
            html += "Byte 8 (error):      " + String(lastAccessoryResponse[8]) + "\n";
            html += "Byte 10:             " + String(lastAccessoryResponse[10]) + " (0x" + String(lastAccessoryResponse[10], HEX) + ")\n";
            html += "Byte 11:             " + String(lastAccessoryResponse[11]) + " (0x" + String(lastAccessoryResponse[11], HEX) + ")\n";
            html += "Byte 12:             " + String(lastAccessoryResponse[12]) + " (0x" + String(lastAccessoryResponse[12], HEX) + ") <- possible battery?\n";

            // Show MAC address extraction
            html += "\nMAC Address (bytes 15-20): ";
            for (int i = 15; i <= 20; i++) {
                char hex[4];
                sprintf(hex, "%02X", lastAccessoryResponse[i]);
                html += hex;
                if (i < 20) html += ":";
            }
            html += "\n</pre>";
        }
    }

    html += "<p><a href='/'>Back</a></p>";
    html += "</body></html>";
    server.send(200, "text/html", html);
}

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n\n==========================================");
    Serial.println("ESP32-CAM Kodak Printer - Battery Debug");
    Serial.println("==========================================\n");

    // Start WiFi AP
    Serial.println("Starting WiFi Access Point...");
    WiFi.softAP(AP_SSID, AP_PASS);
    IPAddress IP = WiFi.softAPIP();
    Serial.print("AP IP address: ");
    Serial.println(IP);
    Serial.print("Connect to WiFi: ");
    Serial.print(AP_SSID);
    Serial.print(" / ");
    Serial.println(AP_PASS);

    // Setup web server routes
    server.on("/", handleRoot);
    server.on("/battery", handleBattery);
    server.on("/status", handleStatus);
    server.begin();
    Serial.println("HTTP server started on port 80");

    // Initialize camera (minimal, just for the helper)
    Serial.println("Initializing camera...");
    if (!camera.begin(FRAMESIZE_VGA, 10)) {
        Serial.println("WARNING: Camera init failed - continuing anyway");
    }

    // Initialize Bluetooth
    Serial.println("Initializing Bluetooth...");
    if (!printer.begin("ESP32-Kodak")) {
        Serial.println("FATAL: Bluetooth init failed");
        return;
    }

    // Connect to printer by name
    Serial.println("Searching for Kodak Step printer...");
    if (!printer.connectByName("Step")) {
        Serial.println("WARNING: Failed to connect to printer");
        Serial.print("Error: ");
        Serial.println(printer.getLastError());
        Serial.println("Web interface still available to retry later");
    } else {
        printerConnected = true;
        Serial.println("Printer connected!");

        // Query both accessory info and battery to compare
        Serial.println("\n=== Testing Protocol Responses ===");

        // First, send GET_ACCESSORY_INFO and see full response
        Serial.println("\n--- GET_ACCESSORY_INFO ---");
        if (printer.initialize(false, lastAccessoryResponse)) {
            hasAccessoryResponse = true;
            Serial.println("Initialize succeeded");
            Serial.print("Byte 12 (possible battery): ");
            Serial.println(lastAccessoryResponse[12]);
        } else {
            // Still capture response even on "error"
            hasAccessoryResponse = true;
            Serial.println("Initialize failed (expected - no paper)");
            Serial.print("Byte 12 (possible battery): ");
            Serial.println(lastAccessoryResponse[12]);
        }

        delay(500);

        // Now query battery
        Serial.println("\n--- GET_BATTERY_LEVEL ---");
        uint8_t battery = 0;
        if (printer.getBatteryLevel(&battery, lastBatteryResponse)) {
            hasLastResponse = true;
            Serial.print("Battery level parsed: ");
            Serial.print(battery);
            Serial.println("%");
        } else {
            Serial.println("Battery query failed");
        }
    }

    Serial.println("\n=== Ready ===");
    Serial.print("Open http://");
    Serial.print(IP);
    Serial.println("/ in your browser");
}

void loop() {
    server.handleClient();
    delay(10);
}
