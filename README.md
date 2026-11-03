# Deeplitics, Prototyp

## Secure backend foundation (initial implementation)

The repository now includes a separate tenant-aware Flask API foundation in
`backend/`, with OIDC bearer-token validation, PostgreSQL migrations and
row-level security, encrypted workspace text, membership provisioning, and
workspace-scoped API routes. The existing static story browser and fixture-
based `v2/` prototype remain separate. This is not a declaration of GDPR
compliance; before using real customer data, follow the deployment and
privacy gaps in [`docs/SAFE_BACKEND.md`](docs/SAFE_BACKEND.md).

## Deeplitics v3 app

The new API-backed reading experience lives in `v3/` and is served at
`/app/`. It keeps the existing prototype unchanged. Story browsing is public;
saved stories and topic preferences require a verified OIDC login and are
encrypted per workspace member. See [`v3/README.md`](v3/README.md) for setup,
OIDC registration and the hardware deployment plan.

Ziel: politische Nachrichten aus vielen Quellen automatisch zu **Storys**
verdichten, die zeigen **wie Ereignisse, Akteure und Länder zusammenhängen**,
nicht nur was gerade passiert ist.

## Version 8 (19.08.2026), Prototyp-Feinschliff + neues v2-Projekt „Thread-basiertes System"

Zwei parallele Nutzeranfragen in dieser Sitzung: (a) mehrere konkrete
Detail-Fixes am bestehenden statischen v7-Prototypen, (b) der Aufbau eines
komplett neuen, eigenständigen zweiten Projekts (`v2/`) nach einer vom
Nutzer übergebenen "Bauanleitung für ein LLM: Thread-basiertes System für
politische Nachrichten".

**a) Fixes am bestehenden Prototyp (`frontend/`, `pipeline/`):**

- **Bug behoben: Entity-Modal ließ sich nicht schließen.** Ursache: auf
  Desktop-Breite bewegte die CSS-Transition das geschlossene Modal nur um
  40px nach unten statt vollständig aus dem sichtbaren Bereich, X-Klick
  und Scrim-Klick funktionierten technisch, das Modal blieb aber optisch
  sichtbar und blockierend. Fix: `opacity`/`visibility`/`pointer-events`
  zusätzlich zur Transform-Verschiebung, unabhängig vom Breakpoint robust.
- **Story-Detail neu strukturiert:** oben jetzt fix Bild + Titel +
  Kurzzusammenfassung, direkt darunter ein horizontales 4er-Swipe-Menü in
  der Reihenfolge Historien ← Übersicht (Stichpunkte + „Weiterlesen"-Button
  für die ausführliche Version) → Stakeholders → Märkte — Übersicht ist
  der Startpunkt beim Öffnen, exakt wie vom Nutzer beschrieben ("links
  History, rechts Stakeholders/Märkte").
- **„Akteure" → „Stakeholders" mit echter Pro/Con-Sicht.** Neues Feld
  `stakeholders: {pro, con, note}` je Story
  (`pipeline/enrich_stakeholders_2026-08-19.py`), aus dem bereits
  vorhandenen `cui_bono`-Text redaktionell in strukturierte Pro-/Con-Listen
  umgesetzt (keine neuen Fakten, nur Restrukturierung bestehender Aussagen).
  Zeigt für jede Story explizit, wer profitiert UND wer nicht/verliert,
  nicht mehr nur einseitig Gewinner. Klick auf eine Stakeholder-Karte
  öffnet weiterhin das normale Entity-Profil mit Bio/Wikipedia-Link.
- **Letztes fehlendes Story-Bild ergänzt** (Gaza-Story, vorher ohne Bild
  wegen aufgebrauchtem WebSearch-Budget in der vorigen Sitzung) — per
  Recherche-Agent verifiziertes offizielles Weißes-Haus-Foto von Trump und
  Netanyahu, über Wikimedia Commons. Damit haben jetzt wirklich alle 10
  Storys ein Bild.
- **Bild-zu-Artikel-Übergang verfeinert:** Hero-Bild und Inhalt
  überlappen jetzt bewusst (negativer Margin + Farbverlauf bis zur
  exakten Content-Hintergrundfarbe), der Titel sitzt teilweise auf dem
  ausklingenden Bild, näher an einem "Apple-artigen" nahtlosen Übergang
  statt eines harten Schnitts.
- **„Stand: …"-Zeitstempel oben rechts** im Topbar, aus dem Build-Datum
  des statischen Snapshots abgeleitet (`build_frontend.py`), ehrlich als
  Build-Datum und nicht als Live-Update gekennzeichnet.

**b) Neues Projekt `v2/`: Thread-basiertes System (siehe `v2/README.md`
für die volle Dokumentation).** Eigenständig neben dem bestehenden
Prototyp aufgebaut, mit echtem Flask-Backend + SQLite statt einer rein
statischen Single-File-Seite. Umgesetzt in der von der Bauanleitung
vorgegebenen Reihenfolge, nach jedem Schritt an den Testdaten verifiziert
(`v2/tests/test_pipeline.py`, 51/51 Checks bestanden):

