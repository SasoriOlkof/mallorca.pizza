from json import loads
from pathlib import Path
from textwrap import dedent

import pytest
from starlette.testclient import TestClient

from mallorca_pizza.config import build_catalog
from mallorca_pizza.main import create_app

PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\r"
    b"IHDR"
    b"\x00\x00\x00\x01"
    b"\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00"
)


def write_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(PNG_1X1)


def write_restaurant(
    root: Path,
    restaurant_id: str,
    *,
    canonical_host: str | None = None,
    aliases: tuple[str, ...] = (),
    enabled: bool = True,
    description: str = "Plain pizza text",
    item_description: str = "Tomato and mozzarella",
) -> None:
    restaurant_dir = root / restaurant_id
    restaurant_dir.mkdir(parents=True)
    host = canonical_host or f"{restaurant_id}.mallorca.pizza"
    aliases_yaml = "\n".join(f"  - {alias}" for alias in aliases)
    if aliases_yaml == "":
        aliases_yaml = "  []"

    (restaurant_dir / "restaurant.yaml").write_text(
        dedent(
            f"""
            id: {restaurant_id}
            enabled: {str(enabled).lower()}
            canonical_host: {host}
            aliases:
            {aliases_yaml}
            name: {restaurant_id.title()} Pizzeria
            description: {description}
            assets:
              logo:
                path: branding/logo.png
                alt: "{restaurant_id.title()} logo"
              hero:
                path: branding/hero.png
                alt: "Pizza on a table"
            blocks:
              - type: menu
                variant: full
                show_descriptions: true
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (restaurant_dir / "menu.yaml").write_text(
        dedent(
            f"""
            categories:
              - id: pizzas
                name: Pizzas
                items:
                  - id: margarita
                    name: Margarita
                    description: {item_description}
                    price_cents: 895
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (restaurant_dir / "theme.yaml").write_text(
        dedent(
            """
            palette:
              primary: "#0f766e"
              accent: "#dc2626"
              background: "#fff7ed"
              surface: "#ffffff"
              text: "#111827"
            spacing: comfortable
            radius: medium
            shadow: soft
            density: normal
            font: system
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (restaurant_dir / "seo.yaml").write_text(
        dedent(
            """
            title: Test Pizzeria
            description: Fresh pizza in Mallorca
            robots:
              index: true
              follow: true
            sitemap_paths:
              - /
            structured_data_enabled: true
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    write_png(restaurant_dir / "assets" / "branding" / "logo.png")
    write_png(restaurant_dir / "assets" / "branding" / "hero.png")


def make_client(restaurants_root: Path) -> TestClient:
    catalog = build_catalog(restaurants_root)
    return TestClient(create_app(catalog=catalog))


def test_health_endpoints_do_not_resolve_host(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        live = client.get("/health/live", headers={"Host": "bad host"})
        ready = client.get("/health/ready", headers={"Host": "bad host"})

    assert live.status_code == 200
    assert live.json() == {"status": "live"}
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready"}


def test_ready_returns_503_before_catalog_is_loaded() -> None:
    app = create_app(load_catalog_on_startup=False)

    with TestClient(app) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}


def test_root_domain_returns_503_when_no_restaurants_are_enabled(
    tmp_path: Path,
) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/", headers={"Host": "mallorca.pizza"})

    assert response.status_code == 503
    assert response.json() == {"detail": "No enabled restaurants"}


def test_root_domain_redirects_to_enabled_restaurant_with_no_store(
    tmp_path: Path,
) -> None:
    write_restaurant(tmp_path, "shine")
    write_restaurant(tmp_path, "belly")

    with make_client(tmp_path) as client:
        response = client.get(
            "/",
            headers={"Host": "mallorca.pizza"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["location"] in {
        "https://shine.mallorca.pizza/",
        "https://belly.mallorca.pizza/",
    }


def test_www_apex_redirects_to_apex(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get(
            "/anything/?a=1",
            headers={"Host": "www.mallorca.pizza"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["location"] == "https://mallorca.pizza/anything?a=1"


def test_canonical_restaurant_host_renders_html(tmp_path: Path) -> None:
    write_restaurant(tmp_path, "shine")

    with make_client(tmp_path) as client:
        response = client.get("/", headers={"Host": "shine.mallorca.pizza"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.headers["Cache-Control"] == "private, max-age=60"
    assert 'data-restaurant="shine"' in response.text
    assert "<title>Test Pizzeria</title>" in response.text
    assert (
        '<meta name="description" content="Fresh pizza in Mallorca">' in response.text
    )
    assert (
        '<link rel="canonical" href="https://shine.mallorca.pizza/">' in response.text
    )
    assert '<link rel="stylesheet" href="/static/css/site.css">' in response.text
    assert "<h1>Shine Pizzeria</h1>" in response.text
    assert "Margarita" in response.text
    assert "8,95 EUR" in response.text


def test_host_normalization_allows_port_and_trailing_dot(tmp_path: Path) -> None:
    write_restaurant(tmp_path, "shine")

    with make_client(tmp_path) as client:
        response = client.get("/", headers={"Host": "SHINE.mallorca.pizza.:8000"})

    assert response.status_code == 200
    assert 'data-restaurant="shine"' in response.text


def test_alias_redirects_to_canonical_host(tmp_path: Path) -> None:
    write_restaurant(
        tmp_path,
        "shine",
        aliases=("pizza-shine.mallorca.pizza",),
    )

    with make_client(tmp_path) as client:
        response = client.get(
            "/menu/?size=large",
            headers={"Host": "pizza-shine.mallorca.pizza"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert (
        response.headers["location"] == "https://shine.mallorca.pizza/menu?size=large"
    )


def test_unknown_host_returns_404(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/", headers={"Host": "unknown.mallorca.pizza"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_malicious_host_returns_404(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get(
            "/",
            headers={"Host": "shine.mallorca.pizza,evil.example"},
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_disabled_restaurant_host_returns_404(tmp_path: Path) -> None:
    write_restaurant(tmp_path, "shine", enabled=False)

    with make_client(tmp_path) as client:
        response = client.get("/", headers={"Host": "shine.mallorca.pizza"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_unknown_route_on_valid_host_returns_404(tmp_path: Path) -> None:
    write_restaurant(tmp_path, "shine")

    with make_client(tmp_path) as client:
        response = client.get("/not-found", headers={"Host": "shine.mallorca.pizza"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_yaml_text_is_rendered_as_escaped_plain_text(tmp_path: Path) -> None:
    write_restaurant(
        tmp_path,
        "shine",
        description="Fresh & bright **pizza**",
        item_description="Tomato & mozzarella **classic**",
    )

    with make_client(tmp_path) as client:
        response = client.get("/", headers={"Host": "shine.mallorca.pizza"})

    assert response.status_code == 200
    assert "Fresh &amp; bright **pizza**" in response.text
    assert "Tomato &amp; mozzarella **classic**" in response.text
    assert "<strong>classic</strong>" not in response.text


def test_templates_do_not_use_safe_filter() -> None:
    template_root = Path("src/mallorca_pizza/rendering/templates")

    for template in template_root.rglob("*.html"):
        assert "|safe" not in template.read_text(encoding="utf-8")


def test_structured_data_is_rendered_from_python_object(tmp_path: Path) -> None:
    write_restaurant(tmp_path, "shine")

    with make_client(tmp_path) as client:
        response = client.get("/", headers={"Host": "shine.mallorca.pizza"})

    marker = '<script type="application/ld+json">'
    start = response.text.index(marker) + len(marker)
    end = response.text.index("</script>", start)
    structured_data = loads(response.text[start:end])
    assert structured_data["@context"] == "https://schema.org"
    assert structured_data["@type"] == "Restaurant"
    assert structured_data["name"] == "Shine Pizzeria"
    assert structured_data["url"] == "https://shine.mallorca.pizza/"


def test_security_headers_and_request_id_are_added(tmp_path: Path) -> None:
    write_restaurant(tmp_path, "shine")

    with make_client(tmp_path) as client:
        response = client.get(
            "/",
            headers={
                "Host": "shine.mallorca.pizza",
                "X-Request-ID": "request-123",
            },
        )

    assert response.headers["X-Request-ID"] == "request-123"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["Permissions-Policy"] == (
        "camera=(), microphone=(), geolocation=()"
    )


def test_request_log_is_structured(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    write_restaurant(tmp_path, "shine")
    caplog.set_level("INFO", logger="mallorca_pizza.requests")

    with make_client(tmp_path) as client:
        client.get("/", headers={"Host": "shine.mallorca.pizza"})

    log_payload = loads(caplog.records[-1].message)
    assert log_payload["host"] == "shine.mallorca.pizza"
    assert log_payload["path"] == "/"
    assert log_payload["status"] == 200
    assert "duration_ms" in log_payload
    assert "request_id" in log_payload


def test_static_assets_are_served_with_moderate_cache(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/static/css/site.css")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "public, max-age=86400"
    assert "--brand-primary" in response.text


def test_restaurant_media_is_served_only_for_own_canonical_host(
    tmp_path: Path,
) -> None:
    write_restaurant(tmp_path, "shine")
    write_restaurant(tmp_path, "belly")

    with make_client(tmp_path) as client:
        own_asset = client.get(
            "/media/shine/branding/logo.png",
            headers={"Host": "shine.mallorca.pizza"},
        )
        cross_brand = client.get(
            "/media/belly/branding/logo.png",
            headers={"Host": "shine.mallorca.pizza"},
        )
        undeclared = client.get(
            "/media/shine/branding/missing.png",
            headers={"Host": "shine.mallorca.pizza"},
        )

    assert own_asset.status_code == 200
    assert own_asset.headers["Cache-Control"] == "public, max-age=86400"
    assert own_asset.content.startswith(PNG_1X1[:8])
    assert cross_brand.status_code == 404
    assert undeclared.status_code == 404


def test_restaurant_media_alias_redirects_to_canonical(tmp_path: Path) -> None:
    write_restaurant(
        tmp_path,
        "shine",
        aliases=("pizza-shine.mallorca.pizza",),
    )

    with make_client(tmp_path) as client:
        response = client.get(
            "/media/shine/branding/logo.png",
            headers={"Host": "pizza-shine.mallorca.pizza"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["location"] == (
        "https://shine.mallorca.pizza/media/shine/branding/logo.png"
    )


def test_restaurant_robots_and_sitemap_are_brand_specific(tmp_path: Path) -> None:
    write_restaurant(tmp_path, "shine")

    with make_client(tmp_path) as client:
        robots = client.get("/robots.txt", headers={"Host": "shine.mallorca.pizza"})
        sitemap = client.get("/sitemap.xml", headers={"Host": "shine.mallorca.pizza"})

    assert robots.status_code == 200
    assert robots.headers["Cache-Control"] == "public, max-age=300"
    assert "Sitemap: https://shine.mallorca.pizza/sitemap.xml" in robots.text
    assert sitemap.status_code == 200
    assert sitemap.headers["Cache-Control"] == "public, max-age=300"
    assert "<loc>https://shine.mallorca.pizza/</loc>" in sitemap.text


def test_apex_sitemap_lists_only_enabled_restaurants(tmp_path: Path) -> None:
    write_restaurant(tmp_path, "shine")
    write_restaurant(tmp_path, "belly", enabled=False)

    with make_client(tmp_path) as client:
        response = client.get("/sitemap.xml", headers={"Host": "mallorca.pizza"})

    assert response.status_code == 200
    assert "https://shine.mallorca.pizza/" in response.text
    assert "https://belly.mallorca.pizza/" not in response.text


def test_seo_endpoints_reject_unknown_hosts(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        robots = client.get("/robots.txt", headers={"Host": "unknown.mallorca.pizza"})
        sitemap = client.get("/sitemap.xml", headers={"Host": "unknown.mallorca.pizza"})

    assert robots.status_code == 404
    assert sitemap.status_code == 404
