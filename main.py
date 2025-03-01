from sys import exit
from typing import Sequence

import pygame as pg

from constants import (
    COLORS,
    EDGE_WIDTH,
    FONT,
    FPS,
    GAME_FIELD_HEIGHT,
    GAME_FIELD_RECT_TO_SCREEN,
    GAME_FIELD_SURFACE,
    GAME_FIELD_WIDTH,
    PAUSE_OVERLAY,
    SCREEN,
    UI_TEXT_SIZE,
    States,
)
from entities import (
    Ball,
    Brick,
    Edge,
    Entity,
    LeftEdge,
    Paddle,
    RightEdge,
    TopEdge,
    update_enabled_collision_sides,
)


# pygame setup
pg.init()
CLOCK: pg.Clock = pg.time.Clock()


def show_fps_cps(fps: float) -> None:
    fps_text, _ = FONT.render(f"FPS: {int(fps)}", COLORS["YELLOW"], size=UI_TEXT_SIZE)
    SCREEN.blit(fps_text, fps_text.get_rect(topleft=(0, 0)))


class Game:
    def __init__(self) -> None:
        self.state: States = States.GAME_RUNNING
        self.score: int = 0

        # Create paddle
        self.paddle: Paddle = Paddle(
            rect=pg.Rect(
                (0, 0),
                pg.Vector2(100, 20),
            ).move_to(center=(GAME_FIELD_WIDTH / 2, GAME_FIELD_HEIGHT - 30)),
            vel=pg.Vector2(0, 0),
            color=COLORS["LIGHT_GREY"],
        )

        # Create ball
        self.ball: Ball = Ball(
            rect=pg.Rect(
                (0, 0),
                pg.Vector2(15, 15),
            ).move_to(midbottom=self.paddle.rect.midtop),
            vel=pg.Vector2(-1, -1),
            color=COLORS["WHITE"],
        )
        self.balls: list[Ball] = [self.ball]

        # Create bricks
        self.bricks: list[Brick] = []
        brick_width = 40
        brick_height = 20
        for i in range(int(800 / brick_width)):
            for j in range(int(500 / brick_height)):
                if j % 2 == 0:
                    continue
                self.bricks.append(
                    Brick(
                        pg.Rect((i * brick_width, j * brick_height), (brick_width, brick_height)),
                        color=COLORS["LIGHT_GREY"],
                    )
                )

        # Create edges
        self.edges: list[Edge] = [
            LeftEdge(),
            TopEdge(),
            RightEdge(),
        ]

        for brick in self.bricks:
            brick.update_neighbors(self.bricks)

        update_enabled_collision_sides(self.bricks, self.edges)

    def get_all_entities(self) -> Sequence[Entity]:
        return [self.paddle] + self.balls + self.bricks + self.edges

    def render_all_entities(self) -> None:
        for entity in self.get_all_entities():
            entity.render()

        SCREEN.blit(GAME_FIELD_SURFACE, GAME_FIELD_RECT_TO_SCREEN)

    def render_score(self) -> None:
        text, _ = FONT.render(f"score:{self.score:0>5}", COLORS["YELLOW"], size=UI_TEXT_SIZE)
        SCREEN.blit(text, text.get_rect(topleft=GAME_FIELD_RECT_TO_SCREEN.topright + pg.Vector2(EDGE_WIDTH + 10, 0)))

    def handle_pause_quit_restart(self, key, event_type) -> None:
        if event_type == pg.KEYDOWN:
            if key in (pg.K_q, pg.K_ESCAPE):
                self.state = States.EXITING
            elif key == pg.K_r:
                self.state = States.RESTART
            elif key == pg.K_p and self.state == States.GAME_PAUSED:
                self.state = States.GAME_RUNNING
            elif key == pg.K_p and self.state == States.GAME_RUNNING:
                self.state = States.GAME_PAUSED

    def game_loop_logic(self, dt: float) -> None:
        global score

        # Handle input
        for event in pg.event.get():
            match event.dict:
                case {"key": key} if event.type in [pg.KEYDOWN, pg.KEYUP]:
                    self.handle_pause_quit_restart(key, event.type)
                    self.paddle.handle_keyboard_input(key, event.type)

        # Do move and collide
        self.paddle.move_and_collide(dt, [])

        others = [self.paddle] + self.bricks + self.edges
        for ball in self.balls:
            ball.move_and_collide(dt, others)

        bricks_to_check: list[Brick] = []
        for brick in self.bricks:
            if brick.health <= 0:
                self.score += 5
                brick.to_be_deleted = True
                bricks_to_check.extend(brick.neighbors)

        update_enabled_collision_sides(bricks_to_check, self.edges)

        for entity in [e for e in self.bricks if e.to_be_deleted]:
            self.bricks.remove(entity)

    def game_loop_render(self) -> None:
        self.render_all_entities()
        self.render_score()

    def paused_loop_logic(self) -> None:
        # Handle input
        for event in pg.event.get():
            match event.dict:
                case {"key": key} if event.type in [pg.KEYDOWN, pg.KEYUP]:
                    self.handle_pause_quit_restart(key, event.type)

    def paused_loop_render(self) -> None:
        self.render_all_entities()
        self.render_score()
        SCREEN.blit(PAUSE_OVERLAY)

    def exiting(self) -> None:
        print("Exiting")
        exit(0)


def main():
    game = Game()
    dt: int = 0  # ms

    while True:
        if pg.event.peek(pg.QUIT):
            game.state = States.EXITING

        # Update loop
        match game.state:
            case States.MAIN_MENU_SCREEN:
                pass
            case States.GAME_RUNNING:
                game.game_loop_logic(dt)
            case States.GAME_PAUSED:
                game.paused_loop_logic()
            case States.GAME_OVER_SCREEN:
                pass
            case States.EXITING:
                game.exiting()
            case States.RESTART:
                game = Game()
                dt: int = 0
                continue

        # Render
        # Clear screen
        SCREEN.fill(COLORS["BLACK"])
        GAME_FIELD_SURFACE.fill(COLORS["DARK_GREY"])
        show_fps_cps(CLOCK.get_fps())

        match game.state:
            case States.MAIN_MENU_SCREEN:
                pass
            case States.GAME_RUNNING:
                game.game_loop_render()
            case States.GAME_PAUSED:
                game.paused_loop_render()
            case States.GAME_OVER_SCREEN:
                pass
            case States.EXITING:
                game.exiting()
            case States.RESTART:
                game = Game()
                dt: int = 0
                continue

        # Update the screen
        pg.display.flip()

        # Update the clock
        dt: int = CLOCK.tick(FPS)


if __name__ == "__main__":
    main()
