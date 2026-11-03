"""
Orchestriert die gesamte Pipeline:
  1. RSS-Feeds von allen Quellen abrufen           (fetch_feeds)
  2. Pro Artikel Volltext nachladen                (extract_article)
  3. Nahezu-Duplikate entfernen                     (dedupe_articles)
  4. Artikel zu Storys clustern                     (cluster_articles)
  5. Pro Cluster eine Story synthetisieren           (synthesize_story),
     PARALLEL über einen Thread-Pool, s. Version 6 unten
  6. Bilder & echte Kursdaten nachladen (pro Story)  (enrich_entity_images,
                                                       enrich_market_data)
  7. Ergebnis als data/stories.json schreiben        (-> Frontend liest das)

WICHTIG: In dieser Cloud-Sandbox ist der Netzwerkzugriff auf Paket-
Registries beschränkt (siehe docs/NETWORK_NOTES.md), `requests.get()` zu
normalen Webseiten schlägt hier fehl. Dieses Skript ist trotzdem voll
lauffähig in jeder normalen Umgebung (eigener Rechner, Server, GitHub
Actions, Vercel Cron, ...).

Version 6, auf Nutzerwunsch "generalisieren/formalisieren + beim Skalieren
gut funktionieren, nicht zu viele Tokens/Rechenzeit":

- Alle Skalierungs-Regler kommen jetzt aus `pipeline/config.py`
  (`PipelineConfig`), per CLI überschreibbar (`--help` für alle Optionen),
  statt Funktionsparameter-Defaults hier im Code zu verstecken.
- Synthese läuft PARALLEL über `ThreadPoolExecutor`
  (`config.synthesis_concurrency`), nicht mehr seriell, das ist der größte
  Hebel dafür, dass "mehr Storys" nicht linear "mehr Wartezeit" bedeutet.
- `--max-stories` deckelt, wie viele der gefundenen Multi-Source-Cluster
  tatsächlich synthetisiert werden (die größten/best-belegten zuerst, s.
  `cluster.py`-Sortierung), UNABHÄNGIG davon wie viele Rohartikel/Cluster
  insgesamt gefunden wurden, das macht Kosten eines Laufs vorhersagbar.
- Ein einzelner fehlgeschlagener Story-Synthese-Aufruf (Netzwerkfehler,
  ungültiges JSON nach allen Retries, Rate-Limit) bricht NICHT mehr den
  ganzen Lauf ab, sondern wird geloggt und übersprungen.
- Am Ende gibt es eine Lauf-Zusammenfassung (Anzahl Storys, falls
  API-Metadaten vorhanden: Gesamt-Tokens, ungefähre Laufzeit), damit
  Kosten/Skalierung beim Hochfahren der Story-Zahl beobachtbar sind.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.cluster import cluster_articles  # noqa: E402
from pipeline.llm_cluster import llm_cluster_articles  # noqa: E402
from pipeline.config import DEFAULT_CONFIG, FULL_DEPTH_CONFIG, LITE_SCALE_CONFIG, PipelineConfig  # noqa: E402
from pipeline.extract_article import fetch_and_extract_with_image  # noqa: E402
from pipeline.enrich_entity_images import enrich_entity_images  # noqa: E402
from pipeline.enrich_market_data import enrich_market_data  # noqa: E402
from pipeline.fetch_feeds import fetch_all  # noqa: E402
from pipeline.synthesize_story import build_prompt, synthesize_with_claude  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

PROFILES = {
    "default": DEFAULT_CONFIG,
    "lite": LITE_SCALE_CONFIG,
    "full": FULL_DEPTH_CONFIG,
}


def dedupe_articles(articles: list[dict], title_similarity: float = 0.85) -> list[dict]:
    """Entfernt Artikel mit (fast) identischem Titel (z.B. wenn ein Feed
    denselben Artikel zweimal listet)."""
    kept: list[dict] = []
    for a in articles:
        is_dupe = any(
            SequenceMatcher(None, a["title"].lower(), k["title"].lower()).ratio()
            > title_similarity
            for k in kept
        )
        if not is_dupe:
            kept.append(a)
    return kept


def _load_existing_stories() -> list[dict]:
    """Laedt bereits gespeicherte Storys aus data/stories.json, falls
    vorhanden -- Grundlage fuer die Story-AKKUMULATION (Nutzerwunsch
    23.08.2026: alte Storys bleiben auf der Website sichtbar statt bei
    jedem Lauf ueberschrieben zu werden). Leere Liste bei fehlender/
    kaputter Datei, statt den Lauf abzubrechen."""
    path = DATA_DIR / "stories.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[warn] data/stories.json nicht lesbar ({exc}), starte mit leerer Historie.", file=sys.stderr)
        return []
    return data if isinstance(data, list) else []


def _merge_stories(
    new_stories: list[dict],
    existing_stories: list[dict],
    title_similarity: float = 0.82,
    max_total: int | None = None,
) -> list[dict]:
    """Stellt `new_stories` VOR `existing_stories` (neueste zuerst). Eine
    bestehende Story mit sehr aehnlichem Titel wie eine NEUE Story wird
    dabei aus `existing_stories` entfernt -- die neue, frisch synthetisierte
    Version ERSETZT die alte, statt dass dasselbe Thema doppelt auftaucht,
    wenn es ueber mehrere 6h-Laeufe hinweg in den Schlagzeilen bleibt.
    `max_total` deckelt (falls gesetzt) die Gesamtzahl, aelteste zuerst
    entfernt -- verhindert unbegrenztes Wachstum von data/stories.json."""
    def is_dupe(existing: dict, fresh: dict) -> bool:
        return SequenceMatcher(
            None,
            (existing.get("title") or "").lower(),
            (fresh.get("title") or "").lower(),
        ).ratio() > title_similarity

    kept_existing = [
        e for e in existing_stories
        if not any(is_dupe(e, n) for n in new_stories)
    ]
    merged = new_stories + kept_existing
    if max_total is not None and len(merged) > max_total:
        dropped = len(merged) - max_total
        print(
            f"[info] {dropped} älteste Storys über dem Limit (--max-total-stories "
            f"{max_total}) entfernt.",
            file=sys.stderr,
        )
        merged = merged[:max_total]
    return merged


def _synthesize_one(cluster: list[dict], config: PipelineConfig) -> dict:
    """Eine Story synthetisieren, mit Fallback auf den reinen Prompt, wenn
    keine API verfügbar ist (RuntimeError). Fehler beim eigentlichen
    API-Aufruf (Netzwerk, Rate-Limit, wiederholt ungültiges JSON) werden
    NICHT hier verschluckt, sondern laufen nach oben durch, damit der
    Aufrufer (`run()`) sie pro Story loggen und den restlichen Lauf
    trotzdem fortsetzen kann."""
    try:
        return synthesize_with_claude(cluster, config=config)
    except RuntimeError as e:
        # Kein API-Zugriff (Paket fehlt / kein Key) ist ein erwarteter,
        # nicht-fataler Fall, hier bewusst weiter als "needs_llm_synthesis"
        # Platzhalter statt als Fehler behandelt.
        if "ANTHROPIC_API_KEY" in str(e) or "nicht installiert" in str(e):
            print(f"[info] Kein LLM-API-Zugriff ({e}). Schreibe Prompt stattdessen.", file=sys.stderr)
            return {
                "title": cluster[0]["title"],
                "needs_llm_synthesis": True,
                "prompt": build_prompt(cluster, config=config),
                "sources": sorted({a["source"] for a in cluster}),
                "article_urls": [a.get("link") or a.get("url") for a in cluster],
            }
        raise


def run(
    max_articles_per_source: int | None = None,
    enrich_fulltext: bool = True,
    config: PipelineConfig = DEFAULT_CONFIG,
) -> list[dict]:
    max_articles_per_source = (
        max_articles_per_source
        if max_articles_per_source is not None
        else config.max_articles_per_source
    )
    t_start = time.time()

    print("[1/5] Fetching RSS feeds...", file=sys.stderr)
    raw = fetch_all()

    # pro Quelle begrenzen, damit die Pipeline nicht ewig läuft
    by_source: dict[str, list[dict]] = {}
    for a in raw:
        by_source.setdefault(a["source"], []).append(a)
    limited = [a for arts in by_source.values() for a in arts[:max_articles_per_source]]

    print(f"[2/5] Deduping ({len(limited)} raw items)...", file=sys.stderr)
    deduped = dedupe_articles(limited)

    if enrich_fulltext:
        print(
            f"[3/5] Extracting full text for {len(deduped)} articles "
            f"(concurrency={config.fetch_concurrency})...",
            file=sys.stderr,
        )
        with ThreadPoolExecutor(max_workers=max(1, config.fetch_concurrency)) as pool:
            results = list(pool.map(lambda a: fetch_and_extract_with_image(a["link"]), deduped))
        for a, (text, og_image) in zip(deduped, results):
            a["text"] = text or a.get("summary", "")
            a["combined_text"] = f"{a['title']} {a['text'][:500]}"
            # og:image ist das von der Publikation selbst hinterlegte
            # Vorschaubild (siehe extract_article.py::extract_og_image) --
            # muss hier auf dem Artikel landen UND (s. synthesize_story.py
            # ::_build_prompt_text) in den Prompt, sonst hat das Modell
            # buchstaeblich keine echte Bild-URL zur Auswahl und liefert
            # (korrekterweise, gemaess seiner Anweisung nie zu erfinden)
            # immer null zurueck.
            a["og_image"] = og_image
    else:
        for a in deduped:
            a["text"] = a.get("summary", "")
            a["combined_text"] = f"{a['title']} {a['text']}"

    print("[4/5] Clustering into storylines (LLM-basiert, Fallback TF-IDF)...", file=sys.stderr)
    clusters = llm_cluster_articles(deduped, config=config)
    if clusters is None:
        clusters = cluster_articles(deduped, config=config)
    # nur Cluster aus >= min_sources_for_story verschiedenen Quellen sind
    # "echte" (quellenübergreifende) Storys
    multi_source_clusters = [
        c for c in clusters if len({a["source"] for a in c}) >= config.min_sources_for_story
    ]

    if config.max_stories_per_run is not None:
        skipped = max(0, len(multi_source_clusters) - config.max_stories_per_run)
        if skipped:
            print(
                f"[info] {len(multi_source_clusters)} Multi-Source-Cluster gefunden, "
                f"verarbeite die {config.max_stories_per_run} größten "
                f"(--max-stories), {skipped} übersprungen.",
                file=sys.stderr,
            )
        multi_source_clusters = multi_source_clusters[: config.max_stories_per_run]

    n = len(multi_source_clusters)
    print(
        f"[5/5] Synthesizing {n} stories "
        f"(depth={config.research_depth}, concurrency={config.synthesis_concurrency})...",
        file=sys.stderr,
    )

    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "articles_enriched.json").write_text(
        json.dumps(deduped, indent=2, ensure_ascii=False)
    )

    existing_stories = _load_existing_stories()
    print(
        f"[info] {len(existing_stories)} bestehende Storys geladen -- "
        f"werden mit den neuen zusammengeführt (nicht überschrieben).",
        file=sys.stderr,
    )

    stories: list[dict | None] = [None] * n
    errors = 0
    # WICHTIG (gefunden im ersten echten API-Testlauf, 18.08.2026): eine
    # einzelne besonders lange/mehrfach-retry-pflichtige Story (großes
    # Cluster, Selbstkorrektur-Retry wegen max_tokens, s.
    # synthesize_story.py) kann deutlich länger brauchen als der Rest der
    # Charge. Vorher wurde `data/stories.json` erst NACH `as_completed`
    # für ALLE Futures geschrieben -- ein einziger langsamer/hängender
    # Aufruf verzögerte damit das Sichern ALLER bereits fertigen Storys.
    # Jetzt wird nach JEDER fertigen Story sofort der aktuelle
    # Zwischenstand geschrieben, damit ein Abbruch/Timeout mitten im Lauf
    # nicht die bereits erfolgreich synthetisierten Storys mit verliert.
    with ThreadPoolExecutor(max_workers=max(1, config.synthesis_concurrency)) as pool:
        future_to_idx = {
            pool.submit(_synthesize_one, cluster, config): i
            for i, cluster in enumerate(multi_source_clusters)
        }
        done = 0
        for future in as_completed(future_to_idx):
            i = future_to_idx[future]
            done += 1
            try:
                story = future.result()
                # Kostenlose Bildanreicherung ueber Wikipedia fuer
                # Personen/Organisationen ohne LLM-gefundenes Bild (s.
                # enrich_entity_images.py-Docstring). Laeuft NACH der
                # Synthese, ist reines HTTP, kein zusaetzlicher API-Call --
                # ein Fehlschlag hier darf die Story nicht verwerfen.
                try:
                    enrich_entity_images(story)
                except Exception as img_exc:  # noqa: BLE001
                    print(f"    [warn] Bildanreicherung fehlgeschlagen: {img_exc}", file=sys.stderr)
                # Echte Kursdaten via yfinance nachladen, falls das Modell
                # in market_correlation.tickers welche genannt hat (s.
                # enrich_market_data.py-Docstring). Genau wie die
                # Bildanreicherung: rein additiv, ein Fehlschlag darf die
                # Story nicht verwerfen, sie bleibt dann einfach bei ihrer
                # bisherigen qualitativen Einschätzung ohne Chart.
                try:
                    enrich_market_data(story)
                except Exception as market_exc:  # noqa: BLE001
                    print(f"    [warn] Marktdaten-Anreicherung fehlgeschlagen: {market_exc}", file=sys.stderr)
                stories[i] = story
            except Exception as exc:  # noqa: BLE001 - ein Story-Fehler darf den Lauf nicht stoppen
                errors += 1
                title = multi_source_clusters[i][0].get("title", "?")
                print(f"[error] Story '{title}' fehlgeschlagen: {exc}", file=sys.stderr)
            print(f"    ... {done}/{n} Storys verarbeitet", file=sys.stderr)
            new_so_far = [s for s in stories if s is not None]
            merged_so_far = _merge_stories(new_so_far, existing_stories, max_total=config.max_total_stories)
            (DATA_DIR / "stories.json").write_text(
                json.dumps(merged_so_far, indent=2, ensure_ascii=False)
            )

    stories = [s for s in stories if s is not None]
    merged = _merge_stories(stories, existing_stories, max_total=config.max_total_stories)
    (DATA_DIR / "stories.json").write_text(json.dumps(merged, indent=2, ensure_ascii=False))

    elapsed = time.time() - t_start
    total_in = sum(s.get("_pipeline_meta", {}).get("input_tokens", 0) for s in stories)
    total_out = sum(s.get("_pipeline_meta", {}).get("output_tokens", 0) for s in stories)
    print(
        f"Done in {elapsed:.1f}s. {len(stories)} new stories written "
        f"({errors} failed), {len(merged)} insgesamt akkumuliert -> data/stories.json",
        file=sys.stderr,
    )
    if total_in or total_out:
        print(
            f"Token usage: {total_in} input + {total_out} output "
            f"= {total_in + total_out} total across {len(stories)} stories "
            f"(~{(total_in + total_out) / max(1, len(stories)):.0f}/story).",
            file=sys.stderr,
        )
    return stories


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Deeplitics Pipeline")
    p.add_argument(
        "--profile",
        choices=sorted(PROFILES),
        default="default",
        help="Vorkonfiguriertes Regler-Set aus config.py (default: schnell/günstig ohne Recherche-Tool, "
        "lite: noch schlanker für große Story-Zahlen, full: volle Formel inkl. Web-Recherche).",
    )
    p.add_argument("--max-stories", type=int, default=None, help="Deckelt Anzahl synthetisierter Storys.")
    p.add_argument(
        "--max-total-stories", type=int, default=None,
        help="Deckelt die GESAMTZAHL akkumulierter Storys in data/stories.json "
        "(älteste fliegen zuerst raus). -1 für kein Limit.",
    )
    p.add_argument("--max-articles-per-source", type=int, default=None)
    p.add_argument("--concurrency", type=int, default=None, help="Parallele API-Calls.")
    p.add_argument("--fetch-concurrency", type=int, default=None, help="Parallele Volltext-Fetches.")
    p.add_argument("--model", type=str, default=None)
    p.add_argument("--research-depth", choices=["full", "lite"], default=None)
    p.add_argument("--no-fulltext", action="store_true", help="Nur RSS-Summaries nutzen, keine Volltext-Extraktion.")
    return p.parse_args(argv)


def _config_from_args(args: argparse.Namespace) -> PipelineConfig:
    base = PROFILES[args.profile]
    overrides = {}
    if args.max_stories is not None:
        overrides["max_stories_per_run"] = args.max_stories
    if args.max_total_stories is not None:
        overrides["max_total_stories"] = None if args.max_total_stories < 0 else args.max_total_stories
    if args.max_articles_per_source is not None:
        overrides["max_articles_per_source"] = args.max_articles_per_source
    if args.concurrency is not None:
        overrides["synthesis_concurrency"] = args.concurrency
    if args.fetch_concurrency is not None:
        overrides["fetch_concurrency"] = args.fetch_concurrency
    if args.model is not None:
        overrides["model"] = args.model
    if args.research_depth is not None:
        overrides["research_depth"] = args.research_depth
        overrides["enable_web_search"] = args.research_depth == "full"
    return PipelineConfig(**{**base.__dict__, **overrides})


if __name__ == "__main__":
    parsed = _parse_args(sys.argv[1:])
    cfg = _config_from_args(parsed)
    run(enrich_fulltext=not parsed.no_fulltext, config=cfg)
