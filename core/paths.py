from pathlib import Path


def get_project_path() -> Path:
    return Path(__file__).parent.parent
