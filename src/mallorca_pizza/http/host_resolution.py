"""Host normalization and restaurant resolution for HTTP requests."""

from dataclasses import dataclass
from re import fullmatch
from typing import Literal

from mallorca_pizza.config.catalog import RestaurantBundle, RestaurantCatalog

APEX_HOST = "mallorca.pizza"
WWW_APEX_HOST = "www.mallorca.pizza"

HOST_PATTERN = (
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
)


class HostNormalizationError(ValueError):
    """Raised when a request host cannot be safely normalized."""


@dataclass(frozen=True, slots=True)
class ApexResolution:
    kind: Literal["apex"]
    host: str


@dataclass(frozen=True, slots=True)
class WwwApexResolution:
    kind: Literal["www_apex"]
    host: str


@dataclass(frozen=True, slots=True)
class UnknownHostResolution:
    kind: Literal["unknown"]
    host: str | None


@dataclass(frozen=True, slots=True)
class DisabledRestaurantResolution:
    kind: Literal["disabled"]
    host: str
    bundle: RestaurantBundle


@dataclass(frozen=True, slots=True)
class CanonicalRestaurantResolution:
    kind: Literal["canonical"]
    host: str
    bundle: RestaurantBundle


@dataclass(frozen=True, slots=True)
class AliasRestaurantResolution:
    kind: Literal["alias"]
    host: str
    bundle: RestaurantBundle


HostResolution = (
    ApexResolution
    | WwwApexResolution
    | UnknownHostResolution
    | DisabledRestaurantResolution
    | CanonicalRestaurantResolution
    | AliasRestaurantResolution
)


def normalize_request_host(host_header: str | None) -> str:
    """Normalize an HTTP Host header without trusting it."""
    if host_header is None or host_header == "":
        raise HostNormalizationError("missing host")

    if host_header != host_header.strip():
        raise HostNormalizationError("host contains surrounding whitespace")

    forbidden_fragments = ("/", "\\", " ", "\t", "\n", "\r", ",")
    if any(fragment in host_header for fragment in forbidden_fragments):
        raise HostNormalizationError("host contains invalid characters")

    host = host_header
    if ":" in host:
        host_part, separator, port_part = host.rpartition(":")
        if separator == "" or host_part == "" or not port_part.isdecimal():
            raise HostNormalizationError("host has invalid port")
        host = host_part

    normalized = host.lower().rstrip(".")
    if normalized == "":
        raise HostNormalizationError("host is empty after normalization")

    if not fullmatch(HOST_PATTERN, normalized):
        raise HostNormalizationError("host is not a valid domain")

    return normalized


def resolve_host(
    host_header: str | None,
    catalog: RestaurantCatalog,
) -> HostResolution:
    """Resolve a request host against the immutable restaurant catalog."""
    try:
        host = normalize_request_host(host_header)
    except HostNormalizationError:
        return UnknownHostResolution(kind="unknown", host=None)

    if host == APEX_HOST:
        return ApexResolution(kind="apex", host=host)
    if host == WWW_APEX_HOST:
        return WwwApexResolution(kind="www_apex", host=host)

    bundle = catalog.restaurants_by_host.get(host)
    if bundle is None:
        return UnknownHostResolution(kind="unknown", host=host)

    if not bundle.restaurant.enabled:
        return DisabledRestaurantResolution(kind="disabled", host=host, bundle=bundle)

    if host == bundle.restaurant.canonical_host:
        return CanonicalRestaurantResolution(
            kind="canonical",
            host=host,
            bundle=bundle,
        )

    return AliasRestaurantResolution(kind="alias", host=host, bundle=bundle)
