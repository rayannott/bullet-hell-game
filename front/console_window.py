import datetime

import pygame_gui
import pygame

from front.game_screen import GameScreen


class ConsoleWindow(pygame_gui.windows.UIConsoleWindow):
    def __init__(self, manager: pygame_gui.UIManager, game_screen: GameScreen):
        rect = pygame.Rect(0, 0, 400, 400)
        super().__init__(rect, manager, 'Console')
        self.game_screen = game_screen
        self.starting_text = f'[{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}] Console opened'
        self.reset()
        self.AVAILABLE_COMMANDS = {
            'help': 'Shows this message',
            'clear': 'Clears the console',
            'exit': 'Exits the console',
            'settings': 'Shows the current settings',
        }
    
    def reset(self):
        self.clear_log()
        self.add_output_line_to_log(self.starting_text)

    def process_event(self, event: pygame.event.Event):
        text = self.command_entry.get_text()
        if super().process_event(event):
            text = text.strip()
            print(text)
            if text == 'clear':
                self.reset()
            elif text == 'exit':
                self.kill()
            elif text == 'help':
                self.add_output_line_to_log('Available commands:')
                for k, v in self.AVAILABLE_COMMANDS.items():
                    self.add_output_line_to_log(f'{k}: {v}')
            elif text == 'settings':
                self.add_output_line_to_log(str(self.game_screen.settings))       
            else:
                self.add_output_line_to_log(f'Unknown command: {text}. Type "help" for available commands.')
