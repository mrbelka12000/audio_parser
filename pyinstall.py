import PyInstaller.__main__

PyInstaller.__main__.run(
    [
        'main.py',
        '--name=AudioParser',
        '--icon=docs/audio_logo.icns',
        '--noconfirm',
        '--windowed',
        '--onefile',
    ]
)
