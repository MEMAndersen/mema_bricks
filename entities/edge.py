from constants import COLORS, EDGE_WIDTH, GAME_FIELD_HEIGHT, GAME_FIELD_RECT_TO_SCREEN, GAME_FIELD_WIDTH, SCREEN, Dir
from . import Entity


import pygame as pg


from abc import abstractmethod
from typing import ClassVar


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
