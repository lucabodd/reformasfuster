#!/usr/bin/env python3
"""Prepara las fotos de los proyectos para la web.

Uso:  pip install pillow               (solo la primera vez; pillow-heif para fotos .heic de iPhone)
      python3 tools/fotos.py && python3 tools/build.py

Pon las fotos originales, tal como salen del móvil o de la cámara, en una carpeta por proyecto
cuyo nombre sea el data-project de su ficha en src/index.html:
    fotos/cocina-cabanyal-valencia/
    fotos/fachada-alzira/
    fotos/cocina-bano-buhardilla-carcaixent/
    fotos/proyecto-3d-carcaixent/
    fotos/cocina-isla-carcaixent/
    fotos/cocina-bano-carcaixent/
    fotos/ascensor-canals/
El orden es el alfabético de los archivos, así que para elegir la portada basta con llamarla,
por ejemplo, 01-portada.jpg.

Para cada foto el script:
  - la endereza según la orientación que guardó la cámara,
  - convierte el color a sRGB (las de iPhone vienen en Display P3),
  - la reduce a 1600 px en el lado largo y la guarda como JPEG optimizado,
  - ELIMINA todos los metadatos, incluida la ubicación GPS (son casas de clientes),
y la guarda en assets/img/proyectos/<proyecto>-1.jpg, -2.jpg… De la portada guarda además una
versión de 800 px de ancho (<proyecto>-1-800.jpg) para los móviles. Después escribe las rutas en
el data-gallery del proyecto en src/index.html; tools/build.py hace el resto.

La carpeta fotos/ no se sube al repositorio (está en .gitignore): los originales pesan mucho.
"""
import io
import pathlib
import re
import sys

try:
    from PIL import Image, ImageCms, ImageOps
except ModuleNotFoundError:
    sys.exit("Hace falta Pillow: pip install pillow")

try:  # fotos .heic de iPhone (opcional)
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC = True
except ModuleNotFoundError:
    HEIC = False

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "fotos"
OUTPUT = ROOT / "assets" / "img" / "proyectos"
TEMPLATE = ROOT / "src" / "index.html"

MAX_SIDE = 1600
COVER_WIDTH = 800  # versión pequeña de la portada (build.py la usa en el srcset si existe)
QUALITY = 80
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"} | ({".heic", ".heif"} if HEIC else set())
SRGB = ImageCms.createProfile("sRGB")


def natural_key(path):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name)]


def to_web(src, dest, width=None):
    """Guarda src como JPEG para la web: como mucho MAX_SIDE px de lado, o width px de ancho."""
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        icc = im.info.get("icc_profile")
        if im.mode not in ("RGB", "L"):
            background = Image.new("RGB", im.size, (255, 255, 255))
            rgba = im.convert("RGBA")
            background.paste(rgba, mask=rgba.split()[-1])
            im = background
        if icc:
            try:
                im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(icc)), SRGB, outputMode="RGB")
            except (ImageCms.PyCMSError, OSError):
                pass  # perfil ilegible: se deja el color tal cual
        im = im.convert("RGB")
        if width:
            if im.width <= width:
                return None
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        else:
            im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
        # sin exif= ni icc_profile=: el JPEG resultante no lleva metadatos (ni GPS, ni modelo de móvil…)
        im.save(dest, "JPEG", quality=QUALITY, optimize=True, progressive=True)
        return im.size


def set_gallery(html, slug, paths):
    pattern = re.compile(rf'(<article\b[^>]*\bdata-project="{re.escape(slug)}"[^>]*\bdata-gallery=")[^"]*(")')
    new, count = pattern.subn(lambda m: m.group(1) + ", ".join(paths) + m.group(2), html)
    return new, count == 1


def main():
    if not SOURCE.is_dir():
        sys.exit(f"No existe la carpeta {SOURCE.relative_to(ROOT)}/: crea una subcarpeta por proyecto y pon dentro las fotos.")
    html = TEMPLATE.read_text(encoding="utf-8")
    projects = re.findall(r'data-project="([^"]+)"', html)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    done = 0

    for folder in sorted(p for p in SOURCE.iterdir() if p.is_dir()):
        slug = folder.name
        if slug not in projects:
            print(f"  ¿{slug}? No hay ningún proyecto con ese nombre (válidos: {', '.join(projects)}). Se omite.")
            continue
        originals = sorted((p for p in folder.iterdir() if p.suffix.lower() in EXTENSIONS), key=natural_key)
        skipped = [p.name for p in folder.iterdir() if p.is_file() and p.suffix.lower() not in EXTENSIONS and not p.name.startswith(".")]
        if skipped:
            hint = " (para .heic: pip install pillow-heif)" if any(n.lower().endswith((".heic", ".heif")) for n in skipped) else ""
            print(f"  {slug}: se omiten {', '.join(skipped)}{hint}")
        if not originals:
            print(f"  {slug}: la carpeta no tiene fotos, no se cambia nada.")
            continue

        for old in OUTPUT.glob(f"{slug}-*.jpg"):
            if re.fullmatch(rf"{re.escape(slug)}-\d+(-{COVER_WIDTH})?\.jpg", old.name):
                old.unlink()
        paths = []
        for n, src in enumerate(originals, 1):
            dest = OUTPUT / f"{slug}-{n}.jpg"
            w, h = to_web(src, dest)
            paths.append(dest.relative_to(ROOT).as_posix())
            print(f"  {slug}: {src.name} → {dest.name} ({w}×{h}, {dest.stat().st_size // 1024} KB)")
        small = OUTPUT / f"{slug}-1-{COVER_WIDTH}.jpg"
        if to_web(originals[0], small, width=COVER_WIDTH):
            print(f"  {slug}: portada pequeña → {small.name} ({small.stat().st_size // 1024} KB)")
        html, ok = set_gallery(html, slug, paths)
        if not ok:
            sys.exit(f"No encuentro el data-gallery del proyecto {slug} en src/index.html")
        done += 1

    TEMPLATE.write_text(html, encoding="utf-8")
    print(f"Proyectos con fotos actualizados: {done}. Ahora ejecuta: python3 tools/build.py")


if __name__ == "__main__":
    main()
