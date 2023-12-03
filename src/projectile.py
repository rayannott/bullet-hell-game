from pygame import Vector2, Color

from src.entity import Entity
from src.enums import EntityType, ProjectileType
from src.utils import Timer
from config import (PROJECTILE_DEFAULT_SIZE, PROJECTILE_DEFAULT_DAMAGE,
                        PROJECTILE_DEFAULT_SPEED, PROJECTILE_DEFAULT_LIFETIME)


PROJECTILE_COLOR_MAP = {
    ProjectileType.PLAYER_BULLET: Color('yellow'),
    ProjectileType.NORMAL: Color('#d3dbc8'),
    ProjectileType.HOMING: Color('#46c6e3'),
    ProjectileType.EXPLOSIVE: Color('#598c15'),
}


class Projectile(Entity):
    def __init__(self, 
            pos: Vector2, 
            vel: Vector2,
            projectile_type: ProjectileType,
            damage: float = PROJECTILE_DEFAULT_DAMAGE,
            speed: float = PROJECTILE_DEFAULT_SPEED,
            lifetime: float = PROJECTILE_DEFAULT_LIFETIME,
            homing_target: Entity | None = None,
        ):
        super().__init__(
            pos=pos,
            type=EntityType.PROJECTILE,
            size=PROJECTILE_DEFAULT_SIZE,
            speed=speed,
            vel=vel,
            homing_target=homing_target,
        )
        self._projectile_type = projectile_type
        self._damage = damage
        self._lifetime = lifetime
        self.color = PROJECTILE_COLOR_MAP[projectile_type]
        self._ricochet_count = 0
        self._life_timer = Timer(max_time=self._lifetime)

    def update(self, time_delta: float):
        super().update(time_delta)
        if not self._is_alive: return
        self._life_timer.tick(time_delta)
        if not self._life_timer.running():
            self.kill()


class ExplosiveProjectile(Projectile):
    def __init__(self, 
            _pos: Vector2,
            _vel: Vector2,
            _num_subprojectiles: int = 6,
            _damage: float = PROJECTILE_DEFAULT_DAMAGE,
            _speed: float = PROJECTILE_DEFAULT_SPEED * 0.8,
            _lifetime: float = PROJECTILE_DEFAULT_LIFETIME,
            _homing_target: Entity | None = None,
        ):
        super().__init__(
            pos=_pos,
            vel=_vel,
            projectile_type=ProjectileType.EXPLOSIVE,
            damage=_damage,
            speed=_speed,
            lifetime=_lifetime,
            homing_target=_homing_target,
        )
        self._num_subprojectiles = _num_subprojectiles
        self._can_spawn_entities = True
        self._homing_target = _homing_target
        self._render_trail = False

    def update(self, time_delta: float):
        super().update(time_delta)
        if not self._is_alive: return
        self._life_timer.tick(time_delta)
        if not self._life_timer.running():
            self.kill()
            self.on_natural_death()
    
    def on_natural_death(self):
        N = self._num_subprojectiles
        for i in range(N):
            direction = Vector2(1., 0.).rotate(i * 360. / N)
            self.entities_buffer.append(
                Projectile(
                    pos=self.pos.copy() + direction * (self.size * 1.5),
                    vel=direction,
                    damage=self._damage,
                    projectile_type=ProjectileType.NORMAL,
                    speed=self.speed,
                    lifetime=self._lifetime * 0.8,
                )
            )


class HomingProjectile(Projectile):
    def __init__(self, 
            _pos: Vector2, 
            _vel: Vector2,
            _damage: float = PROJECTILE_DEFAULT_DAMAGE,
            _speed: float = PROJECTILE_DEFAULT_SPEED,
            _lifetime: float = PROJECTILE_DEFAULT_LIFETIME,
            _homing_target: Entity | None = None,
        ):
        super().__init__(
            pos=_pos,
            vel=_vel,
            projectile_type=ProjectileType.HOMING,
            damage=_damage,
            speed=_speed,
            lifetime=_lifetime,
            homing_target=_homing_target,
        )
        self._homing_target = _homing_target
        self._render_trail = True

    def update(self, time_delta: float):
        super().update(time_delta)
        if not self._is_alive: return
        self._life_timer.tick(time_delta)
        if not self._life_timer.running():
            self.kill()


class DefinedTrajectoryProjectile(Projectile):
    """A projectile that follows 
    a defined trajectory (e.g. a Bezier curve, an arc, ...)."""
    # TODO: implement this
