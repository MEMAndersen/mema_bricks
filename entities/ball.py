from dataclasses import dataclass
from typing import Sequence

import pygame as pg

from constants import DT_TOL, Dir, get_vector_dir

from . import Entity, HealthComponent, MovingEntity, Paddle, ScoreComponent, on_collision_components_list


def reflect_rotate(paddle: Paddle, x) -> float:
    PADDLE_REFLECT_MAX_ROTATE = 15  # degrees
    PADDLE_NEUTRAL_REFLECT_RATIO = 0.00

    p_width = paddle.rect.width
    p_width_neutral = p_width * PADDLE_NEUTRAL_REFLECT_RATIO
    p_width_linear = (p_width - p_width_neutral) / 2
    xr = x - paddle.rect.centerx

    # ax+b=angle
    a = PADDLE_REFLECT_MAX_ROTATE / p_width_linear
    if xr < -p_width_neutral / 2:
        a = a
        b = -a * (-p_width_neutral / 2)  # (+0)
    elif xr > +p_width_neutral / 2:
        a = a
        b = -a * (+p_width_neutral / 2)  # (+0)
    else:
        return 0

    return a * xr + b


@dataclass
class Ball(MovingEntity):
    speed: float = 400.0 * 1e-3  # pix/ms
    max_speed: float = 1000.0 * 1e-3  # pix/ms
    damage: int = 1

    def __post_init__(self) -> None:
        self.vel = self.vel.normalize() * self.speed

    @property
    def move_dir_x(self) -> Dir | None:
        if self.vel.x < 0:
            return Dir.LEFT
        if self.vel.x > 0:
            return Dir.RIGHT
        return Dir.STATIONARY

    @property
    def move_dir_y(self) -> Dir | None:
        if self.vel.y < 0:
            return Dir.UP
        if self.vel.y > 0:
            return Dir.DOWN
        return Dir.STATIONARY

    def move_and_collide(self, dt: float, others: Sequence[Entity]) -> None:
        dt_remain = dt
        while True:
            collisions = self.find_next_collisions(dt_remain, others)

            # If no collision happen move and return out
            if not collisions:
                self.move(dt_remain)
                return

            min_dt_to_collision = collisions[0][0]

            dt_used: float = 0
            for dt_to_collision, colliding_entity, collide_dir in collisions:
                # If collision happens within the tolerance of the minimum dt_to_collision calculate the collision
                if abs(dt_to_collision - min_dt_to_collision) <= DT_TOL:
                    self.move_and_collide_with(colliding_entity, dt_to_collision - dt_used, collide_dir)
                    dt_used = dt_to_collision
                else:  # list is sorted so break after the first time the condition is not true
                    continue
            dt_remain -= dt_used  # subtract only the used dt after all collisions

    def find_next_collisions(self, dt_remain: float, others: Sequence[Entity]) -> list[tuple[float, Entity, Dir]]:
        """Returns a list of tuples containing the possible collisions doing dt_remain. The list is sorted after the
        time to collision

        Args:
            dt_remain (float): Remaining time in seconds.
            others (list[Entity]): List of entities to possibly collide with.

        Returns:
            list[tuple[float, Entity, Dir]]: List of tuples containing the time for the collision, the entity that
            collides and the direction of the collision
        """

        moved_rect: pg.Rect = self.rect.copy().move(self.vel * dt_remain)
        potential_collisions: list[Entity] = [
            o for o in others if o.enabled_collision_sides and o.rect.colliderect(moved_rect)
        ]

        collisions: list[tuple[float, Entity, Dir]] = []

        # Find first collision along velocity vector
        for pc in potential_collisions:
            # collide left side of self with right side of other
            if self.move_dir_x == Dir.LEFT and Dir.RIGHT in pc.enabled_collision_sides:
                pc_dtx = abs((pc.rect.right - self.rect.left) / self.vel.x)
                pc_collide_dirx = Dir.LEFT
            # collide right side of self with left side of other
            elif self.move_dir_x == Dir.RIGHT and Dir.LEFT in pc.enabled_collision_sides:
                pc_dtx = abs((pc.rect.left - self.rect.right) / self.vel.x)
                pc_collide_dirx = Dir.RIGHT
            else:
                pc_dtx = float("inf")
                pc_collide_dirx = Dir.STATIONARY
            x_collision: tuple[float, Entity, Dir] = (pc_dtx, pc, pc_collide_dirx)

            # collide top side of self with bottom side of other
            if self.move_dir_y == Dir.UP and Dir.DOWN in pc.enabled_collision_sides:
                pc_dty: float = abs((self.rect.top - pc.rect.bottom) / self.vel.y)
                pc_collide_diry = Dir.TOP
            # collide bottom side of self with top side of other
            elif self.move_dir_y == Dir.DOWN and Dir.UP in pc.enabled_collision_sides:
                pc_dty: float = abs((self.rect.bottom - pc.rect.top) / self.vel.y)
                pc_collide_diry = Dir.BOTTOM
            else:
                pc_dty = float("inf")
                pc_collide_diry = Dir.STATIONARY
            y_collision: tuple[float, Entity, Dir] = (pc_dty, pc, pc_collide_diry)

            if pc_collide_dirx == Dir.STATIONARY and pc_collide_diry == Dir.STATIONARY:
                continue

            # Test if either is stationary / not turned on
            if pc_collide_diry == Dir.STATIONARY:
                if pc_dtx <= dt_remain:
                    collisions.append(x_collision)
                continue
            if pc_collide_dirx == Dir.STATIONARY:
                if pc_dty <= dt_remain:
                    collisions.append(y_collision)
                continue

            # Neither is stationary
            if abs(pc_dtx - pc_dty) < DT_TOL:
                # Collisions in x and y happen simultaneously)
                collisions.append(x_collision)
                collisions.append(y_collision)
            elif pc_dtx < pc_dty and pc_dtx <= dt_remain:
                collisions.append(x_collision)
            elif pc_dtx > pc_dty and pc_dty <= dt_remain:
                collisions.append(y_collision)

        return sorted(collisions, key=lambda x: x[0])

    def move_and_collide_with(self, colliding_entity, dt_to_collision, collide_dir) -> None:
        # Move
        self.move(dt_to_collision)

        if isinstance(colliding_entity, Paddle):
            self.reflect_on_paddle(collide_dir, colliding_entity)
        else:
            self.reflect(collide_dir)

        for component in [c for c in colliding_entity.components if type(c) in on_collision_components_list]:
            match component:
                case HealthComponent():
                    colliding_entity.to_be_deleted_flag = component.take_damage(self.damage)
                case ScoreComponent():
                    component.on_hit()

    def reflect(self, reflect_dir: Dir) -> None:
        reflect_normal = get_vector_dir(reflect_dir)

        # only reflect if velocity is opposite normal
        if self.vel.dot(reflect_normal) < 0:
            self.vel.reflect_ip(reflect_normal)

    def reflect_on_paddle(self, reflect_dir: Dir, paddle: Paddle) -> None:
        angle_change = reflect_rotate(paddle, self.rect.centerx)

        if reflect_dir == Dir.BOTTOM:
            reflect_normal = get_vector_dir(reflect_dir).rotate(angle_change)
        else:
            reflect_normal = get_vector_dir(reflect_dir)

        # only reflect if velocity is opposite normal
        if self.vel.dot(reflect_normal) < 0:
            self.vel.reflect_ip(reflect_normal)

        self.clamp_vel_angle()

    def clamp_vel_angle(self) -> None:
        MINIMUM_VEL_ANGLE = 60

        vel_angle = self.vel.angle_to(pg.Vector2(0, -1))

        if abs(vel_angle) >= 90:
            return

        if vel_angle < -MINIMUM_VEL_ANGLE:
            self.vel.rotate_ip((vel_angle + MINIMUM_VEL_ANGLE))
        elif vel_angle > MINIMUM_VEL_ANGLE:
            self.vel.rotate_ip((vel_angle - MINIMUM_VEL_ANGLE))
