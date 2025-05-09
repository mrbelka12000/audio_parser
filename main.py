import sounddevice as sd
import tkinter as tk
import threading
import queue
import numpy as np
from tkinter import Toplevel, Listbox, Scrollbar, RIGHT, Y, messagebox, simpledialog
from openai import OpenAI
import sqlite3
import speech_recognition as sr
import uuid
import io
import os
from scipy.io.wavfile import write
import logging

# -----------------------SETTINGS----------------------------
samplerate = 44100
channels = 2  # record more to capture full mic + system range
q = queue.Queue()
recording = False
stream = None
frames = []
r = sr.Recognizer()
myuuid = None

default_directory_name = "~/.audio_parser"
database_name='recordings.db'
default_files_dir = "files/"
default_logs_dir = "logs/"
api_key_id = 10
api_key = None

collected_audio_np = []


def init_dirs():

    os.makedirs(os.path.expanduser(default_directory_name), exist_ok=True)
    os.makedirs(os.path.expanduser(os.path.join(default_directory_name, default_files_dir)), exist_ok=True)
    os.makedirs(os.path.expanduser(os.path.join(default_directory_name, default_logs_dir)), exist_ok=True)

init_dirs()


def get_file_path(file_name):
    return os.path.expanduser(os.path.join(default_directory_name, default_files_dir, file_name+".wav"))

def get_file_name():
    return f"{myuuid}"

def get_logging_file_name():
    return os.path.expanduser(os.path.join(default_directory_name, default_logs_dir, "logs.txt"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename=get_logging_file_name(),
    filemode="a",
)
# -----------------------DATABASE---------------------------

def connect():
    db_path = os.path.expanduser(os.path.join(default_directory_name, database_name))
    conn = sqlite3.connect(db_path)
    return conn

def init_db():
    conn = connect()
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS recordings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT,
        transcript TEXT,
        analytics TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS api_key(
        id  INTEGER,
        key TEXT
    )
""")

    conn.commit()
    conn.close()


def insert_transript(file_name, transcript):
    conn = connect()
    cur = conn.cursor()

    # Insert record
    cur.execute("""
        INSERT INTO recordings (file_name, transcript)
        VALUES (?, ?)
    """, (file_name, transcript))
    
    conn.commit()
    conn.close()


def update_analytics(file_name, analytics):
    conn = connect()
    cur = conn.cursor()

    # Update the analytics field for the matching file_name
    cur.execute("""
        UPDATE recordings
        SET analytics = ?
        WHERE file_name = ?
    """, (analytics, file_name))

    if cur.rowcount == 0:
        logging.info(f"[DB] No record found for: {file_name}")
    else:
        logging.info(f"[DB] Analytics updated for: {file_name}")
    
    conn.commit()
    conn.close()

# Function to add text to an existing transcript in the database, or insert if no record exists
def add_text_to_transcript(file_name, new_text):
    conn = connect()
    cur = conn.cursor()

    # Check if a transcript already exists for the given file_name
    cur.execute("SELECT id, transcript FROM recordings WHERE file_name = ?", (file_name,))
    row = cur.fetchone()
    if row:
        # If a transcript exists, append the new text
        current_transcript = row[1]  # Get the existing transcript (index 1)
        updated_transcript = current_transcript + " " + new_text
        # Update the transcript in the database
        cur.execute("UPDATE recordings SET transcript = ? WHERE file_name = ?", (updated_transcript, file_name))
    else:
        # If no record exists, insert a new one with the file_name and new_text as transcript
        cur.execute("INSERT INTO recordings (file_name, transcript) VALUES (?, ?)", (file_name, new_text))

    # Commit changes and close the connection
    conn.commit()
    conn.close()

def get_recording(file_name):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, file_name, transcript, analytics, created_at
        FROM recordings
        WHERE file_name = ?
    """, (file_name,))
    
    row = cur.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "file_name": row[1],
            "transcript": row[2],
            "analytics": row[3],
            "created_at": row[4],
        }
    else:
        return None
    

def set_api_key(api_key):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO api_key(id, key) VALUES(?, ?)", (api_key_id, api_key))
    conn.commit()
    conn.close()

