import pytest
from src.app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok'}

def test_index_served(client):
    response = client.get('/')
    assert response.status_code == 200
    # Should return HTML content
    assert b'<title>Bud Credit Form</title>' in response.data