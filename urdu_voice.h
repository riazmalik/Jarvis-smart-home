#ifndef URDU_VOICE_H
#define URDU_VOICE_H

#include <stdbool.h>
#include <stddef.h>

typedef struct {
    char *command_urdu;
    char *command_roman;
    void (*action)(void);
    char *response_urdu;
} urdu_command_t;

void init_urdu_voice(void);
void process_urdu_command(const char *text);
bool match_urdu_command(const char *text, urdu_command_t *cmd);

#endif // URDU_VOICE_H