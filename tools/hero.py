"""Ilustración isométrica del hero de index.html: capa «plano» (líneas y cotas) y capa «3D» (render a color).

Uso:  python3 tools/hero.py
Regenera las dos capas y las inserta en index.html entre los marcadores
<!-- hero:plan --> ... <!-- /hero:plan --> y <!-- hero:render --> ... <!-- /hero:render -->.

Proyección isométrica: x hacia abajo-derecha, y hacia abajo-izquierda, z hacia arriba (unidades en metros).
Los estilos de la capa del plano (.w-*) están en assets/css/styles.css.
"""
import math
import pathlib
import re

S = 23.0  # px por metro
C30 = math.cos(math.radians(30))
W, H = 640, 540
OX, OY = 292.0, 176.0


def P(x, y, z=0.0):
    return (OX + (x - y) * C30 * S, OY + (x + y) * 0.5 * S - z * S)


def fmt(pts):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def poly(pts3, fill, extra=""):
    pts = [P(*p) for p in pts3]
    return f'<polygon points="{fmt(pts)}" fill="{fill}"{extra}/>'


def line(a, b, cls="", extra=""):
    (x1, y1), (x2, y2) = P(*a), P(*b)
    c = f' class="{cls}"' if cls else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"{c}{extra}/>'


def path3(pts3, cls="", closed=True, extra=""):
    pts = [P(*p) for p in pts3]
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + (" Z" if closed else "")
    c = f' class="{cls}"' if cls else ""
    return f'<path d="{d}"{c}{extra}/>'


def rect_y(y, x0, x1, z0, z1):
    """Rectángulo en un plano y=cte (fachada +y)."""
    return [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]


def rect_x(x, y0, y1, z0, z1):
    """Rectángulo en un plano x=cte (fachada +x)."""
    return [(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)]


def rect_z(z, x0, x1, y0, y1):
    return [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]


# ---------------------------------------------------------------- modelo
PLOT = (0.0, 16.0, 0.0, 12.0)  # x0, x1, y0, y1
SLAB = 0.55
A = dict(x0=2.0, x1=10.0, y0=2.0, y1=8.0, h=6.0)  # volumen principal
RIDGE_Y, RIDGE_Z, OVER = 5.0, 8.0, 0.4
SLOPE = (RIDGE_Z - A["h"]) / (RIDGE_Y - A["y0"])  # 2/3
EAVE_Z = RIDGE_Z - (RIDGE_Y - (A["y0"] - OVER)) * SLOPE
B = dict(x0=10.0, x1=14.0, y0=3.5, y1=8.0, h=3.2, par=0.8, t=0.15)  # anexo con terraza

# Huecos (fachada +y del volumen A, y = 8)
A_Y_OPENINGS = [
    ("win", 2.6, 3.8, 0.9, 2.3),
    ("door", 4.3, 5.5, 0.0, 2.45),
    ("win", 6.4, 9.2, 0.6, 2.4),
    ("win", 2.6, 3.8, 3.75, 5.1),
    ("win", 5.0, 6.2, 3.45, 5.45),  # puerta balcón
    ("win", 7.6, 8.8, 3.75, 5.1),
]
# Huecos (fachada +x del volumen A, x = 10)
A_X_OPENINGS = [
    ("win", 4.3, 5.7, 3.85, 5.1),
    ("win", 4.72, 5.28, 6.35, 6.95),  # ventanuco en el hastial
]
B_Y_OPENINGS = [("win", 10.6, 13.4, 0.35, 2.5)]
B_X_OPENINGS = [("win", 4.9, 6.9, 1.0, 2.4)]
BALCONY = dict(x0=4.6, x1=6.6, y0=8.0, y1=8.85, z=3.3, t=0.14, rail=0.95)
CHIMNEY = dict(x0=3.0, x1=3.8, y0=2.9, y1=3.7, top=8.75)
POOL = dict(x0=8.9, x1=14.3, y0=9.9, y1=11.4, lip=0.25, depth=0.16)
PATH_STONES = [(9.75, 10.25), (10.55, 11.05), (11.35, 11.85)]
LIGHT = (0.78, -0.45)  # desplazamiento de sombra por metro de altura (x, y)


def roof_z(y):
    return RIDGE_Z - abs(RIDGE_Y - y) * SLOPE


# ---------------------------------------------------------------- utilidades
def convex_hull(points):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def shadow_of(points3):
    """Proyecta puntos 3D sobre el suelo (z=0) según la luz."""
    out = []
    for x, y, z in points3:
        out.append((x + LIGHT[0] * z, y + LIGHT[1] * z))
    return out


