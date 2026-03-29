from flask import Flask, request, send_from_directory, jsonify
import os
import re
import html
from datetime import datetime
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

API_TOKEN = os.getenv('API_TOKEN', 'changeme')  # optional token for API auth

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

    # ---------- Remaining (optional) ----------
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

    # ---------- Previous (optional, read‑only) ----------
    previous_raw = data.get('previous', '')
    previous = sanitize_input(previous_raw)
    if len(previous) > 2000:
        errors['previous'] = 'Previous field exceeds maximum allowed length.'
    sanitized['previous'] = previous

    return sanitized, errors


# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------
@app.route('/', methods=['GET'])
def serve_index():
    """Serve the main page."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/health', methods=['GET'])
def health_check():
    """Simple health‑check endpoint."""
    return jsonify({'status': 'ok'})


@app.route('/submit', methods=['POST'])
def submit_form():
    """Validate, sanitize and return the form data."""
    data = request.form
    sanitized, errors = validate_form(data)

    if errors:
        return jsonify({'status': 'error', 'errors': errors}), 400

    # Here you could persist the sanitized data to the database.
    # For now we simply echo it back.
    return jsonify({'status': 'success', 'data': sanitized}), 200


# ----------------------------------------------------------------------
# Application entry point
# ----------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)