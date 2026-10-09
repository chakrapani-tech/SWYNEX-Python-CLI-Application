"""
storage.py

Responsible for all JSON file persistence for the SWYNEX Task Manager:
loading tasks from disk, saving tasks to disk, and creating the data
file automatically if it does not yet exist.
"""

import json
import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TASKS_FILE = str(Path(__file__).resolve().with_name("tasks.json"))


class StorageError(Exception):
    """Raised when tasks cannot be loaded from, or saved to, disk."""


def load_task_data(
    file_path: str = TASKS_FILE,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Load the task list from the given JSON file.

    Behavior:
        - If the file does not exist, it is created with an empty task
          collection and an empty collection is returned.
        - If the file exists but is empty, an empty list is returned.
        - Both the original JSON list and the current object format are
          supported. The object format stores the next ID as well as tasks.
        - If the file contains invalid JSON or the wrong data shape,
          a StorageError is raised so the caller can decide how to
          recover (the file itself is left untouched).

    Args:
        file_path: Path to the JSON tasks file.

    Returns:
        The task dictionaries and the next unused task ID.

    Raises:
        StorageError: If the file cannot be read or contains invalid data.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            raw_content = file.read().strip()
    except FileNotFoundError:
        save_tasks([], file_path, next_id=1)
        return [], 1
    except (OSError, UnicodeError) as error:
        raise StorageError(f"Could not read '{file_path}': {error}") from error

    if not raw_content:
        return [], 1

    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as error:
        raise StorageError(
            f"'{file_path}' contains invalid JSON and could not be parsed "
            f"(line {error.lineno}, column {error.colno}). "
            "The file was left unchanged."
        ) from error

    if isinstance(data, list):
        tasks = data
        next_id = 1
    elif isinstance(data, dict) and isinstance(data.get("tasks"), list):
        tasks = data["tasks"]
        next_id = data.get("next_id")
        if type(next_id) is not int or next_id < 1:
            raise StorageError(f"'{file_path}' contains an invalid next_id.")
    else:
        raise StorageError(f"'{file_path}' does not contain a valid task list.")

    ids = []
    for task in tasks:
        if not isinstance(task, dict) or type(task.get("id")) is not int or task["id"] < 1:
            raise StorageError(f"'{file_path}' contains a task with an invalid ID.")
        if not isinstance(task.get("title"), str) or not task["title"].strip():
            raise StorageError(f"'{file_path}' contains a task with an invalid title.")
        if "description" in task and not isinstance(task["description"], str):
            raise StorageError(f"'{file_path}' contains an invalid description.")
        if "completed" in task and type(task["completed"]) is not bool:
            raise StorageError(f"'{file_path}' contains an invalid completion status.")
        if "priority" in task and task["priority"] not in ("Low", "Medium", "High"):
            raise StorageError(f"'{file_path}' contains an invalid priority.")
        due_date = task.get("due_date")
        if due_date is not None:
            if not isinstance(due_date, str):
                raise StorageError(f"'{file_path}' contains an invalid due date.")
            try:
                parsed_date = date.fromisoformat(due_date)
            except ValueError as error:
                raise StorageError(f"'{file_path}' contains an invalid due date.") from error
            if parsed_date.isoformat() != due_date:
                raise StorageError(f"'{file_path}' contains an invalid due date.")
        ids.append(task["id"])
    if len(ids) != len(set(ids)):
        raise StorageError(f"'{file_path}' contains duplicate task IDs.")

    if isinstance(data, list):
        next_id = max(ids, default=0) + 1
    elif next_id <= max(ids, default=0):
        raise StorageError(f"'{file_path}' contains a next_id that is not unique.")
    return tasks, next_id


def load_tasks(file_path: str = TASKS_FILE) -> List[Dict[str, Any]]:
    """Load task records, preserving the original list-returning API."""
    tasks, _ = load_task_data(file_path)
    return tasks


def save_tasks(
    tasks: List[Dict[str, Any]],
    file_path: str = TASKS_FILE,
    next_id: Optional[int] = None,
) -> None:
    """
    Save the given list of tasks to the JSON file, overwriting its contents.

    Args:
        tasks: The full list of task dictionaries to persist.
        file_path: Path to the JSON tasks file.

    Raises:
        StorageError: If the file cannot be written to disk.
    """
    try:
        if next_id is None:
            next_id = max((task["id"] for task in tasks), default=0) + 1
        if type(next_id) is not int or next_id <= max(
            (task["id"] for task in tasks), default=0
        ):
            raise ValueError("next_id must be greater than every task ID")
        payload = {"next_id": next_id, "tasks": tasks}
        destination = Path(file_path)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=str(destination.parent),
                delete=False,
            ) as file:
                temp_path = file.name
                json.dump(payload, file, indent=4)
                file.write("\n")
            os.replace(temp_path, destination)
        finally:
            if temp_path is not None and os.path.exists(temp_path):
                os.unlink(temp_path)
    except (OSError, TypeError, ValueError, KeyError) as error:
        raise StorageError(f"Could not write to '{file_path}': {error}") from error
