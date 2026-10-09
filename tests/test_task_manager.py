import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import main
from storage import load_tasks, save_tasks
from task_manager import TaskManager
from validators import parse_due_date, parse_task_id, validate_priority, validate_search_query


class TaskManagerTests(unittest.TestCase):
    def test_add_task_generates_unique_ids(self):
        manager = TaskManager()
        first = manager.add_task("Write report", "Draft the internship update", "High")
        second = manager.add_task("Review code", "Check for validation issues", "Low")

        self.assertEqual(first["id"], 1)
        self.assertEqual(second["id"], 2)
        self.assertEqual(len(manager.get_all_tasks()), 2)

    def test_search_is_case_insensitive_and_matches_title_or_description(self):
        manager = TaskManager([
            {"id": 1, "title": "Plan sprint", "description": "Outline backlog items", "completed": False, "priority": "Medium", "due_date": None, "created_at": "2026-01-01T10:00:00"},
            {"id": 2, "title": "Fix bug", "description": "Resolve login issue", "completed": False, "priority": "High", "due_date": None, "created_at": "2026-01-01T11:00:00"},
        ])

        matches = manager.search_tasks("LOGIN")
        self.assertEqual([task["id"] for task in matches], [2])

        matches = manager.search_tasks("sprint")
        self.assertEqual([task["id"] for task in matches], [1])

    def test_validators_reject_invalid_input(self):
        self.assertIsNone(parse_task_id("0"))
        self.assertIsNone(parse_task_id("abc"))
        self.assertIsNone(validate_priority("urgent"))
        self.assertIsNone(parse_due_date("2026-02-30"))
        self.assertFalse(validate_search_query("   "))

    def test_storage_round_trip_uses_temp_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "tasks.json"
            tasks = [{"id": 1, "title": "Demo", "description": "Example", "completed": False, "priority": "Low", "due_date": "2026-12-31", "created_at": "2026-01-01T00:00:00"}]
            save_tasks(tasks, str(path))
            loaded = load_tasks(str(path))
            self.assertEqual(loaded, tasks)

    def test_print_task_displays_task_details(self):
        task = {
            "id": 7,
            "title": "Prepare pitch",
            "description": "Create demo deck",
            "completed": False,
            "priority": "High",
            "due_date": "2026-11-05",
            "created_at": "2026-10-01T09:30:00",
        }

        stream = io.StringIO()
        with redirect_stdout(stream):
            main.print_task(task)

        output = stream.getvalue()
        self.assertIn("ID: 7", output)
        self.assertIn("Title: Prepare pitch", output)
        self.assertIn("Description: Create demo deck", output)
        self.assertIn("Priority: High", output)
        self.assertIn("Due Date: 2026-11-05", output)
        self.assertIn("Status: Pending", output)
        self.assertIn("Created: 2026-10-01", output)

    def test_cli_menu_handles_add_and_view_flow(self):
        with patch("main.storage.load_tasks", return_value=[]), \
             patch("main.storage.save_tasks", return_value=None), \
             patch("builtins.input", side_effect=["1", "Team sync", "Discuss sprint plan", "low", "2026-12-20", "2", "6"]):
            stream = io.StringIO()
            with redirect_stdout(stream):
                main.main()

        output = stream.getvalue()
        self.assertIn("Task added successfully with ID: 1", output)
        self.assertIn("Title: Team sync", output)
        self.assertIn("Thank you for using SWYNEX Task Manager. Goodbye!", output)


if __name__ == "__main__":
    unittest.main()
