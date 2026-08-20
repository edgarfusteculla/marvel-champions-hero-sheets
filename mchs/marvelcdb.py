"""Cliente de la API pública de MarvelCDB con caché en disco."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

LOCALE_HOSTS = {
    "es": "https://es.marvelcdb.com",
    "en": "https://marvelcdb.com",
}

# Las imágenes de carta solo existen en inglés, se sirven siempre desde el dominio principal.
IMAGE_HOST = "https://marvelcdb.com"

USER_AGENT = "marvel-champions-hero-sheets (proyecto fan, sin ánimo de lucro)"

Card = dict[str, Any]


class MarvelCDBError(RuntimeError):
    pass


def _ssl_context() -> ssl.SSLContext:
    """Valida con el almacén de certificados del sistema.

    En redes con proxy corporativo la CA que firma el tráfico está en el almacén de Windows
    pero no en el bundle que trae Python, y la verificación falla sin esto.
    """
    try:
        import truststore
    except ImportError:
        return ssl.create_default_context()
    return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


class MarvelCDB:
    def __init__(self, cache_dir: Path, locale: str = "es", refresh: bool = False) -> None:
        if locale not in LOCALE_HOSTS:
            raise MarvelCDBError(
                f"Idioma '{locale}' no soportado. Opciones: {', '.join(LOCALE_HOSTS)}"
            )
        self.locale = locale
        self.host = LOCALE_HOSTS[locale]
        self.cache_dir = cache_dir / locale
        self.refresh = refresh
        self._packs: dict[str, list[Card]] = {}
        self._ssl = _ssl_context()

    def _fetch(self, path: str, cache_name: str) -> Any:
        cache_file = self.cache_dir / f"{cache_name}.json"
        if cache_file.exists() and not self.refresh:
            return json.loads(cache_file.read_text(encoding="utf-8"))

        request = urllib.request.Request(self.host + path, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=30, context=self._ssl) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as error:
            if cache_file.exists():
                return json.loads(cache_file.read_text(encoding="utf-8"))
            raise MarvelCDBError(f"No se pudo descargar {self.host}{path}: {error}") from error

        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        return payload

    def card(self, code: str) -> Card:
        return self._fetch(f"/api/public/card/{code}.json", f"card-{code}")

    def pack(self, pack_code: str) -> list[Card]:
        if pack_code not in self._packs:
            self._packs[pack_code] = self._fetch(
                f"/api/public/cards/{pack_code}.json", f"pack-{pack_code}"
            )
        return self._packs[pack_code]

    def hero_kit(self, hero_card_code: str) -> tuple[Card, dict[str, Card]]:
        """Devuelve la carta de héroe y todas las cartas de su set de firma indexadas por código."""
        hero = self.card(hero_card_code)
        card_set = hero.get("card_set_code")
        if not card_set:
            raise MarvelCDBError(f"La carta {hero_card_code} no pertenece a ningún set de héroe.")
        kit = {
            card["code"]: card
            for card in self.pack(hero["pack_code"])
            if card.get("card_set_code") == card_set
        }
        return hero, kit


def image_url(card: Card) -> str | None:
    source = card.get("imagesrc")
    return IMAGE_HOST + source if source else None
