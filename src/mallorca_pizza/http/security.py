"""HTTP security, cache and observability middleware."""

from collections.abc import Awaitable, Callable
from json import dumps
from logging import getLogger
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response

logger = getLogger("mallorca_pizza.requests")

ASSET_CACHE_CONTROL = "public, max-age=86400"
HTML_CACHE_CONTROL = "private, max-age=60"
SEO_CACHE_CONTROL = "public, max-age=300"
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "object-src 'none'; "
        "base-uri 'none'; "
        "frame-ancestors 'none'; "
        "form-action 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


async def security_and_observability_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Add headers and structured request logs."""
    request_id = get_request_id(request)
    start = perf_counter()
    response = await call_next(request)
    duration_ms = round((perf_counter() - start) * 1000, 3)

    response.headers["X-Request-ID"] = request_id
    for header, value in SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)
    apply_cache_policy(request, response)

    logger.info(
        dumps(
            {
                "request_id": request_id,
                "host": request.headers.get("host", ""),
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
            separators=(",", ":"),
        )
    )
    return response


def get_request_id(request: Request) -> str:
    candidate = request.headers.get("x-request-id")
    if candidate is None:
        return uuid4().hex
    if not candidate or len(candidate) > 100:
        return uuid4().hex
    if any(character.isspace() for character in candidate):
        return uuid4().hex
    return candidate


def apply_cache_policy(request: Request, response: Response) -> None:
    if "Cache-Control" in response.headers:
        return

    path = request.url.path
    if path.startswith(("/static/", "/media/")):
        response.headers["Cache-Control"] = ASSET_CACHE_CONTROL
    elif path in {"/robots.txt", "/sitemap.xml"}:
        response.headers["Cache-Control"] = SEO_CACHE_CONTROL
    elif response.headers.get("content-type", "").startswith("text/html"):
        response.headers["Cache-Control"] = HTML_CACHE_CONTROL
