import os
from flask import Flask, jsonify, send_from_directory
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Determine the project root where index.html resides (one level up from this file)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Flask app configuration
app = Flask(__name__, static_folder=PROJECT_ROOT, static_url_path='')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'baked_dev_secret_2026')

# ----------------------------------------------------------------------
# Simple health check endpoint
# ----------------------------------------------------------------------
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

# ----------------------------------------------------------------------
# Serve the main index.html page
# ----------------------------------------------------------------------
@app.route('/', methods=['GET'])
def serve_index():
    # index.html is located in the project root directory
    return send_from_directory(app.static_folder, 'index.html')

# ----------------------------------------------------------------------
# Optional: placeholder for future DB initialization (no-op for now)
# ----------------------------------------------------------------------
def init_db():
    """Placeholder function for database initialization.
    Currently does nothing to keep the application lightweight for tests.
    """
    pass

if __name__ == '__main__':
    # Run the Flask development server for manual testing
    app.run(host='0.0.0.0', port=5000, debug=True)
