from pygame import Color, Surface, Rect
import pygame_gui

from front.utils import paint
from config import (LIGHT_MAGENTA_HEX, NICER_GREEN_HEX, LIGHT_ORANGE_HEX)

LIGHT_MAGENTA, NICER_GREEN, LIGHT_ORANGE = map(Color, (LIGHT_MAGENTA_HEX, NICER_GREEN_HEX, LIGHT_ORANGE_HEX))

# TODO !!!
TEXT = f'''<b>{paint(("Idea"), NICER_GREEN)}</b>


<b>{paint(("Mechanics and Controls"), NICER_GREEN)}</b>


<b>{paint(("Enemies and Bullets"), NICER_GREEN)}</b>
- <b> enemies </b>
- <b> bullets </b>


<b>{paint(("Artifacts"), NICER_GREEN)}</b>
There are two types of artifacts: <b>active</b> and <b>stat boosts</b>.
- <b> active </b>
- <b> stat boosts </b>


<b>{paint(("Other Entities"), NICER_GREEN)}</b>
- energy orbs
- oil spills
- mines
- bonus orbs
- corpses


<b>{paint(("Other"), NICER_GREEN)}</b>
- <b> Achievements </b>
There are many achievements to unlock in this game. The achievements are unlocked during the individual runs and are saved between the runs. You can see the list of all achievements in the main menu by pressing the `{paint("a", LIGHT_MAGENTA)}` key.

- <b> Stats </b>
'''


class RulesWindow(pygame_gui.windows.UIMessageWindow):
    def __init__(self, manager: pygame_gui.UIManager, surface: Surface):
        rect = Rect(40, 40, 600, 1000)
        super().__init__(
            rect=rect,
            manager=manager,
            window_title='Rules',
            html_message=TEXT
        )
