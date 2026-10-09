"""
main.py

Entry point for the SWYNEX Task Manager CLI application.

Responsible for starting the application, displaying the menu, and
running the main input loop. Task logic lives in task_manager.py,
persistence lives in storage.py, and input checks live in validators.py.
"""

from datetime import datetime
from typing import Any, Dict, List

import storage
from storage import StorageError
from task_manager import DEFAULT_PRIORITY, TaskManager
from validators import (
    parse_due_date,
    parse_task_id,
    validate_menu_choice,
    validate_priority,
    validate_search_query,
    validate_task_title,
    validate_yes_no,
)

MENU_TEXT = """
========================================
          SWYNEX TASK MANAGER
========================================
1. Add Task
2. View Tasks
3. Complete Task
4. Delete Task
5. Search Tasks
6. Filter Tasks
7. Exit
========================================
"""

VALID_CHOICES = {"1", "2", "3", "4", "5", "6", "7"}


def display_menu() -> None:
    """Print the main menu to the console."""
    print(MENU_TEXT)


def format_created_date(created_at: str) -> str:
    """
    Format a stored ISO timestamp as YYYY-MM-DD for display.

    Falls back to showing the raw value (or 'Unknown') if the stored
    timestamp is missing or cannot be parsed, so a bad timestamp never
    crashes the display.
    """
    try:
        return datetime.fromisoformat(created_at).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return created_at or "Unknown"


def format_due_date(due_date: Any) -> str:
    """Format a task's due date for display, handling a missing date."""
    return due_date if due_date else "Not set"


def print_task(task: Dict[str, Any]) -> None:
    """
    Print a single task's details in the application's standard format.

    Shared by View Tasks and Search Tasks so both stay in sync and the
    display logic exists in exactly one place.
    """
    status = "Completed" if task.get("completed") else "Pending"
    print(f"ID: {task['id']}")
    print(f"Title: {task['title']}")
    print(f"Description: {task.get('description') or '(none)'}")
    print(f"Priority: {task.get('priority', DEFAULT_PRIORITY)}")
    print(f"Due Date: {format_due_date(task.get('due_date'))}")
    print(f"Status: {status}")
    print(f"Created: {format_created_date(task.get('created_at', ''))}")
    print("-" * 40)


def print_task_summary(tasks: List[Dict[str, Any]]) -> None:
    """Print a short count of total, pending, and completed tasks."""
    total = len(tasks)
    completed = sum(1 for task in tasks if task.get("completed"))
    pending = total - completed
    print("Summary:")
    print(f"Total: {total}")
    print(f"Pending: {pending}")
    print(f"Completed: {completed}")


def persist(manager: TaskManager) -> bool:
    """Save tasks and report whether the update reached persistent storage."""
    try:
        storage.save_tasks(manager.get_all_tasks(), next_id=manager.next_id)
    except StorageError as error:
        print(f"Error: The change is only in memory; saving to disk failed. {error}")
        return False
    return True


def handle_add_task(manager: TaskManager) -> None:
    """Prompt for a new task's details, validate, add it, and save."""
    title = input("Enter task title: ")
    if not validate_task_title(title):
        print("Error: Task title cannot be empty. Task was not added.")
        return

    description = input("Enter task description (optional): ")

    raw_priority = input("Enter task priority (Low/Medium/High): ")
    priority = validate_priority(raw_priority)
    if priority is None:
        print(
            "Error: Priority must be Low, Medium, or High. Task was not added."
        )
        return

    raw_due_date = input("Enter due date (YYYY-MM-DD, optional): ")
    due_date = None
    if raw_due_date.strip():
        due_date = parse_due_date(raw_due_date)
        if due_date is None:
            print(
                f"Warning: '{raw_due_date.strip()}' is not a valid date in "
                "YYYY-MM-DD format. The task will be added without a due date."
            )

    task = manager.add_task(title, description, priority, due_date)
    if persist(manager):
        print(f"Task added successfully with ID: {task['id']}")
    else:
        print(f"Task added in memory with ID: {task['id']}, but was not saved.")


def handle_view_tasks(manager: TaskManager) -> None:
    """Display all tasks in a readable, consistent format, with a summary."""
    tasks = manager.get_all_tasks()
    if not tasks:
        print("No tasks found. Add a task to get started.")
        return

    print("-" * 40)
    for task in tasks:
        print_task(task)

    print_task_summary(tasks)


