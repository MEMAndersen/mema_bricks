from abc import ABC
from dataclasses import dataclass
from enum import Enum, auto

from globals import score


@dataclass
class Component(ABC): ...


@dataclass
class ScoreComponent(Component):
    score_death: int
    score_hit: int

    def on_death(self) -> None:
        global score
        score += self.score_death

    def on_hit(self) -> None:
        global score
        score += self.score_hit


@dataclass
class HealthComponent(Component):
    health: int
    max_health: int

    def take_damage(self, damage: int):
        self.health -= damage
        print(self.health)

        if self.health <= 0:
            return True
        return False


on_collision_components_list: list[type[Component]] = [
    HealthComponent,
    ScoreComponent,
]
on_delete_component_list: list[type[Component]] = [
    ScoreComponent,
]
