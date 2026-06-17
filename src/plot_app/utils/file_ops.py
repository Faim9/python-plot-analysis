import json
from pathlib import Path

def save_json(filepath: Path, data: dict):
    """Safely writes a dictionary to a JSON file."""
    # Ensure the parent directory exists before saving
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def load_json(filepath: Path) -> dict:
    """Reads a JSON file into a dictionary. Returns empty dict if missing."""
    if not filepath.exists():
        print(f"Warning: {filepath} does not exist. Returning empty dict.")
        return {}
    else:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Failed to decode JSON from {filepath}. Returning empty dict.")
            return {}
        

def get_safe_path_destination(proposed_path: Path) -> Path:
        """
        Checks if a path exists. If it does, appends _v1, _v2, etc.
        Works flawlessly for both files (Test.dat -> Test_v1.dat) 
        and folders (My_Data -> My_Data_v1).
        """
        # If the coast is clear, just return the original path!
        if not proposed_path.exists():
            return proposed_path
            
        # The path exists. We need to split it apart to inject the version number.
        directory = proposed_path.parent
        stem = proposed_path.stem      # e.g., "Test_1" or "My_Folder"
        suffix = proposed_path.suffix  # e.g., ".dat" or "" (for folders)
        
        counter = 1
        while True:
            # Construct the new candidate: "Test_1_v1.dat"
            new_name = f"{stem}_v{counter}{suffix}"
            candidate_path = directory / new_name
            
            # If this new name doesn't exist, we return it.
            if not candidate_path.exists():
                return candidate_path
                
            # If _v1 is also taken, loop again and try _v2
            counter += 1

def extract_path(full_path: Path, folder:str) -> Path | None:
    """Extracts 'folder/...' from a path, regardless of how deep it is."""
    
    # 1. Break the path into a tuple of strings
    # Example: ('C:\\', 'Users', 'App', 'Projects', 'DF', 'Day_1', 'data.dat')
    parts = full_path.parts
    
    # 2. Safety check: Make sure the path actually exists in the full path
    if folder in parts:
        # 3. Find the exact index of 'DF'
        path_index = parts.index(folder)
        
        # 4. Slice the tuple from the path to the end, and unpack (*) it back into a Path
        sliced_path = Path(*parts[path_index:])
        
        return sliced_path
    else:
        return None