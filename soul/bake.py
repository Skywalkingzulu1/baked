"""
Core baking algorithm.

Provides a `bake` function that calculates the total weight of the
ingredients and an estimated baking time based on that weight.

The algorithm is deliberately simple so that it can be exercised by
unit tests without requiring any external dependencies.
"""

from typing import List, Dict


def bake(ingredients: List[float]) -> Dict[str, float]:
    """
    Calculate total weight and estimated baking time.

    Parameters
    ----------
    ingredients: List[float]
        Quantities of each ingredient in grams. All values must be
        non‑negative.

    Returns
    -------
    dict
        A dictionary with two keys:
        - ``total_weight``: sum of the ingredient quantities.
        - ``baking_time``: estimated baking time in minutes, calculated
          as ``total_weight * 0.5`` and rounded to two decimal places.

    Raises
    ------
    ValueError
        If any ingredient quantity is negative.
    """
    # Validate input – negative quantities do not make sense in a baking
    # context and should be rejected early.
    if any(qty < 0 for qty in ingredients):
        raise ValueError("Ingredient quantities must be non‑negative")

    total_weight = sum(ingredients)
    # The simple heuristic: 0.5 minutes of baking per gram.
    baking_time = round(total_weight * 0.5, 2)

    return {"total_weight": total_weight, "baking_time": baking_time}
