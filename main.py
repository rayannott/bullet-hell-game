import pygame

from front.menu_screen import MenuScreen


def main():
    pygame.init()
    surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    menu_screen = MenuScreen(surface)
    menu_screen.run()


def play_through_sound_effects():
    from front.sounds import play_sfx, SOUND_EFFECTS
    for k in SOUND_EFFECTS:
        play_sfx(k)
        print(k)
        input()


if __name__ == '__main__':
    main()
    # play_through_sound_effects()
