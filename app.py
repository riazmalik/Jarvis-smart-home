from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import requests
import uuid
from gtts import gTTS
import subprocess

app = Flask(__name__)
CORS(app)

# ===== Configuration =====
ESP32_IP = "192.168.1.100"  # ⚠️ CHANGE THIS to your ESP32 IP
AUDIO_FOLDER = "audio_files"
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# ===== Urdu Command Dictionary =====
URDU_COMMANDS = {
    "سب لائٹ آن کرو": "all_on",
    "سب لائٹ بند کرو": "all_off",
    "لونگ روم لائٹ آن کرو": "living_on",
    "لونگ روم لائٹ بند کرو": "living_off",
    "بیڈ روم لائٹ آن کرو": "bedroom_on",
    "بیڈ روم لائٹ بند کرو": "bedroom_off",
    "کچن لائٹ آن کرو": "kitchen_on",
    "کچن لائٹ بند کرو": "kitchen_off",
    "سٹڈی روم لائٹ آن کرو": "study_on",
    "سٹڈی روم لائٹ بند کرو": "study_off",
    "روشنی کرو": "all_on",
    "اندھیرا کرو": "all_off",
}

def send_to_esp32(command):
    """Send command to ESP32 via HTTP"""
    try:
        action_map = {
            "all_on": "/api/bulb?all=on",
            "all_off": "/api/bulb?all=off",
            "living_on": "/api/bulb?index=0&state=on",
            "living_off": "/api/bulb?index=0&state=off",
            "bedroom_on": "/api/bulb?index=1&state=on",
            "bedroom_off": "/api/bulb?index=1&state=off",
            "kitchen_on": "/api/bulb?index=2&state=on",
            "kitchen_off": "/api/bulb?index=2&state=off",
            "study_on": "/api/bulb?index=3&state=on",
            "study_off": "/api/bulb?index=3&state=off",
        }
        url = f"http://{ESP32_IP}{action_map.get(command, '')}"
        response = requests.get(url, timeout=2)
        return response.status_code == 200
    except Exception as e:
        print(f"ESP32 error: {e}")
        return False

@app.route('/voice', methods=['POST'])
def process_voice():
    """Receive voice command from ESP32 or web"""
    data = request.json
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    # Match command
    action = None
    for cmd, act in URDU_COMMANDS.items():
        if cmd in text:
            action = act
            break
    
    if not action:
        return jsonify({"error": "Command not recognized", "text": text}), 400
    
    # Send to ESP32
    success = send_to_esp32(action)
    
    # Generate response in Urdu
    responses = {
        "all_on": "تمام لائٹس آن کر دیں",
        "all_off": "تمام لائٹس بند کر دیں",
        "living_on": "لونگ روم کی لائٹ آن کی",
        "living_off": "لونگ روم کی لائٹ بند کی",
        "bedroom_on": "بیڈ روم کی لائٹ آن کی",
        "bedroom_off": "بیڈ روم کی لائٹ بند کی",
        "kitchen_on": "کچن کی لائٹ آن کی",
        "kitchen_off": "کچن کی لائٹ بند کی",
        "study_on": "سٹڈی روم کی لائٹ آن کی",
        "study_off": "سٹڈی روم کی لائٹ بند کی",
    }
    
    response_text = responses.get(action, "کمانڈ موصول ہو گئی")
    
    return jsonify({
        "success": success,
        "text": text,
        "action": action,
        "response": response_text
    })

@app.route('/gesture', methods=['POST'])
def handle_gesture():
    """Receive gesture command"""
    data = request.json
    gesture = data.get('gesture', '')
    
    gesture_map = {
        "open": "all_on",
        "closed": "all_off"
    }
    
    action = gesture_map.get(gesture)
    if not action:
        return jsonify({"error": "Unknown gesture"}), 400
    
    success = send_to_esp32(action)
    return jsonify({"success": success, "action": action})

@app.route('/status', methods=['GET'])
def get_status():
    """Get bulb status from ESP32"""
    try:
        response = requests.get(f"http://{ESP32_IP}/api/status", timeout=2)
        return jsonify(response.json())
    except:
        return jsonify({"error": "ESP32 not reachable"}), 500

if __name__ == '__main__':
    # Get ESP32 IP from user
    esp_ip = input("Enter ESP32 IP address (e.g., 192.168.1.100): ").strip()
    if esp_ip:
        ESP32_IP = esp_ip
    print(f"🚀 Flask server starting... ESP32 IP: {ESP32_IP}")
    app.run(host='0.0.0.0', port=5000, debug=True)