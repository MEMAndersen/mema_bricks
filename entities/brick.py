from constants import Dir
from typing import Sequence
from . import Entity


from dataclasses import dataclass, field


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
