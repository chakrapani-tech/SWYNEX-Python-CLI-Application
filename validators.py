"""
validators.py

Responsible for reusable input validation used throughout the SWYNEX
Task Manager. Keeping validation here avoids duplicating checks in
main.py and task_manager.py, and ensures invalid user input is caught
before it can crash the application.
"""

from datetime import datetime
from typing import Iterable, Optional

# Canonical, display-ready priority labels. Comparisons against user
# input are case-insensitive (see validate_priority).
VALID_PRIORITIES = ("Low", "Medium", "High")

# The only due-date format the application accepts from the user.
DUE_DATE_FORMAT = "%Y-%m-%d"


def validate_menu_choice(choice: str, valid_choices: Iterable[str]) -> bool:
    """
    Check whether a menu choice is one of the accepted options.

    Args:
        choice: Raw text entered by the user.
        valid_choices: The set/collection of acceptable choice strings.

    Returns:
        True if the (stripped) choice is valid, False otherwise.
    """
    return choice.strip() in valid_choices


def validate_task_title(title: str) -> bool:
    """
    Check whether a task title is non-empty.

    Args:
        title: Raw text entered by the user.

    Returns:
        True if the title contains non-whitespace characters.
    """
    return bool(title and title.strip())


def parse_task_id(raw_id: str) -> Optional[int]:
    """
    Safely convert user-entered text into a positive task ID.

    Args:
        raw_id: Raw text entered by the user.

    Returns:
        The parsed positive integer ID, or None if the input is not a
        valid positive whole number (this never raises an exception).
    """
    raw_id = raw_id.strip()
    if not raw_id:
        return None

    try:
        task_id = int(raw_id)
    except ValueError:
        return None

    if task_id <= 0:
        return None

    return task_id


def validate_priority(raw_priority: str) -> Optional[str]:
    """
    Validate and normalize a task priority.

    Accepts 'Low', 'Medium', or 'High' in any letter case (extra
    surrounding whitespace is ignored).

    Args:
        raw_priority: Raw text entered by the user.

    Returns:
        The canonical priority string ('Low', 'Medium', or 'High') if
        the input matches one of the accepted priorities, or None if it
        doesn't.
    """
    normalized = raw_priority.strip().lower()
    for priority in VALID_PRIORITIES:
        if normalized == priority.lower():
            return priority
    return None


def parse_due_date(raw_date: str) -> Optional[str]:
    """
    Validate and normalize an optional due date.

    Args:
        raw_date: Raw text entered by the user, expected in YYYY-MM-DD
            format (e.g. '2026-10-01').

    Returns:
        The date normalized to zero-padded YYYY-MM-DD form if raw_date
        is a real calendar date in that format, or None if raw_date is
        blank or is not a valid date (this never raises an exception,
        so obviously invalid dates like '2026-13-45' are simply
        rejected rather than crashing the application).
    """
    raw_date = raw_date.strip()
    if not raw_date:
        return None

    try:
        parsed_date = datetime.strptime(raw_date, DUE_DATE_FORMAT).date()
    except ValueError:
        return None

    if parsed_date.isoformat() != raw_date:
        return None
    return parsed_date.isoformat()


def validate_search_query(query: str) -> bool:
    """
    Check whether a search query contains meaningful (non-blank) text.

    Args:
        query: Raw text entered by the user.

    Returns:
        True if the query contains non-whitespace characters.
    """
    return bool(query and query.strip())


def validate_yes_no(response: str) -> Optional[bool]:
    """
    Interpret a yes/no confirmation response.

    Args:
        response: Raw text entered by the user.

    Returns:
        True for an affirmative response ('y'/'yes'), False for a
        negative response ('n'/'no'), or None if the response is not
        recognized.
    """
    normalized = response.strip().lower()
    if normalized in ("y", "yes"):
        return True
    if normalized in ("n", "no"):
        return False
    return None
