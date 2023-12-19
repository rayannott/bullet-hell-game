import shelve

from pygame import Color, Surface, Rect
import pygame_gui

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


class StatsWindow(pygame_gui.windows.UIMessageWindow):
    def __init__(self, manager: pygame_gui.UIManager, surface: Surface):
        rect = Rect(40, 40, 1000, 800)
        rect.center = surface.get_rect().center
        with shelve.open(str(SAVES_FILE)) as saves:
            print(saves, *saves.items())
            text = self.construct_html(saves)

        super().__init__(
            rect=rect,
            manager=manager,
            window_title='Stats',
            html_message=text
        )
    
    def construct_one_save_html(self, datetime_str: str, info: dict) -> str:
        # TODO
        difficulty_field =  f"difficulty: {paint(info['difficulty'], NICER_GREEN)};" if info['difficulty'] != 3 else ''
        died_because_str = f"died because {paint(info['reason_of_death'], NICER_RED)}" if info['reason_of_death'] else 'did not die'
        achievements_list = info['achievements'].achievements_pretty()
        achievements_str = f'  {paint("- " + "\n      - ".join(achievements_list), NICER_BLUE)}' if achievements_list else '    none'
        artifacts_handler: ArtifactsHandler = info['artifacts']

        stats_boosts = [el.stats_boost for el in artifacts_handler.inactive_artifacts]
        total_stats_boots = sum(stats_boosts, StatsBoost())
        stats_boosts_str = f'  {paint("- " + "\n          - ".join(map(str, stats_boosts)), NICER_YELLOW)}' if stats_boosts else '    none'
        active_artifacts = [el.get_verbose_string() for el in artifacts_handler.iterate_active()]
        active_artifacts_str = f'  {paint("- " + "\n          - ".join(active_artifacts), LIGHT_ORANGE)}' if active_artifacts else '    none'


        text = f'''--- GAME {paint(datetime_str.replace('/', '.'), LIGHT_BLUE)} ---
    level: {paint(info['level'], NICER_GREEN)};{difficulty_field} time: {paint('{:.2f}'.format(info['time']), NICER_GREEN)}
    {died_because_str}
    stats:
    ...
    achievements:
    {achievements_str}
    artifacts:
        stats: 
        {stats_boosts_str}
        (total: {paint(str(total_stats_boots), NICER_YELLOW)})
        active:
        {active_artifacts_str}
    '''
        return text
    
    def construct_html(self, saves: shelve.Shelf) -> str:
        if len(saves) == 0:
            return 'No saves yet'
        text = ''
        for datetime_str, info in reversed(list(saves.items())):
            text += self.construct_one_save_html(datetime_str, info) + '<br>'
        return text