1. Datenmodell (Article/Thread/Topic/Actor/User) + 16 synthetische
   Test-Artikel über 6 Themen-Cluster + 1 Singleton, klar als Fixture
   gekennzeichnet.
2. Clustering per TF-IDF + Cosine-Similarity (konfigurierbare Schwelle),
   trifft im Test exakt die im Datensatz angelegten 7 Gruppen.
3. LLM-Extraktion (Faktenkern/Zeitleiste/Akteure) mit echtem API-Pfad
   (mit `ANTHROPIC_API_KEY`) und einem dokumentierten Offline-Pfad mit
   von mir selbst als LLM erstellten echten Extraktionen für die
   Testdaten (kein Platzhalter-Mock).
4. Tagging (fester 9-Themen-Katalog, Fakt/Meinung-Flag, das bewusst
   einfache "abweichende Perspektive ja/nein"-Flag als Ersatz für den in
   V1 ausdrücklich nicht gebauten zweiachsigen politischen Kompass) +
   Wichtigkeits-Score aus Quellenzahl, offizieller Handlung und
   geschätzter Betroffenenzahl.
5. Zwei Feeds: "Das Wichtigste" (fest 6 Threads, nicht user-konfigurierbar,
   nie leer) und Themenblock-Feeds mit Wichtigkeit+Aktualität-Ranking und
   "neu seit letztem Besuch"-Markierung.
6. Serverseitig gerendertes Flask+Jinja2-Frontend: Dashboard, Themen-
   Ansicht, Thread-Detail (Faktenkern, Zeitleiste, Akteure, Quellen),
   Einstellungsseite. Perspektivenbreite-Regler klappt eine abweichende
   Quelle bei „eng" nur ein (`<details>`-Element, kein JS nötig), entfernt
   sie nie aus den Daten — technisch erzwungen, nicht nur als Empfehlung.

Bewusste Vereinfachungen, offen dokumentiert in `v2/README.md`: TF-IDF
statt echter Sentence-Embeddings (konsistent mit dem Rest des Projekts),
synthetische statt echter RSS-Testdaten, ein einziger fest hinterlegter
Nutzer ohne Login (wie in Abschnitt 7 der Bauanleitung ausdrücklich
erlaubt).



Kompletter Rewrite des Frontends nach expliziter Design-Vorgabe des Nutzers,
diesmal wieder rein statisch (kein API-Call zur Laufzeit, alles in
`frontend/index.html` gerendert). Kernänderungen:

- **Story-Detail neu strukturiert:** horizontales, swipebares Tab-Menü
  (Historien / Akteure / Märkte) statt fixem Zwei-Spalten-Layout, per CSS
  `translateX`-Track + Touch-Swipe-Erkennung. Darunter fest: erst Zitate,
  dann Quellen.
- **Quellen als Buttons statt Links:** `<button data-open="URL">` öffnet die
  URL per `window.open()`; die URL selbst ist im DOM als Attribut vorhanden,
  aber nirgends als sichtbarer Text/Linktext gerendert. Anzeigename wird aus
  dem Hostnamen abgeleitet (`hostLabel()`), Bias-Punkt via Präfix-Match gegen
  die bestehende Bias-Liste.
- **Farbsystem:** 6 feste Themenfarben (Sicherheit, Diplomatie, Handel,
  Bürgerrechte, Konflikt, Überwachung), je Story fest zugeordnet
  (`STORY_CATEGORY` in der Anreicherung), nicht rotierend — gemäß
  dataviz-Skill-Regel "kategoriale Farben in fester Reihenfolge, nie
  zyklisch".
- **Medien-Anreicherung (`pipeline/enrich_media_2026-08-18.py`):** jede
  Story bekommt ein Hero-Bild, jede Entität (wo auffindbar) ein rundes
  Portraitbild UND ein größeres quadratisches Kontextbild (z.B. Person in
  einer Situation, Ministeriumsgebäude, Flagge/Logo der Institution statt
  nochmal desselben Gesichts) plus einen Wikipedia-Link. Bildquellen wurden
  über 10 parallele Recherche-Agenten (mit eigenem Web-Zugriff) verifiziert
  und laufen über den Wikimedia-Commons-`Special:FilePath`-Redirect (kein
  Hash-Pfad-Raten nötig). Wo kein verifiziertes Bild gefunden wurde (9 von
  ~92 Entitäten, plus die Gaza-Story als einzige Story ohne Hero-Bild wegen
  aufgebrauchtem WebSearch-Budget in dieser Sitzung), zeigt die UI einen
  gestalteten Icon/Gradient-Fallback statt eines kaputten Bildes.
- **"Wichtige Entität"-Kennzeichnung:** statt neue Langbiografien für alle
  Entitäten zu schreiben, wird die ohnehin variable Länge des bestehenden
  `profile`-Felds als Signal genutzt — Entitäten mit `profile.length > 300`
  bekommen ein "Zentrale Figur dieser Story"-Badge im Entitäts-Modal.
