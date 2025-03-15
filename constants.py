from enum import Enum, auto
from pathlib import Path
import pygame as pg
import pygame.freetype

# Debug flag
DEBUG: bool = True

# Time constants
FPS: int = 60  # frame per sec
DT_TOL: float = 0.01  # ms tolerance when considering multiple collisions at the same time
SHOW_FPS: bool = True

# Assets
ASSETS_PATH = Path(r"assets")
FONTS_PATH = ASSETS_PATH / "fonts"
MAPS_PATH = ASSETS_PATH / "maps"

# fonts constants
pygame.freetype.init()
FONT: pygame.freetype.Font = pygame.freetype.Font(FONTS_PATH / "PixelIntv-OPxd.ttf")
UI_TEXT_SIZE: int = 25
PAUSE_TEXT_SIZE: int = 50
ROW_COL_TEXT_SIZE: int = 10

# Colors
COLORS: dict[str, pg.typing.ColorLike] = {
    "BLACK": (0, 0, 0),
    "WHITE": (255, 255, 255),
    "DARK_GREY": (25, 25, 25),
    "LIGHT_GREY": (155, 155, 155),
    "PAUSE_OVERLAY": (0, 0, 0, 200),
    "DEBUG": (255, 0, 0),
    "YELLOW": (255, 255, 0),
}

# Screen and geometry
RENDER_GRID_FLAG: bool = True

EDGE_WIDTH = 20

SCREEN_WIDTH: int = 1248
SCREEN_HEIGHT: int = 800
SCREEN_SIZE: tuple[int, int] = (SCREEN_WIDTH, SCREEN_HEIGHT)
SCREEN: pg.Surface = pg.display.set_mode(SCREEN_SIZE, vsync=0)

GAME_FIELD_WIDTH: int = SCREEN_HEIGHT
GAME_FIELD_HEIGHT: int = SCREEN_HEIGHT - EDGE_WIDTH
GAME_FIELD_SIZE: tuple[int, int] = (GAME_FIELD_WIDTH, GAME_FIELD_HEIGHT)
GAME_FIELD_SURFACE: pg.Surface = pg.Surface(GAME_FIELD_SIZE)
GAME_FIELD_RECT_TO_SCREEN: pg.Rect = GAME_FIELD_SURFACE.get_rect().move_to(midbottom=SCREEN.get_rect().midbottom)


GRID_DX: int = 20
GRID_DY: int = 20


# Pause overlay
PAUSE_OVERLAY: pg.Surface = pg.Surface(SCREEN_SIZE, pg.SRCALPHA)
PAUSE_OVERLAY.fill(COLORS["PAUSE_OVERLAY"])
PAUSE_TEXT, _ = FONT.render("PAUSED", COLORS["LIGHT_GREY"], size=PAUSE_TEXT_SIZE)
PAUSE_OVERLAY.blit(PAUSE_TEXT, PAUSE_TEXT.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)))


class States(Enum):
    MAIN_MENU_SCREEN = auto()
    GAME_RUNNING = auto()
    GAME_PAUSED = auto()
    GAME_OVER_SCREEN = auto()
    EXITING = auto()
    RESTART = auto()


class Dir(Enum):
    LEFT = auto()
    RIGHT = auto()
    TOP = auto()
    UP = TOP  # Alias
    BOTTOM = auto()
    DOWN = BOTTOM  # Alias
    STATIONARY = auto()


def get_vector_dir(reflect_dir: Dir) -> pg.Vector2:
    match reflect_dir:
        case Dir.LEFT:
            return pg.Vector2(1.0, 0.0)
        case Dir.RIGHT:
            return pg.Vector2(-1.0, 0.0)
        case Dir.UP:
            return pg.Vector2(0.0, 1.0)
        case Dir.DOWN:
            return pg.Vector2(0.0, -1.0)
        case _:
            return pg.Vector2(0.0, 0.0)


## Paddle constants
PADDLE_START_SPEED = 300.0 * 1e-3  # pix/ms
PADDLE_MIN_SPEED = 150.0 * 1e-3  # pix/ms
PADDLE_MAX_SPEED = 9999.0 * 1e-3  # pix/ms

## Ball constants
BALL_START_SPEED = 500.0 * 1e-3  # pix/ms
BALL_MIN_SPEED = 400.0 * 1e-3  # pix/ms
BALL_MAX_SPEED = 1000.0 * 1e-3  # pix/ms
