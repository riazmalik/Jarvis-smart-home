# 🔌 Wiring Diagram - Jarvis Smart Home

## Pin Mapping

| Component | Pin | ESP32 Pin | Wire Color |
|-----------|-----|-----------|------------|
| INMP441 | VDD | 3.3V | 🔴 Red |
| | GND | GND | ⚫ Black |
| | SD | GPIO 3 | 🟡 Yellow |
| | WS | GPIO 7 | 🟢 Green |
| | SCK | GPIO 17 | 🔵 Blue |
| | L/R | GND | ⚫ Black |
| MAX98357 | VIN | 5V | 🔴 Red |
| | GND | GND | ⚫ Black |
| | DIN | GPIO 6 | 🟡 Yellow |
| | LRC | GPIO 4 | 🟢 Green |
| | BCLK | GPIO 5 | 🔵 Blue |
| | GAIN | GND | ⚫ Black |
| | SD | 3.3V | 🔴 Red |
| Speaker | + | MAX98357 OUT+ | ⚪ White |
| | - | MAX98357 OUT- | ⚫ Black |
| OLED | VCC | 3.3V | 🔴 Red |
| | GND | GND | ⚫ Black |
| | SDA | GPIO 21 | 🟣 Purple |
| | SCL | GPIO 22 | 🟤 Brown |
| Buzzer | + | GPIO 18 | 🟠 Orange |
| | - | GND | ⚫ Black |
| Relay | VCC | 5V | 🔴 Red |
| | GND | GND | ⚫ Black |
| | IN1 | GPIO 8 | 🟡 Yellow |
| | IN2 | GPIO 9 | 🟢 Green |
| | IN3 | GPIO 10 | 🔵 Blue |
| | IN4 | GPIO 11 | 🟣 Purple |

## Power Rails

| Rail | Source | Devices |
|------|--------|---------|
| Left RED | ESP32 5V | INMP441, OLED (via 3.3V), MAX98357, Buzzer |
| Left BLUE | ESP32 GND | All components GND |
| Right RED | Power Supply 5V | Relay Module |
| Right BLUE | Power Supply GND | Relay Module GND |