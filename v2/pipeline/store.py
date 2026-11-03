"""
Persistenz ueber SQLite (Python-Standardbibliothek `sqlite3`, keine ORM-
Abhaengigkeit noetig) -- eine der in Abschnitt 7 der Bauanleitung
ausdruecklich freigestellten technischen Entscheidungen ("eine relationale
Datenbank fuer die Kernentitaeten").
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from pipeline.models import Article, Thread, TimelineEntry, User

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    published_at TEXT NOT NULL,
    source_dissenting INTEGER NOT NULL DEFAULT 0,
    is_opinion INTEGER,
    thread_id TEXT
);
CREATE TABLE IF NOT EXISTS threads (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    fact_core TEXT NOT NULL DEFAULT '',
    timeline_json TEXT NOT NULL DEFAULT '[]',
    topic TEXT,
    actors_json TEXT NOT NULL DEFAULT '[]',
    article_ids_json TEXT NOT NULL DEFAULT '[]',
    importance_score REAL NOT NULL DEFAULT 0,
    n_independent_sources INTEGER NOT NULL DEFAULT 0,
    has_official_action INTEGER NOT NULL DEFAULT 0,
    people_affected_estimate INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    pinned_topics_json TEXT NOT NULL DEFAULT '[]',
    detail_level TEXT NOT NULL DEFAULT 'medium',
    perspective_breadth TEXT NOT NULL DEFAULT 'wide',
    last_seen_thread_ids_json TEXT NOT NULL DEFAULT '[]'
);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def reset_db(conn: sqlite3.Connection) -> None:
    conn.executescript("DELETE FROM articles; DELETE FROM threads;")
    conn.commit()


def save_articles(conn: sqlite3.Connection, articles: list[Article]) -> None:
    conn.executemany(
        """INSERT INTO articles (id, source, url, title, text, published_at,
               source_dissenting, is_opinion, thread_id)
           VALUES (?,?,?,?,?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET
               is_opinion=excluded.is_opinion, thread_id=excluded.thread_id""",
        [
            (a.id, a.source, a.url, a.title, a.text, a.published_at,
             int(a.source_dissenting), a.is_opinion, a.thread_id)
            for a in articles
        ],
    )
    conn.commit()


def save_threads(conn: sqlite3.Connection, threads: list[Thread]) -> None:
    conn.executemany(
        """INSERT INTO threads (id, title, fact_core, timeline_json, topic,
               actors_json, article_ids_json, importance_score,
               n_independent_sources, has_official_action, people_affected_estimate)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET
               title=excluded.title, fact_core=excluded.fact_core,
               timeline_json=excluded.timeline_json, topic=excluded.topic,
               actors_json=excluded.actors_json, article_ids_json=excluded.article_ids_json,
               importance_score=excluded.importance_score,
               n_independent_sources=excluded.n_independent_sources,
               has_official_action=excluded.has_official_action,
               people_affected_estimate=excluded.people_affected_estimate""",
        [
            (
                th.id, th.title, th.fact_core,
                json.dumps([e.__dict__ for e in th.timeline], ensure_ascii=False),
                th.topic, json.dumps(th.actors, ensure_ascii=False),
                json.dumps(th.article_ids, ensure_ascii=False),
                th.importance_score, th.n_independent_sources,
                int(th.has_official_action), th.people_affected_estimate,
            )
            for th in threads
        ],
    )
    conn.commit()


def save_user(conn: sqlite3.Connection, user: User) -> None:
    conn.execute(
        """INSERT INTO users (id, pinned_topics_json, detail_level,
               perspective_breadth, last_seen_thread_ids_json)
           VALUES (?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET
               pinned_topics_json=excluded.pinned_topics_json,
               detail_level=excluded.detail_level,
               perspective_breadth=excluded.perspective_breadth,
               last_seen_thread_ids_json=excluded.last_seen_thread_ids_json""",
        (user.id, json.dumps(user.pinned_topics, ensure_ascii=False),
         user.detail_level, user.perspective_breadth,
         json.dumps(user.last_seen_thread_ids, ensure_ascii=False)),
    )
    conn.commit()


def _row_to_article(row: sqlite3.Row) -> Article:
    return Article(
        id=row["id"], source=row["source"], url=row["url"], title=row["title"],
        text=row["text"], published_at=row["published_at"],
        source_dissenting=bool(row["source_dissenting"]),
        is_opinion=(bool(row["is_opinion"]) if row["is_opinion"] is not None else None),
        thread_id=row["thread_id"],
    )


def _row_to_thread(row: sqlite3.Row) -> Thread:
    return Thread(
        id=row["id"], title=row["title"], fact_core=row["fact_core"],
        timeline=[TimelineEntry(**e) for e in json.loads(row["timeline_json"])],
        topic=row["topic"], actors=json.loads(row["actors_json"]),
        article_ids=json.loads(row["article_ids_json"]),
        importance_score=row["importance_score"],
        n_independent_sources=row["n_independent_sources"],
        has_official_action=bool(row["has_official_action"]),
        people_affected_estimate=row["people_affected_estimate"],
    )


def load_articles(conn: sqlite3.Connection) -> list[Article]:
    return [_row_to_article(r) for r in conn.execute("SELECT * FROM articles")]


def load_threads(conn: sqlite3.Connection) -> list[Thread]:
    return [_row_to_thread(r) for r in conn.execute("SELECT * FROM threads")]


def load_thread(conn: sqlite3.Connection, thread_id: str) -> Thread | None:
    row = conn.execute("SELECT * FROM threads WHERE id=?", (thread_id,)).fetchone()
    return _row_to_thread(row) if row else None


def load_articles_for_thread(conn: sqlite3.Connection, thread_id: str) -> list[Article]:
    rows = conn.execute("SELECT * FROM articles WHERE thread_id=?", (thread_id,))
    return [_row_to_article(r) for r in rows]


def load_user(conn: sqlite3.Connection, user_id: str) -> User:
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not row:
        return User(id=user_id)
    return User(
        id=row["id"], pinned_topics=json.loads(row["pinned_topics_json"]),
        detail_level=row["detail_level"], perspective_breadth=row["perspective_breadth"],
        last_seen_thread_ids=json.loads(row["last_seen_thread_ids_json"]),
    )
