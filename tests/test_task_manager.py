import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import main
from storage import StorageError, load_task_data, load_tasks, save_tasks
from task_manager import TaskManager
from validators import (
    parse_due_date,
    parse_task_id,
    validate_menu_choice,
    validate_priority,
    validate_search_query,
    validate_task_title,
    validate_yes_no,
)


class TaskManagerTests(unittest.TestCase):
    def test_add_task_normalizes_values_and_generates_ids(self):
        manager = TaskManager()
        first = manager.add_task("  Write report  ", "  Draft update  ", "High")
        second = manager.add_task("Review code", priority="Low")

        self.assertEqual([first["id"], second["id"]], [1, 2])
        self.assertEqual(first["title"], "Write report")
        self.assertEqual(first["description"], "Draft update")
        self.assertIsNone(first["due_date"])
        self.assertEqual(manager.next_id, 3)

    def test_deleted_id_is_not_reused_after_restart(self):
        manager = TaskManager()
        first = manager.add_task("First")
        manager.add_task("Second")
        manager.delete_task(first["id"])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "tasks.json")
            save_tasks(manager.get_all_tasks(), path, next_id=manager.next_id)
            loaded, next_id = load_task_data(path)
            restored = TaskManager(loaded, next_id=next_id)
            new_task = restored.add_task("Third")

        self.assertEqual(new_task["id"], 3)

    def test_find_complete_delete_and_missing_ids(self):
        manager = TaskManager()
        task = manager.add_task("Task")

        self.assertIs(manager.find_task(task["id"]), task)
        self.assertTrue(manager.complete_task(task["id"]))
        self.assertTrue(task["completed"])
        self.assertFalse(manager.complete_task(99))
        self.assertTrue(manager.delete_task(task["id"]))
        self.assertFalse(manager.delete_task(task["id"]))
        self.assertEqual(manager.get_all_tasks(), [])

    def test_search_is_case_insensitive_for_title_and_description(self):
        manager = TaskManager()
        manager.add_task("Plan Sprint", "Outline backlog")
        manager.add_task("Fix bug", "Resolve LOGIN issue")

        self.assertEqual([t["id"] for t in manager.search_tasks("sprint")], [1])
        self.assertEqual([t["id"] for t in manager.search_tasks("LOGIN")], [2])
        self.assertEqual(manager.search_tasks("missing"), [])

    def test_filter_by_priority_status_and_both(self):
        manager = TaskManager()
        manager.add_task("High pending", priority="High")
        manager.add_task("High complete", priority="High")
        manager.add_task("Low pending", priority="Low")
        manager.complete_task(2)

        self.assertEqual([t["id"] for t in manager.filter_tasks(priority="High")], [1, 2])
        self.assertEqual([t["id"] for t in manager.filter_tasks(completed=False)], [1, 3])
        self.assertEqual(
            [t["id"] for t in manager.filter_tasks("High", True)], [2]
        )
        self.assertEqual(manager.filter_tasks("Medium", True), [])

    def test_legacy_task_fields_are_normalized(self):
        manager = TaskManager([{"id": 5, "title": "Legacy"}])
        self.assertEqual(manager.get_all_tasks()[0]["priority"], "Medium")
        self.assertEqual(manager.get_all_tasks()[0]["description"], "")
        self.assertIsNone(manager.get_all_tasks()[0]["due_date"])
        self.assertEqual(manager.next_id, 6)


class ValidatorTests(unittest.TestCase):
    def test_menu_title_and_search_validation(self):
        self.assertTrue(validate_menu_choice(" 1 ", {"1", "2"}))
        self.assertFalse(validate_menu_choice("x", {"1", "2"}))
        self.assertTrue(validate_task_title("Task"))
        self.assertFalse(validate_task_title("  "))
        self.assertTrue(validate_search_query(" term "))
        self.assertFalse(validate_search_query(" "))

    def test_task_id_validation(self):
        self.assertEqual(parse_task_id(" 12 "), 12)
        for invalid in ("", "0", "-1", "1.2", "abc"):
            with self.subTest(invalid=invalid):
                self.assertIsNone(parse_task_id(invalid))

    def test_priority_validation(self):
        self.assertEqual(validate_priority(" high "), "High")
        self.assertIsNone(validate_priority("Urgent"))
        self.assertIsNone(validate_priority(""))

    def test_due_date_requires_real_zero_padded_iso_date(self):
        self.assertEqual(parse_due_date("2026-02-28"), "2026-02-28")
        for invalid in ("", "2026-02-29", "2026-13-01", "2026-2-01", "01-02-2026"):
            with self.subTest(invalid=invalid):
                self.assertIsNone(parse_due_date(invalid))

    def test_yes_no_validation(self):
        self.assertIs(validate_yes_no(" YES "), True)
        self.assertIs(validate_yes_no("n"), False)
        self.assertIsNone(validate_yes_no("maybe"))


