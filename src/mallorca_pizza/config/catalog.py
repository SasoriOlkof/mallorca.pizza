"""Immutable restaurant catalog construction."""

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import cast

from pydantic import ValidationError

from mallorca_pizza.config.assets import ValidatedAsset, validate_restaurant_assets
from mallorca_pizza.config.errors import ConfigError
from mallorca_pizza.config.models import (
    MenuConfig,
    RestaurantConfig,
    SeoConfig,
    ThemeConfig,
)
from mallorca_pizza.config.yaml_loader import load_yaml_document


@dataclass(frozen=True, slots=True)
class RestaurantBundle:
    root_dir: Path
    restaurant: RestaurantConfig
    menu: MenuConfig
    theme: ThemeConfig
    seo: SeoConfig
    assets: tuple[ValidatedAsset, ...]


@dataclass(frozen=True, slots=True)
class RestaurantCatalog:
    restaurants_by_id: MappingProxyType[str, RestaurantBundle]
    restaurants_by_host: MappingProxyType[str, RestaurantBundle]
    enabled_restaurants: tuple[RestaurantBundle, ...]

    @property
    def host_allowlist(self) -> frozenset[str]:
        return frozenset(self.restaurants_by_host)


def build_catalog(restaurants_root: Path) -> RestaurantCatalog:
    """Build an immutable catalog from all restaurant directories."""
    if not restaurants_root.exists():
        raise ConfigError(f"Restaurants root does not exist: {restaurants_root}")
    if not restaurants_root.is_dir():
        raise ConfigError(f"Restaurants root is not a directory: {restaurants_root}")

    bundles = [
        load_restaurant_bundle(path)
        for path in sorted(restaurants_root.iterdir())
        if path.is_dir()
    ]
    return build_catalog_from_bundles(bundles)


def build_catalog_from_bundles(
    bundles: list[RestaurantBundle],
) -> RestaurantCatalog:
    """Build an immutable catalog from already-loaded restaurant bundles."""
    restaurants_by_id: dict[str, RestaurantBundle] = {}
    restaurants_by_host: dict[str, RestaurantBundle] = {}
    enabled_restaurants: list[RestaurantBundle] = []

    for bundle in bundles:
        restaurant = bundle.restaurant
        if restaurant.id in restaurants_by_id:
            raise ConfigError(f"Duplicate restaurant id: {restaurant.id}")
        restaurants_by_id[restaurant.id] = bundle

        for host in (restaurant.canonical_host, *restaurant.aliases):
            existing = restaurants_by_host.get(host)
            if existing is not None:
                raise ConfigError(
                    f"Duplicate host {host!r} for restaurants "
                    f"{existing.restaurant.id!r} and {restaurant.id!r}"
                )
            restaurants_by_host[host] = bundle

        if restaurant.enabled:
            enabled_restaurants.append(bundle)

    return RestaurantCatalog(
        restaurants_by_id=MappingProxyType(restaurants_by_id),
        restaurants_by_host=MappingProxyType(restaurants_by_host),
        enabled_restaurants=tuple(enabled_restaurants),
    )


def load_restaurant_bundle(restaurant_dir: Path) -> RestaurantBundle:
    """Load and validate one restaurant directory."""
    restaurant = _load_model(
        restaurant_dir / "restaurant.yaml",
        RestaurantConfig,
    )
    menu = _load_model(restaurant_dir / "menu.yaml", MenuConfig)
    theme = _load_model(restaurant_dir / "theme.yaml", ThemeConfig)
    seo = _load_model(restaurant_dir / "seo.yaml", SeoConfig)

    if restaurant.id != restaurant_dir.name:
        raise ConfigError(
            f"Restaurant id {restaurant.id!r} must match directory "
            f"{restaurant_dir.name!r}"
        )

    assets = validate_restaurant_assets(restaurant.id, restaurant_dir, restaurant)
    return RestaurantBundle(
        root_dir=restaurant_dir,
        restaurant=restaurant,
        menu=menu,
        theme=theme,
        seo=seo,
        assets=assets,
    )


def _load_model[T: RestaurantConfig | MenuConfig | ThemeConfig | SeoConfig](
    path: Path,
    model_type: type[T],
) -> T:
    document = load_yaml_document(path)
    try:
        return cast(T, model_type.model_validate(document))
    except ValidationError as exc:
        raise ConfigError(f"Invalid configuration in {path}: {exc}") from exc
