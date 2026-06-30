"""Uvicorn server entrypoint."""

import uvicorn

from mallorca_pizza.settings import AppSettings, validate_runtime_settings


def main() -> None:
    """Run the ASGI app with Uvicorn."""
    settings = AppSettings.from_environment()
    validate_runtime_settings(settings)
    uvicorn.run(
        "mallorca_pizza.main:app",
        host=settings.bind_host,
        port=settings.port,
        forwarded_allow_ips=settings.forwarded_allow_ips,
        proxy_headers=True,
    )


if __name__ == "__main__":
    main()