class StorageTests(unittest.TestCase):
    def test_atomic_storage_round_trip_preserves_id_sequence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "tasks.json")
            tasks = [{"id": 1, "title": "Demo", "completed": False}]
            save_tasks(tasks, path, next_id=7)
            loaded, next_id = load_task_data(path)
            loaded_tasks = load_tasks(path)

        self.assertEqual(loaded, tasks)
        self.assertEqual(next_id, 7)
        self.assertEqual(loaded_tasks, tasks)

    def test_missing_file_is_created_as_empty_task_store(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "new.json"
            self.assertEqual(load_task_data(str(path)), ([], 1))
            self.assertTrue(path.exists())
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {
                "next_id": 1,
                "tasks": [],
            })

    def test_legacy_list_format_loads_and_derives_next_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "legacy.json"
            path.write_text('[{"id": 4, "title": "Old"}]', encoding="utf-8")
            self.assertEqual(load_task_data(str(path)), ([{"id": 4, "title": "Old"}], 5))

    def test_corrupted_or_invalid_data_raises_storage_error_without_overwrite(self):
        invalid_values = ("{broken", "{}", '[{"id": 1, "title": ""}]', '[{"id": 1, "title": "A"}, {"id": 1, "title": "B"}]')
        for contents in invalid_values:
            with self.subTest(contents=contents), tempfile.TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / "bad.json"
                path.write_text(contents, encoding="utf-8")
                with self.assertRaises(StorageError):
                    load_task_data(str(path))
                self.assertEqual(path.read_text(encoding="utf-8"), contents)

    def test_save_reports_unwritable_destination(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "missing" / "tasks.json")
            with self.assertRaises(StorageError):
                save_tasks([], path)


