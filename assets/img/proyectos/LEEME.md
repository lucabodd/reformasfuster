# Fotos de los proyectos

Sube aquí las fotos de las obras (JPG, unos 1600–2000 px de ancho, máximo ~400 KB cada una).

Después, en **`src/index.html`** (la plantilla, no el `index.html` de la raíz), escribe sus rutas en el atributo `data-gallery` del proyecto correspondiente, separadas por comas. La primera será la portada. Las rutas empiezan en la raíz de la web y sirven para los tres idiomas:

```html
<article class="project project--wide" data-reveal
         data-gallery="assets/img/proyectos/fachada-alzira-1.jpg, assets/img/proyectos/fachada-alzira-2.jpg">
```

Y regenera las páginas:

```bash
python3 tools/build.py
```

Nombres sugeridos:

| Proyecto | Fotos |
|---|---|
| Rehabilitación de fachada – Alzira | `fachada-alzira-1.jpg`, `fachada-alzira-2.jpg`… |
| Reforma parcial – Carcaixent | `reforma-parcial-carcaixent-1.jpg`… |
| Reforma integral – Carcaixent | `reforma-integral-carcaixent-1.jpg`… |
| Ascensor a cota 0 – Canals | `ascensor-canals-1.jpg`… |

Mientras un proyecto no tenga fotos, la web muestra su dibujo técnico.
