import os
import sqlite3


def get_db_connection(db_path: str = "nifty100.db") -> sqlite3.Connection:
    """
    Creates and returns a connection to the SQLite database.
    Explicitly enforces foreign key constraints.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    # Return rows as dictionaries for easier manipulation
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = "nifty100.db", schema_path: str = "db/schema.sql") -> None:
    """
    Initializes the SQLite database with the tables defined in the schema file.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")

    conn = sqlite3.connect(db_path)
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    db = "nifty100.db"
    print(f"Initializing database: {db}...")
    init_db(db)
    print("Database initialized successfully.")
