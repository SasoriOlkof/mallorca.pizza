# Mallorca Pizza

Multi-site platform for restaurant brands hosted under the `mallorca.pizza`
domain.

A single FastAPI service renders different restaurant websites depending on the
original HTTP `Host` received by the application.

Examples:

* `shine.mallorca.pizza`
* `belly.mallorca.pizza`
* `bollywood.mallorca.pizza`

Each restaurant has its own:

* Name and branding.
* Visual theme.
* Menu and prices.
* Contact information.
* Opening hours.
* Images and assets.
* SEO metadata.
* Canonical URLs.
* `robots.txt`.
* `sitemap.xml`.
* Structured data.

The platform does not use a database. All restaurant information is stored in
version-controlled YAML configuration files and packaged into the Docker image.

## Project status

The project is in the planning and initial implementation stage.

The technology decision has been made:

* Python 3.13.
* FastAPI.
* Jinja2 for server-rendered HTML.
* Pydantic for strict configuration models and validation.
* YAML restaurant configuration.
* Uvicorn as the ASGI server.
* `uv` for dependency management and lockfile.
* pytest for tests.
* Ruff for formatting and linting.
* mypy for type checking.
* Docker for production.
* Traefik as an external reverse proxy.

Traefik is not part of this repository. It receives requests for
`mallorca.pizza` and `*.mallorca.pizza`, preserves the original host, and
forwards traffic to the application container.

See the documentation in [`docs/`](./docs/) for the current requirements and
decisions.

## How it works

All supported domains and subdomains point to the same service.

During application startup, the service:

1. Loads all restaurant YAML configuration files.
2. Rejects unsafe YAML, multiple YAML documents, invalid values and unknown
   fields.
3. Validates the data with Pydantic models.
4. Checks configured assets.
5. Builds an immutable in-memory catalog of enabled and disabled restaurants,
   canonical hosts, aliases and media paths.

For every request, the service:

1. Reads the original HTTP `Host`.
2. Normalizes and validates it.
3. Resolves the corresponding restaurant from the closed allowlist built at
   startup.
4. Renders restaurant-specific HTML and resources from the already-loaded
   catalog.
5. Returns controlled errors for unknown hosts, disabled restaurants and unknown
   routes.

Example:

```text
GET /
Host: shine.mallorca.pizza
```

The service resolves the `shine` restaurant and returns its content, design and
SEO metadata.

The host value must never be used directly to construct filesystem paths.

## Runtime behavior

### Health checks

The service exposes two health endpoints:

* `/health/live`: returns `200` when the process is alive.
* `/health/ready`: returns `200` only after the restaurant catalog has been
  loaded and validated. It may return `503` during initialization. Invalid
  production configuration terminates startup instead of leaving the service in
  a permanently unready state.

Docker health checks use `/health/ready`.

### Root domain

Requests to:

```text
https://mallorca.pizza/
```

are redirected temporarily to a randomly selected enabled restaurant using
status `302` and `Cache-Control: no-store`.

Disabled restaurants are excluded from redirect destinations. If no restaurant
is enabled, the root domain returns `503`.

`www.mallorca.pizza` is a non-canonical alias for the apex domain and redirects
temporarily to `mallorca.pizza`.

### Restaurant hosts

Requests to a restaurant canonical host render that restaurant.

Restaurant aliases are allowed only when explicitly configured and validated.
Aliases redirect temporarily to the configured canonical host.

Unknown hosts and disabled restaurants return a controlled `404`.

### SEO endpoints

The following endpoints are restaurant-specific:

* `/robots.txt`
* `/sitemap.xml`
* canonical URLs
* HTML metadata
* structured data

Structured data is built as Python objects and serialized as JSON. YAML content
is plain text only; it is not rendered as HTML or Markdown.

## Scope

The initial functional version includes:

* Server-rendered restaurant websites.
* Host-based restaurant resolution.
* Configuration loading and validation at startup.
* Immutable in-memory restaurant catalog.
* Restaurant information.
* Opening hours.
* Contact details.
* Menus with categories, products and prices.
* Responsive restaurant websites.
* Shared `mallorca.pizza` visual system.
* Brand variations through themes, assets, registered blocks and allowed
  variants.
* Restaurant-specific SEO.
* Restaurant-specific `robots.txt`.
* Restaurant-specific `sitemap.xml`.
* Restaurant-specific structured data.
* Health checks.
* Security headers.
* Structured logs with request IDs.
* Automated tests.
* Docker production build.
* GitHub Actions verification.

## Out of scope

The initial version does not include:

