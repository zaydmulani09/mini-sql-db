"""
database.py - Core engine for the Mini SQL Database.

Manages an in-memory dictionary of tables and exposes operations that
mirror a subset of SQL semantics:

    CREATE TABLE  →  Database.create_table()
    INSERT INTO   →  Database.insert()
    SELECT *      →  Database.select()

Persistence is delegated entirely to storage.py.
"""

import storage


class DatabaseError(Exception):
    """Raised for semantic errors such as duplicate tables or bad column counts."""


class Database:
    """
    In-memory relational database backed by a JSON file.

    Internal structure of self._db:
        {
            "<table_name>": {
                "columns": ["col1", "col2", ...],
                "rows":    [[val1, val2, ...], ...]
            }
        }
    """

    def __init__(self, filepath: str = "minidb.json") -> None:
        self.filepath = filepath
        self._db: dict = {}

    # ------------------------------------------------------------------
    # DDL
    # ------------------------------------------------------------------

    def create_table(self, table_name: str, columns: list[str]) -> None:
        """
        Define a new table with the given column names.

        Args:
            table_name: Unique name for the table.
            columns:    Ordered list of column name strings.

        Raises:
            DatabaseError: If the table already exists or columns is empty.
        """
        if not columns:
            raise DatabaseError("A table must have at least one column.")
        if table_name in self._db:
            raise DatabaseError(f"Table '{table_name}' already exists.")

        self._db[table_name] = {"columns": columns, "rows": []}

    # ------------------------------------------------------------------
    # DML - write
    # ------------------------------------------------------------------

    def insert(self, table_name: str, values: list) -> None:
        """
        Append a row to an existing table.

        Args:
            table_name: Target table.
            values:     Ordered list of values matching the table's columns.

        Raises:
            DatabaseError: If the table does not exist or the value count
                           does not match the column count.
        """
        table = self._get_table(table_name)
        expected = len(table["columns"])
        if len(values) != expected:
            raise DatabaseError(
                f"Table '{table_name}' has {expected} column(s), "
                f"but {len(values)} value(s) were provided."
            )
        table["rows"].append(list(values))

    # ------------------------------------------------------------------
    # DML - read
    # ------------------------------------------------------------------

    def select(self, table_name: str, where: dict | None = None) -> list[dict]:
        """
        Return rows from a table as a list of column→value dicts.

        Args:
            table_name: Source table.
            where:      Optional filter dict, e.g. {"name": "Alice"}.
                        Only rows where ALL key-value pairs match are returned.
                        Comparison is case-insensitive for string values.

        Returns:
            List of row dicts.  Empty list if no rows match.

        Raises:
            DatabaseError: If the table does not exist.
        """
        table = self._get_table(table_name)
        columns = table["columns"]

        results = []
        for row in table["rows"]:
            record = dict(zip(columns, row))
            if where and not self._row_matches(record, where):
                continue
            results.append(record)
        return results

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Persist the current database state to disk."""
        storage.save(self.filepath, self._db)

    def load(self) -> None:
        """Replace the in-memory state with the contents of the database file."""
        self._db = storage.load(self.filepath)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def list_tables(self) -> list[str]:
        """Return a sorted list of all table names."""
        return sorted(self._db.keys())

    def get_columns(self, table_name: str) -> list[str]:
        """Return the column names for a table."""
        return list(self._get_table(table_name)["columns"])

    # ------------------------------------------------------------------
    # Context manager  (with Database(...) as db:)
    # ------------------------------------------------------------------

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.save()
        return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_table(self, table_name: str) -> dict:
        if table_name not in self._db:
            raise DatabaseError(f"Table '{table_name}' does not exist.")
        return self._db[table_name]

    @staticmethod
    def _row_matches(record: dict, where: dict) -> bool:
        for col, val in where.items():
            actual = record.get(col)
            # Case-insensitive comparison for strings.
            if isinstance(actual, str) and isinstance(val, str):
                if actual.lower() != val.lower():
                    return False
            elif actual != val:
                return False
        return True
