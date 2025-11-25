# YouTube -> Audio -> Text -> Multi-Format + Language + Dialogue Summary Web App
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
    st.info("Attempting audio download...")
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
            st.success("Audio downloaded using yt_dlp!")
            break
        except (yt_dlp.utils.DownloadError, socket.timeout) as e:
            st.warning(f"yt_dlp timeout (try {attempt+1}/3): {e}")
            time.sleep(3)
        except Exception as e:
            st.warning(f"yt_dlp error (try {attempt+1}/3): {e}")
            time.sleep(3)
    else:
        st.error("yt_dlp failed, switching to pytube...")
        try:
            yt = YouTube(video_url)
            stream = yt.streams.filter(only_audio=True).first()
            out_file = stream.download(filename="audio")
            if not out_file.endswith(".wav"):
                os.rename(out_file, filename)
            st.success("Audio downloaded using pytube fallback!")
        except Exception as e:
            st.error(f"pytube also failed: {e}")
            return None

    if os.path.exists("audio.wav"):
        return "audio.wav"
    elif os.path.exists("audio.wav.wav"):
        os.rename("audio.wav.wav", "audio.wav")
        return "audio.wav"
    else:
        st.error("Audio file not found after download.")
        return None

# =============================
# TRANSCRIBE AUDIO (Whisper)
# =============================

def transcribe_audio(audio_file="audio.wav"):
    if not os.path.exists(audio_file):
        st.error("Audio file not found. Please download first.")
        return ""
    st.info("Loading Whisper model (small)...")
    model = whisper.load_model("small")
    st.info("Transcribing audio... please wait...")
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
Convert the following text into a natural back-and-forth dialogue between Speaker 1 and Speaker 2 in {language}.
Each line should be in this format:
Speaker 1: "..."
Speaker 2: "..."
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
        if not re.match(r"^(Speaker 1|Speaker 2):", line):
            speaker = "Speaker 1" if len(formatted) % 2 == 0 else "Speaker 2"
            line = f'{speaker}: "{line}"'
        elif '"' not in line:
            parts = line.split(":", 1)
            if len(parts) == 2:
                speaker, text = parts
                line = f'{speaker.strip()}: "{text.strip()}"'
        formatted.append(line)
    return "\n".join(formatted)

# =============================
# MODERN LIGHT MODE STYLING
# =============================

