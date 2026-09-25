#!/usr/bin/env python3
"""Genera la web en castellano, valenciano e inglés a partir de la plantilla.

Uso:  python3 tools/build.py

Lee  src/index.html   plantilla de la página
     src/i18n.toml    textos en los tres idiomas
     src/partials/    trozos que se insertan en la plantilla (iconos, ilustración, logo)
Escribe index.html (castellano), va/index.html (valencià), en/index.html (English) y sitemap.xml.

Fotos de los proyectos: en cada ficha (<article data-gallery="foto1.jpg, foto2.jpg…">) pone la portada
(la primera foto) dentro de .project__media, con su texto alternativo («título en lugar»), su tamaño y,
si existe foto1-800.jpg, un srcset para los móviles. Comprueba que todas las fotos existen y las añade
al sitemap para que Google Imágenes las encuentre (las del resto de la galería solo las carga el JS).

Sintaxis de la plantilla:
  {{ clave }}           texto de src/i18n.toml en el idioma de la página (puede llevar HTML)
  {{ clave | attr }}    el mismo texto, escapado para ir dentro de un atributo
  {{ clave | url }}     codificado para una URL (enlaces de WhatsApp)
  {{ clave | json }}    como cadena JSON sin etiquetas HTML (datos estructurados)
  {{ page.xxx }}        valores que calcula este script (idioma, rutas, enlaces entre idiomas…)
  {{> archivo }}        inserta src/partials/archivo

Requiere Python 3.11 o superior (o el paquete tomli en versiones anteriores).
"""
import hashlib
import html
import json
import pathlib
import re
import sys
import urllib.parse

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        sys.exit("Hace falta Python 3.11 o superior (o instalar tomli: pip install tomli).")

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
SITE = "https://www.f2fconstruccionesyreformas.com/"

# El primero es el idioma por defecto (se publica en la raíz y es el x-default).
LANGS = {
    "es": dict(dir="", html_lang="es", hreflang="es", og_locale="es_ES", name="Castellano", short="ES", og_image="og-image.jpg"),
    "va": dict(dir="va/", html_lang="ca-valencia", hreflang="ca", og_locale="ca_ES", name="Valencià", short="VA", og_image="og-image-va.jpg"),
    "en": dict(dir="en/", html_lang="en", hreflang="en", og_locale="en_GB", name="English", short="EN", og_image="og-image-en.jpg"),
}
DEFAULT = next(iter(LANGS))

TAG = re.compile(r"\{\{\s*(>)?\s*([\w.\-/]+)\s*(?:\|\s*(\w+)\s*)?\}\}")
HTML_TAG = re.compile(r"<[^>]+>")
JSON_LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
PROJECT = re.compile(r'(<article\b[^>]*\bdata-gallery="([^"]*)"[^>]*>)(.*?</article>)', re.S)
MEDIA = '<div class="project__media">'

# Portadas de los proyectos: versión pequeña (tools/fotos.py la genera con este ancho) y ancho con que
# se muestran, coherente con la rejilla de .projects__grid en styles.css (la ficha más ancha mide 715 px).
COVER_WIDTH = 800
COVER_SIZES = "(min-width: 1304px) 715px, (min-width: 900px) 55vw, 100vw"

# Límites orientativos de lo que Google muestra sin cortar en los resultados de búsqueda
MAX_TITLE = 62
MAX_DESCRIPTION = 160

# Hojas de estilo y scripts: se enlazan con ?v=<huella del contenido> para que los navegadores
# puedan guardarlos en caché mucho tiempo y aun así reciban la versión nueva tras cada cambio.
VERSIONED_ASSETS = {"css": "assets/css/styles.css", "js": "assets/js/main.js"}
GENERATED_NOTE = "<!-- Generado por tools/build.py a partir de src/index.html y src/i18n.toml: no editar a mano. -->"


class BuildError(Exception):
    pass


def load_strings():
    with open(SRC / "i18n.toml", "rb") as fh:
        tree = tomllib.load(fh)
    strings, errors = {}, []

    def walk(node, prefix):
        for key, value in node.items():
            path = f"{prefix}{key}"
            if isinstance(value, dict) and value and set(value) <= set(LANGS) and all(isinstance(v, str) for v in value.values()):
                missing = [lang for lang in LANGS if lang not in value]
                if missing:
                    errors.append(f"{path}: falta la traducción {', '.join(missing)}")
                strings[path] = value
            elif isinstance(value, dict):
                walk(value, f"{path}.")
            else:
                errors.append(f"{path}: cada texto necesita sus versiones {path}.es / .va / .en")

    walk(tree, "")
    if errors:
        raise BuildError("Errores en src/i18n.toml:\n  " + "\n  ".join(errors))
    return strings


