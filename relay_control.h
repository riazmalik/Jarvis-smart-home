#ifndef RELAY_CONTROL_H
#define RELAY_CONTROL_H

#include <stdbool.h>
#include "driver/gpio.h"

// GPIO Pin Definitions
#define RELAY1_PIN    GPIO_NUM_8   // Living Room
#define RELAY2_PIN    GPIO_NUM_9   // Bedroom
#define RELAY3_PIN    GPIO_NUM_10  // Kitchen
#define RELAY4_PIN    GPIO_NUM_11  // Study Room
#define BUZZER_PIN    GPIO_NUM_18  // Buzzer

// Function prototypes
void init_relays(void);
void init_buzzer(void);
void toggle_bulb(int index);
void turn_on_bulb(int index);
void turn_off_bulb(int index);
void turn_all_on(void);
void turn_all_off(void);
void play_beep(int frequency, int duration_ms);
bool get_bulb_state(int index);
void play_feedback_sound(void);

#endif // RELAY_CONTROL_H