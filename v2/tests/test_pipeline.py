"""
Tests je Pipeline-Schritt an den Beispieldaten (Bauanleitung Abschnitt 8:
"teste nach jedem Schritt mit ein paar Beispielartikeln, bevor du
weitermachst"). Bewusst mit einfachen `assert`-Funktionen statt eines
Test-Frameworks gehalten (keine zusaetzliche Abhaengigkeit noetig) --
Aufruf: `python3 tests/test_pipeline.py`.
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.cluster import cluster_articles
from pipeline.config import DEFAULT_CONFIG, TOPIC_KEYS
from pipeline.extract import extract_thread_fields
from pipeline.feeds import apply_perspective_breadth, get_top_feed, get_topic_feed
from pipeline.models import User
from pipeline.tagging import tag_and_score_thread
from pipeline.test_articles import get_test_articles

PASSED = 0
FAILED = []


def check(name: str, condition: bool) -> None:
    global PASSED
    if condition:
        PASSED += 1
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name}")


def build_pipeline():
    articles = get_test_articles()
    threads = cluster_articles(articles, DEFAULT_CONFIG)
    by_id = {a.id: a for a in articles}
    for th in threads:
        th_articles = [by_id[aid] for aid in th.article_ids]
        fields = extract_thread_fields(th_articles)
        th.fact_core = fields["fact_core"]
        th.actors = fields["actors"]
        tag_and_score_thread(th, th_articles, DEFAULT_CONFIG)
    return articles, by_id, threads


def test_step1_models_and_fixtures():
    print("Schritt 1: Datenmodell + Testartikel")
    articles = get_test_articles()
    check("mind. 15 Testartikel vorhanden", len(articles) >= 15)
    check("mind. 8 unterschiedliche Quellen", len({a.source for a in articles}) >= 8)
    check("jeder Artikel hat eine ID, Quelle, Titel, Text", all(a.id and a.source and a.title and a.text for a in articles))
    check("mind. ein source_dissenting=True Artikel", any(a.source_dissenting for a in articles))


def test_step2_clustering():
    print("Schritt 2: Clustering")
    articles = get_test_articles()
    threads = cluster_articles(articles, DEFAULT_CONFIG)
    check("mehr als 1, aber deutlich weniger Threads als Artikel", 1 < len(threads) < len(articles))
    check("jeder Artikel hat genau einen thread_id", all(a.thread_id for a in articles))
    check("jeder Thread hat mind. einen Artikel", all(len(t.article_ids) >= 1 for t in threads))
    ids_in_threads = sorted(aid for t in threads for aid in t.article_ids)
    check("jeder Artikel taucht in genau einem Thread auf (keine Duplikate/Verluste)",
          ids_in_threads == sorted(a.id for a in articles))
    # Bekannte, im Testdatensatz absichtlich angelegte Gruppierung:
    by_thread = {t.id: set(t.article_ids) for t in threads}
    expected_groups = [
        {"a01", "a02", "a03"}, {"a04", "a05", "a06"}, {"a09", "a10", "a11"},
        {"a07", "a08"}, {"a12", "a13"}, {"a14", "a15"}, {"a16"},
    ]
    actual_groups = list(by_thread.values())
    check("Clustering trifft exakt die im Testdatensatz angelegten 7 Gruppen",
          all(g in actual_groups for g in expected_groups) and len(actual_groups) == 7)


def test_step3_extraction():
    print("Schritt 3: LLM-Extraktion")
    articles, by_id, _ = None, None, None
    arts = get_test_articles()
    threads = cluster_articles(arts, DEFAULT_CONFIG)
    by_id = {a.id: a for a in arts}
    for th in threads:
        th_articles = [by_id[aid] for aid in th.article_ids]
        fields = extract_thread_fields(th_articles)
        check(f"Thread {sorted(th.article_ids)}: fact_core nicht leer", bool(fields["fact_core"]))
        check(f"Thread {sorted(th.article_ids)}: mind. ein Zeitleisten-Eintrag", len(fields["timeline"]) >= 1)
        check(f"Thread {sorted(th.article_ids)}: mind. ein Akteur", len(fields["actors"]) >= 1)
        # Ehrlichkeitsregel (Abschnitt 6): keine Wertungswoerter im Faktenkern.
        lowered = fields["fact_core"].lower()
        check(f"Thread {sorted(th.article_ids)}: fact_core enthaelt keine offensichtliche Wertung",
              not any(w in lowered for w in ["skandal", "katastrophal", "hervorragend", "meiner meinung"]))


def test_step4_tagging_and_score():
    print("Schritt 4+5: Tagging + Score")
    _, by_id, threads = build_pipeline()
    check("jeder Thread hat einen gueltigen Themenblock", all(t.topic in TOPIC_KEYS for t in threads))
    check("Scores liegen in [0, 1]", all(0.0 <= t.importance_score <= 1.0 for t in threads))
    opinion_articles = [a for a in by_id.values() if a.is_opinion]
    check("genau der markierte Kommentar (a08) ist als Meinung getaggt",
          {a.id for a in opinion_articles} == {"a08"})
    official = {t.topic for t in threads if t.has_official_action}
    check("Schritte mit klarer Kabinetts-/Gipfel-/KMK-Entscheidung als offizielle Handlung erkannt",
          {"wirtschaft", "sicherheit", "bildung", "demokratie", "klima"} <= official)
    check("Asylreform (nur Kommissionsvorschlag) NICHT als offizielle Handlung erkannt",
          not any(t.topic == "migration" and t.has_official_action for t in threads))


def test_step5_feeds():
    print("Schritt 5: Feeds")
    _, by_id, threads = build_pipeline()
    top = get_top_feed(threads, DEFAULT_CONFIG)
    check("Das-Wichtigste-Feed ist nicht leer, wenn Threads existieren", len(top) > 0)
    check("Das-Wichtigste-Feed haelt die konfigurierte Groesse ein", len(top) <= DEFAULT_CONFIG.top_feed_size)
    check("Das-Wichtigste-Feed ist nach Score absteigend sortiert",
          all(top[i].importance_score >= top[i + 1].importance_score for i in range(len(top) - 1)))

    user_wide = User(id="u1", pinned_topics=["wirtschaft"], perspective_breadth="wide")
    today = datetime.date(2026, 8, 19)
    feed = get_topic_feed(threads, by_id, "wirtschaft", user_wide, today=today)
    check("Themenblock-Feed 'wirtschaft' enthaelt genau den Bundeshaushalt-Thread", len(feed) == 1)
    check("neuer Thread ist als is_new markiert (noch nichts gesehen)", feed[0].is_new is True)

    user_seen = User(id="u2", last_seen_thread_ids=[feed[0].thread.id])
    feed2 = get_topic_feed(threads, by_id, "wirtschaft", user_seen, today=today)
    check("bereits gesehener Thread ist NICHT mehr als is_new markiert", feed2[0].is_new is False)

    # Perspektivenbreite: Regel darf NIE Daten entfernen (Abschnitt 6).
    nato_thread = next(t for t in threads if t.topic == "sicherheit")
    nato_articles = [by_id[aid] for aid in nato_thread.article_ids]
    narrow_user = User(id="u3", perspective_breadth="narrow")
    wide_user = User(id="u4", perspective_breadth="wide")
    narrow_view = apply_perspective_breadth(nato_articles, narrow_user)
    wide_view = apply_perspective_breadth(nato_articles, wide_user)
    check("perspective_breadth=narrow ENTFERNT die abweichende Quelle NICHT aus den Daten",
          len(narrow_view) == len(nato_articles))
    check("perspective_breadth=narrow klappt die abweichende Quelle nur EIN (collapsed=True)",
          any(v.collapsed for v in narrow_view))
    check("perspective_breadth=wide zeigt dieselbe Quelle nicht eingeklappt",
          not any(v.collapsed for v in wide_view))


def main():
    test_step1_models_and_fixtures()
    test_step2_clustering()
    test_step3_extraction()
    test_step4_tagging_and_score()
    test_step5_feeds()
    print(f"\n{PASSED} bestanden, {len(FAILED)} fehlgeschlagen.")
    if FAILED:
        print("Fehlgeschlagen:", FAILED)
        sys.exit(1)


if __name__ == "__main__":
    main()
