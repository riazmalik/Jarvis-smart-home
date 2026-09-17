import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Use the new Interactions API with the latest model
interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input="Say 'Jarvis online' in Urdu and English. One line each.",
)

print(interaction.output_text)