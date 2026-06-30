import pytest

from mallorca_pizza.settings import (
    AppSettings,
    RuntimeSettingsError,
    parse_port,
    validate_runtime_settings,
)


def test_parse_port_accepts_valid_tcp_port() -> None:
    assert parse_port("8000") == 8000


@pytest.mark.parametrize("raw_port", ["", "abc", "0", "65536", "-1"])
def test_parse_port_rejects_invalid_values(raw_port: str) -> None:
    with pytest.raises(RuntimeSettingsError):
        parse_port(raw_port)


def test_production_rejects_wildcard_forwarded_allow_ips() -> None:
    settings = AppSettings(
        environment="production",
        forwarded_allow_ips="*",
    )

    with pytest.raises(RuntimeSettingsError, match="not allowed in production"):
        validate_runtime_settings(settings)


def test_development_allows_wildcard_forwarded_allow_ips() -> None:
    settings = AppSettings(
        environment="development",
        forwarded_allow_ips="*",
    )

    validate_runtime_settings(settings)


def test_bind_host_must_not_be_empty() -> None:
    settings = AppSettings(bind_host=" ")

    with pytest.raises(RuntimeSettingsError, match="BIND_HOST"):
        validate_runtime_settings(settings)