def apply_modern_styling():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 2rem 1rem;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Header */
    h1 {
        color: #1a1a1a !important;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem !important;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
    }
    
    .subtitle {
        text-align: center;
        color: #4a5568;
        font-size: 1.1rem;
        margin-bottom: 3rem;
        font-weight: 400;
    }
    
    /* Modern Cards */
    div[data-summary-card-marker] {
        display: none;
    }
    
    div[data-testid="stVerticalBlock"]:has(> div > div[data-summary-card-marker]) {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1), 0 4px 12px rgba(0, 0, 0, 0.08);
        margin-bottom: 1.5rem;
        border: 1px solid rgba(0, 0, 0, 0.06);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    div[data-testid="stVerticalBlock"]:has(> div > div[data-summary-card-marker]):hover {
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15), 0 12px 32px rgba(0, 0, 0, 0.1);
        transform: translateY(-4px);
    }
    /* Input section card */
    div[data-testid="stVerticalBlock"]:has(> div > p[data-card="input"]) {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
        margin-bottom: 2rem;
        border: 1px solid rgba(0, 0, 0, 0.06);
    }
    
    p[data-card="workflow-title"] + div[data-testid="stHorizontalBlock"] {
        max-width: 1150px;
        margin: 0 auto 1.5rem;
        gap: 1.5rem !important;
    }
    
    p[data-card="workflow-title"] + div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        min-width: 0;
        display: flex;
    }
    
    p[data-card="workflow-title"] + div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div {
        flex: 1;
        display: flex;
    }
    
    p[data-card="workflow-title"] + div[data-testid="stHorizontalBlock"] div[data-testid="stVerticalBlock"]:has(.step-header[data-card="workflow-step"]) {
        background: transparent;
        border-radius: 0;
        padding: 0;
        box-shadow: none;
        border-left: none;
        transition: none;
        height: 100%;
        display: flex;
        flex-direction: column;
        margin-bottom: 1.5rem;
    }
    
    p[data-card="workflow-title"] + div[data-testid="stHorizontalBlock"] div[data-testid="stVerticalBlock"]:has(.step-header[data-card="workflow-step"]):hover {
        box-shadow: none;
        transform: none;
        border-left-color: transparent;
    }
    
    /* How-to cards */
    .how-section {
        margin: 3rem auto 0;
        text-align: center;
        max-width: 1150px;
    }
    
    .how-section h2 {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #1a1a1a;
    }
    
    .how-section p {
        color: #4a5568;
        margin-bottom: 2rem;
    }
    
    .how-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1.5rem;
        align-items: stretch;
    }
    
    .how-card {
        background: white;
        border-radius: 18px;
        padding: 2rem;
        box-shadow: 0 15px 40px rgba(15, 23, 42, 0.08);
        border: 1px solid rgba(226, 232, 240, 0.9);
        height: 100%;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        text-align: left;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .how-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 35px 60px rgba(15, 23, 42, 0.12);
    }
    
    .how-card-icon {
        width: 56px;
        height: 56px;
        border-radius: 14px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
    }
    
    .how-card-icon i {
        width: 28px;
        height: 28px;
    }
    
    .how-card h4 {
        margin: 0;
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a202c;
    }
    
    .how-card p {
        margin: 0;
        color: #4a5568;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    
    .step-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 1rem;
    }
    
    .step-number {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #FF0000 0%, #CC0000 100%);
        color: white;
        border-radius: 50%;
        font-weight: 700;
        font-size: 1.1rem;
        box-shadow: 0 4px 10px rgba(255, 0, 0, 0.3);
    }
    
    .step-title {
        color: #1a1a1a;
        font-weight: 600;
        font-size: 1.2rem;
        margin: 0;
    }
    
    .step-description {
        color: #718096;
        font-size: 0.9rem;
        margin-bottom: 1rem;
        padding-left: 52px;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input {
        background-color: #f7fafc;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        color: #1a1a1a;
        padding: 12px 16px;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #FF0000;
        background-color: white;
        box-shadow: 0 0 0 3px rgba(255, 0, 0, 0.1);
    }
    
    /* Select Boxes */
    .stSelectbox > div > div {
        background-color: #f7fafc;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:hover {
        border-color: #FF0000;
    }
    
    .stSelectbox label {
        color: #2d3748 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #FF0000 0%, #CC0000 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 14px 28px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 4px 12px rgba(255, 0, 0, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 0, 0, 0.4);
        background: linear-gradient(135deg, #FF1A1A 0%, #E60000 100%);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Text Areas */
    .stTextArea > div > div > textarea {
        background-color: #f7fafc;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        color: #1a1a1a;
        padding: 12px;
        font-size: 0.95rem;
        transition: all 0.3s ease;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #FF0000;
        background-color: white;
        box-shadow: 0 0 0 3px rgba(255, 0, 0, 0.1);
    }
    
    .stTextArea label {
        color: #2d3748 !important;
        font-weight: 600 !important;
    }
    
    /* Icon headings */
    .icon-heading {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        font-weight: 700;
    }
    
    .icon-heading i {
        width: 22px;
        height: 22px;
    }
    
    .step-title {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 0;
    }
    
    .step-title i {
        width: 20px;
        height: 20px;
    }
    
    .summary-heading {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    .summary-heading i {
        width: 20px;
        height: 20px;
    }
    
    /* Alert Messages */
    .stAlert {
        background-color: white;
        border-radius: 12px;
        border-left: 4px solid;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: white;
        border-right: 1px solid #e2e8f0;
        box-shadow: 4px 0 10px rgba(0, 0, 0, 0.05);
        position: sticky;
        top: 0;
        height: 100vh;
        align-self: flex-start;
    }
    
    section[data-testid="stSidebar"] > div {
        height: 100%;
        overflow-y: auto;
        padding-bottom: 2rem;
    }
    
    section[data-testid="stSidebar"] h2 {
        color: #1a1a1a !important;
        font-weight: 700 !important;
        font-size: 1.3rem !important;
    }
    
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label {
        color: #4a5568 !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
        border: none;
        color: white;
    }
    
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, #fc8181 0%, #f56565 100%);
    }
    
    section[data-testid="stSidebar"] hr {
        border-color: #e2e8f0;
        margin: 1.5rem 0;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #f7fafc;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        color: #2d3748;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: #edf2f7;
        border-color: #FF0000;
    }
    
    .streamlit-expanderContent {
        background-color: white;
        border: 2px solid #e2e8f0;
        border-top: none;
        border-radius: 0 0 12px 12px;
        color: #4a5568;
    }
    
    /* Audio Player */
    audio {
        width: 100%;
        margin: 1rem 0;
        border-radius: 12px;
    }
    
    /* Section Headers */
    h3 {
        color: #1a1a1a !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
        margin-top: 2rem;
        margin-bottom: 1.5rem;
    }
    
    /* Labels */
    label {
        color: #2d3748 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    
    /* Progress Indicator */
    .progress-bar {
        width: 100%;
        height: 6px;
        background: #e2e8f0;
        border-radius: 10px;
        overflow: hidden;
        margin: 1rem 0;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #FF0000 0%, #CC0000 100%);
        border-radius: 10px;
        transition: width 0.5s ease;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #FF0000 !important;
    }
    
    /* Info boxes */
    .info-box {
        background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%);
        border-left: 4px solid #3182ce;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        color: #2c5282;
    }
    
    .success-box {
        background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
        border-left: 4px solid #38a169;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        color: #22543d;
    }
    
    /* Card title */
    .card-title {
        color: #1a1a1a;
        font-weight: 700;
        font-size: 1.3rem;
        margin-bottom: 1.5rem;
        padding-bottom: 0.8rem;
        border-bottom: 2px solid #e2e8f0;
    }
    </style>
    """, unsafe_allow_html=True)


def inject_lucide_icons():
    """Injects Lucide icons and ensures they render after Streamlit reruns."""
    st.markdown("""
    <script src="https://unpkg.com/lucide@latest"></script>
    <script>
    const renderLucideIcons = () => {
        if (window.lucide) {
            window.lucide.createIcons();
        }
    };
    window.renderLucideIcons = renderLucideIcons;
    renderLucideIcons();
    const observer = new MutationObserver(() => renderLucideIcons());
    observer.observe(document.body, { subtree: true, childList: true });
    </script>
    """, unsafe_allow_html=True)

# =============================
# STREAMLIT UI
# =============================

st.set_page_config(
    page_title="YouTube AI Summarizer",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_modern_styling()
inject_lucide_icons()

# Header
st.markdown("""
    <h1>
        <svg viewBox="0 0 24 24" width="40" height="40" fill="#FF0000">
            <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
        </svg>
        YouTube AI Summarizer
    </h1>
""", unsafe_allow_html=True)

st.markdown('<p class="subtitle">Transform YouTube videos into intelligent summaries with AI-powered transcription and translation</p>', unsafe_allow_html=True)

# Input Card
st.markdown('<p data-card="input" class="card-title icon-heading"><i data-lucide="settings-2"></i><span>Input & Configuration</span></p>', unsafe_allow_html=True)

video_url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...", label_visibility="visible")

col_format, col_lang = st.columns(2)
with col_format:
    summary_type = st.selectbox("Summary Format", ["Paragraph", "Bullet Points", "Conversational"])
with col_lang:
    language = st.selectbox("Output Language", ["English", "Kannada", "Hindi","Tamil","Telugu","Malayalam","Bengali","French","Arabic","Korean"])

# Processing Workflow
st.markdown('<p data-card="workflow-title" class="card-title icon-heading" style="margin-top: 2rem;"><i data-lucide="workflow"></i><span>Processing Workflow</span></p>', unsafe_allow_html=True)

# Create 3 columns for workflow steps
col1, col2, col3 = st.columns(3, gap="large")

# Step 1: Download
with col1:
    with st.container():
        st.markdown('''
            <div class="step-header" data-card="workflow-step">
                <span class="step-number">1</span>
                <h3 class="step-title"><i data-lucide="download"></i>Download Audio</h3>
            </div>
            <p class="step-description">Extract high-quality audio from the YouTube video</p>
        ''', unsafe_allow_html=True)

        if st.button("Start Download", key="btn_download", use_container_width=True):
            with st.spinner("Downloading audio from YouTube..."):
                audio_path = download_audio(video_url)
                if audio_path:
                    st.success("Audio downloaded successfully!")
                    st.audio(audio_path)

# Step 2: Transcribe
with col2:
    with st.container():
        st.markdown('''
            <div class="step-header" data-card="workflow-step">
                <span class="step-number">2</span>
                <h3 class="step-title"><i data-lucide="mic"></i>Transcribe Audio</h3>
            </div>
            <p class="step-description">Convert speech to text using advanced AI technology</p>
        ''', unsafe_allow_html=True)

        if st.button("Start Transcription", key="btn_transcribe", use_container_width=True):
            with st.spinner("Transcribing audio... This may take a minute"):
                transcript = transcribe_audio()
                if transcript:
                    st.success("Transcription completed!")
                    with st.expander("View Full Transcript"):
                        st.text_area("", transcript, height=200, label_visibility="collapsed", key="transcript_view")

# Step 3: Summarize
with col3:
    with st.container():
        st.markdown('''
            <div class="step-header" data-card="workflow-step">
                <span class="step-number">3</span>
                <h3 class="step-title"><i data-lucide="file-text"></i>Generate Summary</h3>
            </div>
            <p class="step-description">Create an intelligent summary in your chosen language and format</p>
        ''', unsafe_allow_html=True)

        if st.button("Generate Summary", key="btn_summarize", use_container_width=True):
            if os.path.exists("transcript.txt"):
                with open("transcript.txt", "r", encoding="utf-8") as f:
                    text = f.read()
                with st.spinner(f"Generating {summary_type} summary in {language}..."):
                    summary = summarize_text_openai(text, summary_type, language)
                    st.success(f"Summary generated in {language}!")

                    with st.container():
                        st.markdown('<div data-summary-card-marker></div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="summary-heading icon-heading"><i data-lucide="notebook-text"></i><span>{summary_type} Summary ({language})</span></div>', unsafe_allow_html=True)
                        
                        if summary_type == "Bullet Points":
                            formatted = format_bullet_points(summary)
                            st.markdown(formatted)
                        elif summary_type == "Conversational":
                            formatted = format_conversation(summary)
                            st.code(formatted, language="text")
                        else:
                            st.text_area("", summary, height=250, label_visibility="collapsed", key="summary_output")

                    # Save to history
                    entry = {
                        "video_url": video_url,
                        "summary_type": summary_type,
                        "language": language,
                        "summary": summary,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    save_history(entry)
            else:
                st.error("Please complete transcription first.")

how_cards = [
    {
        "title": "Step 1 · Share the video link",
        "description": "Paste any public YouTube URL and pick the summary style and language that fits your workflow.",
        "icon": "link-2",
        "accent": "#2563eb"
    },
    {
        "title": "Step 2 · Let the AI do the heavy lifting",
        "description": "Kick off download + transcription. We fetch the audio, run Whisper, and prep the transcript automatically.",
        "icon": "cpu",
        "accent": "#d97706"
    },
    {
        "title": "Step 3 · Review and reuse the summary",
        "description": "Generate concise paragraphs, bullets, or dialogue recaps and save them to history for quick access.",
        "icon": "notebook-text",
        "accent": "#16a34a"
    }
]

how_cards_html = "".join([
    f"""
    <div class="how-card">
        <div class="how-card-icon" style="background: {card['accent']}1a; color: {card['accent']};">
            <i data-lucide="{card['icon']}"></i>
        </div>
        <h4>{card['title']}</h4>
        <p>{card['description']}</p>
    </div>
    """
    for card in how_cards
])

st.markdown(f"""
    <div class="how-section">
        <h2>How to Summarize YouTube Videos?</h2>
        <p>You can turn any video into a structured summary in just three guided steps.</p>
        <div class="how-grid">
            {how_cards_html}
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown('<script>window.renderLucideIcons && window.renderLucideIcons();</script>', unsafe_allow_html=True)

st.markdown('<script>window.renderLucideIcons && window.renderLucideIcons();</script>', unsafe_allow_html=True)

# =============================
# SIDEBAR HISTORY
# =============================

with st.sidebar:
    st.markdown('<div class="icon-heading" style="font-size:1.25rem;"><i data-lucide="clock-3"></i><span>History</span></div>', unsafe_allow_html=True)
    
    history = load_history()
    st.markdown(f"**{len(history)} summaries saved**")
    st.markdown("")
    
    if st.button("Clear All History", use_container_width=True):
        open(HISTORY_FILE, "w").write("[]")
        st.success("History cleared!")
        st.rerun()
    
    st.markdown("---")
    
    if history:
        for idx, item in enumerate(history[:10]):
            with st.expander(f"{item['timestamp']}", expanded=False):
                st.markdown("**Video**")
                st.caption(f"[{item['video_url'][:40]}...]({item['video_url']})")
                st.markdown(f"**Language:** {item['language']}")
                st.markdown(f"**Format:** {item['summary_type']}")
                st.markdown("**Summary:**")
                summary_preview = item['summary'][:300] + "..." if len(item['summary']) > 300 else item['summary']
                st.text_area("", summary_preview, height=120, key=f"hist_{idx}", label_visibility="collapsed")
    else:
        st.info("No summaries yet. Process your first video!")
