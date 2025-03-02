from dataclasses import dataclass, field
from constants import COLORS, EDGE_WIDTH, GAME_FIELD_HEIGHT, GAME_FIELD_RECT_TO_SCREEN, GAME_FIELD_WIDTH, SCREEN, Dir
from . import Entity


import pygame as pg


from abc import abstractmethod


@dataclass
class Edge(Entity):
    color: pg.typing.ColorLike = COLORS["WHITE"]
    render_flag: bool = False

    @abstractmethod
    def render_transform(self) -> dict[str, tuple[int, int]]: ...

    def render(self) -> None:
        # EDGES RENDER DIRECTLY TO SCREEN
        if self.render_flag:
            pg.draw.rect(SCREEN, self.color, self.rect.move_to(**self.render_transform()))


@dataclass
class LeftEdge(Edge):
    rect: pg.Rect = field(
        default_factory=lambda: pg.Rect((-EDGE_WIDTH, 0), (EDGE_WIDTH, GAME_FIELD_HEIGHT)), init=False
    )

    def __post_init__(self) -> None:
        self.enabled_collision_sides = set([Dir.RIGHT])

    def render_transform(self) -> dict[str, tuple[int, int]]:
        return {"bottomright": GAME_FIELD_RECT_TO_SCREEN.bottomleft}


@dataclass
class RightEdge(Edge):
    rect: pg.Rect = field(
        default_factory=lambda: pg.Rect((GAME_FIELD_WIDTH, 0), (EDGE_WIDTH, GAME_FIELD_HEIGHT)), init=False
    )

    def __post_init__(self) -> None:
        self.enabled_collision_sides = set([Dir.LEFT])

    def render_transform(self) -> dict[str, tuple[int, int]]:
        return {"bottomleft": GAME_FIELD_RECT_TO_SCREEN.bottomright}


@dataclass
class TopEdge(Edge):
    rect: pg.Rect = field(
        default_factory=lambda: pg.Rect((EDGE_WIDTH, -EDGE_WIDTH), (GAME_FIELD_WIDTH + 2 * EDGE_WIDTH, EDGE_WIDTH)),
        init=False,
    )

    def __post_init__(self) -> None:
        self.enabled_collision_sides = set([Dir.BOTTOM])

    def render_transform(self) -> dict[str, tuple[int, int]]:
        return {"midbottom": GAME_FIELD_RECT_TO_SCREEN.midtop}
