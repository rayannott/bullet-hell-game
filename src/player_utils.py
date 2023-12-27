from dataclasses import dataclass
from typing import Generator


@dataclass
class Stats:
    ENERGY_ORBS_COLLECTED: int = 0
    PROJECTILES_FIRED: int = 0
    ENEMIES_KILLED: int = 0
    ACCURATE_SHOTS_RICOCHET: int = 0
    BULLETS_CAUGHT: int = 0
    ACCURATE_SHOTS: int = 0
    ENEMIES_COLLIDED_WITH: int = 0
    ENERGY_ORBS_SPAWNED: int = 0
    CORPSES_LET_SPAWN: int = 0
    BULLET_SHIELDS_ACTIVATED: int = 0
    BULLET_SHIELD_BULLETS_BLOCKED: int = 0
    MINES_STEPPED_ON: int = 0
    MINES_PLANTED: int = 0
    DASHES_ACTIVATED: int = 0
    TIME_STOPS_ACTIVATED: int = 0
    DASHED_THROUGH_ENEMIES: int = 0
    BONUS_ORBS_COLLECTED: int = 0
    BLOCKS_LIFTED: int = 0

    DAMAGE_TAKEN: float = 0.
    DAMAGE_DEALT: float = 0.
    ENERGY_COLLECTED: float = 0.
    OIL_SPILL_TIME_SPENT: float = 0.

    def get_accuracy(self) -> float:
        return self.ACCURATE_SHOTS / self.PROJECTILES_FIRED if self.PROJECTILES_FIRED > 0 else 0.

    def get_as_dict(self) -> dict:
        return self.__dict__
    
    @staticmethod
    def _snakecase_to_title(snakecase: str) -> str:
        return ' '.join(snakecase.split('_')).title()
    
    def get_pretty_stats(self) -> list[tuple[str, str]]:
        return [(f'{self._snakecase_to_title(k)}', f'{str(v) if isinstance(v, int) else f"{v:.2f}"}') for k, v in self.__dict__.items() if v > 0]


@dataclass
class EffectFlags:
    """
    Flags for effects that can be applied to the player.
    """
    OIL_SPILL: bool = False

    def reset(self):
        self.OIL_SPILL = False


@dataclass
class Achievements:
    """
    Achievement flags.
    """
    REACH_LEVEL_5_WITH_NO_CORPSES: bool = False
    REACH_LEVEL_5_WITHOUT_TAKING_DAMAGE: bool = False
    REACH_LEVEL_5_WITH_100_PERCENT_ACCURACY: bool = False
    REACH_LEVEL_5_WITHOUT_COLLECTING_ENERGY_ORBS: bool = False
    GET_ALL_LEVEL_5_ACHIEVEMENTS_SIMULTANEOUSLY: bool = False
    REACH_LEVEL_10: bool = False
    RECEIVE_1000_DAMAGE: bool = False
    FIRE_200_PROJECTILES: bool = False
    KILL_100_ENEMIES: bool = False
    BLOCK_100_BULLETS: bool = False
    COLLECT_200_ENERGY_ORBS: bool = False
    COLLECT_ALL_ENERGY_ORBS_BY_LEVEL_2: bool = False
    COLLIDE_WITH_15_ENEMIES: bool = False
    DASH_THROUGH_10_ENEMIES: bool = False
    KILL_BOSS_WITH_RICOCHET: bool = False
    KILL_BOSS_WITHOUT_BULLETS: bool = False
    KILL_BOSS_USING_EXACTLY_7_BULLETS: bool = False
    KILL_BOSS_WITHIN_ONE_SECOND: bool = False

    def update(self, other: 'Achievements'):
        for k, v in other.__dict__.items():
            if v: setattr(self, k, v)

    @staticmethod
    def _snakecase_to_title(snakecase: str) -> str:
        return ' '.join(snakecase.split('_')).title()
    
    def items_pretty(self) -> Generator[tuple[str, bool], None, None]:
        for k, v in self.__dict__.items():
            yield (self._snakecase_to_title(k), v)
    
    def achievements_pretty(self) -> list[str]:
        return [k for k, v in self.items_pretty() if v]

    def all_achievements_pretty(self) -> list[str]:
        return [k for k in self.__dict__.keys()]
