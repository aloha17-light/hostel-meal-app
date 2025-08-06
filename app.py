from flask import Flask, render_template, request, redirect, session
from config import get_db_connection
from datetime import datetime

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
    meal_history = cursor.fetchall()

    conn.close()
    return render_template('dashboard.html', name=session['name'], meal_count=count, meal_history=meal_history)



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
