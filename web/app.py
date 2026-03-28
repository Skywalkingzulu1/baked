from flask import Flask, request, send_from_directory, jsonify
import os
import re
import html
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='')

# Helper function to sanitize input strings
def sanitize_input(value: str) -> str:
    """Escape HTML characters to prevent injection attacks."""
    return html.escape(value.strip())

@app.route('/', methods=['GET', 'POST'])
def serve_index():
    if request.method == 'POST':
        # Extract form data
        data = request.form

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
        # Limit length to prevent overly large payloads
        if len(previous) > 2000:
            errors['previous'] = 'Previous field exceeds maximum allowed length.'

        # If there are validation errors, return them
        if errors:
            return jsonify({'status': 'error', 'errors': errors}), 400

        # Build sanitized response payload
        response_payload = {
            'name': name,
            'address': address,
            'phone': phone,
            'date': date_str,
            'cost': cost_val,
            'remaining': remaining_val,
            'previous': previous if previous else None
        }

        return jsonify({
            'status': 'success',
            'message': 'Form submitted successfully.',
            'data': response_payload
        }), 200

    # For GET requests, serve the static index.html
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/health')
def health():
    return jsonify(status='ok'), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)