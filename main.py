from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from sys import exit
from typing import ClassVar, Sequence

import pygame as pg

# Aliases
V2 = pg.Vector2

# pygame setup
pg.init()
CLOCK: pg.Clock = pg.time.Clock()
FPS = 60
DT_TOL = 1e-7  # seconds tolerance when considering multiple collisions at the same time

# fonts setup
pg.freetype.init()  # type: ignore
FONT: pg.freetype.Font = pg.freetype.Font(Path(r"assets\fonts\PixelIntv-OPxd.ttf"))  # type: ignore

COLORS: dict[str, pg.typing.ColorLike] = {
    "BLACK": (0, 0, 0),
    "WHITE": (255, 255, 255),
    "DARK_GREY": (25, 25, 25),
    "LIGHT_GREY": (155, 155, 155),
    "PAUSE_OVERLAY": (0, 0, 0, 125),
}

EDGE_WIDTH = 20

SCREEN_WIDTH: int = 1248
SCREEN_HEIGHT: int = 800
SCREEN_SIZE: tuple[int, int] = (SCREEN_WIDTH, SCREEN_HEIGHT)
SCREEN: pg.Surface = pg.display.set_mode(SCREEN_SIZE)

GAME_FIELD_WIDTH: int = SCREEN_HEIGHT
GAME_FIELD_HEIGHT: int = SCREEN_HEIGHT - EDGE_WIDTH
GAME_FIELD_SIZE: tuple[int, int] = (GAME_FIELD_WIDTH, GAME_FIELD_HEIGHT)
GAME_FIELD_SURFACE: pg.Surface = pg.Surface(GAME_FIELD_SIZE)
GAME_FIELD_RECT_TO_SCREEN: pg.Rect = GAME_FIELD_SURFACE.get_rect().move_to(midbottom=SCREEN.get_rect().midbottom)

# Pause overlay
PAUSE_OVERLAY: pg.Surface = pg.Surface(SCREEN_SIZE, pg.SRCALPHA)
PAUSE_OVERLAY.fill(COLORS["PAUSE_OVERLAY"])
PAUSE_TEXT, _ = FONT.render("PAUSED", COLORS["LIGHT_GREY"], size=50)
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


# Global variables
score = 0


@dataclass
class Entity(ABC):
    rect: pg.Rect
    color: pg.typing.ColorLike
    enabled_collision_sides: ClassVar[list[Dir]] = [Dir.LEFT, Dir.RIGHT, Dir.UP, Dir.DOWN]

    def render(self) -> None:
        pg.draw.rect(GAME_FIELD_SURFACE, self.color, self.rect)


@dataclass
class MovingEntity(Entity, ABC):
    vel: V2

    @abstractmethod
    def move_and_collide(self, dt: float, others: Sequence[Entity]) -> None:
        # Collide self with others
        ...

    def move(self, dt) -> None:
        self.rect.center += self.vel * dt


@dataclass
class Paddle(MovingEntity):
    speed: float = 300.0  # pixels/second
    enabled_collision_sides: ClassVar[list[Dir]] = [Dir.LEFT, Dir.RIGHT, Dir.UP]

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

    # def collide_edges(self) -> None:
    #     if self.rect.left < 0:
    #         self.rect.left = 0
    #     elif self.rect.right > GAME_FIELD_WIDTH:
    #         self.rect.right = GAME_FIELD_WIDTH

    #     if self.rect.top > GAME_FIELD_HEIGHT:
    #         self.rect.top = GAME_FIELD_HEIGHT

    def move_and_collide(self, dt, others) -> None:
        # For paddle only calculate collision with edges
        self.move(dt)
        self.rect.clamp_ip(GAME_FIELD_SURFACE.get_rect())


@dataclass
class Brick(Entity):
    health: int = 1


@dataclass
class BrickLayout:
    bricks: list[Brick]


# TODO fix edges
class Edge(Entity):
    thickness: ClassVar[int] = EDGE_WIDTH
    color: pg.typing.ColorLike = COLORS["WHITE"]

    @abstractmethod
    def render_transform(self) -> dict[str, tuple[int, int]]: ...

    def render(self):
        # EDGES RENDER DIRECTLY TO SCREEN
        pg.draw.rect(SCREEN, self.color, self.rect.move_to(**self.render_transform()))


class LeftEdge(Edge):
    enabled_collision_sides: ClassVar[list[Dir]] = [Dir.RIGHT]

    def __init__(self):
        self.rect = pg.Rect((-self.thickness, 0), (self.thickness, GAME_FIELD_HEIGHT))

    def render_transform(self) -> dict[str, tuple[int, int]]:
        return {"bottomright": GAME_FIELD_RECT_TO_SCREEN.bottomleft}


class RightEdge(Edge):
    enabled_collision_sides: ClassVar[list[Dir]] = [Dir.LEFT]

    def __init__(self):
        self.rect = pg.Rect((GAME_FIELD_WIDTH, 0), (self.thickness, GAME_FIELD_HEIGHT))

    def render_transform(self) -> dict[str, tuple[int, int]]:
        return {"bottomleft": GAME_FIELD_RECT_TO_SCREEN.bottomright}


