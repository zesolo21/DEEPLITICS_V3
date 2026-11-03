"""
Zentrale, formalisierte Konfiguration der Pipeline (Version 6).

Vorher lagen die "Skalierungs-Regler" verstreut als Magic Numbers in
cluster.py/synthesize_story.py/run_pipeline.py (z.B. `max_articles_per_source
= 8` als Funktionsparameter-Default in run_pipeline.py, `distance_threshold
= 0.75` in cluster.py, `max_tokens=6000` in synthesize_story.py). Diese
Datei bündelt sie an EINEM Ort, mit Begründung, damit das Verhalten bei
wachsender Datenmenge (mehr Quellen, mehr Artikel pro Lauf, mehr Storys
gleichzeitig) über ein paar dokumentierte Zahlen gesteuert werden kann,
statt bei jedem Skalierungsschritt Code an mehreren Stellen anzufassen.

Kernidee für Skalierbarkeit: die Kosten/Latenz PRO STORY sind absichtlich
UNABHÄNGIG von der Cluster-Größe gedeckelt (`max_articles_per_story`,
`max_chars_per_article`), damit ein Cluster mit 40 Artikeln nicht 10x so
teuer ist wie einer mit 4. Die Kosten/Latenz DER GESAMTEN Pipeline skalieren
dann näherungsweise LINEAR mit der Anzahl Storys (nicht mit der Anzahl
Rohartikel), und `synthesis_concurrency` steuert, wie viel davon parallel
statt seriell passiert.

`research_depth` ist der wichtigste Hebel für "viele Storys, wenig Kosten":
  - "full": inkl. echter Web-Recherche (Primärquellen, Marktkorrelation),
    teurer und langsamer pro Story, aber inhaltlich vollständig.
  - "lite": überspringt Primärquellen-/Marktrecherche komplett (kein
    Tool-Aufruf, kürzerer Prompt, kürzere Antwort), für schnelle/günstige
    Testläufe mit vielen Storys oder als genereller Default, wenn die
    Web-Recherche-Tiefe nicht gebraucht wird. `political_theory` bleibt in
    beiden Modi erhalten, da es reines Modellwissen ist und kaum Kosten
    verursacht.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ResearchDepth = Literal["full", "lite"]


@dataclass(frozen=True)
class PipelineConfig:
    # --- Sammlung (fetch_feeds.py / run_pipeline.py) ---
    max_articles_per_source: int = 8
    # Volltext-Extraktion ist pro Artikel ein serieller HTTP-Request
    # (`extract_article.py::fetch_and_extract`), bei hunderten Artikeln
    # dominiert das sonst die Laufzeit der ganzen Pipeline. Parallelisiert
    # über einen Thread-Pool, analog zu `synthesis_concurrency` unten.
    fetch_concurrency: int = 8
    # Sicherheitsgrenze für das Clustering, s. cluster.py-Docstring: der
    # TF-IDF+Agglomerative-Ansatz ist O(n^2) im Speicher/Laufzeit, bei sehr
    # vielen Rohartikeln wird VOR dem Clustering gekappt statt dass der
    # Lauf unkontrolliert langsam wird oder OOM geht.
    max_articles_for_clustering: int = 1500

    # --- Clustering (cluster.py) ---
    cluster_distance_threshold: float = 0.75
    min_sources_for_story: int = 2

    # --- Synthese-INPUT, deckelt Prompt-Größe pro Story ---
    # Repräsentative Artikel je Cluster (round-robin über Quellen für
    # Diversität), NICHT alle Artikel eines Clusters, s. synthesize_story.py
    # ::select_representative_articles.
    max_articles_per_story: int = 6
    # Volltext-Cap je Artikel im Prompt (Zeichen, nicht Tokens, als
    # einfache konservative Näherung, ca. 3-4 Zeichen/Token im Englischen).
    max_chars_per_article: int = 3000

    # --- Synthese-OUTPUT ---
    model: str = "claude-sonnet-4-5"
    max_output_tokens: int = 6000
    research_depth: ResearchDepth = "lite"

    # --- Skalierung über viele Storys hinweg (run_pipeline.py) ---
    # None = alle Multi-Source-Cluster verarbeiten. Für Tests/Kostenkontrolle
    # auf eine feste Zahl setzen, unabhängig davon wie viele Cluster
    # entstehen.
    max_stories_per_run: int | None = None
    # Story-AKKUMULATION (Nutzerwunsch 23.08.2026): bestehende Storys in
    # data/stories.json bleiben über Läufe hinweg erhalten, neue werden
    # davorgestellt (neueste zuerst), statt sie komplett zu überschreiben,
    # s. run_pipeline.py::_merge_stories. Dieses Feld deckelt die
    # GESAMTZAHL gespeicherter Storys (älteste fliegen zuerst raus), damit
    # data/stories.json nicht über Monate hinweg unbegrenzt wächst. None
    # = kein Deckel (uneingeschränktes Wachstum).
    max_total_stories: int | None = 150
    # parallele API-Calls; die Anthropic-API hat pro Organisation ein
    # Rate-Limit, ein niedriger konservativer Default vermeidet 429s ohne
    # dass man das erst tunen muss.
    synthesis_concurrency: int = 4
    # Selbstkorrektur-Versuche, wenn die Modellantwort kein valides JSON
    # ist (kommt vor allem bei sehr langen Tool-Use-Antworten vor).
    max_json_retries: int = 1

    # --- Web-Recherche (Primärquellen/Markt), nur in research_depth="full" ---
    enable_web_search: bool = True
    # Deckelt Tool-Aufrufe PRO STORY, damit eine einzelne Story nicht durch
    # exzessives Nachsuchen Zeit/Kosten der ganzen Charge dominiert.
    web_search_max_uses: int = 6


DEFAULT_CONFIG = PipelineConfig()

# Vorgefertigtes Profil für große/günstige Testläufe (viele Storys, wenig
# Tiefe): keine Web-Recherche, kürzere Artikel-Ausschnitte, mehr Parallelität.
LITE_SCALE_CONFIG = PipelineConfig(
    max_articles_per_story=4,
    max_chars_per_article=1800,
    # WICHTIG (gefunden im ersten echten API-Testlauf, 18.08.2026): das
    # volle Story-JSON-Schema (Titel, Summary-Bullets, Entities inkl.
    # Profiltext, mehrere historische Threads mit je one_line+extended,
    # politische Theorie, Connections, cui_bono) braucht auch OHNE
    # primary_sources/market_correlation (die im Lite-Modus leer bleiben)
    # regelmäßig deutlich mehr als 4000 Output-Tokens. Bei 4000 wurde die
    # Modellantwort im echten Testlauf mehrfach mitten im JSON abgeschnitten
    # (kein schließendes ``` mehr), was danach IMMER am JSON-Parsing
    # scheitert -- auch der Selbstkorrektur-Retry kann das nicht heilen,
    # wenn das Tokenbudget gleich bleibt. Deshalb hier auf 6000 angehoben
    # (wie DEFAULT_CONFIG); das ist die eigentliche Ersparnis von "lite"
    # ohnehin primär über `enable_web_search=False` (kein Tool-Call, kein
    # Recherche-Overhead) und die kürzeren Artikel-Ausschnitte, nicht über
    # ein zu knappes Output-Budget, das nur zu stillen Fehlschlägen führt.
    max_output_tokens=6000,
    research_depth="lite",
    enable_web_search=False,
    synthesis_concurrency=6,
    # 2 statt 1: `synthesize_with_claude` erkennt jetzt explizit
    # stop_reason == "max_tokens" und erhöht das Budget PRO Retry
    # (statt bei gleichem Budget nochmal zu scheitern), s. Kommentar dort
    # und bei `max_output_tokens` oben. Zwei solcher Budget-Retries kosten
    # nur dann etwas, wenn eine Story tatsächlich ungewöhnlich lang wird,
    # nicht bei jedem Lauf.
    max_json_retries=2,
)

# Vorgefertigtes Profil für die volle Formel (wenige, aber vollständig
# recherchierte Storys, wie in der manuellen v5-Demo dieser Session).
FULL_DEPTH_CONFIG = PipelineConfig(
    max_articles_per_story=8,
    max_chars_per_article=4000,
    max_output_tokens=7000,
    research_depth="full",
    enable_web_search=True,
    synthesis_concurrency=3,
)