# ---------------------------------------------------------------- colores
C = dict(
    lawn="#c9cba3", lawn_dark="#b9bd92", earth_lit="#a07f61", earth_shade="#876a51",
    paving="#ede5d6", paving_line="#ddd2bf", stone="#e2d7c3",
    plaster_lit="#f5ede1", plaster_shade="#dccab1", plinth_lit="#ddd1bd", plinth_shade="#c4b59b",
    roof_front="#cf6b43", roof_back="#b3552f", roof_edge="#8e3e21", tile="#a9492a",
    glass="#86a4a8", glass_dark="#6c898e", frame="#2b2825", door="#7a4d31", sill="#fbf7f0",
    terrace="#e9dfcf", par_inner="#e3d6c2", par_top="#fbf7f0",
    water="#96cbcf", pool_wall="#6fa6ad", pool_wall2="#5f959c", coping="#f3ede2",
    tree_dark="#7c8b5b", tree_light="#9dab74", trunk="#6b4a33", cypress="#5d6e47", cypress_light="#71835a",
    shadow="rgba(62,42,24,.17)",
)


# ================================================================= RENDER 3D
def render_layer():
    o = []
    x0, x1, y0, y1 = PLOT
    # --- base de terreno (bloque cortado)
    o.append(poly([(x0, y1, 0), (x1, y1, 0), (x1, y1, -SLAB), (x0, y1, -SLAB)], C["earth_lit"]))
    o.append(poly([(x1, y0, 0), (x1, y1, 0), (x1, y1, -SLAB), (x1, y0, -SLAB)], C["earth_shade"]))
    o.append(poly(rect_z(0, x0, x1, y0, y1), C["lawn"]))
    # franjas de césped
    lawn_stroke = ' stroke="%s" stroke-width="1"' % C["lawn_dark"]
    for k in range(1, 8):
        yy = y0 + k * 1.5
        o.append('<g opacity=".35">' + line((x0 + 0.2, yy, 0), (x1 - 0.2, yy, 0), extra=lawn_stroke) + "</g>")
    # --- pavimento alrededor de la casa
    o.append(poly(rect_z(0, 1.2, 15.0, 1.2, 9.4), C["paving"]))
    for k in range(2, 15):
        o.append(line((k * 1.0 + 0.2, 1.2, 0), (k * 1.0 + 0.2, 9.4, 0), extra=f' stroke="{C["paving_line"]}" stroke-width=".7"'))
    # --- camino de acceso (piedras)
    for a, b in PATH_STONES:
        o.append(poly(rect_z(0, 4.25, 5.55, a, b), C["stone"]))
    # --- piscina
    p = POOL
    o.append(poly(rect_z(0, p["x0"], p["x1"], p["y0"], p["y1"]), C["coping"]))
    ix0, ix1, iy0, iy1 = p["x0"] + p["lip"], p["x1"] - p["lip"], p["y0"] + p["lip"], p["y1"] - p["lip"]
    o.append(poly([(ix0, iy0, 0), (ix1, iy0, 0), (ix1, iy0, -p["depth"]), (ix0, iy0, -p["depth"])], C["pool_wall"]))
    o.append(poly([(ix0, iy0, 0), (ix0, iy1, 0), (ix0, iy1, -p["depth"]), (ix0, iy0, -p["depth"])], C["pool_wall2"]))
    o.append(poly(rect_z(-p["depth"], ix0, ix1, iy0, iy1), C["water"]))
    for (wx, wy, L) in [(10.2, 10.55, 1.1), (12.1, 10.85, 0.9), (11.0, 10.4, 0.6)]:
        o.append(line((wx, wy, -p["depth"]), (wx + L, wy, -p["depth"]), extra=' stroke="#fff" stroke-opacity=".7" stroke-width="1.2" stroke-linecap="round"'))

    # --- sombras proyectadas (recortadas a la parcela)
    a_top = [(A["x0"], A["y0"], A["h"]), (A["x1"], A["y0"], A["h"]), (A["x1"], A["y1"], A["h"]), (A["x0"], A["y1"], A["h"]),
             (A["x0"] - OVER, RIDGE_Y, RIDGE_Z), (A["x1"] + OVER, RIDGE_Y, RIDGE_Z),
             (A["x0"] - OVER, A["y0"] - OVER, EAVE_Z), (A["x1"] + OVER, A["y0"] - OVER, EAVE_Z),
             (A["x0"] - OVER, A["y1"] + OVER, EAVE_Z), (A["x1"] + OVER, A["y1"] + OVER, EAVE_Z)]
    a_foot = [(A["x0"], A["y0"]), (A["x1"], A["y0"]), (A["x1"], A["y1"]), (A["x0"], A["y1"])]
    b_top = [(B["x0"], B["y0"], B["h"] + B["par"]), (B["x1"], B["y0"], B["h"] + B["par"]),
             (B["x1"], B["y1"], B["h"] + B["par"]), (B["x0"], B["y1"], B["h"] + B["par"])]
    b_foot = [(B["x0"], B["y0"]), (B["x1"], B["y0"]), (B["x1"], B["y1"]), (B["x0"], B["y1"])]
    shadows = []
    for foot, top in ((a_foot, a_top), (b_foot, b_top)):
        hull = convex_hull(foot + shadow_of(top))
        shadows.append(f'<polygon points="{fmt([P(x, y, 0) for x, y in hull])}"/>')
    # árbol delantero y ciprés
    o.append('<clipPath id="plot-clip"><polygon points="' + fmt([P(*q) for q in rect_z(0, *PLOT)]) + '"/></clipPath>')
    o.append(f'<g clip-path="url(#plot-clip)" fill="{C["shadow"]}">' + "".join(shadows) + "</g>")

    # --- ciprés (detrás de la casa)
    o += cypress(13.75, 0.85, 4.4)
    o += cypress(15.1, 1.1, 5.2)

    # --- volumen A
    ax0, ax1, ay0, ay1, ah = A["x0"], A["x1"], A["y0"], A["y1"], A["h"]
    o.append(poly(rect_y(ay1, ax0, ax1, 0, ah), C["plaster_lit"]))
    o.append(poly([(ax1, ay0, 0), (ax1, ay1, 0), (ax1, ay1, ah), (ax1, RIDGE_Y, RIDGE_Z), (ax1, ay0, ah)], C["plaster_shade"]))
    o.append(poly(rect_y(ay1, ax0, ax1, 0, 0.45), C["plinth_lit"]))
    o.append(poly(rect_x(ax1, ay0, ay1, 0, 0.45), C["plinth_shade"]))
    # línea de forjado
    o.append(line((ax0, ay1, 3.05), (ax1, ay1, 3.05), extra=' stroke="#000" stroke-opacity=".07" stroke-width="1"'))
    o.append(line((ax1, ay0, 3.05), (ax1, ay1, 3.05), extra=' stroke="#000" stroke-opacity=".07" stroke-width="1"'))
    for kind, a, b, z0, z1 in A_Y_OPENINGS:
        o += opening_y(ay1, a, b, z0, z1, kind)
    for kind, a, b, z0, z1 in A_X_OPENINGS:
        o += opening_x(ax1, a, b, z0, z1, kind)
    # balcón
    o += balcony_render()
    # --- cubierta
    rx0, rx1 = ax0 - OVER, ax1 + OVER
    o.append(poly([(rx0, RIDGE_Y, RIDGE_Z), (rx1, RIDGE_Y, RIDGE_Z), (rx1, ay0 - OVER, EAVE_Z), (rx0, ay0 - OVER, EAVE_Z)], C["roof_back"]))
    o.append(poly([(rx0, RIDGE_Y, RIDGE_Z), (rx1, RIDGE_Y, RIDGE_Z), (rx1, ay1 + OVER, EAVE_Z), (rx0, ay1 + OVER, EAVE_Z)], C["roof_front"]))
    n = 22
    for k in range(1, n):
        xx = rx0 + (rx1 - rx0) * k / n
        o.append(line((xx, RIDGE_Y, RIDGE_Z), (xx, ay1 + OVER, EAVE_Z), extra=f' stroke="{C["tile"]}" stroke-width=".9" stroke-opacity=".55"'))
        o.append(line((xx, RIDGE_Y, RIDGE_Z), (xx, ay0 - OVER, EAVE_Z), extra=f' stroke="{C["roof_edge"]}" stroke-width=".8" stroke-opacity=".35"'))
    # cumbrera
    o.append(line((rx0, RIDGE_Y, RIDGE_Z), (rx1, RIDGE_Y, RIDGE_Z), extra=f' stroke="{C["roof_edge"]}" stroke-width="2.2" stroke-linecap="round"'))
    # canto del alero (espesor)
    th = 0.22
    o.append(poly([(rx0, ay1 + OVER, EAVE_Z), (rx1, ay1 + OVER, EAVE_Z), (rx1, ay1 + OVER, EAVE_Z - th), (rx0, ay1 + OVER, EAVE_Z - th)], C["roof_edge"]))
    o.append(poly([(rx1, ay0 - OVER, EAVE_Z), (rx1, RIDGE_Y, RIDGE_Z), (rx1, ay1 + OVER, EAVE_Z), (rx1, ay1 + OVER, EAVE_Z - th), (rx1, RIDGE_Y, RIDGE_Z - th), (rx1, ay0 - OVER, EAVE_Z - th)], "#9b4526"))
    # chimenea
    c = CHIMNEY
    zb0, zb1 = roof_z(c["y0"]), roof_z(c["y1"])
    o.append(poly([(c["x1"], c["y0"], zb0), (c["x1"], c["y1"], zb1), (c["x1"], c["y1"], c["top"]), (c["x1"], c["y0"], c["top"])], C["plaster_shade"]))
    o.append(poly([(c["x0"], c["y1"], zb1), (c["x1"], c["y1"], zb1), (c["x1"], c["y1"], c["top"]), (c["x0"], c["y1"], c["top"])], C["plaster_lit"]))
    e, ct = 0.1, 0.18
    o.append(poly(rect_x(c["x1"] + e, c["y0"] - e, c["y1"] + e, c["top"], c["top"] + ct), "#9b4526"))
    o.append(poly(rect_y(c["y1"] + e, c["x0"] - e, c["x1"] + e, c["top"], c["top"] + ct), C["roof_front"]))
    o.append(poly(rect_z(c["top"] + ct, c["x0"] - e, c["x1"] + e, c["y0"] - e, c["y1"] + e), C["roof_edge"]))

    # --- volumen B (anexo con terraza)
    bx0, bx1, by0, by1, bh, par, t = B["x0"], B["x1"], B["y0"], B["y1"], B["h"], B["par"], B["t"]
    o.append(poly(rect_z(bh, bx0, bx1 - t, by0 + t, by1 - t), C["terrace"]))
    for k in range(1, 8):
        xx = bx0 + k * 0.5
        o.append(line((xx, by0 + t, bh), (xx, by1 - t, bh), extra=' stroke="#d6c9b4" stroke-width=".6"'))
    o.append(poly(rect_y(by0 + t, bx0, bx1 - t, bh, bh + par), C["par_inner"]))
    o.append(poly(rect_z(bh + par, bx0, bx1, by0, by0 + t), C["par_top"]))
    # macetas en la terraza
    o += pot(11.0, 4.3, bh)
    o += pot(12.9, 4.4, bh)
    o.append(poly(rect_y(by1, bx0, bx1, 0, bh + par), C["plaster_lit"]))
    o.append(poly(rect_x(bx1, by0, by1, 0, bh + par), C["plaster_shade"]))
    o.append(poly(rect_y(by1, bx0, bx1, 0, 0.45), C["plinth_lit"]))
    o.append(poly(rect_x(bx1, by0, by1, 0, 0.45), C["plinth_shade"]))
    o.append(poly(rect_z(bh + par, bx0, bx1, by1 - t, by1), C["par_top"]))
    o.append(poly(rect_z(bh + par, bx1 - t, bx1, by0, by1), C["par_top"]))
    for kind, a, b, z0, z1 in B_Y_OPENINGS:
        o += opening_y(by1, a, b, z0, z1, kind)
    for kind, a, b, z0, z1 in B_X_OPENINGS:
        o += opening_x(bx1, a, b, z0, z1, kind)

    # --- árboles delanteros
    o += tree(1.6, 10.4, 1.25, 3.3)
    o += tree(15.1, 9.6, 0.95, 2.6)
    return "\n".join(o)


