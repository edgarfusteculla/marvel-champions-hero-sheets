"""Genera las hojas de héroe en HTML listas para imprimir.

Ejemplos:
    python build.py                     # todos los héroes
    python build.py spider-man          # solo uno
    python build.py --refresh           # ignora la caché y vuelve a bajar los datos
    python build.py spider-man --open   # genera y abre en el navegador
    python build.py --pdf               # genera además el PDF listo para imprimir
"""

from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

from mchs.heroes import HeroDataError, load_all
from mchs.marvelcdb import MarvelCDB, MarvelCDBError
from mchs.pdf import PdfExportError, export as export_pdf
from mchs.render import make_environment, render_hero

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "heroes"
TEMPLATES_DIR = ROOT / "templates"
CACHE_DIR = ROOT / "cache"
DIST_DIR = ROOT / "dist"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slugs", nargs="*", help="Héroes a generar (por nombre de archivo, sin .json).")
    parser.add_argument("--refresh", action="store_true", help="Vuelve a descargar los datos de MarvelCDB.")
    parser.add_argument("--locale", default="es", choices=["es", "en"], help="Idioma de los textos de carta.")
    parser.add_argument("--pdf", action="store_true", help="Genera también el PDF (necesita Edge o Chrome).")
    parser.add_argument("--open", action="store_true", help="Abre las hojas generadas en el navegador.")
    args = parser.parse_args(argv)

    try:
        heroes = load_all(DATA_DIR, args.slugs or None)
    except HeroDataError as error:
        print(f"Error en los datos: {error}", file=sys.stderr)
        return 1

    client = MarvelCDB(CACHE_DIR, locale=args.locale, refresh=args.refresh)
    env = make_environment(TEMPLATES_DIR)
    DIST_DIR.mkdir(exist_ok=True)

    for hero in heroes:
        try:
            html = render_hero(hero, client, env)
        except (MarvelCDBError, ValueError) as error:
            print(f"Error generando '{hero['slug']}': {error}", file=sys.stderr)
            return 1

        output = DIST_DIR / f"{hero['slug']}.html"
        output.write_text(html, encoding="utf-8")
        print(f"OK  {output.relative_to(ROOT)}")

        if args.pdf:
            pdf_path = output.with_suffix(".pdf")
            try:
                export_pdf(output, pdf_path)
            except PdfExportError as error:
                print(f"Aviso: {error}", file=sys.stderr)
            else:
                print(f"OK  {pdf_path.relative_to(ROOT)}")

        if args.open:
            webbrowser.open(output.as_uri())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