def get_api_key():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT key FROM api_key WHERE id = ?
""", (api_key_id,))
    row = cur.fetchone()
    conn.close()

    if row:
        return {
            "key": row[0],
        }
    else:
        return None
    
def update_transcript(file_name, new_transcript):
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE recordings SET transcript = ? WHERE file_name = ?", (new_transcript, file_name))
    conn.commit()
    conn.close()

def update_analytics(file_name, new_analytics):
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE recordings SET analytics = ? WHERE file_name = ?", (new_analytics, file_name))
    conn.commit()
    conn.close()

def get_all_recordings():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, file_name, transcript, analytics, created_at
        FROM recordings
        ORDER BY created_at DESC
    """)
    
    rows = cur.fetchall()
    conn.close()

    recordings = []
    for row in rows:
        recordings.append({
            "id": row[0],
            "file_name": row[1],
            "transcript": row[2],
            "analytics": row[3],
            "created_at": row[4]
        })

    return recordings


def delete_record_by_file_name(file_name):
    try:
        conn = connect()  # replace with your correct DB path
        cur = conn.cursor()
        cur.execute("DELETE FROM recordings WHERE file_name = ?", (file_name,))
        conn.commit()
        conn.close()
        logging.info(f"✅ Record with file_name '{file_name}' deleted.")
    except Exception as e:
        logging.error(f"❌ Failed to delete record '{file_name}': {e}")

def delete_all_records():
    answer = messagebox.askyesno("Confirm", "Are you sure you want to delete all records?")
    if answer:
        try:
            recordings = get_all_recordings()
            for rec in recordings:
                file_path = get_file_path(file_name=rec.get("file_name"))
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logging.info(f"✅ File '{file_path}' deleted successfully.")
                else:
                    logging.error(f"⚠️ File '{file_path}' does not exist.")        
        except Exception as e:
            logging.error(f"⚠️ Failed to delete file:'{file_path}'.")        
            messagebox.showinfo("Failed", f"Something went wrong: {e}")
            return

        try:
            conn = connect()
            cur = conn.cursor()
            cur.execute("DELETE FROM recordings")
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "All records have been deleted.")
        except Exception as e:
            logging.error(f"failed delete file: {e}")
            messagebox.showinfo("Failed", f"Something went wrong: {e}")

# -----------------------AI------------------------------
def get_analytics_from_ai(transcript):
    client = OpenAI(
        # This is the default and can be omitted
        api_key=api_key,
    )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "developer", "content": 'Я предоставлю тебе транскрипт или краткое содержание нашей ежедневной встречи. Твоя задача — проанализировать его и составить чёткий, действенный план. Результат должен включать: 	1.	Ключевые обсуждаемые темы 	2.	Задачи к выполнению (с ответственными и сроками, если есть) 	3.	Открытые вопросы или блокеры 	4.	Следующие шаги  Будь кратким и используй маркированные списки для наглядности.'},
            {
                "role": "user",
                "content": transcript,
            },
        ],
    )

    return completion.choices[0].message.content

# -----------------------TKINTER---------------------------
def audio_callback(indata, frames_, time_, status):
    if status:
        logging.info("Stream status:", status)
    q.put(indata.copy())

def start_recording():
    global stream, recording, frames,myuuid
    myuuid = uuid.uuid4()

    frames.clear()
    recording = True
    btn_start.config(state=tk.DISABLED)
    btn_stop.config(state=tk.NORMAL)

    def _record():
        global stream
        device = None
        for idx, d in enumerate(sd.query_devices()):
            if "default" in d['name']:
                device = idx
                break
        if device is None:
            logging.error("Aggregate device not found")
            return

        stream = sd.InputStream(samplerate=samplerate,
                                channels=channels,
                                callback=audio_callback,
                                device=device,
                                )
        stream.start()
        while recording:
            while not q.empty() and recording:

                frames.append(q.get())

                if len(frames) >= 200 and len(frames) % 50 == 0:
                    process_stream()

            sd.sleep(100)

        stream.stop()
        stream.close()

    threading.Thread(target=_record, daemon=True).start()


def get_audio_np():
    audio_data = np.concatenate(frames, axis=0)

    if audio_data.ndim == 2 and audio_data.shape[1] == 2:
        audio_data = audio_data.mean(axis=1)

    if np.all(audio_data == 0):
        logging.debug("❌ Audio is all zeros.")
        return np.zeros(1, dtype=np.int16)

    audio_data = audio_data.astype(np.float32)
    gain = 2.5  # ← adjust gain factor here (1.0 = no change)
    audio_data *= gain

    audio_data = (audio_data * 32767).clip(-32768, 32767).astype(np.int16)
    return audio_data

