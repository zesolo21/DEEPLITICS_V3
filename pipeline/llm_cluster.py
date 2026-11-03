"""
LLM-basiertes Clustering: ersetzt die TF-IDF+Cosine-Distanz aus cluster.py
mit echtem semantischem Verstaendnis durch das Sprachmodell selbst --
nutzt denselben `ANTHROPIC_API_KEY`, der ohnehin schon fuer die
Story-Synthese gesetzt ist, keine zusaetzliche Einrichtung noetig.

WARUM (gefunden 23.08.2026): TF-IDF gruppiert nach WORT-UEBERLAPPUNG, nicht
nach tatsaechlicher Bedeutung. Zwei Artikel ueber DASSELBE Ereignis, aber
mit unterschiedlichem Blickwinkel/Wortschatz formuliert (z.B. "USA
verhaengen 50%-Zoelle auf Kanada" und "Gespraeche gescheitert, Kanada
kuendigt Vergeltung an" -- beides derselbe Zollstreit), koennen unter dem
TF-IDF-Distanz-Schwellenwert als ZWEI getrennte Cluster landen, obwohl sie
eindeutig zur selben Story gehoeren. Das Modell selbst versteht das ohne
Schwellenwert-Tuning richtig.

Ansatz: EIN einzelner (billiger) API-Aufruf mit nur Titel+Kurz-Snippet ALLER
gededuplizierten Artikel (kein Volltext -- haelt den Aufruf klein/billig
verglichen mit den eigentlichen Synthese-Aufrufen). Das Modell gibt direkt
Gruppenzuordnungen zurueck (Artikel-Indices pro Cluster + Kurzlabel).

Fallback: OHNE API-Key (oder bei einem Fehler/ungueltiger Modellantwort)
gibt `llm_cluster_articles` `None` zurueck: der Aufrufer (run_pipeline.py)
faellt dann automatisch auf das bisherige TF-IDF-Clustering
(cluster.py::cluster_articles) zurueck, damit ein einzelner Cluster-Fehler
NIE den ganzen Lauf verhindert.
"""

from __future__ import annotations

import os
import sys

from pipeline.config import DEFAULT_CONFIG, PipelineConfig
from pipeline.synthesize_story import _create_message, _extract_json_text, _parse_json_loose

LLM_CLUSTER_PROMPT_TEMPLATE = """Du bekommst eine nummerierte Liste politischer Nachrichtenartikel (Index, Quelle, Titel, Kurz-Ausschnitt).

Gruppiere sie zu Storys: Artikel gehoeren NUR dann in dieselbe Gruppe, wenn sie ueber DASSELBE konkrete reale Ereignis / denselben Vorgang berichten (nicht nur dasselbe grobe Thema oder Land). Verschiedene Teilaspekte/Blickwinkel DESSELBEN Ereignisses gehoeren in DIESELBE Gruppe (z.B. "Zoelle verhaengt" und "Vergeltung angekuendigt" zum selben Zollstreit sind EINE Story, nicht zwei).

ARTIKEL:
{articles_block}

Gib AUSSCHLIESSLICH valides JSON zurueck, keine Markdown-Codeblock-Markierung, kein Begleittext:
{{
  "clusters": [
    {{"label": "kurzes Schlagwort der Story", "indices": [0, 5, 12]}}
  ]
}}

Nur Gruppen mit >= 2 Artikeln aufnehmen. Jeder Index taucht in HOECHSTENS einer Gruppe auf. Artikel, die zu keiner Story mit mindestens einem weiteren Artikel passen, einfach weglassen (nicht als Ein-Artikel-Gruppe auffuehren).
"""


def _build_articles_block(articles: list[dict]) -> str:
    lines = []
    for i, a in enumerate(articles):
        snippet = (a.get("summary") or a.get("text") or "").replace("\n", " ")[:200]
        lines.append(f"[{i}] ({a.get('source', '?')}) {a.get('title', '?')} -- {snippet}")
    return "\n".join(lines)


def llm_cluster_articles(
    articles: list[dict],
    config: PipelineConfig = DEFAULT_CONFIG,
) -> list[list[dict]] | None:
    """Gibt Cluster zurueck (Liste von Artikel-Listen, groesste zuerst,
    passend zum Rueckgabeformat von cluster.py::cluster_articles), oder
    `None` wenn kein API-Zugriff besteht oder die Modellantwort nicht
    verwertbar war -- der Aufrufer faellt dann auf TF-IDF zurueck."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[info] Kein ANTHROPIC_API_KEY -- LLM-Clustering übersprungen, Fallback auf TF-IDF.", file=sys.stderr)
        return None
    if len(articles) < 2:
        return [articles] if articles else []

    prompt = LLM_CLUSTER_PROMPT_TEMPLATE.format(articles_block=_build_articles_block(articles))

    try:
        resp = _create_message(
            api_key=api_key,
            model=config.model,
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
            tools=None,
        )
        data = _parse_json_loose(_extract_json_text(resp))
    except Exception as exc:  # noqa: BLE001 - Clustering darf den Lauf nie abbrechen
        print(f"[warn] LLM-Clustering fehlgeschlagen ({exc}), Fallback auf TF-IDF.", file=sys.stderr)
        return None

    clusters: list[list[dict]] = []
    seen: set[int] = set()
    for c in data.get("clusters", []):
        idxs = [
            i for i in c.get("indices", [])
            if isinstance(i, int) and 0 <= i < len(articles) and i not in seen
        ]
        if len(idxs) < 2:
            continue
        seen.update(idxs)
        clusters.append([articles[i] for i in idxs])

    if not clusters:
        print("[warn] LLM-Clustering lieferte keine verwertbaren Gruppen, Fallback auf TF-IDF.", file=sys.stderr)
        return None

    print(
        f"[info] LLM-Clustering: {len(clusters)} Gruppen aus {len(articles)} Artikeln "
        f"({len(seen)} zugeordnet, {len(articles) - len(seen)} ohne Gruppe).",
        file=sys.stderr,
    )
    return sorted(clusters, key=len, reverse=True)
