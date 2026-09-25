# Fotos de los proyectos

Las fotos de esta carpeta las genera `tools/fotos.py`: no hace falta ponerlas aquí a mano.

1. Pon los originales, tal como salen del móvil, en una carpeta por proyecto dentro de `fotos/`
   (en la raíz del repositorio; esa carpeta no se sube a GitHub). El nombre de la carpeta es el
   `data-project` de la ficha en `src/index.html`:

   | Proyecto | Carpeta |
   |---|---|
   | Cocina abierta con península – Valencia (El Cabanyal) | `fotos/cocina-cabanyal-valencia/` |
   | Fachada con aplacado de piedra – Alzira | `fotos/fachada-alzira/` |
   | Cocina, baño y buhardilla – Carcaixent | `fotos/cocina-bano-buhardilla-carcaixent/` |
   | Proyecto de reforma integral (infografías 3D) – Carcaixent | `fotos/proyecto-3d-carcaixent/` |
   | Cocina abierta con isla – Carcaixent | `fotos/cocina-isla-carcaixent/` |
   | Cocina y baño – Carcaixent | `fotos/cocina-bano-carcaixent/` |
   | Ascensor a cota 0 – Canals | `fotos/ascensor-canals/` |

   Van en orden alfabético y la primera es la portada: para elegirla, llámala por ejemplo `01-portada.jpg`.

2. Ejecuta:

   ```bash
   pip install pillow            # solo la primera vez (y pillow-heif para fotos .heic de iPhone)
   python3 tools/fotos.py
   python3 tools/build.py
   ```

El script endereza las fotos, las pasa a sRGB, las reduce a 1600 px, **les quita todos los metadatos
(también la ubicación GPS, que en casas de clientes es un dato sensible)**, las guarda aquí como
`<proyecto>-1.jpg`, `-2.jpg`… (y la portada también a 800 px de ancho, `<proyecto>-1-800.jpg`, para
los móviles) y rellena el `data-gallery` del proyecto en `src/index.html`. Después `tools/build.py`
pone la portada en la página con su texto alternativo y añade todas las fotos al `sitemap.xml`.

Solo se actualizan los proyectos que tienen carpeta en `fotos/`: los demás se quedan como están.
