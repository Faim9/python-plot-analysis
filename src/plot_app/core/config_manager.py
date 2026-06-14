from pathlib import Path
from utils.file_ops import load_json, save_json


#Main class for handling any json configs. (project-wide, plot-wide, etc.)

DEFAULT_CONFIGS_DIR = Path(__file__).parent.parent / "assets" / "default_configs"

class ConfigManager:
    def __init__(self, user_config_path: str | Path, default_config_path: str | Path, fallback_config: dict):

        #Store the paths and fallback config for eventual later use
        self.user_config_path = Path(user_config_path)
        self.default_config_path = Path(default_config_path)
        self.fallback_config = fallback_config

        #Load the user config, applying defaults and using the fallback for any crucial missing keys
        #load_json will return an empty dict if the file doesn't exist, or fail to decode JSON, 
        #so this is safe even on first run, in case the user config file hasn't been created yet
        self.user_config = {**self.fallback_config, **load_json(self.default_config_path), **load_json(self.user_config_path)}

        #Immedietely save the merged config back to the user config path, ensuring it exists for future loads and that any missing keys are added
        self.save()

    def save(self):
        """Writes the current state of self.user_config to disk."""
        save_json(self.user_config_path, self.user_config)

    def update(self, key: str, value):
        """Updates a setting in memory and immediately saves to disk."""
        self.user_config[key] = value
        self.save()

    # Some functions to help with code readability when using this class

    def __getitem__(self, key):
        '''Allows dict-like access to config values, e.g. config_manager["some_key"]'''
        return self.user_config.get(key)
    
    def __setitem__(self, key, value):
        '''Allows dict-like setting of config values, e.g. config_manager["some_key"] = new_value'''
        self.update(key, value)

    def get(self, key, default=None):
        '''Allows dict-like access with a default value, e.g. config_manager.get("some_key", default_value)'''
        return self.user_config.get(key, default)

class ProjectConfig(ConfigManager):
    '''
    Specialized ConfigManager for handling project-specific settings, stored in .other/project_config.json within the project folder.
    It is initialized when a project is created or opened, at which point project_dir is passed to it.
    '''
    def __init__(self, project_dir: str | Path):
        
        # 1. Store the project directory path
        self.project_dir = Path(project_dir)
        
        # 2. Define where the project config lives inside the project directory
        USER_CONFIG_SUBPATH = Path(".other") / "project_config.json"
        self.user_config_path = self.project_dir / USER_CONFIG_SUBPATH

        # 3. Get the default config path
        # This is a static file that lives in /src/plot_app/assets/default_configs
        # So, we can hardcode the relative path to the default config, since it's always in the same place relative to this code (which is in /src/plot_app/core/config_manager.py)
        self.default_config_path = DEFAULT_CONFIGS_DIR / "default_project_config.json"

        # 4. Define a fallback config for any crucial keys that must exist for the app to function, even if the default config file is missing or corrupted.
        FALLBACK_CONFIG = {
            "plot_prefs": {
                "line_width": 2.0,
                "scatter_size": 5,
                "theme": "light"},
            "column_mapping": {
                "x_col": 0,
                "y_col": 1},
            }

        self.fallback_config = FALLBACK_CONFIG

        super().__init__(self.user_config_path, self.default_config_path, self.fallback_config)

