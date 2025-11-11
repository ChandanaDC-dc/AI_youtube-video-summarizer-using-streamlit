Portfolio
🎥 YouTube Video AI Summarizer

🧠 AI-powered summarization of YouTube videos into structured, multilingual summaries.

🧠 Overview

The YouTube Video AI Summarizer automatically extracts transcripts or audio from YouTube videos and uses AI to summarize the content into multiple formats such as bullet points, paragraphs, or topic highlights.
It’s designed to help users quickly understand lengthy videos without needing to watch them fully.

🚀 Key Features

🎥 YouTube Transcript Extraction — Fetches video transcripts automatically

🧠 AI Summarization — Converts video content into:

Bullet-point summaries

Paragraph summaries

Topic-wise sections

🌍 Multilingual Support — Summaries in English, Kannada, Hindi, and French

📝 Format Options — Choose your preferred summary style

🔊 Audio-to-Text Conversion (if no transcript available)

💻 Clean Streamlit UI for simple, interactive use

🧰 Tech Stack
Function	Technology
Transcript Extraction	YouTube Transcript API
AI Model	Google Gemini / OpenAI GPT
App Framework	Streamlit
Backend	Python
Translation	Google Translate API or model-based translation
File Handling	textwrap, re, os
⚙️ Installation
1️⃣ Clone the repository
git clone https://github.com/ChandanaDC-dc/AI_youtube-video-summarizer-using-streamlit
cd AI_youtube-video-summarizer-using-streamlit
2️⃣ Install dependencies
pip install streamlit youtube-transcript-api google-generativeai openai textwrap

3️⃣ Add your API key

Open the code and replace the placeholder:

GEMINI_API_KEY = "YOUR_API_KEY_HERE"

4️⃣ Run the app
streamlit run app_youtube_summarizer.py

🧭 How to Use

Paste a YouTube video link into the input box.

Select the summary type — bullet points, paragraph, or detailed summary.

Choose output language (English, Kannada, Hindi, or French).

Click “Generate Summary” — AI will process the transcript and display results instantly.

🧠 Example Output

Input Video:
“AI in Agriculture – Future of Smart Farming”

Output Summary (Bullet Format):

AI is revolutionizing farming with precision analysis.

Farmers can detect diseases early using image recognition.

Crop recommendations are optimized using data models.

Output Summary (Kannada):

ಕೃಷಿಯಲ್ಲಿ ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ ನಿಖರವಾದ ವಿಶ್ಲೇಷಣೆಯನ್ನು ನೀಡುತ್ತದೆ.

ರೈತರು ಚಿತ್ರ ಗುರುತಿಸುವಿಕೆಯ ಮೂಲಕ ಬೆಳೆ ರೋಗಗಳನ್ನು ಬೇಗನೆ ಪತ್ತೆಹಚ್ಚಬಹುದು.

🧩 Folder Structure
📦 youtube-ai-summarizer
 ┣ 📄 app_youtube_summarizer.py
 ┣ 📄 README.md
 ┣ 📁 transcripts/
 ┣ 📁 outputs/
 ┗ 📄 requirements.txt

🧭 Future Enhancements

⏱️ Timestamp-based summaries (jump to key moments)

🗣️ Voice-over of summaries

💾 Download summaries as PDF or text files

🧩 Chrome extension for direct YouTube summarization

👩‍💻 Developer

Name: Chandana DC
Role: AI & Software Developer
Focus Areas: AI, NLP, Summarization Systems, Multilingual Processing

⚖️ License

This project is open-sourced under the MIT License.
Feel free to use and modify with attribution.

🌟 Acknowledgments

Special thanks to:

YouTube Transcript API for transcript access

Google Gemini / OpenAI GPT for summarization models

Streamlit for easy UI building
