from pathlib import Path
from utils.file_ops import load_json, save_json

class ProjectConfig:
    def __init__(self, project_dir: str | Path):
        self.project_dir = Path(project_dir)
        
        # Define the exact path to the preferences file
        self.config_path = self.project_dir / ".other" / "project_prefs.json"
        
        # Load existing settings or generate defaults
        self.settings = self._load_or_create_defaults()

        # Save immediately to ensure the file exists for future loads (and to create the .other folder if needed)
        self.save()

    def _load_or_create_defaults(self) -> dict:
        """Loads settings from disk, applying defaults for missing keys."""
        default_settings = {
            "data_folder": str(self.project_dir / "DF"),
            "plot_prefs": {
                "line_width": 2.0,
                "scatter_size": 5,
                "theme": "dark"
            },
            "column_mapping": {
                "x_col": 0,
                "y_col": 1
            }
        }
        
        user_settings = load_json(self.config_path)
        
        # Merge defaults with whatever the user has saved
        # (This ensures new updates don't break old project files)
        return {**default_settings, **user_settings}

    def save(self):
        """Writes the current state of self.settings to disk."""
        save_json(self.config_path, self.settings)

    def update(self, key: str, value):
        """Updates a setting in memory and immediately saves to disk."""
        self.settings[key] = value
        self.save()

