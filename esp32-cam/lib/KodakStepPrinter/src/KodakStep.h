/**
 * KodakStepPrinter Library
 *
 * Arduino library for communicating with Kodak Step series Zink printers
 * via Bluetooth Classic SPP.
 *
 * Supported printers:
 *   - Kodak Step
 *   - Kodak Step Touch
 *   - Kodak Step Slim
 *   - Kodak Step Touch Snap 2
 *
 * Requirements:
 *   - ESP32 with Bluetooth Classic support
 *   - Arduino framework
 *
 * Basic usage:
 *   #include <KodakStep.h>
 *
 *   KodakStepPrinter printer;
 *
 *   void setup() {
 *       printer.begin("MyESP32");
 *       printer.connectByName("Step");
 *       printer.initialize();
 *   }
 *
 *   void printPhoto(uint8_t* jpeg, size_t size) {
 *       printer.printImage(jpeg, size);
 *   }
 *
 * For more information, see the protocol documentation at:
 *   docs/KODAK_STEP_PROTOCOL.md
 */

#ifndef KODAK_STEP_H
#define KODAK_STEP_H

#include "KodakStepProtocol.h"
#include "KodakStepPrinter.h"

#endif // KODAK_STEP_H
