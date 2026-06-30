"""FastAPI application entrypoint for Mallorca Pizza."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from random import choice
from typing import cast

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from mallorca_pizza import __version__
from mallorca_pizza.config import build_catalog
from mallorca_pizza.config.catalog import RestaurantCatalog
from mallorca_pizza.http.host_resolution import (
    APEX_HOST,
    resolve_host,
)
from mallorca_pizza.http.runtime import RuntimeState
from mallorca_pizza.http.security import security_and_observability_middleware
from mallorca_pizza.rendering import RestaurantRenderer
from mallorca_pizza.seo import (
    build_apex_robots,
    build_apex_sitemap,
    build_restaurant_robots,
    build_restaurant_sitemap,
    restaurant_canonical_url,
)
from mallorca_pizza.settings import AppSettings, validate_runtime_settings


def create_app(
    *,
    settings: AppSettings | None = None,
    catalog: RestaurantCatalog | None = None,
    load_catalog_on_startup: bool = True,
) -> FastAPI:
    """Create the FastAPI application."""
    app_settings = settings or AppSettings.from_environment()
    validate_runtime_settings(app_settings)
    runtime_state = RuntimeState(catalog=catalog)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.runtime = runtime_state
        if runtime_state.catalog is None and load_catalog_on_startup:
            runtime_state.catalog = build_catalog(app_settings.restaurants_root)
        yield

    app = FastAPI(
        title="Mallorca Pizza",
        summary="Host-resolved multi-site restaurant platform.",
        version=__version__,
        lifespan=lifespan,
    )
    app.state.runtime = runtime_state
    app.state.settings = app_settings
    app.state.renderer = RestaurantRenderer()
    app.middleware("http")(security_and_observability_middleware)
    app.mount(
        "/static",
        StaticFiles(directory=app_settings.static_root),
        name="static",
    )

    register_routes(app)
    return app


def register_routes(app: FastAPI) -> None:
    """Register phase 4 HTTP routes."""

    @app.get("/health/live", include_in_schema=False)
    def health_live() -> dict[str, str]:
        return {"status": "live"}

    @app.get("/health/ready", include_in_schema=False)
    def health_ready(request: Request) -> Response:
        runtime = get_runtime_state(request)
        if not runtime.ready:
            return JSONResponse({"status": "not_ready"}, status_code=503)
        return JSONResponse({"status": "ready"})

    @app.get("/robots.txt", include_in_schema=False)
    def robots_txt(request: Request) -> Response:
        return handle_robots_request(request)

    @app.get("/sitemap.xml", include_in_schema=False)
    def sitemap_xml(request: Request) -> Response:
        return handle_sitemap_request(request)

    @app.get("/media/{restaurant_id}/{asset_path:path}", include_in_schema=False)
    def media_asset(request: Request, restaurant_id: str, asset_path: str) -> Response:
        return handle_media_request(request, restaurant_id, asset_path)

    @app.get("/", include_in_schema=False)
    def root(request: Request) -> Response:
        return handle_resolved_request(request, route_exists=True)

    @app.get("/{path:path}", include_in_schema=False)
    def catch_all(request: Request, path: str) -> Response:
        return handle_resolved_request(request, route_exists=False)


def handle_resolved_request(request: Request, *, route_exists: bool) -> Response:
    """Resolve the request host and return the phase 4 response."""
    runtime = get_runtime_state(request)
    if runtime.catalog is None:
        return JSONResponse({"detail": "Service not ready"}, status_code=503)

    resolution = resolve_host(request.headers.get("host"), runtime.catalog)

    if resolution.kind == "www_apex":
        return temporary_redirect(request, APEX_HOST)

    if resolution.kind == "apex":
        if not route_exists:
            return controlled_not_found()
        if not runtime.catalog.enabled_restaurants:
            return JSONResponse({"detail": "No enabled restaurants"}, status_code=503)
        destination = choice(runtime.catalog.enabled_restaurants)
        response = temporary_redirect(request, destination.restaurant.canonical_host)
        response.headers["Cache-Control"] = "no-store"
        return response

    if resolution.kind == "alias":
        return temporary_redirect(request, resolution.bundle.restaurant.canonical_host)

    if resolution.kind == "unknown":
        return controlled_not_found()

    if resolution.kind == "disabled":
        return controlled_not_found()

    if not route_exists:
        return controlled_not_found()

    renderer = get_renderer(request)
    return HTMLResponse(
        renderer.render(
            resolution.bundle,
            canonical_url=restaurant_canonical_url(resolution.bundle),
        )
    )


def handle_robots_request(request: Request) -> Response:
    runtime = get_runtime_state(request)
    if runtime.catalog is None:
        return JSONResponse({"detail": "Service not ready"}, status_code=503)

    resolution = resolve_host(request.headers.get("host"), runtime.catalog)
    if resolution.kind == "www_apex":
        return temporary_redirect(request, APEX_HOST)
    if resolution.kind == "apex":
        return Response(build_apex_robots(), media_type="text/plain")
    if resolution.kind == "alias":
        return temporary_redirect(request, resolution.bundle.restaurant.canonical_host)
    if resolution.kind == "unknown":
        return controlled_not_found()
    if resolution.kind == "disabled":
        return controlled_not_found()
    return Response(build_restaurant_robots(resolution.bundle), media_type="text/plain")


def handle_sitemap_request(request: Request) -> Response:
    runtime = get_runtime_state(request)
    if runtime.catalog is None:
        return JSONResponse({"detail": "Service not ready"}, status_code=503)

    resolution = resolve_host(request.headers.get("host"), runtime.catalog)
    if resolution.kind == "www_apex":
        return temporary_redirect(request, APEX_HOST)
    if resolution.kind == "apex":
        return Response(
            build_apex_sitemap(runtime.catalog),
            media_type="application/xml",
        )
    if resolution.kind == "alias":
        return temporary_redirect(request, resolution.bundle.restaurant.canonical_host)
    if resolution.kind == "unknown":
        return controlled_not_found()
    if resolution.kind == "disabled":
        return controlled_not_found()
    return Response(
        build_restaurant_sitemap(resolution.bundle),
        media_type="application/xml",
    )


def handle_media_request(
    request: Request,
    restaurant_id: str,
    asset_path: str,
) -> Response:
    runtime = get_runtime_state(request)
    if runtime.catalog is None:
        return JSONResponse({"detail": "Service not ready"}, status_code=503)

    resolution = resolve_host(request.headers.get("host"), runtime.catalog)
    if resolution.kind == "alias":
        return temporary_redirect(request, resolution.bundle.restaurant.canonical_host)
    if resolution.kind != "canonical":
        return controlled_not_found()
    if resolution.bundle.restaurant.id != restaurant_id:
        return controlled_not_found()

    asset = next(
        (
            candidate
            for candidate in resolution.bundle.assets
            if candidate.logical_path == asset_path
        ),
        None,
    )
    if asset is None:
        return controlled_not_found()
    return FileResponse(asset.physical_path)


def temporary_redirect(request: Request, host: str) -> RedirectResponse:
    """Build a temporary redirect to a validated host."""
    path = canonical_path(request.url.path)
    query = f"?{request.url.query}" if request.url.query else ""
    return RedirectResponse(
        url=f"https://{host}{path}{query}",
        status_code=302,
    )


def canonical_path(path: str) -> str:
    """Normalize redirect paths by removing trailing slashes except root."""
    if path == "" or path == "/":
        return "/"
    return path.rstrip("/")


def controlled_not_found() -> JSONResponse:
    return JSONResponse({"detail": "Not Found"}, status_code=404)


def get_runtime_state(request: Request) -> RuntimeState:
    return cast(RuntimeState, request.app.state.runtime)


def get_renderer(request: Request) -> RestaurantRenderer:
    return cast(RestaurantRenderer, request.app.state.renderer)


app = create_app()