def opening_y(y, a, b, z0, z1, kind):
    o = []
    f = 0.09
    o.append(poly(rect_y(y, a - f, b + f, z0 - (0 if kind == "door" else f), z1 + f), C["frame"]))
    if kind == "door":
        o.append(poly(rect_y(y, a, b, z0, z1), C["door"]))
        o.append(line((a + (b - a) * 0.5, y, z0 + 0.1), (a + (b - a) * 0.5, y, z1 - 0.1), extra=' stroke="#000" stroke-opacity=".25" stroke-width="1"'))
        o.append(poly(rect_y(y, a + 0.12, a + 0.3, 1.1, 1.2), "#e9c46a"))
        return o
    o.append(poly(rect_y(y, a, b, z0, z1), C["glass"]))
    # reflejo diagonal
    w, h = b - a, z1 - z0
    o.append(poly([(a + w * 0.12, y, z0), (a + w * 0.42, y, z0), (a + w * 0.78, y, z1), (a + w * 0.48, y, z1)], "rgba(255,255,255,.28)"))
    if w > 1.8:  # ventanal con montante central
        o.append(line((a + w / 2, y, z0), (a + w / 2, y, z1), extra=f' stroke="{C["frame"]}" stroke-width="1.6"'))
    # persiana (parte superior)
    o.append(poly(rect_y(y, a, b, z1 - h * 0.22, z1), "#d9cdb9"))
    o.append(line((a, y, z1 - h * 0.11), (b, y, z1 - h * 0.11), extra=' stroke="#b9ab94" stroke-width=".6"'))
    # vierteaguas
    o.append(poly(rect_y(y, a - 0.15, b + 0.15, z0 - 0.16, z0 - 0.02), C["sill"]))
    return o


