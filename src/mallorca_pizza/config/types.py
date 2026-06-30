"""Shared Pydantic helpers for configuration models."""

from collections.abc import Sequence
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, Field, StrictStr

from mallorca_pizza.config import limits

ID_PATTERN = r"^[a-z][a-z0-9-]{1,48}[a-z0-9]$"
HOST_PATTERN = (
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)
HEX_COLOR_PATTERN = r"^#[0-9a-fA-F]{6}$"
PATH_PATTERN = r"^[a-zA-Z0-9][a-zA-Z0-9._/-]*$"


def ensure_yaml_list(value: object) -> object:
    """Require YAML sequences for list-like configuration fields."""
    if not isinstance(value, list):
        msg = "expected a YAML sequence"
        raise ValueError(msg)
    return value


def ensure_plain_text(value: str) -> str:
    """Reject markup-like text for v1 plain-text configuration fields."""
    if "<" in value or ">" in value:
        msg = "HTML-like markup is not allowed"
        raise ValueError(msg)
    return value


def normalize_host_value(value: object) -> object:
    """Normalize a configured host and reject malformed values."""
    if not isinstance(value, str):
        return value
    normalized = value.lower().rstrip(".")
    forbidden_fragments = ("/", "\\", " ", "\t", "\n", "\r", ",")
    if any(fragment in normalized for fragment in forbidden_fragments):
        msg = "host contains invalid characters"
        raise ValueError(msg)
    if ":" in normalized:
        msg = "configured hosts must not include ports"
        raise ValueError(msg)
    return normalized


def ensure_unique_sequence(values: Sequence[str]) -> Sequence[str]:
    """Reject duplicate values while preserving the original sequence."""
    if len(set(values)) != len(values):
        msg = "duplicate values are not allowed"
        raise ValueError(msg)
    return values


PlainText = Annotated[
    StrictStr,
    Field(min_length=1, max_length=limits.MAX_TEXT_LENGTH),
    AfterValidator(ensure_plain_text),
]
LongPlainText = Annotated[
    StrictStr,
    Field(min_length=1, max_length=limits.MAX_LONG_TEXT_LENGTH),
    AfterValidator(ensure_plain_text),
]
RestaurantId = Annotated[StrictStr, Field(pattern=ID_PATTERN)]
HostName = Annotated[
    StrictStr,
    BeforeValidator(normalize_host_value),
    Field(pattern=HOST_PATTERN),
]
HexColor = Annotated[StrictStr, Field(pattern=HEX_COLOR_PATTERN)]
AssetPath = Annotated[StrictStr, Field(pattern=PATH_PATTERN)]
PathList = Annotated[tuple[str, ...], BeforeValidator(ensure_yaml_list)]
