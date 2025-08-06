from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey' # It's good practice to change this to a more complex key

def get_db_connection():
    """Creates a database connection."""
    conn = sqlite3.connect('hostel_meals.db')
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    return conn

@app.route('/')
def home():
    """Redirects the root URL to the login page."""
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles user registration."""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password'] # In a real app, you should hash passwords!

        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )
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
    """Handles user login."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, password)
        ).fetchone()
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
    """Displays the user's dashboard with their meal history."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()

    # Fetch meal history for the user
    meals = conn.execute(
        "SELECT date, lunch_choice, dinner_choice FROM meals WHERE user_id = ? ORDER BY date DESC",
        (user_id,)
    ).fetchall()

    # Check if a meal has already been submitted for today
    today_meal = conn.execute(
        "SELECT * FROM meals WHERE user_id = ? AND date = ?",
        (user_id, date.today().isoformat())
    ).fetchone()

    conn.close()

    meal_count = len(meals)
    already_submitted = today_meal is not None

    return render_template('dashboard.html',
                           name=session['name'],
                           meal_count=meal_count,
                           meals=meals,
                           already_submitted=already_submitted)

@app.route('/submit_meal', methods=['POST'])
def submit_meal():
    """Handles the submission of daily meal choices."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    today = date.today().isoformat()
    lunch = request.form.get('lunch')
    dinner = request.form.get('dinner')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if a meal has already been submitted for today
    cursor.execute("SELECT * FROM meals WHERE user_id = ? AND date = ?", (user_id, today))
    if cursor.fetchone():
        flash('You have already submitted your meal choice for today.', 'warning')
    else:
        # Insert the new meal choice
        cursor.execute(
            "INSERT INTO meals (user_id, date, lunch_choice, dinner_choice) VALUES (?, ?, ?, ?)",
            (user_id, today, lunch, dinner)
        )
        conn.commit()
        flash('Your meal choice has been submitted successfully!', 'success')

    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/admin')
def admin_dashboard():
    """Displays the admin dashboard with meal counts for the day."""
    # Security check: ensure user is logged in and is an admin
    if 'user_id' not in session or not session.get('is_admin'):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    today_str = date.today().isoformat()

    # Get aggregate meal counts for today
    counts = conn.execute("""
        SELECT
            SUM(CASE WHEN lunch_choice = 'veg' THEN 1 ELSE 0 END) as lunch_veg,
            SUM(CASE WHEN lunch_choice = 'nonveg' THEN 1 ELSE 0 END) as lunch_nonveg,
            SUM(CASE WHEN dinner_choice = 'veg' THEN 1 ELSE 0 END) as dinner_veg,
            SUM(CASE WHEN dinner_choice = 'nonveg' THEN 1 ELSE 0 END) as dinner_nonveg
        FROM meals WHERE date = ?
    """, (today_str,)).fetchone()

    # Get individual meal records for today
    records = conn.execute("""
        SELECT users.name, meals.lunch_choice, meals.dinner_choice
        FROM meals
        JOIN users ON meals.user_id = users.id
        WHERE meals.date = ?
    """, (today_str,)).fetchall()

    conn.close()

    return render_template('admin_dashboard.html',
                           counts=counts,
                           records=records,
                           today=date.today().strftime('%B %d, %Y'))


@app.route('/logout')
def logout():
    """Logs the user out by clearing the session."""
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d-%m-%Y'):
    """Custom template filter to format date strings."""
    if isinstance(value, str):
        try:
            # Assumes date is in 'YYYY-MM-DD' format from the database
            value = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return value # Return original value if parsing fails
    if hasattr(value, 'strftime'):
        return value.strftime(format)
    return value

if __name__ == '__main__':
    app.run(debug=True)