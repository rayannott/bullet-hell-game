import pygame

from front.menu_screen import MenuScreen


def main():
    pygame.init()
    surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    menu_screen = MenuScreen(surface)
    menu_screen.run()


if __name__ == '__main__':
    main()
