# Mini SQL Database

A custom relational database engine built in Python from scratch. Supports table creation, row insertion, and record querying through a SQL-like syntax, with JSON-based file persistence and an interactive command-line interface. Designed as a software engineering project to demonstrate layered architecture, clean module separation, and fundamental database concepts.

---

## Features

- **DDL support** — define tables with named columns via `CREATE TABLE`
- **DML support** — append records with `INSERT INTO`, query with `SELECT *`
- **WHERE filtering** — retrieve specific records using equality conditions
- **File persistence** — database state is saved to and loaded from a JSON file automatically
- **Atomic writes** — file saves use a write-then-rename strategy to prevent data corruption
- **Interactive CLI** — REPL loop with readable ASCII table output
- **Type coercion** — integer and float values are detected automatically; strings require no quoting
- **Zero dependencies** — built entirely on the Python standard library

---

## Project Structure

```
minisqldb/
├── main.py        # CLI entry point and REPL loop
├── database.py    # Table management and query execution
├── parser.py      # SQL command tokenizer and validator
├── storage.py     # JSON file persistence layer
└── minidb.json    # Auto-created on first save
```

### Architecture

Each module has a single, well-defined responsibility:

```
main.py
  └── parser.py     (parse raw input into structured commands)
  └── database.py   (execute commands against in-memory tables)
        └── storage.py  (read/write the database file)
```

---

## Requirements

- Python 3.10 or higher
- No third-party packages required

---

## Installation

```bash
git clone https://github.com/your-username/minisqldb.git
cd minisqldb
```

No virtual environment or `pip install` needed.

---

## Running the Database

```bash
python main.py
```

To use a custom database file:

```bash
python main.py myproject.json
```

On startup, the engine loads any existing data from the file. On `EXIT`, all changes are written back to disk.

---

## Supported Commands

| Command | Description |
|---|---|
| `CREATE TABLE <n> (<col1>, <col2>, ...)` | Define a new table with named columns |
| `INSERT INTO <n> VALUES (<val1>, <val2>, ...)` | Append a row to a table |
| `SELECT * FROM <n>` | Retrieve all rows from a table |
| `SELECT * FROM <n> WHERE <col> = <value>` | Retrieve rows matching a condition |
| `SHOW TABLES` | List all tables and their columns |
| `EXIT` | Save the database to disk and quit |

---

## Example Session

```
$ python main.py

Mini SQL Database
Database file : minidb.json
Tables loaded : 0
Type EXIT to quit, or enter a SQL command.

sql> CREATE TABLE users (id, name, email)
Table 'users' created with columns: id, name, email.

sql> INSERT INTO users VALUES (1, Alice, alice@example.com)
1 row inserted into 'users'.

sql> INSERT INTO users VALUES (2, Bob, bob@example.com)
1 row inserted into 'users'.

sql> INSERT INTO users VALUES (3, Carol, carol@example.com)
1 row inserted into 'users'.

sql> SELECT * FROM users
+----+-------+----------------------+
| id | name  | email                |
+----+-------+----------------------+
| 1  | Alice | alice@example.com    |
| 2  | Bob   | bob@example.com      |
| 3  | Carol | carol@example.com    |
+----+-------+----------------------+
  3 row(s)

sql> SELECT * FROM users WHERE name = Alice
+----+-------+-------------------+
| id | name  | email             |
+----+-------+-------------------+
| 1  | Alice | alice@example.com |
+----+-------+-------------------+
  1 row(s)

sql> SHOW TABLES
  users  (id, name, email)

sql> EXIT
Changes saved. Goodbye!
```

---

## Persistence Format

The database is stored as a plain JSON file, making it easy to inspect and version-control:

```json
{
  "users": {
    "columns": ["id", "name", "email"],
    "rows": [
      [1, "Alice", "alice@example.com"],
      [2, "Bob",   "bob@example.com"],
      [3, "Carol", "carol@example.com"]
    ]
  }
}
```

---

## Error Handling

The engine distinguishes between parse errors (malformed SQL) and runtime errors (semantic violations), surfacing both without crashing the session:

```
sql> INSERT INTO users VALUES (1, 2)
[error] Table 'users' has 3 column(s), but 2 value(s) were provided.

sql> SELECT * FROM orders
[error] Table 'orders' does not exist.

sql> SELEKT * FROM users
[parse error] Unrecognised command 'SELEKT'. Supported: CREATE TABLE, INSERT INTO, SELECT, SHOW TABLES, EXIT.
```

---

## Known Limitations

- `SELECT *` only — column projection (e.g. `SELECT name FROM ...`) is not yet supported
- Single equality `WHERE` conditions only — `AND`, `OR`, and comparison operators (`>`, `<`) are not implemented
- No `UPDATE` or `DELETE` statements
- No primary key enforcement or uniqueness constraints
- Designed for single-process use — concurrent access is not supported

---

## Extending the Project

The layered architecture makes it straightforward to add features incrementally:

- **New SQL commands** — add a new `_parse_*` function in `parser.py` and a corresponding method in `database.py`
- **Column projections** — extend `Database.select()` to accept a column list and filter the output dicts
- **WHERE operators** — update `_parse_select()` in `parser.py` to recognise `>`, `<`, `!=` and wire them into `Database._row_matches()`
- **Alternative storage backends** — swap out `storage.py` for a SQLite or CSV implementation without touching any other module

---

## License

MIT License. See `LICENSE` for details.