def expand_partials(text, depth=0):
    if depth > 5:
        raise BuildError("Demasiados niveles de {{> parcial }} anidados")

    def replace(match):
        if not match.group(1):
            return match.group(0)
        path = SRC / "partials" / match.group(2)
        if not path.is_file():
            raise BuildError(f"No existe el parcial src/partials/{match.group(2)}")
        return expand_partials(path.read_text(encoding="utf-8").rstrip("\n"), depth + 1)

    return TAG.sub(replace, text)


def plain_text(value):
    return re.sub(r"\s+", " ", html.unescape(HTML_TAG.sub("", value))).strip()


def versioned(path):
    digest = hashlib.sha1((ROOT / path).read_bytes()).hexdigest()[:10]
    return f"{path}?v={digest}"


SINGLE_QUOTED_ATTR = re.compile(r"(\s[\w:-]+)='([^'\"<>]*)'")


def apply_filter(value, name, key):
    if name is None:
        # en i18n.toml los atributos de los enlaces van entre comillas simples; en la página, dobles
        return SINGLE_QUOTED_ATTR.sub(r'\1="\2"', value)
    if name == "attr":
        return html.escape(html.unescape(value), quote=True)
    if name == "url":
        return urllib.parse.quote(html.unescape(value), safe="")
    if name == "json":
        return json.dumps(plain_text(value), ensure_ascii=False)
    raise BuildError(f"Filtro desconocido «{name}» en {{{{ {key} }}}}")


def image_size(path):
    """Ancho y alto de un JPEG o PNG leyendo solo su cabecera; None si no se reconoce el formato."""
    data = path.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if data[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            return None
        marker = data[i + 1]
        if marker == 0xFF:  # byte de relleno
            i += 1
        elif marker == 0x01 or 0xD0 <= marker <= 0xD8:  # marcadores sin longitud
            i += 2
        elif 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):  # SOFn: ahí está el tamaño
            return int.from_bytes(data[i + 7:i + 9], "big"), int.from_bytes(data[i + 5:i + 7], "big")
        else:
            i += 2 + int.from_bytes(data[i + 2:i + 4], "big")
    return None


def find_projects(template):
    """Las fichas de proyecto con fotos: [{"photos": [...], "render": bool}], comprobando que existen."""
    projects, missing = [], []
    for match in PROJECT.finditer(template):
        photos = [path.strip() for path in match.group(2).split(",") if path.strip()]
        missing += [path for path in photos if not (ROOT / path).is_file()]
        if photos:
            projects.append({"photos": photos, "render": 'data-kind="render"' in match.group(1)})
    if missing:
        raise BuildError("data-gallery de src/index.html apunta a fotos que no existen:\n  " + "\n  ".join(missing))
    return projects


def cover_img(photos, root, alt):
    """<img> de la portada de un proyecto (la primera foto de su galería)."""
    cover = ROOT / photos[0]
    size = image_size(cover)
    attrs = [f'class="project__cover" src="{root}{urllib.parse.quote(photos[0])}"']
    small = cover.with_name(f"{cover.stem}-{COVER_WIDTH}{cover.suffix}")
    small_size = image_size(small) if small.is_file() else None
    if size and small_size:
        small_path = urllib.parse.quote(small.relative_to(ROOT).as_posix())
        attrs.append(f'srcset="{root}{small_path} {small_size[0]}w, {root}{urllib.parse.quote(photos[0])} {size[0]}w" sizes="{COVER_SIZES}"')
    if size:
        attrs.append(f'width="{size[0]}" height="{size[1]}"')
    attrs.append(f'alt="{html.escape(alt, quote=True)}" loading="lazy" decoding="async"')
    return f"<img {' '.join(attrs)}>"


def add_covers(page, root, in_place):
    def replace(match):
        opening, gallery, body = match.groups()
        photos = [path.strip() for path in gallery.split(",") if path.strip()]
        if not photos or MEDIA not in body:
            return match.group(0)
        title = re.search(r"<h3>(.*?)</h3>", body, re.S)
        place = re.search(r'class="project__loc">(.*?)</span>', body, re.S)
        title = plain_text(title.group(1)) if title else ""
        alt = in_place.replace("{title}", title).replace("{place}", plain_text(place.group(1))) if place else title
        indent = "\n" + " " * 14
        img = cover_img(photos, root, alt)
        if f"{MEDIA}</div>" in body:
            body = body.replace(f"{MEDIA}</div>", f"{MEDIA}{indent}{img}{indent[:-2]}</div>", 1)
        else:
            body = body.replace(MEDIA, f"{MEDIA}{indent}{img}", 1)
        return opening + body

    return PROJECT.sub(replace, page)


def lang_links(current, root, compact):
    items = []
    for code, lang in LANGS.items():
        href = f"{root}{lang['dir']}" or "./"
        attrs = f'href="{href}" hreflang="{lang["hreflang"]}" lang="{lang["html_lang"]}" data-lang-link'
        if code == current:
            attrs += ' aria-current="page"'
        label = f'{lang["short"]}<span class="visually-hidden"> · {lang["name"]}</span>' if compact else lang["name"]
        items.append(f"            <li><a {attrs}>{label}</a></li>")
    return "\n".join(items)


