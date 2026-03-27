from flask import Flask, request, send_from_directory, jsonify
import os
import re
import html
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='')

@app.route('/', methods=['GET', 'POST'])
def serve_index():
    if request.method == 'POST':
        # Extract form data
        data = request.form

        errors = {}

        # Validate and sanitize Name
        name = data.get('name', '').strip()
        if not name:
            errors['name'] = 'Name is required.'
        safe_name = html.escape(name)

        # Validate and sanitize Address
        address = data.get('address', '').strip()
        if not address:
            errors['address'] = 'Address is required.'
        safe_address = html.escape(address)

        # Validate Phone (must be exactly 10 digits)
        phone = data.get('phone', '').strip()
        if not re.fullmatch(r'\d{10}', phone):
            errors['phone'] = 'Phone number must be exactly 10 digits.'
        safe_phone = html.escape(phone)

        # Validate Date (ISO format YYYY-MM-DD)
        date_str = data.get('date', '').strip()
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            errors['date'] = 'Invalid date format. Expected YYYY-MM-DD.'

        # Validate Cost (numeric, 0 to 500)
        cost_str = data.get('cost', '').strip()
        try:
            cost_val = float(cost_str)
            if not (0 <= cost_val <= 500):
                raise ValueError
        except ValueError:
            errors['cost'] = 'Cost must be a number between 0 and 500.'

        # Validate Remaining (optional, numeric, 0 to 500)
        remaining_str = data.get('remaining', '').strip()
        if remaining_str:
            try:
                remaining_val = float(remaining_str)
                if not (0 <= remaining_val <= 500):
                    raise ValueError
            except ValueError:
                errors['remaining'] = 'Remaining credit must be a number between 0 and 500.'

        # If there are validation errors, return them
        if errors:
            return jsonify({'status': 'error', 'errors': errors}), 400

        # Build sanitized response payload (could be stored or processed further)
        response_payload = {
            'name': safe_name,
            'address': safe_address,
            'phone': safe_phone,
            'date': date_str,
            'cost': cost_val,
            'remaining': remaining_val if remaining_str else None
        }

        return jsonify({'status': 'success', 'message': 'Form submitted successfully.', 'data': response_payload}), 200

    # For GET requests, serve the static index.html
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/health')
def health():
    return jsonify(status='ok'), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)