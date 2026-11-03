"""
Clustering: viele Einzelartikel (potenziell aus verschiedenen Quellen /
Ländern, die über dasselbe Ereignis berichten) zu Gruppen zusammenfassen,
die dann jeweils zu EINER Story synthetisiert werden.

MVP-Ansatz (bewusst leichtgewichtig, kein Embedding-API-Call nötig):
TF-IDF über Titel+Summary, dann Agglomeratives Clustering auf Basis von
Cosine-Distanz mit einem Schwellenwert. Reicht für "gleiche Story, andere
Quelle" gut aus, weil politische Nachrichten zum selben Ereignis meist
überlappende Eigennamen/Begriffe benutzen (gleiche Personen, Länder,
Institutionen).

SKALIERUNG: `AgglomerativeClustering` mit "average"-Linkage braucht eine
volle N×N-Distanzmatrix (`tfidf.toarray()` unten), Speicher/Laufzeit sind
also O(n^2). Für ein paar hundert bis ~1500 Artikel pro Lauf ist das
unproblematisch (Sekunden, niedrige zweistellige MB), bei mehreren tausend
wird es schnell teuer. `MAX_ARTICLES_FOR_CLUSTERING` (aus `config.py`,
siehe dort) kappt DESHALB die Eingabe VOR dem Clustering, statt dass ein
großer Lauf unkontrolliert langsam wird oder den Speicher sprengt: die
neuesten Artikel (nach `published`, wo bekannt) werden bevorzugt behalten.
Für "wirklich groß" (zehntausende Artikel/Tag) ist der nächste Schritt
echte Satz-Embeddings + ein inkrementeller/approximativer Algorithmus
(z.B. HDBSCAN auf einem Vektorindex) statt des O(n^2)-Ansatzes hier, die
Funktionssignatur von `cluster_articles` bleibt dafür bewusst stabil.
"""

from __future__ import annotations

import sys

from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer

from pipeline.config import DEFAULT_CONFIG, PipelineConfig

# Rückwärtskompatibler Re-Export, mehrere Module importieren das bisher
# direkt von hier (`from pipeline.cluster import MIN_SOURCES_FOR_STORY`).
MIN_SOURCES_FOR_STORY = DEFAULT_CONFIG.min_sources_for_story


def _cap_articles_for_clustering(
    articles: list[dict], max_articles: int
) -> list[dict]:
    """Kappt VOR dem O(n^2)-Clustering, bevorzugt die neuesten Artikel
    (nach `published`-Feld, wo geparst werden kann, sonst Reihenfolge
    unverändert = FIFO-Fallback)."""
    if len(articles) <= max_articles:
        return articles

    print(
        f"[warn] {len(articles)} Artikel überschreiten das Cluster-Limit "
        f"({max_articles}), kappe auf die neuesten {max_articles}.",
        file=sys.stderr,
    )
    # published ist ein Roh-String aus RSS (nicht immer ISO), daher nur
    # eine grobe, best-effort Sortierung: Artikel mit `published` zuerst
    # (neueste zuerst über String-Vergleich, funktioniert für ISO-artige
    # Formate gut genug für diesen Zweck), Artikel ohne Datum ans Ende.
    with_date = [a for a in articles if a.get("published")]
    without_date = [a for a in articles if not a.get("published")]
    with_date.sort(key=lambda a: a["published"], reverse=True)
    return (with_date + without_date)[:max_articles]


def cluster_articles(
    articles: list[dict],
    distance_threshold: float | None = None,
    text_key: str = "combined_text",
    config: PipelineConfig = DEFAULT_CONFIG,
) -> list[list[dict]]:
    """Gruppiert Artikel. Gibt eine Liste von Clustern zurück, jeder
    Cluster ist eine Liste von Artikel-dicts, größte Cluster zuerst."""
    if distance_threshold is None:
        distance_threshold = config.cluster_distance_threshold

    articles = _cap_articles_for_clustering(
        articles, config.max_articles_for_clustering
    )

    if len(articles) < 2:
        return [articles] if articles else []

    texts = [a.get(text_key) or f"{a.get('title', '')} {a.get('summary', '')}" for a in articles]

    vectorizer = TfidfVectorizer(stop_words="english", max_features=20000, ngram_range=(1, 2))
    tfidf = vectorizer.fit_transform(texts)

    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=distance_threshold,
        metric="cosine",
        linkage="average",
    )
    labels = clustering.fit_predict(tfidf.toarray())

    clusters: dict[int, list[dict]] = {}
    for label, article in zip(labels, articles):
        clusters.setdefault(int(label), []).append(article)

    # Größte Cluster zuerst (interessanter für "große" Storys, und
    # `run_pipeline.py` nutzt diese Reihenfolge auch, um bei
    # `max_stories_per_run` die größten/best-belegten Storys zu bevorzugen).
    return sorted(clusters.values(), key=len, reverse=True)


if __name__ == "__main__":
    import json
    from pathlib import Path

    in_path = Path(__file__).resolve().parent.parent / "data" / "articles_raw.json"
    articles = json.loads(in_path.read_text())
    clusters = cluster_articles(articles)
    for i, c in enumerate(clusters):
        print(f"--- Cluster {i} ({len(c)} articles) ---", file=sys.stderr)
        for a in c:
            print(f"  [{a['source']}] {a['title']}", file=sys.stderr)
