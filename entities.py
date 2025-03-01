from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar, Sequence

import pygame as pg

from constants import (
    COLORS,
    DEBUG,
    DT_TOL,
    EDGE_WIDTH,
    GAME_FIELD_HEIGHT,
    GAME_FIELD_RECT_TO_SCREEN,
    GAME_FIELD_SURFACE,
    GAME_FIELD_WIDTH,
    SCREEN,
    Dir,
    get_vector_dir,
)


@dataclass
class Entity(ABC):
    rect: pg.Rect
    color: pg.typing.ColorLike
    enabled_collision_sides: set[Dir] = field(default_factory=lambda: set([Dir.LEFT, Dir.RIGHT, Dir.UP, Dir.DOWN]))
    to_be_deleted_flag: bool = False
    render_flag: bool = True

    def render(self) -> None:
        if self.render_flag:
            pg.draw.rect(GAME_FIELD_SURFACE, self.color, self.rect)

        if DEBUG:
            self.debug_render()

    def debug_render(self) -> None:
        # render collision sides
        if Dir.LEFT in self.enabled_collision_sides:
            pg.draw.line(GAME_FIELD_SURFACE, COLORS["DEBUG"], self.rect.topleft, self.rect.bottomleft)
        if Dir.RIGHT in self.enabled_collision_sides:
            pg.draw.line(GAME_FIELD_SURFACE, COLORS["DEBUG"], self.rect.topright, self.rect.bottomright)
        if Dir.TOP in self.enabled_collision_sides:
            pg.draw.line(GAME_FIELD_SURFACE, COLORS["DEBUG"], self.rect.topleft, self.rect.topright)
        if Dir.BOTTOM in self.enabled_collision_sides:
            pg.draw.line(GAME_FIELD_SURFACE, COLORS["DEBUG"], self.rect.bottomleft, self.rect.bottomright)

    def left_line(self) -> tuple[pg.Vector2, pg.Vector2]:
        test_rect = self.rect
        return (test_rect.topleft + pg.Vector2(-1, 1), test_rect.bottomleft + pg.Vector2(-1, -1))

    def right_line(self) -> tuple[pg.Vector2, pg.Vector2]:
        test_rect = self.rect
        return (test_rect.topright + pg.Vector2(1, 1), test_rect.bottomright + pg.Vector2(1, -1))

    def top_line(self) -> tuple[pg.Vector2, pg.Vector2]:
        test_rect = self.rect
        return (test_rect.topleft + pg.Vector2(1, -1), test_rect.topright + pg.Vector2(-1, -1))

    def bottom_line(self) -> tuple[pg.Vector2, pg.Vector2]:
        test_rect = self.rect
        return (test_rect.bottomleft + pg.Vector2(1, 1), test_rect.bottomright + pg.Vector2(-1, 1))

    def is_neighbor(self, other) -> bool:
        return self.rect.copy().inflate(4, 4).colliderect(other.rect)


@dataclass
class MovingEntity(Entity, ABC):
    speed: float = 0  # pix/ms
    max_speed: float = float("inf")  # pix/ms
    vel: pg.Vector2 = field(default_factory=lambda: pg.Vector2(0, 0))

    @abstractmethod
    def move_and_collide(self, dt: float, others: Sequence[Entity]) -> None:
        # Collide self with others
        ...

    def move(self, dt) -> None:
        self.vel.clamp_magnitude_ip(0, self.max_speed)
        self.rect.move_ip(self.vel * dt)


@dataclass
class Paddle(MovingEntity):
    speed: float = 300.0 * 1e-3  # pix/ms
    max_speed: float = float("inf")  # pix/ms
    enabled_collision_sides: set[Dir] = field(default_factory=lambda: set([Dir.LEFT, Dir.RIGHT, Dir.UP]))

    def handle_keyboard_input(self, key, event_type) -> None:
        if event_type == pg.KEYDOWN:
            if key in (pg.K_a, pg.K_LEFT):
                self.vel.x -= self.speed
            elif key in (pg.K_d, pg.K_RIGHT):
                self.vel.x += self.speed
        elif event_type == pg.KEYUP:
            if key in (pg.K_a, pg.K_LEFT):
                self.vel.x += self.speed
            elif key in (pg.K_d, pg.K_RIGHT):
                self.vel.x -= self.speed

    def move_and_collide(self, dt, others) -> None:
        self.move(dt)
        self.rect.clamp_ip(GAME_FIELD_SURFACE.get_rect())


