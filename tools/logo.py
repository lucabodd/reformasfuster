#!/usr/bin/env python3
"""Genera el logotipo de F2F a partir de las fuentes de la marca.

Uso:  pip install fonttools brotli   (solo la primera vez)
      python3 tools/logo.py && python3 tools/build.py

El logotipo es «F2F»: las F en Archivo (peso 800, anchura 125 %) y el 2 en Instrument Serif cursiva,
el mismo contraste tipográfico de los titulares de la web. Se generan contornos (paths), así que los
SVG no dependen de ninguna fuente instalada.

Escribe:
  src/partials/logo-wordmark.svg   logotipo para la cabecera y el pie (colores por CSS: .brand__f / .brand__two)
  assets/img/logo-icon.svg         icono cuadrado: F2F bajo una cota, sobre grafito (app, redes, datos estructurados)
  favicon.svg                      favicon: el 2 en cursiva sobre grafito (legible a 16 px)
"""
import pathlib

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"

GRAPHITE = "#1d1b18"
PAPER = "#f5f0e8"
TERRACOTTA_LIGHT = "#e8835a"

SANS = instantiateVariableFont(TTFont(FONTS / "archivo-var.woff2"), {"wght": 800, "wdth": 125})
SERIF = TTFont(FONTS / "instrument-serif-italic.woff2")

TWO_SCALE = 1.16   # el 2 algo mayor que las F: sobresale por arriba
KERN_F2 = -0.10    # espacio F→2 (en alturas de mayúscula)
KERN_2F = 0.10     # espacio 2→F


def glyph(font, ch, size):
    """(path, bounds) del carácter con cuerpo `size`, con la línea base en y = 0."""
    gs = font.getGlyphSet()
    name = font.getBestCmap()[ord(ch)]
    s = size / font["head"].unitsPerEm
    pen = SVGPathPen(gs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    gs[name].draw(TransformPen(pen, (s, 0, 0, -s, 0, 0)))
    bounds_pen = BoundsPen(gs)
    gs[name].draw(bounds_pen)
    x0, y0, x1, y1 = (v * s for v in bounds_pen.bounds)
    return pen.getCommands(), (x0, -y1, x1, -y0)


def wordmark(cap=100):
    """Devuelve [(clase, path, dx)], ancho, alto_total, y_superior para «F2F» con altura de mayúscula `cap`."""
    size = cap / 0.688  # altura de la F en Archivo = 0,688 em
    d_f, b_f = glyph(SANS, "F", size)
    d_2, b_2 = glyph(SERIF, "2", size * TWO_SCALE)
    parts, x = [], -b_f[0]
    parts.append(("brand__f", d_f, x))
    x2 = x + b_f[2] + KERN_F2 * cap - b_2[0]
    parts.append(("brand__two", d_2, x2))
    x3 = x2 + b_2[2] + KERN_2F * cap - b_f[0]
    parts.append(("brand__f", d_f, x3))
    width = x3 + b_f[2]
    top = min(b_f[1], b_2[1])
    return parts, width, top


def fmt(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def wordmark_svg():
    parts, width, top = wordmark(100)
    paths = "".join(f'<path class="{c}" d="{d}" transform="translate({fmt(dx)} 0)"/>' for c, d, dx in parts)
    h = -top
    return (f'<svg class="brand__logo" viewBox="0 {fmt(top)} {fmt(width)} {fmt(h)}" aria-hidden="true" focusable="false">'
            f"{paths}</svg>")


def icon_svg():
    """Icono 100×100: cota + F2F sobre grafito."""
    parts, width, top = wordmark(100)
    scale = 70 / width
    tx = (100 - width * scale) / 2
    cap_px = 100 * scale
    base = 57 + cap_px / 2
    paths = "".join(
        f'<path d="{d}" fill="{TERRACOTTA_LIGHT if c == "brand__two" else PAPER}" transform="translate({fmt(tx + dx * scale)} {fmt(base)}) scale({scale:.4f})"/>'
        for c, d, dx in parts
    )
    x0, x1, y = fmt(tx), fmt(tx + width * scale), 27
    cota = (f'<path d="M{x0} {y}H{x1}M{x0} {y - 5}v10M{x1} {y - 5}v10" fill="none" stroke="{TERRACOTTA_LIGHT}" '
            f'stroke-width="3" stroke-linecap="square"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" rx="22" fill="{GRAPHITE}"/>'
            f"{cota}{paths}</svg>\n")


def favicon_svg():
    """El 2 en cursiva sobre grafito, con márgenes pensados para 16–48 px."""
    d, (x0, y0, x1, y1) = glyph(SERIF, "2", 96)
    dx = 50 - (x0 + x1) / 2
    dy = 51 - (y0 + y1) / 2
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" rx="22" fill="{GRAPHITE}"/>'
            f'<path d="{d}" fill="{TERRACOTTA_LIGHT}" transform="translate({fmt(dx)} {fmt(dy)})"/></svg>\n')


if __name__ == "__main__":
    (ROOT / "src" / "partials" / "logo-wordmark.svg").write_text(wordmark_svg() + "\n", encoding="utf-8")
    (ROOT / "assets" / "img" / "logo-icon.svg").write_text(icon_svg(), encoding="utf-8")
    (ROOT / "favicon.svg").write_text(favicon_svg(), encoding="utf-8")
    print("Logotipo generado: src/partials/logo-wordmark.svg, assets/img/logo-icon.svg, favicon.svg")
