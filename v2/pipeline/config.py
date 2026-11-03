"""
Alle Skalierungs-/Verhaltensregler an einem Ort (Muster aus dem v1-Prototyp
uebernommen, siehe ../../pipeline/config.py dort).
"""

from __future__ import annotations

from dataclasses import dataclass

from pipeline.models import Topic

# Bauanleitung Abschnitt 2: feste, stabile Liste von 8-12 groben Themen,
# bewusst das vom Nutzer selbst genannte Beispiel uebernommen -- die Liste
# ist bewusst klein und stabil, damit sie sich gut anpinnen laesst.
TOPICS: list[Topic] = [
    Topic("wirtschaft", "Wirtschaft & Finanzen"),
    Topic("migration", "Migration & Integration"),
    Topic("klima", "Klima & Energie"),
    Topic("sicherheit", "Sicherheit & Verteidigung"),
    Topic("soziales", "Soziales & Gesundheit"),
    Topic("bildung", "Bildung"),
    Topic("digitales", "Digitales"),
    Topic("aussenpolitik", "Außenpolitik & Europa"),
    Topic("demokratie", "Demokratie & Institutionen"),
]
TOPIC_KEYS = [t.key for t in TOPICS]
TOPIC_LABELS = {t.key: t.label for t in TOPICS}

DEFAULT_USER_ID = "default"  # Abschnitt 7: ein einziger fest hinterlegter Nutzer


@dataclass
class PipelineConfig:
    # Schritt 2, Clustering: Aehnlichkeits-Schwelle fuer TF-IDF-Cosine-
    # Similarity, ab der ein neuer Artikel einem bestehenden Thread statt
    # einem neuen Thread zugeordnet wird. Konfigurierbar, wie von der
    # Bauanleitung ausdruecklich verlangt ("als konfigurierbaren Parameter
    # beschreiben, statt sie hart zu verdrahten").
    cluster_similarity_threshold: float = 0.08

    # Schritt 5, Wichtigkeits-Score: Gewichtung der drei Signale.
    # Eigene, austauschbare Funktion (siehe tagging.py::importance_score),
    # damit die Gewichtung spaeter ohne Code-Umbau anpassbar ist.
    weight_sources: float = 0.4
    weight_official_action: float = 0.35
    weight_people_affected: float = 0.25

    # Schritt 4/5: "Das Wichtigste"-Kachel -- feste Groesse, siehe Abschnitt 6:
    # DARF NICHT auf 0 reduzierbar sein, deshalb hier eine Konstante statt
    # einer vom Nutzer aenderbaren Einstellung.
    top_feed_size: int = 6


DEFAULT_CONFIG = PipelineConfig()
