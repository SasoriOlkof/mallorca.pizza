"""Command-line configuration validation."""

from argparse import ArgumentParser
from collections.abc import Sequence
from pathlib import Path

from mallorca_pizza.config import ConfigError, build_catalog


def run(argv: Sequence[str] | None = None) -> int:
    parser = ArgumentParser(description="Validate Mallorca Pizza configuration.")
    parser.add_argument(
        "--restaurants-root",
        type=Path,
        default=Path("restaurants"),
        help="Path to the restaurants configuration directory.",
    )
    args = parser.parse_args(argv)

    try:
        catalog = build_catalog(args.restaurants_root)
    except ConfigError as exc:
        print(f"Configuration invalid: {exc}")
        return 1

    total = len(catalog.restaurants_by_id)
    enabled = len(catalog.enabled_restaurants)
    print(f"Configuration valid: {total} restaurant(s), {enabled} enabled.")
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
