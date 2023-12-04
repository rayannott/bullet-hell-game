import pathlib


FRAMERATE = 60

SM = 5 # small margin
BM = 10 # big margin

QUIT_BUTTON_SIZE = 40, 40

# MenuScreen
MENU_BUTTONS_SIZE = 400, 100

# GameScreen
GAME_STATS_PANEL_SIZE = 210, 300
GAME_HEALTH_BAR_SIZE = 200, 50
GAME_ENERGY_BAR_SIZE = 200, 25

GAME_STATS_TEXTBOX_SIZE = 200, 200

ASSETS_DIR = pathlib.Path('assets').resolve()
SOUNDS_DIR = ASSETS_DIR / 'sounds'
SAVES_DIR = ASSETS_DIR / 'saves'
