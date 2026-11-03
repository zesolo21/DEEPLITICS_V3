"""
Kern-Datenmodell fuer das Thread-basierte System (Bauanleitung Abschnitt 2).

Bewusst als einfache dataclasses statt eines schweren ORMs gehalten, damit
das Modell unabhaengig von der konkreten Persistenz (hier: SQLite in
store.py) lesbar und testbar bleibt. store.py uebernimmt die Umsetzung
in/aus SQLite-Zeilen.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Article:
    """Ein einzelner eingelesener Nachrichtenartikel."""

    id: str
    source: str
    url: str
    title: str
    text: str
    published_at: str  # ISO-Datum, z.B. "2026-08-17"
    # "abweichende Perspektive ja/nein" -- das bewusst vereinfachte Ersatz-
    # Flag fuer den in V1 explizit NICHT gebauten zweiachsigen politischen
    # Kompass (Bauanleitung Abschnitt 1).
    source_dissenting: bool = False
    # Wird in Schritt 4 (Tagging) gesetzt: Faktenmeldung oder Meinungsstueck.
    is_opinion: Optional[bool] = None
    # Wird in Schritt 2 (Clustering) gesetzt: Referenz auf genau einen Thread.
    thread_id: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TimelineEntry:
    date: str
    description: str


@dataclass
class Thread:
    """Ein Ereignisstrang: mehrere Artikel, die inhaltlich zusammengehoeren."""

    id: str
    title: str
    fact_core: str = ""  # Faktenkern, 2-3 Saetze, vom LLM generiert
    timeline: list[TimelineEntry] = field(default_factory=list)
    topic: Optional[str] = None  # Referenz auf genau einen Themenblock
    actors: list[str] = field(default_factory=list)
    article_ids: list[str] = field(default_factory=list)
    importance_score: float = 0.0
    # Einzelsignale, die in den Score einfliessen (Abschnitt 3, Schritt 5) --
    # separat gehalten, damit die Gewichtung spaeter nachjustierbar bleibt,
    # ohne den Score-Berechnungsweg zu verschleiern.
    n_independent_sources: int = 0
    has_official_action: bool = False
    people_affected_estimate: int = 0

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class Topic:
    """Ein Eintrag aus der festen, stabilen Themenliste (Abschnitt 2)."""

    key: str
    label: str


@dataclass
class Actor:
    """Eine Person, Partei oder Institution, die Threads referenzieren."""

    name: str
    description: str = ""


@dataclass
class User:
    """Bauanleitung Abschnitt 7: ein einziger fest hinterlegter Nutzer reicht,
    kein Login-System in Version 1."""

    id: str
    pinned_topics: list[str] = field(default_factory=list)
    # Regler 1: nur die Darstellung (wie viel Text angezeigt wird), NICHT
    # die Auswahl der Threads selbst (Abschnitt 4).
    detail_level: str = "medium"  # "short" | "medium" | "full"
    # Regler 2: steuert, ob eine abweichende Quelle zusaetzlich angezeigt
    # wird -- bei niedrigster Stufe eingeklappt, NIE vollstaendig entfernt
    # (Abschnitt 6: technisch erzwungene Regel).
    perspective_breadth: str = "wide"  # "narrow" | "wide"
    last_seen_thread_ids: list[str] = field(default_factory=list)