class Edge(Entity):
    thickness: ClassVar[int] = EDGE_WIDTH
    color: pg.typing.ColorLike = COLORS["WHITE"]
    render_flag: bool = False

    @abstractmethod
    def render_transform(self) -> dict[str, tuple[int, int]]: ...

    def render(self) -> None:
        # EDGES RENDER DIRECTLY TO SCREEN
        if self.render_flag:
            pg.draw.rect(SCREEN, self.color, self.rect.move_to(**self.render_transform()))


class LeftEdge(Edge):
    enabled_collision_sides: set[Dir] = set([Dir.RIGHT])

    def __init__(self) -> None:
        self.rect = pg.Rect((-self.thickness, 0), (self.thickness, GAME_FIELD_HEIGHT))

    def render_transform(self) -> dict[str, tuple[int, int]]:
        return {"bottomright": GAME_FIELD_RECT_TO_SCREEN.bottomleft}


class RightEdge(Edge):
    enabled_collision_sides: set[Dir] = set([Dir.LEFT])

    def __init__(self):
        self.rect = pg.Rect((GAME_FIELD_WIDTH, 0), (self.thickness, GAME_FIELD_HEIGHT))

    def render_transform(self) -> dict[str, tuple[int, int]]:
        return {"bottomleft": GAME_FIELD_RECT_TO_SCREEN.bottomright}


class TopEdge(Edge):
    enabled_collision_sides: set[Dir] = set([Dir.BOTTOM])

    def __init__(self):
        self.rect = pg.Rect((self.thickness, -self.thickness), (GAME_FIELD_WIDTH + 2 * self.thickness, self.thickness))

    def render_transform(self) -> dict[str, tuple[int, int]]:
        return {"midbottom": GAME_FIELD_RECT_TO_SCREEN.midtop}


@dataclass
class Brick(Entity):
    health: int = 1
    neighbors: list["Brick"] = field(default_factory=lambda: list(), repr=False)

    def update_neighbors(self, others: list["Brick"]) -> None:
        self.neighbors = [o for o in others if self.is_neighbor(o)]


def update_enabled_collision_sides(bricks_to_check: Sequence[Brick], others: Sequence[Entity]):
    for brick in [b for b in bricks_to_check if not b.to_be_deleted_flag]:
        brick.enabled_collision_sides = set([Dir.LEFT, Dir.RIGHT, Dir.TOP, Dir.BOTTOM])

        possible_neighbors = [e for e in others if not e.to_be_deleted_flag] + [
            e for e in brick.neighbors if not e.to_be_deleted_flag
        ]

        for other in possible_neighbors:
            if other == brick:
                continue

            # TODO: Think about this when blocks can be staggered
            # if Dir.LEFT in brick.enabled_collision_sides and other.rect.clipline(brick.left_line()):
            #     brick.enabled_collision_sides.remove(Dir.LEFT)

            # if Dir.RIGHT in brick.enabled_collision_sides and other.rect.clipline(brick.right_line()):
            #     brick.enabled_collision_sides.remove(Dir.RIGHT)

            # if Dir.TOP in brick.enabled_collision_sides and other.rect.clipline(brick.top_line()):
            #     brick.enabled_collision_sides.remove(Dir.TOP)

            # if Dir.BOTTOM in brick.enabled_collision_sides and other.rect.clipline(brick.bottom_line()):
            #     brick.enabled_collision_sides.remove(Dir.BOTTOM)


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
            if hasattr(colliding_entity, "health"):
                colliding_entity.health -= self.damage

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

        print(f"{vel_angle=}")

        if abs(vel_angle) >= 90:
            return

        if vel_angle < -MINIMUM_VEL_ANGLE:
            self.vel.rotate_ip((vel_angle + MINIMUM_VEL_ANGLE))
            print(f"CLAMPED: {self.vel.angle_to(pg.Vector2(0, -1))}")
        elif vel_angle > MINIMUM_VEL_ANGLE:
            self.vel.rotate_ip((vel_angle - MINIMUM_VEL_ANGLE))
            print(f"CLAMPED: {self.vel.angle_to(pg.Vector2(0, -1))}")


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
