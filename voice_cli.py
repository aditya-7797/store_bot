import sounddevice as sd
import soundfile as sf
from tools.voice_tools import speech_to_text
from graph.workflow import graph

FS = 16000
DURATION = 5  # seconds

def record_voice():
    print("\n🎙 Press ENTER and speak...")
    input()
    print("Recording...")

    audio = sd.rec(int(DURATION * FS), samplerate=FS, channels=1)
    sd.wait()

    sf.write("voice.wav", audio, FS)
    print("🛑 Recording saved as voice.wav")

def main():
    record_voice()

    text = speech_to_text("voice.wav")
    print("\n🗣 You said:", text)

    result = graph.invoke({"query": text})
    print("\n🤖 Bot:", result["response"])

if __name__ == "__main__":
    main()
