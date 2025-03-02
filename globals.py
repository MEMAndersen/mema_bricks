# TODO fix score
import pygame as pg

from constants import COLORS, EDGE_WIDTH, FONT, GAME_FIELD_RECT_TO_SCREEN, SCREEN, UI_TEXT_SIZE


def init_globals() -> None:
    # ONLY RUN THIS ONCE!
    global score, num_lives
    score = 0
    num_lives = 0


def reset_score() -> None:
    global score
    score = 0


def reset_num_lives() -> None:
    global num_lives
    num_lives = 0


def render_score() -> None:
    global score
    text, _ = FONT.render(f"score:{score:0>5}", COLORS["YELLOW"], size=UI_TEXT_SIZE)
    SCREEN.blit(text, text.get_rect(topleft=GAME_FIELD_RECT_TO_SCREEN.topright + pg.Vector2(EDGE_WIDTH + 10, 0)))


def render_num_lives() -> None:
    global num_lives
    text, _ = FONT.render(f"Life: {score:.>6}", COLORS["YELLOW"], size=UI_TEXT_SIZE)
    SCREEN.blit(text, text.get_rect(topleft=GAME_FIELD_RECT_TO_SCREEN.topright + pg.Vector2(EDGE_WIDTH + 10, 30)))
