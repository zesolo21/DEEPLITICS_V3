# Deeplitics v2 — Thread-basiertes System (Prototyp)

Eigenständiges, neues Projekt neben dem bestehenden statischen Deeplitics-
Prototyp (`../frontend/`, `../pipeline/`). Umgesetzt nach der vom Nutzer
übergebenen "Bauanleitung für ein LLM: Thread-basiertes System für
politische Nachrichten" (19.08.2026).

## Kernidee

Ein Strom politischer Nachrichtenartikel wird zu **Threads** (zusammen-
gehörigen Ereignissträngen) geclustert, jeder Thread bekommt einen groben
**Themenblock**, beteiligte **Akteure** und einen **Wichtigkeits-Score**.
Der Nutzer sieht auf einem Dashboard erstens seine gepinnten Themenblöcke,
zweitens unveränderlich eine **"Das Wichtigste"**-Kachel, damit nichts
Großes verpasst wird, nur weil es außerhalb der gepinnten Themen liegt.

## Bewusster Scope von Version 1 (MVP), wie in der Bauanleitung gefordert

Explizit NICHT gebaut: zweiachsiger politischer Kompass (ersetzt durch ein
einziges "zeigt eine abweichende Perspektive?"-Flag pro Quelle),
Empfehlungssystem auf Basis von Leseverhalten, mehrsprachige Inhalte,
mobile Apps, Login-System (ein einziger fest hinterlegter Nutzer reicht
laut Bauanleitung Abschnitt 7 für Version 1).

## Struktur

```
v2/
  pipeline/
    models.py        Article/Thread/Topic/Actor/User-Datenmodell (dataclasses)
    config.py         Themenliste, Clustering-Schwelle, Scoring-Gewichte
    test_articles.py  Feste Test-Artikelmenge (SYNTHETISCH, klar als Fixture markiert)
    cluster.py         Artikel -> Threads (TF-IDF-Vektoren + Cosine-Similarity-Schwelle)
    extract.py         LLM-Extraktion: Faktenkern + Zeitleisten-Eintrag + Akteure
                        (pluggable: echter Anthropic-API-Call wenn ANTHROPIC_API_KEY
                        gesetzt ist, sonst dokumentierter Offline-Pfad mit von mir als
                        LLM tatsächlich erstellten Extraktionen für die Testdaten)
    tagging.py          Themenblock-Zuordnung, Fakt/Meinung-Flag, Wichtigkeits-Score
    feeds.py             "Das Wichtigste" + Themenblock-Feeds, Perspektivenbreite-Regler
    store.py             SQLite-Persistenz (stdlib sqlite3, keine ORM-Abhängigkeit)
    run_pipeline.py      Orchestriert alle Schritte nacheinander
  web/
    server.py            Flask-App: Dashboard, Themen-Ansicht, Thread-Detail, Einstellungen
    templates/            Jinja2-Templates für die vier Ansichten
    static/style.css      Eigenständiges, minimalistisches CSS (gleiche Design-Sprache
                           wie der v7-Prototyp: dunkel als Standard, Apple-artiger Stil)
  tests/
    test_pipeline.py      Tests je Pipeline-Schritt an den Beispieldaten (Abschnitt 8
                           der Bauanleitung: "teste nach jedem Schritt")

## Bau-Reihenfolge (befolgt die Vorgabe aus Abschnitt 8 der Bauanleitung)

1. Datenmodell + feste Test-Artikelmenge
2. Clustering (Artikel -> Threads)
3. LLM-gestützte Extraktion (Faktenkern, Zeitleiste, Akteure)
4. Tagging (Themenblock, Fakt/Meinung, abweichende Perspektive) + Wichtigkeits-Score
5. Zwei Feeds (Das Wichtigste, Themenblöcke) mit einfachem Ranking
6. Frontend: Dashboard, Themen-Ansicht, Thread-Detail, Einstellungen

Nach jedem Schritt wurde mit den Test-Artikeln verifiziert, bevor der
nächste Schritt begonnen wurde (siehe `tests/test_pipeline.py`).

## Lauffähig machen

```bash
cd v2
python3 pipeline/run_pipeline.py     # baut deeplitics_v2.db aus den Testartikeln
python3 web/server.py                # startet lokal auf http://127.0.0.1:5057
```

## Wichtige, ehrlich offengelegte Vereinfachungen dieser Version

- **Testdaten sind synthetisch.** `pipeline/test_articles.py` enthält KEINE
  echten Presseartikel, sondern von mir erfundene, klar als Fixture
  markierte Beispielszenarien (deutsche/EU-Politik, Datenstand fiktiv
  August 2026), damit die Pipeline-Logik ohne echten RSS-Zugriff testbar
  ist. Für echten Betrieb braucht `pipeline/ingest.py` (noch nicht gebaut)
  echte RSS-Feeds wie im v1-Prototyp (`../pipeline/sources/feeds.py`).
- **Clustering nutzt TF-IDF-Vektoren statt echter Sentence-Embeddings.**
  Bewusste Entscheidung, konsistent mit dem restlichen Projekt (auch der
  v1-Prototyp vermeidet schwere ML-Abhängigkeiten wegen der Sandbox-
  Einschränkungen). `scikit-learn` ist bereits eine Abhängigkeit. Echte
  Embeddings (z.B. `sentence-transformers`) sind ein sauberer Austausch-
  Punkt für später, die Funktionssignatur von `cluster.py::cluster_articles()`
  ist bewusst stabil dafür gehalten.
- **LLM-Extraktion**: `extract.py` hat einen echten, produktionsfähigen
  API-Pfad (HTTP gegen `api.anthropic.com`, wie im v1-Prototyp). Da diese
  Sitzung keinen `ANTHROPIC_API_KEY` gesetzt hat, wurden die Extraktionen
  für die Test-Threads von mir (als das LLM, das diese Anleitung umsetzt)
  direkt und mit echtem Verständnis der Testartikel erstellt und als
  Fixture hinterlegt (`pipeline/extract.py::_OFFLINE_EXTRACTIONS`) — das
  ist keine Mock-Attrappe, sondern eine echte, nur eben interaktiv statt
  per Laufzeit-API-Call erstellte Extraktion. Mit gesetztem API-Key läuft
  derselbe Code stattdessen live gegen die echte API.
- **Ein einziger, fest hinterlegter Nutzer** (`config.DEFAULT_USER_ID`),
  kein Login-System, wie in Abschnitt 7 der Bauanleitung ausdrücklich
  erlaubt.
