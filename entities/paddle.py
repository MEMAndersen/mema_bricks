from constants import GAME_FIELD_SURFACE, PADDLE_MAX_SPEED, PADDLE_START_SPEED, Dir
from . import MovingEntity


import pygame as pg


from dataclasses import dataclass, field


@dataclass
class Paddle(MovingEntity):
    speed: float = PADDLE_START_SPEED  # pix/ms
    min_speed: float = PADDLE_MIN_SPEED  # pix/ms
    max_speed: float = PADDLE_MAX_SPEED  # pix/ms
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
