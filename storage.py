"""
storage.py

Responsible for all JSON file persistence for the SWYNEX Task Manager:
loading tasks from disk, saving tasks to disk, and creating the data
file automatically if it does not yet exist.
"""

import json
import os
from typing import Any, Dict, List

TASKS_FILE = "tasks.json"


class StorageError(Exception):
    """Raised when tasks cannot be loaded from, or saved to, disk."""


def load_tasks(file_path: str = TASKS_FILE) -> List[Dict[str, Any]]:
    """
    Load the task list from the given JSON file.

    Behavior:
        - If the file does not exist, it is created with an empty list
          and an empty list is returned.
        - If the file exists but is empty, an empty list is returned.
        - If the file contains invalid JSON or the wrong data shape,
          a StorageError is raised so the caller can decide how to
          recover (the file itself is left untouched).

    Args:
        file_path: Path to the JSON tasks file.

    Returns:
        A list of task dictionaries.

    Raises:
        StorageError: If the file cannot be read or contains invalid data.
    """
    if not os.path.exists(file_path):
        save_tasks([], file_path)
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            raw_content = file.read().strip()
    except OSError as error:
        raise StorageError(f"Could not read '{file_path}': {error}") from error

    if not raw_content:
        return []

    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as error:
        raise StorageError(
            f"'{file_path}' contains invalid JSON and could not be parsed "
            f"(line {error.lineno}, column {error.colno}). "
            "The file was left unchanged."
        ) from error

    if not isinstance(data, list):
        raise StorageError(
            f"'{file_path}' does not contain a list of tasks as expected."
        )

    return data


def save_tasks(tasks: List[Dict[str, Any]], file_path: str = TASKS_FILE) -> None:
    """
    Save the given list of tasks to the JSON file, overwriting its contents.

    Args:
        tasks: The full list of task dictionaries to persist.
        file_path: Path to the JSON tasks file.

    Raises:
        StorageError: If the file cannot be written to disk.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(tasks, file, indent=4)
    except OSError as error:
        raise StorageError(f"Could not write to '{file_path}': {error}") from error
