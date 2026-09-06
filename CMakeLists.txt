idf_component_register(SRCS 
    "main.c" 
    "relay_control.c" 
    "urdu_voice.c" 
    "webserver.c" 
    "gesture.c"
    "audio_handler.c"
    "oled_handler.c"
    INCLUDE_DIRS "."
)

target_compile_definitions(${COMPONENT_LIB} PRIVATE 
    -DRELAY1_PIN=8
    -DRELAY2_PIN=9
    -DRELAY3_PIN=10
    -DRELAY4_PIN=11
)