# Source: Jennifer Campbell
# Course: University of Toronto, CSC271H, Winter 2026
# Description: Provided course code, used with permission.

import sqlite3
import pandas as pd

def create_database(db_name: str) -> None:
    """Create a new SQLite database file named db_name."""
    conn = sqlite3.connect(db_name)
    conn.close()


def connect(db_name: str) -> sqlite3.Connection:
    """Return a connection to the SQLite database db_name with foreign
    keys enabled.
    """

    conn = sqlite3.connect(db_name)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def add_table(conn: sqlite3.Connection, sql_create: str) -> None:
    """Create a new table in the database connected via conn using
    the SQL statement sql_create."""
    conn.execute(sql_create)
    conn.commit()


def run_sql(conn: sqlite3.Connection, sql: str,
            params: tuple | dict | None = None) -> pd.DataFrame | None:
    """Run the SQL statement sql using connection conn. Return a DataFrame
    containing the query results if sql is a SELECT statement, 
    or None otherwise.
    """

    if sql.strip().upper().startswith("SELECT"):
        return pd.read_sql_query(sql, conn, params=params)
    else:
        if params is None:
            conn.execute(sql)
        else:
            conn.execute(sql, params)
        conn.commit()
        return None
    