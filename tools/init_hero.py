"""Crea la plantilla inicial de un héroe (JSON + notas) sin inventar criterio."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mchs.catalogo import find_hero, write_html
from mchs.heroes import ASPECTS
from mchs.marvelcdb import MarvelCDB
from mchs.render import NON_DECK_TYPES

HEROES_DIR = ROOT / "data" / "heroes"
NOTES_DIR = ROOT / "notas"

WIP_HIDE = [
    "fortalezas",
    "debilidades",
    "aspectos",
    "basicas",
    "mazos",
    "consideraciones",
    "mulligan",
]


def init_hero(slug: str, code: str | None = None, *, force: bool = False) -> Path:
    listed = find_hero(slug)
    hero_code = code or (listed or {}).get("code")
    if not hero_code:
        raise SystemExit(
            f"No tengo código MarvelCDB para '{slug}'. Pásalo o añádelo a data/catalogo.json."
        )

    json_path = HEROES_DIR / f"{slug}.json"
    if json_path.exists() and not force:
        raise SystemExit(f"Ya existe {json_path}. Usa --force para sobrescribir una plantilla.")

    client = MarvelCDB(ROOT / "cache", locale="es")
    hero_card, kit = client.hero_kit(hero_code)
    linked = hero_card.get("linked_to_code")
    alter = client.card(linked) if linked else {}

    display = (listed or {}).get("name") or hero_card.get("name")
    alter_name = alter.get("name") or ""

    cards = []
    for card in sorted(kit.values(), key=lambda item: item["code"]):
        if card.get("type_code") in NON_DECK_TYPES:
            continue
        cards.append({"code": card["code"], "priority": 3, "note": ""})

    data = {
        "slug": slug,
        "hero_card_code": hero_code,
        "display_name": display,
        "alter_ego_name": alter_name,
        "wip": True,
        "difficulty": 3,
        "power": 3,
        "strengths": [],
        "weaknesses": [],
        "aspects": {aspect: {"solo": 3, "duo": 3, "grupo": 3} for aspect in ASPECTS},
        "cards": cards,
        "basics": [],
        "mazos": [],
        "consideraciones": [],
        "mulligan": {"keep": [], "toss": []},
        "hide": WIP_HIDE,
    }
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    notes_path = NOTES_DIR / f"{slug}.md"
    if not notes_path.exists() or force:
        notes_path.write_text(
            f"# {display}" + (f" ({alter_name})" if alter_name else "") + "\n\n"
            "Plantilla inicial. Rellena esto y luego `data/heroes/" + slug + ".json`.\n"
            "No pongas valoraciones ni consejos inventados: solo lo que hayas jugado.\n\n"
            "## Aspectos (solo / 2 / 3-4)\n\n"
            "- Agresividad\n- Justicia\n- Liderazgo\n- Protección\n\n"
            "Dificultad ?, potencia ?.\n\n"
            "## Fortalezas\n\n-\n\n"
            "## Debilidades\n\n-\n\n"
            "## Cartas básicas indispensables\n\n-\n\n"
            "## Mazos recomendados\n\n-\n\n"
            "## Consideraciones\n\n-\n\n"
            "## Mulligan\n\n"
            "Buscar:\n-\n\n"
            "Cambia:\n-\n",
            encoding="utf-8",
        )

    write_html()
    return json_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", help="Nombre de archivo, sin .json.")
    parser.add_argument("code", nargs="?", help="Código MarvelCDB de la carta de héroe (01001a).")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    path = init_hero(args.slug, args.code, force=args.force)
    print(f"OK  {path.relative_to(ROOT)}")
    print("OK  docs/catalogo.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
