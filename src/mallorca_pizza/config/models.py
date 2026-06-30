"""Pydantic models for restaurant configuration."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)

from mallorca_pizza.config import limits
from mallorca_pizza.config.types import (
    AssetPath,
    HexColor,
    HostName,
    LongPlainText,
    PlainText,
    RestaurantId,
    ensure_plain_text,
    ensure_unique_sequence,
    ensure_yaml_list,
)


def ensure_yaml_sequence_or_default_tuple(value: object) -> object:
    """Accept explicit YAML sequences and internal tuple defaults."""
    if isinstance(value, tuple):
        return value
    return ensure_yaml_list(value)


class ConfigBaseModel(BaseModel):
    """Base model shared by all configuration models."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class SpacingScale(StrEnum):
    COMPACT = "compact"
    COMFORTABLE = "comfortable"
    GENEROUS = "generous"


class RadiusScale(StrEnum):
    NONE = "none"
    SMALL = "small"
    MEDIUM = "medium"


class ShadowScale(StrEnum):
    NONE = "none"
    SOFT = "soft"
    STRONG = "strong"


class DensityScale(StrEnum):
    DENSE = "dense"
    NORMAL = "normal"
    AIRY = "airy"


class FontFamily(StrEnum):
    SYSTEM = "system"
    DISPLAY = "display"
    FRIENDLY = "friendly"


class HeroVariant(StrEnum):
    CENTERED = "centered"
    POSTER = "poster"
    SPLIT = "split"


class MenuVariant(StrEnum):
    COMPACT = "compact"
    FULL = "full"


class GalleryVariant(StrEnum):
    GRID = "grid"
    STRIP = "strip"


class HoursVariant(StrEnum):
    SIMPLE = "simple"
    WEEKLY = "weekly"


class ContactVariant(StrEnum):
    SIMPLE = "simple"
    FEATURED = "featured"


YamlTextList = Annotated[tuple[PlainText, ...], Field(max_length=20)]
YamlHostList = Annotated[
    tuple[HostName, ...],
    Field(max_length=limits.MAX_ALIASES),
    AfterValidator(ensure_unique_sequence),
]
YamlImageList = Annotated[
    tuple[AssetPath, ...],
    Field(max_length=limits.MAX_GALLERY_IMAGES),
]


class ImageAsset(ConfigBaseModel):
    path: AssetPath
    alt: PlainText | None = None
    decorative: StrictBool = False

    @model_validator(mode="after")
    def require_alt_or_decorative(self) -> "ImageAsset":
        if self.decorative and self.alt is not None:
            msg = "decorative images must not define alt text"
            raise ValueError(msg)
        if not self.decorative and self.alt is None:
            msg = "images must define alt text or decorative: true"
            raise ValueError(msg)
        return self


class RestaurantAssets(ConfigBaseModel):
    logo: ImageAsset
    hero: ImageAsset
    gallery: Annotated[
        tuple[ImageAsset, ...],
        Field(default_factory=tuple, max_length=limits.MAX_GALLERY_IMAGES),
    ]

    @field_validator("gallery", mode="before")
    @classmethod
    def require_gallery_sequence(cls, value: object) -> object:
        if value is None:
            return []
        return ensure_yaml_sequence_or_default_tuple(value)


class ContactConfig(ConfigBaseModel):
    phone: PlainText | None = None
    email: PlainText | None = None
    address: PlainText | None = None


class LocationConfig(ConfigBaseModel):
    locality: PlainText
    region: PlainText | None = None
    country: PlainText = "ES"
    latitude: float | None = None
    longitude: float | None = None


class OpeningHoursPeriod(ConfigBaseModel):
    label: PlainText
    value: PlainText


class HeroBlock(ConfigBaseModel):
    type: Literal["hero"]
    variant: HeroVariant
    title: PlainText
    subtitle: PlainText | None = None
    image: AssetPath | None = None


class MenuBlock(ConfigBaseModel):
    type: Literal["menu"]
    variant: MenuVariant
    show_descriptions: StrictBool = True


class GalleryBlock(ConfigBaseModel):
    type: Literal["gallery"]
    variant: GalleryVariant
    images: YamlImageList

    @field_validator("images", mode="before")
    @classmethod
    def require_images_sequence(cls, value: object) -> object:
        return ensure_yaml_list(value)


class HoursBlock(ConfigBaseModel):
    type: Literal["hours"]
    variant: HoursVariant


class ContactBlock(ConfigBaseModel):
    type: Literal["contact"]
    variant: ContactVariant


