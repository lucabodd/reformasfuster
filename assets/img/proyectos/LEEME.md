# Fotos de los proyectos

Las fotos de esta carpeta las genera `tools/fotos.py`: no hace falta ponerlas aquí a mano.

1. Pon los originales, tal como salen del móvil, en una carpeta por proyecto dentro de `fotos/`
   (en la raíz del repositorio; esa carpeta no se sube a GitHub):

   | Proyecto | Carpeta |
   |---|---|
   | Rehabilitación de fachada – Alzira | `fotos/fachada-alzira/` |
   | Reforma parcial – Carcaixent | `fotos/reforma-parcial-carcaixent/` |
   | Reforma integral – Carcaixent | `fotos/reforma-integral-carcaixent/` |
   | Ascensor a cota 0 – Canals | `fotos/ascensor-canals/` |

   Van en orden alfabético: para elegir la portada, llámala por ejemplo `01-portada.jpg`.

2. Ejecuta:

   ```bash
   pip install pillow            # solo la primera vez (y pillow-heif para fotos .heic de iPhone)
   python3 tools/fotos.py
   python3 tools/build.py
   ```

El script endereza las fotos, las pasa a sRGB, las reduce a 1600 px, **les quita todos los metadatos
(también la ubicación GPS, que en casas de clientes es un dato sensible)**, las guarda aquí como
`<proyecto>-1.jpg`, `-2.jpg`… y rellena el `data-gallery` del proyecto en `src/index.html`.

Mientras un proyecto no tenga fotos, la web muestra su dibujo técnico.