def opening_x(x, a, b, z0, z1, kind):
    o = []
    f = 0.09
    o.append(poly(rect_x(x, a - f, b + f, z0 - f, z1 + f), C["frame"]))
    o.append(poly(rect_x(x, a, b, z0, z1), C["glass_dark"]))
    w, h = b - a, z1 - z0
    o.append(poly([(x, a + w * 0.15, z0), (x, a + w * 0.4, z0), (x, a + w * 0.75, z1), (x, a + w * 0.5, z1)], "rgba(255,255,255,.18)"))
    if h > 1.0:
        o.append(poly(rect_x(x, a, b, z1 - h * 0.22, z1), "#c7b9a2"))
        o.append(poly(rect_x(x, a - 0.15, b + 0.15, z0 - 0.16, z0 - 0.02), "#e9e0d1"))
    return o


def balcony_render():
    b = BALCONY
    o = []
    x0, x1, y0, y1, z, t, r = b["x0"], b["x1"], b["y0"], b["y1"], b["z"], b["t"], b["rail"]
    # losa
    o.append(poly(rect_y(y1, x0, x1, z - t, z), "#e2d6c3"))
    o.append(poly(rect_x(x1, y0, y1, z - t, z), "#cbbca4"))
    o.append(poly(rect_z(z, x0, x1, y0, y1), "#f1eadf"))
    # barandilla de forja
    stroke = f' stroke="{C["frame"]}" stroke-width="1.1"'
    o.append(line((x0, y1, z + r), (x1, y1, z + r), extra=' stroke="#2b2825" stroke-width="1.6"'))
    o.append(line((x1, y0, z + r), (x1, y1, z + r), extra=' stroke="#2b2825" stroke-width="1.6"'))
    n = 12
    for k in range(n + 1):
        xx = x0 + (x1 - x0) * k / n
        o.append(line((xx, y1, z), (xx, y1, z + r), extra=stroke))
    for k in range(1, 4):
        yy = y0 + (y1 - y0) * k / 4
        o.append(line((x1, yy, z), (x1, yy, z + r), extra=stroke))
    return o


