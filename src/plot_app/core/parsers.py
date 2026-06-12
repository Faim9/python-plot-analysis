import pandas as pd
import csv
import re
from pathlib import Path

def _is_data_row(line: str) -> bool:
    """
    Helper function to determine if a line consists strictly of numbers.
    It handles scientific notation (e.g., 1.2e-4) and standard floats.
    """
    if not line.strip():
        return False
    
    # Replace common delimiters with spaces to easily split
    clean_line = line.replace(',', ' ').replace('\t', ' ')
    parts = clean_line.split()
    
    try:
        # Attempt to convert all items in the row to floats
        [float(p) for p in parts]
        return True
    except ValueError:
        return False

def sniff_and_read_dat(filepath: str | Path, scan_lines: int = 100) -> pd.DataFrame:
    """
    Heuristically parses a messy .dat file, bypasses text headers, 
    detects delimiters, and returns a clean Pandas DataFrame.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        # Read the first chunk of lines to analyze the file structure
        lines = [f.readline() for _ in range(scan_lines)]
        
    # 1. Find where the actual data begins
    data_start_idx = 0
    for i, line in enumerate(lines):
        # We check for two consecutive data rows to avoid false positives 
        # (like a single random number in a header text)
        if _is_data_row(line) and _is_data_row(lines[i+1]):
            data_start_idx = i
            break
            
    # 2. Extract column names if a header exists
    skiprows = data_start_idx
    header_line = lines[skiprows - 1].strip() if skiprows > 0 else ""
    
    # 3. Sniff the delimiter (comma, tab, or space)
    delimiter = None
    try:
        # Sniffer works best on a line with letters and delimiters
        line_to_sniff = header_line if header_line else lines[data_start_idx]
        dialect = csv.Sniffer().sniff(line_to_sniff)
        delimiter = dialect.delimiter
    except csv.Error:
        # Fallback: Scientific data is notoriously separated by arbitrary whitespace
        delimiter = r'\s+' 

    # 4. Hand off the clean parameters to Pandas
    try:
        df = pd.read_csv(
            filepath, 
            skiprows=skiprows, 
            sep=delimiter, 
            engine='python', 
            header=None if not header_line else 0
        )
        
        # If there was no header, assign generic column names
        if not header_line:
            df.columns = [f"Column_{i}" for i in range(len(df.columns))]
            
        return df

    except Exception as e:
        raise ValueError(f"Failed to parse {filepath}. Error: {str(e)}")