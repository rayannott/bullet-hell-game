import shelve

from pygame import Color, Surface, Rect
import pygame_gui
from config.paths import SAVES_DIR

from front.utils import paint
from config import (LIGHT_MAGENTA_HEX, NICER_GREEN_HEX, NICER_YELLOW_HEX,
    LIGHT_ORANGE_HEX, NICER_RED_HEX, NICER_BLUE_HEX, LIGHT_BLUE_HEX,
    SAVES_FILE,
)
from src.artifacts import ArtifactsHandler, StatsBoost


(LIGHT_MAGENTA, NICER_GREEN, LIGHT_ORANGE, 
NICER_RED, NICER_BLUE, NICER_YELLOW, LIGHT_BLUE) = map(Color, 
(LIGHT_MAGENTA_HEX, NICER_GREEN_HEX, LIGHT_ORANGE_HEX, 
NICER_RED_HEX, NICER_BLUE_HEX, NICER_YELLOW_HEX, LIGHT_BLUE_HEX))

PRETTY_MAGENTA = Color('#8663e6')
WHITE = Color('white')


class StatsWindow(pygame_gui.windows.UIMessageWindow):
    def __init__(self, manager: pygame_gui.UIManager, surface: Surface):
        rect = Rect(40, 40, 1000, 800)
        rect.center = surface.get_rect().center
        if not SAVES_DIR.exists():
            SAVES_DIR.mkdir(exist_ok=True, parents=True)
            with shelve.open(str(SAVES_FILE)) as saves:
                saves.clear()
        with shelve.open(str(SAVES_FILE)) as saves:
            text = self.construct_html(saves)

        super().__init__(
            rect=rect,
            manager=manager,
            window_title='Stats',
            html_message=text
        )
    
    def construct_one_save_html(self, datetime_str: str, info: dict) -> str:
        # TODO
        difficulty_field =  f"{paint('difficulty', PRETTY_MAGENTA)}: {paint(info['difficulty'], NICER_GREEN)};" if info['difficulty'] != 3 else ''
        died_because_str = f"{paint('died because', PRETTY_MAGENTA)} {paint(info['reason_of_death'], NICER_RED)}" if info['reason_of_death'] else paint('did not die', PRETTY_MAGENTA)
        achievements_list = info['achievements'].achievements_pretty()
        achievements_str = f'{paint(", ".join(achievements_list), NICER_BLUE)}' if achievements_list else 'none'
        artifacts_handler: ArtifactsHandler = info['artifacts']

        stats_boosts = [el.stats_boost for el in artifacts_handler.inactive_artifacts]
        total_stats_boots = sum(stats_boosts, StatsBoost())
        stats_boosts_str = f'{paint(", ".join(map(str, stats_boosts)), NICER_YELLOW)}' if stats_boosts else 'none'
        active_artifacts = [el.get_verbose_string() for el in artifacts_handler.iterate_active()]
        active_artifacts_str = f'{paint(", ".join(active_artifacts), LIGHT_ORANGE)}' if active_artifacts else 'none'

        stats_str = info['stats'].get_pretty_stats()


        text = f'''<b>--- {paint('GAME', WHITE)} {paint(datetime_str.replace('/', '.'), LIGHT_BLUE)} ---</b>
    {paint('level', PRETTY_MAGENTA)}: {paint(info['level'], NICER_GREEN)};{difficulty_field} {paint('time', PRETTY_MAGENTA)}: {paint('{:.2f}'.format(info['time']), NICER_GREEN)} sec
    {paint('stats', PRETTY_MAGENTA)}:
        {stats_str}
    {paint('achievements', PRETTY_MAGENTA)}:
        {achievements_str}
    {paint('artifacts', PRETTY_MAGENTA)}:
        stats:
            {stats_boosts_str}
            (total: {paint(str(total_stats_boots), NICER_YELLOW)})
        active:
            {active_artifacts_str}
    {died_because_str}
    '''
        return text
    
    def construct_html(self, saves: shelve.Shelf) -> str:
        if len(saves) == 0:
            return 'No saves yet'
        text = ''
        for datetime_str, info in reversed(list(saves.items())):
            text += self.construct_one_save_html(datetime_str, info) + '<br>'
        return text
