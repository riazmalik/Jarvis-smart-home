#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_log.h"
#include "nvs_flash.h"

#include "relay_control.h"
#include "urdu_voice.h"
#include "webserver.h"
#include "gesture.h"
#include "audio_handler.h"
#include "oled_handler.h"

static const char *TAG = "JARVIS_MAIN";

void app_main(void) {
    ESP_LOGI(TAG, "🚀 Starting Jarvis Smart Home...");
    
    // Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    
    // Initialize all components
    init_relays();
    init_buzzer();
    init_oled();
    init_audio();
    init_wifi();
    init_webserver();
    init_urdu_voice();
    init_gesture();
    
    ESP_LOGI(TAG, "✅ Jarvis Smart Home ready!");
    ESP_LOGI(TAG, "📢 Urdu voice commands active");
    ESP_LOGI(TAG, "🖐️ Gesture control active");
    ESP_LOGI(TAG, "🌐 Web server running on port 80");
    
    while (1) {
        // Process audio and gesture commands
        process_audio_commands();
        process_gesture_commands();
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}