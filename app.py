"""
Jarvis Smart Home - AI Voice Assistant Server
Gemini + tool calling + edge-tts + webcam gestures + chat fallback
"""
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from google import genai
from google.genai import types
from dotenv import load_dotenv
import requests
import os
import re
import io
import unicodedata
import datetime
import threading
import json
import asyncio
import edge_tts

# =============================================================
#  Config
# =============================================================
load_dotenv()

ESP32_IP       = os.getenv("ESP32_IP", "192.168.137.58")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = "gemini-2.0-flash-lite"
ESP32_TIMEOUT  = 3

DEFAULT_VOICE_EN = "en-GB-RyanNeural"
DEFAULT_VOICE_UR = "ur-PK-AsadNeural"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
CORS(app)

if not GEMINI_API_KEY:
    print("⚠️  GEMINI_API_KEY missing in .env — AI features disabled")
    client = None
else:
    client = genai.Client(api_key=GEMINI_API_KEY)


# =============================================================
#  ESP32 device control
# =============================================================
ACTION_URLS = {
    "all_on":      "/api/bulb?all=on",
    "all_off":     "/api/bulb?all=off",
    "living_on":   "/api/bulb?index=0&state=on",
    "living_off":  "/api/bulb?index=0&state=off",
    "bedroom_on":  "/api/bulb?index=1&state=on",
    "bedroom_off": "/api/bulb?index=1&state=off",
    "kitchen_on":  "/api/bulb?index=2&state=on",
    "kitchen_off": "/api/bulb?index=2&state=off",
    "study_on":    "/api/bulb?index=3&state=on",
    "study_off":   "/api/bulb?index=3&state=off",
}

ROOM_MAP = {
    "all": "all", "every": "all", "everything": "all", "house": "all", "home": "all",
    "سب": "all", "تمام": "all", "سارے": "all", "گھر": "all",
    "living": "living", "lounge": "living",
    "لونگ": "living", "بیٹھک": "living",
    "bedroom": "bedroom", "bed": "bedroom",
    "بیڈ": "bedroom", "بیڈروم": "bedroom", "سونے": "bedroom",
    "kitchen": "kitchen",
    "کچن": "kitchen", "باورچی": "kitchen",
    "study": "study", "office": "study",
    "سٹڈی": "study", "مطالعہ": "study", "دفتر": "study",
}

URDU_RESPONSES = {
    "all_on":      "تمام لائٹس آن کر دی گئیں، سر۔",
    "all_off":     "تمام لائٹس بند کر دی گئیں، سر۔",
    "living_on":   "لونگ روم کی لائٹ آن کر دی گئی، سر۔",
    "living_off":  "لونگ روم کی لائٹ بند کر دی گئی، سر۔",
    "bedroom_on":  "بیڈ روم کی لائٹ آن کر دی گئی، سر۔",
    "bedroom_off": "بیڈ روم کی لائٹ بند کر دی گئی، سر۔",
    "kitchen_on":  "کچن کی لائٹ آن کر دی گئی، سر۔",
    "kitchen_off": "کچن کی لائٹ بند کر دی گئی، سر۔",
    "study_on":    "سٹڈی روم کی لائٹ آن کر دی گئی، سر۔",
    "study_off":   "سٹڈی روم کی لائٹ بند کر دی گئی، سر۔",
}

# Simple conversational replies (used when Gemini is unavailable)
CHAT_RESPONSES = {
    # English
    "hello":              ("en", "Hello, Sir. How may I help you?"),
    "hi":                 ("en", "Hello, Sir. At your service."),
    "hey":                ("en", "Yes, Sir?"),
    "good morning":       ("en", "Good morning, Sir."),
    "good evening":       ("en", "Good evening, Sir."),
    "good night":         ("en", "Good night, Sir. Rest well."),
    "how are you":        ("en", "Functioning optimally, Sir. Thank you for asking."),
    "how r you":          ("en", "Functioning optimally, Sir."),
    "who are you":        ("en", "I'm JARVIS, your smart-home assistant, Sir."),
    "what is your name":  ("en", "JARVIS, Sir. Just call my name."),
    "thank you":          ("en", "Always a pleasure, Sir."),
    "thanks":             ("en", "My pleasure, Sir."),
    "bye":                ("en", "Goodbye, Sir."),
    "goodbye":            ("en", "Goodbye, Sir."),
    # Urdu
    "ہیلو":               ("ur", "ہیلو سر، میں حاضر ہوں۔"),
    "السلام علیکم":        ("ur", "وعلیکم السلام، سر۔"),
    "شکریہ":              ("ur", "خوشی ہوئی، سر۔"),
    "آپ کیسے ہیں":         ("ur", "میں بالکل ٹھیک ہوں، سر۔"),
    "خدا حافظ":            ("ur", "خدا حافظ، سر۔"),
    "آپ کا نام کیا ہے":    ("ur", "جاریس، سر۔"),
}


