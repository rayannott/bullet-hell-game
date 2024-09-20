import random
from pygame import mixer

from config import SOUNDS_DIR

mixer.init()

SFX_DIR = SOUNDS_DIR / "sfx"
MUSIC_DIR = SOUNDS_DIR / "music"


SOUND_EFFECTS = {
    file.stem: mixer.Sound(file) for file in SFX_DIR.iterdir() if file.suffix == ".wav"
}

BG_MUSIC_FILES = [file for file in MUSIC_DIR.iterdir() if file.suffix == ".mp3"]


def play_sfx(name: str):
    SOUND_EFFECTS[name].play()


def play_bg_music():
    bg_track = random.choice(BG_MUSIC_FILES)
    mixer.music.load(bg_track)
    mixer.music.play(-1)


def set_sfx_volume(volume: float):
    for sound in SOUND_EFFECTS.values():
        sound.set_volume(volume)


def set_bg_music_vol(volume: float):
    mixer.music.set_volume(volume)
