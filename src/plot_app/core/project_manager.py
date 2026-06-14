from pathlib import Path
from core.config_manager import ProjectConfig

class ProjectManager:
    def __init__(self):
        self.active_project_path = None
        self.project_config = None
        self.is_project_loaded = False

    def _is_folder_valid_project(self, folder_path: str | Path) -> bool:
        """Checks if the given folder has the necessary structure to be considered a valid project."""
        # For a folder to be a valid project, it only needs the .other/project_config.json file
        pf_path = Path(folder_path)
        config_path = pf_path / ".other" / "project_config.json"

        return pf_path.exists() and config_path.exists()

    def create_new_project(self, target_folder: str | Path) -> bool:
        """Generates the PF, DF, and AF tree for a brand-new project."""
        pf_path = Path(target_folder)

        # 1. Define the subfolders
        df_path = pf_path / "DF"
        af_path = pf_path / "AF"
        
        try:
            # 2. Create the directories safely
            # exist_ok=True ensures the app doesn't crash if the folder already exists
            df_path.mkdir(parents=True, exist_ok=True)
            af_path.mkdir(parents=True, exist_ok=True)

            # 3. Store the active project path
            self.active_project_path = pf_path
            
            # 4. Initialize the config (this creates project_prefs.json with defaults in .other/)
            self.project_config = ProjectConfig(self.active_project_path)
            
            self.is_project_loaded = True
            return True
            
        except Exception as e:
            print(f"Failed to create project tree: {e}")
            return False

    def load_project(self, folder_path: str | Path) -> bool:
        """Initializes a project from a given folder."""
        pf_path = Path(folder_path)
        
        if not pf_path.exists() or not self._is_folder_valid_project(pf_path):
            return False
 
            
        self.active_project_path = pf_path
        
        # This will load the existing config
        self.project_config = ProjectConfig(project_dir=self.active_project_path)
        self.is_project_loaded = True
        
        return True
    


