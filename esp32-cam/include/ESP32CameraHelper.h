#ifndef ESP32_CAMERA_HELPER_H
#define ESP32_CAMERA_HELPER_H

#include <Arduino.h>
#include "esp_camera.h"

// Camera pin definitions for AI-Thinker ESP32-CAM
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// Flash LED pin
#define FLASH_GPIO_NUM     4

/**
 * Helper class for ESP32-CAM image capture
 */
class ESP32CameraHelper {
public:
    ESP32CameraHelper();

    // Initialization
    bool begin(framesize_t frameSize = FRAMESIZE_UXGA, int jpegQuality = 10);
    void end();

    // Image capture
    camera_fb_t* captureImage();
    void releaseImage(camera_fb_t* fb);

    // Flash control
    void setFlash(bool on);
    void flashBlink(int times = 1, int delayMs = 100);

    // Camera settings
    bool setFrameSize(framesize_t size);
    bool setJpegQuality(int quality);
    bool setVFlip(bool enable);
    bool setHMirror(bool enable);

    // Status
    bool isInitialized();
    void printCameraInfo();

private:
    bool initialized;
    camera_config_t config;

    void initConfig();
};

#endif // ESP32_CAMERA_HELPER_H
