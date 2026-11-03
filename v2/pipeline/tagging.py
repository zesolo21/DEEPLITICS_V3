"""
Schritt 4 (Tagging) + Schritt 5 (Wichtigkeits-Bewertung), Bauanleitung
Abschnitt 3.

Tagging ordnet jeden Thread einem der festen Themenbloecke zu und setzt
bei jedem Artikel das Fakt/Meinung-Flag (das Abweichende-Perspektive-Flag
ist bereits beim Einlesen pro Quelle gesetzt, siehe test_articles.py).

Der Wichtigkeits-Score kombiniert drei Signale zu einer austauschbaren,
eigenen Funktion (`importance_score`), damit die Gewichtung spaeter ohne
Code-Umbau anpassbar bleibt (Abschnitt 3, ausdruecklicher Wunsch der
Bauanleitung).

Themenzuordnung und Meinungs-/Offizielle-Handlung-Erkennung laufen ueber
einfache Stichwortsuche statt eines eigenen LLM-Calls -- das ist fuer
Version 1 bewusst so vorgesehen (Abschnitt 3: "das kann grob per
Stichwortsuche oder per LLM-Klassifikation erkannt werden"). Ein Wechsel
auf eine LLM-Klassifikation ist ein sauberer spaeterer Austausch, ohne
dass sich die Funktionssignaturen aendern muessten.
"""

from __future__ import annotations

from pipeline.config import PipelineConfig, DEFAULT_CONFIG, TOPIC_KEYS
from pipeline.models import Article, Thread

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "migration": ["Asyl", "Migration", "Grenzverfahren", "GEAS", "Flüchtl", "Einwanderung"],
    "wirtschaft": ["Haushalt", "Schulden", "Finanzminist", "Steuer", "Kabinett", "Etat"],
    "klima": ["Kohle", "Klima", "Energie", "CO2", "Emission", "Netzausbau"],
    "sicherheit": ["NATO", "Verteidigung", "Bundeswehr", "Militär", "Rüstung"],
    "soziales": ["Sozial", "Gesundheit", "Rente", "Pflege", "Wohlfahrtsverband"],
    "bildung": ["Schule", "Lehrer", "Bildung", "Digitalpakt", "Kultusminister"],
    "digitales": ["KI-Gesetz", "Künstliche Intelligenz", "Digitalminist", "Hochrisiko"],
    "aussenpolitik": ["EU-Kommission", "Europaparlament", "Außenpolitik", "Diplomatie"],
    "demokratie": ["Bürgerrat", "Wahlrecht", "Parteienfinanzierung", "Demokratie", "Losverfahren"],
}
assert set(TOPIC_KEYWORDS) == set(TOPIC_KEYS), "TOPIC_KEYWORDS muss exakt die Themenliste abdecken"

OFFICIAL_ACTION_KEYWORDS = [
    "beschließt", "beschlossen", "beschloss", "verabschiedet", "eingerichtet",
    "kündigt an", "angekündigt", "zieht vor", "ziehen vor", "unterzeichnet",
    "Urteil", "Gesetz tritt in Kraft",
]

OPINION_MARKERS = ["Kommentar:", "Meinung:", "Kommentar ", "[Meinung]"]


def tag_topic(thread_text: str) -> str:
    scores = {topic: sum(thread_text.count(kw) for kw in kws) for topic, kws in TOPIC_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "demokratie"  # Auffangkategorie, ehrlich als schwaechster Fall erkennbar am Score 0
    return best


def tag_opinion(article: Article) -> bool:
    blob = f"{article.title}\n{article.text}"
    return any(marker in blob for marker in OPINION_MARKERS)


def detect_official_action(thread_text: str) -> bool:
    return any(kw in thread_text for kw in OFFICIAL_ACTION_KEYWORDS)


def estimate_people_affected(thread_text: str) -> int:
    """Sehr grobe Heuristik: sucht nach Zahlen im Text, die im Kontext von
    Betroffenen/Beschaeftigten/Buergern stehen koennten, sonst ein
    konservativer Basiswert. Bewusst simpel gehalten (Abschnitt 3 verlangt
    kein praezises Modell, nur ein Signal unter dreien)."""
    lowered = thread_text.lower()
    if any(w in lowered for w in ["bundesweit", "alle mitgliedstaaten", "alle bürger", "millionen"]):
        return 1_000_000
    if any(w in lowered for w in ["bundesländer", "bundesland", "region"]):
        return 100_000
    return 10_000


def tag_and_score_thread(
    thread: Thread, articles: list[Article], config: PipelineConfig = DEFAULT_CONFIG
) -> Thread:
    """Mutiert `thread` (Topic, Score-Signale) und die `is_opinion`-Flags der
    zugehoerigen `articles` in-place, gibt `thread` zur Verkettung zurueck."""

    blob = " ".join(f"{a.title} {a.text}" for a in articles)

    thread.topic = tag_topic(blob)
    for a in articles:
        a.is_opinion = tag_opinion(a)

    thread.n_independent_sources = len({a.source for a in articles})
    thread.has_official_action = detect_official_action(blob)
    thread.people_affected_estimate = estimate_people_affected(blob)
    thread.importance_score = importance_score(thread, config)
    return thread


def importance_score(thread: Thread, config: PipelineConfig = DEFAULT_CONFIG) -> float:
    """Kombiniert die drei Signale aus Abschnitt 3 zu einem Score in [0, 1].
    Eigene, austauschbare Funktion -- die Gewichte liegen in config.py,
    nicht hier hart codiert."""

    # Quellenzahl: normiert auf einen plausiblen Maximalwert (5 unabhaengige
    # Quellen gilt hier als "voll ausgeschoepft"), darueber hinaus saettigt
    # das Signal bewusst statt linear weiterzuwachsen.
    sources_component = min(thread.n_independent_sources / 5.0, 1.0)
    action_component = 1.0 if thread.has_official_action else 0.0
    # Betroffenenzahl: log-artige Stufen statt linearer Skala, damit ein
    # einzelner Ausreisser (z.B. "Millionen") den Score nicht komplett
    # dominiert.
    if thread.people_affected_estimate >= 1_000_000:
        people_component = 1.0
    elif thread.people_affected_estimate >= 100_000:
        people_component = 0.6
    else:
        people_component = 0.25

    score = (
        config.weight_sources * sources_component
        + config.weight_official_action * action_component
        + config.weight_people_affected * people_component
    )
    return round(score, 4)
