"""
storage.py - JSON-based persistence layer for the Mini SQL Database.

Responsibilities:
    - Serialize the in-memory database (a dict of tables) to a JSON file.
    - Deserialize a JSON file back into the in-memory structure.

Database structure on disk:
    {
        "users": {
            "columns": ["id", "name", "email"],
            "rows": [
                [1, "Alice", "alice@example.com"],
                [2, "Bob",   "bob@example.com"]
            ]
        },
        ...
    }
"""

import json
import os
import tempfile


def save(filepath: str, database: dict) -> None:
    """
    Write the database dictionary to a JSON file atomically.

    The write-to-temp-then-rename pattern ensures the existing file is
    never left in a partial state if the process is interrupted.

    Args:
        filepath: Destination path for the JSON file.
        database: Dict mapping table names to their column/row data.

    Raises:
        TypeError: If the database contains non-JSON-serializable values.
        OSError:   If the file cannot be written.
    """
    dir_name = os.path.dirname(os.path.abspath(filepath))
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(database, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, filepath)
    except Exception:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise


def load(filepath: str) -> dict:
    """
    Read a JSON file and return the database dictionary.

    Returns an empty dict if the file does not exist yet, so the first
    run starts cleanly without requiring a pre-created file.

    Args:
        filepath: Path to the JSON database file.

    Returns:
        The deserialized database dict, or {} if the file is absent.

    Raises:
        ValueError: If the file exists but contains invalid JSON.
        OSError:    If the file exists but cannot be read.
    """
    if not os.path.exists(filepath):
        return {}

    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Database file '{filepath}' is corrupted: {exc}"
            ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected a JSON object in '{filepath}', "
            f"got {type(data).__name__}."
        )
    return data