class CliTests(unittest.TestCase):
    def test_add_rejects_blank_title_and_invalid_priority(self):
        manager = TaskManager()
        stream = io.StringIO()
        with patch("builtins.input", side_effect=["   "]), redirect_stdout(stream):
            main.handle_add_task(manager)
        self.assertIn("title cannot be empty", stream.getvalue())
        self.assertEqual(manager.get_all_tasks(), [])

        stream = io.StringIO()
        with patch("builtins.input", side_effect=["Valid title", "", "Urgent"]), \
             redirect_stdout(stream):
            main.handle_add_task(manager)
        self.assertIn("Priority must be Low, Medium, or High", stream.getvalue())
        self.assertEqual(manager.get_all_tasks(), [])

    def test_invalid_due_date_is_reported_and_task_saved_without_date(self):
        manager = TaskManager()
        stream = io.StringIO()
        with patch(
            "builtins.input",
            side_effect=["Valid title", "", "Medium", "2026-02-30"],
        ), patch("main.storage.save_tasks"), redirect_stdout(stream):
            main.handle_add_task(manager)

        self.assertIn("not a valid date", stream.getvalue())
        self.assertIsNone(manager.get_all_tasks()[0]["due_date"])

    def test_view_tasks_displays_every_task_field_and_summary(self):
        manager = TaskManager()
        manager.add_task("Prepare pitch", "Create demo deck", "High", "2026-11-05")
        stream = io.StringIO()
        with redirect_stdout(stream):
            main.handle_view_tasks(manager)

        output = stream.getvalue()
        for value in (
            "ID: 1", "Title: Prepare pitch", "Description: Create demo deck",
            "Priority: High", "Due Date: 2026-11-05", "Status: Pending",
            "Created:", "Total: 1", "Pending: 1", "Completed: 0",
        ):
            self.assertIn(value, output)

    def test_view_displays_all_tasks_loaded_from_json_with_correct_summary(self):
        tasks = [
            {
                "id": 4,
                "title": "Pending report",
                "description": "Prepare the summary",
                "completed": False,
                "priority": "High",
                "due_date": "2026-11-05",
                "created_at": "2026-10-01T09:30:00",
            },
            {
                "id": 9,
                "title": "Completed review",
                "description": "Review the draft",
                "completed": True,
                "priority": "Low",
                "due_date": None,
                "created_at": "2026-10-02T14:15:00",
            },
            {
                "id": 12,
                "title": "Another pending task",
                "description": "Check the release",
                "completed": False,
                "priority": "Medium",
                "due_date": "2026-12-01",
                "created_at": "2026-10-03T08:00:00",
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "tasks.json")
            save_tasks(tasks, path, next_id=13)
            loaded_tasks, next_id = load_task_data(path)

        manager = TaskManager(loaded_tasks, next_id=next_id)
        stream = io.StringIO()
        with redirect_stdout(stream):
            main.handle_view_tasks(manager)

        output = stream.getvalue()
        for value in (
            "ID: 4", "Title: Pending report",
            "Description: Prepare the summary", "Priority: High",
            "Due Date: 2026-11-05", "Status: Pending",
            "Created: 2026-10-01",
            "ID: 9", "Title: Completed review",
            "Description: Review the draft", "Priority: Low",
            "Due Date: Not set", "Status: Completed",
            "Created: 2026-10-02",
            "ID: 12", "Title: Another pending task",
            "Due Date: 2026-12-01", "Total: 3", "Pending: 2",
            "Completed: 1",
        ):
            self.assertIn(value, output)

    def test_empty_view_and_filter_show_helpful_message(self):
        stream = io.StringIO()
        with redirect_stdout(stream):
            main.handle_view_tasks(TaskManager())
        self.assertIn("No tasks found", stream.getvalue())

        with patch("builtins.input", side_effect=["", ""]), redirect_stdout(stream):
            main.handle_filter_tasks(TaskManager())
        self.assertIn("No tasks match", stream.getvalue())

    def test_full_add_view_search_filter_complete_delete_cli_flow(self):
        initial = []
        with patch("main.storage.load_task_data", return_value=(initial, 1)), \
             patch("main.storage.save_tasks") as save, \
             patch("builtins.input", side_effect=[
                 "1", "Team sync", "Discuss sprint", "high", "2026-12-20",
                 "2", "5", "sprint", "6", "High", "pending", "3", "1",
                 "4", "1", "y", "7",
             ]), redirect_stdout(io.StringIO()) as output:
            main.main()

        self.assertIn("Task added successfully with ID: 1", output.getvalue())
        self.assertIn("Found 1 matching task(s)", output.getvalue())
        self.assertIn("Found 1 matching task(s)", output.getvalue())
        self.assertIn("Task marked as completed successfully", output.getvalue())
        self.assertIn("Task deleted successfully", output.getvalue())
        self.assertGreaterEqual(save.call_count, 3)

    def test_invalid_menu_choice_does_not_crash(self):
        with patch("main.storage.load_task_data", return_value=([], 1)), \
             patch("builtins.input", side_effect=["x", "7"]), \
             redirect_stdout(io.StringIO()) as output:
            main.main()
        self.assertIn("Invalid choice", output.getvalue())
        self.assertIn("Goodbye", output.getvalue())

    def test_corrupted_task_file_is_reported_without_crashing(self):
        with patch(
            "main.storage.load_task_data",
            side_effect=StorageError("invalid JSON"),
        ), redirect_stdout(io.StringIO()) as output:
            main.main()

        self.assertIn("invalid JSON", output.getvalue())
        self.assertIn("No changes were made to the task file", output.getvalue())
        self.assertNotIn("1. Add Task", output.getvalue())

    def test_persistence_failure_does_not_report_success(self):
        manager = TaskManager()
        with patch(
            "main.storage.save_tasks",
            side_effect=StorageError("disk unavailable"),
        ), redirect_stdout(io.StringIO()) as output:
            saved = main.persist(manager)

        self.assertFalse(saved)
        self.assertIn("only in memory", output.getvalue())
        self.assertNotIn("successfully", output.getvalue())


if __name__ == "__main__":
    unittest.main()
