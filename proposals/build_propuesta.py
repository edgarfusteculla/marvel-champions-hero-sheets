"""Genera una hoja de propuesta, sin tocar la plantilla oficial.

    python proposals/build_propuesta.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mchs.heroes import ASPECT_LABELS, load_hero
from mchs.marvelcdb import MarvelCDB, image_url
from mchs.render import TYPE_LABELS, build_context, make_environment

BASICS = [
    {
        "code": "29027",
        "note": "Peter es Genio: la juegas en alter ego y genera un comodín cada ronda.",
    },
    {
        "code": "01092",
        "note": "Un recurso extra cada turno. Encaja con su curva barata.",
    },
    {
        "code": "01091",
        "note": "Robo estable los turnos que pasas a Peter a curarte.",
    },
]

ASPECT_CARDS = [
    {
        "code": "01053",
        "aspect": "aggression",
        "note": "Daño extra cuando el Balanceo se queda corto contra esbirros.",
    },
    {
        "code": "01060",
        "aspect": "justice",
        "note": "Tapa de un golpe su Intervención 1.",
    },
    {
        "code": "01071",
        "aspect": "leadership",
        "note": "Saca aliados que se ocupen de la amenaza.",
    },
    {
        "code": "01077",
        "aspect": "protection",
        "note": "Con Defensa 3, devolver el golpe duele.",
    },
]


def enrich(entry: dict, client: MarvelCDB) -> dict:
    card = client.card(entry["code"])
    data = {
        "name": card["name"],
        "type_label": TYPE_LABELS.get(card["type_code"], card.get("type_name", "")),
        "image": image_url(card),
        "note": entry["note"],
    }
    if "aspect" in entry:
        data["aspect"] = entry["aspect"]
        data["aspect_label"] = ASPECT_LABELS[entry["aspect"]]
    return data


def main() -> int:
    client = MarvelCDB(ROOT / "cache", locale="es")
    env = make_environment(ROOT / "proposals")
    env.loader.searchpath.append(str(ROOT / "templates"))

    hero = load_hero(ROOT / "data" / "heroes" / "spider-man.json")
    context = build_context(hero, client)
    context["recommended_basics"] = [enrich(item, client) for item in BASICS]
    context["recommended_aspects"] = [enrich(item, client) for item in ASPECT_CARDS]

    html = env.get_template("hero_sheet_propuesta.html.j2").render(**context)
    output = ROOT / "dist" / "propuesta-spider-man.html"
    output.write_text(html, encoding="utf-8")
    print(f"OK  {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
