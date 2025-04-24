import sounddevice as sd
import soundfile as sf
import tkinter as tk
import threading
import queue
import numpy as np
import time
import os
from tkinter import Toplevel, Listbox
import analyze
import assembly

samplerate = 44100
channels = 10  # record more to capture full mic + system range
q = queue.Queue()
recording = False
stream = None
frames = []
files_dir = "files/"

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
    if not os.path.exists(files_dir):
        os.makedirs(files_dir)

    base_name = os.path.join(files_dir, get_file_name())

    # Save full multi-channel audio
    full_path = base_name + ".wav"
    sf.write(full_path, audio_data, samplerate)

    print(f"[Saved] Full: {full_path}")

    time.sleep(2)

    transcript = assembly.get_transcript(full_path)

    print("Transcript done\n")

    print(analyze.get_analytics_from_ai(transcript))

def open_files_window():
    if not os.path.exists(files_dir):
        os.makedirs(files_dir)

    window = Toplevel(root)
    window.title("Files in 'files/' Directory")
    window.geometry("300x400")

    listbox = Listbox(window, width=40)
    listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    files = sorted(os.listdir(files_dir))
    for f in files:
        listbox.insert(tk.END, f)

    def on_file_select(event):
        selected_idx = listbox.curselection()
        if not selected_idx:
            return
        filename = listbox.get(selected_idx[0])
        show_file_actions(filename)

    listbox.bind("<<ListboxSelect>>", on_file_select)

def show_file_actions(filename):
    action_win = Toplevel(root)
    action_win.title(f"Actions for {filename}")
    action_win.geometry("300x150")

    label = tk.Label(action_win, text=f"Selected File:\n{filename}", pady=10)
    label.pack()

    btn_text = tk.Button(action_win, text="📝 Print Path", command=lambda: print(f"[Selected] {filename}"))
    btn_text.pack(pady=5)

    btn_analytics = tk.Button(action_win, text="📊 Dummy Analytics", command=lambda: print(f"[Analytics] {filename}"))
    btn_analytics.pack(pady=5)

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