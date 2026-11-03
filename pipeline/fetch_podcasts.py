"""
Episoden-Metadaten aus Podcast-RSS-Feeds abrufen.

Strukturell fast identisch zu `fetch_feeds.py` fuer Text-Quellen: beides
sind RSS/Atom-Feeds, per `xml.etree.ElementTree` geparst (kein
`feedparser`, siehe docs/NETWORK_NOTES.md). Der einzige Unterschied: jedes
<item> hat zusaetzlich ein <enclosure url="..." type="audio/mpeg" .../>
-Tag, das auf die Audiodatei zeigt, und optional <itunes:duration>/
<itunes:summary>.

Der Output (`PodcastEpisode`) ist bewusst noch KEIN `Article` — eine
Episode hat erst dann verwertbaren Text, wenn `transcribe.py` das Audio in
ein Transkript umgewandelt hat. Erst danach (siehe
`episode_to_article_stub`) kann sie in dieselbe Cluster-/Synthese-Pipeline
wie Artikel einfliessen.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import requests

from pipeline.sources.podcasts import PODCASTS, PodcastSource

USER_AGENT = (
    "Mozilla/5.0 (compatible; DeeplíticsBot/0.1; "
    "+https://example.org/deeplitics-bot) Python-requests"
)

ITUNES_NS = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"


@dataclass
class PodcastEpisode:
    podcast_name: str
    publisher: str
    bias: str
    title: str
    description: str
    published: str | None
    audio_url: str | None
    duration: str | None
    episode_page_url: str | None  # <link>, falls vorhanden (Shownotes-Seite)


def _text(el: ET.Element | None) -> str | None:
    if el is None or el.text is None:
        return None
    return el.text.strip()


def parse_podcast_rss(xml_text: str, src: PodcastSource) -> list[PodcastEpisode]:
    episodes: list[PodcastEpisode] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        print(f"[warn] could not parse podcast feed {src.feed_url}: {exc}", file=sys.stderr)
        return episodes

    channel = root.find("channel")
    items = channel.findall("item") if channel is not None else root.findall(".//item")

    for item in items:
        enclosure = item.find("enclosure")
        audio_url = enclosure.get("url") if enclosure is not None else None

        duration = _text(item.find(f"{ITUNES_NS}duration"))
        description = _text(item.find(f"{ITUNES_NS}summary")) or _text(item.find("description")) or ""

        episodes.append(
            PodcastEpisode(
                podcast_name=src.name,
                publisher=src.publisher,
                bias=src.bias,
                title=_text(item.find("title")) or "(ohne Titel)",
                description=description,
                published=_text(item.find("pubDate")),
                audio_url=audio_url,
                duration=duration,
                episode_page_url=_text(item.find("link")),
            )
        )
    return episodes


def fetch_podcast_episodes(src: PodcastSource, timeout: int = 10) -> list[PodcastEpisode]:
    try:
        resp = requests.get(src.feed_url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] could not fetch podcast feed {src.name}: {exc}", file=sys.stderr)
        return []
    return parse_podcast_rss(resp.text, src)


def fetch_all_podcasts(limit_per_show: int = 5) -> list[PodcastEpisode]:
    """Holt die neuesten `limit_per_show` Episoden je Podcast aus `PODCASTS`.
    Kaputte/nicht erreichbare Feeds werden übersprungen, nicht die ganze
    Pipeline zum Absturz gebracht (gleiches Verhalten wie fetch_feeds.py)."""
    all_eps: list[PodcastEpisode] = []
    for src in PODCASTS:
        eps = fetch_podcast_episodes(src)[:limit_per_show]
        print(f"[info] {src.name}: {len(eps)} Episoden geladen", file=sys.stderr)
        all_eps.extend(eps)
    return all_eps


if __name__ == "__main__":
    eps = fetch_all_podcasts()
    for e in eps:
        print(f"- [{e.podcast_name}] {e.title} ({e.published}) -> {e.audio_url}")
