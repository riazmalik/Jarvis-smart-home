import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def turn_on_light(room: str) -> str:
    """Turn on a light in a specific room.

    Args:
        room: One of 'all', 'living', 'bedroom', 'kitchen', 'study'.
    """
    print(f"   >>> TOOL CALLED: turn_on_light(room='{room}')")
    return f"OK: turned on {room} light"

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Turn on the bedroom light",
    config=types.GenerateContentConfig(
        tools=[turn_on_light],
    ),
)
print("Reply:", response.text)