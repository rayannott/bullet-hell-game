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
        self.projectile_type = projectile_type
        self.damage = damage
        self.lifetime = lifetime
        self.color = PROJECTILE_COLOR_MAP[projectile_type]
        self.ricochet_count = 0
        self.life_timer = Timer(max_time=self.lifetime)

    def update(self, time_delta: float):
        super().update(time_delta)
        if not self._is_alive: return
        self.life_timer.tick(time_delta)
        if not self.life_timer.running():
            self.kill()


class ExplosiveProjectile(Projectile):
    def __init__(self, 
            pos: Vector2,
            vel: Vector2,
            num_subprojectiles: int = 6,
            damage: float = PROJECTILE_DEFAULT_DAMAGE,
            speed: float = PROJECTILE_DEFAULT_SPEED * 0.8,
            lifetime: float = PROJECTILE_DEFAULT_LIFETIME,
            homing_target: Entity | None = None,
        ):
        super().__init__(
            pos=pos,
            vel=vel,
            projectile_type=ProjectileType.EXPLOSIVE,
            damage=damage,
            speed=speed,
            lifetime=lifetime,
            homing_target=homing_target,
        )
        self.num_subprojectiles = num_subprojectiles
        self.can_spawn_entities = True
        self.homing_target = homing_target
        self.render_trail = False

    def update(self, time_delta: float):
        super().update(time_delta)
        if not self._is_alive: return
        self.life_timer.tick(time_delta)
        if not self.life_timer.running():
            self.kill()
            self.on_natural_death()
    
    def on_natural_death(self):
        N = self.num_subprojectiles
        for i in range(N):
            direction = Vector2(1., 0.).rotate(i * 360. / N)
            self.entities_buffer.append(
                Projectile(
                    pos=self.pos.copy() + direction * (self.size * 1.5),
                    vel=direction,
                    damage=self.damage,
                    projectile_type=ProjectileType.NORMAL,
                    speed=self.speed,
                    lifetime=self.lifetime * 0.8,
                )
            )


class HomingProjectile(Projectile):
    def __init__(self, 
            pos: Vector2, 
            vel: Vector2,
            damage: float = PROJECTILE_DEFAULT_DAMAGE,
            speed: float = PROJECTILE_DEFAULT_SPEED,
            lifetime: float = PROJECTILE_DEFAULT_LIFETIME,
            homing_target: Entity | None = None,
        ):
        super().__init__(
            pos=pos,
            vel=vel,
            projectile_type=ProjectileType.HOMING,
            damage=damage,
            speed=speed,
            lifetime=lifetime,
            homing_target=homing_target,
        )
        self.homing_target = homing_target
        self.render_trail = True

    def update(self, time_delta: float):
        super().update(time_delta)
        if not self._is_alive: return
        self.life_timer.tick(time_delta)
        if not self.life_timer.running():
            self.kill()


class DefinedTrajectoryProjectile(Projectile):
    """A projectile that follows 
    a defined trajectory (e.g. a Bezier curve, an arc, ...)."""
    # TODO: implement this
