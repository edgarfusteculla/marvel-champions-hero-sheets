"""Carga y validación de los archivos editoriales de héroe (data/heroes/*.json)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ASPECTS = ("aggression", "justice", "leadership", "protection")

ASPECT_LABELS = {
    "aggression": "Agresión",
    "justice": "Justicia",
    "leadership": "Liderazgo",
    "protection": "Protección",
}

REQUIRED_FIELDS = ("slug", "hero_card_code", "difficulty", "power")

LEVELS = ("principiante", "intermedio", "avanzado")

SIDES = ("a", "b")

TONES = ("consejo", "aviso", "neutro")

# Apartados que se pueden quitar de una hoja con "hide", para dejar solo lo que interese.
HIDEABLE = (
    "fuertes-debiles",
    "aspectos",
    "circunstanciales",
    "consejos",
    "curva",
    "mulligan",
)


class HeroDataError(ValueError):
    pass


def _check_rating(value: Any, field: str, slug: str) -> int:
    if not isinstance(value, int) or not 1 <= value <= 5:
        raise HeroDataError(f"[{slug}] '{field}' debe ser un entero de 1 a 5, y es {value!r}.")
    return value


def _validate(data: dict[str, Any]) -> dict[str, Any]:
    slug = data.get("slug", "?")
    for field in REQUIRED_FIELDS:
        if not data.get(field):
            raise HeroDataError(f"[{slug}] falta el campo obligatorio '{field}'.")

    _check_rating(data["difficulty"], "difficulty", slug)
    _check_rating(data["power"], "power", slug)

    aspects = data.get("aspects", {})
    for aspect in ASPECTS:
        if aspect not in aspects:
            raise HeroDataError(
                f"[{slug}] falta la valoración del aspecto '{aspect}'. "
                f"Se esperan los cuatro: {', '.join(ASPECTS)}."
            )
        _check_rating(aspects[aspect].get("rating"), f"aspects.{aspect}.rating", slug)

    seen: set[str] = set()
    for card in data.get("cards", []):
        code = card.get("code")
        if not code:
            raise HeroDataError(f"[{slug}] hay una entrada en 'cards' sin 'code'.")
        if code in seen:
            raise HeroDataError(f"[{slug}] la carta '{code}' aparece dos veces en 'cards'.")
        seen.add(code)
        _check_rating(card.get("priority"), f"cards[{code}].priority", slug)

    level = data.get("level")
    if level is not None and level not in LEVELS:
        raise HeroDataError(
            f"[{slug}] 'level' debe ser uno de {', '.join(LEVELS)}, y es {level!r}."
        )

    unknown = set(data.get("hide", [])) - set(HIDEABLE)
    if unknown:
        raise HeroDataError(
            f"[{slug}] 'hide' contiene apartados que no existen: {', '.join(sorted(unknown))}. "
            f"Se pueden ocultar: {', '.join(HIDEABLE)}."
        )

    for index, section in enumerate(data.get("sections", [])):
        where = f"sections[{index}]"
        if not section.get("title"):
            raise HeroDataError(f"[{slug}] {where} necesita un 'title'.")
        if section.get("side") not in SIDES:
            raise HeroDataError(
                f"[{slug}] {where}.side debe ser 'a' o 'b', y es {section.get('side')!r}."
            )
        if not section.get("items"):
            raise HeroDataError(f"[{slug}] {where} no tiene ninguna nota en 'items'.")
        tone = section.get("tone", "consejo")
        if tone not in TONES:
            raise HeroDataError(
                f"[{slug}] {where}.tone debe ser uno de {', '.join(TONES)}, y es {tone!r}."
            )

    return data


def apply_variant(data: dict[str, Any], name: str) -> dict[str, Any]:
    """Devuelve el héroe con la variante aplicada encima.

    La variante sustituye por completo las claves que declara, así que en ella solo hace falta
    escribir lo que cambia respecto a la hoja base.
    """
    variants = data.get("variants", {})
    if name not in variants:
        raise HeroDataError(
            f"[{data['slug']}] no tiene la variante '{name}'. "
            f"Definidas: {', '.join(variants) or 'ninguna'}."
        )
    merged = {key: value for key, value in data.items() if key != "variants"}
    merged.update(variants[name])
    merged["slug"] = f"{data['slug']}-{name}"
    merged["variant"] = name
    return _validate(merged)


def load_hero(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise HeroDataError(f"{path.name} no es un JSON válido: {error}") from error

    data.setdefault("slug", path.stem)
    return _validate(data)


def load_all(directory: Path, slugs: list[str] | None = None) -> list[dict[str, Any]]:
    files = sorted(directory.glob("*.json"))
    if slugs:
        wanted = set(slugs)
        files = [f for f in files if f.stem in wanted]
        missing = wanted - {f.stem for f in files}
        if missing:
            raise HeroDataError(
                f"No encuentro datos para: {', '.join(sorted(missing))} en {directory}."
            )
    if not files:
        raise HeroDataError(f"No hay ningún archivo de héroe en {directory}.")
    return [load_hero(f) for f in files]
