import sqlite3

conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

try:
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    if users:
        for user in users:
            print(dict(user))
    else:
        print("✅ No users found in the database.")
except Exception as e:
    print("❌ Error:", e)

conn.close()
