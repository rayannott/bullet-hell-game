import pathlib

ASSETS_DIR = pathlib.Path("assets").resolve()
SOUNDS_DIR = ASSETS_DIR / "sounds"
SAVES_DIR = ASSETS_DIR / "saves"
SETTINGS_FILE = ASSETS_DIR / "settings.json"
FONT_FILE = ASSETS_DIR / "cnr.otf"
SAVES_FILE = SAVES_DIR / "saves.shlv"
ACHIEVEMENTS_FILE = SAVES_DIR / "achievements.pckl"
