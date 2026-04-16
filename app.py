from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'mysecret123'
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"
# ---------------- DB FUNCTION ----------------
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- INIT DB ----------------
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Workers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS workers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        work TEXT,
        phone TEXT,
        location TEXT,
        rating INTEGER           
                   
    )
    ''')

    # Booking table (👉 नया add किया)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        worker_id INTEGER,
        customer_name TEXT,
        date TEXT
    )
    ''')
    # 👉 Users table (login system)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME + SEARCH ----------------
@app.route('/', methods=['GET', 'POST'])
def home():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        work = request.form.get('work', '')
        location = request.form.get('location', '')

        cursor.execute(
            "SELECT * FROM workers WHERE work LIKE ? AND location LIKE ?",
            ('%' + work + '%', '%' + location + '%')
        )
    else:
        cursor.execute("SELECT * FROM workers")

    workers = cursor.fetchall()
    conn.close()

    return render_template('index.html', workers=workers)

# ---------------- WORKER PROFILE ----------------
@app.route('/worker/<int:id>')
def worker_profile(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM workers WHERE id = ?", (id,))
    worker = cursor.fetchone()

    conn.close()

    return render_template('worker.html', worker=worker)

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        work = request.form['work']
        phone = request.form['phone']
        location = request.form['location']   # 👉 नया add

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO workers (name, work, phone, location) VALUES (?, ?, ?, ?)",
            (name, work, phone, location)
        )

        conn.commit()
        conn.close()

        return redirect(url_for('home'))

    return render_template('register.html')

# signup route (👉 नया add)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('signup.html')
# ---------------- LOGIN (UPDATED) ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            session['user'] = user['username']
            return redirect('/')
        else:
            return "❌ Invalid Login"

    return render_template('login.html')

# ---------------- ADMIN LOGIN ----------------
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect('/admin')
        else:
            return "❌ Invalid Admin Login"

    return render_template('admin_login.html')

# ---------------- BOOKING (UPDATED) ----------------
@app.route('/book/<int:id>', methods=['GET', 'POST'])
def book(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        customer_name = request.form['name']
        date = request.form['date']
        payment = request.form['payment']

        cursor.execute(
            "INSERT INTO bookings (worker_id, customer_name, date) VALUES (?, ?, ?)",
            (id, customer_name, date)
        )

        conn.commit()
        conn.close()

        return f"✅ Booking Confirmed! Payment Method: {payment}"

    return render_template('book.html', worker_id=id)
# ---------------- RATING ----------------
@app.route('/rate/<int:id>', methods=['POST'])
def rate(id):
    rating = request.form['rating']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE workers SET rating=? WHERE id=?",
        (rating, id)
    )

    conn.commit()
    conn.close()

    return redirect('/')
# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# ---------------- ADMIN PANEL ----------------
@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect('/admin_login')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Workers
    cursor.execute("SELECT * FROM workers")
    workers = cursor.fetchall()

    # Bookings (JOIN वाला)
    cursor.execute('''
                        SELECT bookings.id, workers.name, bookings.customer_name, bookings.date
                        FROM bookings
                        JOIN workers ON bookings.worker_id = workers.id
                    ''')
    bookings = cursor.fetchall()

    # ⭐ STATS
    cursor.execute("SELECT COUNT(*) FROM workers")
    total_workers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    conn.close()

    return render_template(
        'admin.html',
        workers=workers,
        bookings=bookings,
        total_workers=total_workers,
        total_bookings=total_bookings,
        total_users=total_users
    )
# ---------------- DELETE WORKER ----------------
@app.route('/delete_worker/<int:id>')
def delete_worker(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM workers WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/admin')
# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)