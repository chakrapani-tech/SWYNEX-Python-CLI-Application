# SWYNEX Python CLI Task Manager

A menu-driven task manager created for SWYNEX Python Developer Internship
Task 1. It uses Python's standard library and saves task data to a local JSON
file. The application code is split into modules for the CLI, task logic,
validation, and storage.

## Features

- Create tasks with a required title and optional description and due date.
- Set task priority to Low, Medium, or High.
- View task details and a pending/completed summary.
- Mark tasks completed and delete tasks with confirmation.
- Search titles and descriptions without case sensitivity.
- Filter by priority, completion status, or both.
- Save changes to JSON, preserving task IDs even after deleting tasks.
- Validate input and report malformed task files without replacing them.
- Continue to read the original JSON list format used by earlier versions.

## Requirements

- Python 3.8 or newer.
- No third-party packages.

## Setup and execution

Download or clone the repository, then open a terminal in the project
directory (the folder containing `main.py`). Run:

```powershell
python main.py
```

The task file is `tasks.json` beside the application modules. It is therefore
the same file regardless of the terminal's current directory.

## Menu

```text
1. Add Task
2. View Tasks
3. Complete Task
4. Delete Task
5. Search Tasks
6. Filter Tasks
7. Exit
```

When adding a task, enter a title, optional description, one of the listed
priorities, and optionally a real calendar date in `YYYY-MM-DD` format. For
filters, leave a prompt blank to include all values for that field.

Example task display:

```text
ID: 1
Title: Finish internship report
Description: Summarize Task 1
Priority: High
Due Date: 2026-10-15
Status: Pending
Created: 2026-10-09
```

## Run tests

The tests use Python's built-in `unittest` runner:

```powershell
python -m unittest discover -s tests -v
```

They exercise task operations, filters, validators, task rendering, JSON
persistence and recovery, and representative CLI flows.

## Project structure

```text
main.py                 CLI menu, task display, and user interaction
task_manager.py         In-memory task operations and filtering
storage.py              JSON loading, validation, and atomic persistence
validators.py           Reusable validation functions
tasks.json              Persisted task data
tests/test_task_manager.py  Automated unit and CLI regression tests
```
