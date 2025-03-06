import shelve
from collections import Counter
from itertools import batched

from pygame import Color, Event, Surface, Rect
import pygame
import pygame_gui

from front.utils import paint
from config import (
    SAVES_BATCH_SIZE,
    LIGHT_MAGENTA_HEX,
    NICER_GREEN_HEX,
    NICER_YELLOW_HEX,
    LIGHT_ORANGE_HEX,
    NICER_RED_HEX,
    NICER_BLUE_HEX,
    LIGHT_BLUE_HEX,
    SAVES_FILE,
)
from src.misc.artifacts import ArtifactsHandler, StatsBoost


(
    LIGHT_MAGENTA,
    NICER_GREEN,
    LIGHT_ORANGE,
    NICER_RED,
    NICER_BLUE,
    NICER_YELLOW,
    LIGHT_BLUE,
) = map(
    Color,
    (
        LIGHT_MAGENTA_HEX,
        NICER_GREEN_HEX,
        LIGHT_ORANGE_HEX,
        NICER_RED_HEX,
        NICER_BLUE_HEX,
        NICER_YELLOW_HEX,
        LIGHT_BLUE_HEX,
    ),
)

PRETTY_MAGENTA = Color("#8663e6")
WHITE = Color("white")



class StatsWindow(pygame_gui.windows.UIMessageWindow):
    def __init__(self, manager: pygame_gui.UIManager, surface: Surface):
        rect = Rect(40, 40, 550, 800)
        rect.center = surface.get_rect().center

        with shelve.open(str(SAVES_FILE)) as saves:
            self.save_batches = list(batched(reversed(list(saves.items())), SAVES_BATCH_SIZE))
            self.current_batch = 0
            self.total_batches = len(self.save_batches)
            len_saves = len(saves)
        super().__init__(
            rect=rect,
            manager=manager,
            window_title=f'Stats ({len_saves} saves)',
            html_message=self.get_current_text(),
        )

        assert self.dismiss_button is not None
        self.dismiss_button.set_text("Close")
    
    def get_current_text(self) -> str:
        if not self.total_batches:
            return self.construct_html(())
        header = f'saves batch {self.current_batch + 1}/{self.total_batches}<br>'
        return header + self.construct_html(self.save_batches[self.current_batch])

    @staticmethod
    def construct_one_save_html(datetime_str: str, info: dict) -> str:
        TAB = "    "
        difficulty_field = (
            f" {paint('difficulty', PRETTY_MAGENTA)}: {paint(info['difficulty'], NICER_GREEN)};"
            if info["difficulty"] != 3
            else ""
        )
        died_because_str = (
            f"{paint('died because', PRETTY_MAGENTA)} {paint(info['reason_of_death'], LIGHT_ORANGE)}"
            if info["reason_of_death"]
            else paint("did not die", PRETTY_MAGENTA)
        )
        achievements_list = info["achievements"].achievements_pretty()
        achievements_str = (
            f'{paint('achievements', PRETTY_MAGENTA)}:\n{TAB*2}{paint(", ".join(achievements_list), NICER_BLUE)}'
            if achievements_list
            else ""
        )
        artifacts_handler: ArtifactsHandler = info["artifacts"]

        stats_boosts = [el.stats_boost for el in artifacts_handler.inactive_artifacts]
        total_stats_boots = sum(stats_boosts, StatsBoost())
        stats_boosts_counter = Counter(stats_boosts)
        stats_boosts_str = (
            f'stat boosts:\n{TAB*3}{paint(", ".join((f"{cnt} x {sb}" if cnt > 1 else str(sb)) for sb, cnt in stats_boosts_counter.most_common()), NICER_YELLOW)}\n{TAB*3}(total: {paint(str(total_stats_boots), NICER_YELLOW)})'
            if stats_boosts
            else ""
        )
        active_artifacts = [
            el.get_verbose_string() for el in artifacts_handler.iterate_active()
        ]
        active_artifacts_str = (
            f'active:\n{TAB*3}{paint(", ".join(active_artifacts), LIGHT_ORANGE)}'
            if active_artifacts
            else ""
        )

        stats_list_pairs: list[tuple[str, str]] = info["stats"].get_pretty_stats()
        stats_str = "\n        ".join(
            f"{paint(k, NICER_GREEN):<60} {paint(v, NICER_YELLOW):>5}"
            for k, v in stats_list_pairs
        )

        artifacts_str = (
            f'{paint('artifacts', PRETTY_MAGENTA)}:\n{TAB*2}{stats_boosts_str}\n{TAB*2}{active_artifacts_str}'
            if stats_boosts_str or active_artifacts_str
            else ""
        )

        DASHES = "-" * 10
        text = f"""<b>{DASHES} {paint('GAME', WHITE)} {paint(datetime_str.replace('/', '.'), LIGHT_BLUE)} (score={info.get('score', 0)}) {DASHES}</b>
    {paint('level', PRETTY_MAGENTA)}: {paint(info['level'], NICER_GREEN)};{difficulty_field} {paint('time', PRETTY_MAGENTA)}: {paint('{:.2f}'.format(info['time']), NICER_GREEN)} sec
    {paint('stats', PRETTY_MAGENTA)}:
        {stats_str}
    {achievements_str}
    {artifacts_str}
    {died_because_str}
    """
        return text

    def construct_html(self, saves: tuple[tuple[str, dict], ...]) -> str:
        if len(saves) == 0:
            return "No saves yet"
        texts = []
        for datetime_str, info in saves:
            texts.append(self.construct_one_save_html(datetime_str, info))
        return "\n\n".join(texts)

    def process_event(self, event: Event) -> bool:
        # space
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if not self.total_batches:
                    return False
                self.current_batch = (self.current_batch + 1) % self.total_batches
                assert self.text_block is not None
                self.text_block.set_text(self.get_current_text())
        return super().process_event(event)
