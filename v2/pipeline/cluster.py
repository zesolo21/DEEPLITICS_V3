"""
Schritt 2: Clustering -- gruppiert neue Artikel zu bestehenden oder neuen
Threads (Bauanleitung Abschnitt 3).

Nutzt TF-IDF-Vektoren (sciki-learn) + eine konfigurierbare Cosine-
Similarity-Schwelle statt echter Sentence-Embeddings -- eine bewusste,
im README dokumentierte Vereinfachung, konsistent mit dem Rest des
Projekts (siehe v2/README.md, Abschnitt "Wichtige ... Vereinfachungen").
Die Funktionssignatur ist bewusst stabil gehalten, damit ein Austausch
gegen echte Embeddings spaeter moeglich ist, ohne Aufrufer anzufassen.

Verarbeitet Artikel in chronologischer Reihenfolge (wie ein echter
Ingestion-Strom) und ordnet jeden neuen Artikel entweder einem
bestehenden, inhaltlich naeheren Thread zu, oder eroeffnet einen neuen.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from pipeline.config import PipelineConfig, DEFAULT_CONFIG
from pipeline.models import Article, Thread


def _article_text(a: Article) -> str:
    # Titel doppelt gewichten (einfacher Trick: Titeltext anhaengen), weil
    # er meist das praeziseste Signal fuer das Thema eines Artikels ist.
    return f"{a.title}\n{a.title}\n{a.text}"


def cluster_articles(
    articles: list[Article], config: PipelineConfig = DEFAULT_CONFIG
) -> list[Thread]:
    """Gruppiert `articles` zu Threads. Mutiert `article.thread_id` in-place
    und gibt die entstandenen Threads zurueck (noch ohne Faktenkern/Tagging,
    das passiert in den folgenden Schritten extract.py/tagging.py)."""

    if not articles:
        return []

    ordered = sorted(articles, key=lambda a: (a.published_at, a.id))
    texts = [_article_text(a) for a in ordered]

    # Unigramme statt Bigramme: bei kurzen Nachrichtentexten verduennen
    # Bigramme das Aehnlichkeitssignal zu stark (empirisch an den
    # Testartikeln geprueft, siehe tests/test_pipeline.py::test_clustering).
    vectorizer = TfidfVectorizer(
        max_df=0.9, min_df=1, ngram_range=(1, 1), stop_words=_GERMAN_STOPWORDS
    )
    matrix = vectorizer.fit_transform(texts)

    threads: list[Thread] = []
    # Fuer jeden Thread: Liste der Zeilenindizes seiner Artikel in `matrix`,
    # um bei Bedarf einen Centroid-Vektor (Mittelwert) zu berechnen.
    thread_row_indices: dict[str, list[int]] = {}

    for row_idx, article in enumerate(ordered):
        best_thread_id = None
        best_sim = 0.0
        if threads:
            row_vec = matrix[row_idx]
            for th in threads:
                rows = thread_row_indices[th.id]
                centroid = matrix[rows].mean(axis=0)
                centroid = np.asarray(centroid)
                sim = float(cosine_similarity(row_vec, centroid)[0][0])
                if sim > best_sim:
                    best_sim = sim
                    best_thread_id = th.id

        if best_thread_id is not None and best_sim >= config.cluster_similarity_threshold:
            article.thread_id = best_thread_id
            thread_row_indices[best_thread_id].append(row_idx)
            th = next(t for t in threads if t.id == best_thread_id)
            th.article_ids.append(article.id)
        else:
            new_thread = Thread(
                id=f"th-{uuid.uuid4().hex[:8]}",
                title=article.title,  # vorlaeufiger Titel, Schritt 3 verfeinert ihn ggf.
                article_ids=[article.id],
            )
            threads.append(new_thread)
            thread_row_indices[new_thread.id] = [row_idx]
            article.thread_id = new_thread.id

    return threads


# Minimal-Stopwortliste fuer deutsche Nachrichtentexte -- scikit-learn hat
# keine eingebaute deutsche Liste, eine vollstaendige linguistische Liste
# ist fuer TF-IDF-Clustering aber nicht noetig, die haeufigsten
# Funktionswoerter reichen, um sie aus den Vektoren herauszuhalten.
_GERMAN_STOPWORDS = [
    "der", "die", "das", "den", "dem", "des", "ein", "eine", "einer", "eines",
    "einem", "einen", "und", "oder", "aber", "auch", "auf", "aus", "bei",
    "bis", "durch", "fuer", "für", "gegen", "im", "in", "mit", "nach", "sich",
    "sie", "sind", "sind", "sowie", "um", "und", "von", "vor", "wie", "wird",
    "werden", "wurde", "wurden", "zu", "zum", "zur", "ist", "war", "waren",
    "haben", "hat", "hatte", "als", "an", "am", "dass", "es", "er", "man",
    "noch", "nicht", "nur", "so", "sei", "seit", "soll", "sollen", "kann",
    "koennen", "können", "laut", "unter", "ueber", "über", "diese", "dieser",
    "dieses", "diesen", "einige", "mehrere", "erste", "ersten",
]
