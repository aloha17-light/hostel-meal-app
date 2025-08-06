from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import date, datetime
import os

# --- Environment-Aware Database Path ---
if os.path.exists('/data'):
    DB_PATH = '/data/hostel_meals.db' # Path for Render's persistent disk
else:
    DB_PATH = 'hostel_meals.db' # Path for local development

app = Flask(__name__)
app.secret_key = 'a_very_secret_key_please_change_this'

# --- Database Initialization Function ---
def init_database():
    """Checks for DB and creates tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Ensuring database tables exist at {DB_PATH}...")

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
    
    # Create a default admin user if one doesn't exist
    cursor.execute("SELECT * FROM users WHERE email = ?", ('admin@example.com',))
    if not cursor.fetchone():
        cursor.execute('''
        INSERT INTO users (name, email, password, is_admin)
        VALUES (?, ?, ?, ?)
        ''', ('Admin', 'admin@example.com', 'admin123', 1))
        print("✅ Default admin user created.")

    conn.commit()
    conn.close()
    print("--- Database is ready. ---")

# --- Database Connection Function ---
def get_db_connection():
    """Creates a database connection using the correct path."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- Flask Routes ---

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
        except sqlite3.IntegrityError:
            flash('That email address is already in use.', 'danger')
        finally:
            conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['is_admin'] = bool(user['is_admin'])
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db_connection()
    meals = conn.execute("SELECT date, lunch_choice, dinner_choice FROM meals WHERE user_id = ? ORDER BY date DESC", (user_id,)).fetchall()
    today_meal = conn.execute("SELECT * FROM meals WHERE user_id = ? AND date = ?", (user_id, date.today().isoformat())).fetchone()
    conn.close()
    meal_count = len(meals)
    already_submitted = today_meal is not None
    return render_template('dashboard.html', name=session['name'], meal_count=meal_count, meals=meals, already_submitted=already_submitted)

@app.route('/submit_meal', methods=['POST'])
def submit_meal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    today = date.today().isoformat()
    lunch = request.form.get('lunch')
    dinner = request.form.get('dinner')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meals WHERE user_id = ? AND date = ?", (user_id, today))
    if cursor.fetchone():
        flash('You have already submitted your meal choice for today.', 'warning')
    else:
        cursor.execute("INSERT INTO meals (user_id, date, lunch_choice, dinner_choice) VALUES (?, ?, ?, ?)", (user_id, today, lunch, dinner))
        conn.commit()
        flash('Your meal choice has been submitted successfully!', 'success')
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('login'))
    conn = get_db_connection()
    today_str = date.today().isoformat()
    counts = conn.execute("""
        SELECT
            SUM(CASE WHEN lunch_choice = 'veg' THEN 1 ELSE 0 END) as lunch_veg,
            SUM(CASE WHEN lunch_choice = 'nonveg' THEN 1 ELSE 0 END) as lunch_nonveg,
            SUM(CASE WHEN dinner_choice = 'veg' THEN 1 ELSE 0 END) as dinner_veg,
            SUM(CASE WHEN dinner_choice = 'nonveg' THEN 1 ELSE 0 END) as dinner_nonveg
        FROM meals WHERE date = ?
    """, (today_str,)).fetchone()
    records = conn.execute("""
        SELECT users.name, meals.lunch_choice, meals.dinner_choice
        FROM meals JOIN users ON meals.user_id = users.id WHERE meals.date = ?
    """, (today_str,)).fetchall()
    conn.close()
    return render_template('admin_dashboard.html', counts=counts, records=records, today=date.today().strftime('%B %d, %Y'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d-%m-%Y'):
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return value
    if hasattr(value, 'strftime'):
        return value.strftime(format)
    return value

# --- Main Execution Block ---
if __name__ == '__main__':
    # This block runs when you execute "python app.py" locally
    init_database() # Create DB for local testing
    app.run(debug=True)
else:
    # This block runs when Gunicorn starts the app on Render
    init_database()