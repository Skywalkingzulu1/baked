import pytest
from soul.bake import bake

def test_bake_function():
    ingredients = [100.0, 50.0, 25.0]
    result = bake(ingredients)
    assert result["total_weight"] == sum(ingredients)
    assert result["baking_time"] == round(sum(ingredients) * 0.5, 2)