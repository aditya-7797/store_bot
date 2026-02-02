import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def speech_to_text(audio_path: str) -> str:
    """
    Converts speech to text using Groq Whisper
    """
    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3"
        )

    return transcription.text
