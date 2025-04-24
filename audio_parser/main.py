import sounddevice as sd
import soundfile as sf
import tkinter as tk
import threading
import queue
import numpy as np
import time
import os
from tkinter import Toplevel, Listbox, messagebox
import analyze
import assembly
import db

samplerate = 44100
channels = 10  # record more to capture full mic + system range
q = queue.Queue()
recording = False
stream = None
frames = []
files_dir = "files/"
os.makedirs(files_dir, exist_ok=True)

def get_file_name():
    from datetime import datetime
    return datetime.now().strftime("recording_%Y%m%d_%H%M%S")

def audio_callback(indata, frames_, time_, status):
    if status:
        print("Stream status:", status)
    q.put(indata.copy())

def start_recording():
    global stream, recording, frames
    frames.clear()
    recording = True
    btn_start.config(state=tk.DISABLED)
    btn_stop.config(state=tk.NORMAL)

    def _record():
        global stream
        device = None
        for idx, d in enumerate(sd.query_devices()):
            if "Aggregate" in d['name']:
                device = idx
                break
        if device is None:
            print("Aggregate device not found")
            return

        stream = sd.InputStream(samplerate=samplerate,
                                channels=channels,
                                callback=audio_callback,
                                device=device)
        stream.start()
        while recording:
            while not q.empty():
                frames.append(q.get())
            sd.sleep(100)
        stream.stop()
        stream.close()

    threading.Thread(target=_record, daemon=True).start()

def stop_recording():
    global recording
    recording = False
    btn_start.config(state=tk.NORMAL)
    btn_stop.config(state=tk.DISABLED)

    if not frames:
        print("No audio captured.")
        return

    audio_data = np.concatenate(frames, axis=0)
    base_name = os.path.join(files_dir, get_file_name())
    full_path = base_name + ".wav"
    sf.write(full_path, audio_data, samplerate)
    print(f"[Saved] Full: {full_path}")

    # Show loader
    loader = tk.Toplevel(root)
    loader.geometry("300x100")
    loader.title("Processing")
    loader_label = tk.Label(loader, text="⏳ Processing audio...")
    loader_label.pack(pady=20)

    # Step 1: after 100ms, update to transcript
    def step_1():
        loader_label.config(text="📄 Getting transcript...")
        transcript = assembly.get_transcript(full_path)
        db.insert_transript(file_path=full_path, transcript=transcript)
        print("Transcript Done")
        root.after(100, lambda: step_2(transcript))  # next step

    # Step 2: update to analytics
    def step_2(transcript):
        loader_label.config(text="📊 Analyzing transcript...")
        analytics = analyze.get_analytics_from_ai(transcript=transcript)
        db.update_analytics(file_path=full_path, new_analytics=analytics)
        print("Analyze done")
        root.after(100, step_3)

    # Step 3: close loader
    def step_3():
        loader_label.config(text="✅ Done!")
        root.after(1000, loader.destroy)

    root.after(100, step_1)

from tkinter import Toplevel, Listbox, Scrollbar, RIGHT, Y
from db import get_all_recordings  # assuming you saved that function

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
        filename = os.path.basename(rec["file_path"])
        created = rec["created_at"]
        display_text = f"{created.ljust(25)} {filename.ljust(30)}"
        listbox.insert(tk.END, display_text)

    # Store mapping: index -> file_path
    index_to_path = {i: rec["file_path"] for i, rec in enumerate(recordings)}

    def on_file_select(event):
        selected_idx = listbox.curselection()
        if not selected_idx:
            return
        filename = index_to_path[selected_idx[0]]
        show_file_actions(os.path.basename(filename))

    listbox.bind("<<ListboxSelect>>", on_file_select)

def show_file_actions(filename):
    from db import get_recording, update_transcript, update_analytics
    from tkinter import messagebox

    action_win = Toplevel(root)
    action_win.title(f"Transcript for {filename}")
    action_win.geometry("800x600")

    base_name = os.path.join(files_dir, filename)

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
        analytics = analyze.get_analytics_from_ai(new_text)
        update_analytics(file_path=base_name, new_analytics=analytics)
        messagebox.showinfo("Saved", "✅ Transcript has been successfully updated!")

    def save_analytics():
        new_analytics = text_box.get("1.0", tk.END).strip()
        update_analytics(file_path=base_name, new_analytics=new_analytics)
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

btn_start = tk.Button(root, text="Start Recording", command=start_recording)
btn_start.pack(padx=20, pady=10)

btn_stop = tk.Button(root, text="Stop Recording", command=stop_recording, state=tk.DISABLED)
btn_stop.pack(padx=20, pady=10)

btn_view_files = tk.Button(root, text="View Files", command=open_files_window)
btn_view_files.pack(padx=20, pady=10)

root.mainloop()