"""Minimal message catalog for UI strings. English is the default locale."""

import json
from functools import cache
from pathlib import Path

LOCALES_DIR = Path(__file__).parent / "locales"
DEFAULT_LOCALE = "en"


@cache
def catalog(locale: str = DEFAULT_LOCALE) -> dict[str, str]:
    """Load the messages of ``locale``, falling back to English for missing keys."""
    messages: dict[str, str] = json.loads((LOCALES_DIR / "en.json").read_text("utf-8"))
    path = LOCALES_DIR / f"{locale}.json"
    if locale != DEFAULT_LOCALE and path.is_file():
        messages.update(json.loads(path.read_text("utf-8")))
    return messages


def translate(key: str, locale: str = DEFAULT_LOCALE, **params: object) -> str:
    """Return the message for ``key`` with ``{placeholders}`` filled in; unknown keys echo."""
    message = catalog(locale).get(key, key)
    return message.format(**params) if params else message