def tree(x, y, r, hz):
    o = []
    # sombra en el suelo
    sx, sy = P(x + LIGHT[0] * hz * 0.6, y + LIGHT[1] * hz * 0.6, 0)
    o.append(f'<ellipse cx="{sx:.1f}" cy="{sy:.1f}" rx="{r * S * 1.25:.1f}" ry="{r * S * 0.62:.1f}" fill="{C["shadow"]}" opacity=".7"/>')
    bx, by = P(x, y, 0)
    tx, ty = P(x, y, hz)
    o.append(f'<path d="M{bx - 2.2:.1f},{by:.1f} L{tx - 1.2:.1f},{ty:.1f} L{tx + 1.2:.1f},{ty:.1f} L{bx + 2.2:.1f},{by:.1f} Z" fill="{C["trunk"]}"/>')
    cx, cy = P(x, y, hz + r * 0.6)
    R = r * S
    o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{R:.1f}" fill="{C["tree_dark"]}"/>')
    o.append(f'<circle cx="{cx - R * 0.55:.1f}" cy="{cy + R * 0.2:.1f}" r="{R * 0.72:.1f}" fill="{C["tree_dark"]}"/>')
    o.append(f'<circle cx="{cx + R * 0.5:.1f}" cy="{cy + R * 0.3:.1f}" r="{R * 0.66:.1f}" fill="{C["tree_dark"]}"/>')
    o.append(f'<circle cx="{cx - R * 0.25:.1f}" cy="{cy - R * 0.25:.1f}" r="{R * 0.62:.1f}" fill="{C["tree_light"]}"/>')
    o.append(f'<circle cx="{cx - R * 0.72:.1f}" cy="{cy + R * 0.22:.1f}" r="{R * 0.36:.1f}" fill="{C["tree_light"]}"/>')
    return o


def cypress(x, y, h):
    o = []
    bx, by = P(x, y, 0)
    cx, cy = P(x, y, h * 0.55)
    rx, ry = 0.62 * S, h * 0.5 * S
    o.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{C["cypress"]}"/>')
    o.append(f'<ellipse cx="{cx - rx * 0.28:.1f}" cy="{cy + ry * 0.05:.1f}" rx="{rx * 0.5:.1f}" ry="{ry * 0.86:.1f}" fill="{C["cypress_light"]}"/>')
    return o


