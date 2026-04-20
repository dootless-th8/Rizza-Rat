import json, os
from settings import *

class SettingsManager:

    SETTINGS_FILE = 'settings.json'

    DEFAULT_SETTINGS = {
        'volume':100,
        'fullscreen': False
    }

    def __init__(self):
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.load_settings()

    def load_settings(self):
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, 'r') as f:
                    loaded = json.load(f)
                    self.settings.update(loaded)
                    print(f"Loading Success from {self.SETTINGS_FILE}")
            except json.JSONDecodeError:
                print(f"Error from reading {self.SETTINGS_FILE}, using default")

            except Exception as e:
                print(f"Error from loading {self.SETTINGS_FILE}, using default")

        else:
            print("Nothing found, using default")
            self.save_settings()

    def save_settings(self):
        try:
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
            print(f"Settings saved to {self.SETTINGS_FILE}")
        except Exception as e:
            print(f"Error saving settings: {e}")

    # Get specific setting's value
    def get(self, key, default=None):
        return self.settings.get(key, default)
    
    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

    def get_all(self):
        return self.settings.copy()
    
    def reset_to_defaults(self):
        self.settings = self.SETTINGS_FILE.copy()
        self.save_settings()