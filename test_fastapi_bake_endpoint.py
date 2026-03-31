import pytest
from fastapi.testclient import TestClient
from soul.main import app

client = TestClient(app)


def test_post_bake_success():
    """POST /api/bake with valid data should return correct calculations."""
    payload = {"ingredients": [80, 40, 20]}
    response = client.post("/api/bake", json=payload)
    assert response.status_code == 200
    data = response.json()
    expected_total = sum(payload["ingredients"])
    expected_time = round(expected_total * 0.5, 2)
    assert data["total_weight"] == expected_total
    assert data["baking_time"] == expected_time


def test_post_bake_negative_ingredient_returns_400():
    """POST /api/bake with a negative ingredient should result in a 400 error."""
    payload = {"ingredients": [10, -3, 5]}
    response = client.post("/api/bake", json=payload)
    assert response.status_code == 400
    # FastAPI returns a detail field with the validation error message
    assert "non‑negative" in response.json().get("detail", "")


def test_post_bake_missing_ingredients_field():
    """If the request body lacks the required 'ingredients' field, FastAPI should return a 422 validation error."""
    payload = {"not_ingredients": [1, 2, 3]}
    response = client.post("/api/bake", json=payload)
    assert response.status_code == 422
    # Ensure the response mentions the missing field
    assert any(error.get("loc") == ["body", "ingredients"] for error in response.json().get("detail", []))
