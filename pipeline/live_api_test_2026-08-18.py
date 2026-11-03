"""
Erster ECHTER API-Testlauf, 18.08.2026.

Der Nutzer hat einen ANTHROPIC_API_KEY direkt im Chat gepostet. Damit ist
dieses Skript der erste Lauf, der tatsächlich `synthesize_with_claude()`
aus `pipeline/synthesize_story.py` gegen die echte Anthropic API aufruft
(SDK-oder-HTTP-Fallback, s. dortiger Docstring) -- inklusive echtem
Token-Tracking über `_pipeline_meta`. Alles davor (Demo-Storys,
Skalierungs-Batch vom 17.08.) wurde von Recherche-Agenten OHNE gemessenen
API-Aufruf erzeugt.

Weil in dieser Cloud-Sandbox `requests.get()` gegen normale RSS-Feed-
Domains blockiert ist (bestätigt: Reuters/AP/BBC/Axios/DW/France24 liefern
alle ProxyError, nur `api.anthropic.com` ist erreichbar, s.
docs/NETWORK_NOTES.md), kann der Schritt "echte RSS-Feeds live abrufen"
hier nicht ausgeführt werden. Um trotzdem einen ECHTEN, nicht simulierten
Test des API-Aufruf-Pfads zu machen, wurden die Rohartikel stattdessen via
WebSearch/WebFetch (eigene, von der Sandbox getrennte Tools) aus echten,
aktuellen (10.-17.08.2026) Artikeln von 10 unterschiedlichen realen Quellen
zu 5 Themen-Clustern zusammengetragen (data/live_api_test_2026-08-18/raw_articles.json).
Das ersetzt nur den Fetch-Schritt (1) der Pipeline durch eine andere reale
Quelle -- ab dem Clustering/Synthese-Schritt läuft alles unverändert über
den echten Produktionscode (`select_representative_articles`,
`synthesize_with_claude`, `_finalize_story_dict`, Lite-Profil).

Themen (bewusst keine Überschneidung mit den bestehenden 8 Storys):
1. Taiwan Han-Kuang-Manöver / China-Spannungen
2. EU 21. + geplantes 22. Sanktionspaket gegen Russland
3. Nachwirkungen der Maduro-Festnahme (Venezuela)
4. Führungskrise um Starmer (UK Labour)
5. Netanyahu vs. Gaza-Fahrplan / Kushner-Vermittlung

Profil: LITE (wie vom Nutzer zuvor gewählt: "Klein & günstig testen,
~10 Storys") -- kein `web_search`-Tool, `primary_sources`/
`market_correlation` werden serverseitig hart geleert, volles
Token-Tracking läuft trotzdem.
"""

from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.config import LITE_SCALE_CONFIG  # noqa: E402
from pipeline.synthesize_story import synthesize_with_claude  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
RAW_PATH = BASE / "data" / "live_api_test_2026-08-18" / "raw_articles.json"
STORIES_JSON = BASE / "data" / "stories.json"
RESULT_LOG = BASE / "data" / "live_api_test_2026-08-18" / "run_result.json"


def load_clusters() -> dict[str, list[dict]]:
    return json.loads(RAW_PATH.read_text())


def _synthesize_one(story_id: str, articles: list[dict]) -> tuple[str, dict | None, str | None]:
    try:
        story = synthesize_with_claude(articles, config=LITE_SCALE_CONFIG)
        story["id"] = story_id
        return story_id, story, None
    except Exception as exc:  # echte Fehlerisolation, wie in run_pipeline.py
        return story_id, None, f"{type(exc).__name__}: {exc}"


def run() -> None:
    clusters = load_clusters()
    print(f"Lade {len(clusters)} Cluster, Profil=lite, Modell={LITE_SCALE_CONFIG.model}")

    t0 = time.time()
    results: dict[str, dict] = {}
    errors: dict[str, str] = {}

    def _persist_partial() -> None:
        # Nach jeder fertigen Story sofort sichern, s. run_pipeline.py-Fix
        # vom selben Testlauf: ein einzelner langsamer Cluster darf nicht
        # dazu führen, dass bereits erfolgreiche Storys verloren gehen,
        # falls der Gesamtlauf abgebrochen/getimeoutet wird.
        RESULT_LOG.parent.mkdir(parents=True, exist_ok=True)
        RESULT_LOG.write_text(json.dumps({
            "partial": True,
            "elapsed_seconds_so_far": time.time() - t0,
            "stories_ok": list(results.keys()),
            "errors": errors,
        }, indent=2, ensure_ascii=False))
        if results:
            existing = json.loads(STORIES_JSON.read_text()) if STORIES_JSON.exists() else []
            existing_ids = {s["id"] for s in existing}
            for story_id, story in results.items():
                if story_id not in existing_ids:
                    existing.append(story)
                    existing_ids.add(story_id)
            STORIES_JSON.write_text(json.dumps(existing, indent=2, ensure_ascii=False))

    with ThreadPoolExecutor(max_workers=LITE_SCALE_CONFIG.synthesis_concurrency) as pool:
        futures = {
            pool.submit(_synthesize_one, story_id, articles): story_id
            for story_id, articles in clusters.items()
        }
        for fut in as_completed(futures):
            story_id, story, err = fut.result()
            if story is not None:
                results[story_id] = story
                meta = story.get("_pipeline_meta", {})
                print(f"  OK   {story_id}  in={meta.get('input_tokens')} out={meta.get('output_tokens')}")
            else:
                errors[story_id] = err
                print(f"  FAIL {story_id}  {err}")
            _persist_partial()

    elapsed = time.time() - t0
    total_in = sum(s.get("_pipeline_meta", {}).get("input_tokens", 0) for s in results.values())
    total_out = sum(s.get("_pipeline_meta", {}).get("output_tokens", 0) for s in results.values())

    print(f"\nFertig in {elapsed:.1f}s. {len(results)}/{len(clusters)} Storys erfolgreich.")
    print(f"Tokens gesamt: input={total_in}, output={total_out}")
    # Sonnet-4.5-Preise (platform.claude.com/docs, Stand dieser Session): $3/MTok in, $15/MTok out
    cost = total_in / 1_000_000 * 3 + total_out / 1_000_000 * 15
    print(f"Geschaetzte Kosten dieses Laufs: ${cost:.4f}")

    RESULT_LOG.parent.mkdir(parents=True, exist_ok=True)
    RESULT_LOG.write_text(json.dumps({
        "elapsed_seconds": elapsed,
        "total_input_tokens": total_in,
        "total_output_tokens": total_out,
        "estimated_cost_usd": cost,
        "stories_ok": list(results.keys()),
        "errors": errors,
    }, indent=2, ensure_ascii=False))

    if results:
        existing = json.loads(STORIES_JSON.read_text()) if STORIES_JSON.exists() else []
        existing_ids = {s["id"] for s in existing}
        appended = 0
        for story_id, story in results.items():
            if story_id not in existing_ids:
                existing.append(story)
                appended += 1
        STORIES_JSON.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
        print(f"{appended} neue Storys an {STORIES_JSON} angehaengt -> {len(existing)} Storys gesamt.")


if __name__ == "__main__":
    run()
