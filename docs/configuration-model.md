# Modelo de configuracion

## Objetivo

La configuracion define restaurantes, hosts, contenido, menus, temas, SEO,
bloques visuales y assets sin permitir codigo ejecutable ni rutas arbitrarias.

Todos los archivos se cargan y validan durante startup. La aplicacion construye
un catalogo inmutable y no vuelve a leer configuracion por peticion.

## Estructura

Cada restaurante tendra una carpeta propia:

```text
restaurants/<restaurant-id>/
├── restaurant.yaml
├── menu.yaml
├── theme.yaml
├── seo.yaml
└── assets/
    ├── branding/
    └── menu/
```

El identificador de restaurante debe ser estable, unico y valido. No debe
derivarse de valores recibidos en peticiones.

## Reglas YAML

Los YAML deben:

* cargarse con un loader seguro;
* contener exactamente un documento;
* rechazar tags personalizados;
* respetar limites de tamano por archivo;
* usar datos, no codigo;
* permanecer faciles de revisar en Git.

La implementacion inicial usa un limite de 128 KiB por archivo YAML. Este valor
podra ajustarse si el contenido real lo requiere.

## Validacion Pydantic

Todos los modelos Pydantic usaran `extra="forbid"`.

No se usara `strict=True` globalmente en todos los modelos.

Los campos criticos usaran tipos estrictos, enums, regex y validadores
especificos para evitar coerciones silenciosas, especialmente:

* IDs;
* hosts;
* booleanos;
* precios;
* listas;
* limites numericos;
* rutas relativas de assets;
* variantes de bloques;
* tokens de tema.

## `restaurant.yaml`

Define identidad, estado, hosts y datos de contacto.

Campos esperados a nivel conceptual:

* `id`: identificador estable.
* `enabled`: booleano estricto.
* `canonical_host`: host principal.
* `aliases`: hosts alternativos permitidos.
* `name`: nombre publico.
* `description`: texto plano corto.
* `contact`: telefono, email y direccion si aplica.
* `location`: datos de direccion y coordenadas si aplica.
* `opening_hours`: horarios visibles.
* `assets`: referencias a assets requeridos de identidad.

Cada host de produccion debe ser unico en todo el catalogo.

## `menu.yaml`

Define categorias y productos.

Reglas:

* Precios en unidades menores, por ejemplo centimos.
* No usar floats.
* Categorias con orden estable.
* Productos con nombre, descripcion opcional y precio.
* Maximo inicial de 40 categorias.
* Maximo inicial de 80 productos por categoria.

## `theme.yaml`

Define variaciones visuales validadas.

La configuracion puede usar:

* colores validados;
* tokens de espaciado;
* tokens de bordes;
* tokens de sombras;
* tokens de densidad;
* familias tipograficas permitidas;
* variantes registradas.

No se permiten:

* expresiones CSS arbitrarias;
* CSS libre;
* JavaScript;
* nombres de plantilla;
* rutas arbitrarias.

La aplicacion expondra solamente variables CSS derivadas de valores validados.

## `seo.yaml`

Define SEO por marca.

Campos esperados a nivel conceptual:

* titulo;
* descripcion;
* canonical path o canonical host derivado;
* reglas de `robots.txt`;
* entradas de `sitemap.xml`;
* datos estructurados permitidos.

El JSON-LD no se escribe como HTML en YAML. La aplicacion construye objetos
Python y los serializa como JSON.

## Bloques visuales

Cada bloque visual tendra un modelo Pydantic propio.

Ejemplos:

* `HeroBlock`.
* `MenuBlock`.
* `GalleryBlock`.
* `HoursBlock`.
* `ContactBlock`.

Los bloques usaran una union discriminada por `type`.

No se usara `dict[str, Any]` para configurar bloques.

Cada bloque aceptara solamente sus opciones y variantes registradas.

La configuracion no podra incluir HTML, Markdown renderizado, JavaScript ni rutas
de plantilla.

## Textos

En v1, todos los textos procedentes de YAML son texto plano.

No se permite:

* HTML;
* Markdown renderizado;
* scripts;
* estilos inline;
* uso de `|safe` con valores de YAML.

La implementacion inicial limita textos cortos a 500 caracteres y textos largos
a 2.000 caracteres.

## Assets

Assets compartidos:

```text
/static/
```

Assets por restaurante:

```text
/media/<restaurant-id>/
```

Los assets se referencian por claves o rutas relativas validadas dentro del
directorio del restaurante. La peticion no decide rutas fisicas.

Formatos de imagen obligatorios en v1:

* JPEG.
* PNG.
* WebP.

AVIF queda pendiente hasta confirmar validacion fiable en Docker.

SVG de terceros queda deshabilitado en v1 salvo sanitizacion futura.

Cada imagen debe declarar una de estas opciones:

* `alt` no vacio para imagenes informativas.
* `decorative: true` para imagenes decorativas.

No se pueden omitir ambas.

Se validaran extension, tamano, dimensiones y existencia.

Limites iniciales:

* 5 MiB por imagen.
* 5.000 px de ancho maximo.
* 5.000 px de alto maximo.

## Catalogo resultante

Tras validar la configuracion, la app construira:

* restaurantes por ID;
* hosts canonicos;
* aliases;
* host allowlist;
* restaurantes habilitados;
* rutas logicas de media;
* rutas fisicas validadas;
* datos SEO precalculables;
* bloques validados.

El catalogo sera inmutable durante la vida del proceso.

## Decisiones pendientes

* Ajustar limites iniciales si el contenido real lo requiere.
* Esquema final campo por campo.
* Contenido real de restaurantes iniciales.
* Inclusion de AVIF.
