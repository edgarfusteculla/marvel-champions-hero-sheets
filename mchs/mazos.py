"""Catálogo de mazos de aspecto reutilizables (data/mazos/*.json)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .heroes import ASPECTS, HeroDataError, parse_mazo_ref

REQUIRED_FIELDS = ("slug", "name", "aspect", "face_card")

MAZOS_DIR = Path(__file__).resolve().parent.parent / "data" / "mazos"


def _validate(data: dict[str, Any], source: str) -> dict[str, Any]:
    slug = data.get("slug") or Path(source).stem
    for field in REQUIRED_FIELDS:
        if not data.get(field):
            raise HeroDataError(f"[{source}] falta el campo obligatorio '{field}'.")
    if data["aspect"] not in ASPECTS:
        raise HeroDataError(
            f"[{slug}] 'aspect' debe ser uno de {', '.join(ASPECTS)}, "
            f"y es {data['aspect']!r}."
        )
    if data.get("face_image"):
        art = Path(__file__).resolve().parent.parent / "data" / "art" / data["face_image"]
        if not art.exists():
            raise HeroDataError(f"[{slug}] no encuentro data/art/{data['face_image']}.")
    return data


def load_mazo(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise HeroDataError(f"{path.name} no es un JSON válido: {error}") from error
    data.setdefault("slug", path.stem)
    return _validate(data, path.name)


def load_catalog(directory: Path | None = None) -> dict[str, dict[str, Any]]:
    folder = directory or MAZOS_DIR
    if not folder.exists():
        return {}
    catalog: dict[str, dict[str, Any]] = {}
    for path in sorted(folder.glob("*.json")):
        mazo = load_mazo(path)
        slug = mazo["slug"]
        if slug in catalog:
            raise HeroDataError(f"El mazo '{slug}' está definido dos veces.")
        catalog[slug] = mazo
    return catalog


def resolve_hero_mazos(
    hero: dict[str, Any], catalog: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    slug = hero.get("slug", "?")
    resolved = []
    for index, entry in enumerate(hero.get("mazos", [])):
        ref = parse_mazo_ref(entry, slug, index)
        mazo = catalog.get(ref["slug"])
        if mazo is None:
            known = ", ".join(sorted(catalog)) or "ninguno"
            raise HeroDataError(
                f"[{slug}] no existe el mazo '{ref['slug']}'. Definidos: {known}."
            )
        resolved.append({**mazo, "note": ref["note"]})
    return resolved
