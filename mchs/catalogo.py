"""Catálogo de héroes: estado inferido del disco y HTML para consultar."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "data" / "catalogo.json"
HEROES_DIR = ROOT / "data" / "heroes"
FINALS_HTML = ROOT / "finals" / "heroes" / "html"
CATALOG_HTML = ROOT / "docs" / "catalogo.html"

STATUS_LABELS = {
    "cerrado": "Terminado",
    "wip": "Trabajando",
    "pendiente": "Pendiente",
}

COUNT_LABELS = {
    "cerrado": "terminados",
    "wip": "trabajando",
    "pendiente": "pendientes",
}


def load_catalog() -> dict[str, Any]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def infer_status(slug: str, code: str | None) -> str | None:
    if not code:
        return None
    if (FINALS_HTML / f"{slug}.html").exists():
        return "cerrado"
    if (HEROES_DIR / f"{slug}.json").exists():
        return "wip"
    return "pendiente"


def annotated_catalog() -> dict[str, Any]:
    data = load_catalog()
    counts = {key: 0 for key in STATUS_LABELS}
    groups = []
    for group in data["groups"]:
        heroes = []
        for hero in group["heroes"]:
            status = infer_status(hero["slug"], hero.get("code"))
            if status is None:
                continue
            hero = {**hero, "status": status}
            heroes.append(hero)
            counts[status] += 1
        if heroes:
            groups.append({**group, "heroes": heroes})
    data["groups"] = groups
    data["counts"] = counts
    return data


def render_html(data: dict[str, Any] | None = None) -> str:
    data = data or annotated_catalog()
    counts = data["counts"]
    cards = []
    for group in data["groups"]:
        items = []
        for hero in group["heroes"]:
            status = hero["status"]
            items.append(
                f'<li class="hero {status}">'
                f'<span class="name">{_esc(hero["name"])}</span>'
                f'<span class="pill">{STATUS_LABELS[status]}</span>'
                f"</li>"
            )
        cards.append(
            f'<section class="group kind-{group["kind"]}">'
            f"<h2>{_esc(group['name'])}</h2>"
            f"<ul>{''.join(items)}</ul>"
            f"</section>"
        )
    count_pills = "".join(
        f'<span class="{key}">{counts[key]} {COUNT_LABELS[key]}</span>'
        for key in STATUS_LABELS
    )
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Catálogo de héroes · Marvel Champions</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
  --ink: #141414;
  --paper: #f4efe4;
  --paper-light: #fbf8f1;
  --cerrado: #2f9455;
  --wip: #b8860b;
  --pendiente: #6b6560;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: #4a4a4a;
  color: var(--ink);
  font-family: Inter, sans-serif;
}}
.page {{
  max-width: 1100px;
  margin: 24px auto;
  background: var(--paper);
  padding: 28px 32px 40px;
  border-radius: 8px;
}}
h1 {{
  font-family: "Barlow Condensed", sans-serif;
  font-size: 42px;
  letter-spacing: .04em;
  text-transform: uppercase;
  margin: 0 0 18px;
}}
.counts {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 28px;
}}
.counts span {{
  font-family: "Barlow Condensed", sans-serif;
  text-transform: uppercase;
  letter-spacing: .06em;
  padding: 6px 12px;
  border-radius: 999px;
  color: #fff;
  font-weight: 700;
}}
.counts .cerrado {{ background: var(--cerrado); }}
.counts .wip {{ background: var(--wip); }}
.counts .pendiente {{ background: var(--pendiente); }}
.group {{
  margin-bottom: 22px;
}}
.group h2 {{
  font-family: "Barlow Condensed", sans-serif;
  text-transform: uppercase;
  letter-spacing: .08em;
  font-size: 18px;
  margin: 0 0 8px;
  padding-bottom: 4px;
  border-bottom: 2px solid #141414;
}}
.group ul {{
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 8px;
}}
.hero {{
  background: var(--paper-light);
  border: 1px solid #d7d0c3;
  border-left: 5px solid #bbb;
  border-radius: 6px;
  padding: 8px 10px 9px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}}
.hero .name {{ font-weight: 700; }}
.hero .pill {{
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .04em;
  text-transform: uppercase;
  white-space: nowrap;
}}
.hero.cerrado {{ border-left-color: var(--cerrado); }}
.hero.wip {{ border-left-color: var(--wip); }}
.hero.pendiente {{ border-left-color: var(--pendiente); }}
.hero.cerrado .pill {{ color: var(--cerrado); }}
.hero.wip .pill {{ color: var(--wip); }}
.hero.pendiente .pill {{ color: var(--pendiente); }}
</style>
</head>
<body>
<div class="page">
  <h1>Catálogo de héroes</h1>
  <div class="counts">
    {count_pills}
  </div>
  {''.join(cards)}
</div>
</body>
</html>
"""


def _esc(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_html(path: Path | None = None) -> Path:
    output = path or CATALOG_HTML
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(), encoding="utf-8")
    return output


def find_hero(slug: str) -> dict[str, Any] | None:
    for group in load_catalog()["groups"]:
        for hero in group["heroes"]:
            if hero["slug"] == slug:
                return {**hero, "group": group["id"], "group_name": group["name"]}
    return None