- **Profil-Panel oben rechts (rein clientseitig, siehe unten):** Sprache
  DE/EN, Hell-/Dunkelmodus (Dunkel = Standard), Inhaltspräferenzen
  (Themenfarben an-/abwählen), zufälliger Avatar (kein Bild-Upload möglich),
  Lese-Verlauf, gespeicherte Storys.
- **Kreative Begrüßung auf der Startseite:** 7 Tageszeit-Buckets, je
  mehrere DE/EN-Varianten, zufällig gewählt (`GREETINGS`/`pickGreeting()`).

**Wichtige Einschränkung, bewusst so umgesetzt:** Artifacts in dieser
Umgebung dürfen laut Systemvorgabe kein `localStorage`/`sessionStorage`
verwenden. Profil, Sprache, Theme, Verlauf und gespeicherte Storys sind
deshalb reiner In-Memory-State (JS-Variablen) — sie gelten nur für die
aktuelle Sitzung und werden bei einem Neuladen der Seite zurückgesetzt.
Das ist im UI-Text selbst offen kommuniziert, nicht versteckt. Für eine
echte Persistenz über Sitzungen hinweg bräuchte es entweder einen echten
Cookie-/Backend-Login oder eine Ausführungsumgebung ohne diese
Storage-Einschränkung (z.B. ein eigenständiges Deployment, siehe
`docs/HOSTING.md`).

QA: alle 10 Storys per Playwright durchgeklickt (Desktop 1400×1000 und
Mobile 390×844), 0 JS-Fehler in allen Fällen (die einzigen Konsolenfehler
sind `ERR_TUNNEL_CONNECTION_FAILED` für externe Bild-URLs — ein Artefakt
der komplett netzisolierten Sandbox, kein echter Bug; die Bilder sollten im
normalen Browser des Nutzers laden). Dabei mehrere echte Feldnamen-Bugs
gefunden und behoben: `quotes[].attribution` (nicht `.speaker`),
`primary_sources[].note`/`.issuer` (nicht `.description`/`.publisher`),
`political_theory.theory` (nicht `.concept`), sowie eine falsche
Index-Kopplung von `sources[]` und `article_urls[]` (nicht garantiert
gleich lang/sortiert — Quellen-Buttons werden jetzt direkt aus
`article_urls[]` abgeleitet).

## Version 6.1 (18.08.2026), Erster echter API-Testlauf: 2 reale Bugs gefunden und behoben

Der Nutzer hat einen `ANTHROPIC_API_KEY` direkt im Chat geteilt. Das war der
erste Lauf, der tatsächlich `synthesize_with_claude()` gegen die echte
Anthropic-API aufgerufen hat (nicht Recherche-Agenten wie am 17.08.), mit
echtem Token-/Kosten-Tracking über `_pipeline_meta`.

**Wichtiger Hinweis zur Sicherheit:** Ein API-Key im Klartext im Chat ist
ein Sicherheitsrisiko, sobald er irgendwo geloggt wird. Der Nutzer wurde
gebeten, den Key danach im Anthropic Console zu rotieren/widerrufen.

**Sandbox-Einschränkung bestätigt:** echte RSS-Feed-Domains (Reuters, AP,
BBC, Axios, DW, France24, ...) sind aus dieser Cloud-Sandbox weiterhin nicht
erreichbar (ProxyError bei allen getesteten Quellen), nur `api.anthropic.com`
ist erreichbar. Der Fetch-Schritt (1) der Pipeline wurde deshalb für diesen
Test durch echte, aktuelle Artikel ersetzt, die per WebSearch/WebFetch (von
der Sandbox getrennte Tools) aus 10 unterschiedlichen realen Quellen zu 5
neuen Themen-Clustern zusammengetragen wurden
(`data/live_api_test_2026-08-18/raw_articles.json`). Ab dem Clustering/
Synthese-Schritt lief alles unverändert über den echten Produktionscode.

**Bug 1, gefunden und behoben: `max_output_tokens` im Lite-Profil war zu
knapp.** `LITE_SCALE_CONFIG.max_output_tokens` stand auf 4000 (dann testweise
6000), das volle Story-JSON-Schema (Titel, mehrere Summary-Bullets, 8-17
Entities mit Profiltext, mehrere historische Threads, politische Theorie,
Connections) braucht aber real gemessen 7000-9000 Output-Tokens, auch ohne
Primärquellen-/Marktrecherche. Die Antworten wurden dadurch systematisch
mitten im JSON abgeschnitten, was beim Parsen einen irreführenden Fehler
("line 1 column 1") erzeugte und selbst nach einer Selbstkorrektur-Runde
nicht mehr behebbar war, weil das Budget gleich blieb. Behoben durch:
- `LITE_SCALE_CONFIG.max_output_tokens` von 4000 auf 6000 angehoben.
- `synthesize_with_claude()` erkennt jetzt `stop_reason == "max_tokens"`
  explizit und erhöht bei einem Retry das Budget selbst (statt nur eine
  "gib nur JSON zurück"-Korrekturnachricht zu schicken, die das eigentliche
  Problem nicht löst), gedeckelt bei 16.000 Tokens.