* Online orders.
* Payments.
* Reservations.
* User accounts.
* Authentication.
* Customer reviews.
* An administration panel.
* A database.
* A native mobile application.
* Public contribution workflow.
* Publishing images to GHCR.
* Automatic deployment to the production server.

## Repository structure

The planned repository structure is:

```text
.
├── AGENTS.md
├── README.md
├── docs/
├── src/
│   └── mallorca_pizza/
├── restaurants/
│   ├── shine/
│   ├── belly/
│   └── bollywood/
├── static/
├── tests/
└── .github/
    └── workflows/
```

The final structure may evolve during implementation, but restaurant-specific
content must remain separate from shared application logic.

### `src/`

FastAPI application code, domain resolution, configuration loading, validation,
rendering, templates and reusable logic.

### `restaurants/`

Restaurant-specific YAML configuration and media assets.

A restaurant should normally be added by creating or updating a folder here,
without modifying shared application logic.

### `static/`

Shared static assets for the common `mallorca.pizza` visual system.

### `tests/`

Unit and integration tests.

### `docs/`

Product requirements, architecture decisions, configuration model, security
requirements, testing strategy, deployment guidance and implementation plan.

## Restaurant configuration

Each restaurant is expected to have a structure similar to:

```text
restaurants/shine/
├── restaurant.yaml
├── menu.yaml
├── theme.yaml
├── seo.yaml
└── assets/
    ├── branding/
    └── menu/
```

All configuration files are loaded at startup and validated before the
application becomes ready.

See [`docs/configuration-model.md`](./docs/configuration-model.md).

## Assets

Shared assets are served under:

```text
/static/
```

Restaurant assets are served under controlled media routes:

```text
/media/<restaurant-id>/
```

A restaurant can access only its own media assets and shared static assets.
Physical filesystem paths come from the validated startup catalog, never from
request values.

Version 1 supports JPEG, PNG and WebP images. AVIF is pending until validation
inside Docker is proven reliable without adding unnecessary complexity. Third
party SVG assets are disabled in v1 unless a future sanitization process is
added.

## Local development

Local development uses `uv`:

```bash
uv sync
uv run mallorca-pizza-serve
```

The current application resolves hosts, loads the startup catalog, exposes
health checks, renders restaurant pages with Jinja2, serves controlled media,
emits restaurant SEO, adds security/cache headers, and provides Docker and CI
verification.

Runtime variables:

* `BIND_HOST`: listen address, default `0.0.0.0`.
* `PORT`: listen port, default `8000`.
* `FORWARDED_ALLOW_IPS`: trusted Traefik IP or network.
* `ENVIRONMENT`: `development` or `production`.
* `RESTAURANTS_ROOT`: restaurant configuration root.
* `STATIC_ROOT`: shared static asset root.

In production, `FORWARDED_ALLOW_IPS="*"` is rejected.

Development may support a local-only restaurant selector such as:

```text
http://localhost:8000/?restaurant=shine
```

This override must never be enabled in production.

## Validation and quality checks

The current phase provides:

```bash
uv run ruff format --check
uv run ruff check
uv run mypy
uv run pytest
uv run python -m mallorca_pizza.validate_config
uv run mallorca-pizza-validate-config
```

Docker build verification:

```bash
docker build -t mallorca-pizza:local .
```

## Deployment

The intended production setup is:

```text
mallorca.pizza
*.mallorca.pizza
        │
        ▼
Traefik reverse proxy
        │
        ▼
Single Docker container
```

The application container listens on `BIND_HOST` and `PORT`. The application
port must not be exposed directly to the internet.

Traefik must preserve the original host and provide trusted forwarded headers.
HSTS is managed by Traefik, not by the application.

Build the image locally:

```bash
docker build -t mallorca-pizza:local .
```

Run with compose behind an existing Traefik network:

```bash
FORWARDED_ALLOW_IPS=172.18.0.0/16 TRAEFIK_NETWORK=traefik docker compose up -d
```

The compose file uses `expose`, not `ports`, so the app is reachable only from
the Docker network unless the deployment deliberately changes that.

See [`docs/deployment.md`](./docs/deployment.md).

## Documentation

Current documentation:

```text
docs/
├── project-brief.md
├── architecture.md
├── configuration-model.md
├── security.md
├── testing-strategy.md
├── deployment.md
└── implementation-plan.md
```

## Pending decisions

* Final review of `shine` details and real content/assets for `belly` and
  `bollywood`.
* Whether AVIF enters v1.
* Whether the initial YAML, text, menu and image limits need adjustment once
  real content is available.
* Production Traefik network or IP range for `FORWARDED_ALLOW_IPS`.
* Server update mechanism before image publishing or deployment automation.
* Project license before making the repository public.

## License

`PENDING`: Define the project license before making the repository public.
