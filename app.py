# 🎧 YouTube → Audio → Text → Multi-Format + Language + Dialogue Summary Web App
# Run using: streamlit run app.py

import os
import re
import time
import json
import socket
import requests
import yt_dlp
import whisper
from pytube import YouTube
from datetime import datetime
import streamlit as st
from openai import OpenAI

# =============================
# CONFIGURATION
# =============================

OPENAI_API_KEY = " "  # Replace with your valid OpenAI API key
client = OpenAI(api_key=OPENAI_API_KEY)
HISTORY_FILE = "history.json"

# =============================
# HISTORY HANDLING
# =============================

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(entry):
    history = load_history()
    history.insert(0, entry)  # newest first
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)
    return history

# =============================
# AUDIO DOWNLOAD (Robust)
# =============================

def download_audio(video_url, filename="audio.wav"):
    st.info("🎧 Attempting audio download...")
    video_url = video_url.split("?")[0]

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'noplaylist': True,
        'nocheckcertificate': True,
        'retries': 5,
        'socket_timeout': 60,
        'quiet': True,
    }

    for attempt in range(3):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            st.success("✅ Audio downloaded using yt_dlp!")
            break
        except (yt_dlp.utils.DownloadError, socket.timeout) as e:
            st.warning(f"⚠️ yt_dlp timeout (try {attempt+1}/3): {e}")
            time.sleep(3)
        except Exception as e:
            st.warning(f"⚠️ yt_dlp error (try {attempt+1}/3): {e}")
            time.sleep(3)
    else:
        st.error("❌ yt_dlp failed, switching to pytube...")
        try:
            yt = YouTube(video_url)
            stream = yt.streams.filter(only_audio=True).first()
            out_file = stream.download(filename="audio")
            if not out_file.endswith(".wav"):
                os.rename(out_file, filename)
            st.success("✅ Audio downloaded using pytube fallback!")
        except Exception as e:
            st.error(f"❌ pytube also failed: {e}")
            return None

    if os.path.exists("audio.wav"):
        return "audio.wav"
    elif os.path.exists("audio.wav.wav"):
        os.rename("audio.wav.wav", "audio.wav")
        return "audio.wav"
    else:
        st.error("❌ Audio file not found after download.")
        return None

# =============================
# TRANSCRIBE AUDIO (Whisper)
# =============================

def transcribe_audio(audio_file="audio.wav"):
    if not os.path.exists(audio_file):
        st.error("❌ Audio file not found. Please download first.")
        return ""
    st.info("🧠 Loading Whisper model (small)…")
    model = whisper.load_model("small")
    st.info("🎙️ Transcribing audio… please wait…")
    result = model.transcribe(audio_file)
    text = result["text"]

    with open("transcript.txt", "w", encoding="utf-8") as f:
        f.write(text)
    return text

# =============================
# OPENAI SUMMARIZATION + TRANSLATION
# =============================

def summarize_text_openai(text, summary_type="Paragraph", language="English"):
    if not text.strip():
        return "No transcript found."

    if summary_type == "Paragraph":
        prompt = f"Summarize this transcript into one short, clear paragraph in {language}:\n\n{text}"

    elif summary_type == "Bullet Points":
        prompt = f"""
Summarize the following transcript into short, clear **numbered points** in {language}.
Each point should capture one key idea or event on a new line.
Do not repeat similar ideas.
Output format:
1. ...
2. ...
3. ...
Transcript:
{text}
"""

    elif summary_type == "Conversational":
        prompt = f"""
Convert the following text into a natural back-and-forth dialogue between Alex and Beth in {language}.
Each line should be in this format:
Alex: "..."
Beth: "..."
Alternate naturally between them, only including ideas found in the text.

Transcript:
{text}
"""
    else:
        prompt = text

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# =============================
# FORMATTING HELPERS
# =============================

