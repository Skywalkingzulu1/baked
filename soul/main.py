"""
FastAPI endpoint for baking calculations.

This module defines a minimal FastAPI application with a single POST
endpoint `/api/bake`. The implementation is defensive: if FastAPI is
not available in the execution environment (e.g., during unit tests
that only target the Flask app), a lightweight stub is provided so
that the module can be imported without raising ImportError.
"""

# ----------------------------------------------------------------------
# Defensive import of FastAPI
# ----------------------------------------------------------------------
try:
    from fastapi import FastAPI, HTTPException
except Exception:  # pragma: no cover
    # Minimal stub implementations to allow the module to be imported
    class FastAPI:  # type: ignore
        def __init__(self, *args, **kwargs):
            self.routes = []

        def post(self, path: str):
            """Decorator that registers a POST route (no‑op stub)."""
            def decorator(func):
                self.routes.append(("POST", path, func))
                return func
            return decorator

    class HTTPException(Exception):  # type: ignore
        def __init__(self, status_code: int, detail: str = None):
            self.status_code = status_code
            self.detail = detail

# ----------------------------------------------------------------------
# Pydantic model for request validation
# ----------------------------------------------------------------------
from pydantic import BaseModel, validator
from typing import List

# Local import of the core baking logic (relative import for package flexibility)
from .bake import bake

# ----------------------------------------------------------------------
# FastAPI application instance
# ----------------------------------------------------------------------
app = FastAPI()


class BakeRequest(BaseModel):
    """
    Request schema for the /api/bake endpoint.

    The `ingredients` field must be a list of non‑negative floats.
    """
    ingredients: List[float]

    @validator("ingredients")
    def non_negative(cls, values):
        if any(qty < 0 for qty in values):
            raise ValueError("Ingredient quantities must be non‑negative")
        return values


# ----------------------------------------------------------------------
# Endpoint implementation
# ----------------------------------------------------------------------
@app.post("/api/bake")
def bake_endpoint(request: BakeRequest):
    """
    Receive a list of ingredient quantities and return the total weight
    and estimated baking time.

    Returns
    -------
    dict
        ``{"total_weight": float, "baking_time": float}``
    """
    try:
        result = bake(request.ingredients)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
