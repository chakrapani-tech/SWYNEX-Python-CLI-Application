# SWYNEX Python CLI Application

## Description

This is a command-line **Task Manager** application developed as part of
**SWYNEX Technologies – Internship Task 1**. It lets a user add, view,
search, complete, and delete tasks — each with a priority and an optional
due date — from a simple text-based menu, with all data saved to a local
JSON file so tasks persist between runs.

The project is intentionally built using only Python's standard library,
with a clean separation between the CLI, business logic, data persistence,
and input validation.

## Features

- Menu-driven command-line interface (Add, View, Complete, Delete, Search, Exit)
- Add tasks with a required title, an optional description, a required
  priority (Low / Medium / High), and an optional due date
- Automatically generated, unique task IDs
- View all tasks in a clean, readable format with priority, due date,
  status, and creation date
- A task summary (total / pending / completed counts) shown after viewing
- Search tasks by title or description text, case-insensitively
- Mark tasks as completed
- Delete tasks, with a yes/no confirmation prompt before removal
- Automatic JSON file creation if `tasks.json` does not exist
- Tasks are loaded on startup and saved after every change
- Backward-compatible loading: tasks saved by older versions of this app
  (without priority/due date) load safely with sensible defaults filled in
- Input validation for menu choices, task titles, task IDs, priorities,
  due dates, search text, and yes/no responses
- Exception handling for invalid input, missing files, corrupted JSON,
  and file read/write errors — the app never crashes on bad input

## Technologies Used

- Python (standard library only)
- JSON (via Python's built-in `json` module)

## Project Structure

```text
SWYNEX-Python-CLI-Application/
│
├── main.py             # Entry point: menu loop, user I/O, wires everything together
├── task_manager.py     # TaskManager class: add/find/complete/delete task logic
├── storage.py          # Loading and saving tasks.json, file-related error handling
├── validators.py       # Reusable input validation functions
├── tasks.json          # JSON data file where tasks are persisted
├── README.md           # This file
├── requirements.txt    # Dependency notes (standard library only)
└── .gitignore          # Files/folders excluded from Git
```

**main.py** — Starts the application, displays the menu, reads user input,
and calls into `task_manager` and `storage` as needed. Contains no
persistence or business-rule logic itself.

**task_manager.py** — Defines the `TaskManager` class, which holds the
in-memory list of tasks and implements adding, finding, completing,
deleting, and searching tasks, including unique ID generation and
filling in default priority/due-date values for older task records.

**storage.py** — Handles all reading and writing of `tasks.json`,
including creating the file if it's missing and raising a clear
`StorageError` if the file is unreadable, unwritable, or contains invalid
JSON. This module is unaware of the task schema, so it needed no changes
to support the new fields.

**validators.py** — Small, reusable functions that validate menu choices,
task titles, task ID input, task priority, due dates, search text, and
yes/no confirmation responses, so invalid input can never crash the app.

## Installation

1. Clone or download this repository.
2. Open the project folder in a terminal:
   ```bash
   cd SWYNEX-Python-CLI-Application
   ```

No installation step beyond having Python itself is required, since the
project has no external dependencies.

## Requirements

- Python 3.8 or newer (developed and tested on Python 3.12)
- No third-party packages (see `requirements.txt`)

## Running the Application

```bash
python main.py
```

On some systems (particularly Linux/macOS where `python` points to
Python 2), use:

```bash
python3 main.py
```

## Usage

When you run the application, you'll see a menu with six options:

- **1. Add Task** — Enter a title (required), a description (optional),
  a priority (required: `Low`, `Medium`, or `High`, case-insensitive),
  and a due date (optional, in `YYYY-MM-DD` format). The task is saved
  with a new unique ID. An invalid priority cancels the whole add; an
  invalid due date only skips the due date, so a minor date typo doesn't
  cost you the rest of the task.
- **2. View Tasks** — Lists every task with its ID, title, description,
  priority, due date, status (Pending/Completed), and creation date,
  followed by a short summary of total/pending/completed counts. If
  there are no tasks, a friendly message is shown instead.
- **3. Complete Task** — Enter the ID of the task to mark as completed.
  If the ID doesn't exist, you'll see `Task not found.`
- **4. Delete Task** — Enter the ID of the task to remove. You'll be
  asked to confirm with `y` or `n` before it's actually deleted.
- **5. Search Tasks** — Enter any text; the app shows every task whose
  title or description contains that text, ignoring letter case. If
  nothing matches, a clear "no tasks found" message is shown instead.
- **6. Exit** — Closes the application.

All changes (adding, completing, deleting) are saved to `tasks.json`
immediately, so your tasks are still there the next time you run the
program.

### Example: viewing tasks

```text
----------------------------------------
ID: 1
Title: Finish internship report
Description: Summarize Task 1 and Task 2
Priority: High
Due Date: 2026-10-05
Status: Pending
Created: 2026-09-27
----------------------------------------
Summary:
Total: 1
Pending: 1
Completed: 0
```

## Error Handling

The application is designed to never crash on normal invalid input or
common file problems:

- **Invalid menu choices** (letters, out-of-range numbers) show an error
  and re-display the menu instead of crashing.
- **Non-numeric or invalid task IDs** are caught before use and produce a
  clear error message.
- **Empty task titles** are rejected with an error, and the task is not
  added.
- **Invalid priorities** (anything other than Low/Medium/High) are
  rejected with an error, and the task is not added.
- **Invalid due dates** (bad format, or an impossible calendar date like
  `2026-13-45` or `2026-02-30`) are caught and reported, and the task is
  still added without a due date rather than being lost entirely.
- **Empty search text** is rejected with a clear error instead of
  searching for nothing.
- **Unrecognized yes/no responses** during delete confirmation cancel the
  deletion safely rather than guessing.
- **Missing `tasks.json`** is handled by automatically creating a new,
  empty file.
- **Corrupted or invalid JSON** in `tasks.json` is caught, a clear warning
  is shown, and the app continues with an empty in-memory task list for
  that session without overwriting the damaged file until you save new
  changes yourself.
- **File read/write errors** (e.g. permission problems) are caught and
  reported with a clear message instead of an unhandled traceback.

## Learning Outcomes

This project was built to demonstrate:

- Python functions and clear single-responsibility design
- Modular programming across multiple files (`main`, `task_manager`,
  `storage`, `validators`)
- Input validation, including date/calendar validation
- Exception handling (specific exceptions, not bare `except:`)
- JSON-based file persistence, including backward-compatible data migration
- Building a usable, menu-driven CLI application

## Internship

**SWYNEX Technologies – Internship Task 1**

## Note on Task IDs

Task IDs are generated as one greater than the current highest ID among
existing tasks. This keeps IDs unique among all tasks present at any
given time (there are never two tasks with the same ID simultaneously).
One side effect of this simple scheme: if the task with the highest ID is
deleted, a future new task can be assigned that same numeric ID again.
This is a normal trade-off for a lightweight, dependency-free ID scheme
and does not affect correctness of any single session's data.

## Note on Backward Compatibility

If your `tasks.json` contains tasks saved before priority and due dates
were added to this app, they will still load correctly: missing fields
are automatically filled in with sensible defaults (`Medium` priority,
no due date) the first time the file is loaded. Nothing needs to be
edited by hand, and existing Add/View/Complete/Delete behavior is
unchanged for those tasks.
