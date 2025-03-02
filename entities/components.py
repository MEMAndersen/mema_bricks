from abc import ABC
from dataclasses import dataclass

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


on_collision_components_list: list[type[Component]] = [
    HealthComponent,
    ScoreComponent,
]
on_delete_component_list: list[type[Component]] = [
    ScoreComponent,
]
