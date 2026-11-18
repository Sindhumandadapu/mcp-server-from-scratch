
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "database" / "smarttools.db"


def initialize_database():
    """Create the database and initialize sample tables."""

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                salary REAL NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            )
        """)

        connection.executemany("""
            INSERT OR IGNORE INTO employees
            (id, name, department, salary, email)
            VALUES (?, ?, ?, ?, ?)
        """, [
            (1, "Rahul", "Engineering", 65000, "rahul@example.com"),
            (2, "Priya", "HR", 45000, "priya@example.com"),
            (3, "Arjun", "Engineering", 72000, "arjun@example.com"),
            (4, "Sneha", "Finance", 55000, "sneha@example.com"),
        ])

        connection.executemany("""
            INSERT OR IGNORE INTO products
            (id, name, category, price, stock)
            VALUES (?, ?, ?, ?, ?)
        """, [
            (1, "Laptop", "Electronics", 65000, 10),
            (2, "Keyboard", "Accessories", 1500, 25),
            (3, "Mouse", "Accessories", 800, 40),
            (4, "Monitor", "Electronics", 18000, 12),
        ])

    return DATABASE_PATH
