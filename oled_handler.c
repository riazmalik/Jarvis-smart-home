#include "oled_handler.h"
#include "esp_log.h"

static const char *TAG = "OLED";

void init_oled(void) {
    ESP_LOGI(TAG, "🖥️ OLED display initialized");
    // Future: Initialize SSD1306 via I2C
}

void update_oled_display(void) {
    // Future: Update OLED with bulb status
}