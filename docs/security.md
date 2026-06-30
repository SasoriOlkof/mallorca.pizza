# Seguridad

## Principios

La aplicacion trata cabeceras, URLs, YAML y assets como datos no confiables hasta
validarlos.

No se permite construir rutas fisicas, rutas de plantillas ni destinos de
redirect a partir de valores recibidos en peticiones.

## Hosts

La resolucion de restaurante usa el `Host` original recibido por la aplicacion.

El host se normaliza y valida antes de consultarse en la allowlist del catalogo.

Se rechazaran:

* hosts desconocidos;
* multiples hosts;
* hosts con espacios;
* hosts con rutas embebidas;
* hosts con caracteres invalidos;
* hosts que no existan en la configuracion validada;
* restaurantes deshabilitados.

Los hosts desconocidos y restaurantes deshabilitados devuelven 404 controlado.

## Redirects

Los destinos de redirect salen solo del catalogo validado.

El dominio raiz redirige con `302` a un restaurante habilitado aleatorio y usa
`Cache-Control: no-store`.

Si no hay restaurantes habilitados, el dominio raiz devuelve `503`.

`www.mallorca.pizza` redirige temporalmente al apex.

Los aliases de restaurantes redirigen temporalmente al host canonico configurado.

## Proxy y forwarded headers

Traefik es externo al repositorio.

La aplicacion debe ejecutarse detras de Traefik y el puerto de la app no debe
exponerse directamente a internet.

Traefik debe conservar el `Host` original.

`X-Forwarded-Proto` se usara para construir URLs absolutas solo cuando venga de
una red confiable.

`FORWARDED_ALLOW_IPS` debe configurarse con la red o IP confiable de Traefik.

En produccion no se permite `FORWARDED_ALLOW_IPS="*"`.

HSTS se gestiona en Traefik.

## YAML

Los YAML deben cargarse con un loader seguro.

Se rechazaran:

* tags personalizados;
* multiples documentos;
* archivos demasiado grandes;
* claves desconocidas;
* valores fuera de rango;
* rutas relativas que escapen del directorio permitido.

Los modelos Pydantic usaran `extra="forbid"` y validadores especificos en campos
criticos.

## Jinja2 y contenido

Jinja2 debe mantener autoescape activo.

Los textos de YAML son texto plano. No se renderizara HTML ni Markdown desde
configuracion.

No se usara `|safe` con valores procedentes de YAML.

El JSON-LD se construira como objetos Python y se serializara como JSON.

## Assets

Assets compartidos se sirven bajo `/static/`.

Assets de restaurante se sirven bajo `/media/<restaurant-id>/`.

Una marca solo puede acceder a sus propios assets y a assets compartidos.

Las rutas fisicas de assets salen del catalogo validado.

SVG de terceros esta deshabilitado en v1 salvo sanitizacion futura.

## Cabeceras de seguridad

La aplicacion anadira:

* `Content-Security-Policy`;
* `X-Content-Type-Options`;
* `Referrer-Policy`;
* `Permissions-Policy`.

La politica CSP inicial permite recursos propios, imagenes propias/data URIs,
JSON-LD inline y variables CSS inline derivadas de tokens validados. No permite
contenido inline arbitrario desde YAML.

HSTS queda fuera de la app y sera responsabilidad de Traefik.

## Observabilidad segura

Los logs seran estructurados e incluiran:

* request ID;
* host;
* ruta;
* status;
* duracion.

No se registraran:

* secretos;
* payloads completos de configuracion;
* rutas internas innecesarias;
* datos personales no necesarios.

## Errores

En produccion no se deben exponer stack traces ni rutas internas.

Los errores de host, restaurante deshabilitado, ruta desconocida y configuracion
invalida deben tener respuestas controladas.

La configuracion invalida en produccion termina el proceso durante startup.

## Decisiones pendientes

* Refinamiento final de CSP, por ejemplo nonces/hashes cuando el despliegue este
  estabilizado.
* Red o IP de Traefik para `FORWARDED_ALLOW_IPS`.
* Ajustes finales de limites de archivos y assets.
