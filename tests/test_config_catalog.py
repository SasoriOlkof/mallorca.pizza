from pathlib import Path
from textwrap import dedent

import pytest
from pydantic import ValidationError

from mallorca_pizza.config import ConfigError, build_catalog
from mallorca_pizza.config.catalog import build_catalog_from_bundles
from mallorca_pizza.config.models import ImageAsset, MenuConfig, RestaurantConfig
from mallorca_pizza.config.yaml_loader import load_yaml_document
from mallorca_pizza.validate_config import run as run_validate_config

PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\r"
    b"IHDR"
    b"\x00\x00\x00\x01"
    b"\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00"
)


def write_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(PNG_1X1)


def write_restaurant(
    root: Path,
    restaurant_id: str,
    *,
    canonical_host: str | None = None,
    enabled: bool = True,
    logo_path: str = "branding/logo.png",
) -> Path:
    restaurant_dir = root / restaurant_id
    restaurant_dir.mkdir(parents=True)
    host = canonical_host or f"{restaurant_id}.mallorca.pizza"

    (restaurant_dir / "restaurant.yaml").write_text(
        dedent(
            f"""
            id: {restaurant_id}
            enabled: {str(enabled).lower()}
            canonical_host: {host}
            aliases: []
            name: {restaurant_id.title()} Pizzeria
            description: Plain pizza text
            assets:
              logo:
                path: {logo_path}
                alt: "{restaurant_id.title()} logo"
              hero:
                path: branding/hero.png
                alt: "Pizza on a table"
              gallery:
                - path: gallery/pizza.png
                  alt: "Pizza slice"
            blocks:
              - type: hero
                variant: centered
                title: {restaurant_id.title()} Pizzeria
                subtitle: Fresh pizza
                image: branding/hero.png
              - type: menu
                variant: full
                show_descriptions: true
              - type: gallery
                variant: grid
                images:
                  - gallery/pizza.png
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (restaurant_dir / "menu.yaml").write_text(
        dedent(
            """
            categories:
              - id: pizzas
                name: Pizzas
                items:
                  - id: margarita
                    name: Margarita
                    description: Tomato and mozzarella
                    price_cents: 895
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (restaurant_dir / "theme.yaml").write_text(
        dedent(
            """
            palette:
              primary: "#0f766e"
              accent: "#dc2626"
              background: "#fff7ed"
              surface: "#ffffff"
              text: "#111827"
            spacing: comfortable
            radius: medium
            shadow: soft
            density: normal
            font: system
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (restaurant_dir / "seo.yaml").write_text(
        dedent(
            """
            title: Shine Pizzeria
            description: Fresh pizza in Mallorca
            robots:
              index: true
              follow: true
            sitemap_paths:
              - /
            structured_data_enabled: true
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    write_png(restaurant_dir / "assets" / "branding" / "logo.png")
    write_png(restaurant_dir / "assets" / "branding" / "hero.png")
    write_png(restaurant_dir / "assets" / "gallery" / "pizza.png")
    return restaurant_dir


def test_yaml_loader_rejects_multiple_documents(tmp_path: Path) -> None:
    path = tmp_path / "multi.yaml"
    path.write_text("---\na: 1\n---\nb: 2\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="exactly one document"):
        load_yaml_document(path)


def test_yaml_loader_rejects_custom_tags(tmp_path: Path) -> None:
    path = tmp_path / "tag.yaml"
    path.write_text("value: !secret nope\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="Cannot parse YAML"):
        load_yaml_document(path)


def test_catalog_builds_immutable_allowlist_and_media(tmp_path: Path) -> None:
    write_restaurant(tmp_path, "shine", canonical_host="SHINE.mallorca.pizza.")

    catalog = build_catalog(tmp_path)

    assert catalog.host_allowlist == frozenset({"shine.mallorca.pizza"})
    assert len(catalog.enabled_restaurants) == 1
    bundle = catalog.restaurants_by_id["shine"]
    assert bundle.assets[0].media_path == "/media/shine/branding/logo.png"

    with pytest.raises(TypeError):
        catalog.restaurants_by_id["other"] = bundle  # type: ignore[index]


def test_disabled_restaurant_is_not_enabled_but_host_is_validated(
    tmp_path: Path,
) -> None:
    write_restaurant(tmp_path, "shine", enabled=False)

    catalog = build_catalog(tmp_path)

    assert catalog.host_allowlist == frozenset({"shine.mallorca.pizza"})
    assert catalog.enabled_restaurants == ()


def test_duplicate_hosts_are_rejected(tmp_path: Path) -> None:
    write_restaurant(tmp_path, "shine", canonical_host="pizza.mallorca.pizza")
    write_restaurant(tmp_path, "belly", canonical_host="pizza.mallorca.pizza")

    with pytest.raises(ConfigError, match="Duplicate host"):
        build_catalog(tmp_path)


def test_catalog_accepts_empty_restaurants_root(tmp_path: Path) -> None:
    catalog = build_catalog(tmp_path)

    assert catalog.restaurants_by_id == {}
    assert catalog.enabled_restaurants == ()


def test_price_float_is_rejected() -> None:
    with pytest.raises(ValidationError):
        MenuConfig.model_validate(
            {
                "categories": [
                    {
                        "id": "pizzas",
                        "name": "Pizzas",
                        "items": [
                            {
                                "id": "margarita",
                                "name": "Margarita",
                                "price_cents": 8.95,
                            }
                        ],
                    }
                ]
            }
        )


def test_block_union_rejects_unknown_options() -> None:
    with pytest.raises(ValidationError):
        RestaurantConfig.model_validate(
            {
                "id": "shine",
                "enabled": True,
                "canonical_host": "shine.mallorca.pizza",
                "aliases": [],
                "name": "Shine",
                "assets": {
                    "logo": {"path": "branding/logo.png", "alt": "Logo"},
                    "hero": {"path": "branding/hero.png", "alt": "Hero"},
                },
                "blocks": [
                    {
                        "type": "hero",
                        "variant": "centered",
                        "title": "Shine",
                        "template": "unsafe.html",
                    }
                ],
            }
        )


def test_image_requires_alt_or_decorative() -> None:
    with pytest.raises(ValidationError):
        ImageAsset.model_validate({"path": "branding/logo.png"})


def test_svg_asset_is_rejected(tmp_path: Path) -> None:
    restaurant_dir = write_restaurant(
        tmp_path,
        "shine",
        logo_path="branding/logo.svg",
    )
    svg_path = restaurant_dir / "assets" / "branding" / "logo.svg"
    svg_path.write_text("<svg></svg>", encoding="utf-8")

    with pytest.raises(ConfigError, match="Unsupported image extension"):
        build_catalog(tmp_path)


def test_asset_path_escape_is_rejected(tmp_path: Path) -> None:
    write_restaurant(tmp_path, "shine", logo_path="branding/../logo.png")

    with pytest.raises(ConfigError, match="Invalid asset path"):
        build_catalog(tmp_path)


def test_block_asset_references_must_be_declared(tmp_path: Path) -> None:
    restaurant_dir = write_restaurant(tmp_path, "shine")
    restaurant_yaml = restaurant_dir / "restaurant.yaml"
    restaurant_yaml.write_text(
        restaurant_yaml.read_text(encoding="utf-8").replace(
            "image: branding/hero.png",
            "image: branding/undeclared.png",
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="undeclared asset"):
        build_catalog(tmp_path)


def test_validate_config_command_accepts_empty_root(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = run_validate_config(["--restaurants-root", str(tmp_path)])

    captured = capsys.readouterr()
    assert result == 0
    assert "Configuration valid: 0 restaurant(s), 0 enabled." in captured.out


def test_duplicate_restaurant_ids_are_rejected(tmp_path: Path) -> None:
    first = build_catalog(tmp_path)
    assert first.restaurants_by_id == {}

    write_restaurant(tmp_path, "shine")
    bundle = build_catalog(tmp_path).restaurants_by_id["shine"]

    with pytest.raises(ConfigError, match="Duplicate restaurant id"):
        build_catalog_from_bundles([bundle, bundle])
