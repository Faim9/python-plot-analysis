from pathlib import Path
from core.config_manager import ProjectConfig
from utils.file_ops import get_safe_path_destination
import logging
from shutil import copy2, copytree
from ui.dialogs import FileConflictDialog

class ProjectManager:
    def __init__(self):
        self.active_project_path = None
        self.project_config = None
        self.is_project_loaded = False

        self.app_logger = logging.getLogger('AppLogger')

    def _is_folder_valid_project(self, folder_path: str | Path) -> bool:
        """Checks if the given folder has the necessary structure to be considered a valid project."""
        # For a folder to be a valid project, it needs the .other/project_config.json file and the /DF directory
        pf_path = Path(folder_path)
        config_path = pf_path / ".other" / "project_config.json"
        DF_path = pf_path / "DF"

        return pf_path.exists() and config_path.exists() and DF_path.exists()

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
        
    def import_folder(self,source_folder:Path):
        '''Import entire folder structures to the Data Folder, /DF'''

        aimed_directory = self.active_project_path / 'DF' / source_folder.name #type:ignore

        # State variables for the import
        skip_all = False
        replace_all = False
        import_cancelled = False
        rename_all = False

        # --- THE INTERCEPTOR ---
        def smart_copy(src, dst):
            nonlocal skip_all,replace_all,import_cancelled,rename_all

            # If the user previously clicked cancel, immediately abort further copies
            if import_cancelled:
                return 

            # Check if there is a collision
            if Path(dst).exists():
                
                #Check if user already decided to skip
                if skip_all:
                    return  # Do nothing, just return
                
                #Check if user already decided to rename all
                if rename_all:
                    new_dst = get_safe_path_destination(Path(dst))
                    self.app_logger.debug(f'File {Path(dst).name} autorenamed to {Path(new_dst).name}.')
                    copy2(src,new_dst)
                    return
                
                self.app_logger.warning(f'Conflict in file {src} at {dst}. Already exists.')

                if not replace_all:
                    # Pop the dialog! (This pauses the script until they click)
                    conflict_message = f'The file {Path(src).name} already exists in {Path(dst).parent}. What to do?'
                    dialog = FileConflictDialog(conflict_message,options = ["Cancel","Skip all", "Skip","Rename", "Rename all", "Replace", "Replace all"])
                    dialog.exec()
                    
                    # Process their decision
                    if dialog.decision == "Cancel":
                        import_cancelled = True
                        self.app_logger.debug(f'User decided to cancel import')
                        return
                    elif dialog.decision == "Skip all":
                        skip_all = True
                        self.app_logger.debug(f'User decided to skip all.')
                        return
                    elif dialog.decision == "Skip":
                        self.app_logger.debug(f'User decided to skip this file.')
                        return
                    elif dialog.decision == "Rename":
                        dst = get_safe_path_destination(Path(dst)) #Rename and let fall to copy2
                        self.app_logger.debug(f'User decided to rename this file to {Path(dst).name}.')
                    elif dialog.decision == "Rename all":
                        self.app_logger.debug(f'User decided to rename all files')
                        rename_all = True
                        dst = get_safe_path_destination(dst) #set var, rename and let fall to copy2
                        self.app_logger.debug(f'File autorenamed to {Path(dst).name}.')
                    elif dialog.decision == "Replace all":
                        replace_all = True #Set var
                        self.app_logger.debug(f'User decided to replace all files.')
                        #Dont rename and let fall to overwrite/replace
                    elif dialog.decision == "Replace":
                        self.app_logger.debug(f'User decided to replace this file.')
                        #Let fall too.

            # If we reach here, it's safe to overwrite or the file is new/renamed
            self.app_logger.debug(f'File copying: {Path(dst).name}')
            copy2(src, dst)


        try:
            copytree(source_folder,aimed_directory, dirs_exist_ok=True,copy_function=smart_copy)
            if import_cancelled:
                self.app_logger.info(f'User canceled import.')
            else: self.app_logger.info(f'Import sucess.')
        except Exception as e:
            self.app_logger.exception(f'Error during folder import: {e}.')


    def import_files(self, imported_files: list) -> None:
        '''Import files .dat to the Data Folder, /DF'''

        aimed_directory = self.active_project_path / 'DF' #type: ignore
        num_files_failed = 0
        total_files = len(imported_files)

        # 1. Quick Guard: If the user passed an empty list, just return
        if total_files == 0:
            return 

        self.app_logger.info(f'Importing {total_files} files to {aimed_directory.name}.')

        # 2. State variables for the loop
        skip_all = False
        replace_all = False
        rename_all = False
        import_cancelled = False

        # 3. Dynamic Dialog Options (Remove "all" options if only 1 file is selected)
        if total_files > 1:
            dialog_options = ["Cancel", "Skip all", "Skip", "Rename", "Rename all", "Replace", "Replace all"]
        else:
            dialog_options = ["Cancel", "Skip", "Rename", "Replace"]

        # 4. Safely process each file
        for file_path_str in imported_files:
            
            # If the user clicked cancel on a previous file, immediately break the loop
            if import_cancelled:
                break

            source_file = Path(file_path_str)
            destination_file = aimed_directory / source_file.name

            # --- COLLISION INTERCEPTOR ---
            if destination_file.exists():
                
                if skip_all:
                    continue # Skip to the next file in the loop immediately
                    
                if rename_all:
                    destination_file = get_safe_path_destination(destination_file)
                    self.app_logger.debug(f'Auto-renamed to: {destination_file.name}')
                    
                elif not replace_all:
                    self.app_logger.warning(f'Conflict: {source_file.name} already exists in /DF.')
                    
                    # Pop the dialog!
                    conflict_message = f'The file {source_file.name} already exists in {aimed_directory.name}. What to do?'
                    dialog = FileConflictDialog(conflict_message, options=dialog_options)
                    dialog.exec()
                    
                    # Process their decision
                    if dialog.decision == "Cancel":
                        import_cancelled = True
                        self.app_logger.info(f'User cancelled the batch import process.')
                        break # Kills the loop entirely
                        
                    elif dialog.decision == "Skip all":
                        skip_all = True
                        self.app_logger.debug(f'User decided to skip all remaining conflicts.')
                        continue
                        
                    elif dialog.decision == "Skip":
                        self.app_logger.debug(f'User skipped this file.')
                        continue
                        
                    elif dialog.decision == "Rename all":
                        rename_all = True
                        destination_file = get_safe_path_destination(destination_file)
                        self.app_logger.debug(f'User decided to rename all. New path: {destination_file.name}')
                        
                    elif dialog.decision == "Rename":
                        destination_file = get_safe_path_destination(destination_file)
                        self.app_logger.debug(f'User renamed file to: {destination_file.name}')
                        
                    elif dialog.decision == "Replace all":
                        replace_all = True
                        self.app_logger.debug(f'User decided to replace all remaining conflicts.')
                        
                    elif dialog.decision == "Replace":
                        self.app_logger.debug(f'User decided to replace {source_file.name}.')


            # --- THE ACTUAL COPY ---
            try:
                self.app_logger.debug(f"Copying file -> {destination_file.name}")
                copy2(source_file, destination_file)
            except Exception as e:
                self.app_logger.exception(f'Unable to import {source_file.name}. Skipping file. Exception: {e}')
                num_files_failed += 1

        # 5. Final Summary Log
        if not import_cancelled:
            successful_imports = total_files - num_files_failed
            self.app_logger.info(f'Import complete. {successful_imports} succeeded, {num_files_failed} failed.')



