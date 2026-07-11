import sys
import os

def get_resource_path(relative_path: str) -> str:
    """
    Get the absolute path to a resource.
    This is necessary for PyInstaller to find files after packaging.
    When packaged, PyInstaller extracts resources to a temporary folder (_MEIPASS).
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # If not running as a bundled executable, use the current working directory
        base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        # Here we assume utils.py is in src/, so its parent is the project root.

    return os.path.join(base_path, relative_path)