def normalize_urdu(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    replacements = {
        "ي": "ی", "ك": "ک", "ة": "ہ", "ۀ": "ہ", "ؤ": "و",
        "إ": "ا", "أ": "ا", "آ": "ا",
        "\u200c": " ", "\u200d": " ", "\u00a0": " ",
        "\u200f": "", "\u200e": "",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return re.sub(r"\s+", " ", text).strip()


def normalize_room(room: str) -> str:
    if not room:
        return "all"
    r = normalize_urdu(room.lower().strip())
    for key, val in ROOM_MAP.items():
        if key in r:
            return val
    return "all"


def send_to_esp32(action: str) -> bool:
    path = ACTION_URLS.get(action)
    if not path:
        return False
    url = f"http://{ESP32_IP}{path}"
    try:
        r = requests.get(url, timeout=ESP32_TIMEOUT)
        return r.status_code == 200
    except requests.RequestException as e:
        print(f"❌ ESP32 error: {e}")
        return False


# =============================================================
#  TOOLS the AI can call
# =============================================================
def turn_on_light(room: str) -> str:
    """Turn ON a light in a specific room.

    Args:
        room: One of 'all', 'living', 'bedroom', 'kitchen', 'study'.
    """
    r = normalize_room(room)
    ok = send_to_esp32(f"{r}_on")
    print(f"   🔧 turn_on_light({r}) -> {ok}")
    return f"Turned ON the {r} light. ESP32 responded: {ok}"


def turn_off_light(room: str) -> str:
    """Turn OFF a light in a specific room.

    Args:
        room: One of 'all', 'living', 'bedroom', 'kitchen', 'study'.
    """
    r = normalize_room(room)
    ok = send_to_esp32(f"{r}_off")
    print(f"   🔧 turn_off_light({r}) -> {ok}")
    return f"Turned OFF the {r} light. ESP32 responded: {ok}"


def get_light_status() -> str:
    """Get the current state of all lights from the ESP32."""
    try:
        r = requests.get(f"http://{ESP32_IP}/api/status", timeout=ESP32_TIMEOUT)
        return json.dumps(r.json())
    except requests.RequestException as e:
        return f"Error reaching ESP32: {e}"


def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.datetime.now().strftime("%A, %d %B %Y, %I:%M %p")


TIMERS = {}


def set_timer(seconds: int, task: str) -> str:
    """Set a timer that performs a task after a delay.

    Args:
        seconds: Delay in seconds.
        task: Natural description, e.g. 'turn off all lights'.
    """
    def fire():
        t_lower = task.lower()
        if "off" in t_lower or "بند" in task or "band" in t_lower:
            if "all" in t_lower or "سب" in task:
                send_to_esp32("all_off")
            else:
                send_to_esp32(f"{normalize_room(task)}_off")
        else:
            if "all" in t_lower or "سب" in task:
                send_to_esp32("all_on")
            else:
                send_to_esp32(f"{normalize_room(task)}_on")

    t = threading.Timer(seconds, fire)
    t.daemon = True
    t.start()
    TIMERS[id(t)] = t
    print(f"   ⏰ Timer set: {seconds}s -> {task}")
    return f"Timer set for {seconds} seconds to: {task}"


TOOLS = [turn_on_light, turn_off_light, get_light_status, get_current_time, set_timer]


# =============================================================
#  Jarvis personality
# =============================================================
SYSTEM_PROMPT = """You are JARVIS, a polite, witty, efficient AI smart-home assistant.

PERSONALITY:
- Address the user as "Sir" (or "جناب" in Urdu).
- Reply in 1-2 short sentences. Never lecture.
- Speak the SAME language the user used:
    * Urdu (اردو) -> reply in Urdu
    * English -> reply in English
    * Mixed -> same mix
- Light dry British-butler humour is welcome.
- Never mention being an AI language model. You ARE JARVIS.

CAPABILITIES:
- Control lights with turn_on_light / turn_off_light.
- Report status with get_light_status.
- Tell time with get_current_time.
- Set timers with set_timer.

RULES:
- For light commands, ALWAYS call the appropriate tool.
- If room unspecified, default to 'all'.
- For plain chat, don't call tools.
- After a tool call, confirm briefly in the user's language.
"""

CHAT_HISTORIES = {}
SESSION_MAX_TURNS = 10


def get_history(session_id: str):
    if session_id not in CHAT_HISTORIES:
        CHAT_HISTORIES[session_id] = []
    return CHAT_HISTORIES[session_id]


def reset_chat(session_id: str):
    CHAT_HISTORIES.pop(session_id, None)


def ask_gemini(session_id: str, user_message: str) -> str:
    history = get_history(session_id)

    contents = []
    contents.append(types.Content(
        role="user",
        parts=[types.Part(text=SYSTEM_PROMPT + "\n\n(End of instructions. Begin.)")]
    ))
    contents.append(types.Content(
        role="model",
        parts=[types.Part(text="Understood, Sir. Jarvis at your service.")]
    ))
    for role, text in history:
        contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(tools=TOOLS, temperature=0.7),
    )

    reply = (response.text or "").strip()

    history.append(("user", user_message))
    if reply:
        history.append(("model", reply))
    if len(history) > SESSION_MAX_TURNS * 2:
        del history[:-SESSION_MAX_TURNS * 2]

    return reply


# =============================================================
#  Legacy keyword fallback (works WITHOUT Gemini)
# =============================================================
LEGACY_COMMANDS = {
    normalize_urdu(k): v for k, v in {
        # --- Urdu ---
        "سب لائٹ آن کرو": "all_on", "سب لائٹ بند کرو": "all_off",
        "سب لائٹس آن کرو": "all_on", "سب لائٹس بند کرو": "all_off",
        "روشنی کرو": "all_on", "اندھیرا کرو": "all_off",
        "لائٹ آن کرو": "all_on", "لائٹ بند کرو": "all_off",
        "لونگ روم لائٹ آن کرو": "living_on", "لونگ روم لائٹ بند کرو": "living_off",
        "بیٹھک کی لائٹ جلاو": "living_on", "بیٹھک کی لائٹ بجھاو": "living_off",
        "بیڈ روم لائٹ آن کرو": "bedroom_on", "بیڈ روم لائٹ بند کرو": "bedroom_off",
        "کچن لائٹ آن کرو": "kitchen_on", "کچن لائٹ بند کرو": "kitchen_off",
        "سٹڈی روم لائٹ آن کرو": "study_on", "سٹڈی روم لائٹ بند کرو": "study_off",

        # --- English: ALL ---
        "turn on all lights": "all_on", "turn off all lights": "all_off",
        "all lights on": "all_on", "all lights off": "all_off",
        "turn on everything": "all_on", "turn off everything": "all_off",
        "lights on": "all_on", "lights off": "all_off",
        "switch on all lights": "all_on", "switch off all lights": "all_off",
        "turn on the lights": "all_on", "turn off the lights": "all_off",

        # --- English: Living Room ---
        "turn on living room": "living_on", "turn off living room": "living_off",
        "turn on the living room": "living_on", "turn off the living room": "living_off",
        "living room on": "living_on", "living room off": "living_off",
        "turn on living room light": "living_on", "turn off living room light": "living_off",
        "turn on living room lights": "living_on", "turn off living room lights": "living_off",

        # --- English: Bedroom ---
        "turn on bedroom": "bedroom_on", "turn off bedroom": "bedroom_off",
        "turn on the bedroom": "bedroom_on", "turn off the bedroom": "bedroom_off",
        "bedroom on": "bedroom_on", "bedroom off": "bedroom_off",
        "turn on bedroom light": "bedroom_on", "turn off bedroom light": "bedroom_off",
        "turn on bedroom lights": "bedroom_on", "turn off bedroom lights": "bedroom_off",

        # --- English: Kitchen ---
        "turn on kitchen": "kitchen_on", "turn off kitchen": "kitchen_off",
        "turn on the kitchen": "kitchen_on", "turn off the kitchen": "kitchen_off",
        "kitchen on": "kitchen_on", "kitchen off": "kitchen_off",
        "kitchen light on": "kitchen_on", "kitchen light off": "kitchen_off",
        "turn on kitchen light": "kitchen_on", "turn off kitchen light": "kitchen_off",
        "turn on kitchen lights": "kitchen_on", "turn off kitchen lights": "kitchen_off",

        # --- English: Study ---
        "turn on study": "study_on", "turn off study": "study_off",
        "turn on the study": "study_on", "turn off the study": "study_off",
        "study on": "study_on", "study off": "study_off",
        "study room on": "study_on", "study room off": "study_off",
        "turn on study light": "study_on", "turn off study light": "study_off",
        "turn on study room": "study_on", "turn off study room": "study_off",
        "turn on study room light": "study_on", "turn off study room light": "study_off",
    }.items()
}


def legacy_match(text: str):
    n = normalize_urdu(text.lower())
    for cmd in sorted(LEGACY_COMMANDS.keys(), key=len, reverse=True):
        if cmd in n:
            return LEGACY_COMMANDS[cmd]
    return None


def match_chat_reply(text: str):
    """Match a short conversational phrase; returns (lang, reply) or (None, None)."""
    n = normalize_urdu(text.lower().strip())
    for phrase in sorted(CHAT_RESPONSES.keys(), key=len, reverse=True):
        if normalize_urdu(phrase) in n:
            return CHAT_RESPONSES[phrase]
    return None, None


# =============================================================
#  Gesture → action mapping
# =============================================================
GESTURE_ACTIONS = {
    "open":    "all_on",
    "closed":  "all_off",
    "one":     "living_on",
    "two":     "bedroom_on",
    "three":   "kitchen_on",
    "thumb":   "study_on",
}


# =============================================================
#  Edge-TTS helpers
# =============================================================
def is_urdu(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text))


