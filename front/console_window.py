import datetime
from pprint import pformat

import pygame_gui
import pygame

from config import CONSOLE_WINDOW_SIZE
from config.settings import Settings


class UnknownSettingsField(Exception):
    pass


class WrongValueType(Exception):
    pass


class ConsoleWindow(pygame_gui.windows.UIConsoleWindow):
    def __init__(self, manager: pygame_gui.UIManager, menu_screen):
        rect = pygame.Rect(0, 0, *CONSOLE_WINDOW_SIZE)
        super().__init__(rect, manager, "Console")
        self.menu_screen = menu_screen
        self.starting_text = (
            f'[{datetime.datetime.now():%d/%m/%Y, %H:%M:%S}] Console opened'
        )
        self.reset()
        self.AVAILABLE_COMMANDS = {
            "help": "Shows this message",
            "clear": "Clears the console",
            "exit": "Exits the console",
            "settings": "Shows the current settings",
            "settings default": "Sets the settings to default",
            "settings <field> <value>": "Changes the value of the <field> to <value>",
            # 'saves delete <save_name>': 'Deletes the save with the given name',
        }

    def add_log(self, text: str):
        self.add_output_line_to_log(text)

    def reset(self):
        self.clear_log()
        self.add_log(self.starting_text)

    def change_settings(self, field: str, new_value: str):
        s: Settings = self.menu_screen.settings
        if field not in s.__dataclass_fields__:
            raise UnknownSettingsField
        field_type = s.__annotations__[field]
        try:
            new_value_to_set = field_type(new_value)
        except ValueError:
            raise WrongValueType(f"{new_value} is not a valid {field_type.__name__}")
        setattr(s, field, new_value_to_set)
        s.dump()

    def command_settings(self, args: list[str]):
        if not len(args):
            self.add_log(str(self.menu_screen.settings))
            return
        if len(args) == 1 and args[0] == "default":
            Settings.create_default()
            self.menu_screen.reload_settings()
            self.add_log("Settings set to default")
            return
        if len(args) == 2:
            try:
                field, new_value = args
                self.change_settings(field, new_value)
                self.menu_screen.reload_settings()
                self.add_log(f"Successfully changed {field} to {new_value}")
                return
            except UnknownSettingsField:
                self.add_log(f"[!] Unknown settings field: {field}")  # type: ignore
                return
            except WrongValueType as e:
                self.add_log(f"[!] {e}")
                return
        self.add_log("[!] Usage: settings <field> <value>")

    def process_event(self, event: pygame.event.Event):
        text = self.command_entry.get_text()
        if super().process_event(event) and text:
            text = text.strip()
            if text == "clear":
                self.reset()
            elif text == "exit":
                self.kill()
            elif text == "help":
                self.add_log("Available commands:")
                for k, v in self.AVAILABLE_COMMANDS.items():
                    self.add_log(f"{k}: {v}")
            elif text.startswith("settings"):
                args = text.split()[1:]
                self.command_settings(args)
            elif text == "info":
                if self.menu_screen.game_screen is not None:
                    self.add_log(pformat(self.menu_screen.game_screen.game.get_info()))
                else:
                    self.add_log("No game has been played yet")
            else:
                self.add_log(
                    f'[!] Unknown command: {text}. Type "help" for available commands'
                )
