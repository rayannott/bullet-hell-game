import PyInstaller.__main__

PyInstaller.__main__.run([
    'main.py',
    '-i', 'icon.ico',
    '--onefile',
])
