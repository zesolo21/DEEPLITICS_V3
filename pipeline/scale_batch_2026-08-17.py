"""
Skalierungs-Batch, 17.08.2026: vier ZUSÄTZLICHE, komplett neu und
unabhängig recherchierte Storys, auf Nutzerwunsch ("versuche die Anzahl
der Storys zu skalieren"), NACHDEM der Nutzer den ersten echten
API-Testlauf für diese Session zurückgestellt hat ("tut mir leid, diesen
Lauf noch ohne API").

Weil kein `ANTHROPIC_API_KEY` verfügbar war, wurde dieser Batch NICHT über
`pipeline/synthesize_story.py::synthesize_with_claude()` erzeugt, sondern
nach demselben Muster wie die ursprüngliche v5-Demo: vier parallele
Recherche-Agenten (Claude mit WebSearch/WebFetch) haben je EINE Story
komplett eigenständig recherchiert und nach der v6-Formel strukturiert
(STORY_JSON_SCHEMA_HINT aus synthesize_story.py als Vorgabe, inkl.
synthetischem Stil, Primärquellen-Recherche, politischer Theorie,
ehrlicher Marktkorrelations-Prüfung). Das ist NICHT dasselbe wie ein
automatisierter Pipeline-Lauf über die Anthropic API (kein Token-/
Kosten-Tracking, kein `_pipeline_meta`), demonstriert aber, dass die
generalisierte v6-Formel über vier thematisch/regional komplett
unterschiedliche, tagesaktuelle Themen hinweg zuverlässig funktioniert,
ohne dass die Struktur bricht oder erzwungen wirkt.

Themenauswahl bewusst divers, keine Überschneidung mit den 4
bestehenden `demo_live_run.py`-Storys (Naher Osten/zivil-militärische
Aufsicht, Afghanistan/Einwanderung, Sudan/Afrika, Ukraine/Militärschläge):

1. CIA-Drohnenangriffe vor Ecuador/Galápagos, verdeckte Kriegsführung,
   Lateinamerika.
2. Putins Kurilen-Besuch, Russland-Japan-Territorialstreit, Ostasien/Pazifik.
3. Section-338-Zölle gegen Kanada, Handelspolitik, Nordamerika.
4. DHS-Überwachung linker Gruppen in Minnesota, Bürgerrechte/Innenpolitik, USA.

Wie bei der v5-Demo gilt: Grundfakten, Zitate, Primärquellen und
Marktdaten stammen aus echter, web-gestützter Recherche vom 17.08.2026,
historische Linien nutzen etabliertes Allgemeinwissen. Wo keine belastbare
Primärquelle oder Marktkorrelation gefunden wurde, bleibt das Feld ehrlich
leer/false statt erfunden (siehe je Story `primary_sources`/
`market_correlation`).
"""

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
STORIES_JSON = BASE / "data" / "stories.json"
DEMO_MODULE = BASE / "pipeline" / "demo_live_run.py"

NEW_STORY_FILES_WITH_IDS = [
    ("cia-ecuador-drone-strikes-2026-08", "1_cia_ecuador.json"),
    ("putin-kuril-islands-visit-2026-08", "2_putin_kuril.json"),
    ("us-canada-section-338-tariffs-2026-08", "3_section338.json"),
    ("dhs-minnesota-surveillance-2026-08", "4_dhs_minnesota.json"),
]

# Die Rohrecherche-JSONs (von den vier parallelen Recherche-Agenten dieser
# Session produziert) liegen dauerhaft im Repo, nicht nur unter /tmp,
# damit dieses Skript in künftigen Sessions reproduzierbar lauffähig bleibt.
RAW_DIR = BASE / "data" / "scale_batch_2026-08-17"


def load_new_stories() -> list[dict]:
    stories = []
    for story_id, filename in NEW_STORY_FILES_WITH_IDS:
        raw = json.loads((RAW_DIR / filename).read_text())
        raw["id"] = story_id
        stories.append(raw)
    return stories


def run() -> list[dict]:
    # 1) die ursprünglichen 4 v5-Demo-Storys neu schreiben (Quelle der
    #    Wahrheit bleibt demo_live_run.py)
    import subprocess
    import sys

    subprocess.run([sys.executable, str(DEMO_MODULE)], check=True)
    base_stories = json.loads(STORIES_JSON.read_text())

    # 2) die 4 neuen Storys anhängen
    new_stories = load_new_stories()
    combined = base_stories + new_stories

    STORIES_JSON.write_text(json.dumps(combined, indent=2, ensure_ascii=False))
    print(f"Wrote {len(combined)} stories ({len(base_stories)} v5-Demo + {len(new_stories)} neu) -> {STORIES_JSON}")
    return combined


if __name__ == "__main__":
    run()
