"""Básicas en mazos de MarvelCDB de los últimos 2 años."""

from __future__ import annotations

import json
import re
import ssl
import time
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    import truststore

    SSL_CTX = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
except ImportError:
    SSL_CTX = ssl.create_default_context()

HOST = "https://marvelcdb.com"
ES_HOST = "https://es.marvelcdb.com"
UA = {"User-Agent": "marvel-champions-hero-sheets (proyecto fan, sin animo de lucro)"}
CACHE = Path(__file__).resolve().parent.parent / "cache" / "mcdb-decks"
GENERIC_RESOURCES = {"01088", "01089", "01090"}
CUTOFF = datetime(2024, 8, 26, tzinfo=timezone.utc)
MAX_PAGES = 20

HEROES = {
    "spider-man": "01001a",
    "hulka": "01019a",
    "capitana-marvel": "01010a",
}


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=30, context=SSL_CTX) as response:
        return response.read()


def cached_json(name: str, url: str) -> object:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{name}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    time.sleep(0.12)
    data = json.loads(fetch(url).decode("utf-8"))
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def card_index() -> dict[str, dict]:
    cards = cached_json("cards-es", f"{ES_HOST}/api/public/cards/")
    return {card["code"]: card for card in cards}


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


def parse_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def recent_decks(hero_code: str) -> list[dict]:
    aliases = {hero_code, hero_code.rstrip("a")}
    decks: list[dict] = []
    seen: set[str] = set()
    done = False
    for page in range(1, MAX_PAGES + 1):
        html = fetch(
            f"{HOST}/decklists/find/{page}?hero={hero_code}&sort=date"
        ).decode("utf-8", "replace")
        ids = re.findall(r"/decklist/view/(\d+)", html)
        if not ids:
            break
        page_oldest = None
        for deck_id in ids:
            if deck_id in seen:
                continue
            seen.add(deck_id)
            payload = cached_json(
                f"deck-{deck_id}", f"{HOST}/api/public/decklist/{deck_id}.json"
            )
            if payload.get("hero_code") not in aliases:
                continue
            created = parse_date(payload.get("date_creation"))
            if created is None:
                continue
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if page_oldest is None or created < page_oldest:
                page_oldest = created
            if created >= CUTOFF:
                decks.append(payload)
        if page_oldest is not None and page_oldest < CUTOFF:
            done = True
            break
        print(f"  página {page}: {len(decks)} mazos recientes acumulados", flush=True)
    if not done:
        print(f"  aviso: se cortó en {MAX_PAGES} páginas")
    return decks


def analyze(slug: str, hero_code: str, cards: dict[str, dict]) -> None:
    print(f"=== {slug} ({hero_code}) ===", flush=True)
    decks = recent_decks(hero_code)
    print(f"Mazos desde {CUTOFF.date()}: {len(decks)}", flush=True)
    if not decks:
        print()
        return

    hero_set = (cards.get(hero_code) or {}).get("card_set_code")
    present = Counter()
    copies = Counter()
    by_asp: dict[str, list] = defaultdict(list)
    for deck in decks:
        meta = deck.get("meta") or "{}"
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except json.JSONDecodeError:
                meta = {}
        by_asp[(meta or {}).get("aspect") or "?"].append(deck)
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
    shown = 0
    for code, count in present.most_common():
        if code in GENERIC_RESOURCES:
            continue
        card = cards[code]
        pct = 100 * count / n
        avg = copies[code] / n
        print(
            f"{pct:7.0f}%  {avg:11.2f}  {code}   "
            f"{card.get('name')} ({card.get('type_name')})"
        )
        shown += 1
        if shown >= 12:
            break

    print(
        "Aspectos: "
        + ", ".join(
            f"{k}={len(v)}" for k, v in sorted(by_asp.items(), key=lambda i: -len(i[1]))
        )
    )
    print()


def main() -> None:
    cards = card_index()
    print(f"Corte: mazos publicados desde {CUTOFF.date()} (últimos 2 años)\n", flush=True)
    for slug, code in HEROES.items():
        analyze(slug, code, cards)


if __name__ == "__main__":
    main()
