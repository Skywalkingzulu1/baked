import os
import re
import html
import json
from datetime import datetime
from flask import Flask, request, send_from_directory, jsonify, abort
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
app = Flask(__name__, static_folder='static', static_url_path='')

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
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        cursor_factory=RealDictCursor
    )
    return conn

def init_db():
    """Initialize the submissions table if it does not exist."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS submissions (
        id SERIAL PRIMARY KEY,
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
    """
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
    finally:
        conn.close()

# Initialize DB on startup
init_db()

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def sanitize_input(value: str) -> str:
    """Escape HTML characters to prevent injection attacks and trim whitespace."""
    return html.escape(value.strip())

def validate_form(data: dict):
    """
    Validate and sanitize incoming form fields.
    Returns a tuple (sanitized_dict, errors_dict).
    """
    errors = {}
    sanitized = {}

    # Name (required)
    name = sanitize_input(data.get('name', ''))
    if not name:
        errors['name'] = 'Name is required.'
    sanitized['name'] = name

    # Email (optional)
    email = sanitize_input(data.get('email', ''))
    if email:
        email_regex = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
        if not re.fullmatch(email_regex, email):
            errors['email'] = 'Invalid email format.'
    sanitized['email'] = email

    # Address (required)
    address = sanitize_input(data.get('address', ''))
    if not address:
        errors['address'] = 'Address is required.'
    sanitized['address'] = address

    # Phone (required, exactly 10 digits)
    phone = sanitize_input(data.get('phone', ''))
    if not re.fullmatch(r'\d{10}', phone):
        errors['phone'] = 'Phone number must be exactly 10 digits.'
    sanitized['phone'] = phone

    # Date (required, YYYY-MM-DD)
    date_str = data.get('date', '').strip()
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        errors['date'] = 'Invalid date format. Expected YYYY-MM-DD.'
        date_obj = None
    sanitized['date'] = date_str  # keep original string for DB insertion

    # Cost (required, numeric 0-500)
    cost_raw = data.get('cost', '').strip()
    try:
        cost_val = float(cost_raw)
        if not (0 <= cost_val <= 500):
            raise ValueError
    except ValueError:
        errors['cost'] = 'Cost must be a number between 0 and 500.'
        cost_val = None
    sanitized['cost'] = cost_val

    # Remaining (optional, numeric 0-500)
    remaining_raw = data.get('remaining', '').strip()
    remaining_val = None
    if remaining_raw:
        try:
            remaining_val = float(remaining_raw)
            if not (0 <= remaining_val <= 500):
                raise ValueError
        except ValueError:
            errors['remaining'] = 'Remaining credit must be a number between 0 and 500.'
    sanitized['remaining'] = remaining_val

    # Previous (optional, read‑only)
    previous = sanitize_input(data.get('previous', ''))
    if len(previous) > 2000:
        errors['previous'] = 'Previous field exceeds maximum allowed length.'
    sanitized['previous'] = previous

    return sanitized, errors

# ----------------------------------------------------------------------
# Flask routes
# ----------------------------------------------------------------------
@app.route('/', methods=['GET'])
def serve_index():
    """Serve the main page."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({'status': 'ok'}), 200

@app.route('/submit', methods=['POST'])
def submit_form():
    """Validate, sanitize, store (if valid) and return the form data."""
    sanitized, errors = validate_form(request.form)

    if errors:
        return jsonify({'status': 'error', 'errors': errors}), 400

    # Store the sanitized data in the database
    insert_sql = """
        INSERT INTO submissions
        (name, email, address, phone, submission_date, cost, remaining, previous)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, created_at;
    """
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    insert_sql,
                    (
                        sanitized['name'],
                        sanitized['email'] or None,
                        sanitized['address'],
                        sanitized['phone'],
                        sanitized['date'],
                        sanitized['cost'],
                        sanitized['remaining'],
                        sanitized['previous']
                    )
                )
                result = cur.fetchone()
                sanitized['id'] = result['id']
                sanitized['created_at'] = result['created_at'].isoformat()
    finally:
        conn.close()

    return jsonify({'status': 'success', 'data': sanitized}), 200

if __name__ == '__main__':
    # Default to host 0.0.0.0 and port from env or 5000
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', '5000'))
    app.run(host=host, port=port, debug=False)