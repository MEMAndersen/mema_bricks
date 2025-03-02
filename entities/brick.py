from abc import ABC
from dataclasses import dataclass, field
from typing import ClassVar, Sequence

import pygame as pg

from constants import GRID_DX, GRID_DY, Dir
from entities.components import ScoreComponent

from . import Entity, HealthComponent


@dataclass
class Brick(Entity, ABC):
    width: ClassVar[int] = 0
    height: ClassVar[int] = 0
    symbol: ClassVar[str] = "."
    neighbors: list["Brick"] = field(default_factory=lambda: list(), repr=False)

    def update_neighbors(self, others: list["Brick"]) -> None:
        self.neighbors = [o for o in others if self.neighbor_is_neighbor(o)]

    @classmethod
    def skip_cols(cls) -> int:
        return int(cls.width / GRID_DX) - 1


@dataclass
class BrickSquare(Brick):
    width: ClassVar[int] = GRID_DX
    height: ClassVar[int] = GRID_DY
    symbol: ClassVar[str] = "b"

    def __post_init__(self) -> None:
        self.components.append(HealthComponent(health=1, max_health=1))
        self.components.append(ScoreComponent(score_death=4, score_hit=1))


@dataclass
class BrickLong(Brick):
    width: ClassVar[int] = 2 * GRID_DX
    height: ClassVar[int] = GRID_DY
    symbol: ClassVar[str] = "B"

    def __post_init__(self) -> None:
        self.components.append(HealthComponent(health=1, max_health=1))
        self.components.append(ScoreComponent(score_death=8, score_hit=2))


bricks_dict: dict[str, type[Brick] | None] = {
    ".": None,
    "b": BrickSquare,
    "B": BrickLong,
}


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
            if Dir.LEFT in brick.enabled_collision_sides and (
                points := other.rect.clipline(brick.neighbor_left_line())
            ):
                p1, p2 = (pg.Vector2(points[0]), pg.Vector2(points[1]))
                if abs(p2.y - p1.y) == brick.rect.height - 1:
                    brick.enabled_collision_sides.remove(Dir.LEFT)

            if Dir.RIGHT in brick.enabled_collision_sides and (
                points := other.rect.clipline(brick.neighbor_right_line())
            ):
                p1, p2 = (pg.Vector2(points[0]), pg.Vector2(points[1]))
                if abs(p2.y - p1.y) == brick.rect.height - 1:
                    brick.enabled_collision_sides.remove(Dir.RIGHT)

            if Dir.TOP in brick.enabled_collision_sides and (points := other.rect.clipline(brick.neighbor_top_line())):
                p1, p2 = (pg.Vector2(points[0]), pg.Vector2(points[1]))
                if abs(p2.x - p1.x) == brick.rect.width - 1:
                    brick.enabled_collision_sides.remove(Dir.TOP)

            if Dir.BOTTOM in brick.enabled_collision_sides and (
                points := other.rect.clipline(brick.neighbor_bottom_line())
            ):
                p1, p2 = (pg.Vector2(points[0]), pg.Vector2(points[1]))
                if abs(p2.x - p1.x) == brick.rect.width - 1:
                    brick.enabled_collision_sides.remove(Dir.BOTTOM)
