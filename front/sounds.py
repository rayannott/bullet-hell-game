from pygame import mixer

from config import SOUNDS_DIR

mixer.init()

SFX_DIR = SOUNDS_DIR / 'sfx'
MUSIC_DIR = SOUNDS_DIR / 'music'


SOUND_EFFECTS = {file.stem: mixer.Sound(file)
    for file in SFX_DIR.iterdir() if file.suffix == '.wav'}


def play_sfx(name: str):
    SOUND_EFFECTS[name].play()