class TopEdge(Edge):
    enabled_collision_sides: ClassVar[list[Dir]] = [Dir.BOTTOM]

    def __init__(self):
        self.rect = pg.Rect((self.thickness, -self.thickness), (GAME_FIELD_WIDTH + 2 * self.thickness, self.thickness))

    def render_transform(self) -> dict[str, tuple[int, int]]:
        return {"midbottom": GAME_FIELD_RECT_TO_SCREEN.midtop}


@dataclass
class Ball(MovingEntity):
    speed: float = 400.0  # pixels/second
    damage: int = 1

    def __post_init__(self):
        self.vel = self.vel * self.speed / self.vel.magnitude()

    @property
    def move_dir_x(self) -> Dir | None:
        if self.vel.x < 0:
            return Dir.LEFT
        if self.vel.x > 0:
            return Dir.RIGHT
        return Dir.STATIONARY

    @property
    def move_dir_y(self) -> Dir | None:
        if self.vel.y < 0:
            return Dir.UP
        if self.vel.y > 0:
            return Dir.DOWN
        return Dir.STATIONARY

    def move_and_collide(self, dt: float, others: Sequence[Entity]) -> None:
        dt_remain = dt
        while True:
            collisions = self.find_next_collisions(dt_remain, others)

            # If no collision happen move and return out
            if not collisions:
                self.move(dt_remain)
                return

            min_dt_to_collision = collisions[0][0]

            dt_used: float = 0
            for dt_to_collision, colliding_entity, collide_dir in collisions:
                # If collision happens within the tolerance of the minimum dt_to_collision calculate the collision
                if abs(dt_to_collision - min_dt_to_collision) <= DT_TOL:
                    self.move_and_collide_with(colliding_entity, dt_to_collision, collide_dir)
                    dt_used = dt_to_collision
                    print(f"{colliding_entity=}, {dt_to_collision=}, {collide_dir=}, {dt_used=}")
                    print()
                else:  # list is sorted so break after the first time the condition is not true
                    continue
            dt_remain -= dt_used

    def find_next_collisions(self, dt_remain: float, others: Sequence[Entity]) -> list[tuple[float, Entity, Dir]]:
        """Returns a list of tuples containing the possible collisions doing dt_remain. The list is sorted after the
        time to collision

        Args:
            dt_remain (float): Remaining time in seconds.
            others (list[Entity]): List of entities to possibly collide with.

        Returns:
            list[tuple[float, Entity, Dir]]: List of tuples containing the time for the collision, the entity that
            collides and the direction of the collision
        """

        moved_rect: pg.Rect = self.rect.copy().move(self.vel * dt_remain)
        potential_collisions: list[Entity] = [o for o in others if o.rect.colliderect(moved_rect)]

        collisions: list[tuple[float, Entity, Dir]] = []

        # Find first collision along velocity vector
        for pc in potential_collisions:
            # collide left side of self with right side of other
            if self.move_dir_x == Dir.LEFT and Dir.RIGHT in pc.enabled_collision_sides:
                pc_dtx = abs((pc.rect.right - self.rect.left) / self.vel.x)
                pc_collide_dirx = Dir.LEFT
            # collide right side of self with left side of other
            elif self.move_dir_x == Dir.RIGHT and Dir.LEFT in pc.enabled_collision_sides:
                pc_dtx = abs((pc.rect.left - self.rect.right) / self.vel.x)
                pc_collide_dirx = Dir.RIGHT
            else:
                pc_dtx = float("inf")
                pc_collide_dirx = Dir.STATIONARY
            x_collision: tuple[float, Entity, Dir] = (pc_dtx, pc, pc_collide_dirx)

            # collide top side of self with bottom side of other
            if self.move_dir_y == Dir.UP and Dir.DOWN in pc.enabled_collision_sides:
                pc_dty: float = abs((self.rect.top - pc.rect.bottom) / self.vel.y)
                pc_collide_diry = Dir.TOP
            # collide bottom side of self with top side of other
            elif self.move_dir_y == Dir.DOWN and Dir.UP in pc.enabled_collision_sides:
                pc_dty: float = abs((self.rect.bottom - pc.rect.top) / self.vel.y)
                pc_collide_diry = Dir.BOTTOM
            else:
                pc_dty = float("inf")
                pc_collide_diry = Dir.STATIONARY
            y_collision: tuple[float, Entity, Dir] = (pc_dty, pc, pc_collide_diry)

            if pc_collide_dirx == Dir.STATIONARY and pc_collide_diry == Dir.STATIONARY:
                continue

            # Test if either is stationary / not turned on
            if pc_collide_diry == Dir.STATIONARY:
                if pc_dtx <= dt_remain:
                    collisions.append(x_collision)
                continue
            if pc_collide_dirx == Dir.STATIONARY:
                if pc_dty <= dt_remain:
                    collisions.append(y_collision)
                continue

            # Neither is stationary the greatest is the one that limits the hit
            if abs(pc_dtx - pc_dty) < DT_TOL:
                # Collisions in x and y happen simultaneously)
                collisions.append(x_collision)
                collisions.append(y_collision)
            elif (pc_dtx < pc_dty or pc_collide_dirx == Dir.STATIONARY) and pc_dty <= dt_remain:
                collisions.append((pc_dty, pc, pc_collide_diry))
            elif (pc_dtx > pc_dty or pc_collide_diry == Dir.STATIONARY) and pc_dtx <= dt_remain:
                collisions.append((pc_dtx, pc, pc_collide_dirx))

        return sorted(collisions, key=lambda x: x[0])

    def move_and_collide_with(self, colliding_entity, dt_to_collision, collide_dir):
        # Move
        self.move(dt_to_collision)
        self.reflect(collide_dir)

        if hasattr(colliding_entity, "health"):
            colliding_entity.health -= self.damage

    def reflect(self, reflect_dir: Dir) -> None:
        match reflect_dir:
            case Dir.LEFT:
                reflect_normal = (1.0, 0.0)
            case Dir.RIGHT:
                reflect_normal = (-1.0, 0.0)
            case Dir.UP:
                reflect_normal = (0.0, 1.0)
            case Dir.DOWN:
                reflect_normal = (0.0, -1.0)
            case _:
                return

        # only reflect if velocity is opposite normal
        if self.vel.dot(reflect_normal) < 0:
            self.vel.reflect_ip(reflect_normal)


