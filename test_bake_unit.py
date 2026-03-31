import pytest
from soul.bake import bake


def test_bake_calculations():
    """Verify total weight and baking time calculation for a typical list of ingredients."""
    ingredients = [100.0, 50.5, 25.25]
    result = bake(ingredients)
    expected_total = sum(ingredients)
    expected_time = round(expected_total * 0.5, 2)
    assert result["total_weight"] == expected_total
    assert result["baking_time"] == expected_time


def test_bake_empty_list():
    """An empty ingredient list should result in zero weight and zero baking time."""
    result = bake([])
    assert result["total_weight"] == 0
    assert result["baking_time"] == 0


def test_bake_negative_quantity_raises():
    """Providing a negative ingredient quantity must raise a ValueError."""
    with pytest.raises(ValueError) as exc_info:
        bake([10, -5, 20])
    assert "non‑negative" in str(exc_info.value)
