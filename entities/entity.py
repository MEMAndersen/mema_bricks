from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Sequence

import pygame as pg

from . import Component

from constants import (
    COLORS,
    DEBUG,
    GAME_FIELD_SURFACE,
    Dir,
)


@dataclass
class Entity(ABC):
    rect: pg.Rect
    color: pg.typing.ColorLike
    components: list[Component] = field(default_factory=lambda: [])
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

    def neighbor_left_line(self) -> tuple[pg.Vector2, pg.Vector2]:
        return (self.rect.topleft + pg.Vector2(-1, 0), self.rect.bottomleft + pg.Vector2(-1, 0))

    def neighbor_right_line(self) -> tuple[pg.Vector2, pg.Vector2]:
        return (self.rect.topright + pg.Vector2(1, 0), self.rect.bottomright + pg.Vector2(1, 0))

    def neighbor_top_line(self) -> tuple[pg.Vector2, pg.Vector2]:
        return (self.rect.topleft + pg.Vector2(0, -1), self.rect.topright + pg.Vector2(0, -1))

    def neighbor_bottom_line(self) -> tuple[pg.Vector2, pg.Vector2]:
        return (self.rect.bottomleft + pg.Vector2(0, 1), self.rect.bottomright + pg.Vector2(0, 1))

    def neighbor_is_neighbor(self, other) -> bool:
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
