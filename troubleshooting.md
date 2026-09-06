# 🔧 Troubleshooting Guide

## Common Issues

### ESP32 Not Connecting to WiFi
- Check SSID and password in `webserver.c`
- Ensure router is within range
- Check if WiFi is 2.4GHz (ESP32 doesn't support 5GHz)

### No Audio from Microphone
- INMP441 VDD connected to **3.3V** (NOT 5V!)
- Check GPIO connections: SD→GPIO3, WS→GPIO7, SCK→GPIO17
- Verify L/R pin connected to GND

### Speaker No Sound
- MAX98357 VIN connected to **5V**
- Speaker connected to OUT+ and OUT- (NOT GND!)
- Check GPIO connections: DIN→GPIO6, LRC→GPIO4, BCLK→GPIO5

### Relays Not Clicking
- Relay VCC connected to **5V** (External power supply)
- Active LOW: Set pin to LOW to turn ON
- Check IN1-IN4 connections: GPIO 8,9,10,11

### OLED Not Displaying
- I2C connections: SDA→GPIO21, SCL→GPIO22
- Try both I2C addresses: 0x3C and 0x3D
- Check VCC to 3.3V

### Flask Server "ESP32 Not Reachable"
- Check ESP32_IP in `app.py`
- Ensure ESP32 is connected to same network
- Try pinging the IP address

### Gesture Not Detected
- Good lighting conditions
- Clear background (not too cluttered)
- Hand should be within frame
- Try adjusting min_detection_confidence (0.5-0.9)