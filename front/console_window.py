import datetime

import pygame_gui
import pygame

from config.settings import Settings


class UnknownSettingsField(Exception):
    pass


class WrongValueType(Exception):
    pass


class ConsoleWindow(pygame_gui.windows.UIConsoleWindow):
    def __init__(self, manager: pygame_gui.UIManager, menu_screen):
        rect = pygame.Rect(0, 0, 600, 400)
        super().__init__(rect, manager, 'Console')
        self.menu_screen = menu_screen
        self.starting_text = f'[{datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}] Console opened'
        self.reset()
        self.AVAILABLE_COMMANDS = {
            'help': 'Shows this message',
            'clear': 'Clears the console',
            'exit': 'Exits the console',
            'settings': 'Shows the current settings',
            'settings default': 'Sets the settings to default',
            'settings <field> <value>': 'Changes the value of the <field> to <value>',
        }
    
    def reset(self):
        self.clear_log()
        self.add_output_line_to_log(self.starting_text)

    def change_settings(self, field: str, new_value: str):
        s: Settings = self.menu_screen.settings
        if field not in s.__dict__: raise UnknownSettingsField
        field_type = type(s.__dict__[field])
        try:
            new_value_to_set = field_type(new_value)
        except ValueError:
            raise WrongValueType(f'{new_value} is not a valid {field_type.__name__}')
        setattr(s, field, new_value_to_set)
        s.dump()
    
    def command_settings(self, args: list[str]):
        if not len(args):
            self.add_output_line_to_log(str(self.menu_screen.settings))
            return
        if len(args) == 1 and args[0] == 'default':
            s = Settings.create_default()
            self.menu_screen.reload_settings()
            self.add_output_line_to_log(f'Settings set to default')
            return
        if len(args) == 2:
            try:
                field, new_value = args
                self.change_settings(field, new_value)
                self.menu_screen.reload_settings()
                self.add_output_line_to_log(f'Successfully changed {field} to {new_value}')
                return
            except UnknownSettingsField:
                self.add_output_line_to_log(f'[!] Unknown settings field: {field}') # type: ignore
                return
            except WrongValueType as e:
                self.add_output_line_to_log(f'[!] {e}')
                return
        self.add_output_line_to_log(f'[!] Usage: settings <field> <value>')

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
            elif text.startswith('settings'):
                args = text.split()[1:]
                self.command_settings(args)
            else:
                self.add_output_line_to_log(f'[!] Unknown command: {text}. Type "help" for available commands')
