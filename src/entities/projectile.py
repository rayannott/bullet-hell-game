import random
from pygame import Vector2, Color

from src.entities.entity import Entity
from src.utils.enums import EntityType, ProjectileType
from src.utils.utils import Interpolate2D
from config import (
    PROJECTILE_DEFAULT_SIZE,
    PROJECTILE_DEFAULT_DAMAGE,
    PROJECTILE_DEFAULT_SPEED,
    PROJECTILE_DEFAULT_LIFETIME,
)


PROJECTILE_COLOR_MAP = {
    ProjectileType.PLAYER_BULLET: Color("yellow"),
    ProjectileType.NORMAL: Color("#d3dbc8"),
    ProjectileType.HOMING: Color("#46c6e3"),
    ProjectileType.EXPLOSIVE: Color("#598c15"),
    ProjectileType.DEF_TRAJECTORY: Color("#e3b146"),
}

RED = Color("red")


class Projectile(Entity):
    def __init__(
        self,
        pos: Vector2,
        vel: Vector2,
        projectile_type: ProjectileType,
        damage: float = PROJECTILE_DEFAULT_DAMAGE,
        speed: float = PROJECTILE_DEFAULT_SPEED,
        lifetime: float = PROJECTILE_DEFAULT_LIFETIME,
        homing_target: Entity | None = None,
        turn_coefficient: float = 1.0,
        render_trail: bool = False,
        can_spawn_entities: bool = False,
    ):
        super().__init__(
            pos=pos,
            type=EntityType.PROJECTILE,
            size=PROJECTILE_DEFAULT_SIZE,
            speed=speed,
            vel=vel,
            homing_target=homing_target,
            render_trail=render_trail,
            turn_coefficient=turn_coefficient,
            can_spawn_entities=can_spawn_entities,
            lifetime=lifetime,
        )
        self.projectile_type = projectile_type
        self.damage = damage
        self.color = PROJECTILE_COLOR_MAP[projectile_type]
        self.ricochet_count = 0

    def update(self, time_delta: float):
        super().update(time_delta)
        if not self._is_alive:
            return

    def get_damage(self) -> float:
        """Return the damage scaled by the time alive and number of ricochets."""
        return (
            self.damage * (1 + 0.5 * self.i_has_lifetime.timer.get_percent_full() ** 2)
            + 10 * self.ricochet_count
        )

    def on_natural_death(self):
        pass


class ExplosiveProjectile(Projectile):
    def __init__(
        self,
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
            render_trail=True,
            can_spawn_entities=True,
        )
        self._original_color = self.color
        self.num_subprojectiles = num_subprojectiles
        self.homing_target = homing_target

    def on_natural_death(self):
        N = self.num_subprojectiles
        assert self.i_can_spawn_entities
        for i in range(N):
            direction = Vector2(1.0, 0.0).rotate(
                i * 360.0 / N + random.uniform(-10, 10)
            )
            self.i_can_spawn_entities.add(
                Projectile(
                    pos=self.pos.copy() + direction * (self.size * 1.5),
                    vel=direction,
                    damage=self.damage,
                    projectile_type=ProjectileType.NORMAL,
                    speed=self.speed,
                    lifetime=self.lifetime * 0.8,
                )
            )
    
    def update(self, time_delta: float):
        super().update(time_delta)
        if self.i_has_lifetime.timer.get_time_left() < 1.0:
            self.color = random.choice([RED, self._original_color])

class HomingProjectile(Projectile):
    def __init__(
        self,
        pos: Vector2,
        vel: Vector2,
        damage: float = PROJECTILE_DEFAULT_DAMAGE,
        speed: float = PROJECTILE_DEFAULT_SPEED,
        lifetime: float = PROJECTILE_DEFAULT_LIFETIME,
        homing_target: Entity | None = None,
        turn_coefficient: float = 1.0,
    ):
        super().__init__(
            pos=pos,
            vel=vel,
            projectile_type=ProjectileType.HOMING,
            damage=damage,
            speed=speed,
            lifetime=lifetime,
            homing_target=homing_target,
            turn_coefficient=turn_coefficient,
            render_trail=True,
        )


class DefinedTrajectoryProjectile(Projectile):
    """A projectile that follows
    a defined trajectory (e.g. a Bezier curve, an arc, ...)."""

    def __init__(
        self,
        points: list[Vector2],
        damage: float = PROJECTILE_DEFAULT_DAMAGE,
        lifetime: float = PROJECTILE_DEFAULT_LIFETIME,
        turn_coefficient: float = 1.0,
    ):
        self.traj = Interpolate2D(points)
        self.render_traj_points = [self.traj(t * 0.01) for t in range(101)]

        super().__init__(
            pos=points[0],
            vel=self.traj.derivative(0.0),
            projectile_type=ProjectileType.DEF_TRAJECTORY,
            damage=damage,
            speed=PROJECTILE_DEFAULT_SPEED,
            lifetime=lifetime,
            turn_coefficient=turn_coefficient,
        )

    def update(self, time_delta: float):
        if not self._is_alive:
            return
        super().update(time_delta)
        t = min(self.i_has_lifetime.timer.get_percent_full(), 1.0)
        self.pos = self.traj(t)
        self.vel = self.traj.derivative(t)
        self.speed = self.vel.magnitude()
