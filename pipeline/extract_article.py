"""
Volltext-Extraktion aus einer Artikel-URL.

Ohne `trafilatura`/`newspaper3k` (nicht installierbar in dieser Sandbox),
dafür mit einer simplen, aber robusten Heuristik auf Basis von
BeautifulSoup: Wir suchen den `<article>`-Tag bzw. das Element mit den
meisten <p>-Zeichen, entfernen Nav/Ads/Scripts und geben den reinen
Fließtext zurück.

Für Produktion später leicht durch `trafilatura.extract()` ersetzbar
(gleiche Funktionssignatur `extract_article_text(html) -> str`) – das ist
qualitativ meist noch etwas besser, sobald PyPI erreichbar ist.
"""

from __future__ import annotations

import re
import sys

import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (compatible; DeeplíticsBot/0.1; "
    "+https://example.org/deeplitics-bot) Python-requests"
)

NOISE_TAGS = [
    "script", "style", "nav", "footer", "header", "aside", "form",
    "iframe", "noscript", "svg", "button",
]


def extract_article_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(NOISE_TAGS):
        tag.decompose()

    # Kandidaten: <article>, sonst Element mit meistem <p>-Text
    candidates = soup.find_all("article")
    if not candidates:
        candidates = soup.find_all(["div", "section", "main"])

    best_text = ""
    best_len = 0
    for c in candidates:
        paragraphs = [p.get_text(" ", strip=True) for p in c.find_all("p")]
        text = "\n".join(p for p in paragraphs if len(p) > 40)
        if len(text) > best_len:
            best_text, best_len = text, len(text)

    if not best_text:
        # Fallback: alle <p> im ganzen Dokument
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        best_text = "\n".join(p for p in paragraphs if len(p) > 40)

    best_text = re.sub(r"\n{3,}", "\n\n", best_text).strip()
    return best_text


def extract_og_image(html: str) -> str | None:
    """Liest das og:image (Fallback: twitter:image) aus dem HTML-Head.

    Das ist das Vorschaubild, das die Publikation selbst hinterlegt hat,
    damit Facebook/Twitter/Slack/etc. eine Bildvorschau beim Teilen des
    Links zeigen. Frei verfuegbar und genau fuer diesen Zweck gedacht,
    also der pragmatischste Weg zu einem Hero-Bild pro Artikel, ohne eine
    eigene Bildersuche pro Story zu brauchen.
    """
    soup = BeautifulSoup(html, "lxml")
    for prop in ("og:image", "og:image:secure_url", "twitter:image"):
        tag = soup.find("meta", attrs={"property": prop}) or soup.find(
            "meta", attrs={"name": prop}
        )
        if tag and tag.get("content"):
            return tag["content"].strip()
    return None


def fetch_and_extract(url: str, timeout: int = 10) -> str:
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] could not fetch {url}: {exc}", file=sys.stderr)
        return ""
    return extract_article_text(resp.text)


def fetch_and_extract_with_image(url: str, timeout: int = 10) -> tuple[str, str | None]:
    """Wie fetch_and_extract, gibt zusaetzlich das og:image zurueck."""
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] could not fetch {url}: {exc}", file=sys.stderr)
        return "", None
    return extract_article_text(resp.text), extract_og_image(resp.text)


if __name__ == "__main__":
    import sys as _sys

    if len(_sys.argv) != 2:
        print("Usage: python3 extract_article.py <url>")
        raise SystemExit(1)
    print(fetch_and_extract(_sys.argv[1]))
