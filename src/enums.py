from enum import Enum, auto


class EntityType(Enum):
    """
    Enumeration of all entity types.
    """
    DUMMY = auto()
    OIL_SPILL = auto()
    CORPSE = auto()
    PLAYER = auto()
    PROJECTILE = auto()
    ENERGY_ORB = auto()
    ENEMY = auto()
    MINE = auto()
    CRATER = auto()


class EnemyType(Enum):
    """
    Enumeration of all enemy types.
    """
    BASIC = auto()
    FAST = auto()
    TANK = auto()
    ARTILLERY = auto()
    BOSS = auto()


class ProjectileType(Enum):
    """
    Enumeration of all projectile types.
    """
    PLAYER_BULLET = auto()
    NORMAL = auto()
    HOMING = auto()
    EXPLOSIVE = auto()


class ArtifactType(Enum):
    BULLET_SHIELD = auto()
    DASH = auto()
    BAIT = auto()
    ROTATING_BULLETS = auto()
    MINE_SPAWN = auto()
