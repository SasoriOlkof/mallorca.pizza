from starlette.routing import Route

from mallorca_pizza import __version__
from mallorca_pizza.main import create_app


def test_create_app_sets_project_metadata() -> None:
    app = create_app()

    assert app.title == "Mallorca Pizza"
    assert app.version == __version__


def test_minimal_app_has_no_restaurant_routes_yet() -> None:
    app = create_app()
    registered_paths = {route.path for route in app.routes if isinstance(route, Route)}

    assert "/" in registered_paths
    assert "/health/live" in registered_paths
    assert "/health/ready" in registered_paths
