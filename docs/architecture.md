# Arquitectura

## Resumen

`mallorca.pizza` sera una aplicacion Python renderizada en servidor.

El servicio sera unico para `mallorca.pizza` y `*.mallorca.pizza`. FastAPI
recibira las peticiones, resolvera el restaurante a partir del `Host` original y
renderizara HTML con Jinja2.

La aplicacion no usara base de datos. Todo el contenido se cargara desde YAML y
assets versionados en el repositorio e incluidos en la imagen Docker.

## Stack

* Python 3.13.
* FastAPI.
* Jinja2.
* Pydantic.
* YAML.
* Uvicorn.
* `uv`.
* pytest.
* Ruff.
* mypy.
* Docker.
* Traefik externo.

## Capas

La implementacion se dividira en estas responsabilidades:

* Runtime ASGI: arranque, lifespan de FastAPI, health checks y wiring.
* Configuracion: lectura segura de YAML, validacion Pydantic y comprobacion de
  assets.
* Catalogo: estructura inmutable en memoria con restaurantes, hosts canonicos,
  aliases, media validada y restaurantes habilitados.
* Resolucion de host: normalizacion, allowlist, deteccion de apex, `www`, aliases
  y hosts desconocidos.
* Renderizado: plantillas Jinja2 internas, bloques visuales registrados y datos
  de vista derivados del catalogo.
* SEO: canonical, metadata, `robots.txt`, `sitemap.xml` y JSON-LD por marca.
* Seguridad: cabeceras, autoescape, control de forwarded headers y errores
  controlados.
* Observabilidad: logs estructurados, request ID, status y duracion.

## Startup y catalogo

Durante el arranque, la app cargara todos los YAML de restaurantes y validara:

* estructura esperada;
* hosts unicos;
* IDs unicos;
* hosts canonicos y aliases;
* estado `enabled`;
* menu y precios;
* temas;
* bloques visuales;
* SEO;
* assets requeridos;
* limites de tamano pendientes de concretar.

Si la configuracion es invalida en produccion, el proceso debe terminar durante
startup.

Una vez validada, la configuracion se convertira en un catalogo inmutable en
memoria. Las peticiones no releeran YAML ni escanearan directorios.

El entrypoint `mallorca-pizza-serve` arranca Uvicorn con:

* `BIND_HOST`;
* `PORT`;
* `FORWARDED_ALLOW_IPS`;
* `proxy_headers=True`.

La app valida la configuracion de runtime antes de crear el servidor. En
produccion, `FORWARDED_ALLOW_IPS="*"` termina el arranque.

## Resolucion de host

La resolucion se hara exclusivamente con el `Host` original recibido por la app.

El host se normalizara de forma centralizada:

* minusculas;
* sin puerto;
* sin punto final;
* formato de dominio valido;
* sin rutas embebidas;
* sin espacios;
* sin listas de hosts;
* sin caracteres sospechosos.

El host normalizado se compara contra la allowlist del catalogo.

El host nunca se usa para construir rutas fisicas ni rutas de plantillas.

## Comportamiento HTTP

`GET /` en un host canonico de restaurante renderiza ese restaurante.

`GET /` en `mallorca.pizza` redirige con `302` a un restaurante habilitado
aleatorio y anade `Cache-Control: no-store`.

Si no hay restaurantes habilitados, `mallorca.pizza/` devuelve `503`.

`www.mallorca.pizza` es alias no canonico del apex y redirige temporalmente a
`mallorca.pizza`.

Aliases de restaurante solo existen si estan configurados y validados. Redirigen
temporalmente al host canonico del restaurante.

Hosts desconocidos y restaurantes deshabilitados devuelven `404` controlado.

Rutas desconocidas en hosts validos devuelven `404` controlado.

Las URLs canonicas se emitiran sin barra final salvo `/`.

## Health checks

`/health/live` devuelve `200` si el proceso responde.

`/health/ready` devuelve `200` cuando el catalogo esta cargado y validado. Puede
devolver `503` durante una inicializacion incompleta. No debe ocultar errores de
configuracion permanentes: en produccion, esos errores terminan el proceso.

Docker usara `/health/ready`.

## Renderizado

Las plantillas Jinja2 seran internas y registradas por la aplicacion.

La configuracion no podra seleccionar rutas de plantillas ni incluir HTML,
JavaScript, Markdown renderizado o expresiones CSS arbitrarias.

Los textos de YAML son texto plano en v1. Jinja2 debe mantener autoescape activo
y no debe usar `|safe` con valores procedentes de YAML.

El JSON-LD se construira como objetos Python y se serializara como JSON.

## Sistema visual

La plataforma tendra un sistema visual comun de `mallorca.pizza`.

Cada marca podra variar mediante:

* tema validado;
* assets propios;
* bloques visuales registrados;
* variantes permitidas por bloque.

Cada bloque tendra su propio modelo Pydantic y se seleccionara mediante una
union discriminada por `type`.

## Assets

Assets compartidos: `/static/`.

Assets de restaurante: `/media/<restaurant-id>/`.

Una marca solo podra acceder a sus propios assets y a assets compartidos.

Las rutas fisicas de assets saldran del catalogo validado, nunca de valores de
peticion.

La v1 soporta JPEG, PNG y WebP. AVIF queda pendiente. SVG de terceros queda
deshabilitado salvo futura sanitizacion.

## Proxy inverso

Traefik es externo al repositorio.

La aplicacion espera que Traefik:

* conserve el `Host` original;
* envie `X-Forwarded-Proto`;
* enrute `mallorca.pizza` y `*.mallorca.pizza` al contenedor;
* no exponga el puerto de la app directamente a internet;
* gestione HSTS.

La aplicacion configurara `FORWARDED_ALLOW_IPS` con la red confiable de Traefik.
En produccion no se permitira `*`.

## Decisiones pendientes

* Ajustes finales de limites numericos para YAML, textos, menus y assets.
* Inclusion de AVIF.
* Red o IP exacta de Traefik.
* Contenido real de restaurantes iniciales.
