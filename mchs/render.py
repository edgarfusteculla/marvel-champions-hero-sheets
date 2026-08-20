"""Combina los datos editoriales con los de MarvelCDB y renderiza la hoja de héroe."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markupsafe import Markup

from .heroes import ASPECTS, ASPECT_LABELS
from .marvelcdb import Card, MarvelCDB, image_url

# Tipos que no se juegan desde la mano y por tanto no cuentan en la curva de coste.
NON_DECK_TYPES = {"hero", "alter_ego", "obligation"}

# Cartas que se muestran a tamaño grande en la cara B; el resto va en la lista compacta.
KEY_CARD_COUNT = 4

TYPE_LABELS = {
    "ally": "Aliado",
    "event": "Evento",
    "resource": "Recurso",
    "support": "Apoyo",
    "upgrade": "Mejora",
    "obligation": "Obligación",
}

RESOURCE_LABELS = {
    "physical": "FÍS",
    "energy": "ENE",
    "mental": "MEN",
    "wild": "COM",
    "per_hero": "/héroe",
    "star": "★",
}

DEFAULT_PALETTE = ["#8a1a2c", "#1f2f6b", "#111111", "#f7f3ea"]

ICON_PATTERN = re.compile(r'<span class="icon-([a-z_]+)"[^>]*></span>')

# Según la carta, MarvelCDB devuelve los iconos como <span> o como marcador [mental].
TOKEN_PATTERN = re.compile(r"\[([a-z_]+)\]")
PARAGRAPH_PATTERN = re.compile(r"</p>\s*<p>")
STRIP_PATTERN = re.compile(r"</?p>")


def format_card_text(raw: str | None) -> Markup:
    """Convierte el HTML de MarvelCDB en HTML propio, con los iconos como etiquetas legibles."""
    if not raw:
        return Markup("")

    def replace_icon(match: re.Match[str]) -> str:
        key = match.group(1)
        label = RESOURCE_LABELS.get(key, key.replace("_", " ").upper())
        return f'<span class="res res-{key}">{label}</span>'

    text = ICON_PATTERN.sub(replace_icon, raw)
    text = TOKEN_PATTERN.sub(replace_icon, text)
    text = PARAGRAPH_PATTERN.sub("<br>", text)
    text = STRIP_PATTERN.sub("", text)
    return Markup(text.replace("\n", "<br>"))


def _luminance(hex_color: str) -> float:
    value = hex_color.lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    r, g, b = (int(value[i : i + 2], 16) / 255 for i in (0, 2, 4))
    channels = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ink(hex_color: str) -> str:
    return "#111111" if _luminance(hex_color) > 0.45 else "#ffffff"


def build_palette(hero_card: Card, overrides: dict[str, str] | None) -> dict[str, str]:
    colors = (hero_card.get("meta") or {}).get("colors") or []
    colors = [c for c in colors if isinstance(c, str) and c.startswith("#")]
    colors = (colors + DEFAULT_PALETTE)[:4]
    palette = {
        "primary": colors[0],
        "secondary": colors[1],
        "dark": colors[2],
        "light": colors[3],
    }
    palette.update(overrides or {})
    palette["on_primary"] = contrast_ink(palette["primary"])
    palette["on_secondary"] = contrast_ink(palette["secondary"])
    return palette


def _merge_cards(editorial: list[dict[str, Any]], kit: dict[str, Card]) -> list[dict[str, Any]]:
    merged = []
    for entry in editorial:
        card = kit.get(entry["code"])
        if card is None:
            raise ValueError(
                f"La carta {entry['code']} no está en el set de firma de este héroe. "
                f"Códigos disponibles: {', '.join(sorted(kit))}"
            )
        merged.append(
            {
                "code": card["code"],
                "name": card["name"],
                "type_code": card["type_code"],
                "type_label": TYPE_LABELS.get(card["type_code"], card.get("type_name", "")),
                "cost": card.get("cost"),
                "quantity": card.get("quantity", 1),
                "traits": card.get("traits") or "",
                "text": format_card_text(card.get("text") or card.get("real_text")),
                "image": image_url(card),
                "priority": entry["priority"],
                "note": entry.get("note", ""),
                "mulligan": entry.get("mulligan"),
            }
        )
    return merged


def _cost_curve(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets = {label: 0 for label in ("0", "1", "2", "3", "4+")}
    for card in cards:
        if card["type_code"] in NON_DECK_TYPES or card["cost"] is None:
            continue
        label = str(card["cost"]) if card["cost"] < 4 else "4+"
        buckets[label] += card["quantity"]
    peak = max(buckets.values()) or 1
    return [
        {"label": label, "count": count, "height": round(100 * count / peak)}
        for label, count in buckets.items()
    ]


def build_context(hero_data: dict[str, Any], client: MarvelCDB) -> dict[str, Any]:
    hero_card, kit = client.hero_kit(hero_data["hero_card_code"])

    # El objeto 'linked_card' que viene incrustado no está traducido, hay que pedirlo aparte.
    linked_code = hero_card.get("linked_to_code")
    alter_ego = client.card(linked_code) if linked_code else (hero_card.get("linked_card") or {})

    cards = _merge_cards(hero_data.get("cards", []), kit)
    playable = [c for c in cards if c["type_code"] not in NON_DECK_TYPES]
    playable.sort(key=lambda c: (-c["priority"], c["cost"] if c["cost"] is not None else 99))
    obligations = [c for c in cards if c["type_code"] == "obligation"]

    ratings = hero_data["aspects"]
    best = max(ratings[a]["rating"] for a in ASPECTS)
    aspects = sorted(
        (
            {
                "key": key,
                "label": ASPECT_LABELS[key],
                "rating": ratings[key]["rating"],
                "note": ratings[key].get("note", ""),
                "recommended": ratings[key]["rating"] == best,
            }
            for key in ASPECTS
        ),
        key=lambda a: -a["rating"],
    )

    return {
        "hero": hero_data,
        "palette": build_palette(hero_card, hero_data.get("palette")),
        "hero_card": {
            "name": hero_data.get("display_name") or hero_card["name"],
            "image": image_url(hero_card),
            "text": format_card_text(hero_card.get("text") or hero_card.get("real_text")),
            "traits": hero_card.get("traits") or "",
            "attack": hero_card.get("attack"),
            "thwart": hero_card.get("thwart"),
            "defense": hero_card.get("defense"),
            "health": hero_card.get("health"),
            "hand_size": hero_card.get("hand_size"),
        },
        "alter_ego": {
            "name": hero_data.get("alter_ego_name") or alter_ego.get("name", ""),
            "image": image_url(alter_ego) if alter_ego else None,
            "text": format_card_text(alter_ego.get("text") or alter_ego.get("real_text")),
            "recover": alter_ego.get("recover"),
            "hand_size": alter_ego.get("hand_size"),
        },
        "aspects": aspects,
        "hide": set(hero_data.get("hide", [])),
        "sections_a": [s for s in hero_data.get("sections", []) if s["side"] == "a"],
        "sections_b": [s for s in hero_data.get("sections", []) if s["side"] == "b"],
        "key_cards": playable[:KEY_CARD_COUNT],
        "other_cards": playable[KEY_CARD_COUNT:],
        "obligations": obligations,
        "curve": _cost_curve(cards),
        "deck_size": sum(c["quantity"] for c in cards if c["type_code"] not in NON_DECK_TYPES),
        "pack_name": hero_card.get("pack_name", ""),
    }


def make_environment(templates_dir: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["contrast_ink"] = contrast_ink
    return env


def render_hero(hero_data: dict[str, Any], client: MarvelCDB, env: Environment) -> str:
    template = env.get_template("hero_sheet.html.j2")
    return template.render(**build_context(hero_data, client))
