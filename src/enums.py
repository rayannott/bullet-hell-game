from enum import Enum, auto


class EntityType(Enum):
    """
    Enumeration of all entity types.
    """
    PLAYER = auto()
    PROJECTILE = auto()
    ENERGY_ORB = auto()
    ENEMY = auto()
    SPAWNER = auto()


class ProjectileType(Enum):
    """
    Enumeration of all projectile types.
    """
    NORMAL = auto()
    HOMING = auto()
    EXPLOSIVE = auto()