- `max_json_retries` im Lite-Profil von 1 auf 2 erhöht, damit das Budget
  bei Bedarf zweimal wachsen kann (6000 -> 9600 -> 15360).
- `_parse_json_loose()` gibt bei abgeschnittenem Codeblock jetzt einen
  aussagekräftigen Fehler an der tatsächlichen Abbruchstelle statt der
  irreführenden Meldung "line 1 column 1".

**Bug 2, gefunden und behoben: eine langsame Story blockierte das Sichern
aller anderen.** `run_pipeline.py` (und das Testskript dieses Laufs)
schrieben `data/stories.json` bisher erst NACH `as_completed` für ALLE
Cluster. Eine einzelne besonders lange Story (z.B. weil sie den
Budget-Retry aus Bug 1 braucht) verzögerte dadurch das Sichern bereits
erfolgreich fertiger Storys. Behoben: `data/stories.json` wird jetzt nach
JEDER fertigen Story sofort mit dem aktuellen Zwischenstand überschrieben,
sowohl in `run_pipeline.py` als auch im Testskript dieses Laufs.

**Ergebnis des Testlaufs:** von 5 neuen Themen-Clustern (Taiwan/China-
Manöver, EU-Sanktionen gg. Russland, Venezuela nach Maduro-Festnahme,
UK-Starmer-Führungskrise, Netanyahu/Gaza-Fahrplan) wurden 2 erfolgreich per
echtem API-Call synthetisiert (EU-Sanktionen, Gaza-Fahrplan), bevor das
Guthaben des vom Nutzer geteilten Keys aufgebraucht war (`400
invalid_request_error: credit balance too low`) und die restlichen 3
fehlschlugen. Das ist eine Zahlungs-/Guthabengrenze, kein Pipeline-Fehler.
Damit sind es jetzt **10 Storys** insgesamt (8 vom 17.08. + 2 echte
API-Storys vom 18.08.), mit vollem `_pipeline_meta`:

| Story | Input-Tokens | Output-Tokens | geschätzte Kosten |
|---|---|---|---|
| EU-Sanktionen gg. Russland | 3.310 | 7.774 | $0.1265 |
| Netanyahu/Gaza-Fahrplan | 3.372 | 8.800 | $0.1421 |

Bei ca. $0.13-0.14/Story im Lite-Profil (Sonnet 4.5: $3/MTok in, $15/MTok
out) inklusive vollem Schema ohne Primärquellen-/Marktrecherche liegt eine
"echte" Realität näher an ~$1.30-1.40 für 10 Storys als an den ursprünglich
grob geschätzten Kosten -- eine nützliche Kalibrierung für die
Kostenplanung beim weiteren Skalieren. (Zusätzlich wurden bei den beiden
vorherigen Testläufen, in denen Bug 1 erst gefunden und behoben wurde,
weitere Tokens für fehlgeschlagene, abgeschnittene Antworten verbraucht,
die nicht in obiger Tabelle auftauchen, da `_pipeline_meta` nur bei
erfolgreicher Synthese gesetzt wird -- eine Lücke im Kosten-Tracking für
fehlgeschlagene Versuche, die für einen künftigen Lauf noch geschlossen
werden sollte.)

**Offen für einen künftigen Lauf, sobald wieder Guthaben verfügbar ist:**
die restlichen 3 Cluster (Taiwan, Venezuela, UK-Starmer) sind bereits
vorbereitet in `data/live_api_test_2026-08-18/raw_articles.json` und können
mit `python3 pipeline/live_api_test_2026-08-18.py` jederzeit nachgeholt
werden, ohne erneute Recherche.

## Version 6 (17.08.2026), Formel generalisiert/formalisiert, echte Skalierung

Nutzerwunsch: die Formel generalisieren/formalisieren und sicherstellen,
dass sie beim Skalieren der Datenmenge (mehr Quellen, mehr Artikel, mehr
Storys pro Lauf) gut funktioniert, ohne unnötig viele Tokens/Rechenzeit zu
brauchen. Kernänderung: alle "Skalierungs-Regler", die vorher als
verstreute Magic Numbers im Code lagen, sind jetzt an einem Ort gebündelt.

- **`pipeline/config.py`, neu**: `PipelineConfig`-Dataclass bündelt JEDEN
  Skalierungs-Regler (Artikel pro Quelle, Cluster-Grenzen, Artikel/Zeichen
  pro Story-Prompt, Modell, Output-Tokens, Recherche-Tiefe, Parallelität,
  Web-Search-Limit) an einem Ort, dokumentiert und mit sinnvollen
  Defaults. Drei vorgefertigte Profile: `DEFAULT_CONFIG` (schnell/günstig,
  kein Such-Tool), `LITE_SCALE_CONFIG` (noch schlanker, für viele Storys),
  `FULL_DEPTH_CONFIG` (volle Formel inkl. echter Web-Recherche, wie die
  v5-Demo).