def page_vars(code, strings, projects):
    lang = LANGS[code]
    root = "../" * lang["dir"].count("/")
    alternates = [f'  <link rel="alternate" hreflang="{l["hreflang"]}" href="{SITE}{l["dir"]}">' for l in LANGS.values()]
    alternates.append(f'  <link rel="alternate" hreflang="x-default" href="{SITE}{LANGS[DEFAULT]["dir"]}">')
    og_alternates = [f'  <meta property="og:locale:alternate" content="{l["og_locale"]}">' for c, l in LANGS.items() if c != code]
    js_strings = {key[3:]: value[code] for key, value in strings.items() if key.startswith("js.")}
    return {
        "lang": lang["html_lang"],
        "root": root,
        "url": f"{SITE}{lang['dir']}",
        "alternates": "\n".join(alternates),
        "og_locale": lang["og_locale"],
        "og_locale_alternates": "\n".join(og_alternates),
        "og_image": f"{SITE}assets/img/{lang['og_image']}",
        # imágenes de la empresa para los datos estructurados: la de compartir y las portadas de las obras
        "images": json.dumps(
            [f"{SITE}assets/img/{lang['og_image']}"]
            + [SITE + urllib.parse.quote(p["photos"][0]) for p in projects if not p["render"]]
        ),
        "lang_links_short": lang_links(code, root, compact=True),
        "lang_links_full": lang_links(code, root, compact=False),
        "js_strings": json.dumps(js_strings, ensure_ascii=False).replace("</", "<\\/"),
        **{name: versioned(path) for name, path in VERSIONED_ASSETS.items()},
        "generated_note": GENERATED_NOTE,
    }


def render(template, code, strings, used, projects):
    page = page_vars(code, strings, projects)

    def replace(match):
        key, filt = match.group(2), match.group(3)
        if key.startswith("page."):
            name = key[5:]
            if name not in page:
                raise BuildError(f"Variable desconocida {{{{ {key} }}}}")
            return apply_filter(page[name], filt, key)
        if key not in strings:
            raise BuildError(f"La plantilla usa {{{{ {key} }}}} pero no está en src/i18n.toml")
        used.add(key)
        return apply_filter(strings[key][code], filt, key)

    out = TAG.sub(replace, template)
    out = add_covers(out, page["root"], strings["js.in_place"][code])
    leftover = re.search(r"\{\{|\}\}", out)
    if leftover:
        line = out.count("\n", 0, leftover.start()) + 1
        raise BuildError(f"[{code}] Queda una llave sin sustituir en la línea {line}")
    for block in JSON_LD.findall(out):
        try:
            json.loads(block)
        except json.JSONDecodeError as err:
            raise BuildError(f"[{code}] Los datos estructurados (JSON-LD) no son JSON válido: {err}") from None
    return out


def seo_warnings(strings):
    warnings = []
    for key, limit in (("meta.title", MAX_TITLE), ("meta.description", MAX_DESCRIPTION)):
        for code, value in strings.get(key, {}).items():
            length = len(plain_text(value))
            if length > limit:
                warnings.append(f"{key}.{code} tiene {length} caracteres (Google suele cortar a partir de ~{limit})")
    return warnings


def sitemap(projects):
    images = "".join(
        f"\n    <image:image><image:loc>{SITE}{urllib.parse.quote(photo)}</image:loc></image:image>"
        for project in projects for photo in project["photos"]
    )
    urls = []
    for lang in LANGS.values():
        links = "".join(
            f'\n    <xhtml:link rel="alternate" hreflang="{l["hreflang"]}" href="{SITE}{l["dir"]}"/>' for l in LANGS.values()
        )
        links += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{LANGS[DEFAULT]["dir"]}"/>'
        urls.append(f"  <url>\n    <loc>{SITE}{lang['dir']}</loc>{links}{images}\n  </url>")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml"'
        ' xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )


def main():
    strings = load_strings()
    template = expand_partials((SRC / "index.html").read_text(encoding="utf-8"))
    projects = find_projects(template)
    used = set()
    for code, lang in LANGS.items():
        out = ROOT / lang["dir"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(template, code, strings, used, projects), encoding="utf-8")
        print(f"  {code}  →  {out.relative_to(ROOT)}")
    (ROOT / "sitemap.xml").write_text(sitemap(projects), encoding="utf-8")
    photos = sum(len(p["photos"]) for p in projects)
    print(f"  sitemap.xml ({photos} fotos de {len(projects)} proyectos)")

    unused = sorted(key for key in strings if key not in used and not key.startswith("js."))
    if unused:
        print("Aviso: textos de src/i18n.toml que la plantilla no usa: " + ", ".join(unused))
    for warning in seo_warnings(strings):
        print("Aviso SEO: " + warning)


if __name__ == "__main__":
    try:
        main()
    except BuildError as err:
        sys.exit(f"Error: {err}")
