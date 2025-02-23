from sys import exit
import pygame
from enum import Enum, auto
from dataclasses import dataclass

# pygame setup
pygame.init()
CLOCK: pygame.Clock = pygame.time.Clock()

COLORS: dict[str : tuple[int, int, int]] = {
    "BLACK": (0, 0, 0),
    "WHITE": (255, 255, 255),
    "DARK_GREY": (25, 25, 25),
    "LIGHT_GREY": (155, 155, 155),
}

WIDTH: int = 640
HEIGHT: int = 480
SIZE: tuple[int, int] = (WIDTH, HEIGHT)
SCREEN = pygame.display.set_mode(SIZE)


class States(Enum):
    MAIN_MENU_SCREEN = auto()
    GAME_RUNNING = auto()
    GAME_PAUSED = auto()
    GAME_OVER_SCREEN = auto()
    EXITING = auto()


class Game:
    def __init__(self):
        self.state = States.GAME_RUNNING

    def handle_pause_quit(self, unicode):
        if unicode == "q":
            self.state = States.EXITING
        elif unicode == "p" and self.state == States.GAME_PAUSED:
            self.state = States.GAME_RUNNING
        elif unicode == "p" and self.state == States.GAME_RUNNING:
            self.state = States.GAME_PAUSED

    def game_loop(self):
        # Handle input
        for event in pygame.event.get():
            match event.dict:
                case {"unicode": unicode} if event.type == pygame.KEYDOWN:
                    self.handle_pause_quit(unicode)

        print("game_loop")

    def paused_loop(self):
        # Handle input
        for event in pygame.event.get():
            match event.dict:
                case {"unicode": unicode} if event.type == pygame.KEYDOWN:
                    self.handle_pause_quit(unicode)

        print("paused_loop")


def main():
    game = Game()

    while True:
        # Clear screen
        SCREEN.fill(COLORS["BLACK"])

        # Check if should exit
        if pygame.event.peek(pygame.QUIT):
            game.state = States.EXITING

        match game.state:
            case States.MAIN_MENU_SCREEN:
                pass
            case States.GAME_RUNNING:
                game.game_loop()
            case States.GAME_PAUSED:
                game.paused_loop()
            case States.GAME_OVER_SCREEN:
                pass
            case States.EXITING:
                print("Exiting")
                exit(1)

        # flip() the display to put your work on screen
        pygame.display.flip()
        CLOCK.tick(60)  # limits FPS to 60


if __name__ == "__main__":
    main()
