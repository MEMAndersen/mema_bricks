from abc import ABC
from dataclasses import dataclass, field

import pygame as pg
from pygame.typing import ColorLike, Point

from constants import GAME_FIELD_SURFACE, SCREEN
import globals


@dataclass
class Component(ABC): ...


@dataclass
class ScoreComponent(Component):
    score_death: int
    score_hit: int

    def on_death(self) -> None:
        globals.score += self.score_death

    def on_hit(self) -> None:
        globals.score += self.score_hit


@dataclass
class HealthComponent(Component):
    health: int
    max_health: int

    def take_damage(self, damage: int):
        self.health -= damage

        if self.health <= 0:
            return True
        return False


@dataclass
class BallTrailComponent(Component):
    trail_length: int  # ms
    color: ColorLike

    coordinates: list[Point] = field(default_factory=lambda: [], init=False)
    cumulative_time: list[int] = field(default_factory=lambda: [], init=False)

    def add_segment(self, coord, dt) -> None:
        self.coordinates.append(coord)
        self.cumulative_time = [ct + dt for ct in self.cumulative_time]
        self.cumulative_time.append(dt)

    def update(self) -> None:
        self.coordinates = [c for c, ct in zip(self.coordinates, self.cumulative_time) if ct < self.trail_length]
        self.cumulative_time = [ct for ct in self.cumulative_time if ct < self.trail_length]

    def render(self) -> None:
        if len(self.coordinates) < 2:
            return
        pg.draw.aalines(GAME_FIELD_SURFACE, self.color, False, self.coordinates)


on_collision_components_list: list[type[Component]] = [
    HealthComponent,
    ScoreComponent,
]
on_delete_component_list: list[type[Component]] = [
    ScoreComponent,
]
on_move_component_list: list[type[Component]] = [
    BallTrailComponent,
]
on_update_component_list: list[type[Component]] = [
    BallTrailComponent,
]
on_render_component_list: list[type[Component]] = [
    BallTrailComponent,
]