BlockConfig = Annotated[
    HeroBlock | MenuBlock | GalleryBlock | HoursBlock | ContactBlock,
    Field(discriminator="type"),
]


class RestaurantConfig(ConfigBaseModel):
    id: RestaurantId
    enabled: StrictBool
    canonical_host: HostName
    aliases: YamlHostList = ()
    name: PlainText
    description: LongPlainText | None = None
    contact: ContactConfig | None = None
    location: LocationConfig | None = None
    opening_hours: Annotated[
        tuple[OpeningHoursPeriod, ...],
        Field(default_factory=tuple, max_length=14),
    ]
    assets: RestaurantAssets
    blocks: Annotated[
        tuple[BlockConfig, ...],
        Field(default_factory=tuple, max_length=limits.MAX_BLOCKS),
    ]

    @field_validator("aliases", mode="before")
    @classmethod
    def require_alias_sequence(cls, value: object) -> object:
        if value is None:
            return []
        return ensure_yaml_sequence_or_default_tuple(value)

    @field_validator("opening_hours", "blocks", mode="before")
    @classmethod
    def require_sequence(cls, value: object) -> object:
        if value is None:
            return []
        return ensure_yaml_sequence_or_default_tuple(value)

    @model_validator(mode="after")
    def reject_canonical_host_in_aliases(self) -> "RestaurantConfig":
        if self.canonical_host in self.aliases:
            msg = "canonical_host must not be repeated in aliases"
            raise ValueError(msg)
        return self


class MenuItem(ConfigBaseModel):
    id: RestaurantId
    name: PlainText
    description: LongPlainText | None = None
    price_cents: Annotated[StrictInt, Field(ge=0, le=100_000)]


class MenuCategory(ConfigBaseModel):
    id: RestaurantId
    name: PlainText
    items: Annotated[
        tuple[MenuItem, ...],
        Field(min_length=1, max_length=limits.MAX_MENU_ITEMS_PER_CATEGORY),
    ]

    @field_validator("items", mode="before")
    @classmethod
    def require_items_sequence(cls, value: object) -> object:
        return ensure_yaml_list(value)


class MenuConfig(ConfigBaseModel):
    categories: Annotated[
        tuple[MenuCategory, ...],
        Field(min_length=1, max_length=limits.MAX_CATEGORIES),
    ]

    @field_validator("categories", mode="before")
    @classmethod
    def require_categories_sequence(cls, value: object) -> object:
        return ensure_yaml_list(value)

    @model_validator(mode="after")
    def reject_duplicate_categories(self) -> "MenuConfig":
        category_ids = [category.id for category in self.categories]
        ensure_unique_sequence(category_ids)
        for category in self.categories:
            item_ids = [item.id for item in category.items]
            ensure_unique_sequence(item_ids)
        return self


class PaletteConfig(ConfigBaseModel):
    primary: HexColor
    accent: HexColor
    background: HexColor
    surface: HexColor
    text: HexColor


class ThemeConfig(ConfigBaseModel):
    palette: PaletteConfig
    spacing: SpacingScale
    radius: RadiusScale
    shadow: ShadowScale
    density: DensityScale
    font: FontFamily = FontFamily.SYSTEM


class RobotsConfig(ConfigBaseModel):
    index: StrictBool
    follow: StrictBool


def validate_sitemap_path(value: str) -> str:
    if not value.startswith("/"):
        msg = "sitemap paths must start with /"
        raise ValueError(msg)
    if "//" in value or "\\" in value:
        msg = "sitemap path is malformed"
        raise ValueError(msg)
    return value


SitemapPath = Annotated[
    StrictStr,
    Field(min_length=1, max_length=120),
    AfterValidator(ensure_plain_text),
    AfterValidator(validate_sitemap_path),
]


class SeoConfig(ConfigBaseModel):
    title: PlainText
    description: LongPlainText
    robots: RobotsConfig
    sitemap_paths: Annotated[
        tuple[SitemapPath, ...],
        Field(default=("/",), max_length=limits.MAX_SITEMAP_PATHS),
    ]
    structured_data_enabled: StrictBool = True

    @field_validator("sitemap_paths", mode="before")
    @classmethod
    def require_sitemap_sequence(cls, value: object) -> object:
        if value is None:
            return ["/"]
        return ensure_yaml_sequence_or_default_tuple(value)

    @model_validator(mode="after")
    def reject_duplicate_sitemap_paths(self) -> "SeoConfig":
        ensure_unique_sequence(list(self.sitemap_paths))
        return self