class Game:
    def __init__(self) -> None:
        self.state: States = States.GAME_RUNNING

        # Create paddle
        self.paddle: Paddle = Paddle(
            rect=pg.Rect(
                (0, 0),
                V2(800, 20),
            ).move_to(center=(GAME_FIELD_WIDTH / 2, GAME_FIELD_HEIGHT - 30)),
            vel=V2(0, 0),
            color=COLORS["LIGHT_GREY"],
        )

        # Create ball
        self.ball: Ball = Ball(
            rect=pg.Rect(
                (0, 0),
                V2(15, 15),
            ).move_to(midbottom=self.paddle.rect.midtop),
            vel=V2(-1, -0.1),
            color=COLORS["WHITE"],
        )
        self.balls: list[Ball] = [self.ball]

        # Create bricks
        self.bricks: list[Brick] = []
        brick_width = 40
        brick_height = 20
        for i in range(int(800 / brick_width)):
            for j in range(int(500 / brick_height)):
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

        # Reset score
        global score
        score = 0

    def get_all_entities(self) -> list:
        return [self.paddle] + self.balls + self.bricks + self.edges

    def render_all_entities(self) -> None:
        for entity in self.get_all_entities():
            entity.render()

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

    def game_loop(self, dt: float) -> None:
        global score

        # Handle input
        for event in pg.event.get():
            match event.dict:
                case {"key": key} if event.type in [pg.KEYDOWN, pg.KEYUP]:
                    self.handle_pause_quit_restart(key, event.type)
                    self.paddle.handle_keyboard_input(key, event.type)

        # Do move and collide
        self.paddle.move_and_collide(dt, self.edges)

        others = [self.paddle] + self.bricks + self.edges
        for ball in self.balls:
            ball.move_and_collide(dt, others)

        for brick in self.bricks:
            if brick.health <= 0:
                score += 5
                print(f"score: {score}")
                self.bricks.remove(brick)

        # Render
        self.render_all_entities()
        SCREEN.blit(GAME_FIELD_SURFACE, GAME_FIELD_RECT_TO_SCREEN)

    def paused_loop(self):
        # Handle input
        for event in pg.event.get():
            match event.dict:
                case {"key": key} if event.type in [pg.KEYDOWN, pg.KEYUP]:
                    self.handle_pause_quit_restart(key, event.type)

        # Render
        self.render_all_entities()
        SCREEN.blit(PAUSE_OVERLAY)

    def exiting(self) -> None:
        print("Exiting")
        exit(0)


def main():
    game = Game()
    dt: float = 0

    while True:
        # Clear screen
        SCREEN.fill(COLORS["BLACK"])
        GAME_FIELD_SURFACE.fill(COLORS["DARK_GREY"])

        if pg.event.peek(pg.QUIT):
            game.state = States.EXITING

        match game.state:
            case States.MAIN_MENU_SCREEN:
                pass
            case States.GAME_RUNNING:
                game.game_loop(dt)
            case States.GAME_PAUSED:
                game.paused_loop()
            case States.GAME_OVER_SCREEN:
                pass
            case States.EXITING:
                game.exiting()
            case States.RESTART:
                game = Game()
                dt: float = 0
                continue

        # Update the screen
        pg.display.flip()
        dt = CLOCK.tick(FPS) * 1e-3


if __name__ == "__main__":
    main()