def handle_search_tasks(manager: TaskManager) -> None:
    """Prompt for search text and display tasks whose title or description match."""
    query = input("Enter search text (title or description): ")
    if not validate_search_query(query):
        print("Error: Search text cannot be empty.")
        return

    matches = manager.search_tasks(query)
    if not matches:
        print(f"No tasks found matching '{query.strip()}'.")
        return

    print(f"Found {len(matches)} matching task(s):")
    print("-" * 40)
    for task in matches:
        print_task(task)


def handle_filter_tasks(manager: TaskManager) -> None:
    """Filter tasks by optional priority and completion status."""
    raw_priority = input("Priority (Low/Medium/High, or blank for any): ")
    priority = None
    if raw_priority.strip():
        priority = validate_priority(raw_priority)
        if priority is None:
            print("Error: Priority must be Low, Medium, or High.")
            return

    raw_status = input("Status (pending/completed, or blank for any): ")
    status = raw_status.strip().lower()
    if status not in ("", "pending", "completed"):
        print("Error: Status must be pending or completed.")
        return

    completed = None if not status else status == "completed"
    matches = manager.filter_tasks(priority=priority, completed=completed)
    if not matches:
        print("No tasks match the selected filters.")
        return

    print(f"Found {len(matches)} matching task(s):")
    print("-" * 40)
    for task in matches:
        print_task(task)


def handle_complete_task(manager: TaskManager) -> None:
    """Prompt for a task ID and mark that task as completed."""
    raw_id = input("Enter task ID to mark as completed: ")
    task_id = parse_task_id(raw_id)
    if task_id is None:
        print("Error: Please enter a valid positive task ID (numbers only).")
        return

    if manager.complete_task(task_id):
        if persist(manager):
            print("Task marked as completed successfully.")
        else:
            print("Task marked completed in memory, but was not saved.")
    else:
        print("Task not found.")


def handle_delete_task(manager: TaskManager) -> None:
    """Prompt for a task ID, confirm, and delete that task if confirmed."""
    raw_id = input("Enter task ID to delete: ")
    task_id = parse_task_id(raw_id)
    if task_id is None:
        print("Error: Please enter a valid positive task ID (numbers only).")
        return

    if manager.find_task(task_id) is None:
        print("Task not found.")
        return

    confirmation = input("Are you sure you want to delete this task? (y/n): ")
    answer = validate_yes_no(confirmation)

    if answer is None:
        print("Invalid response. Deletion cancelled.")
        return
    if not answer:
        print("Deletion cancelled.")
        return

    manager.delete_task(task_id)
    if persist(manager):
        print("Task deleted successfully.")
    else:
        print("Task deleted in memory, but the deletion was not saved.")


def load_initial_tasks() -> TaskManager:
    """
    Load tasks from disk at startup.

    If the tasks file is missing, storage.load_task_data creates it. A
    storage error is propagated so the caller can stop rather than allowing
    a later save to replace an unreadable or malformed file.
    """
    tasks, next_id = storage.load_task_data()
    return TaskManager(tasks, next_id=next_id)


def main() -> None:
    """Run the SWYNEX Task Manager CLI loop."""
    print("Welcome to SWYNEX Task Manager!")
    try:
        manager = load_initial_tasks()
    except StorageError as error:
        print(f"Unable to load saved tasks: {error}")
        print("No changes were made to the task file. Exiting safely.")
        return

    actions = {
        "1": handle_add_task,
        "2": handle_view_tasks,
        "3": handle_complete_task,
        "4": handle_delete_task,
        "5": handle_search_tasks,
        "6": handle_filter_tasks,
    }

    while True:
        display_menu()
        choice = input("Enter your choice: ")

        if not validate_menu_choice(choice, VALID_CHOICES):
            print("Invalid choice. Please enter a number between 1 and 7.")
            continue

        choice = choice.strip()
        if choice == "7":
            print("Thank you for using SWYNEX Task Manager. Goodbye!")
            break

        actions[choice](manager)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user. Goodbye!")
    except EOFError:
        print("\nInput stream closed. Exiting.")
