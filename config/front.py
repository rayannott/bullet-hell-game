import pathlib


FRAMERATE = 60

SM = 5 # small margin
BM = 10 # big margin

QUIT_BUTTON_SIZE = 40, 40

# MenuScreen
MENU_BUTTONS_SIZE = 400, 100
CONSOLE_WINDOW_SIZE = 600, 800

# GameScreen
GAME_STATS_PANEL_SIZE = 210, 90
GAME_HEALTH_BAR_SIZE = 200, 50
GAME_ENERGY_BAR_SIZE = 200, 30

GAME_STATS_TEXTBOX_SIZE = 200, 200
GAME_DEBUG_RECT_SIZE = 220, 80

ASSETS_DIR = pathlib.Path('assets').resolve()
SOUNDS_DIR = ASSETS_DIR / 'sounds'
SAVES_DIR = ASSETS_DIR / 'saves'
SETTINGS_FILE = ASSETS_DIR / 'settings.json'
FONT_FILE = ASSETS_DIR / 'cnr.otf'
