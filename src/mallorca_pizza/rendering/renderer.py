"""Safe Jinja2 restaurant rendering."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from mallorca_pizza.config.assets import ValidatedAsset
from mallorca_pizza.config.catalog import RestaurantBundle
from mallorca_pizza.config.models import (
    BlockConfig,
    ContactBlock,
    DensityScale,
    GalleryBlock,
    HeroBlock,
    HoursBlock,
    MenuBlock,
    RadiusScale,
    ShadowScale,
    SpacingScale,
)

TEMPLATE_ROOT = Path(__file__).resolve().parent / "templates"


@dataclass(frozen=True, slots=True)
class RenderedBlock:
    template_name: str
    block: BlockConfig


@dataclass(frozen=True, slots=True)
class RestaurantPage:
    bundle: RestaurantBundle
    canonical_url: str
    blocks: tuple[RenderedBlock, ...]
    assets_by_path: dict[str, ValidatedAsset]

    @property
    def restaurant_id(self) -> str:
        return self.bundle.restaurant.id

    @property
    def restaurant_name(self) -> str:
        return self.bundle.restaurant.name

    @property
    def meta_title(self) -> str:
        return self.bundle.seo.title

    @property
    def meta_description(self) -> str:
        return self.bundle.seo.description

    @property
    def theme_variables(self) -> dict[str, str]:
        palette = self.bundle.theme.palette
        return {
            "--brand-primary": palette.primary,
            "--brand-accent": palette.accent,
            "--brand-background": palette.background,
            "--brand-surface": palette.surface,
            "--brand-text": palette.text,
            "--brand-spacing": spacing_value(self.bundle.theme.spacing),
            "--brand-radius": radius_value(self.bundle.theme.radius),
            "--brand-shadow": shadow_value(self.bundle.theme.shadow),
            "--brand-density": density_value(self.bundle.theme.density),
            "--brand-font": self.bundle.theme.font.value,
        }

    @property
    def structured_data(self) -> dict[str, Any]:
        restaurant = self.bundle.restaurant
        hero_asset = self.asset_for(restaurant.assets.hero.path)
        data: dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "Restaurant",
            "name": restaurant.name,
            "description": self.bundle.seo.description,
            "url": self.canonical_url,
            "servesCuisine": "Pizza",
        }
        if hero_asset is not None:
            data["image"] = (
                f"https://{restaurant.canonical_host}{hero_asset.media_path}"
            )
        if restaurant.contact is not None:
            if restaurant.contact.phone is not None:
                data["telephone"] = restaurant.contact.phone
            if restaurant.contact.address is not None:
                data["address"] = restaurant.contact.address
        return data

    def asset_for(self, logical_path: str | None) -> ValidatedAsset | None:
        if logical_path is None:
            return None
        return self.assets_by_path.get(logical_path)

    @staticmethod
    def price(cents: int) -> str:
        euros, centimos = divmod(cents, 100)
        return f"{euros},{centimos:02d} EUR"


class RestaurantRenderer:
    """Render restaurant pages using only registered internal templates."""

    def __init__(self, environment: Environment | None = None) -> None:
        self._environment = environment or create_environment()

    def render(self, bundle: RestaurantBundle, *, canonical_url: str) -> str:
        template = self._environment.get_template("restaurant.html")
        page = RestaurantPage(
            bundle=bundle,
            canonical_url=canonical_url,
            blocks=tuple(
                RenderedBlock(
                    template_name=template_for_block(block),
                    block=block,
                )
                for block in bundle.restaurant.blocks
            ),
            assets_by_path={asset.logical_path: asset for asset in bundle.assets},
        )
        return template.render(page=page)


def create_environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(TEMPLATE_ROOT),
        autoescape=select_autoescape(
            enabled_extensions=("html", "xml"),
            default_for_string=True,
        ),
        undefined=StrictUndefined,
    )


def template_for_block(block: object) -> str:
    if isinstance(block, HeroBlock):
        return "blocks/hero.html"
    if isinstance(block, MenuBlock):
        return "blocks/menu.html"
    if isinstance(block, GalleryBlock):
        return "blocks/gallery.html"
    if isinstance(block, HoursBlock):
        return "blocks/hours.html"
    if isinstance(block, ContactBlock):
        return "blocks/contact.html"

    msg = f"Unsupported block type: {type(block).__name__}"
    raise TypeError(msg)


def spacing_value(spacing: SpacingScale) -> str:
    return {
        SpacingScale.COMPACT: "0.75rem",
        SpacingScale.COMFORTABLE: "1rem",
        SpacingScale.GENEROUS: "1.5rem",
    }[spacing]


def radius_value(radius: RadiusScale) -> str:
    return {
        RadiusScale.NONE: "0",
        RadiusScale.SMALL: "0.25rem",
        RadiusScale.MEDIUM: "0.5rem",
    }[radius]


def shadow_value(shadow: ShadowScale) -> str:
    return {
        ShadowScale.NONE: "none",
        ShadowScale.SOFT: "0 0.5rem 1.5rem rgb(17 24 39 / 0.12)",
        ShadowScale.STRONG: "0 1rem 2rem rgb(17 24 39 / 0.2)",
    }[shadow]


def density_value(density: DensityScale) -> str:
    return {
        DensityScale.DENSE: "0.875",
        DensityScale.NORMAL: "1",
        DensityScale.AIRY: "1.125",
    }[density]
