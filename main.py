from sys import exit
from typing import NoReturn, Sequence

import pygame as pg

import globals
from constants import (
    COLORS,
    FONT,
    FPS,
    GAME_FIELD_HEIGHT,
    GAME_FIELD_RECT_TO_SCREEN,
    GAME_FIELD_SURFACE,
    GAME_FIELD_WIDTH,
    PAUSE_OVERLAY,
    RENDER_GRID_FLAG,
    SCREEN,
    SHOW_FPS,
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
    ScoreComponent,
    TopEdge,
    on_delete_component_list,
    update_enabled_collision_sides,
)
from map import create_bricks_from_lvl_txt, render_grid, render_row_col_ids

globals.init_globals()


def show_fps_cps(fps: float) -> None:
    fps_text, _ = FONT.render(f"FPS: {int(fps)}", COLORS["YELLOW"], size=UI_TEXT_SIZE)
    SCREEN.blit(fps_text, fps_text.get_rect(topleft=(0, 0)))


class Game:
    def __init__(self) -> None:
        self.state: States = States.GAME_RUNNING

        globals.reset_score()

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
        self.bricks: list[Brick] = create_bricks_from_lvl_txt("lvl1.txt")

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
        # Reset variables
        bricks_to_check: list[Brick] = []

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

        for entity in [e for e in self.get_all_entities() if e.to_be_deleted_flag]:
            for component in [c for c in entity.components if type(c) in on_delete_component_list]:
                match component:
                    case ScoreComponent():
                        component.on_death()

            match entity:
                case Brick():
                    bricks_to_check.extend(entity.neighbors)
                    self.bricks.remove(entity)
                case Ball():
                    self.balls.remove(entity)
                    if len(self.balls) < 1:
                        # TODO: Reduce life:
                        ...

        update_enabled_collision_sides(bricks_to_check, self.edges)

    def game_loop_render(self) -> None:
        self.render_all_entities()
        globals.render_score()

    def paused_loop_logic(self) -> None:
        # Handle input
        for event in pg.event.get():
            match event.dict:
                case {"key": key} if event.type in [pg.KEYDOWN, pg.KEYUP]:
                    self.handle_pause_quit_restart(key, event.type)

    def paused_loop_render(self) -> None:
        self.render_all_entities()
        globals.render_score()
        SCREEN.blit(PAUSE_OVERLAY)

    def exiting(self) -> None:
        print("Exiting")
        exit(0)


def main() -> NoReturn:
    # pygame setup
    pg.init()
    CLOCK: pg.Clock = pg.time.Clock()

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

        if RENDER_GRID_FLAG:
            render_grid(20, 20)
            render_row_col_ids(20, 20)

        if SHOW_FPS:
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
