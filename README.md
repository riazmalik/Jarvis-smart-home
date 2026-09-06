# 🔌 Jarvis Smart Home - Complete System

A fully functional smart home system with Urdu voice commands, hand gesture control, and web interface.

## 🚀 Quick Start

```bash
# 1. Build ESP32 firmware
cd esp32_firmware
idf.py build
idf.py -p COM3 flash

# 2. Start Flask server
cd ../flask_server
python app.py

# 3. Start gesture control (in new terminal)
python gesture_control.py

# 4. Open web interface
# http://[ESP32_IP]
# Flask Server for Jarvis Smart Home

This server handles:
- Urdu voice command processing
- Gesture detection API
- ESP32 communication

## Installation

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
