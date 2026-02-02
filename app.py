import streamlit as st
import tempfile
import sounddevice as sd
import soundfile as sf

from tools.voice_tools import speech_to_text
from graph.workflow import graph

st.set_page_config(page_title="Inventory Assistant", layout="centered")
st.title("📦 Inventory Assistant")
st.caption("Push-to-Talk")

# ---------- SESSION ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "recording" not in st.session_state:
    st.session_state.recording = False

# ---------- CHAT HISTORY ----------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

st.divider()
st.subheader("🎙 Push to Talk")

# ---------- AUDIO RECORD ----------
DURATION = 5  # seconds
SAMPLE_RATE = 16000

if st.button("🎤 Hold & Speak (5s)"):
    st.info("Recording... Speak now")    

    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32"
    )
    sd.wait()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, audio, SAMPLE_RATE)
        audio_path = tmp.name

    # Speech to text
    text = speech_to_text(audio_path)
    st.success(f"Recognized: {text}")

    # User message
    st.session_state.messages.append({"role": "user", "content": text})
    with st.chat_message("user"):
        st.markdown(text)

    # Graph response
    final_state = graph.invoke({"query": text})
    bot_reply = final_state.get("response", "Something went wrong.")

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.markdown(bot_reply)

# ---------- TEXT INPUT ----------
st.divider()
st.subheader("💬 Text Input")

user_input = st.chat_input("Ask something about inventory...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    final_state = graph.invoke({"query": user_input})
    bot_reply = final_state.get("response", "Something went wrong.")

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
