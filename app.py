import os
import re
import html
import json
from datetime import datetime
from flask import Flask, request, send_from_directory, jsonify, abort
from dotenv import load_dotenv

# ----------------------------------------------------------------------
# Load environment variables
# ----------------------------------------------------------------------
load_dotenv()

# ----------------------------------------------------------------------
# Flask app configuration
# ----------------------------------------------------------------------
app = Flask(__name__, static_folder='static', static_url_path='')

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def sanitize_input(value: str) -> str:
    """
    Escape HTML characters to prevent injection attacks and trim whitespace.
    """
    return html.escape(value.strip())

def validate_form(data: dict):
    """
    Validate and sanitize incoming form fields.
    Returns a tuple (sanitized_dict, errors_dict).
    """
    errors = {}
    sanitized = {}

    # ---------- Name ----------
    name = sanitize_input(data.get('name', ''))
    if not name:
        errors['name'] = 'Name is required.'
    sanitized['name'] = name

    # ---------- Email (optional) ----------
    email = sanitize_input(data.get('email', ''))
    if email:
        email_regex = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
        if not re.fullmatch(email_regex, email):
            errors['email'] = 'Invalid email format.'
    sanitized['email'] = email

    # ---------- Address ----------
    address = sanitize_input(data.get('address', ''))
    if not address:
        errors['address'] = 'Address is required.'
    sanitized['address'] = address

    # ---------- Phone ----------
    phone = sanitize_input(data.get('phone', ''))
    if not re.fullmatch(r'\d{10}', phone):
        errors['phone'] = 'Phone number must be exactly 10 digits.'
    sanitized['phone'] = phone

    # ---------- Date ----------
    date_str = data.get('date', '').strip()
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        errors['date'] = 'Invalid date format. Expected YYYY-MM-DD.'
    sanitized['date'] = date_str

    # ---------- Cost ----------
    cost_raw = data.get('cost', '').strip()
    try:
        cost_val = float(cost_raw)
        if not (0 <= cost_val <= 500):
            raise ValueError
    except ValueError:
        errors['cost'] = 'Cost must be a number between 0 and 500.'
        cost_val = None
    sanitized['cost'] = cost_val

    # ---------- Remaining (optional) ----------
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

    # ---------- Previous (optional, read‑only) ----------
    previous = sanitize_input(data.get('previous', ''))
    if len(previous) > 2000:
        errors['previous'] = 'Previous field exceeds maximum allowed length (2000 characters).'
    sanitized['previous'] = previous

    return sanitized, errors

# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------
@app.route('/', methods=['GET'])
def serve_index():
    """
    Serve the main page (index.html).
    """
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """
    Simple health‑check endpoint.
    """
    return jsonify({'status': 'ok'}), 200

@app.route('/submit', methods=['POST'])
def submit_form():
    """
    Validate, sanitize and process the credit form submission.
    Returns JSON with either success data or detailed error messages.
    """
    try:
        # Flask's request.form provides a MultiDict; convert to a regular dict for validation
        form_data = request.form.to_dict()
        sanitized, errors = validate_form(form_data)

        if errors:
            # Return a 400 Bad Request with error details
            return jsonify({'status': 'error', 'errors': errors}), 400

        # In a real application you would persist `sanitized` securely (e.g., parameterised DB query)
        # For this task we simply echo the sanitized data back to the client.
        return jsonify({'status': 'success', 'data': sanitized}), 200

    except Exception as e:
        # Log the exception in a real-world scenario; here we return a generic error.
        return jsonify({'status': 'error', 'message': 'Internal server error.'}), 500

# ----------------------------------------------------------------------
# Application entry point
# ----------------------------------------------------------------------
if __name__ == '__main__':
    # Bind to all interfaces for containerised environments
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', '5000'))
    app.run(host=host, port=port, debug=False)