def format_bullet_points(summary):
    lines = [line.strip() for line in summary.split("\n") if line.strip()]
    formatted = []
    for i, line in enumerate(lines):
        if not re.match(r"^\d+\.", line):
            formatted.append(f"{i+1}. {line}")
        else:
            formatted.append(line)
    return "\n".join(formatted)

def format_conversation(summary_text):
    lines = re.split(r'(?<=\.)\s+', summary_text.strip())
    formatted = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if not re.match(r"^(Alex|Beth):", line):
            speaker = "Alex" if len(formatted) % 2 == 0 else "Beth"
            line = f'{speaker}: "{line}"'
        elif '"' not in line:
            parts = line.split(":", 1)
            if len(parts) == 2:
                speaker, text = parts
                line = f'{speaker.strip()}: "{text.strip()}"'
        formatted.append(line)
    return "\n".join(formatted)

# =============================
# STREAMLIT UI
# =============================

st.set_page_config(page_title="🎧 YouTube AI Summarizer + Translation", page_icon="🎙️", layout="wide")
st.title("🎧 YouTube → Audio → Text → AI Summary + Translation 🌐")
st.markdown("Extract, Transcribe, Summarize, Translate and Store History with OpenAI.")

video_url = st.text_input("🔗 Enter YouTube video URL:")
summary_type = st.selectbox("🧾 Choose Summary Format:", ["Paragraph", "Bullet Points", "Conversational"])
language = st.selectbox("🌍 Choose Output Language:", ["English", "Kannada", "Hindi"])

# =============================
# SIDEBAR HISTORY
# =============================

with st.sidebar:
    st.header("🕘 Summary History")
    history = load_history()
    if st.button("🧹 Clear History"):
        open(HISTORY_FILE, "w").write("[]")
        st.success("History cleared!")
    if history:
        for item in history[:5]:  # show latest 5
            st.markdown(f"""
            **🕓 {item['timestamp']}**
            - 🔗 [Video]({item['video_url']})
            - 🌍 {item['language']} | 🧾 {item['summary_type']}
            <details>
            <summary>📜 View Summary</summary>
            <p>{item['summary']}</p>
            </details>
            <hr>
            """, unsafe_allow_html=True)
    else:
        st.info("No summaries yet. Generate one to see history here.")

# =============================
# MAIN APP LOGIC
# =============================

if st.button("1️⃣ Download Audio"):
    with st.spinner("Downloading audio..."):
        audio_path = download_audio(video_url)
        if audio_path:
            st.success("✅ Audio downloaded successfully!")
            st.audio(audio_path)
        else:
            st.error("❌ Failed to download audio.")

if st.button("2️⃣ Transcribe Audio"):
    with st.spinner("Transcribing..."):
        transcript = transcribe_audio()
        if transcript:
            st.success("✅ Transcription complete!")
            st.text_area("📝 Full Transcript:", transcript, height=200)

if st.button("3️⃣ Generate Summary (Translated)"):
    if os.path.exists("transcript.txt"):
        with open("transcript.txt", "r", encoding="utf-8") as f:
            text = f.read()
        with st.spinner(f"Summarizing in {language} ({summary_type} format)..."):
            summary = summarize_text_openai(text, summary_type, language)
            st.success(f"✅ Summary generated in {language}!")

            if summary_type == "Bullet Points":
                formatted = format_bullet_points(summary)
                st.markdown(f"### 🧾 Numbered Summary ({language}):\n\n{formatted}")

            elif summary_type == "Conversational":
                formatted = format_conversation(summary)
                st.markdown(f"### 💬 Dialogue Summary ({language}):\n\n```\n{formatted}\n```")

            else:
                st.text_area(f"🧾 {language} Summary:", summary, height=250)

            # ✅ Save to local history
            entry = {
                "video_url": video_url,
                "summary_type": summary_type,
                "language": language,
                "summary": summary,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_history(entry)
    else:
        st.error("⚠️ Transcript not found. Please transcribe first.")
