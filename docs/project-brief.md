# Mallorca Pizza - Descripcion inicial

## Objetivo

Crear una plataforma multisitio para publicar distintas identidades visuales de
un mismo restaurante.

Cada identidad tendra:

* Un subdominio propio bajo `mallorca.pizza`.
* Nombre e identidad visual propios.
* Informacion del restaurante.
* Horarios.
* Datos de contacto.
* Menu completo con categorias, productos, descripciones y precios.
* Metadatos SEO propios.
* `robots.txt`, `sitemap.xml`, favicon y datos estructurados propios.

## Stack decidido

La primera version funcional usara:

* Python 3.13.
* FastAPI.
* Jinja2 para HTML renderizado en servidor.
* Pydantic para modelos y validacion.
* YAML para configuracion de restaurantes.
* Uvicorn como servidor ASGI.
* `uv` para dependencias y lockfile.
* pytest para pruebas.
* Ruff para formato y lint.
* mypy para comprobacion de tipos.
* Docker para produccion.
* Traefik como proxy inverso externo.

No se utilizara Astro, Node como runtime de aplicacion, Vercel ni otro proveedor
gestionado como parte de la arquitectura base.

## Ejemplos de dominios

* `shine.mallorca.pizza`
* `belly.mallorca.pizza`
* `bollywood.mallorca.pizza`

## Funcionamiento por dominio

Todas las peticiones llegaran al mismo servicio.

El servicio leera y validara el host original de la peticion antes de generar la
respuesta.

Segun el subdominio solicitado, cargara desde un catalogo inmutable:

* HTML renderizado para esa identidad.
* Contenido y menu propios.
* Estilos e imagenes propios.
* Metadatos SEO correctos.
* URL canonica correcta.
* `robots.txt` especifico.
* `sitemap.xml` especifico.
* Favicon y recursos especificos.

Los subdominios desconocidos deberan devolver una respuesta 404 controlada.

## Dominio raiz

Cuando se solicite `mallorca.pizza`, el servicio elegira aleatoriamente una de
las identidades habilitadas y respondera con una redireccion HTTP temporal hacia
su subdominio canonico.

La redireccion usara `302` y `Cache-Control: no-store`.

Los restaurantes deshabilitados no podran ser seleccionados.

Si no hay restaurantes habilitados, el dominio raiz devolvera `503`.

## Persistencia

No se utilizara una base de datos.

Toda la informacion se almacenara en archivos YAML versionados mediante Git.

Todos los YAML se cargaran y validaran durante el arranque. En produccion, una
configuracion invalida impedira que el proceso arranque correctamente.

Los archivos de configuracion y assets formaran parte de la imagen Docker.

## Alcance inicial

La primera version solo mostrara informacion.

No incluira:

* Pedidos.
* Pagos.
* Reservas.
* Usuarios.
* Autenticacion.
* Panel de administracion.
* Opiniones o puntuaciones.
* Base de datos.
* Aplicacion movil.

## Gestion de restaurantes

Crear una nueva identidad no debera requerir modificar la logica principal.

Idealmente, anadir un restaurante consistira en:

1. Crear una carpeta de configuracion.
2. Definir su identificador estable.
3. Definir su host canonico y aliases permitidos.
4. Anadir sus datos, menu, tema, SEO y bloques visuales.
5. Anadir sus recursos graficos.
6. Validar la configuracion y los assets.
7. Construir y desplegar una nueva imagen Docker.

## Requisitos generales

* Un unico repositorio.
* Un unico servicio.
* Configuracion independiente por identidad.
* Renderizado en servidor.
* Python tipado.
* Configuraciones validadas mediante Pydantic.
* Sin acceso directo a rutas construido a partir de valores no confiables.
* Los hosts validos deben proceder de una lista cerrada de configuraciones.
* Buen rendimiento.
* HTML accesible y semantico.
* Diseno responsive.
* SEO correcto por subdominio.
* Pruebas automaticas.
* Despliegue reproducible con Docker.
* Traefik externo conservando el host original.

## Decisiones pendientes

* Contenido y assets reales para los restaurantes iniciales.
* Inclusion de AVIF en v1.
* Ajustes finales de limites de YAML, textos, menus, imagenes y numero de assets
  cuando exista contenido real.
* Red o IP de Traefik para `FORWARDED_ALLOW_IPS`.
* Mecanismo de actualizacion del servidor.
* Licencia del proyecto.