def pot(x, y, z):
    px, py = P(x, y, z)
    return [
        f'<path d="M{px - 5:.1f},{py - 7:.1f} L{px + 5:.1f},{py - 7:.1f} L{px + 3.6:.1f},{py:.1f} L{px - 3.6:.1f},{py:.1f} Z" fill="#b8633f"/>',
        f'<circle cx="{px:.1f}" cy="{py - 12:.1f}" r="6.5" fill="{C["tree_light"]}"/>',
        f'<circle cx="{px + 3:.1f}" cy="{py - 9:.1f}" r="4.2" fill="{C["tree_dark"]}"/>',
    ]


# ================================================================= PLANO (líneas)
def wire_layer():
    o = []
    x0, x1, y0, y1 = PLOT
    # rejilla isométrica sobre el terreno
    g = []
    for k in range(int(x0), int(x1) + 1):
        g.append(line((k, y0, 0), (k, y1, 0)))
    for k in range(int(y0), int(y1) + 1):
        g.append(line((x0, k, 0), (x1, k, 0)))
    o.append('<g class="w-grid">' + "".join(g) + "</g>")

    hidden, visible, detail = [], [], []
    ax0, ax1, ay0, ay1, ah = A["x0"], A["x1"], A["y0"], A["y1"], A["h"]
    rx0, rx1 = ax0 - OVER, ax1 + OVER
    # perímetro de parcela
    visible.append(path3([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)]))
    visible.append(path3([(x0, y1, 0), (x0, y1, -SLAB), (x1, y1, -SLAB), (x1, y0, -SLAB), (x1, y0, 0)], closed=False))
    visible.append(path3([(x1, y1, 0), (x1, y1, -SLAB)], closed=False))
    # aristas ocultas del volumen A
    hidden.append(path3([(ax0, ay1, 0), (ax0, ay0, 0), (ax1, ay0, 0)], closed=False))
    hidden.append(path3([(ax0, ay0, 0), (ax0, ay0, ah)], closed=False))
    # volumen A visible
    visible.append(path3([(ax0, ay1, 0), (ax1, ay1, 0), (ax1, ay0, 0)], closed=False))
    visible.append(path3([(ax0, ay1, 0), (ax0, ay1, ah)], closed=False))
    visible.append(path3([(ax1, ay1, 0), (ax1, ay1, ah)], closed=False))
    visible.append(path3([(ax1, ay0, 0), (ax1, ay0, ah)], closed=False))
    visible.append(path3([(ax0, ay1, ah), (ax1, ay1, ah), (ax1, RIDGE_Y, RIDGE_Z), (ax1, ay0, ah)], closed=False))
    # cubierta
    visible.append(path3([(rx0, ay0 - OVER, EAVE_Z), (rx1, ay0 - OVER, EAVE_Z), (rx1, RIDGE_Y, RIDGE_Z), (rx0, RIDGE_Y, RIDGE_Z), (rx0, ay0 - OVER, EAVE_Z)]))
    visible.append(path3([(rx0, RIDGE_Y, RIDGE_Z), (rx0, ay1 + OVER, EAVE_Z), (rx1, ay1 + OVER, EAVE_Z), (rx1, RIDGE_Y, RIDGE_Z)], closed=False))
    visible.append(path3([(rx0, ay1 + OVER, EAVE_Z - 0.22), (rx1, ay1 + OVER, EAVE_Z - 0.22), (rx1, RIDGE_Y, RIDGE_Z - 0.22), (rx1, ay0 - OVER, EAVE_Z - 0.22)], closed=False))
    # chimenea
    c = CHIMNEY
    zb0, zb1 = roof_z(c["y0"]), roof_z(c["y1"])
    visible.append(path3([(c["x0"], c["y1"], zb1), (c["x0"], c["y1"], c["top"]), (c["x1"], c["y1"], c["top"]), (c["x1"], c["y0"], c["top"]), (c["x0"], c["y0"], c["top"]), (c["x0"], c["y1"], c["top"])], closed=False))
    visible.append(path3([(c["x1"], c["y1"], zb1), (c["x1"], c["y1"], c["top"])], closed=False))
    visible.append(path3([(c["x1"], c["y0"], zb0), (c["x1"], c["y0"], c["top"])], closed=False))
    # forjado (discontinuo)
    hidden.append(path3([(ax0, ay1, 3.05), (ax1, ay1, 3.05), (ax1, ay0, 3.05)], closed=False))
    # huecos
    for kind, a, b, z0, z1 in A_Y_OPENINGS:
        detail.append(path3(rect_y(ay1, a, b, z0, z1)))
        if kind == "door":
            detail.append(path3([(a + (b - a) / 2, ay1, z0), (a + (b - a) / 2, ay1, z1)], closed=False))
        else:
            detail.append(path3([(a, ay1, z0), (b, ay1, z1)], closed=False, extra=' class="w-faint"'))
    for kind, a, b, z0, z1 in A_X_OPENINGS:
        detail.append(path3(rect_x(ax1, a, b, z0, z1)))
    # balcón
    bl = BALCONY
    detail.append(path3([(bl["x0"], ay1, bl["z"]), (bl["x0"], bl["y1"], bl["z"]), (bl["x1"], bl["y1"], bl["z"]), (bl["x1"], ay1, bl["z"])], closed=False))
    detail.append(path3([(bl["x0"], bl["y1"], bl["z"] + bl["rail"]), (bl["x1"], bl["y1"], bl["z"] + bl["rail"]), (bl["x1"], ay1, bl["z"] + bl["rail"])], closed=False))
    detail.append(path3([(bl["x0"], bl["y1"], bl["z"]), (bl["x0"], bl["y1"], bl["z"] + bl["rail"])], closed=False))
    detail.append(path3([(bl["x1"], bl["y1"], bl["z"]), (bl["x1"], bl["y1"], bl["z"] + bl["rail"])], closed=False))
    # volumen B
    bx0, bx1, by0, by1, bh, par, t = B["x0"], B["x1"], B["y0"], B["y1"], B["h"], B["par"], B["t"]
    hidden.append(path3([(bx0, by0, 0), (bx1, by0, 0)], closed=False))
    visible.append(path3([(bx0, by1, 0), (bx1, by1, 0), (bx1, by0, 0), (bx1, by0, bh + par)], closed=False))
    visible.append(path3([(bx1, by1, 0), (bx1, by1, bh + par)], closed=False))
    visible.append(path3(rect_z(bh + par, bx0, bx1, by0, by1)))
    visible.append(path3([(bx0, by0 + t, bh + par), (bx1 - t, by0 + t, bh + par), (bx1 - t, by1 - t, bh + par), (bx0, by1 - t, bh + par)], closed=False))
    hidden.append(path3([(bx0, by0 + t, bh), (bx1 - t, by0 + t, bh), (bx1 - t, by1 - t, bh)], closed=False))
    for kind, a, b, z0, z1 in B_Y_OPENINGS:
        detail.append(path3(rect_y(by1, a, b, z0, z1)))
        detail.append(path3([(a + (b - a) / 2, by1, z0), (a + (b - a) / 2, by1, z1)], closed=False))
    for kind, a, b, z0, z1 in B_X_OPENINGS:
        detail.append(path3(rect_x(bx1, a, b, z0, z1)))
    # piscina y camino
    p = POOL
    detail.append(path3(rect_z(0, p["x0"], p["x1"], p["y0"], p["y1"])))
    detail.append(path3(rect_z(0, p["x0"] + p["lip"], p["x1"] - p["lip"], p["y0"] + p["lip"], p["y1"] - p["lip"])))
    for a, b in PATH_STONES:
        detail.append(path3(rect_z(0, 4.25, 5.55, a, b)))
    detail.append(path3(rect_z(0, 1.2, 15.0, 1.2, 9.4), extra=' class="w-faint"'))

    o.append('<g class="w-hidden">' + "".join(hidden) + "</g>")
    o.append('<g class="w-line">' + "".join(p.replace("<path ", '<path pathLength="1" ') for p in visible) + "</g>")
    o.append('<g class="w-detail">' + "".join(p.replace("<path ", '<path pathLength="1" ') for p in detail) + "</g>")

    # árboles en planta (círculos punteados)
    tx, ty = P(1.6, 10.4, 0)
    o.append(f'<ellipse class="w-tree" cx="{tx:.1f}" cy="{ty:.1f}" rx="{1.25 * S * 1.2:.1f}" ry="{1.25 * S * 0.7:.1f}"/>')
    tx, ty = P(15.1, 9.6, 0)
    o.append(f'<ellipse class="w-tree" cx="{tx:.1f}" cy="{ty:.1f}" rx="{0.95 * S * 1.2:.1f}" ry="{0.95 * S * 0.7:.1f}"/>')

    o.append(cotas())
    return "\n".join(o)