- **Kosten/Latenz pro Story sind jetzt UNABHÄNGIG von der Cluster-Größe**:
  `synthesize_story.py::select_representative_articles()` wählt bis zu
  `max_articles_per_story` Artikel per Round-Robin über die Quellen aus
  (maximale Perspektivendiversität statt zufälliger Reihenfolge) und kappt
  jeden Artikeltext auf `max_chars_per_article`. Ein Cluster mit 40
  Artikeln kostet dadurch nicht 10x so viel wie einer mit 4.
- **`research_depth`: "full" vs. "lite"**, der wichtigste Hebel für "viele
  Storys, wenig Kosten". "Full" bindet das echte Anthropic-Server-Tool
  `web_search` ein (vorher war die Anweisung "recherchiere Primärquellen"
  ohne echtes Such-Tool eine Einladung zur Halluzination). "Lite"
  überspringt Primärquellen-/Marktrecherche komplett, `primary_sources`
  und `market_correlation` werden serverseitig HART auf leer/`null`
  erzwungen (`_finalize_story_dict`), egal was das Modell zurückgibt, das
  ist die eigentliche Garantie gegen Erfindungen ohne Such-Tool.
  `political_theory` bleibt in beiden Modi erhalten (reines Modellwissen,
  kaum Zusatzkosten).
- **Kein `anthropic`-SDK mehr zwingend nötig**: `_create_message()` nutzt
  das offizielle SDK, wenn installiert, fällt sonst automatisch auf einen
  direkten HTTP-Call gegen `api.anthropic.com` über `requests` zurück
  (inkl. Retry/Backoff bei 429/5xx). Grund: diese Sandbox kann keine
  PyPI-Pakete installieren, `api.anthropic.com` selbst ist aber direkt
  erreichbar, das macht die Pipeline portabler UND hat den ersten echten
  Testlauf in genau dieser Sandbox erst ermöglicht.
- **Response-Parsing robust gegenüber Tool-Use-Antworten** (mehrere
  Content-Blöcke bei Websuche), plus eine Selbstkorrektur-Runde
  (`max_json_retries`), falls die letzte Text-Antwort kein valides JSON
  ist, statt sofort zu scheitern.
- **Synthese läuft PARALLEL** über `ThreadPoolExecutor`
  (`synthesis_concurrency`), nicht mehr seriell, das ist der größte Hebel
  dafür, dass "mehr Storys" nicht linear "mehr Wartezeit" bedeutet. Ein
  einzelner fehlgeschlagener Story-Aufruf bricht den Lauf nicht mehr ab,
  sondern wird geloggt und übersprungen.
- **Volltext-Extraktion läuft ebenfalls PARALLEL** (`fetch_concurrency`),
  vorher ein serieller HTTP-Request pro Artikel, bei hunderten Artikeln
  vorher der heimliche Laufzeit-Dominator.
- **`--max-stories`** deckelt, wie viele der gefundenen Multi-Source-
  Cluster tatsächlich synthetisiert werden (die größten/best-belegten
  zuerst), UNABHÄNGIG davon wie viele Cluster insgesamt gefunden wurden,
  das macht Kosten eines Laufs vorhersagbar und planbar.
- **`cluster.py`**: Sicherheitsgrenze `max_articles_for_clustering` vor
  dem O(n²)-Agglomerative-Clustering (kappt auf die neuesten Artikel statt
  unkontrolliert langsam zu werden/OOM zu gehen), dokumentierter Pfad für
  "wirklich groß" (Embeddings + approximatives Clustering statt O(n²)).
- **Token-Nutzung pro Story wird mitgeloggt** (`_pipeline_meta`:
  `input_tokens`/`output_tokens`/`model`/`research_depth`), `run_pipeline.py`
  summiert das am Laufende zu einer Kosten-/Skalierungs-Übersicht
  (Gesamt-Tokens, Tokens/Story im Schnitt).
- Alle Regler sind jetzt auch über die Kommandozeile steuerbar:
  `python3 pipeline/run_pipeline.py --profile lite --max-stories 20
  --concurrency 6` (`--help` für alle Optionen).

### Skalierungs-Batch statt Live-API-Test (17.08.2026)

