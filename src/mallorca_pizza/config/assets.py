"""Asset validation for restaurant media."""

from dataclasses import dataclass
from pathlib import Path
from struct import unpack

from mallorca_pizza.config import limits
from mallorca_pizza.config.errors import ConfigError
from mallorca_pizza.config.models import (
    GalleryBlock,
    HeroBlock,
    ImageAsset,
    RestaurantConfig,
)

ALLOWED_IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})


@dataclass(frozen=True, slots=True)
class ValidatedAsset:
    logical_path: str
    physical_path: Path
    media_path: str
    alt: str | None
    decorative: bool
    width: int
    height: int
    size_bytes: int


def validate_restaurant_assets(
    restaurant_id: str,
    restaurant_dir: Path,
    config: RestaurantConfig,
) -> tuple[ValidatedAsset, ...]:
    """Validate all assets referenced by a restaurant configuration."""
    assets_dir = restaurant_dir / "assets"
    image_assets = _collect_image_assets(config)
    _validate_block_asset_references(config, image_assets)
    validated_assets = [
        validate_image_asset(restaurant_id, assets_dir, image_asset)
        for image_asset in image_assets.values()
    ]
    return tuple(validated_assets)


def validate_image_asset(
    restaurant_id: str,
    assets_dir: Path,
    image_asset: ImageAsset,
) -> ValidatedAsset:
    """Validate one configured image asset."""
    logical_path = image_asset.path
    if "\\" in logical_path or logical_path.startswith("/") or ".." in logical_path:
        raise ConfigError(f"Invalid asset path {logical_path!r}")

    extension = Path(logical_path).suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ConfigError(f"Unsupported image extension for {logical_path!r}")

    assets_root = assets_dir.resolve()
    physical_path = (assets_root / logical_path).resolve()
    try:
        physical_path.relative_to(assets_root)
    except ValueError as exc:
        raise ConfigError(
            f"Asset path escapes restaurant assets: {logical_path}"
        ) from exc

    try:
        size_bytes = physical_path.stat().st_size
    except OSError as exc:
        raise ConfigError(f"Missing asset {logical_path!r}") from exc

    if size_bytes > limits.MAX_IMAGE_BYTES:
        raise ConfigError(f"Asset {logical_path!r} exceeds size limit")

    try:
        data = physical_path.read_bytes()
    except OSError as exc:
        raise ConfigError(f"Cannot read asset {logical_path!r}") from exc

    width, height = read_image_dimensions(data, extension)
    if width < 1 or height < 1:
        raise ConfigError(f"Asset {logical_path!r} has invalid dimensions")
    if width > limits.MAX_IMAGE_WIDTH or height > limits.MAX_IMAGE_HEIGHT:
        raise ConfigError(f"Asset {logical_path!r} exceeds dimension limits")

    return ValidatedAsset(
        logical_path=logical_path,
        physical_path=physical_path,
        media_path=f"/media/{restaurant_id}/{logical_path}",
        alt=image_asset.alt,
        decorative=image_asset.decorative,
        width=width,
        height=height,
        size_bytes=size_bytes,
    )


def read_image_dimensions(data: bytes, extension: str) -> tuple[int, int]:
    """Read dimensions for v1 supported image formats."""
    if extension == ".png":
        return _read_png_dimensions(data)
    if extension in {".jpg", ".jpeg"}:
        return _read_jpeg_dimensions(data)
    if extension == ".webp":
        return _read_webp_dimensions(data)
    raise ConfigError(f"Unsupported image extension {extension!r}")


def _collect_image_assets(config: RestaurantConfig) -> dict[str, ImageAsset]:
    assets: list[ImageAsset] = [config.assets.logo, config.assets.hero]
    assets.extend(config.assets.gallery)

    image_assets: dict[str, ImageAsset] = {}
    for asset in assets:
        image_assets.setdefault(asset.path, asset)
    return image_assets


def _validate_block_asset_references(
    config: RestaurantConfig,
    image_assets: dict[str, ImageAsset],
) -> None:
    for block in config.blocks:
        if isinstance(block, HeroBlock) and block.image is not None:
            _require_declared_asset(block.image, image_assets)
        elif isinstance(block, GalleryBlock):
            for path in block.images:
                _require_declared_asset(path, image_assets)


def _require_declared_asset(
    logical_path: str,
    image_assets: dict[str, ImageAsset],
) -> None:
    if logical_path not in image_assets:
        raise ConfigError(f"Block references undeclared asset {logical_path!r}")


def _read_png_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ConfigError("Invalid PNG image")
    return unpack(">II", data[16:24])


def _read_jpeg_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        raise ConfigError("Invalid JPEG image")

    index = 2
    while index < len(data):
        while index < len(data) and data[index] == 0xFF:
            index += 1
        if index >= len(data):
            break

        marker = data[index]
        index += 1
        if marker in {0xD8, 0xD9}:
            continue
        if index + 2 > len(data):
            break

        segment_length = unpack(">H", data[index : index + 2])[0]
        if segment_length < 2 or index + segment_length > len(data):
            break

        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }:
            if segment_length < 7:
                break
            height = unpack(">H", data[index + 3 : index + 5])[0]
            width = unpack(">H", data[index + 5 : index + 7])[0]
            return width, height

        index += segment_length

    raise ConfigError("Cannot read JPEG dimensions")


def _read_webp_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ConfigError("Invalid WebP image")

    chunk_type = data[12:16]
    if chunk_type == b"VP8X":
        width = int.from_bytes(data[24:27], "little") + 1
        height = int.from_bytes(data[27:30], "little") + 1
        return width, height

    if chunk_type == b"VP8L":
        if len(data) < 25 or data[20] != 0x2F:
            raise ConfigError("Invalid WebP lossless image")
        b1, b2, b3, b4 = data[21:25]
        width = 1 + b1 + ((b2 & 0x3F) << 8)
        height = 1 + ((b2 & 0xC0) >> 6) + (b3 << 2) + ((b4 & 0x0F) << 10)
        return width, height

    if chunk_type == b"VP8 ":
        if len(data) < 30 or data[23:26] != b"\x9d\x01\x2a":
            raise ConfigError("Invalid WebP lossy image")
        width = unpack("<H", data[26:28])[0] & 0x3FFF
        height = unpack("<H", data[28:30])[0] & 0x3FFF
        return width, height

    raise ConfigError("Unsupported WebP image chunk")
