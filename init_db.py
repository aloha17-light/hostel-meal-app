import sqlite3

# Replace with your actual DB file if different
conn = sqlite3.connect('hostel_meals.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date TEXT,
    lunch_choice TEXT,
    dinner_choice TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

conn.commit()
conn.close()

print("Meal table created.")
