#include "audio_handler.h"
#include "esp_log.h"

static const char *TAG = "AUDIO";

void init_audio(void) {
    ESP_LOGI(TAG, "🔊 Audio system initialized");
    // Future: Initialize I2S for INMP441 and MAX98357
}

void process_audio_commands(void) {
    // Future: Read from microphone and process voice commands
}