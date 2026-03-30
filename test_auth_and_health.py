import pytest
import jwt
from datetime import datetime, timedelta

# Import the Flask app that contains the authentication decorators
from app import app as auth_app, admin_required, user_required

# Import the Flask app that provides the health endpoint (src/app.py)
from src.app import app as health_app

# Helper to create a JWT token
def create_token(secret, payload, expires_in=3600):
    payload_copy = payload.copy()
    payload_copy.update({
        "exp": datetime.utcnow() + timedelta(seconds=expires_in),
        "iat": datetime.utcnow()
    })
    return jwt.encode(payload_copy, secret, algorithm="HS256")

# Fixture for the auth app test client
@pytest.fixture
def client():
    with auth_app.test_client() as client:
        yield client

# Fixture for the health app test client
@pytest.fixture
def health_client():
    with health_app.test_client() as client:
        yield client

# ----- Admin Required Tests -----

@auth_app.route('/protected_admin')
@admin_required
def protected_admin():
    return {'message': 'admin access granted'}

def test_admin_required_no_token(client):
    response = client.get('/protected_admin')
    assert response.status_code == 401
    assert response.get_json()['message'] == 'Authentication required'

def test_admin_required_invalid_token(client):
    # Set an invalid token (cannot be decoded)
    client.set_cookie('localhost', 'admin_token', 'invalidtoken')
    response = client.get('/protected_admin')
    assert response.status_code == 401
    assert response.get_json()['message'] == 'Invalid token'

def test_admin_required_valid_token(client):
    secret = auth_app.config['SECRET_KEY']
    token = create_token(secret, {"some": "data"})
    client.set_cookie('localhost', 'admin_token', token)
    response = client.get('/protected_admin')
    assert response.status_code == 200
    assert response.get_json()['message'] == 'admin access granted'

# ----- User Required Tests -----

@auth_app.route('/protected_user')
@user_required
def protected_user():
    # The decorator sets request.user_id; we just return it for verification
    from flask import request
    return {'user_id': getattr(request, 'user_id', None)}

def test_user_required_no_token(client):
    response = client.get('/protected_user')
    assert response.status_code == 401
    assert response.get_json()['message'] == 'User authentication required'

def test_user_required_invalid_token(client):
    client.set_cookie('localhost', 'auth_token', 'invalidtoken')
    response = client.get('/protected_user')
    assert response.status_code == 401
    assert response.get_json()['message'] == 'Invalid session'

def test_user_required_valid_token(client):
    secret = auth_app.config['SECRET_KEY']
    token = create_token(secret, {"user_id": 42})
    client.set_cookie('localhost', 'auth_token', token)
    response = client.get('/protected_user')
    assert response.status_code == 200
    assert response.get_json()['user_id'] == 42

# ----- Health Endpoint Test -----

def test_health_endpoint(health_client):
    response = health_client.get('/health')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data == {'status': 'ok'}