def dim_line(a, b, off_dir, off, label, ext_start=0.25, anchor_shift=0.0):
    """Cota entre a y b (puntos 3D en el suelo o fachada), desplazada off en off_dir (vector 3D)."""
    ox, oy, oz = off_dir
    A2 = (a[0] + ox * off, a[1] + oy * off, a[2] + oz * off)
    B2 = (b[0] + ox * off, b[1] + oy * off, b[2] + oz * off)
    e0a = (a[0] + ox * ext_start, a[1] + oy * ext_start, a[2] + oz * ext_start)
    e0b = (b[0] + ox * ext_start, b[1] + oy * ext_start, b[2] + oz * ext_start)
    e1a = (a[0] + ox * (off + 0.35), a[1] + oy * (off + 0.35), a[2] + oz * (off + 0.35))
    e1b = (b[0] + ox * (off + 0.35), b[1] + oy * (off + 0.35), b[2] + oz * (off + 0.35))
    o = [line(e0a, e1a), line(e0b, e1b), line(A2, B2)]
    # marcas oblicuas (estilo arquitectónico)
    for pnt in (A2, B2):
        px, py = P(*pnt)
        o.append(f'<line x1="{px - 4:.1f}" y1="{py + 4:.1f}" x2="{px + 4:.1f}" y2="{py - 4:.1f}" class="w-tick"/>')
    (ax_, ay_), (bx_, by_) = P(*A2), P(*B2)
    mx, my = (ax_ + bx_) / 2, (ay_ + by_) / 2
    ang = math.degrees(math.atan2(by_ - ay_, bx_ - ax_))
    if ang > 90:
        ang -= 180
    if ang < -90:
        ang += 180
    o.append(f'<text x="{mx:.1f}" y="{my - 5 + anchor_shift:.1f}" text-anchor="middle" transform="rotate({ang:.1f} {mx:.1f} {my:.1f})">{label}</text>')
    return "".join(o)