async def _tts_to_bytes(text: str, voice: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice=voice)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()


# =============================================================
#  Routes
# =============================================================
@app.route("/", methods=["GET"])
def index():
    return send_from_directory(BASE_DIR, "dashboard.html")


@app.route("/favicon.ico", methods=["GET"])
def favicon():
    return "", 204


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "esp32_ip": ESP32_IP,
        "gemini_model": GEMINI_MODEL,
        "ai_enabled": client is not None,
    })


@app.route("/speak", methods=["POST"])
def speak():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    voice = (data.get("voice") or "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400
    if not voice:
        voice = DEFAULT_VOICE_UR if is_urdu(text) else DEFAULT_VOICE_EN
    try:
        mp3_bytes = asyncio.run(_tts_to_bytes(text, voice))
        return Response(mp3_bytes, mimetype="audio/mpeg",
                        headers={"Cache-Control": "no-store"})
    except Exception as e:
        print(f"❌ TTS error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/voices", methods=["GET"])
def list_voices():
    return jsonify({
        "ur": [
            {"id": "ur-PK-AsadNeural", "name": "Urdu · Asad (Male)"},
            {"id": "ur-PK-UzmaNeural", "name": "Urdu · Uzma (Female)"},
        ],
        "en": [
            {"id": "en-GB-RyanNeural",   "name": "English UK · Ryan (Male · Jarvis)"},
            {"id": "en-GB-ThomasNeural", "name": "English UK · Thomas (Male)"},
            {"id": "en-GB-SoniaNeural",  "name": "English UK · Sonia (Female)"},
            {"id": "en-US-GuyNeural",    "name": "English US · Guy (Male)"},
            {"id": "en-US-AndrewNeural", "name": "English US · Andrew (Male)"},
            {"id": "en-US-AriaNeural",   "name": "English US · Aria (Female)"},
        ],
        "hi": [
            {"id": "hi-IN-MadhurNeural", "name": "Hindi · Madhur (Male)"},
        ],
    })


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    session_id = data.get("session_id") or "default"

    if not message:
        return jsonify({"success": False, "reply": "I didn't hear anything, Sir.", "error": "empty message"}), 400

    print(f"💬 [{session_id}] User: {message}")

    # ---- 1) Try Gemini first ----
    if client is not None:
        try:
            reply = ask_gemini(session_id, message)
            if reply:
                print(f"🤖 Jarvis: {reply}")
                return jsonify({
                    "success": True,
                    "reply": reply,
                    "source": "gemini",
                    "is_urdu": is_urdu(reply),
                })
            else:
                print("⚠️ Gemini returned empty reply")
        except Exception as e:
            err = str(e)
            print(f"⚠️ Gemini error: {err[:120]}")
            if "RESOURCE_EXHAUSTED" in err or "429" in err:
                print("⚠️ Rate limited — falling back to keyword matching")
            # Fall through to fallbacks below

    # ---- 2) Try light-control keyword matcher ----
    action = legacy_match(message)
    if action:
        ok = send_to_esp32(action)
        reply = URDU_RESPONSES.get(action, "کمانڈ موصول ہو گئی، سر۔")
        print(f"🤖 Jarvis (fallback): {reply}")
        return jsonify({
            "success": ok,
            "reply": reply,
            "source": "fallback",
            "action": action,
            "is_urdu": True,
        })

    # ---- 3) Try conversational keyword matcher ----
    lang, chat_reply = match_chat_reply(message)
    if chat_reply:
        print(f"🤖 Jarvis (chat fallback): {chat_reply}")
        return jsonify({
            "success": True,
            "reply": chat_reply,
            "source": "chat_fallback",
            "is_urdu": (lang == "ur"),
        })

    # ---- 4) Nothing matched ----
    reply = "معذرت سر، میں سمجھ نہیں پایا۔" if is_urdu(message) \
            else "Sorry Sir, I didn't quite catch that."
    return jsonify({"success": False, "reply": reply, "source": "none", "is_urdu": is_urdu(reply)})


@app.route("/direct", methods=["POST"])
def direct():
    """Direct light control — bypasses AI entirely."""
    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "").strip().lower()
    if action not in ACTION_URLS:
        return jsonify({"success": False, "error": f"Unknown action: {action}"}), 400
    ok = send_to_esp32(action)
    print(f"   ⚡ direct '{action}' (ESP32 ok={ok})")
    return jsonify({
        "success": ok,
        "action": action,
        "response": URDU_RESPONSES.get(action, ""),
    })


