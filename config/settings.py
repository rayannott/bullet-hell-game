from dataclasses import dataclass
import json
from typing import TypedDict

from config.front import SETTINGS_FILE


@dataclass
class Settings:
    sfx_volume: float = 0.3
    music_volume: float = 0.3
    difficulty: int = 3 # from 1 to 5; 3 is normal

    def dump(self):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(self.__dict__, f)
    
    @staticmethod
    def create_default() -> 'Settings':
        s = Settings()
        s.dump()
        return s
    
    @staticmethod
    def load() -> 'Settings':
        if not SETTINGS_FILE.exists():
            print('[SettingsWarning] Settings file does not exist. Creating a new settings file with default values.')
            return Settings.create_default()
        with open(SETTINGS_FILE, 'r') as f:
            try:
                json_data = json.load(f)
                # check agains all fields
                s = Settings()
                for field in Settings.__dataclass_fields__.keys():
                    if field in json_data:
                        setattr(s, field, json_data[field])
                    else:
                        print(f'[SettingsWarning] Settings file does not contain field "{field}". Using default value.')
                if unknown_keys:=json_data.keys() - Settings.__dataclass_fields__.keys():
                    print(f'[SettingsWarning] Settings file contains unknown fields: {unknown_keys}.\nThe foreign fields are deprecated and will be ignored.')
                print(f'[Settings] Settings file loaded successfully. Using the following settings:\n{s}')
                s.dump()
                return s
            except json.JSONDecodeError:
                print('[SettingsError] Settings file corrupted. Creating settings file with default values.')
                return Settings.create_default()