def level_mark(pt, label, left=True):
    px, py = P(*pt)
    d = -1 if left else 1
    tri = f'<path class="w-level" d="M{px + d * 18:.1f},{py:.1f} l-5,-8 h10 Z"/>'
    ln = f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{px + d * 44:.1f}" y2="{py:.1f}" class="w-cota-l"/>'
    tx = px + d * 48
    anchor = "end" if left else "start"
    txt = f'<text x="{tx:.1f}" y="{py + 4:.1f}" text-anchor="{anchor}">{label}</text>'
    return tri + ln + txt


def cotas():
    ax0, ax1, ay0, ay1, ah = A["x0"], A["x1"], A["y0"], A["y1"], A["h"]
    o = ['<g class="w-cotas">']
    # cotas horizontales en fachada principal (encadenadas)
    o.append(dim_line((ax0, ay1, 0), (ax1, ay1, 0), (0, 1, 0), 1.45, "8,00"))
    o.append(dim_line((B["x0"], B["y1"], 0), (B["x1"], B["y1"], 0), (0, 1, 0), 1.45, "4,00"))
    # fondo del volumen A (lado derecho, detrás del anexo)
    o.append(dim_line((B["x1"], ay0, 0), (B["x1"], ay1, 0), (1, 0, 0), 1.3, "6,00"))
    # niveles
    o.append(level_mark((ax0, ay1, 0), "±0,00"))
    o.append(level_mark((ax0, ay1, 3.05), "+3,05"))
    o.append(level_mark((ax0, ay1, ah), "+6,00"))
    o.append(level_mark((ax0 - OVER, RIDGE_Y, RIDGE_Z), "+8,00"))
    o.append("</g>")
    return "".join(o)


# ================================================================= salida
def build():
    render = render_layer()
    wire = wire_layer()
    vb = f'0 0 {W} {H}'
    svg_wire = (f'<svg class="compare__svg" viewBox="{vb}" role="img" aria-labelledby="plano-title">'
                f'<title id="plano-title">Plano isométrico de una vivienda con cotas</title>{wire}</svg>')
    svg_render = (f'<svg class="compare__svg" viewBox="{vb}" role="img" aria-labelledby="render-title">'
                  f'<title id="render-title">Visualización 3D de la misma vivienda terminada</title>{render}</svg>')
    return svg_wire, svg_render


def inject(index_path):
    wire, render = build()
    html = index_path.read_text(encoding="utf-8")
    for name, svg in (("plan", wire), ("render", render)):
        pat = re.compile(rf"(<!-- hero:{name} -->)(.*?)(<!-- /hero:{name} -->)", re.S)
        if not pat.search(html):
            raise SystemExit(f"No encuentro el marcador hero:{name} en {index_path}")
        html = pat.sub(lambda m: f"{m.group(1)}\n{svg}\n{m.group(3)}", html)
    index_path.write_text(html, encoding="utf-8")
    print(f"Ilustración actualizada en {index_path}")


if __name__ == "__main__":
    inject(pathlib.Path(__file__).resolve().parent.parent / "index.html")
