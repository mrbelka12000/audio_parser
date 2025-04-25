import os
from setuptools import setup

APP = ['main.py']

libsndfile_path = '/opt/homebrew/lib/libsndfile.dylib'
portaudio_path = '/opt/homebrew/lib/libportaudio.dylib'

for path in [portaudio_path, libsndfile_path]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing: {path}. Try installing with Homebrew.")

DATA_FILES = [
    ('', [portaudio_path, libsndfile_path])

]

OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'docs/audio_logo.icns',
    'plist': {
        'CFBundleName': 'AudioParser',
        'CFBundleIdentifier': 'com.bek.audio',
        'NSMicrophoneUsageDescription': 'Это приложение использует микрофон для распознавания речи.',
    },
    'packages': [
        'sounddevice',
        'soundfile',
        'numpy',
        'scipy',
        'speech_recognition',
        'openai',
        'assemblyai'
    ],
    'includes': ['tkinter'],
}

setup(
    app=APP,
    name='AudioParser',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
