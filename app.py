from flask import Flask, request, send_from_directory, jsonify, send_file
import os
import re
import html
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables from a .env file if present
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

# Simple token‑based authentication for the API endpoint
API_TOKEN = os.getenv('API_TOKEN', 'changeme')  # replace with a strong secret

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
    """Escape HTML characters to prevent injection attacks."""
    return html.escape(value.strip())

def validate_form(data):
    """Validate and sanitize incoming form fields."""
    errors = {}

    # ---------- Name ----------
    name_raw = data.get('name', '')
    name = sanitize_input(name_raw)
    if not name:
        errors['name'] = 'Name is required.'

    # ---------- Address ----------
    address_raw = data.get('address', '')
    address = sanitize_input(address_raw)
    if not address:
        errors['address'] = 'Address is required.'

    # ---------- Phone ----------
    phone_raw = data.get('phone', '')
    phone = sanitize_input(phone_raw)
    if not re.fullmatch(r'\d{10}', phone):
        errors['phone'] = 'Phone number must be exactly 10 digits.'

    # ---------- Date ----------
    date_raw = data.get('date', '')
    date_str = date_raw.strip()
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        errors['date'] = 'Invalid date format. Expected YYYY-MM-DD.'

    # ---------- Cost ----------
    cost_raw = data.get('cost', '')
    cost_str = cost_raw.strip()
    try:
        cost_val = float(cost_str)
        if not (0 <= cost_val <= 500):
            raise ValueError
    except ValueError:
        errors['cost'] = 'Cost must be a number between 0 and 500.'

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

    # ---------- Previous (optional, read‑only) ----------
    previous_raw = data.get('previous', '')
    previous = sanitize_input(previous_raw)
    if len(previous) > 2000:
        errors['previous'] = 'Previous field exceeds maximum allowed length.'

    # Assemble cleaned data (only if no validation errors for those fields)
    cleaned = {
        'name': name,
        'address': address,
        'phone': phone,
        'date': date_str,
        'cost': cost_val if 'cost' not in errors else None,
        'remaining': remaining_val,
        'previous': previous
    }

    return errors, cleaned

def authenticate_request():
    """Simple Bearer token authentication."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    token = auth_header.split(' ', 1)[1]
    return token == API_TOKEN

# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def serve_index():
    """Serve the static index page and handle legacy form POSTs."""
    if request.method == 'POST':
        errors, cleaned = validate_form(request.form)
        if errors:
            return jsonify({'status': 'error', 'errors': errors}), 400
        return jsonify({'status': 'success', 'data': cleaned}), 200

    # GET – serve the static index.html
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/health', methods=['GET'])
def health():
    """Health‑check endpoint."""
    return jsonify({'status': 'ok'}), 200

@app.route('/api/submit', methods=['POST'])
def api_submit():
    """Secure API endpoint that validates, sanitizes, and stores form data."""
    # ---- Authentication ----
    if not authenticate_request():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    # ---- Validation ----
    errors, cleaned = validate_form(request.form)
    if errors:
        return jsonify({'status': 'error', 'errors': errors}), 400

    # ---- Persistence ----
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        insert_sql = """
            INSERT INTO submissions
                (name, address, phone, submission_date, cost, remaining, previous)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """
        cur.execute(insert_sql, (
            cleaned['name'],
            cleaned['address'],
            cleaned['phone'],
            cleaned['date'],
            cleaned['cost'],
            cleaned['remaining'],
            cleaned['previous']
        ))
        new_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        # In a real application you would log the exception details securely.
        return jsonify({
            'status': 'error',
            'message': 'Database error',
            'details': str(e)
        }), 500

    return jsonify({'status': 'success', 'id': new_id}), 201

# ----------------------------------------------------------------------
# Application entry point
# ----------------------------------------------------------------------
if __name__ == '__main__':
    # Development server only; use a production WSGI server in real deployments.
    app.run(host='0.0.0.0', port=5000, debug=True)