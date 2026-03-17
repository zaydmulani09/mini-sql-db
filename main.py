"""
main.py - Interactive CLI for the Mini SQL Database.

Usage
-----
    python main.py                   # default file: minidb.json
    python main.py myproject.json    # custom database file

Supported commands
------------------
    CREATE TABLE users (id, name, email)
    INSERT INTO users VALUES (1, Alice, alice@example.com)
    SELECT * FROM users
    SELECT * FROM users WHERE name = Alice
    SHOW TABLES
    EXIT
"""

import sys

from database import Database, DatabaseError
from parser import ParseError, parse


def _print_table(rows: list[dict]) -> None:
    """Render a list of row dicts as an ASCII table."""
    if not rows:
        print("(no rows)")
        return

    columns = list(rows[0].keys())
    col_widths = {c: len(c) for c in columns}
    for row in rows:
        for col in columns:
            col_widths[col] = max(col_widths[col], len(str(row[col])))

    def _fmt_row(values):
        return "| " + " | ".join(
            str(v).ljust(col_widths[c]) for c, v in zip(columns, values)
        ) + " |"

    separator = "+-" + "-+-".join("-" * col_widths[c] for c in columns) + "-+"
    print(separator)
    print(_fmt_row(columns))
    print(separator)
    for row in rows:
        print(_fmt_row([row[c] for c in columns]))
    print(separator)
    print(f"  {len(rows)} row(s)")


def run(db: Database) -> None:
    """Main REPL loop."""
    print("Mini SQL Database")
    print(f"Database file : {db.filepath}")
    print(f"Tables loaded : {len(db.list_tables())}")
    print("Type EXIT to quit, or enter a SQL command.\n")

    while True:
        try:
            line = input("sql> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nInterrupted. Saving...")
            db.save()
            break

        if not line:
            continue

        # ---- Parse -------------------------------------------------------
        try:
            action, params = parse(line)
        except ParseError as exc:
            print(f"[parse error] {exc}\n")
            continue

        # ---- Execute -----------------------------------------------------
        try:
            if action == "EXIT":
                db.save()
                print("Changes saved. Goodbye!")
                break

            elif action == "SHOW_TABLES":
                tables = db.list_tables()
                if tables:
                    for name in tables:
                        cols = db.get_columns(name)
                        print(f"  {name}  ({', '.join(cols)})")
                else:
                    print("  (no tables)")

            elif action == "CREATE_TABLE":
                db.create_table(params["table"], params["columns"])
                print(
                    f"Table '{params['table']}' created "
                    f"with columns: {', '.join(params['columns'])}."
                )

            elif action == "INSERT":
                db.insert(params["table"], params["values"])
                print(f"1 row inserted into '{params['table']}'.")

            elif action == "SELECT":
                rows = db.select(params["table"], where=params["where"])
                _print_table(rows)

        except DatabaseError as exc:
            print(f"[error] {exc}")

        print()  # Blank line between commands for readability.


def main() -> None:
    filepath = sys.argv[1] if len(sys.argv) > 1 else "minidb.json"
    db = Database(filepath)

    try:
        db.load()
    except (ValueError, OSError) as exc:
        print(f"[warning] Could not load '{filepath}': {exc}")
        print("Starting with an empty database.\n")

    run(db)


if __name__ == "__main__":
    main()
