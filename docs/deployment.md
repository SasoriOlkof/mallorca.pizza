# Deployment

## Objetivo

La aplicacion se desplegara como un contenedor Docker unico detras de Traefik.

Traefik queda fuera de este repositorio.

## Topologia

```text
mallorca.pizza
*.mallorca.pizza
        |
        v
Traefik externo
        |
        v
Contenedor mallorca-pizza
```

El puerto de la aplicacion no debe exponerse directamente a internet.

## Runtime

La aplicacion usara Uvicorn como servidor ASGI.

Variables:

* `BIND_HOST`: direccion de escucha, por defecto `0.0.0.0`.
* `PORT`: puerto de escucha, por defecto `8000`.
* `FORWARDED_ALLOW_IPS`: red o IP confiable de Traefik.
* `ENVIRONMENT`: entorno de ejecucion.

En produccion, `FORWARDED_ALLOW_IPS="*"` no esta permitido.

El comando de entrada de la aplicacion es:

```bash
mallorca-pizza-serve
```

## Docker

La fase 7 incluye:

* `Dockerfile` multi-stage;
* `.dockerignore`;
* `docker-compose.yml` sencillo;
* usuario no root;
* healthcheck del contenedor usando `/health/ready`;
* inclusion de configuracion y assets en la imagen.

La politica de reinicio recomendada en compose sera `restart: unless-stopped`.

Build local:

```bash
docker build -t mallorca-pizza:local .
```

Ejecucion con compose detras de una red Traefik ya existente:

```bash
FORWARDED_ALLOW_IPS=172.18.0.0/16 TRAEFIK_NETWORK=traefik docker compose up -d
```

`docker-compose.yml` usa `expose: 8000`, no `ports`, para evitar publicar el
puerto de la app directamente. La red `traefik` es externa y su nombre puede
cambiarse con `TRAEFIK_NETWORK`.

## Health checks

`/health/live` indica que el proceso responde.

`/health/ready` indica que el catalogo esta cargado y validado.

Docker usara `/health/ready`.

Una configuracion invalida en produccion debe terminar el proceso durante startup.
`/health/ready` devuelve `503` solo durante una inicializacion no completada.

## Traefik

Traefik debe:

* aceptar `mallorca.pizza`;
* aceptar `*.mallorca.pizza`;
* conservar el `Host` original;
* enviar `X-Forwarded-Proto`;
* gestionar TLS;
* gestionar HSTS;
* enrutar al puerto interno del contenedor;
* evitar exponer el contenedor directamente a internet.

La logica de aplicacion debe permanecer independiente de Traefik.

## Cabeceras esperadas

La aplicacion resuelve el restaurante con `Host`.

`X-Forwarded-Proto` puede usarse para construir URLs absolutas cuando venga de
una red confiable configurada.

No se debe confiar en `X-Forwarded-Host` para resolver restaurantes en v1.

## Cache

V1 usa una estrategia simple:

* assets con cache moderada: `public, max-age=86400`;
* HTML con cache conservadora: `private, max-age=60`;
* endpoints SEO con cache conservadora: `public, max-age=300`;
* redirect aleatorio del apex con `Cache-Control: no-store`;
* sin fingerprinting complejo de nombres de archivo todavia.

## CI/CD v1

GitHub Actions validara:

* calidad;
* tipos;
* tests;
* configuracion;
* assets;
* build Docker.

No se publicaran imagenes en GHCR en v1.

No se configurara despliegue automatico hasta definir el mecanismo de
actualizacion del servidor.

El workflow de verificacion esta en `.github/workflows/verify.yml` y ejecuta:

```bash
uv sync --locked --dev
uv run ruff format --check
uv run ruff check
uv run mypy
uv run pytest
uv run mallorca-pizza-validate-config
docker build -t mallorca-pizza:${GITHUB_SHA} .
```

## Rollback manual

Hasta definir despliegue automatico, rollback significa volver a ejecutar una
imagen anterior conocida y comprobar:

* que el contenedor arranca;
* que `/health/ready` devuelve `200`;
* que hosts conocidos renderizan;
* que hosts desconocidos devuelven `404`;
* que el apex redirige o devuelve `503` si no hay restaurantes habilitados.

## Decisiones pendientes

* Mecanismo de actualizacion del servidor.
* Estrategia de publicacion y etiquetado de imagenes.
* Red o IP concreta de Traefik para `FORWARDED_ALLOW_IPS`.
* Ajustes finales de cache cuando haya contenido real y estrategia de despliegue.
