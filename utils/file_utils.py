import os

def file_exists(file_path: str) -> bool:
    """Checks if a file exists and is a regular file.
    
    Args:
        file_path (str): Path to the file.
        
    Returns:
        bool: True if the file exists and is a file, False otherwise.
    """
    return os.path.exists(file_path) and os.path.isfile(file_path)

def is_file_empty(file_path: str) -> bool:
    """Checks if a file has size 0 (is empty).
    
    Args:
        file_path (str): Path to the file.
        
    Returns:
        bool: True if the file is empty, False otherwise.
    """
    if not file_exists(file_path):
        return True
    return os.path.getsize(file_path) == 0

def get_file_extension(file_path: str) -> str:
    """Extracts the file extension in lowercase.
    
    Args:
        file_path (str): Path to the file.
        
    Returns:
        str: The lowercase extension (e.g. '.csv', '.pdf').
    """
    return os.path.splitext(file_path)[1].lower()
