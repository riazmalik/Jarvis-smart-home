#include "gesture.h"
#include "relay_control.h"
#include "esp_log.h"

static const char *TAG = "GESTURE";

void init_gesture(void) {
    ESP_LOGI(TAG, "🖐️ Gesture control initialized");
    // Future: Initialize gesture sensor (APDS-9960)
}

void process_gesture_commands(void) {
    // Future: Read from gesture sensor
    // For now, this is a placeholder
}