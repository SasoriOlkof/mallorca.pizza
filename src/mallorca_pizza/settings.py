"""Application settings."""

from dataclasses import dataclass
from os import environ
from pathlib import Path


class RuntimeSettingsError(ValueError):
    """Raised when runtime settings are invalid."""


@dataclass(frozen=True, slots=True)
class AppSettings:
    restaurants_root: Path = Path("restaurants")
    static_root: Path = Path("static")
    bind_host: str = "0.0.0.0"
    port: int = 8000
    forwarded_allow_ips: str = "127.0.0.1"
    environment: str = "development"

    @classmethod
    def from_environment(cls) -> "AppSettings":
        return cls(
            restaurants_root=Path(environ.get("RESTAURANTS_ROOT", "restaurants")),
            static_root=Path(environ.get("STATIC_ROOT", "static")),
            bind_host=environ.get("BIND_HOST", "0.0.0.0"),
            port=parse_port(environ.get("PORT", "8000")),
            forwarded_allow_ips=environ.get("FORWARDED_ALLOW_IPS", "127.0.0.1"),
            environment=environ.get("ENVIRONMENT", "development"),
        )

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


def parse_port(raw_port: str) -> int:
    """Parse a TCP port from the environment."""
    if not raw_port.isdecimal():
        raise RuntimeSettingsError("PORT must be a decimal integer")
    port = int(raw_port)
    if port < 1 or port > 65535:
        raise RuntimeSettingsError("PORT must be between 1 and 65535")
    return port


def validate_runtime_settings(settings: AppSettings) -> None:
    """Validate runtime settings that are outside the YAML catalog."""
    if settings.bind_host.strip() == "":
        raise RuntimeSettingsError("BIND_HOST must not be empty")
    if settings.is_production and settings.forwarded_allow_ips.strip() == "*":
        raise RuntimeSettingsError(
            'FORWARDED_ALLOW_IPS="*" is not allowed in production',
        )
