import pygame as pg

from constants import (
    FONT,
    GAME_FIELD_HEIGHT,
    GAME_FIELD_RECT_TO_SCREEN,
    GAME_FIELD_SURFACE,
    GAME_FIELD_WIDTH,
    COLORS,
    GRID_DX,
    GRID_DY,
    ROW_COL_TEXT_SIZE,
    SCREEN,
    MAPS_PATH,
)
from entities.brick import Brick


class MapReadError(ValueError): ...


def load_lvl_txt_to_list(lvl_id: str) -> list[str]:
    lvl_txt_path = MAPS_PATH / lvl_id

    if not lvl_txt_path.exists():
        raise ValueError(f"No maps exists with id {lvl_id} in {MAPS_PATH}")

    lvl_list: list[str] = []

    with lvl_txt_path.open("r", encoding="utf8") as map_txt:
        # Ignore first line since it contains column ids
        map_txt.readline()

        # Ignore first two symbols of each line
        for line in map_txt.readlines():
            line = line.rstrip()
            if len(line) != 42:
                raise MapReadError("Wrong number of symbols in line of file {lvl_txt_path}.")

            lvl_list.append(line[2:])

    if len(lvl_list) != 39:
        raise MapReadError("Wrong number of lines in map file {lvl_txt_path}.")

    return lvl_list


def create_bricks_from_lvl_txt(lvl_id: str) -> list[Brick]:
    lvl_list = load_lvl_txt_to_list(lvl_id)

    bricks: list[Brick] = []

    for row, lvl_row in enumerate(lvl_list):
        skip_cols: int = 0
        for col, char in enumerate(lvl_row):
            if skip_cols:
                skip_cols -= 1
                continue

            match char:
                case ".":
                    continue
                case "B":
                    skip_cols = 1
                    bricks.append(
                        Brick(
                            rect=pg.rect.Rect((GRID_DX * col, GRID_DY * row), (40, 20)),
                            color=COLORS["LIGHT_GREY"],
                        ),
                    )

    return bricks


def render_grid(dx: int, dy: int) -> None:
    for v_line in range(1, int(GAME_FIELD_WIDTH / dx) + 2):
        pg.draw.line(GAME_FIELD_SURFACE, COLORS["LIGHT_GREY"], (dx * v_line, 0), (dx * v_line, GAME_FIELD_HEIGHT))

    for h_line in range(1, int(GAME_FIELD_HEIGHT / dy) + 2):
        pg.draw.line(GAME_FIELD_SURFACE, COLORS["LIGHT_GREY"], (0, h_line * dy), (GAME_FIELD_WIDTH, h_line * dy))


def render_row_col_ids(dx: int, dy: int) -> None:
    n_rows = int(GAME_FIELD_HEIGHT / dy)
    for row_num in range(n_rows + 1):
        text, _ = FONT.render(f"{row_num}", COLORS["YELLOW"], size=ROW_COL_TEXT_SIZE)
        SCREEN.blit(
            text,
            text.get_rect(
                midright=(
                    GAME_FIELD_RECT_TO_SCREEN.left,
                    GAME_FIELD_RECT_TO_SCREEN.top + dy * (n_rows - row_num) + dy / 2,
                )
            ),
        )

    n_cols = int(GAME_FIELD_WIDTH / dx)
    for col_num in range(n_cols):
        if col_num < 26:
            chr_number = 97 + col_num
        else:
            chr_number = 65 + (col_num - 26)

        text, _ = FONT.render(f"{chr(chr_number)}", COLORS["YELLOW"], size=ROW_COL_TEXT_SIZE)
        SCREEN.blit(
            text,
            text.get_rect(
                midbottom=(
                    GAME_FIELD_RECT_TO_SCREEN.left + dx * (col_num) + dx / 2,
                    GAME_FIELD_RECT_TO_SCREEN.top,
                )
            ),
        )


if __name__ == "__main__":
    lvl_txt = load_lvl_txt_to_list("lvl1.txt")
    print(lvl_txt)
