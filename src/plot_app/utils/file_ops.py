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