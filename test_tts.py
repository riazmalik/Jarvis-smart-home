import asyncio
import edge_tts

async def main():
    # Urdu male voice — natural, high quality
    c = edge_tts.Communicate("تمام لائٹس آن کر دی گئیں، سر۔", voice="ur-PK-AsadNeural")
    await c.save("test_urdu.mp3")
    print("✅ Urdu saved -> test_urdu.mp3")

    # English UK male — Jarvis-style
    c = edge_tts.Communicate("All lights turned on, Sir.", voice="en-GB-RyanNeural")
    await c.save("test_english.mp3")
    print("✅ English saved -> test_english.mp3")

asyncio.run(main())