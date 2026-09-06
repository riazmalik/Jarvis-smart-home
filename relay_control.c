#include "relay_control.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_rom_sys.h"

static const char *TAG = "RELAY";
static bool bulb_states[4] = {false, false, false, false};

void init_relays(void) {
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << RELAY1_PIN) | (1ULL << RELAY2_PIN) | 
                        (1ULL << RELAY3_PIN) | (1ULL << RELAY4_PIN),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    gpio_config(&io_conf);
    
    // Turn all relays OFF initially (Active LOW)
    gpio_set_level(RELAY1_PIN, 1);
    gpio_set_level(RELAY2_PIN, 1);
    gpio_set_level(RELAY3_PIN, 1);
    gpio_set_level(RELAY4_PIN, 1);
    
    ESP_LOGI(TAG, "✅ Relays initialized (All OFF)");
}

void init_buzzer(void) {
    gpio_config_t io_conf = {
        .pin_bit_mask = (1ULL << BUZZER_PIN),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    gpio_config(&io_conf);
    gpio_set_level(BUZZER_PIN, 0);
    ESP_LOGI(TAG, "✅ Buzzer initialized");
}

void play_beep(int frequency, int duration_ms) {
    int period_us = 1000000 / frequency;
    int half_period_us = period_us / 2;
    int cycles = (duration_ms * 1000) / period_us;
    
    for (int i = 0; i < cycles; i++) {
        gpio_set_level(BUZZER_PIN, 1);
        esp_rom_delay_us(half_period_us);
        gpio_set_level(BUZZER_PIN, 0);
        esp_rom_delay_us(half_period_us);
    }
}

void play_feedback_sound(void) {
    play_beep(1000, 100);
    vTaskDelay(pdMS_TO_TICKS(50));
    play_beep(1200, 100);
}

void toggle_bulb(int index) {
    if (index < 0 || index > 3) return;
    
    gpio_num_t pins[] = {RELAY1_PIN, RELAY2_PIN, RELAY3_PIN, RELAY4_PIN};
    const char *names[] = {"Living", "Bedroom", "Kitchen", "Study"};
    
    bulb_states[index] = !bulb_states[index];
    gpio_set_level(pins[index], bulb_states[index] ? 0 : 1);
    
    ESP_LOGI(TAG, "💡 %s: %s", names[index], bulb_states[index] ? "ON" : "OFF");
    play_feedback_sound();
}

void turn_on_bulb(int index) {
    if (index < 0 || index > 3) return;
    if (!bulb_states[index]) {
        toggle_bulb(index);
    }
}

void turn_off_bulb(int index) {
    if (index < 0 || index > 3) return;
    if (bulb_states[index]) {
        toggle_bulb(index);
    }
}

void turn_all_on(void) {
    for (int i = 0; i < 4; i++) {
        if (!bulb_states[i]) {
            gpio_set_level(RELAY1_PIN + i, 0);
            bulb_states[i] = true;
        }
    }
    ESP_LOGI(TAG, "💡 All bulbs ON");
    play_beep(1500, 150);
}

void turn_all_off(void) {
    for (int i = 0; i < 4; i++) {
        if (bulb_states[i]) {
            gpio_set_level(RELAY1_PIN + i, 1);
            bulb_states[i] = false;
        }
    }
    ESP_LOGI(TAG, "💡 All bulbs OFF");
    play_beep(800, 150);
}

bool get_bulb_state(int index) {
    if (index < 0 || index > 3) return false;
    return bulb_states[index];
}