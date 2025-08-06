# --- init_db.py (Final Version for Render) ---

import sqlite3
import os

# --- Database Path Configuration ---
# Hardcode the path to the persistent disk on Render.
DB_PATH = '/data/hostel_meals.db'

def initialize_database():
    """Initializes the database in the persistent disk path."""
    # The database file will be created in the /data directory on Render
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"Ensuring tables exist in '{DB_PATH}'...")

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        is_admin INTEGER NOT NULL DEFAULT 0
    )
    ''')
    print("✅ 'users' table checked/created.")

    # Create meals table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS meals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        lunch_choice TEXT,
        dinner_choice TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    print("✅ 'meals' table checked/created.")

    # Create a default admin user if one doesn't exist
    cursor.execute("SELECT * FROM users WHERE email = ?", ('admin@example.com',))
    if not cursor.fetchone():
        cursor.execute('''
        INSERT INTO users (name, email, password, is_admin)
        VALUES (?, ?, ?, ?)
        ''', ('Admin', 'admin@example.com', 'admin123', 1))
        print("✅ Default admin user created.")
    else:
        print("ℹ️ Admin user already exists.")

    conn.commit()
    conn.close()
    print("--- Database initialization check complete! ---")

if __name__ == '__main__':
    initialize_database()