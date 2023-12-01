import logging

import pygame

from screens import MenuScreen
from config import setup_logging
setup_logging('DEBUG')


def main():
    logging.debug('Starting the game')
    pygame.init()
    surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    menu_screen = MenuScreen(surface)
    menu_screen.run()


if __name__ == '__main__':
    main()
