import sqlite3
from contextlib import closing

def init_db(db_path="expenses.db"):
    with closing(sqlite3.connect(db_path)) as conn:
        with conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    store TEXT,
                    items TEXT,
                    amount REAL,
                    category TEXT
                )
            ''')

def insert_expense(date, store, items, amount, category, db_path="expenses.db"):
    with closing(sqlite3.connect(db_path)) as conn:
        with conn:
            conn.execute(
                "INSERT INTO expenses (date, store, items, amount, category) VALUES (?, ?, ?, ?, ?)",
                (date, store, items, amount, category)
            )

def fetch_expenses(db_path="expenses.db"):
    with closing(sqlite3.connect(db_path)) as conn:
        with conn:
            return conn.execute("SELECT id, date, store, items, amount, category FROM expenses").fetchall()

def delete_expense(expense_id, db_path="expenses.db"):
    with closing(sqlite3.connect(db_path)) as conn:
        with conn:
            conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))

def fetch_expenses_by_month(month, db_path="expenses.db"):
    """Fetch expenses for a given month (YYYY-MM)."""
    with closing(sqlite3.connect(db_path)) as conn:
        with conn:
            return conn.execute(
                "SELECT id, date, store, items, amount, category FROM expenses WHERE substr(date, 1, 7) = ?",
                (month,)
            ).fetchall()

def update_expense(expense_id, date, store, items, amount, category, db_path="expenses.db"):
    with closing(sqlite3.connect(db_path)) as conn:
        with conn:
            conn.execute(
                "UPDATE expenses SET date = ?, store = ?, items = ?, amount = ?, category = ? WHERE id = ?",
                (date, store, items, amount, category, expense_id)
            ) 