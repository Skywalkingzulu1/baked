import pytest
from src.bake import bake


def test_bake_basic():
    """
    Verify that the function returns the correct total weight and
    baking time for a typical list of ingredient quantities.
    """
    result = bake([100, 200, 50])  # total = 350g
    assert result["total_weight"] == 350
    # 350 * 0.5 = 175.0 minutes
    assert result["baking_time"] == 175.0


def test_bake_empty_list():
    """
    An empty ingredient list should result in zero weight and zero time.
    """
    result = bake([])
    assert result["total_weight"] == 0
    assert result["baking_time"] == 0


def test_bake_negative_quantity_raises():
    """
    Supplying a negative ingredient quantity must raise a ValueError.
    """
    with pytest.raises(ValueError):
        bake([100, -20, 30])