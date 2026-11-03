"""
Schritt 5 (zweiter Teil): zwei getrennte Feeds auf denselben Threads
(Bauanleitung Abschnitt 4).

"Das Wichtigste" ist FEST auf `config.top_feed_size` Eintraege begrenzt und
NICHT vom Nutzer konfigurierbar -- das ist eine bewusste, im Code
kommentierte Design-Entscheidung (Abschnitt 4 + 6: "darf minimiert, aber
nicht deaktiviert werden", "darf nicht auf null Eintraege reduzierbar
sein"). Es gibt in diesem Modul absichtlich KEINEN Parameter, der die
Groesse auf 0 setzen oder den Feed vollstaendig abschalten koennte.

Der Perspektivenbreite-Regler (Abschnitt 4 + 6) entfernt eine abweichende
Quelle NIE aus den Daten, sondern setzt bei niedrigster Stufe nur ein
"collapsed"-Anzeigeflag -- der zugrunde liegende Artikel bleibt jederzeit
abrufbar.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from pipeline.config import PipelineConfig, DEFAULT_CONFIG
from pipeline.models import Article, Thread, User


def _recency_score(thread: Thread, articles: list[Article], today: datetime.date) -> float:
    if not articles:
        return 0.0
    dates = [datetime.date.fromisoformat(a.published_at) for a in articles]
    most_recent = max(dates)
    age_days = max((today - most_recent).days, 0)
    # Exponentiell abklingend: taggenau, aber nicht schlagartig auf 0 --
    # ein 5 Tage alter Thread ist noch relevant, ein 30 Tage alter kaum.
    return round(pow(0.85, age_days), 4)


def rank_value(thread: Thread, articles: list[Article], today: datetime.date) -> float:
    """Kombination aus Wichtigkeits-Score und Aktualitaet fuer die
    Themenblock-Feeds (Abschnitt 4). Das 'Das Wichtigste'-Feed nutzt
    bewusst NUR den reinen Wichtigkeits-Score (siehe get_top_feed) --
    Aktualitaet soll dort nicht durchrutschen lassen, was wichtig, aber
    ein paar Tage alt ist."""
    return round(0.7 * thread.importance_score + 0.3 * _recency_score(thread, articles, today), 4)


def get_top_feed(
    threads: list[Thread], config: PipelineConfig = DEFAULT_CONFIG
) -> list[Thread]:
    """'Das Wichtigste': die `config.top_feed_size` Threads mit dem
    hoechsten Wichtigkeits-Score, UNABHAENGIG von gepinnten Themen. Immer
    sichtbar, nie leer solange ueberhaupt Threads existieren (Abschnitt 6)."""
    ranked = sorted(threads, key=lambda t: t.importance_score, reverse=True)
    return ranked[: config.top_feed_size]


@dataclass
class TopicFeedItem:
    thread: Thread
    is_new: bool
    rank: float


def get_topic_feed(
    threads: list[Thread],
    articles_by_id: dict[str, Article],
    topic_key: str,
    user: User,
    today: datetime.date | None = None,
) -> list[TopicFeedItem]:
    """Alle Threads eines Themenblocks, sortiert nach Wichtigkeit+Aktualitaet,
    mit 'neu seit letztem Login'-Markierung (Abschnitt 4)."""
    today = today or datetime.date.today()
    items = []
    for th in threads:
        if th.topic != topic_key:
            continue
        th_articles = [articles_by_id[aid] for aid in th.article_ids if aid in articles_by_id]
        items.append(TopicFeedItem(
            thread=th,
            is_new=th.id not in user.last_seen_thread_ids,
            rank=rank_value(th, th_articles, today),
        ))
    items.sort(key=lambda it: it.rank, reverse=True)
    return items


def count_new_per_topic(
    threads: list[Thread], user: User
) -> dict[str, int]:
    """Fuer die Dashboard-Kacheln: Anzahl neuer/aktualisierter Threads je
    gepinntem Themenblock seit dem letzten Login (Abschnitt 5)."""
    counts: dict[str, int] = {}
    for th in threads:
        if th.id not in user.last_seen_thread_ids and th.topic:
            counts[th.topic] = counts.get(th.topic, 0) + 1
    return counts


@dataclass
class SourceView:
    article: Article
    collapsed: bool


def apply_perspective_breadth(articles: list[Article], user: User) -> list[SourceView]:
    """Regler 2 (Abschnitt 4 + 6): bei perspective_breadth == 'narrow' wird
    eine abweichende Quelle nur EINGEKLAPPT dargestellt, NIE aus der
    zurueckgegebenen Liste entfernt -- der Aufrufer (Frontend) entscheidet
    anhand von `collapsed`, ob sie initial sichtbar ist."""
    narrow = user.perspective_breadth == "narrow"
    return [
        SourceView(article=a, collapsed=bool(narrow and a.source_dissenting))
        for a in articles
    ]
