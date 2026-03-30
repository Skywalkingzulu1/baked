import os
import re
import html
import jwt
import bcrypt
import csv
import io
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, send_from_directory, jsonify, abort, make_response
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# ----------------------------------------------------------------------
# Load environment variables
# ----------------------------------------------------------------------
load_dotenv()

# ----------------------------------------------------------------------
# Flask app configuration
# ----------------------------------------------------------------------
app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'baked_dev_secret_2026')
ADMIN_PASS_HASH = os.getenv('ADMIN_PASS_HASH', bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode())

# ----------------------------------------------------------------------
# Security Helpers
# ----------------------------------------------------------------------
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('admin_token')
        if not token:
            return jsonify({'message': 'Authentication required'}), 401
        try:
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return jsonify({'message': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

def user_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('auth_token')
        if not token:
            return jsonify({'message': 'User authentication required'}), 401
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            request.user_id = payload['user_id']
        except:
            return jsonify({'message': 'Invalid session'}), 401
        return f(*args, **kwargs)
    return decorated

# ----------------------------------------------------------------------
# Database configuration
# ----------------------------------------------------------------------
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'bud_credit')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

def get_db_connection():
    """Create a new database connection."""
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
        cursor_factory=RealDictCursor
    )
    return conn

def init_db():
    """Initialize the database with users and linked submissions."""
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        full_name TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS submissions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        name TEXT NOT NULL,
                        email TEXT,
                        address TEXT NOT NULL,
                        phone VARCHAR(10) NOT NULL,
                        submission_date DATE NOT NULL,
                        cost NUMERIC CHECK (cost >= 0 AND cost <= 500),
                        remaining NUMERIC CHECK (remaining >= 0 AND remaining <= 500),
                        previous TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
    finally:
        conn.close()

# Initialize on start
init_db()

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def sanitize_input(value: str) -> str:
    return html.escape(value.strip())

def validate_form(data: dict):
    errors = {}
    sanitized = {}
    
    # ... (Keep logic from previous audit) ...
    name = sanitize_input(data.get('name', ''))
    if not name: errors['name'] = 'Name is required.'
    sanitized['name'] = name

    address = sanitize_input(data.get('address', ''))
    if not address: errors['address'] = 'Address is required.'
    sanitized['address'] = address

    phone = sanitize_input(data.get('phone', ''))
    if not re.fullmatch(r'\d{10}', phone): errors['phone'] = '10 digit phone required.'
    sanitized['phone'] = phone

    cost = data.get('cost', '0')
    try:
        c = float(cost)
        if not (0 <= c <= 500): raise ValueError
        sanitized['cost'] = c
    except:
        errors['cost'] = 'Cost 0-500 required.'

    # Default date if missing
    sanitized['date'] = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    sanitized['email'] = data.get('email', '')
    sanitized['remaining'] = data.get('remaining', 0)
    sanitized['previous'] = data.get('previous', '')

    return sanitized, errors

# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email', '').lower()
    password = data.get('password', '')
    name = data.get('name', '')
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO users (email, password_hash, full_name) VALUES (%s, %s, %s)", (email, hashed, name))
                return jsonify({'status': 'success'})
    except: return jsonify({'status': 'error', 'message': 'Registration failed'}), 400
    finally: conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    password = data.get('password', '')
    # Check Admin first
    if bcrypt.checkpw(password.encode(), ADMIN_PASS_HASH.encode()):
        token = jwt.encode({'user': 'admin', 'exp': datetime.utcnow() + timedelta(hours=24)}, app.config['SECRET_KEY'])
        resp = make_response(jsonify({'status': 'success', 'role': 'admin'}))
        resp.set_cookie('admin_token', token, httponly=True)
        return resp
    # User Login check here...
    return jsonify({'status': 'error'}), 401

@app.route('/api/submit', methods=['POST'])
def submit_form():
    sanitized, errors = validate_form(request.form)
    if errors: return jsonify({'status': 'error', 'errors': errors}), 400
    
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO submissions (name, email, address, phone, submission_date, cost, remaining, previous)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (sanitized['name'], sanitized['email'], sanitized['address'], sanitized['phone'], 
                      sanitized['date'], sanitized['cost'], sanitized['remaining'], sanitized['previous']))
                return jsonify({'status': 'success'})
    finally: conn.close()

@app.route('/api/admin/submissions', methods=['GET'])
@admin_required
def get_submissions():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM submissions ORDER BY created_at DESC")
            return jsonify(cur.fetchall())
    finally: conn.close()

@app.route('/api/admin/export', methods=['GET'])
@admin_required
def export_csv():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM submissions")
            rows = cur.fetchall()
            output = io.StringIO()
            if rows:
                writer = csv.DictWriter(output, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            resp = make_response(output.getvalue())
            resp.headers["Content-Disposition"] = "attachment; filename=export.csv"
            resp.headers["Content-type"] = "text/csv"
            return resp
    finally: conn.close()

@app.route('/admin')
def admin_page(): return send_from_directory('.', 'admin.html')

@app.route('/api/user/data', methods=['GET'])
@user_required
def get_user_dashboard():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 1. Fetch User Info
            cur.execute("SELECT id, email, full_name FROM users WHERE id = %s", (request.user_id,))
            user = cur.fetchone()
            
            # 2. Fetch Submissions
            cur.execute("SELECT * FROM submissions WHERE user_id = %s ORDER BY submission_date DESC", (request.user_id,))
            subs = cur.fetchall()
            
            return jsonify({
                'user': user,
                'submissions': subs
            })
    finally: conn.close()

@app.route('/dashboard')
def dashboard(): return send_from_directory('.', 'dashboard.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
