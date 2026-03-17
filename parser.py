"""
parser.py - SQL command parser for the Mini SQL Database.

Supported syntax
----------------
    CREATE TABLE <name> (<col1>, <col2>, ...)
    INSERT INTO  <name> VALUES (<val1>, <val2>, ...)
    SELECT * FROM <name> [WHERE <col> = <value>]
    SHOW TABLES
    EXIT

The parser is intentionally simple: it uses string splitting and regex
rather than a full grammar, which keeps it easy to read and extend.
"""

import re
import shlex


class ParseError(ValueError):
    """Raised when a command cannot be understood."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse(line: str) -> tuple[str, dict]:
    """
    Parse a SQL-like command line into an (action, params) tuple.

    Args:
        line: Raw user input string.

    Returns:
        A tuple of (action, params) where action is one of:
            "CREATE_TABLE", "INSERT", "SELECT", "SHOW_TABLES", "EXIT"
        and params is a dict whose keys depend on the action:

        CREATE_TABLE → {"table": str, "columns": [str, ...]}
        INSERT       → {"table": str, "values": [str, ...]}
        SELECT       → {"table": str, "where": {col: val} | None}
        SHOW_TABLES  → {}
        EXIT         → {}

    Raises:
        ParseError: If the command is empty, unrecognised, or malformed.
    """
    stripped = line.strip()
    if not stripped:
        raise ParseError("Empty input.")

    upper = stripped.upper()

    if upper == "EXIT":
        return "EXIT", {}

    if upper == "SHOW TABLES":
        return "SHOW_TABLES", {}

    if upper.startswith("CREATE TABLE"):
        return _parse_create_table(stripped)

    if upper.startswith("INSERT INTO"):
        return _parse_insert(stripped)

    if upper.startswith("SELECT"):
        return _parse_select(stripped)

    first_word = stripped.split()[0].upper()
    raise ParseError(
        f"Unrecognised command '{first_word}'. "
        "Supported: CREATE TABLE, INSERT INTO, SELECT, SHOW TABLES, EXIT."
    )


# ---------------------------------------------------------------------------
# Private parsers
# ---------------------------------------------------------------------------

def _parse_create_table(line: str) -> tuple[str, dict]:
    """
    CREATE TABLE <name> (<col1>, <col2>, ...)
    """
    pattern = re.compile(
        r"^CREATE\s+TABLE\s+(\w+)\s*\((.+)\)\s*$",
        re.IGNORECASE,
    )
    match = pattern.match(line.strip())
    if not match:
        raise ParseError(
            "Syntax error. Expected: CREATE TABLE <name> (<col1>, <col2>, ...)"
        )

    table_name = match.group(1)
    columns = [c.strip() for c in match.group(2).split(",") if c.strip()]
    if not columns:
        raise ParseError("CREATE TABLE requires at least one column.")

    return "CREATE_TABLE", {"table": table_name, "columns": columns}


def _parse_insert(line: str) -> tuple[str, dict]:
    """
    INSERT INTO <name> VALUES (<val1>, <val2>, ...)
    """
    pattern = re.compile(
        r"^INSERT\s+INTO\s+(\w+)\s+VALUES\s*\((.+)\)\s*$",
        re.IGNORECASE,
    )
    match = pattern.match(line.strip())
    if not match:
        raise ParseError(
            "Syntax error. Expected: INSERT INTO <name> VALUES (<val1>, <val2>, ...)"
        )

    table_name = match.group(1)
    raw_values = match.group(2)
    values = _split_values(raw_values)

    return "INSERT", {"table": table_name, "values": values}


def _parse_select(line: str) -> tuple[str, dict]:
    """
    SELECT * FROM <name> [WHERE <col> = <value>]

    Only SELECT * (all columns) is supported.
    """
    # With WHERE clause
    where_pattern = re.compile(
        r"^SELECT\s+\*\s+FROM\s+(\w+)\s+WHERE\s+(\w+)\s*=\s*(.+?)\s*$",
        re.IGNORECASE,
    )
    # Without WHERE clause
    base_pattern = re.compile(
        r"^SELECT\s+\*\s+FROM\s+(\w+)\s*$",
        re.IGNORECASE,
    )

    where_match = where_pattern.match(line.strip())
    if where_match:
        table_name = where_match.group(1)
        col = where_match.group(2)
        val = _coerce(where_match.group(3).strip("'\""))
        return "SELECT", {"table": table_name, "where": {col: val}}

    base_match = base_pattern.match(line.strip())
    if base_match:
        return "SELECT", {"table": base_match.group(1), "where": None}

    raise ParseError(
        "Syntax error. Expected: SELECT * FROM <name> [WHERE <col> = <value>]"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _split_values(raw: str) -> list:
    """
    Split a comma-separated value list, respecting quoted strings.

    '1, "hello world", 3.14'  →  [1, "hello world", 3.14]
    """
    # Use shlex to handle quoted tokens, then replace commas used as delimiters.
    # We temporarily replace commas inside quotes before splitting.
    try:
        lexer = shlex.shlex(raw, posix=True)
        lexer.whitespace_split = False
        lexer.whitespace = ","
        lexer.quotes = "'\""
        parts = [token.strip() for token in lexer]
    except ValueError as exc:
        raise ParseError(f"Could not parse VALUES list: {exc}") from exc

    return [_coerce(p) for p in parts if p]


def _coerce(value: str):
    """
    Attempt to cast a string token to int or float; fall back to str.

        "42"    → 42
        "3.14"  → 3.14
        "Alice" → "Alice"
    """
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value
