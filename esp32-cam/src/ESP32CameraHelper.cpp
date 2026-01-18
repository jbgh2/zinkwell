#include "ESP32CameraHelper.h"

ESP32CameraHelper::ESP32CameraHelper() {
    initialized = false;
}

void ESP32CameraHelper::initConfig() {
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_sscb_sda = SIOD_GPIO_NUM;
    config.pin_sscb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;

    // Frame buffer configuration
    config.frame_size = FRAMESIZE_UXGA;  // Default: 1600x1200
    config.jpeg_quality = 10;            // 0-63, lower = higher quality
    config.fb_count = 1;                 // Number of frame buffers
    config.grab_mode = CAMERA_GRAB_LATEST;
}

bool ESP32CameraHelper::begin(framesize_t frameSize, int jpegQuality) {
    if (initialized) {
        Serial.println("Camera already initialized");
        return true;
    }

    // Initialize flash LED pin
    pinMode(FLASH_GPIO_NUM, OUTPUT);
    digitalWrite(FLASH_GPIO_NUM, LOW);

    // Setup camera configuration
    initConfig();
    config.frame_size = frameSize;
    config.jpeg_quality = jpegQuality;

    // Initialize camera
    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.print("Camera init failed with error 0x");
        Serial.println(err, HEX);
        return false;
    }

    initialized = true;

    // Get sensor for additional configuration
    sensor_t* s = esp_camera_sensor_get();
    if (s != NULL) {
        // Optional: Set some default sensor settings
        // s->set_brightness(s, 0);     // -2 to 2
        // s->set_contrast(s, 0);       // -2 to 2
        // s->set_saturation(s, 0);     // -2 to 2
        // s->set_special_effect(s, 0); // 0 to 6 (0 - No Effect)
        // s->set_whitebal(s, 1);       // 0 = disable , 1 = enable
        // s->set_awb_gain(s, 1);       // 0 = disable , 1 = enable
        // s->set_wb_mode(s, 0);        // 0 to 4
    }

    Serial.println("Camera initialized successfully");
    printCameraInfo();

    return true;
}

void ESP32CameraHelper::end() {
    if (initialized) {
        esp_camera_deinit();
        initialized = false;
        Serial.println("Camera deinitialized");
    }
}

camera_fb_t* ESP32CameraHelper::captureImage() {
    if (!initialized) {
        Serial.println("Camera not initialized");
        return nullptr;
    }

    Serial.println("Capturing image...");

    // Flash briefly for better lighting (optional)
    // flashBlink(1, 50);

    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) {
        Serial.println("Camera capture failed");
        return nullptr;
    }

    Serial.print("Image captured: ");
    Serial.print(fb->width);
    Serial.print("x");
    Serial.print(fb->height);
    Serial.print(" - ");
    Serial.print(fb->len);
    Serial.println(" bytes");

    return fb;
}

void ESP32CameraHelper::releaseImage(camera_fb_t* fb) {
    if (fb != nullptr) {
        esp_camera_fb_return(fb);
    }
}

void ESP32CameraHelper::setFlash(bool on) {
    digitalWrite(FLASH_GPIO_NUM, on ? HIGH : LOW);
}

void ESP32CameraHelper::flashBlink(int times, int delayMs) {
    for (int i = 0; i < times; i++) {
        setFlash(true);
        delay(delayMs);
        setFlash(false);
        if (i < times - 1) {
            delay(delayMs);
        }
    }
}

bool ESP32CameraHelper::setFrameSize(framesize_t size) {
    if (!initialized) {
        return false;
    }

    sensor_t* s = esp_camera_sensor_get();
    if (s == nullptr) {
        return false;
    }

    return (s->set_framesize(s, size) == 0);
}

bool ESP32CameraHelper::setJpegQuality(int quality) {
    if (!initialized) {
        return false;
    }

    sensor_t* s = esp_camera_sensor_get();
    if (s == nullptr) {
        return false;
    }

    return (s->set_quality(s, quality) == 0);
}

bool ESP32CameraHelper::setVFlip(bool enable) {
    if (!initialized) {
        return false;
    }

    sensor_t* s = esp_camera_sensor_get();
    if (s == nullptr) {
        return false;
    }

    return (s->set_vflip(s, enable ? 1 : 0) == 0);
}

bool ESP32CameraHelper::setHMirror(bool enable) {
    if (!initialized) {
        return false;
    }

    sensor_t* s = esp_camera_sensor_get();
    if (s == nullptr) {
        return false;
    }

    return (s->set_hmirror(s, enable ? 1 : 0) == 0);
}

bool ESP32CameraHelper::isInitialized() {
    return initialized;
}

void ESP32CameraHelper::printCameraInfo() {
    if (!initialized) {
        Serial.println("Camera not initialized");
        return;
    }

    sensor_t* s = esp_camera_sensor_get();
    if (s == nullptr) {
        Serial.println("Failed to get camera sensor");
        return;
    }

    Serial.println("\n=== Camera Info ===");
    Serial.print("Sensor PID: 0x");
    Serial.println(s->id.PID, HEX);

    // Frame size names
    const char* frameSizeNames[] = {
        "96x96",    // FRAMESIZE_96X96
        "QQVGA",    // FRAMESIZE_QQVGA (160x120)
        "QCIF",     // FRAMESIZE_QCIF (176x144)
        "HQVGA",    // FRAMESIZE_HQVGA (240x176)
        "240x240",  // FRAMESIZE_240X240
        "QVGA",     // FRAMESIZE_QVGA (320x240)
        "CIF",      // FRAMESIZE_CIF (400x296)
        "HVGA",     // FRAMESIZE_HVGA (480x320)
        "VGA",      // FRAMESIZE_VGA (640x480)
        "SVGA",     // FRAMESIZE_SVGA (800x600)
        "XGA",      // FRAMESIZE_XGA (1024x768)
        "HD",       // FRAMESIZE_HD (1280x720)
        "SXGA",     // FRAMESIZE_SXGA (1280x1024)
        "UXGA"      // FRAMESIZE_UXGA (1600x1200)
    };

    framesize_t frameSize = (framesize_t)s->status.framesize;
    Serial.print("Frame size: ");
    if (frameSize < (sizeof(frameSizeNames) / sizeof(frameSizeNames[0]))) {
        Serial.println(frameSizeNames[frameSize]);
    } else {
        Serial.println(frameSize);
    }

    Serial.print("JPEG quality: ");
    Serial.println(s->status.quality);

    Serial.println("===================\n");
}