@app.route("/reset", methods=["POST"])
def reset():
    data = request.get_json(silent=True) or {}
    reset_chat(data.get("session_id") or "default")
    return jsonify({"success": True})


@app.route("/voice", methods=["POST"])
def voice():
    return chat()


@app.route("/gesture", methods=["POST"])
def gesture():
    data = request.get_json(silent=True) or {}
    g = (data.get("gesture") or "").strip().lower()
    action = GESTURE_ACTIONS.get(g)
    if not action:
        return jsonify({"success": False, "error": f"Unknown gesture: {g}"}), 400
    ok = send_to_esp32(action)
    print(f"   🖐️  gesture '{g}' -> {action} (ESP32 ok={ok})")
    return jsonify({
        "success": ok,
        "gesture": g,
        "action": action,
        "response": URDU_RESPONSES.get(action, ""),
    })


@app.route("/status", methods=["GET"])
def status():
    try:
        r = requests.get(f"http://{ESP32_IP}/api/status", timeout=ESP32_TIMEOUT)
        return jsonify(r.json()), r.status_code
    except requests.RequestException as e:
        return jsonify({"error": "ESP32 not reachable", "detail": str(e)}), 500


# =============================================================
#  Entry point
# =============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀  JARVIS Smart Home — AI Server")
    print("=" * 60)
    print(f"📡 ESP32 IP:     {ESP32_IP}")
    print(f"🧠 Gemini model: {GEMINI_MODEL}")
    print(f"🔑 API key:      {'✅ loaded' if GEMINI_API_KEY else '❌ missing'}")
    print(f"🔊 TTS voices:   {DEFAULT_VOICE_EN} / {DEFAULT_VOICE_UR}")
    print(f"🎨 Dashboard:    http://localhost:5000/")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False)