"""Regenera docs/catalogo.html a partir de data/catalogo.json y el estado del disco."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mchs.catalogo import annotated_catalog, write_html


def main() -> int:
    data = annotated_catalog()
    path = write_html()
    counts = data["counts"]
    print(f"OK  {path.relative_to(ROOT)}")
    print(
        "     "
        f"{counts['cerrado']} terminados · "
        f"{counts['wip']} trabajando · "
        f"{counts['pendiente']} pendientes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
