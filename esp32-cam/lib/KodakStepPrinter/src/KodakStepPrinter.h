#ifndef KODAK_STEP_PRINTER_H
#define KODAK_STEP_PRINTER_H

#include <Arduino.h>
#include "BluetoothSerial.h"
#include "KodakStepProtocol.h"

// Progress callback for image transfer: (bytesSent, totalBytes)
typedef void (*KodakProgressCallback)(size_t bytesSent, size_t totalBytes);

/**
 * High-level interface for Kodak Step Printer
 * Manages Bluetooth connection, protocol flow, and image transfer
 *
 * Supported printers:
 *   - Kodak Step
 *   - Kodak Step Touch
 *   - Kodak Step Slim
 *   - Kodak Step Touch Snap 2
 *
 * Basic usage:
 *   KodakStepPrinter printer;
 *   printer.begin("MyDevice");
 *   printer.connectByName("Step");
 *   printer.initialize();
 *   printer.printImage(jpegData, jpegSize);
 */
class KodakStepPrinter {
public:
    KodakStepPrinter();
    ~KodakStepPrinter();

    // Prevent copying (contains heap-allocated BluetoothSerial)
    KodakStepPrinter(const KodakStepPrinter&) = delete;
    KodakStepPrinter& operator=(const KodakStepPrinter&) = delete;

    // Connection management
    bool begin(const char* deviceName = "ESP32-Kodak");
    bool connect(const char* printerAddress);
    bool connectByName(const char* printerName);
    void disconnect();
    bool isConnected();

    // Printer operations
    bool initialize(bool isSlimDevice = false, uint8_t* rawResponse = nullptr);
    bool getBatteryLevel(uint8_t* level, uint8_t* rawResponse = nullptr);
    bool getChargingStatus(bool* isCharging, uint8_t* rawResponse = nullptr);
    bool checkPaperStatus();
    bool getPrintCount(uint16_t* count);
    bool getAutoPowerOff(uint8_t* minutes);

    // Printing
    bool printImage(const uint8_t* jpegData, size_t dataSize, uint8_t numCopies = 1,
                    KodakProgressCallback progressCallback = nullptr);

    // Status
    KodakStepProtocol::PrinterStatus getStatus() const;
    const char* getLastError() const;

    // Configuration
    void setDebugOutput(bool enabled);
    bool getDebugOutput() const;

private:
    BluetoothSerial* btSerial;
    KodakStepProtocol protocol;
    KodakStepProtocol::PrinterStatus status;
    char lastError[128];
    bool debugEnabled;

    // Communication helpers (skipConnectionCheck for internal use after already checking)
    bool sendCommand(const uint8_t* command, size_t length, bool skipConnectionCheck = false);
    bool receiveResponse(uint8_t* response, uint32_t timeoutMs = KODAK_COMMAND_TIMEOUT_MS);
    bool sendAndReceive(const uint8_t* command, uint8_t* response);

    // Image transfer
    bool transferImageData(const uint8_t* data, size_t size, KodakProgressCallback progressCallback);

    // Utility
    void setError(const char* error);
    void debugPrint(const char* msg);
    void debugPrintln(const char* msg);
};

#endif // KODAK_STEP_PRINTER_H
