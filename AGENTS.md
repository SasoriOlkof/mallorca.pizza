# AGENTS.md

## Project overview

This repository contains the `mallorca.pizza` multi-site platform.

A single FastAPI service hosts multiple restaurant websites. Each restaurant is
identified by a configured host, for example:

* `shine.mallorca.pizza`
* `belly.mallorca.pizza`
* `bollywood.mallorca.pizza`

The service must resolve the requested host on the server before rendering the
response.

The root domain, `mallorca.pizza`, redirects temporarily to a randomly selected
enabled restaurant.

The project does not use a database. Restaurant content, menus, themes, SEO
settings and media metadata are stored in version-controlled YAML configuration
files.

Read the relevant files in `docs/` before making architectural or product
decisions.

## Core constraints

* Use a single repository and a single deployed service.
* Use Python 3.13, FastAPI, Jinja2, Pydantic, YAML, Uvicorn, `uv`, pytest,
  Ruff, mypy and Docker.
* Do not introduce a database.
* Do not introduce authentication, users, orders, payments or reservations.
* Resolve the restaurant from a closed and validated host configuration.
* Never construct filesystem paths directly from an untrusted `Host` header.
* Unknown hosts must return a controlled `404` response.
* Disabled restaurants must not be rendered or selected for redirection.
* The root-domain redirect must use a temporary HTTP redirect and
  `Cache-Control: no-store`.
* If no restaurants are enabled, the root domain must return `503`.
* HTML, metadata, canonical URLs, structured data, `robots.txt` and
  `sitemap.xml` must match the requested restaurant.
* Restaurant-specific content must remain separate from shared application
  logic.
* Adding a restaurant should normally require configuration and assets, not
  changes to core application code.

## Architecture rules

* Keep domain resolution, configuration loading, validation and rendering as
  separate concerns.
* Centralize host normalization and restaurant resolution.
* Load and validate all restaurant configuration during application startup.
* Build an immutable in-memory catalog at startup.
* Do not reread restaurant configuration on each request.
* In production, invalid configuration or invalid required assets must terminate
  startup.
* Prefer explicit code over unnecessary abstractions.
* Avoid duplicated components between restaurant identities.
* Use configuration for supported visual variations.
* Do not allow configuration files to contain executable code.
* Do not allow configuration files to select arbitrary templates, filesystem
  paths, HTML, JavaScript or CSS expressions.
* Keep framework-specific code outside reusable configuration and validation
  logic where practical.

## Configuration rules

* Every restaurant must have a unique stable identifier.
* Every production host must be unique.
* Use Pydantic validation for all configuration files.
* Use `extra="forbid"` on all Pydantic models.
* Do not use global `strict=True` on every model.
* Use strict types, enums, regular expressions and validators on critical
  fields.
* Avoid silent coercion for prices, booleans, IDs, hosts, lists and numeric
  limits.
* Monetary values must not use floating-point arithmetic for calculations.
* Paths to assets must be validated against the restaurant catalog.
* Required assets must be checked automatically.
* YAML must be loaded safely, must contain exactly one document and must reject
  custom tags.
* Text from YAML is plain text only in v1. Do not render YAML text as HTML or
  Markdown.
* Do not use Jinja2 `|safe` with values from YAML.
* Configuration examples must not contain real secrets.
* Configuration changes must remain easy to review in Git.

## Visual and asset rules

* Use one shared `mallorca.pizza` visual system.
* Support brand variation through validated themes, assets, registered blocks
  and allowed variants.
* Every visual block must have its own Pydantic model.
* Use a discriminated union by `type` for block configuration.
* Do not use `dict[str, Any]` for visual block configuration.
* Theme values must be tokens or enums for spacing, borders, shadows and
  density.
* Do not allow arbitrary CSS expressions in configuration.
* Expose only validated CSS variables.
* Shared assets are served under `/static/`.
* Restaurant assets are served under `/media/<restaurant-id>/`.
* A restaurant may access only its own assets and shared assets.
* Physical asset paths must come from the validated catalog, never from request
  values.
