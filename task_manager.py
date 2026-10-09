"""
task_manager.py

Responsible for task-related business logic: adding tasks, retrieving
tasks, marking tasks complete, deleting tasks, and searching tasks by
title or description. This module knows nothing about the CLI or about
files on disk - it only operates on an in-memory list of task
dictionaries, which keeps it easy to test and reuse.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

# Default priority applied to new tasks when none is given, and to
# existing tasks loaded from disk that predate the priority field.
DEFAULT_PRIORITY = "Medium"


class TaskManager:
    """Manages an in-memory collection of tasks."""

    def __init__(
        self,
        tasks: Optional[List[Dict[str, Any]]] = None,
        next_id: Optional[int] = None,
    ) -> None:
        """
        Initialize the manager with an existing list of tasks (e.g. loaded
        from disk), or start empty if none is provided.

        Loaded tasks are normalized so that older records saved before
        the priority/due-date fields existed still have every expected
        key, with sensible defaults filled in. This keeps the rest of
        the application free to assume every task has the same shape.
        """
        raw_tasks = tasks if tasks is not None else []
        self.tasks: List[Dict[str, Any]] = [
            self._normalize_task(task) for task in raw_tasks
        ]
        highest_id = max((task["id"] for task in self.tasks), default=0)
        self._next_id = max(next_id or 1, highest_id + 1)

    @staticmethod
    def _normalize_task(task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fill in sensible defaults for any fields missing from a task
        record, without altering fields that are already present.

        This is what allows tasks.json files created by earlier
        versions of the application (before priority and due date
        existed) to keep working without modification.
        """
        normalized = dict(task)
        normalized.setdefault("description", "")
        normalized.setdefault("completed", False)
        normalized.setdefault("priority", DEFAULT_PRIORITY)
        normalized.setdefault("due_date", None)
        normalized.setdefault("created_at", "")
        return normalized

    def _generate_task_id(self) -> int:
        """Generate a monotonically increasing task ID."""
        task_id = self._next_id
        self._next_id += 1
        return task_id

    @property
    def next_id(self) -> int:
        """Return the next ID for persistence."""
        return self._next_id

    def add_task(
        self,
        title: str,
        description: str = "",
        priority: str = DEFAULT_PRIORITY,
        due_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new task and add it to the collection.

        Args:
            title: The task title. Assumed already validated as non-empty.
            description: An optional task description.
            priority: The task priority. Assumed already validated as one
                of 'Low', 'Medium', or 'High'.
            due_date: An optional due date, already normalized to
                YYYY-MM-DD format, or None if no due date was given.

        Returns:
            The newly created task dictionary.
        """
        task: Dict[str, Any] = {
            "id": self._generate_task_id(),
            "title": title.strip(),
            "description": description.strip(),
            "completed": False,
            "priority": priority,
            "due_date": due_date,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        self.tasks.append(task)
        return task

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Return every task currently held in memory."""
        return self.tasks

    def find_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        Find a task by its ID.

        Args:
            task_id: The ID to search for.

        Returns:
            The matching task dictionary, or None if not found.
        """
        for task in self.tasks:
            if task["id"] == task_id:
                return task
        return None

    def complete_task(self, task_id: int) -> bool:
        """
        Mark a task as completed.

        Args:
            task_id: The ID of the task to complete.

        Returns:
            True if the task was found and updated, False otherwise.
        """
        task = self.find_task(task_id)
        if task is None:
            return False
        task["completed"] = True
        return True

    def delete_task(self, task_id: int) -> bool:
        """
        Remove a task from the collection.

        Args:
            task_id: The ID of the task to delete.

        Returns:
            True if the task was found and removed, False otherwise.
        """
        task = self.find_task(task_id)
        if task is None:
            return False
        self.tasks.remove(task)
        return True

    def search_tasks(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for tasks whose title or description contains the query.

        The match is case-insensitive and looks for the query as a
        substring, so partial words are matched (e.g. 'rep' matches
        'Report').

        Args:
            query: The text to search for. Assumed already validated
                as non-empty.

        Returns:
            A list of matching task dictionaries, in their existing
            order. Empty if nothing matches.
        """
        normalized_query = query.strip().lower()
        return [
            task
            for task in self.tasks
            if normalized_query in task.get("title", "").lower()
            or normalized_query in task.get("description", "").lower()
        ]

    def filter_tasks(
        self,
        priority: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """Filter tasks by optional canonical priority and completion state."""
        return [
            task
            for task in self.tasks
            if (priority is None or task.get("priority") == priority)
            and (completed is None or task.get("completed") is completed)
        ]
