from flask import Flask, request, send_from_directory, jsonify, g
import os
import re
import html
import jwt
import bcrypt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# ----------------------------------------------------------------------
# Load environment variables
# ----------------------------------------------------------------------
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='')

# ----------------------------------------------------------------------
# Configuration (environment variables)
# ----------------------------------------------------------------------
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'bud_credit')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

JWT_SECRET = os.getenv('JWT_SECRET', 'supersecretkey')
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = int(os.getenv('JWT_EXP_DELTA_SECONDS', '3600'))

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def get_db_connection():
    """Create a new PostgreSQL connection using the configured credentials."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=RealDictCursor
    )

def sanitize_input(value: str) -> str:
    """Escape HTML characters to prevent injection attacks and trim whitespace."""
    return html.escape(value.strip())

def validate_form(data):
    """Validate and sanitize incoming form fields.
    Returns a tuple (sanitized_dict, errors_dict).
    """
    errors = {}
    sanitized = {}

    # ---------- Name ----------
    name_raw = data.get('name', '')
    name = sanitize_input(name_raw)
    if not name:
        errors['name'] = 'Name is required.'
    sanitized['name'] = name

    # ---------- Email (optional) ----------
    email_raw = data.get('email', '')
    email = sanitize_input(email_raw)
    if email:
        email_regex = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
        if not re.fullmatch(email_regex, email):
            errors['email'] = 'Invalid email format.'
    sanitized['email'] = email

    # ---------- Address ----------
    address_raw = data.get('address', '')
    address = sanitize_input(address_raw)
    if not address:
        errors['address'] = 'Address is required.'
    sanitized['address'] = address

    # ---------- Phone ----------
    phone_raw = data.get('phone', '')
    phone = sanitize_input(phone_raw)
    if not re.fullmatch(r'\d{10}', phone):
        errors['phone'] = 'Phone number must be exactly 10 digits.'
    sanitized['phone'] = phone

    # ---------- Date ----------
    date_raw = data.get('date', '')
    date_str = date_raw.strip()
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        errors['date'] = 'Invalid date format. Expected YYYY-MM-DD.'
    sanitized['date'] = date_str

    # ---------- Cost ----------
    cost_raw = data.get('cost', '')
    cost_str = cost_raw.strip()
    try:
        cost_val = float(cost_str)
        if not (0 <= cost_val <= 500):
            raise ValueError
    except ValueError:
        errors['cost'] = 'Cost must be a number between 0 and 500.'
        cost_val = None
    sanitized['cost'] = cost_val

    # ---------- Remaining ----------
    remaining_raw = data.get('remaining', '')
    remaining_str = remaining_raw.strip()
    remaining_val = None
    if remaining_str:
        try:
            remaining_val = float(remaining_str)
            if not (0 <= remaining_val <= 500):
                raise ValueError
        except ValueError:
            errors['remaining'] = 'Remaining credit must be a number between 0 and 500.'
    sanitized['remaining'] = remaining_val

    # ---------- Previous ----------
    previous_raw = data.get('previous', '')
    previous = sanitize_input(previous_raw)
    if len(previous) > 2000:
        errors['previous'] = 'Previous field exceeds maximum allowed length.'
    sanitized['previous'] = previous

    return sanitized, errors

# ----------------------------------------------------------------------
# Authentication helpers
# ----------------------------------------------------------------------
def create_user(username: str, password: str, role: str = 'user'):
    """Insert a new user into the database."""
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (username, password_hash, role)
                VALUES (%s, %s, %s)
                ON CONFLICT (username) DO NOTHING
                """,
                (username, password_hash.decode('utf-8'), role)
            )
            conn.commit()
    finally:
        conn.close()

def get_user_by_username(username: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            return user
    finally:
        conn.close()

def generate_jwt(user_id: int, role: str):
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def token_required(f):
    """Decorator that ensures a valid JWT is present."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization header missing or malformed'}), 401
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            g.current_user = {
                'id': payload['user_id'],
                'role': payload['role']
            }
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

def role_required(required_role):
    """Decorator that checks if the current user has the required role."""
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_role = g.get('current_user', {}).get('role')
            if user_role != required_role and user_role != 'admin':
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ----------------------------------------------------------------------
# Database initialization (ensure users table exists)
# ----------------------------------------------------------------------
def init_db():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(150) UNIQUE NOT NULL,
                    password_hash VARCHAR(200) NOT NULL,
                    role VARCHAR(50) NOT NULL DEFAULT 'user'
                );
            """)
            conn.commit()
    finally:
        conn.close()

init_db()

# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------
@app.route('/', methods=['GET'])
def serve_index():
    """Serve the main page."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

@app.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    Expected JSON: { "username": "...", "password": "...", "role": "user|admin" (optional) }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON payload'}), 400

    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    if get_user_by_username(username):
        return jsonify({'error': 'Username already exists'}), 409

    create_user(username, password, role)
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    """
    Authenticate a user and return a JWT.
    Expected JSON: { "username": "...", "password": "..." }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON payload'}), 400

    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = get_user_by_username(username)
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    stored_hash = user['password_hash'].encode('utf-8')
    if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = generate_jwt(user['id'], user['role'])
    return jsonify({'token': token}), 200

@app.route('/submit', methods=['POST'])
@token_required
@role_required('user')
def submit_form():
    """Validate, sanitize and store the form data."""
    data = request.form
    sanitized, errors = validate_form(data)

    if errors:
        return jsonify({'status': 'error', 'errors': errors}), 400

    # Store the sanitized data in the database (example implementation)
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO bud_credit_forms
                (user_id, name, email, address, phone, date, cost, remaining, previous)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    g.current_user['id'],
                    sanitized['name'],
                    sanitized.get('email'),
                    sanitized['address'],
                    sanitized['phone'],
                    sanitized['date'],
                    sanitized['cost'],
                    sanitized['remaining'],
                    sanitized['previous']
                )
            )
            conn.commit()
    finally:
        conn.close()

    return jsonify({'status': 'success', 'data': sanitized}), 201

# ----------------------------------------------------------------------
# Optional: Admin routes for viewing/editing forms
# ----------------------------------------------------------------------
@app.route('/forms', methods=['GET'])
@token_required
@role_required('admin')
def list_forms():
    """Admin can list all submitted forms."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT f.id, u.username as submitted_by, f.name, f.email, f.address,
                       f.phone, f.date, f.cost, f.remaining, f.previous
                FROM bud_credit_forms f
                JOIN users u ON f.user_id = u.id
                ORDER BY f.id DESC
                """
            )
            rows = cur.fetchall()
            return jsonify({'forms': rows}), 200
    finally:
        conn.close()

# ----------------------------------------------------------------------
# Run the app (development mode)
# ----------------------------------------------------------------------
if __name__ == '__main__':
    # Ensure the forms table exists
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bud_credit_forms (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    name VARCHAR(200) NOT NULL,
                    email VARCHAR(200),
                    address VARCHAR(300) NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    date DATE NOT NULL,
                    cost NUMERIC(10,2) NOT NULL,
                    remaining NUMERIC(10,2),
                    previous TEXT
                );
            """)
            conn.commit()
    finally:
        conn.close()

    app.run(host='0.0.0.0', port=5000, debug=True)