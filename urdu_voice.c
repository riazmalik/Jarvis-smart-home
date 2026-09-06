#include "urdu_voice.h"
#include "relay_control.h"
#include "esp_log.h"
#include <string.h>
#include <ctype.h>

static const char *TAG = "URDU_VOICE";

// ===== Action Functions =====
static void action_all_on(void) {
    turn_all_on();
    ESP_LOGI(TAG, "📢 Command: سب لائٹ آن کرو → All ON");
}

static void action_all_off(void) {
    turn_all_off();
    ESP_LOGI(TAG, "📢 Command: سب لائٹ بند کرو → All OFF");
}

static void action_living_on(void) {
    turn_on_bulb(0);
    ESP_LOGI(TAG, "📢 Command: لونگ روم لائٹ آن کرو → Living ON");
}

static void action_living_off(void) {
    turn_off_bulb(0);
    ESP_LOGI(TAG, "📢 Command: لونگ روم لائٹ بند کرو → Living OFF");
}

static void action_bedroom_on(void) {
    turn_on_bulb(1);
    ESP_LOGI(TAG, "📢 Command: بیڈ روم لائٹ آن کرو → Bedroom ON");
}

static void action_bedroom_off(void) {
    turn_off_bulb(1);
    ESP_LOGI(TAG, "📢 Command: بیڈ روم لائٹ بند کرو → Bedroom OFF");
}

static void action_kitchen_on(void) {
    turn_on_bulb(2);
    ESP_LOGI(TAG, "📢 Command: کچن لائٹ آن کرو → Kitchen ON");
}

static void action_kitchen_off(void) {
    turn_off_bulb(2);
    ESP_LOGI(TAG, "📢 Command: کچن لائٹ بند کرو → Kitchen OFF");
}

static void action_study_on(void) {
    turn_on_bulb(3);
    ESP_LOGI(TAG, "📢 Command: سٹڈی روم لائٹ آن کرو → Study ON");
}

static void action_study_off(void) {
    turn_off_bulb(3);
    ESP_LOGI(TAG, "📢 Command: سٹڈی روم لائٹ بند کرو → Study OFF");
}

// ===== Urdu Command Dictionary =====
static urdu_command_t urdu_commands[] = {
    // All commands
    {"سب لائٹ آن کرو", "sab light on karo", action_all_on, "تمام لائٹس آن کر دیں"},
    {"سب لائٹ بند کرو", "sab light band karo", action_all_off, "تمام لائٹس بند کر دیں"},
    {"روشنی کرو", "roshni karo", action_all_on, "روشنی کر دی"},
    {"اندھیرا کرو", "andhera karo", action_all_off, "اندھیرا کر دیا"},
    
    // Living Room
    {"لونگ روم لائٹ آن کرو", "living room light on karo", action_living_on, "لونگ روم کی لائٹ آن کی"},
    {"لونگ روم لائٹ بند کرو", "living room light band karo", action_living_off, "لونگ روم کی لائٹ بند کی"},
    {"بیٹھک کی لائٹ جلاو", "baithak ki light jalao", action_living_on, "بیٹھک کی لائٹ جلا دی"},
    {"بیٹھک کی لائٹ بجھاو", "baithak ki light bujhao", action_living_off, "بیٹھک کی لائٹ بجھا دی"},
    
    // Bedroom
    {"بیڈ روم لائٹ آن کرو", "bed room light on karo", action_bedroom_on, "بیڈ روم کی لائٹ آن کی"},
    {"بیڈ روم لائٹ بند کرو", "bed room light band karo", action_bedroom_off, "بیڈ روم کی لائٹ بند کی"},
    {"سونے کی لائٹ جلاو", "sone ki light jalao", action_bedroom_on, "سونے کی لائٹ جلا دی"},
    {"سونے کی لائٹ بجھاو", "sone ki light bujhao", action_bedroom_off, "سونے کی لائٹ بجھا دی"},
    
    // Kitchen
    {"کچن لائٹ آن کرو", "kitchen light on karo", action_kitchen_on, "کچن کی لائٹ آن کی"},
    {"کچن لائٹ بند کرو", "kitchen light band karo", action_kitchen_off, "کچن کی لائٹ بند کی"},
    {"باورچی خانے کی لائٹ جلاو", "baorchi khanay ki light jalao", action_kitchen_on, "باورچی خانے کی لائٹ جلا دی"},
    {"باورچی خانے کی لائٹ بجھاو", "baorchi khanay ki light bujhao", action_kitchen_off, "باورچی خانے کی لائٹ بجھا دی"},
    
    // Study Room
    {"سٹڈی روم لائٹ آن کرو", "study room light on karo", action_study_on, "سٹڈی روم کی لائٹ آن کی"},
    {"سٹڈی روم لائٹ بند کرو", "study room light band karo", action_study_off, "سٹڈی روم کی لائٹ بند کی"},
    {"مطالعہ کی لائٹ جلاو", "mutala ki light jalao", action_study_on, "مطالعہ کی لائٹ جلا دی"},
    {"مطالعہ کی لائٹ بجھاو", "mutala ki light bujhao", action_study_off, "مطالعہ کی لائٹ بجھا دی"},
    
    {NULL, NULL, NULL, NULL}  // End marker
};

bool match_urdu_command(const char *text, urdu_command_t *cmd) {
    if (!text || !cmd || !cmd->command_urdu) return false;
    return strstr(text, cmd->command_urdu) != NULL;
}

void process_urdu_command(const char *text) {
    if (!text) return;
    
    ESP_LOGI(TAG, "📢 Processing: %s", text);
    
    for (int i = 0; urdu_commands[i].command_urdu != NULL; i++) {
        if (match_urdu_command(text, &urdu_commands[i])) {
            ESP_LOGI(TAG, "✅ Command matched: %s", urdu_commands[i].command_urdu);
            ESP_LOGI(TAG, "💬 Response: %s", urdu_commands[i].response_urdu);
            
            if (urdu_commands[i].action) {
                urdu_commands[i].action();
            }
            return;
        }
    }
    
    ESP_LOGW(TAG, "❌ No command matched: %s", text);
}

void init_urdu_voice(void) {
    int count = 0;
    while (urdu_commands[count].command_urdu != NULL) count++;
    ESP_LOGI(TAG, "🕌 Urdu Voice System Initialized with %d commands", count);
}