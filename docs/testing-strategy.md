# Estrategia de pruebas

## Objetivo

La suite debe proteger las reglas centrales del sistema:

* resolucion segura por host;
* catalogo inmutable validado al arrancar;
* configuracion YAML segura;
* assets controlados;
* renderizado por marca;
* SEO por marca;
* despliegue Docker verificable.

## Herramientas

* pytest para pruebas unitarias e integracion.
* httpx o TestClient de FastAPI para peticiones ASGI.
* Ruff para formato y lint.
* mypy para tipos.
* GitHub Actions para verificacion.

## Unit tests

Cubrir:

* normalizacion de host;
* rechazo de hosts maliciosos;
* allowlist cerrada;
* hosts canonicos;
* aliases;
* `www.mallorca.pizza`;
* restaurantes deshabilitados;
* root redirect con restaurantes habilitados;
* root `503` sin restaurantes habilitados;
* seleccion aleatoria sin restaurantes deshabilitados;
* carga segura de YAML;
* rechazo de multiples documentos YAML;
* rechazo de tags YAML personalizados;
* limites de tamano;
* IDs duplicados;
* hosts duplicados;
* precios no enteros;
* booleanos sin coercion silenciosa;
* bloques como union discriminada;
* variantes de bloque invalidas;
* temas con tokens invalidos;
* assets faltantes;
* extension de assets invalida;
* alt/decorative obligatorio;
* rutas de assets que intentan escapar del directorio permitido.

## Integration tests

Cubrir peticiones completas:

* `GET /health/live`.
* `GET /health/ready`.
* `GET /` con host canonico de restaurante.
* `GET /` con dominio raiz.
* `GET /` con `www.mallorca.pizza`.
* `GET /` con alias de restaurante.
* `GET /` con host desconocido.
* `GET /` con restaurante deshabilitado.
* ruta desconocida en host valido.
* `/robots.txt` por restaurante.
* `/sitemap.xml` por restaurante.
* canonical por restaurante.
* metadata por restaurante.
* JSON-LD por restaurante.
* cabeceras de seguridad.
* `Cache-Control: no-store` en redirect aleatorio.

## Configuracion y assets

La validacion de configuracion debe poder ejecutarse como comando independiente
en fase 2 o 3.

Las pruebas deben incluir fixtures validos e invalidos.

Los fixtures invalidos deben cubrir:

* YAML demasiado grande;
* YAML con tags personalizados;
* YAML con multiples documentos;
* campos desconocidos;
* host duplicado;
* restaurante sin host canonico;
* assets inexistentes;
* SVG no permitido;
* imagen sin `alt` y sin `decorative: true`;
* bloque con `type` desconocido;
* configuracion con HTML o Markdown que no deba renderizarse.

## Seguridad

Probar:

* host con espacios;
* host con puerto;
* host con punto final;
* host con ruta embebida;
* host con varios valores;
* spoofing de forwarded headers;
* ausencia de `|safe` aplicado a textos YAML;
* no exposicion de stack traces en respuestas de produccion;
* cabeceras CSP, `X-Content-Type-Options`, `Referrer-Policy` y
  `Permissions-Policy`.

## CI/CD v1

GitHub Actions debe ejecutar:

* `uv run ruff format --check`;
* `uv run ruff check`;
* `uv run mypy`;
* `uv run pytest`;
* validacion de configuracion;
* comprobacion de assets;
* build Docker.

La validacion de configuracion y assets usa:

```bash
uv run mallorca-pizza-validate-config
```

El build Docker de CI usa una etiqueta efimera basada en el commit:

```bash
docker build -t mallorca-pizza:${GITHUB_SHA} .
```

En v1 no se publicaran imagenes en GHCR ni se configurara despliegue automatico.

## Criterios de aceptacion

Una fase funcional no se considera completa si:

* no tiene pruebas para el comportamiento nuevo;
* no valida configuracion y assets cuando corresponda;
* falla Ruff, mypy o pytest;
* no documenta comandos inexistentes como pendientes;
* cambia comportamiento no relacionado sin explicarlo.

## Decisiones pendientes

* Limites finales para fixtures de tamano.
* Si se anadiran pruebas end-to-end con navegador en una fase posterior.
