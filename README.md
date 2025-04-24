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

---

## 🧰 Tech Stack

- Python 3.10+ (macOS)
- Tkinter
- SQLite3
- `sounddevice`, `soundfile`, `numpy`
- `python-dotenv` for managing API keys
- `pyinstaller` for packaging

---


## 🎛 Aggregate Device Setup
	
	1.	Install BlackHole 16ch
	2.	Open Audio MIDI Setup
	3.	Create an Aggregate Device combining:
		•	✅ Built-in Microphone
		•	✅ BlackHole 16ch
    	•	✅ MacBook Speakers
    4.  Set Clock Source to MacBook Speakers


#### Audio MIDI Setup(Pay attention to the order of subdevices):
![alt text](docs/audio_midi_setup.png)

#### Speakers Configuration:
![img.png](docs/speakers_configuration.png)
---

## 📦 How to Run (Dev)

```bash
# 1. Clone the repo and navigate to the project
git clone https://github.com/mrbelka12000/audio_parser.git
cd audio_parser
```

```bash
pip install -r requirements.txt
```

### env.py example
```python
import os
os.environ["ASSEMBLY_KEY"] = "****"
os.environ["AI_TOKEN"] = "****"
```

```bash
pyinstaller audio_parser/main.py --distpath app --runtime-hook=env.py
sudo cp app/main/main /usr/local/bin/ap
sudo cp -R app/main/_internal /usr/local/bin/_internal
```


### Run program:

```bash
ap
```

## 🧪 Usage
	•	Start Recording → Captures input/output audio
	•	Stop Recording → Triggers async transcription & analytics
	•	View Files → Browse stored recordings with full metadata
	•	Edit Transcript → Save changes in real-time -> Automatically update analytics


---

## 🚀 Next Steps

    •	📦 Package as a .dmg for easy macOS distribution
    •	🖥 Make cross-platform by supporting Windows and Linux
    •	🎛 Implement a visual progress bar during transcription & analytics
    •	💬 Add multi-language support for transcripts and UI
    •	☁️ Optional: Integrate with cloud storage (Dropbox, Google Drive) for recording backup
    •	📊 Add advanced analytics and visualizations for spoken content
    •	🧪 Add unit tests and CI for packaging validation across platforms

---
## 📬 Contact

If you have questions, feedback, or want to collaborate — feel free to reach out:

- 👤 **Beknur Karshyga**
- 📧 Email: [karshyga.beknur@gmail.com](mailto:karshyga.beknur@gmail.com)
- 💼 GitHub: [@mrbelka12000](https://github.com/mrbelka12000)
- 🌐 LinkedIn: [Beknur Karshyga](https://www.linkedin.com/in/beknur-karshyga)

Feel free to submit issues or feature requests through the GitHub repo as well!

---