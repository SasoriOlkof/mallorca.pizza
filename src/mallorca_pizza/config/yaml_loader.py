"""Safe YAML loading helpers."""

from pathlib import Path

import yaml

from mallorca_pizza.config import limits
from mallorca_pizza.config.errors import ConfigError


def load_yaml_document(path: Path, *, max_bytes: int = limits.MAX_YAML_BYTES) -> object:
    """Load exactly one safe YAML document from a file."""
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ConfigError(f"Cannot stat YAML file {path}") from exc

    if size > max_bytes:
        raise ConfigError(f"YAML file {path} exceeds {max_bytes} bytes")

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"Cannot read YAML file {path}") from exc

    try:
        documents = list(yaml.safe_load_all(content))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Cannot parse YAML file {path}: {exc}") from exc

    if len(documents) != 1:
        raise ConfigError(f"YAML file {path} must contain exactly one document")

    document = documents[0]
    if document is None:
        raise ConfigError(f"YAML file {path} must not be empty")
    if not isinstance(document, dict):
        raise ConfigError(f"YAML file {path} must contain a mapping")
    return document