Der geplante erste echte API-Testlauf wurde vom Nutzer für diese Session
zurückgestellt (kein `ANTHROPIC_API_KEY` zur Hand). Um den zweiten Teil des
Wunsches trotzdem sinnvoll zu bedienen ("versuche, die Anzahl der Storys
zu skalieren"), wurden nach demselben Muster wie die ursprüngliche
v5-Demo VIER weitere, komplett unabhängig recherchierte Storys ergänzt
(`pipeline/scale_batch_2026-08-17.py`, Rohdaten unter
`data/scale_batch_2026-08-17/`): CIA-Drohnenangriffe vor Ecuador/
Galápagos, Putins Kurilen-Besuch (Russland-Japan), Section-338-Zölle
gegen Kanada, DHS-Überwachung linker Gruppen in Minnesota. Bewusst vier
komplett unterschiedliche Weltregionen/Themen ohne Überschneidung mit den
bestehenden 4 Storys, um zu zeigen, dass die v6-Formel über ein breites
Themenspektrum trägt, nicht nur über die ursprünglich gewählten Beispiele.
`data/stories.json` enthält jetzt 8 Storys insgesamt. WICHTIG: Dieser
Batch lief NICHT über `synthesize_with_claude()`/die echte API (kein
`_pipeline_meta`, kein Token-Tracking), sondern über vier parallele
Recherche-Agenten nach demselben Schema. Der echte API-Testlauf mit
Kosten-/Token-Messung steht weiterhin aus, sobald ein Key verfügbar ist.

## Version 5 (17.08.2026), synthetischer Stil, Primärquellen, politische Theorie, Marktkorrelation

Auf ausdrücklichen Nutzerwunsch, generalisiert über das konkret Gesagte
hinaus (Leitlinie: nicht 1:1 umsetzen, das dahinterliegende System
erkennen):

- **Synthetischer statt mosaikartiger Schreibstil**: `summary`,
  `deep_dive` und `cui_bono` sollen die Einzelartikel zu EINEM
  verschmolzenen Verständnis zusammenführen, nicht als Aneinanderreihung
  von "Person X sagte laut Artikel Y..." geschrieben sein. Named Actors
  dürfen als handelnde Parteien vorkommen, aber wörtliche
  Zitat-Attribution ist jetzt AUSSCHLIESSLICH `quotes` vorbehalten
  (`synthesize_story.py`, neuer Abschnitt "STIL"). Einzelne Artikel
  bleiben weiterhin zitierbar/verlinkt (`article_urls`, `sources`), nur
  die Fließtext-Ebene wird nicht mehr als Mosaik geschrieben.
- **`Story.summary` ist jetzt eine Bullet-Liste** (`list[str]`) statt
  eines Fließtext-Absatzes: die Meldung selbst ist knapp und scanbar, der
  Fließtext bleibt dem `deep_dive` vorbehalten, der bewusst weiterhin
  Fließtext ist, aber wirklich in die Tiefe gehen soll, in einfacher
  Sprache statt komplizierter Fachsprache.
- **`PrimarySource` + `Story.primary_sources`** (`schema.py`): echte
  Primärquellen, Regierungsdokumente, offizielle Statements,
  Gerichtsentscheidungen, Pressemitteilungen, GETRENNT von der
  journalistischen Berichterstattung (`article_urls`). Die Formel sucht
  jetzt aktiv im Federal Register, Congressional Record, bei
  Gerichtsdatenbanken, Behörden-/Abgeordneten-Pressemitteilungen und
  internationalen Gremien (AU, UN) nach dem Originaldokument, auf das
  sich die Sekundärberichterstattung bezieht. Ehrlichkeitsregel: leere
  Liste statt erfundener URL, wenn nichts gefunden wird (siehe Story 4 im
  Demo-Datensatz, `ukraine-long-range-strikes-2026-08`, mit `[]`).
- **`PoliticalTheoryNote` + `Story.political_theory`** (`schema.py`):
  ordnet die Story durch die Linse EINES politikwissenschaftlichen
  Konzepts ein, kurz, als Bullet-Points, kein Essay. Im Frontend hinter
  einem eigenen Button versteckt (`Politische Theorie dazu`), nicht Teil
  der Standardansicht, jede Story wird keine Vorlesung. `null` ist ein
  gültiger Wert, wenn kein Konzept wirklich passt.
- **`MarketCorrelation`/`MarketSeries`/`MarketDataPoint` +
  `Story.market_correlation`** (`schema.py`): ehrliche Prüfung, ob sich
  ein Ereignis in Finanzmärkten (Aktien, Rohstoffe, Indizes)
  niedergeschlagen hat. `has_correlation=False` ist ein vollwertiges,
  erwartetes Ergebnis, keine erzwungene Korrelation, keine erfundenen
  Kurswerte. Im Demo-Datensatz hat nur Story 1 (USS Abraham Lincoln)
  `has_correlation=True` (Brent Crude Oil + Lockheed Martin, indexiert,
  Basis 100), die anderen drei zeigen ehrlich recherchierte
  Nicht-Korrelationen mit kurzer Begründung statt eines Charts.
  Frontend-Chart: selbstständiges inline-SVG (kein CDN/Library, konsistent
  mit dem Rest des Projekts), indexierte Mehrfachserien-Linie nach
  `dataviz`-Skill (2px Linien, direkte Endlabel `±X.X%`, Legende,
  Crosshair+Tooltip bei Hover, wiederverwendete bereits CVD-validierte
  Kategorialfarben `--c-actor`/`--c-context` statt neuer unvalidierter
  Farben).
- **Neue Reihenfolge im Detail-View**: Meldung (Bullets) + Historien-Spalte
  nebeneinander (unverändert, vom Nutzer explizit als "ziemlich perfekt"
  bestätigt) → Zitate → Marktkorrelation. Zitate stehen jetzt bewusst NICHT
  mehr am Anfang.

## Version 4 (16.08.2026), Karten, Zitate, Podcasts, eingeklappte Storys

Vier komplett neue, eigenständig recherchierte Storys vom 16.08.2026 (statt
der zwei Beispiele vom Vortag), zeigen, dass die Formel generalisiert statt
auf zwei Spezialfälle zugeschnitten zu sein. Neu hinzugekommen:

- **Zitate** (`Story.quotes`): 1-3 echte, wörtliche O-Töne pro Story, aus
  den Quellartikeln entnommen, nie erfunden oder paraphrasiert. Werden im
  Frontend als Pull-Quotes dargestellt (`schema.py::Quote`).
- **Hero-Bilder** (`Story.image_url`): das og:image eines Quellartikels
  (das Vorschaubild, das die Publikation selbst für Social-Media-Vorschauen
  hinterlegt hat), extrahiert über `extract_article.py::extract_og_image`.
- **Eingeklappte Story-Karten**: eine Story zeigt zunächst nur Bild, Titel
  und Mini-Zusammenfassung; ein Klick öffnet Zitate, historische Linien,
  Cui-Bono-Analyse und Tiefenrecherche. Reduziert die Startseite auf eine
  scanbare Übersicht, ähnlich Aggregatoren wie Particle News.
  Kein langer Erklärtext mehr oben auf der Seite, nur der Deeplitics-
  Schriftzug und ein "Prototyp"-Tag.
- **Podcast-Modul** (`sources/podcasts.py`, `fetch_podcasts.py`,
  `transcribe.py`): Podcast-RSS-Feeds sind strukturell normale RSS-Feeds
  mit einem zusätzlichen Audio-`<enclosure>`-Tag, `fetch_podcasts.py`
  spiegelt daher `fetch_feeds.py`. Vor der eigentlichen Cluster-/
  Synthese-Pipeline braucht eine Episode aber ein Transkript,
  `transcribe.py` ist dafür als PLUGGABLE Interface gebaut (Whisper API,
  lokales Whisper-Modell oder AssemblyAI), da diese Sandbox kein
  STT-Backend/keinen API-Key zur Verfügung hat. Ohne Backend liefert es
  einen klar markierten Platzhalter (Titel + Shownotes) statt erfundenem
  Text.
- **Entity-Bilder statt Farb-/Form-Icons**: die Legende wurde entfernt, im
  Bottom-Sheet-Profil zeigt der kleine Avatar jetzt das echte Foto der
  Entität, wenn vorhanden (Fallback aufs Farb-/Form-Icon nur noch bei
  fehlendem Bild).
- **Stilregeln fest im Synthese-Prompt verankert**
  (`synthesize_story.py::ANALYTICAL_INSTRUCTIONS`): strikt faktisch und
  neutral, keine Gedankenstriche (Em-Dashes) im generierten Text.
- **3 weitere Quellen** (`sources/feeds.py`): Euronews, Kyiv Independent,
  Asharq Al-Awsat English.

## Version 3 (15.08.2026), mehrere konvergierende historische Linien

Kernänderung: Eine Story hat nicht mehr EINE historische Linie, sondern
**mehrere unabhängige** (`historical_threads`, 2-5 Stück, nie künstlich
aufgefüllt). Eine Meldung ist fast immer der Konvergenzpunkt von mindestens
zwei komplett unabhängigen Entwicklungslinien — z.B. einer geopolitischen
Linie UND einer institutionellen/politischen Linie (Gesetz, Programm,
Behörde). Beispiel im Prototyp: die Afghanistan-Story ist gleichzeitig (a)
der jüngste Punkt der Geschichte Afghanistans unter den Taliban UND (b) der
jüngste Punkt der Geschichte der US-Einwanderungspolitik gegenüber
Kriegsverbündeten (SIV-Programm) — zwei Linien, die nur zufällig in
derselben Meldung zusammenlaufen.

**Lesart im Frontend:** horizontal (Tab-Box oben in der Historien-Spalte)
zwischen den verschiedenen Linien wechseln, vertikal die gewählte Linie
chronologisch lesen. Jeder Meilenstein ist ein Schlaglicht (`one_line`,
immer sichtbar) UND extendable (`extended`, per Klick aufklappbar).

Die generalisierte Formel dafür lebt in `pipeline/synthesize_story.py`
(`ANALYTICAL_INSTRUCTIONS` + `STORY_JSON_SCHEMA_HINT`) und fordert bei
JEDEM Artikel-Cluster dieselben Dinge ein:

1. **Inline-Entity-Referenzen** (`[[Name]]`) → klickbare Links im Frontend,
   öffnen ein Profil im Bottom-Sheet (Google-Maps-Stil), inkl. echtem Bild
   wo auffindbar (Wikimedia Commons), sonst Platzhalter mit `onerror`-Fallback.
2. **Strategische Entity-Profile** (Personen UND Institutionen).
3. **Mehrere historische Linien** (`historical_threads`), s.o.
4. **Cui bono** (`cui_bono`) — quellenübergreifende "wem nützt das?"-Analyse.

Zusätzlich: Quellenpool auf ~35 englischsprachige Outlets erweitert und
bewusst über das politische Spektrum gestreut (`pipeline/sources/feeds.py`,
Feld `bias`, grobe AllSides-artige Kategorisierung, als Chip an jeder
Quelle im Frontend sichtbar, klar als Näherung gekennzeichnet).

**Wichtig:** `data/stories.json` enthält vier komplett neue Beispiel-Storys
vom 16.08.2026 (siehe Version 4 oben), nicht mehr die zwei Beispiele vom
15.08.2026. Die Grundfakten stammen aus echten, live abgerufenen Artikeln;
die historischen Linien/Profile/Cui-Bono-Texte sind illustrative Beispiele
der Formel. Die Formel selbst ist generisch und für jedes Thema einsetzbar,
sobald sie über die Anthropic API automatisiert läuft.

## Projektstruktur

```
pipeline/
  config.py                  ALLE Skalierungs-Regler an einem Ort (PipelineConfig, Profile)
  sources/feeds.py        ~35 kuratierte Quellen, je mit Bias-Label
  sources/podcasts.py     kuratierte Podcast-Feeds
  fetch_feeds.py           RSS/Atom abrufen (ohne feedparser)
  fetch_podcasts.py        Podcast-Episoden-Metadaten abrufen
  transcribe.py             Transkriptions-Interface (pluggable, kein Backend in dieser Sandbox)
  extract_article.py       Volltext- + og:image-Extraktion (ohne trafilatura)
  cluster.py                Artikel -> Storyline-Cluster (TF-IDF), MIN_SOURCES_FOR_STORY
  synthesize_story.py      DIE FORMEL: Threads, Zitate, Primärquellen, Theorie, Marktkorrelation, Stilregeln
  schema.py                  Article, Story, Entity, Connection, ThreadEntry, HistoricalThread, Quote,
                              PrimarySource, PoliticalTheoryNote, MarketCorrelation/MarketSeries
  run_pipeline.py           Orchestriert alles
  build_frontend.py        Baut frontend/index.html aus Template + stories.json + Bias-Liste
  demo_live_run.py         Beispieldaten (4 Storys, je 2 Threads, Datenstand 16.08.2026)
data/
  stories.json              Aktuelle Story-Daten
frontend/
  index.html / index.template.html   Eingeklappte Karten, Zwei-Spalten-Layout im Detail: Historien-Tabs links, Inhalt rechts
docs/
  NETWORK_NOTES.md          Warum Bash hier keinen Internetzugriff hat
  HOSTING.md                  Empfehlung für echtes Live-Deployment
requirements.txt
```

## Pipeline selbst ausführen (in einer normalen Umgebung mit Internet)

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...   # nötig für die echte, automatisierte Synthese
python3 pipeline/run_pipeline.py   # -> data/stories.json
python3 pipeline/build_frontend.py # -> frontend/index.html
```

## Nächste sinnvolle Schritte

- Echten API-Lauf testen (automatisierte Synthese statt Beispieldaten),
  prüfen, ob die Formel bei unbekannten Themen genauso zuverlässig
  distinkte historische Linien, echte Zitate UND echte Primärquellen
  findet, ohne bei fehlendem Primärquellen-/Marktbefund in Fabrikation zu
  verfallen.
- Bei der Primärquellen-/Marktrecherche für die Ukraine-Story (v5) fiel
  ein Cluster gefälschter regionaler Nachrichtenseiten auf ("Pravda
  Network"/"Portal Kombat"), die legitime Outlets imitieren. Für künftige
  automatisierte Läufe lohnt sich eine Domain-Hygiene-Prüfung/Blockliste
  gegen bekannte Desinformationsnetzwerke, bevor ein Artikel als Quelle
  genutzt wird.
- Historische Meilensteine haben bereits ein optionales `extended`-Feld
  für Tiefe pro Eintrag, das ist der bestehende Mechanismus für "mehr
  Tiefe pro Meilenstein". Sollte nochmal mit dem Nutzer geprüft werden,
  ob das seinen Wunsch nach tieferer Drill-down-Möglichkeit in der
  Historie schon vollständig abdeckt oder ob mehr gebraucht wird
  (z.B. verlinkte Quellen pro Meilenstein).
- Ein echtes STT-Backend an `transcribe.py` anschließen (Whisper API,
  lokales Modell oder AssemblyAI) und den vollen Podcast-Pfad einmal
  live durchspielen.
- Bild-Recherche systematisieren (aktuell nur für die Demo-Entitäten
  manuell recherchiert), z.B. ein eigener Schritt, der für jede neue
  Entität eine Wikimedia-Commons-Suche macht und die URL vor dem
  Speichern per HTTP-HEAD-Request verifiziert.
- Bias-Datensatz durch eine echte, gepflegte Quelle ersetzen statt der
  handkuratierten Näherung in `feeds.py`.
- Mehrsprachigkeit + Übersetzung.
- Persistenz (DB statt JSON) + geplante automatische Läufe.
- Siehe `docs/HOSTING.md` für den Weg zu einer echten, öffentlichen URL.
