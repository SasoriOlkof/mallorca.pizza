"""SEO response builders."""

from html import escape

from mallorca_pizza.config.catalog import RestaurantBundle, RestaurantCatalog


def restaurant_canonical_url(bundle: RestaurantBundle, path: str = "/") -> str:
    normalized_path = "/" if path == "" or path == "/" else path.rstrip("/")
    return f"https://{bundle.restaurant.canonical_host}{normalized_path}"


def build_restaurant_robots(bundle: RestaurantBundle) -> str:
    directives = ["User-agent: *"]
    if bundle.seo.robots.index and bundle.seo.robots.follow:
        directives.append("Disallow:")
    else:
        directives.append("Disallow: /")
    directives.append(
        f"Sitemap: https://{bundle.restaurant.canonical_host}/sitemap.xml"
    )
    return "\n".join(directives) + "\n"


def build_apex_robots() -> str:
    return "User-agent: *\nDisallow:\nSitemap: https://mallorca.pizza/sitemap.xml\n"


def build_restaurant_sitemap(bundle: RestaurantBundle) -> str:
    urls = [
        f"https://{bundle.restaurant.canonical_host}{path}"
        for path in bundle.seo.sitemap_paths
    ]
    return build_sitemap_xml(urls)


def build_apex_sitemap(catalog: RestaurantCatalog) -> str:
    urls = [
        f"https://{bundle.restaurant.canonical_host}/"
        for bundle in catalog.enabled_restaurants
    ]
    return build_sitemap_xml(urls)


def build_sitemap_xml(urls: list[str]) -> str:
    items = "\n".join(
        f"  <url><loc>{escape(url, quote=True)}</loc></url>" for url in urls
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{items}\n"
        "</urlset>\n"
    )
