"""Básicas más usadas en mazos populares de Iron Man."""

from __future__ import annotations

import json
import re
import ssl
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

try:
    import truststore

    SSL_CTX = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
except ImportError:
    SSL_CTX = ssl.create_default_context()

HOST = "https://marvelcdb.com"
ES_HOST = "https://es.marvelcdb.com"
UA = {"User-Agent": "marvel-champions-hero-sheets (proyecto fan, sin animo de lucro)"}
PAGES = 5
CACHE = Path(__file__).resolve().parent.parent / "cache" / "mcdb-decks"
GENERIC_RESOURCES = {"01088", "01089", "01090"}
HERO = "01029a"


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers=UA)
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=45, context=SSL_CTX) as response:
                return response.read()
        except Exception as error:  # noqa: BLE001 — reintento de red
            last_error = error
            time.sleep(1.5 * (attempt + 1))
    raise last_error  # type: ignore[misc]


def cached_json(name: str, url: str) -> object:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{name}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    time.sleep(0.35)
    data = json.loads(fetch(url).decode("utf-8"))
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def is_basic(card: dict | None, hero_set: str | None) -> bool:
    if not card:
        return False
    if card.get("faction_code") != "basic":
        return False
    if hero_set and card.get("card_set_code") == hero_set:
        return False
    if card.get("type_code") in {"hero", "alter_ego", "obligation", "nemesis"}:
        return False
    return True


def main() -> None:
    cards = {
        card["code"]: card
        for card in cached_json("cards-es", f"{ES_HOST}/api/public/cards/")
    }
    hero_set = (cards.get(HERO) or {}).get("card_set_code")
    aliases = {HERO, HERO.rstrip("a")}

    print("Buscando mazos de Iron Man por likes...", flush=True)
    ids: list[str] = []
    seen: set[str] = set()
    for page in range(1, PAGES + 1):
        html = fetch(f"{HOST}/decklists/find/{page}?hero={HERO}&sort=likes").decode(
            "utf-8", "replace"
        )
        for deck_id in re.findall(r"/decklist/view/(\d+)", html):
            if deck_id not in seen:
                seen.add(deck_id)
                ids.append(deck_id)
    print(f"Listados: {len(ids)}", flush=True)

    decks = []
    for i, deck_id in enumerate(ids, start=1):
        try:
            payload = cached_json(
                f"deck-{deck_id}", f"{HOST}/api/public/decklist/{deck_id}.json"
            )
        except Exception as error:  # noqa: BLE001
            print(f"aviso: no se pudo bajar el mazo {deck_id}: {error}", flush=True)
            continue
        if payload.get("hero_code") in aliases:
            decks.append(payload)
        if i % 10 == 0:
            print(f"  {i}/{len(ids)} mazos...", flush=True)
    print(f"Del héroe: {len(decks)}", flush=True)

    present = Counter()
    copies = Counter()
    for deck in decks:
        seen_in_deck = set()
        for code, qty in (deck.get("slots") or {}).items():
            card = cards.get(code)
            if not is_basic(card, hero_set):
                continue
            if code not in seen_in_deck:
                present[code] += 1
                seen_in_deck.add(code)
            copies[code] += int(qty or 0)

    n = len(decks)
    print(f"{'% mazos':>8}  {'copias/mazo':>11}  código   carta")
    print("-" * 72)
    top = []
    for code, count in present.most_common(20):
        card = cards[code]
        pct = 100 * count / n
        avg = copies[code] / n
        flag = "  *" if code in GENERIC_RESOURCES else ""
        print(
            f"{pct:7.0f}%  {avg:11.2f}  {code}   "
            f"{card.get('name')} ({card.get('type_name')}){flag}"
        )
        if code not in GENERIC_RESOURCES:
            top.append(code)

    recent = [d for d in decks if (d.get("date_creation") or "")[:4] >= "2022"]
    if recent:
        rn = len(recent)
        print(f"\nDesde 2022 (n={rn}):")
        for code in top[:10]:
            pct = 100 * sum(1 for d in recent if code in (d.get("slots") or {})) / rn
            print(f"  {pct:3.0f}%  {cards[code]['name']}")

    by_asp: dict[str, list] = defaultdict(list)
    for deck in decks:
        meta = deck.get("meta") or "{}"
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except json.JSONDecodeError:
                meta = {}
        by_asp[(meta or {}).get("aspect") or "?"].append(deck)
    print(
        "Aspectos: "
        + ", ".join(f"{k}={len(v)}" for k, v in sorted(by_asp.items(), key=lambda i: -len(i[1])))
    )
    print("\n* = recurso genérico de 1. En la hoja ahora: Inventiva 29027.")


if __name__ == "__main__":
    main()
