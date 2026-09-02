"""Cierra una hoja: HTML+PDF a finals/, quita el flag wip y actualiza el catálogo."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mchs.catalogo import write_html
from mchs.pdf import page_count

HEROES_DIR = ROOT / "data" / "heroes"
DIST = ROOT / "dist"
FINALS_HTML = ROOT / "finals" / "heroes" / "html"
FINALS_PDF = ROOT / "finals" / "heroes" / "pdf"


def close_hero(slug: str) -> None:
    json_path = HEROES_DIR / f"{slug}.json"
    if not json_path.exists():
        raise SystemExit(f"No existe {json_path}")

    result = subprocess.run(
        [sys.executable, str(ROOT / "build.py"), slug, "--pdf"],
        cwd=ROOT,
        check=False,
    )
    if result.returncode not in (0, 2):
        raise SystemExit(result.returncode)

    html = DIST / f"{slug}.html"
    pdf = DIST / f"{slug}.pdf"
    FINALS_HTML.mkdir(parents=True, exist_ok=True)
    FINALS_PDF.mkdir(parents=True, exist_ok=True)
    shutil.copy2(html, FINALS_HTML / html.name)
    shutil.copy2(pdf, FINALS_PDF / pdf.name)
    html.unlink(missing_ok=True)
    pdf.unlink(missing_ok=True)

    data = json.loads(json_path.read_text(encoding="utf-8"))
    data.pop("wip", None)
    if data.get("hide") == [
        "fortalezas",
        "debilidades",
        "aspectos",
        "basicas",
        "mazos",
        "consideraciones",
        "mulligan",
    ]:
        data.pop("hide", None)
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    pages = page_count(FINALS_PDF / pdf.name)
    write_html()
    print(f"OK  finals/heroes/html/{slug}.html")
    print(f"OK  finals/heroes/pdf/{slug}.pdf ({pages} páginas)")
    print("OK  docs/catalogo.html")


def main(argv: list[str] | None = None) -> int:
    if not argv:
        argv = sys.argv[1:]
    if len(argv) != 1:
        print("Uso: python tools/close_hero.py <slug>", file=sys.stderr)
        return 2
    close_hero(argv[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
