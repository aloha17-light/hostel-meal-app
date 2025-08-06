from flask import Flask, render_template, request, redirect, session, flash
from config import get_db_connection
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, g



from datetime import date
import sqlite3


app = Flask(__name__)
app.secret_key = 'supersecretkey'

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
        conn.commit()
        conn.close()

        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        with open("login_debug.log", "a") as f:
            f.write(f"Trying to log in with: {email}, {password}\n")


        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            print("Login success for:", user['name'])
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['is_admin'] = bool(user['is_admin'])
            return redirect('/dashboard')
        else:
            print("❌ Login failed")
            return "Login failed"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS meal_count FROM meals WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()['meal_count']

    cursor.execute("SELECT date FROM meals WHERE user_id = ? ORDER BY date DESC", (user_id,))
    meals = cursor.fetchall()

    conn.close()

    return render_template('dashboard.html', name=session['name'], meal_count=count, meals=meals)



@app.route('/add_meal')
def add_meal():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO meals (user_id, date) VALUES (?, ?)", (session['user_id'], datetime.today().date()))
    conn.commit()
    conn.close()

    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d-%m-%Y'):
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d')  # Adjust format if needed
        except ValueError:
            return value  # return as is if parsing fails
    return value.strftime(format)


@app.route('/submit_meal', methods=['POST'])
def submit_meal():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    today = date.today().isoformat()
    lunch = request.form.get('lunch')
    dinner = request.form.get('dinner')

    conn = sqlite3.connect('hostel_meals.db')
    cursor = conn.cursor()

    # Check if already submitted
    cursor.execute("SELECT * FROM meals WHERE user_id = ? AND date = ?", (user_id, today))
    if cursor.fetchone():
        flash('Meal already submitted for today.')
        return redirect('/dashboard')

    # Insert the meal
    cursor.execute("""
        INSERT INTO meals (user_id, date, lunch_choice, dinner_choice)
        VALUES (?, ?, ?, ?)
    """, (user_id, today, lunch if lunch else None, dinner if dinner else None))

    conn.commit()
    conn.close()

    flash('Meal submitted successfully!')
    return redirect('/dashboard')


@app.route('/admin')
def admin_dashboard():
    conn = sqlite3.connect('hostel_meals.db')
    cursor = conn.cursor()

    # Meal counts
    cursor.execute("""
        SELECT
            SUM(CASE WHEN lunch_choice = 'veg' THEN 1 ELSE 0 END),
            SUM(CASE WHEN lunch_choice = 'nonveg' THEN 1 ELSE 0 END),
            SUM(CASE WHEN dinner_choice = 'veg' THEN 1 ELSE 0 END),
            SUM(CASE WHEN dinner_choice = 'nonveg' THEN 1 ELSE 0 END)
        FROM meals WHERE date = ?
    """, (date.today().isoformat(),))
    lunch_veg, lunch_nonveg, dinner_veg, dinner_nonveg = cursor.fetchone()

    # Individual entries
    cursor.execute("""
        SELECT users.name, meals.lunch_choice, meals.dinner_choice
        FROM meals
        JOIN users ON meals.user_id = users.id
        WHERE meals.date = ?
    """, (date.today().isoformat(),))
    records = cursor.fetchall()

    conn.close()
    return render_template('admin_dashboard.html',
                           lunch_veg=lunch_veg,
                           lunch_nonveg=lunch_nonveg,
                           dinner_veg=dinner_veg,
                           dinner_nonveg=dinner_nonveg,
                           records=records)



@app.route('/submit-meal', methods=['POST'])
def submit_meal():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    lunch = request.form.get('lunch')
    dinner = request.form.get('dinner')
    date = datetime.today().strftime('%Y-%m-%d')

    con = sqlite3.connect('hostel_meals.db')  # Replace with your DB name
    cur = con.cursor()

    # Check if user already submitted for today
    cur.execute("SELECT * FROM meals WHERE user_id = ? AND date = ?", (user_id, date))
    if cur.fetchone():
        flash("You have already submitted today's meals.")
    else:
        cur.execute("INSERT INTO meals (user_id, date, lunch, dinner) VALUES (?, ?, ?, ?)",
                    (user_id, date, lunch, dinner))
        con.commit()

    con.close()
    return redirect(url_for('dashboard'))
