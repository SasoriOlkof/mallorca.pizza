# Plan de implementacion

## Resumen

La implementacion se divide en fases pequenas para evitar mezclar decisiones de
arquitectura, tooling, dominio, renderizado, Docker y CI.

La fase 1 solo formaliza documentacion y decisiones. No crea codigo de
produccion, `pyproject.toml`, Dockerfile, tests ni estructura de aplicacion.

## Fase 1 - Documentacion y decisiones

Alcance:

* actualizar `README.md`;
* actualizar `AGENTS.md`;
* actualizar `docs/project-brief.md`;
* crear `docs/architecture.md`;
* crear `docs/configuration-model.md`;
* crear `docs/security.md`;
* crear `docs/testing-strategy.md`;
* crear `docs/deployment.md`;
* crear `docs/implementation-plan.md`;
* documentar decisiones pendientes.

Exclusiones:

* no crear codigo de aplicacion;
* no crear `pyproject.toml`;
* no crear Dockerfile;
* no crear tests;
* no crear estructura `src/`.

## Fase 2 - Base Python y herramientas

Alcance propuesto:

* crear `pyproject.toml`;
* generar `uv.lock`;
* configurar Python 3.13;
* anadir FastAPI, Uvicorn, Jinja2, Pydantic, PyYAML o alternativa segura,
  pytest, Ruff y mypy;
* crear estructura base `src/mallorca_pizza/`;
* crear estructura base `tests/`;
* configurar Ruff;
* configurar mypy;
* anadir comandos documentados para calidad y tests;
* anadir una aplicacion minima sin logica de restaurantes.

Exclusiones:

* no implementar todavia catalogo completo;
* no crear restaurantes iniciales definitivos;
* no crear Dockerfile todavia.

## Fase 3 - Modelos, catalogo y validacion

Alcance:

* lectura segura de YAML;
* rechazo de multiples documentos y tags personalizados;
* modelos Pydantic con `extra="forbid"`;
* validadores estrictos para campos criticos;
* modelos de bloques visuales;
* union discriminada por `type`;
* validacion de temas;
* validacion de menus y precios;
* validacion de assets;
* construccion de catalogo inmutable;
* fallo de startup ante configuracion invalida en produccion;
* comando de validacion de configuracion.

## Fase 4 - Resolucion HTTP, hosts, redirects y health checks

Alcance:

* `/health/live`;
* `/health/ready`;
* normalizacion de host;
* allowlist;
* apex redirect `302`;
* `Cache-Control: no-store` en redirect aleatorio;
* `503` si no hay restaurantes habilitados;
* `www.mallorca.pizza`;
* aliases canonicos;
* 404 de hosts desconocidos;
* 404 de restaurantes deshabilitados;
* 404 de rutas desconocidas.

## Fase 5 - Renderizado Jinja2 y bloques

Alcance:

* plantillas Jinja2 internas;
* autoescape;
* layout comun;
* renderizado de bloques registrados;
* rechazo de HTML/Markdown renderizado desde YAML;
* no usar `|safe` con YAML;
* pruebas de HTML por marca.

## Fase 6 - Temas, assets, SEO y cabeceras de seguridad

Alcance:

* tokens de tema;
* variables CSS validadas;
* assets compartidos `/static/`;
* media de restaurante `/media/<restaurant-id>/`;
* cache moderada para assets;
* cache conservadora para HTML y SEO;
* `robots.txt`;
* `sitemap.xml`;
* canonical;
* metadata;
* JSON-LD construido en Python;
* CSP;
* `X-Content-Type-Options`;
* `Referrer-Policy`;
* `Permissions-Policy`;
* logs estructurados y request ID.

## Fase 7 - Docker y CI de verificacion

Alcance:

* Dockerfile multi-stage;
* `.dockerignore`;
* `docker-compose.yml`;
* usuario no root;
* `BIND_HOST`;
* `PORT`;
* `FORWARDED_ALLOW_IPS`;
* healthcheck Docker con `/health/ready`;
* GitHub Actions para Ruff, mypy, pytest, validacion de configuracion, assets y
  build Docker.

Artefactos:

* `Dockerfile`;
* `.dockerignore`;
* `docker-compose.yml`;
* `.github/workflows/verify.yml`;
* comando `mallorca-pizza-serve`.

Exclusiones:

* no publicar imagenes en GHCR;
* no automatizar despliegue.

## Fase 8 - Restaurantes iniciales y prueba completa

Alcance:

* crear configuraciones iniciales para `shine`, `belly` y `bollywood`;
* anadir assets revisables;
* validar hosts canonicos;
* validar SEO;
* comprobar renderizado completo;
* ejecutar suite completa y build Docker.

## Fase 9 - Preparacion del repositorio publico

Alcance:

* `CONTRIBUTING.md`;
* plantilla de Pull Request;
* reglas para contribuciones de contenido;
* validacion de extensiones, tamanos y rutas modificadas;
* restricciones para cambios externos en `restaurants/<id>/`.

Esta fase no debe retrasar la primera version funcional.

## Fase 10 - Publicacion de imagen y despliegue automatizado

Alcance pendiente:

* definir mecanismo de actualizacion del servidor;
* definir etiquetado de imagenes;
* definir si se publica en GHCR u otro registry;
* automatizar despliegue cuando el mecanismo este aprobado.

## Decisiones pendientes globales

* Revision final de datos de `shine` y contenido/assets reales de `belly` y
  `bollywood`.
* Inclusion de AVIF.
* Ajustes finales de limites para YAML, textos, menus, imagenes y assets.
* Red o IP de Traefik para `FORWARDED_ALLOW_IPS`.
* Mecanismo de actualizacion del servidor.
* Licencia del proyecto.