* Version 1 supports JPEG, PNG and WebP images.
* AVIF is pending until validation in Docker is proven reliable.
* Third-party SVG assets are disabled in v1 unless a sanitization process is
  added.
* Every non-decorative image must have non-empty `alt` text. Decorative images
  must declare `decorative: true`.

## Development workflow

Before implementing a task:

1. Read this file.
2. Read the relevant documentation in `docs/`.
3. Inspect the existing implementation and tests.
4. Identify ambiguities or conflicts with the documented requirements.
5. Present a short implementation plan for substantial changes.

During implementation:

* Stay within the requested scope.
* Do not implement future phases unless required by the current task.
* Do not silently change documented requirements.
* Do not add production dependencies without explaining why they are needed.
* Do not weaken or remove tests merely to make them pass.
* Do not duplicate code to create a new restaurant identity.
* Keep changes small, focused and reviewable.
* Update documentation when behavior or architecture changes.

## Code quality

* Use typed Python.
* Keep mypy checks meaningful; do not silence type errors without justification.
* Avoid `Any` unless its use is explicitly justified and narrowly scoped.
* Prefer small functions with clear responsibilities.
* Use descriptive names.
* Handle errors explicitly.
* Do not expose stack traces or internal paths in production responses.
* Keep business rules independent from HTTP and framework details where
  practical.
* Follow Ruff formatting and linting rules configured in the repository.

## Security

* Treat request headers, URLs and configuration input as untrusted.
* Validate and normalize hosts before resolving a restaurant.
* Use an allowlist of configured hosts.
* Never read arbitrary files based on request values.
* Never commit credentials, tokens or private keys.
* Do not log secrets, full configuration payloads or unnecessary personal
  information.
* Use safe defaults when configuration is missing or invalid.
* Prevent open redirects: redirect destinations must come only from validated
  restaurant configuration.
* Add security headers, including CSP, `X-Content-Type-Options`,
  `Referrer-Policy` and `Permissions-Policy`.
* HSTS is managed by Traefik.
* Do not expose the application port directly to the internet.
* Configure `FORWARDED_ALLOW_IPS` with the trusted Traefik network in
  production. Do not use `*` in production.

## Observability

* Use structured logs.
* Add or propagate a request ID.
* Log host, path, status code and request duration.
* Do not log sensitive data or unnecessary restaurant configuration content.

## Testing expectations

Add or update tests for every behavior change.

At minimum, cover:

* known restaurant host resolution;
* host normalization;
* unknown host rejection;
* disabled restaurant rejection;
* root-domain random redirect;
* `503` when the root domain has no enabled restaurants;
* exclusion of disabled restaurants from redirects;
* configuration schema validation;
* YAML size limits, custom tag rejection and multiple document rejection;
* restaurant-specific metadata;
* restaurant-specific `robots.txt`;
* restaurant-specific `sitemap.xml`;
* invalid or malicious host values;
* missing configuration or assets;
* asset extension, size, dimension and alt/decorative validation;
* visual block discriminated unions and invalid variants;
* security headers;
* `/health/live`;
* `/health/ready`.

Prefer unit tests for pure logic and integration tests for request-to-response
behavior.

## Required checks

Before considering a task complete, run the available project commands for:

* formatting with Ruff;
* linting with Ruff;
* mypy type checking;
* unit and integration tests with pytest;
* configuration validation;
* asset validation;
* Docker build, once Docker exists.

If one of these commands does not exist yet, state that clearly instead of
pretending it was run.

## Definition of done

A task is complete only when:

* the requested behavior is implemented;
* acceptance criteria are satisfied;
* relevant tests are included and passing;
* formatting, linting, type checking, validation and build checks pass when they
  exist;
* no unrelated behavior has been changed;
* affected documentation is updated;
* assumptions and remaining limitations are reported.

## Final response format

When finishing a task, report:

1. What was implemented.
2. Which files were changed.
3. Which commands and tests were run.
4. Their results.
5. Any assumptions made.
6. Any remaining risks or pending work.
