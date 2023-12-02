from pygame import Vector2, Color

from src import Entity, EntityType, ProjectileType, Timer
from config import (PROJECTILE_DEFAULT_SIZE, PROJECTILE_DEFAULT_DAMAGE,
                        PROJECTILE_DEFAULT_SPEED, PROJECTILE_DEFAULT_LIFETIME)


PROJECTILE_COLOR_MAP = {
    ProjectileType.PLAYER_BULLET: Color('yellow'),
    ProjectileType.NORMAL: Color('#d3dbc8'),
    ProjectileType.HOMING: Color('#aee665'),
    ProjectileType.EXPLOSIVE: Color('#598c15'),
}

# TODO: add a projectile type that does something 
# TODO  on a natural death (e.g. explosive, oil spill, etc.)
class Projectile(Entity):
    def __init__(self, 
            _pos: Vector2, 
            _vel: Vector2,
            _projectile_type: ProjectileType,
            _damage: float = PROJECTILE_DEFAULT_DAMAGE,
            _speed: float = PROJECTILE_DEFAULT_SPEED,
            _lifetime: float = PROJECTILE_DEFAULT_LIFETIME,
            _homing_target: Entity | None = None,
        ):
        super().__init__(
            _pos=_pos,
            _type=EntityType.PROJECTILE,
            _size=PROJECTILE_DEFAULT_SIZE,
            _speed=_speed,
            _vel=_vel,
            _homing_target=_homing_target,
        )
        self._projectile_type = _projectile_type
        self._damage = _damage
        self._lifetime = _lifetime
        self._color = PROJECTILE_COLOR_MAP[_projectile_type]
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
            _pos=_pos,
            _vel=_vel,
            _projectile_type=ProjectileType.EXPLOSIVE,
            _damage=_damage,
            _speed=_speed,
            _lifetime=_lifetime,
            _homing_target=_homing_target,
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
            self._entities_buffer.append(
                Projectile(
                    _pos=self._pos.copy() + direction * (self._size * 1.5),
                    _vel=direction,
                    _damage=self._damage,
                    _projectile_type=ProjectileType.NORMAL,
                    _speed=self._speed,
                    _lifetime=self._lifetime * 0.8,
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
            _pos=_pos,
            _vel=_vel,
            _projectile_type=ProjectileType.HOMING,
            _damage=_damage,
            _speed=_speed,
            _lifetime=_lifetime,
            _homing_target=_homing_target,
        )
        self._homing_target = _homing_target
        self._render_trail = True

    def update(self, time_delta: float):
        super().update(time_delta)
        if not self._is_alive: return
        self._life_timer.tick(time_delta)
        if not self._life_timer.running():
            self.kill()