def get_transcript(audio_data):
    try:
        transcript = r.recognize_google(audio_data, language="ru-RU")
        if len(transcript.strip()) == 0:
            logging.debug("Empty transcript")
            return

        return transcript
    except sr.UnknownValueError:
        logging.error("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        logging.error(f"Google Speech Recognition request failed: {e}")
    except Exception as e:
        logging.error(f"Other error: {e}")

def process_stream():
    logging.info(f"Frame count: {len(frames)}")

    if len(frames) == 0:
        logging.info("⚠️ No audio frames collected.")
        return

    audio_np = get_audio_np()
    frames.clear()
    collected_audio_np.append(audio_np)

    # Convert to bytes
    try:
        byte_io = io.BytesIO()
        write(byte_io, samplerate, audio_np)
        byte_io.seek(0)
        result_bytes = byte_io.read()
        audio_data = sr.AudioData(result_bytes, sample_rate=samplerate, sample_width=2)


    except Exception as e:
        logging.error("❌ Audio conversion error:", e)
        return

    transcript = get_transcript(audio_data)
    logging.info(f"Transcript result: {transcript}")

    if transcript is None or len(transcript.strip()) == 0:
        logging.debug("❌ Empty transcript")
        return

    add_text_to_transcript(get_file_name(), transcript)

    logging.info("=== process_stream END ===")
    return transcript

def stop_recording():
    global recording
    recording = False
    btn_start.config(state=tk.NORMAL)
    btn_stop.config(state=tk.DISABLED)

    while not q.empty():
        frames.append(q.get())

    if not frames:
        logging.debug("No audio captured.")
        return
    
    # Show loader
    loader = tk.Toplevel(root)
    loader.geometry("300x100")
    loader.title("Processing")
    loader_label = tk.Label(loader, text="⏳ Getting transcript...")
    loader_label.pack(pady=20)

    # Step 1: after 100ms, update to transcript
    def step_1():
        loader_label.config(text="📄 Getting transcript...")
        transcript = process_stream()
        if transcript is None:
            transcript = ''

        root.after(100, lambda: step_2())  # next step

    # Step 2: update to analytics
    def step_2():

        loader_label.config(text="📊 Analyzing transcript...")

        file_name = get_file_name()
  
        rec = get_recording(file_name=file_name)
        analytics = get_analytics_from_ai(transcript=rec.get("transcript"))
        update_analytics(file_name=file_name, new_analytics=analytics)

        root.after(100, step_3)

    # Step 3: close loader
    def step_3():
        try:
            save_full_audio()
            global collected_audio_np
            collected_audio_np = []
        except Exception as e:
            logging.error(f"Got error on save full audio{e}")
            messagebox.showinfo("Failed" f"Transcript and Analytics is ready but failed to save audio:{e}")

        loader_label.config(text="✅ Done!")
        root.after(1000, loader.destroy)

    root.after(100, step_1)

def save_full_audio():
    if not collected_audio_np:
        logging.debug("⚠️ No collected audio to save.")
        return

    output_path = get_file_path(file_name=get_file_name())

    import numpy as np
    full_audio = np.concatenate(collected_audio_np, axis=0)

    from scipy.io.wavfile import write
    write(output_path, samplerate, full_audio)

    logging.info(f"✅ Full audio saved to {output_path}")


def open_files_window():
    window = Toplevel(root)
    window.title("📁 Recordings in Database")
    window.geometry("600x400")

    listbox = Listbox(window, width=80)
    listbox.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

    scrollbar = Scrollbar(window, orient="vertical", command=listbox.yview)
    scrollbar.pack(side=RIGHT, fill=Y)
    listbox.config(yscrollcommand=scrollbar.set)

    # Get all recordings from the DB
    recordings = get_all_recordings()
    for rec in recordings:
        filename = rec.get("file_name") or "N/A"
        created = rec.get("created_at") or "Unknown"

        display_text = f"{str(created).ljust(25)} {str(filename).ljust(30)}"
        listbox.insert(tk.END, display_text)
    # Store mapping: index -> file_name
    index_to_path = {i: rec["file_name"] for i, rec in enumerate(recordings)}

    def on_file_select(event):
        selected_idx = listbox.curselection()

        if not selected_idx:
            return

        filename = index_to_path[selected_idx[0]]

        show_file_actions(filename)

    listbox.bind("<<ListboxSelect>>", on_file_select)

def show_file_actions(filename):
    from tkinter import messagebox

    action_win = Toplevel(root)
    action_win.title(f"Transcript for {filename}")
    action_win.geometry("800x600")

    base_name = filename

    save_button_visible = {"transcript": False, "analytics":False}  # use mutable dict to modify in nested scope

    # Text box
    text_box = tk.Text(action_win, wrap="word")
    text_box.pack(expand=True, fill="both", padx=10, pady=10)
    rec = get_recording(base_name)
    text_box.insert(tk.END, rec["transcript"])

    def show_transcript():

        save_button_visible["analytics"] = False
        save_button_visible["transcript"] = True

        rec = get_recording(base_name)
        text_box.delete(1.0, tk.END)
        if rec and rec["transcript"]:
            text_box.insert(tk.END, rec["transcript"])
        else:
            text_box.insert(tk.END, "No transcript found.")


    def show_analytics():
        save_button_visible["analytics"] = True
        save_button_visible["transcript"] = False

        action_win.title(f"Analytics for {filename}")
        rec = get_recording(base_name)
        text_box.delete(1.0, tk.END)
        if rec and rec["analytics"]:
            text_box.insert(tk.END, rec["analytics"])
        else:
            text_box.insert(tk.END, "No analytics found.")


    def save_changes():
        if save_button_visible["transcript"]:
            save_transcript()
        elif save_button_visible["analytics"]:
            save_analytics()

    def save_transcript():
        new_text = text_box.get("1.0", tk.END).strip()
        update_transcript(base_name, new_text)
        analytics = get_analytics_from_ai(new_text)
        update_analytics(file_name=base_name, new_analytics=analytics)
        messagebox.showinfo("Saved", "✅ Transcript has been successfully updated!")

    def save_analytics():
        new_analytics = text_box.get("1.0", tk.END).strip()
        update_analytics(file_name=base_name, new_analytics=new_analytics)
        messagebox.showinfo("Saved", "✅ Analytics has been successfully updated!")

    # Buttons
    btn_text = tk.Button(action_win, text="📝 Show Transcript", command=show_transcript)
    btn_text.pack(pady=5)

    btn_analytics = tk.Button(action_win, text="📊 Show Analytics", command=show_analytics)
    btn_analytics.pack(pady=5)

    btn_update = tk.Button(action_win, text="💾 Save Changes", command=save_changes)
    btn_update.pack(pady=5)



# GUI Setup
root = tk.Tk()
root.title("🎙 Dual Audio Recorder")



# ---------------------API_KEY_VALIDATION-------------------------

def prompt_api_key():
    global api_key
    # Disable main window until key entered
    root.withdraw()

    while not api_key:
        api_key = simpledialog.askstring("API Key Required", "Please enter your API Key:", show='*')
        if api_key is None or api_key.strip() == "":
            messagebox.showwarning("Required", "API Key is required to use the app.")
            continue
        api_key = api_key.strip()

        try:
            get_analytics_from_ai("test_transcript")
            set_api_key(api_key)
            break
        except Exception as e:
            messagebox.showerror("Invalid", "API Key is invalid.")
            logging.error(f"Api key is invalid{e}")
            api_key = None  # ❗️reset so loop continues
            continue
            

    # Re-enable main window
    root.deiconify()

init_db()

rec = get_api_key()
if rec and rec["key"]:
    api_key = rec["key"]

prompt_api_key()



# -------------------------TKINTER-----------------------------


btn_start = tk.Button(root, text="Start Recording", command=start_recording)
btn_start.pack(padx=20, pady=10)

btn_stop = tk.Button(root, text="Stop Recording", command=stop_recording, state=tk.DISABLED)
btn_stop.pack(padx=20, pady=10)

btn_view_files = tk.Button(root, text="View Files", command=open_files_window)
btn_view_files.pack(padx=20, pady=10)

btn_delete_all = tk.Button(root, text="Delete All Records", command=delete_all_records)
btn_delete_all.pack(padx=20, pady=10)

root.mainloop()