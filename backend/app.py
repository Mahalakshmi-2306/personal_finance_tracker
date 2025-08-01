from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from config import DB_CONFIG
from datetime import datetime
from flask_cors import CORS
import pytz

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.secret_key = "supersecretkey"
CORS(app, supports_credentials=True)

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if username already exists
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()
        if existing_user:
            conn.close()
            return "Username already exists. Please login.", 400

        hashed_pw = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_pw))
        conn.commit()

        # Get inserted user ID to start session
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()

        session['user_id'] = user['id']
        print(f"[REGISTER] User registered and session started: {user['id']}")
        return redirect('/dashboard')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            print(f"[LOGIN] Login successful. Session set for user_id: {user['id']}")
            return redirect('/dashboard')
        else:
            print("[LOGIN] Invalid credentials.")
            return "Invalid username or password", 401

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    print("[LOGOUT] Session cleared.")
    return redirect('/login')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        print("[DASHBOARD] Unauthorized access, redirecting to login.")
        return redirect('/login')
    return render_template('index.html')

@app.route('/summary')
def summary():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('summary.html')

@app.route('/transactions', methods=['GET', 'POST', 'PUT', 'DELETE'])
def transactions():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        data = request.json

        # Get IST time
        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')

        # Insert with IST timestamp
        cursor.execute("""
            INSERT INTO transactions (user_id, amount, type, category, date, note, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, data['amount'], data['type'], data['category'], data['date'], data.get('note'), timestamp))

        conn.commit()
        conn.close()
        return jsonify({"success": True})

    elif request.method == 'GET':
        cursor.execute("SELECT * FROM transactions WHERE user_id = %s ORDER BY date DESC", (user_id,))
        results = cursor.fetchall()
        conn.close()

        # Convert timestamp and date fields properly
        for tx in results:
            if isinstance(tx['timestamp'], datetime):
                tx['timestamp'] = tx['timestamp'].isoformat()
            elif isinstance(tx['timestamp'], str):
                try:
                    parsed = datetime.strptime(tx['timestamp'], "%Y-%m-%d %H:%M:%S")
                    tx['timestamp'] = parsed.isoformat()
                except:
                    tx['timestamp'] = None

            if isinstance(tx['date'], datetime):
                tx['date'] = tx['date'].strftime("%Y-%m-%d")

        return jsonify(results)


    elif request.method == 'PUT':
        data = request.get_json()
        if not data.get("id"):
            return jsonify({"error": "Missing transaction ID"}), 400

        cursor.execute("""
            UPDATE transactions SET amount=%s, type=%s, category=%s, date=%s, note=%s
            WHERE id=%s AND user_id=%s
        """, (data['amount'], data['type'], data['category'], data['date'], data['note'], data['id'], user_id))

        conn.commit()
        conn.close()
        return jsonify({"success": True})

    elif request.method == 'DELETE':
        id = request.view_args.get('id') or request.args.get('id')
        if not id:
            return jsonify({"error": "ID required"}), 400
        cursor.execute("DELETE FROM transactions WHERE id=%s AND user_id=%s", (id, user_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
@app.route('/transactions/<int:id>', methods=['DELETE'])
def delete_transaction(id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = %s AND user_id = %s", (id, user_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.config['TEMPLATES_AUTO_RELOAD'] = True  # Ensures template changes reload
    app.run(debug=True)
