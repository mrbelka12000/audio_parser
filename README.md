# 🎙️ Audio Parser — GUI Recorder with Transcript & Analytics

This is a macOS desktop application for recording system and microphone audio, transcribing it, and analyzing the result using AI. Built with Python, Tkinter, SQLite, and packaged via `py2app`.

---

## 🚀 Features

- ✅ Record system + microphone audio via **Aggregate Device** (BlackHole + Built-in Mic)
- ✅ Save recordings locally as `.wav`
- ✅ Automatically transcribe using AssemblyAI
- ✅ Analyze transcript using custom AI logic
- ✅ Store metadata in **SQLite** database
- ✅ View & edit transcripts in GUI
- ✅ Display analytics per file
- ✅ Async-safe **loading indicator** during processing
- ✅ Bundled as `.app` using **py2app**

---

## 🧰 Tech Stack

- Python 3.10+ (macOS)
- Tkinter
- SQLite3
- `sounddevice`, `soundfile`, `numpy`
- `python-dotenv` for managing API keys
- `py2app` for packaging

---

## 📦 How to Run (Dev)

```bash
# 1. Clone the repo and navigate to the project
cd audio_parser

# 2. Create virtual environment
python3 -m venv env
source env/bin/activate

# 3. Install dependencies
pip install -r requirements.txt