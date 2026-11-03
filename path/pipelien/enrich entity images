"""
Günstige Bildbeschaffung für Entitäten (Nutzer-Feedback 24.08.2026:
"Versuche irgendwie Bilder zu beschaffen, möglichst günstig!").

Hintergrund: `synthesize_story.py` bittet das LLM zwar um eine
`image_url` je Entität (Personen/Organisationen), aber das Modell darf
NIEMALS eine URL erfinden -- bei weniger prominenten Akteuren bleibt das
Feld deshalb meistens `null`. Diese Datei füllt genau diese Lücken NACH
der LLM-Synthese, mit einer Quelle, die komplett kostenlos ist und ohne
API-Key funktioniert: die Wikipedia-REST-API
(`/api/rest_v1/page/summary/<Titel>`) liefert für die meisten Personen/
Organisationen mit eigenem Wikipedia-Artikel ein `thumbnail.source`-Feld
zurück -- ein einziger schneller HTTP-GET pro Entität, kein LLM-Aufruf,
keine zusätzlichen API-Kosten.

Bewusst NUR type in {person, organization} (die Typen, für die "ein Foto
der Person/Institution" überhaupt Sinn ergibt) und NUR wenn `image_url`
bereits `null` ist (kein Überschreiben einer vom Modell echt gefundenen
URL). Erst Deutsch versucht, dann Englisch als Fallback (mehr Artikel,
gerade zu US-/internationalen Akteuren). Jeder Fehlschlag (404, Timeout,
kein Thumbnail vorhanden) wird still übersprungen -- eine Entität ohne
Bild bekommt im Frontend ohnehin ein Icon-Fallback (s. `mediaTag()` in
app.js), das ist kein Fehlerzustand.
"""

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

IMAGE_ELIGIBLE_TYPES = {"person", "organization"}
WIKI_LANGS = ("de", "en")
REQUEST_TIMEOUT = 4
USER_AGENT = "Deeplitics/1.0 (https://github.com/; kontakt via Repo-Issues) enrich_entity_images.py"


def _fetch_thumbnail(name: str) -> str | None:
    """Versucht, ein frei lizenziertes Vorschaubild für `name` über die
    Wikipedia-REST-API zu finden. Gibt None zurück statt zu werfen, wenn
    nichts gefunden wird -- das ist der Normalfall für viele Entitäten,
    kein Fehler."""
    try:
        import requests
    except ImportError:
        return None

    for lang in WIKI_LANGS:
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{quote(name)}"
        try:
            r = requests.get(
                url,
                headers={"User-Agent": USER_AGENT, "accept": "application/json"},
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException:
            continue
        if r.status_code != 200:
            continue
        try:
            data = r.json()
        except ValueError:
            continue
        # Begriffsklärungsseiten haben kein Thumbnail und sind für uns
        # nutzlos (mehrdeutiger Name), einfach zur nächsten Sprache/weiter.
        if data.get("type") == "disambiguation":
            continue
        thumb = (data.get("thumbnail") or {}).get("source")
        if thumb:
            return thumb
    return None


def enrich_entity_images(story: dict, concurrency: int = 6) -> int:
    """Füllt `image_url: null` bei geeigneten Entitäten der Story, wenn
    über Wikipedia ein Bild auffindbar ist. Mutiert `story` in-place und
    gibt die Anzahl neu befüllter Bilder zurück (rein informativ fürs
    Logging)."""
    entities = story.get("entities") or []
    candidates = [
        e for e in entities
        if isinstance(e, dict)
        and e.get("type") in IMAGE_ELIGIBLE_TYPES
        and not e.get("image_url")
        and e.get("name")
    ]
    if not candidates:
        return 0

    filled = 0
    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        results = list(pool.map(lambda e: _fetch_thumbnail(e["name"]), candidates))
    for entity, thumb in zip(candidates, results):
        if thumb:
            entity["image_url"] = thumb
            entity["image_source"] = "wikipedia"
            filled += 1
    if filled:
        print(
            f"    [info] {filled}/{len(candidates)} Entitäts-Bilder über "
            f"Wikipedia nachgeladen (kostenlos, kein API-Call).",
            file=sys.stderr,
        )
    return filled
