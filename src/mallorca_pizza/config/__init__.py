"""Configuration loading and validation for Mallorca Pizza."""

from mallorca_pizza.config.catalog import (
    RestaurantBundle,
    RestaurantCatalog,
    build_catalog,
)
from mallorca_pizza.config.errors import ConfigError

__all__ = [
    "ConfigError",
    "RestaurantBundle",
    "RestaurantCatalog",
    "build_catalog",
]
