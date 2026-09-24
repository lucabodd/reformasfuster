#!/usr/bin/env python3
"""Genera la web en castellano, valenciano e inglés a partir de la plantilla.

Uso:  python3 tools/build.py

Lee  src/index.html   plantilla de la página
     src/i18n.toml    textos en los tres idiomas
     src/partials/    trozos que se insertan en la plantilla (iconos, ilustraciones, dibujos)
Escribe index.html (castellano), va/index.html (valencià), en/index.html (English) y sitemap.xml.

Sintaxis de la plantilla:
  {{ clave }}           texto de src/i18n.toml en el idioma de la página (puede llevar HTML)
  {{ clave | attr }}    el mismo texto, escapado para ir dentro de un atributo
  {{ clave | url }}     codificado para una URL (enlaces de WhatsApp)
  {{ clave | json }}    como cadena JSON (datos estructurados)
  {{ page.xxx }}        valores que calcula este script (idioma, rutas, enlaces entre idiomas…)
  {{> archivo }}        inserta src/partials/archivo

Requiere Python 3.11 o superior (o el paquete tomli en versiones anteriores).
"""
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


def apply_filter(value, name, key):
    if name is None:
        return value
    if name == "attr":
        return html.escape(html.unescape(value), quote=True)
    if name == "url":
        return urllib.parse.quote(html.unescape(value), safe="")
    if name == "json":
        return json.dumps(html.unescape(value), ensure_ascii=False)
    raise BuildError(f"Filtro desconocido «{name}» en {{{{ {key} }}}}")


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


def page_vars(code, strings):
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
        "lang_links_short": lang_links(code, root, compact=True),
        "lang_links_full": lang_links(code, root, compact=False),
        "js_strings": json.dumps(js_strings, ensure_ascii=False).replace("</", "<\\/"),
        "generated_note": GENERATED_NOTE,
    }


def render(template, code, strings, used):
    page = page_vars(code, strings)

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
    leftover = re.search(r"\{\{|\}\}", out)
    if leftover:
        line = out.count("\n", 0, leftover.start()) + 1
        raise BuildError(f"[{code}] Queda una llave sin sustituir en la línea {line}")
    return out


def sitemap():
    urls = []
    for lang in LANGS.values():
        links = "".join(
            f'\n    <xhtml:link rel="alternate" hreflang="{l["hreflang"]}" href="{SITE}{l["dir"]}"/>' for l in LANGS.values()
        )
        links += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{LANGS[DEFAULT]["dir"]}"/>'
        urls.append(f"  <url>\n    <loc>{SITE}{lang['dir']}</loc>{links}\n  </url>")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )


def main():
    strings = load_strings()
    template = expand_partials((SRC / "index.html").read_text(encoding="utf-8"))
    used = set()
    for code, lang in LANGS.items():
        out = ROOT / lang["dir"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(template, code, strings, used), encoding="utf-8")
        print(f"  {code}  →  {out.relative_to(ROOT)}")
    (ROOT / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    print("  sitemap.xml")

    unused = sorted(key for key in strings if key not in used and not key.startswith("js."))
    if unused:
        print("Aviso: textos de src/i18n.toml que la plantilla no usa: " + ", ".join(unused))


if __name__ == "__main__":
    try:
        main()
    except BuildError as err:
        sys.exit(f"Error: {err}")
