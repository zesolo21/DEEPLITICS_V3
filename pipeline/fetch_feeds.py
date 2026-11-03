"""
RSS/Atom-Feeds abrufen und in eine einheitliche Liste von "Feed Items"
(Titel, Link, Summary, Datum, Quelle) umwandeln.

Bewusst OHNE `feedparser`, weil in bestimmten Umgebungen (z.B. dieser
Cloud-Sandbox) keine PyPI-Installation möglich ist. Stattdessen: Standard-
lib `xml.etree.ElementTree`, was für RSS 2.0 und die meisten Atom-Feeds
ausreicht.

In einer normalen Umgebung mit vollem Internetzugang tut dieses Skript
genau das, was man erwartet: `python3 fetch_feeds.py` -> data/articles_raw.json
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.sources.feeds import SOURCES, Source  # noqa: E402

USER_AGENT = (
    "Mozilla/5.0 (compatible; DeeplíticsBot/0.1; "
    "+https://example.org/deeplitics-bot) Python-requests"
)

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def _text(el) -> str | None:
    return el.text.strip() if el is not None and el.text else None


def parse_rss2(root: ET.Element) -> list[dict]:
    items = []
    for item in root.findall(".//item"):
        items.append(
            {
                "title": _text(item.find("title")),
                "link": _text(item.find("link")),
                "summary": _text(item.find("description")),
                "published": _text(item.find("pubDate")),
            }
        )
    return items


def parse_atom(root: ET.Element) -> list[dict]:
    items = []
    for entry in root.findall("atom:entry", ATOM_NS):
        link_el = entry.find("atom:link", ATOM_NS)
        link = link_el.get("href") if link_el is not None else None
        items.append(
            {
                "title": _text(entry.find("atom:title", ATOM_NS)),
                "link": link,
                "summary": _text(entry.find("atom:summary", ATOM_NS)),
                "published": _text(entry.find("atom:updated", ATOM_NS)),
            }
        )
    return items


def fetch_feed(source: Source, timeout: int = 10) -> list[dict]:
    """Holt und parst einen einzelnen Feed. Gibt [] zurück bei Fehlern
    (Netzwerk, 403, kaputtes XML) statt den ganzen Lauf abzubrechen."""
    try:
        resp = requests.get(
            source.feed_url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as exc:  # noqa: BLE001 - bewusst breit, robuste Pipeline
        print(f"[warn] {source.name}: {exc}", file=sys.stderr)
        return []

    items = parse_rss2(root) if root.tag == "rss" else parse_atom(root)

    out = []
    for it in items:
        if not it.get("title") or not it.get("link"):
            continue
        out.append(
            {
                "source": source.name,
                "country": source.country,
                "title": it["title"],
                "link": it["link"],
                "summary": it.get("summary") or "",
                "published": it.get("published"),
            }
        )
    return out


def fetch_all(sources: list[Source] = SOURCES) -> list[dict]:
    all_items: list[dict] = []
    for src in sources:
        items = fetch_feed(src)
        print(f"[ok] {src.name}: {len(items)} items", file=sys.stderr)
        all_items.extend(items)
    return all_items


if __name__ == "__main__":
    out_path = Path(__file__).resolve().parent.parent / "data" / "articles_raw.json"
    out_path.parent.mkdir(exist_ok=True)
    items = fetch_all()
    out_path.write_text(json.dumps(items, indent=2, ensure_ascii=False))
    print(f"Wrote {len(items)} feed items -> {out_path}")
