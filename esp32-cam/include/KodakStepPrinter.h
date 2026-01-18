#ifndef KODAK_STEP_PRINTER_H
#define KODAK_STEP_PRINTER_H

#include <Arduino.h>
#include "BluetoothSerial.h"
#include "KodakStepProtocol.h"

// SPP UUID for Kodak Step printers
#define KODAK_SPP_UUID "00001101-0000-1000-8000-00805F9B34FB"

/**
 * High-level interface for Kodak Step Printer
 * Manages Bluetooth connection, protocol flow, and image transfer
 */
class KodakStepPrinter {
public:
    KodakStepPrinter();
    ~KodakStepPrinter();

    // Connection management
    bool begin(const char* deviceName = "ESP32-Kodak");
    bool connect(const char* printerAddress);
    bool connectByName(const char* printerName);
    void disconnect();
    bool isConnected();

    // Printer operations
    bool initialize(bool isSlimDevice = false);
    bool getBatteryLevel(uint8_t* level);
    bool checkPaperStatus();
    bool getPrintCount(uint16_t* count);
    bool getAutoPowerOff(uint8_t* minutes);

    // Printing
    bool printImage(const uint8_t* jpegData, size_t dataSize, uint8_t numCopies = 1);

    // Status
    KodakStepProtocol::PrinterStatus getStatus();
    const char* getLastError();

private:
    BluetoothSerial* btSerial;
    KodakStepProtocol protocol;
    KodakStepProtocol::PrinterStatus status;
    char lastError[128];

    // Communication helpers
    bool sendCommand(const uint8_t* command, size_t length);
    bool receiveResponse(uint8_t* response, uint32_t timeoutMs = KODAK_COMMAND_TIMEOUT_MS);
    bool sendAndReceive(const uint8_t* command, uint8_t* response);

    // Image transfer
    bool transferImageData(const uint8_t* data, size_t size);

    // Utility
    void setError(const char* error);
    void delay_ms(uint32_t ms);
};

#endif // KODAK_STEP_PRINTER_H
