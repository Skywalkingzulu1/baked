from flask import Flask, request, send_from_directory, jsonify
import html
import re
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='')

# ----------------------------------------------------------------------
# Helper function to sanitize input strings
# ----------------------------------------------------------------------
def sanitize_input(value: str) -> str:
    """Escape HTML characters to prevent injection attacks."""
    return html.escape(value.strip())

def validate_form(data):
    """Validate and sanitize the incoming form data."""
    errors = {}
    sanitized = {}

    # Name
    name = sanitize_input(data.get('name', ''))
    if not name:
        errors['name'] = 'Name is required.'
    sanitized['name'] = name

    # Address
    address = sanitize_input(data.get('address', ''))
    if not address:
        errors['address'] = 'Address is required.'
    sanitized['address'] = address

    # Phone
    phone = sanitize_input(data.get('phone', ''))
    if not re.fullmatch(r'\d{10}', phone):
        errors['phone'] = 'Phone number must be exactly 10 digits.'
    sanitized['phone'] = phone

    # Date
    date_str = data.get('date', '').strip()
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        errors['date'] = 'Invalid date format. Expected YYYY-MM-DD.'
    sanitized['date'] = date_str

    # Cost
    cost_raw = data.get('cost', '').strip()
    try:
        cost_val = float(cost_raw)
        if not (0 <= cost_val <= 500):
            raise ValueError
    except ValueError:
        errors['cost'] = 'Cost must be a number between 0 and 500.'
        cost_val = None
    sanitized['cost'] = cost_val

    # Remaining (optional)
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

@app.route('/', methods=['GET'])
def serve_index():
    """Serve the main page."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/submit', methods=['POST'])
def submit_form():
    """Validate, sanitize and echo back the form data."""
    sanitized, errors = validate_form(request.form)

    if errors:
        return jsonify({'status': 'error', 'errors': errors}), 400

    # In a real application you would store the sanitized data securely.
    return jsonify({'status': 'success', 'data': sanitized}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)