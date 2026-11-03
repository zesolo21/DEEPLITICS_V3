"""
Orchestriert alle Schritte nacheinander (Bauanleitung Abschnitt 8):
Ingestion (feste Testartikel) -> Clustering -> Extraktion -> Tagging +
Scoring -> Speichern. Feeds werden nicht hier, sondern zur Anzeigezeit
in web/server.py aus den gespeicherten Threads gebaut (Abschnitt 5).

Aufruf: python3 pipeline/run_pipeline.py [--db PATH] [--reset]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.cluster import cluster_articles
from pipeline.config import DEFAULT_CONFIG, DEFAULT_USER_ID
from pipeline.extract import extract_thread_fields
from pipeline.models import TimelineEntry, User
from pipeline.tagging import tag_and_score_thread
from pipeline.test_articles import get_test_articles
from pipeline import store


def run(db_path: str = "deeplitics_v2.db", reset: bool = True) -> None:
    conn = store.connect(ROOT / db_path)
    if reset:
        store.reset_db(conn)

    print("Schritt 1: Ingestion (feste Test-Artikelmenge) ...")
    articles = get_test_articles()
    print(f"  {len(articles)} Artikel eingelesen.")

    print("Schritt 2: Clustering ...")
    threads = cluster_articles(articles, DEFAULT_CONFIG)
    print(f"  {len(threads)} Threads gebildet.")
    for th in threads:
        assert len(th.article_ids) >= 1

    by_id = {a.id: a for a in articles}
    print("Schritt 3: LLM-Extraktion (Faktenkern, Zeitleiste, Akteure) ...")
    for th in threads:
        th_articles = [by_id[aid] for aid in th.article_ids]
        fields = extract_thread_fields(th_articles)
        th.fact_core = fields["fact_core"]
        th.timeline = [TimelineEntry(**e) for e in fields["timeline"]]
        th.actors = fields["actors"]
        # Sinnvoller Titel: erster (chronologisch fruehster) Artikeltitel
        # der Gruppe statt des zufaellig gewaehlten vorlaeufigen Titels.
        th_articles_sorted = sorted(th_articles, key=lambda a: a.published_at)
        th.title = th_articles_sorted[0].title
    print(f"  {len(threads)} Threads extrahiert.")

    print("Schritt 4+5: Tagging + Wichtigkeits-Score ...")
    for th in threads:
        th_articles = [by_id[aid] for aid in th.article_ids]
        tag_and_score_thread(th, th_articles, DEFAULT_CONFIG)
    print("  fertig. Themen/Scores:")
    for th in sorted(threads, key=lambda t: t.importance_score, reverse=True):
        print(f"    [{th.importance_score:.2f}] {th.topic:14s} {th.title[:60]}")

    print("Speichern ...")
    store.save_articles(conn, articles)
    store.save_threads(conn, threads)
    store.save_user(conn, User(id=DEFAULT_USER_ID, pinned_topics=["migration", "wirtschaft", "sicherheit"]))
    conn.close()
    print(f"Fertig. -> {ROOT / db_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="deeplitics_v2.db")
    parser.add_argument("--no-reset", action="store_true")
    args = parser.parse_args()
    run(db_path=args.db, reset=not args.no_reset)
