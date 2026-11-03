"""
Der eigentliche "Deeplitics"-Schritt, die generalisierte Formel (Version 6).

Neu in v3: Eine Story wird nicht mehr in EINE historische Linie
eingeordnet, sondern die Formel sucht aktiv nach MEHREREN unabhängigen
Linien, die zufällig in derselben Meldung zusammenlaufen (siehe
`schema.py`-Docstring für das Beispiel Afghanistan-Bildung +
US-Einwanderungspolitik).

Neu in v4: echte Zitate (`quotes`) und ein Hero-Bild (`image_url`).

Neu in v5: synthetischer statt mosaikartiger Stil, Bullet-Summary,
Primärquellen, politische Theorie (versteckt), Marktkorrelation.

Neu in v6, auf Nutzerwunsch "generalisieren, formalisieren, und dafür
sorgen, dass es beim Skalieren der Datenmenge gut funktioniert und nicht
zu viele Tokens/Rechenzeit braucht":

1. ALLE Skalierungs-Regler sind jetzt in `pipeline/config.py` gebündelt
   (`PipelineConfig`), statt als verstreute Magic Numbers hier zu leben.
2. Der Prompt-INPUT ist jetzt UNABHÄNGIG von der Cluster-Größe gedeckelt:
   `select_representative_articles()` wählt bis zu
   `config.max_articles_per_story` Artikel aus (round-robin über Quellen,
   für Diversität statt zufälliger Reihenfolge) und kappt jeden Artikeltext
   auf `config.max_chars_per_article`. Ein Cluster mit 40 Artikeln kostet
   dadurch nicht 10x so viel wie einer mit 4.
3. ECHTE Web-Recherche statt einer bloßen Textanweisung: Punkt 7
   (Primärquellen) verlangt, dass das Modell ÜBER das mitgelieferte
   Quellmaterial hinaus recherchiert. Ohne ein echtes Such-Tool wäre das
   eine Einladung zu Halluzination, also bindet `synthesize_with_claude()`
   bei `research_depth="full"` das Anthropic-Server-Tool `web_search` ein
   (gedeckelt über `config.web_search_max_uses`). Bei `research_depth=
   "lite"` wird dieser Punkt NICHT ins Prompt aufgenommen und
   `primary_sources` serverseitig fix auf leer gesetzt (siehe
   `_finalize_story_dict`), das braucht tool-verifizierte URLs, die ohne
   Such-Tool nicht verlässlich sind.
   `market_correlation` (Punkt 10/9) ist ANDERS: hier ist auch OHNE
   Recherche-Tool eine ehrliche QUALITATIVE Einschätzung aus dem
   Modell-Allgemeinwissen möglich und erwünscht (Nutzer-Feedback
   24.08.2026: "sei sensibler bei Marktkorrelation" -- vorher fehlte das
   Feld in "lite" komplett aus dem Prompt, das Modell wusste nicht mal,
   dass es existiert). Konkrete Kurszahlen/`series` bleiben aber auch hier
   tabu und werden serverseitig hart entfernt, falls das Modell doch
   welche liefert, s. `STORY_JSON_SCHEMA_HINT_MARKET_LITE` und
   `_finalize_story_dict`.
4. Response-Parsing ist robust gegenüber Tool-Use-Antworten (mehrere
   Content-Blöcke) und hat eine Selbstkorrektur-Runde
   (`config.max_json_retries`), falls die letzte Text-Antwort kein valides
   JSON ist.
5. Token-Nutzung wird pro Story mitgeloggt (`_pipeline_meta`), als
   Diagnosefeld, nicht Teil des offiziellen `schema.py::Story`-Vertrags,
   vom Frontend ignoriert.

Neu in v7 (Nutzer-Feedback 27.08.2026: "Stakeholder sehen nicht schön aus,
mache daraus eine Pro/Con Section, diskutiere jeweils die Sinnhaftigkeit der
Massnahmen eines Politikers, bringe immer Perspektive und Gegenperspektive
ein"): jedes `stakeholders.pro`/`.con`-Element bekommt zusaetzlich zu
`reason` ein `counter`-Feld mit der staerksten echten Gegenperspektive zu
genau dieser Einschaetzung (kein Strawman), s. Punkt 7 der analytischen
Anweisungen unten und Feldbeschreibung im Schema. Dieselbe Perspektiven-/
Gegenperspektiven-Haltung gilt jetzt auch allgemein fuer `deep_dive`/
`cui_bono`, ausdruecklich auch bei reiner Faktenmeldung ohne offenen
Streit -- ohne dabei die STIL-Neutralitaetsvorgabe zu verletzen (beide
Seiten benennen, keine einnehmen).

Zwei Ausführungsmodi:
  1) `synthesize_with_claude(...)` ruft die Anthropic API auf.
  2) `build_prompt(...)`            baut nur den Prompt (Fallback, z.B. für
                                      manuelles Copy-Paste in ein LLM ohne
                                      API-Zugriff).
"""

from __future__ import annotations

import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from itertools import zip_longest

from pipeline.config import DEFAULT_CONFIG, PipelineConfig

STORY_JSON_SCHEMA_HINT_BASE = """
Gib AUSSCHLIESSLICH valides JSON zurück mit exakt diesen Feldern:

{
  "title": "kurzer, präziser Story-Titel",
  "theme_category": "GENAU EINER dieser 6 Werte, exakt so geschrieben (Kleinbuchstaben, keine anderen Werte erlaubt): \"security\" (Sicherheit & Militär), \"diplomacy\" (Diplomatie), \"trade\" (Handel & Wirtschaft), \"rights\" (Migration & Bürgerrechte), \"conflict\" (Konflikt & Krieg), \"surveillance\" (Überwachung & Innenpolitik). Waehle die am besten passende Kategorie, auch wenn mehrere denkbar waeren -- dieses Feld steuert die Filter-Chips im Frontend und MUSS gesetzt sein.",
  "one_line": "1 Satz, worum es geht. Darf [[Entitätsname]]-Referenzen enthalten.",

  "summary": [
    "3-6 Bullet-Points, jeder 1-2 Sätze: nicht nur der nackte Fakt, sondern mit knappem Kontext/Einordnung direkt im Satz (z.B. 'X, ein Rekordwert für Y' statt nur 'X'). Zusammen ergeben sie die Kernfakten der aktuellen Meldung, aber jeder Bullet soll für sich verständlich und angenehm lesbar sein, nicht nur eine Stichwort-Notiz.",
    "Synthetisiert über alle Quellen hinweg, KEINE 'Person X sagte'-Attribution hier, das gehört in 'quotes'.",
    "JEDE Erwähnung einer Entität aus 'entities' MUSS als [[Entitätsname]] geschrieben werden."
  ],

  "deep_dive": "3-5 Absätze Hintergrund/Kontext/warum wichtig, als Fließtext. Auch hier [[Entitätsname]]-Referenzen. Einfache, klare Sprache, die komplexe Zusammenhänge erklärt statt sie komplizierter klingen zu lassen.",

  "cui_bono": "2-4 Sätze: wer profitiert strukturell/strategisch, über die von den Quellen selbst gegebene Erklärung hinausgedacht, quellenübergreifend. [[Entitätsname]]-Referenzen nutzen.",

  "historical_threads": [
    {
      "id": "kurzer_slug",
      "title": "Kurzer Tab-Titel, z.B. 'USA-Iran-Konflikt' oder 'US-Einwanderungspolitik (SIV)'",
      "entries": [
        {
          "date": "grobe Zeitangabe, z.B. '1979' oder '2022-08'",
          "title": "kurzer Titel des Meilensteins",
          "one_line": "1 Satz Schlaglicht: was geschah, wie hängt es mit der heutigen Meldung zusammen. KEINE [[...]]-Syntax hier, wird nicht geparst.",
          "extended": "2-4 Sätze Vertiefung für alle, die tiefer gehen wollen (optional, aber wenn möglich ausfüllen). Auch hier KEINE [[...]]-Syntax."
        }
        // 3-6 Einträge pro Thread, chronologisch aufsteigend
      ]
    }
    // WICHTIG: 2-5 THREADS, aber NUR wenn wirklich unabhängige,
    // unterscheidbare Entwicklungslinien vorliegen. Frage dich aktiv:
    // "Ist diese Meldung der Konvergenzpunkt mehrerer Geschichten?" z.B.
    // eine geopolitische/inhaltliche Linie UND eine institutionelle/
    // politische Linie (ein Gesetz, ein Programm, eine Behörde, eine
    // Partei-Agenda). Lieber 2 wirklich distinkte Threads als 5
    // künstlich aufgefüllte.
  ],

  "entities": [
    {
      "name": "muss exakt mit den [[...]]-Referenzen übereinstimmen",
      "type": "person|organization|country|concept|event",
      "role_in_story": "1 Satz: was tut/ist diese Entität konkret IN DIESER Story",
      "profile": "2-4 Sätze strategisches Profil: wiederkehrende Interessen/Verhaltensmuster",
      "established": "Gründungs-/Bau-/Geburtsdatum falls zutreffend, sonst null",
      "image_url": "eine ECHTE, frei lizenzierte Bild-URL (z.B. von Wikimedia Commons, beginnend mit https://upload.wikimedia.org/...) falls bekannt/auffindbar, sonst null. NIEMALS eine URL erfinden."
    }
  ],

  "quotes": [
    {
      "text": "ECHTES, wörtliches Zitat aus einem der Quellartikel, unverändert übernommen.",
      "attribution": "Name/Rolle der Person ODER Name der Publikation, z.B. 'Senator Ruben Gallego' oder 'NPR'",
      "context": "optionaler 1-Satz-Kontext, wer/was das ist",
      "source_url": "URL des Artikels, aus dem das Zitat stammt"
    }
    // 1-3 Zitate. NUR echte, im Quelltext auffindbare Zitate, niemals
    // erfinden, niemals paraphrasieren. Bevorzugt ein wichtiger O-Ton einer
    // beteiligten Person UND/ODER eine besonders treffende journalistische
    // Einordnung. Kein Zitat erzwingen, wenn keines im Material vorhanden ist.
    // Das ist bewusst der EINZIGE Ort für konkrete Attributionen, siehe STIL.
  ],

  "political_theory": {
    "theory": "kurzer Name eines politikwissenschaftlichen Konzepts, das diese Story erhellt. Wenn der Fachbegriff selbst NICHT bereits als eigene Entität in 'entities' existiert (type: concept, mit eigenem 'profile'-Erklärtext), lege dort eine an und referenziere ihn hier als [[Fachbegriff]] -- WICHTIG, das macht ihn im Frontend anklickbar mit Begriffserklärung, genau wie Personen/Organisationen.",
    "points": ["3-5 Bullet-Points, die die Story konkret an das Konzept anschließen. Auch hier [[Entitätsname]]-Referenzen nutzen, inkl. bereits an anderer Stelle definierter Entitäten (z.B. eine Person oder ein Gesetz), wenn sie hier natürlich vorkommen."]
  },
  // NULL setzen, wenn kein Konzept wirklich passt, nicht erzwingen.
{RESEARCH_FIELDS}
  "connections": [{"source": "EntityA", "target": "EntityB", "relation": "kurze Beschreibung der Beziehung"}],
  "countries_covered": ["..."],
  "image_url": "EXAKT eine der 'BILD:'-URLs aus den Artikeln oben (das eines der Quellartikel, das am besten zur Story passt), NIEMALS eine URL erfinden oder veraendern -- wenn KEIN Artikel ein Bild hat, null setzen.",

  "stakeholders": {
    "pro": [
      {
        "entity": "muss exakt mit einem 'name' aus 'entities' uebereinstimmen",
        "reason": "1 knapper Satz: WORIN konkret der Vorteil/Gewinn besteht",
        "counter": "1-2 knappe Saetze: die STAERKSTE echte Gegenperspektive zu dieser Einschaetzung -- warum andere (Gegner, Betroffene, eine andere politische Seite) das anders sehen, relativieren oder bestreiten wuerden. Kein Strawman, eine ernsthafte Gegenposition. null nur, wenn wirklich keine nachvollziehbare Gegenposition existiert."
      }
    ],
    "con": [
      {
        "entity": "muss exakt mit einem 'name' aus 'entities' uebereinstimmen",
        "reason": "1 knapper Satz: WORIN konkret der Nachteil/Verlust besteht",
        "counter": "1-2 knappe Saetze: die STAERKSTE echte Gegenperspektive zu dieser Einschaetzung, s. Feldbeschreibung bei 'pro'. null nur, wenn wirklich keine existiert."
      }
    ],
    "note": "optionaler 1-Satz-Hinweis, z.B. Unsicherheit/Kontext, sonst null"
  }
  // 1-4 Eintraege je Seite (pro/con), NUR Akteure, die auch in 'entities'
  // auftauchen (damit sie im Frontend anklickbar sind). Leer lassen
  // ([]) statt einen Akteur zu erfinden, der nicht durch die Quellen
  // gedeckt ist. stakeholders selbst NULL setzen nur, wenn wirklich
  // weder Gewinner noch Verlierer identifizierbar sind (selten). `counter`
  // ist das Kernstueck der Pro/Con-Diskussion im Frontend (s. `counter`-
  // Feldbeschreibung oben) -- bitte moeglichst nie leer lassen, das ist
  // KEIN optionales Nice-to-have, sondern der Punkt der ganzen Sektion.
}
"""

# Nur in research_depth="full" ins Schema/Prompt aufgenommen, siehe
# Modul-Docstring Punkt 3. In "lite" werden primary_sources/
# market_correlation serverseitig fix leer/null gesetzt, s.
# `_finalize_story_dict`.
STORY_JSON_SCHEMA_HINT_RESEARCH = """
  "primary_sources": [
    {
      "title": "z.B. 'Blumenthal-Brief an Verteidigungsminister Hegseth'",
      "issuer": "z.B. 'Büro von Senator Richard Blumenthal' oder 'U.S. Federal Register'",
      "url": "echte URL des Primärdokuments",
      "date": "Datum falls bekannt, sonst null",
      "note": "optionaler Hinweis, z.B. wenn nur eingeschränkt zugänglich"
    }
    // 0-4 Einträge. NUR echte, mit dem Such-Tool recherchierte Primärquellen
    // (Regierungsdokumente, offizielle Statements, Gerichtsentscheidungen,
    // Pressemitteilungen von Behörden/Institutionen), NICHT journalistische
    // Berichterstattung darüber. Leer lassen statt eine URL zu erfinden.
  ],

  "market_correlation": {
    "has_correlation": true,
    "explanation": "2-4 Sätze: welcher Zusammenhang mit Finanzmärkten recherchiert wurde (oder warum keiner gefunden wurde, wenn has_correlation=false)",
    "series": [
      {
        "label": "z.B. 'Brent Crude Oil'",
        "raw_unit": "z.B. 'USD/Barrel'",
        "points": [{"date": "YYYY-MM-DD", "value": 100.0}],
        "source_url": "Quelle der Kursdaten"
      }
    ],
    "tickers": ["0-3 ECHTE Yahoo-Finance-Ticker-Symbole der oben genannten Instrumente (z.B. 'BZ=F' fuer Brent), NUR falls du dir bei der exakten Schreibweise sicher bist. Wird NUR genutzt, falls 'series' oben leer bleibt -- ein server-seitiger Dienst holt dann ECHTE Kursdaten fuer diese Ticker nach, statt dass die Story ganz ohne Chart bleibt."],
    "note": "Hinweis auf Näherungen/Indexierung, falls zutreffend"
  },
  // WICHTIG: has_correlation=false mit leerem 'series' ist ein voll
  // akzeptables, oft sogar wahrscheinlicheres Ergebnis. NIEMALS Kurszahlen
  // erfinden oder eine Korrelation herbeischreiben, die nicht recherchiert
  // ist. NULL setzen, wenn eine Marktrecherche gar nicht sinnvoll ist.

"""

# Leichtgewichtige Markt-Einschätzung OHNE Web-Recherche-Tool (Nutzer-
# Feedback 24.08.2026: "sei sensibler bei Marktkorrelation" -- vorher wurde
# dieses Feld in "lite" komplett aus dem Prompt entfernt, das Modell wusste
# nicht mal, dass es existiert, DESHALB gab es nie eine Korrelation, nicht
# weil das Modell geprüft und keine gefunden hätte. Jetzt: qualitative
# Einschätzung aus Modellwissen erlaubt, aber STRIKT ohne `series`/
# Kurszahlen (die sind ohne Tool nicht verifizierbar -- `_finalize_story_dict`
# entfernt eine `series` in diesem Modus notfalls hart, als zweite
# Absicherung gegen Halluzination zusätzlich zur Prompt-Anweisung).
STORY_JSON_SCHEMA_HINT_MARKET_LITE = """
  "market_correlation": {
    "has_correlation": true,
    "explanation": "2-4 Sätze AUS DEINEM ALLGEMEINWISSEN (keine Live-Recherche): welche Märkte/Anlageklassen bei diesem Themenfeld typischerweise reagieren und warum (z.B. bei neuen Zöllen: betroffene Aktienindizes/Branchen, Wechselkurse, Rohstoffe; bei Sanktionen: Energiepreise, betroffene Währungen; bei Zentralbankentscheidungen: Anleiherenditen). Sei GROSSZÜGIG beim Erkennen einer plausiblen Korrelation -- ein großer Handelskonflikt, neue Zölle, Sanktionen, ein Kriegsausbruch oder eine Zentralbankentscheidung haben so gut wie IMMER einen bekannten, plausiblen Marktbezug, den du aus Allgemeinwissen benennen kannst, auch ohne exakte tagesaktuelle Zahlen.",
    "tickers": ["0-3 ECHTE, offizielle Yahoo-Finance-Ticker-Symbole fuer die in 'explanation' genannten Instrumente, NUR wenn du dir bei der exakten Schreibweise wirklich sicher bist -- z.B. Aktien wie 'LMT' oder 'GEO', Indizes wie '^GSPC' oder '^VIX', Rohstoff-Futures wie 'BZ=F' (Brent) oder 'GC=F' (Gold), Waehrungspaare wie 'EURUSD=X'. Ein Server-seitiger Dienst (yfinance) holt fuer diese Ticker ECHTE historische Kursdaten und ersetzt damit deine Einschaetzung durch einen verifizierten Chart. Bei Unsicherheit ueber die exakte Schreibweise leer lassen ([]) statt zu raten -- ein falscher Ticker liefert schlicht keine Daten, ist also ungefaehrlich, aber ein erfundener sollte trotzdem vermieden werden."],
    "note": "kurzer Hinweis, dass dies eine Einschätzung aus Allgemeinwissen ist, keine live abgefragten Kursdaten"
  },
  // has_correlation=false ist ein akzeptables Ergebnis, aber NUR wenn
  // wirklich kein plausibler Marktbezug erkennbar ist (z.B. ein rein
  // innenpolitisches Verfahrensthema ohne wirtschaftliche Dimension) --
  // nicht aus reiner Vorsicht pauschal auf false setzen. NIEMALS `series`,
  // Kurszahlen oder Datenpunkte in diesem Feld angeben, das ist in diesem
  // Modus ohne Recherche-Tool nicht seriös möglich und wird serverseitig
  // ohnehin entfernt -- `tickers` ist die einzige Ausnahme, dafuer siehe
  // Feldbeschreibung oben.

"""

ANALYTICAL_INSTRUCTIONS_BASE = """\
Du bist Teil von Deeplitics, einem System, das politische Nachrichten NICHT
nur zusammenfasst, sondern ihre tiefere Struktur sichtbar macht. Wende bei
JEDEM Thema, unabhängig vom Inhalt, dieselbe analytische Haltung an:

1. Historisiere das Ereignis MEHRFACH. Eine Meldung ist fast immer der
   Konvergenzpunkt mehrerer unabhängiger Entwicklungslinien, nicht nur
   einer. Suche aktiv nach mindestens zwei Kategorien:
   a) einer geopolitischen/inhaltlichen Linie (der Konflikt/das Thema
      selbst, historisch zurückverfolgt),
   b) einer institutionellen/politischen Linie (ein Gesetz, ein Programm,
      eine Behörde, eine Partei-Agenda, die eigene Geschichte hat und
      unabhängig vom Thema in a) besteht).
   Baue für jede gefundene Linie einen eigenen Thread mit 3-6
   Meilensteinen. Erfinde keine Linie nur um eine Zielzahl zu erreichen.
2. Baue strategische Profile der beteiligten Akteure (Personen UND
   Institutionen), wiederkehrende Interessen und Verhaltensmuster, nicht
   nur Biografie.
3. Stelle explizit die Frage "Wem nützt das?", über die in den Quellen
   selbst genannte Erklärung hinaus, indem du die Quellen gegeneinander
   liest.
4. Bleib präzise und belegbar: erfinde keine Fakten und keine Bild-URLs.
   Historisches Allgemeinwissen ist erlaubt und erwünscht für die
   historischen Linien, aber als solches erkennbar sachlich, nicht als
   spekulative Behauptung verkauft.
5. Finde 1-3 echte, wörtliche Zitate (`quotes`) aus dem Quellmaterial: ein
   wichtiger O-Ton einer beteiligten Person und/oder eine treffende
   journalistische Einordnung. Niemals erfinden oder paraphrasieren, nie
   erzwingen, wenn keines vorhanden ist.
6. Nutze wenn vorhanden das og:image eines der Quellartikel als
   `image_url` (Hero-Bild der Story). Nie eine Bild-URL erfinden.
7. Perspektive UND Gegenperspektive (Nutzer-Feedback 27.08.2026: "diskutiere
   jeweils die Sinnhaftigkeit der Massnahmen eines Politikers, bringe immer
   Perspektive und Gegenperspektive ein"). Das gilt in ZWEI Formen:
   a) Fuer JEDEN Akteur in `stakeholders` (pro UND con): fuelle `counter`
      mit der staerksten echten Gegenposition zu `reason` -- warum jemand
      anderes (Gegner, Betroffene, eine andere politische Seite) diese
      Einschaetzung bestreiten, relativieren oder anders bewerten wuerde.
      Kein Strawman, eine ernsthaft vertretene Position.
   b) Auch bei reiner Faktenmeldung ohne offenen Streit: frage dich aktiv,
      wie die jeweils andere politische Seite oder ein betroffener Akteur
      dieselben Fakten anders einordnen wuerde, und lass das in
      `deep_dive`/`cui_bono` einfliessen. Das ist KEIN Freibrief, selbst
      Position zu beziehen: beide Seiten sachlich benennen, keine der
      beiden Positionen einnehmen, s. Neutralitaetsvorgabe in STIL unten.
{research_points}
STIL (gilt für summary/deep_dive/cui_bono, ausnahmslos):
- SYNTHETISCH, nicht als Mosaik: Verschmilz die Einzelartikel zu EINEM
  zusammenhängenden Verständnis. Schreib NICHT im Stil "Person X sagte
  gegenüber Publikation Y, dass..." oder "Laut einem Bericht von Z...".
  Named actors dürfen als HANDELNDE auftreten (wer tut/entscheidet/
  fordert was), aber nicht als zitierte Quelle einer Aussage im Fließtext,
  das ist ausschließlich Aufgabe von `quotes`. Die Herkunft der
  Informationen bleibt über `sources`/`article_urls`{primary_sources_note}
  weiter nachvollziehbar, nur eben nicht als Attributions-Prosa.
- Einfache, klare Sprache. Ziel ist, komplexe politische Zusammenhänge
  zugänglich zu erklären, nicht sie komplizierter klingen zu lassen. Der
  Text soll die Leserin mitnehmen, nicht abhängen.
- Strikt faktisch und neutral. Keine wertenden Adjektive, keine
  Zuspitzung, keine Meinung. Formuliere so, dass Menschen unterschiedlicher
  politischer Ausrichtung den Text als fair und ausgewogen empfinden.
- Verwende KEINE Gedankenstriche/Halbgeviertstriche (Em-Dashes, "—" oder
  " - " als Satzzeichen). Nutze stattdessen Punkte, Kommas oder Doppelpunkte.
"""

ANALYTICAL_INSTRUCTIONS_RESEARCH_POINTS = """\
8. Suche AKTIV mit dem `web_search`-Tool nach PRIMÄRQUELLEN, nicht nur nach
   journalistischer Berichterstattung: offizielle Regierungsdokumente,
   Pressemitteilungen von Behörden/Abgeordneten, Gerichtsentscheidungen,
   Statements internationaler Organisationen. Das ist, worauf sich die
   gesamte journalistische Berichterstattung letztlich stützt, und oft an
   Orten zu finden, an denen die meisten Nachrichtenleser nicht mehr
   nachsehen (Federal Register, Congressional Record, Gerichtsdatenbanken,
   Ministeriums-Websites, Pressemitteilungen einzelner Abgeordneter/
   Senatoren, Communiqués internationaler Gremien wie AU oder UN). Wird
   nichts Belastbares gefunden, bleibt `primary_sources` leer, keine URL
   erfinden. Nutze das Such-Tool sparsam und gezielt (wenige, präzise
   Anfragen), nicht erschöpfend.
9. Ordne die Story, wo ein Konzept wirklich passt, durch die Linse EINES
   politikwissenschaftlichen/politiktheoretischen Konzepts ein (z.B.
   zivil-militärische Aufsicht, Versicherheitlichung/Securitization,
   Prinzipal-Agent-Probleme, Escalation-Dominance, State Capture,
   Legitimitätstheorie). Das gehört NICHT in den Haupttext, sondern in das
   separate `political_theory`-Feld, das im Frontend hinter einem Button
   versteckt ist. Kein Konzept erzwingen, wenn keines wirklich passt,
   dann `political_theory: null`.
10. Prüfe mit dem `web_search`-Tool EHRLICH auf eine Marktkorrelation
   (`market_correlation`): Aktien, Rohstoffpreise, Indizes, Währungen, die
   recherchierbar auf dieses Ereignis reagiert haben. Eine nicht gefundene
   Korrelation ist ein vollständiges, oft das ehrlichere Ergebnis,
   `has_correlation: false` mit einer kurzen Begründung ist genauso
   wertvoll wie ein echter Fund. Niemals Kurszahlen erfinden oder einen
   Zusammenhang herbeischreiben. Wenn eine Marktrecherche für das Thema gar
   nicht sinnvoll ist, `market_correlation: null` setzen.
"""

ANALYTICAL_INSTRUCTIONS_LITE_NOTE = """\
8. Diese Story wird OHNE Web-Recherche-Tool erstellt (Kosten-/
   Zeit-optimierter Modus). Fülle `political_theory`, wenn ein Konzept
   wirklich passt, sonst `null`. `primary_sources` bleibt in diesem Modus
   leer (`[]`), dazu MUSST du nichts recherchieren oder ausdenken -- das
   braucht tool-verifizierte URLs, die hier nicht verfügbar sind, lass das
   Feld einfach weg oder setze es auf `[]`.
9. `market_correlation` FÜLLE trotzdem aus, aus deinem Allgemeinwissen
   (keine Recherche nötig, siehe Feld-Beschreibung im Schema oben für das
   genaue Format): ist ein plausibler Zusammenhang mit Finanzmärkten
   erkennbar (Aktien, Währungen, Rohstoffe, Anleihen)? Ein großer
   Handelsstreit mit hohen Zöllen, Sanktionen, ein Kriegsausbruch oder eine
   Zentralbankentscheidung haben praktisch immer einen bekannten
   Marktbezug -- benenne ihn qualitativ, auch ohne Recherche-Tool. NIEMALS
   konkrete Kurszahlen oder Datenpunkte erfinden, das gehört nicht in
   dieses Feld in diesem Modus. Nenne zusätzlich in `tickers` 0-3 ECHTE
   Yahoo-Finance-Symbole der Instrumente, die du in der Einschätzung
   benennst (nur falls du dir bei der exakten Schreibweise sicher bist,
   sonst leer lassen) -- ein Server-seitiger Dienst holt dafür nach der
   Synthese echte, verifizierte Kursdaten nach und macht aus deiner
   Einschätzung einen echten Chart.
"""


def _build_analytical_instructions(config: PipelineConfig) -> str:
    if config.research_depth == "full" and config.enable_web_search:
        return ANALYTICAL_INSTRUCTIONS_BASE.format(
            research_points=ANALYTICAL_INSTRUCTIONS_RESEARCH_POINTS,
            primary_sources_note="/`primary_sources`",
        )
    return ANALYTICAL_INSTRUCTIONS_BASE.format(
        research_points=ANALYTICAL_INSTRUCTIONS_LITE_NOTE,
        primary_sources_note="",
    )


def _build_schema_hint(config: PipelineConfig) -> str:
    # {RESEARCH_FIELDS} ist ein reiner Platzhalter-Marker (kein
    # str.format(), das Schema enthält massenhaft literale JSON-Klammern),
    # daher ein simpler str.replace() statt Format-Interpolation.
    if config.research_depth == "full" and config.enable_web_search:
        return STORY_JSON_SCHEMA_HINT_BASE.replace(
            "{RESEARCH_FIELDS}", STORY_JSON_SCHEMA_HINT_RESEARCH
        )
    # "lite": keine `primary_sources` (brauchen ein Such-Tool), aber eine
    # leichtgewichtige, qualitative `market_correlation` bleibt im Schema,
    # s. STORY_JSON_SCHEMA_HINT_MARKET_LITE-Docstring.
    return STORY_JSON_SCHEMA_HINT_BASE.replace(
        "{RESEARCH_FIELDS}", STORY_JSON_SCHEMA_HINT_MARKET_LITE
    )


def select_representative_articles(
    articles: list[dict],
    max_articles: int | None = None,
    max_chars: int | None = None,
    config: PipelineConfig = DEFAULT_CONFIG,
) -> list[dict]:
    """Wählt bis zu `max_articles` Artikel aus einem (potenziell großen)
    Cluster aus und kappt jeden Artikeltext auf `max_chars` Zeichen. Das
    hält Prompt-Größe (und damit Kosten/Latenz) für die Synthese
    UNABHÄNGIG von der tatsächlichen Cluster-Größe konstant beschränkt,
    auch wenn ein Cluster z.B. 40 statt 4 Artikel enthält.

    Auswahl per Round-Robin über die Quellen (`itertools.zip_longest`),
    nicht einfach die ersten N: das maximiert die Quellen-/
    Perspektivendiversität im Prompt, was der eigentliche Zweck der
    Multi-Quellen-Synthese ist, statt zufällig N Artikel derselben Quelle
    zu bevorzugen."""
    max_articles = max_articles if max_articles is not None else config.max_articles_per_story
    max_chars = max_chars if max_chars is not None else config.max_chars_per_article

    if len(articles) <= max_articles:
        selected = articles
    else:
        by_source: dict[str, list[dict]] = {}
        for a in articles:
            by_source.setdefault(a.get("source", "?"), []).append(a)
        selected = []
        for round_ in zip_longest(*by_source.values()):
            for a in round_:
                if a is not None:
                    selected.append(a)
                if len(selected) >= max_articles:
                    break
            if len(selected) >= max_articles:
                break

    capped = []
    for a in selected:
        text = (a.get("text") or a.get("summary") or "")
        capped.append({**a, "text": text[:max_chars]})
    return capped


def build_prompt(articles: list[dict], config: PipelineConfig = DEFAULT_CONFIG) -> str:
    """Öffentliche Fallback-API: nimmt einen ROHEN Cluster (nicht
    vorselektiert) und wählt selbst repräsentative Artikel aus. Intern
    nutzt `synthesize_with_claude` stattdessen `_build_prompt_text` direkt
    auf einer bereits vorher berechneten Auswahl, um sie nicht zweimal zu
    berechnen und um zu garantieren, dass Prompt und die tatsächlich an
    `article_urls` gemeldeten Artikel exakt übereinstimmen."""
    selected = select_representative_articles(articles, config=config)
    return _build_prompt_text(selected, config)


def _build_prompt_text(selected: list[dict], config: PipelineConfig) -> str:
    joined = "\n\n---\n\n".join(
        f"QUELLE: {a['source']} ({a.get('country','?')})\n"
        f"TITEL: {a['title']}\n"
        f"BILD (og:image, falls vorhanden -- NUR diese exakte URL darfst du "
        f"als 'image_url' verwenden, niemals eine andere erfinden): "
        f"{a.get('og_image') or 'keins gefunden'}\n"
        f"TEXT: {a.get('text') or a.get('summary','')}"
        for a in selected
    )
    research_hint = (
        "Recherchiere darüber hinaus aktiv mit dem web_search-Tool nach "
        "Primärquellen und einer möglichen Marktkorrelation (siehe Punkte 7 "
        "und 9), das Quellmaterial unten ist nur der Ausgangspunkt."
        if config.research_depth == "full" and config.enable_web_search
        else "Arbeite ausschließlich mit dem Quellmaterial unten plus "
        "deinem Allgemeinwissen (kein Such-Tool in diesem Modus)."
    )
    return f"""{_build_analytical_instructions(config)}

Du bekommst mehrere Nachrichtenartikel von verschiedenen Quellen zum
(vermutlich) selben politischen Ereignis oder Thema. {research_hint}

ARTIKEL:
{joined}

{_build_schema_hint(config)}
"""


def _extract_json_text(resp) -> str:
    """Antworten mit Tool-Use bestehen aus mehreren Content-Blöcken
    (server_tool_use, web_search_tool_result, text, ...). Die finale
    JSON-Antwort ist der LETZTE Text-Block."""
    texts = [block.text for block in resp.content if getattr(block, "type", None) == "text"]
    if not texts:
        raise ValueError("Antwort enthält keinen Text-Block (nur Tool-Use?).")
    return texts[-1]


def _parse_json_loose(text: str) -> dict:
    text = text.strip()
    # Manche Modellantworten packen JSON trotz Anweisung in einen
    # Markdown-Codeblock, das großzügig mit abfangen statt hart zu scheitern.
    fence_match = re.match(r"^```(?:json)?\s*\n(.*)\n```\s*$", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)
    elif text.startswith("```"):
        # Führender Codeblock-Marker ohne (oder mit abgeschnittenem)
        # schließendem Marker -- kommt vor, wenn `max_output_tokens` zu
        # knapp war und die Antwort mitten im JSON endet (gefunden im
        # ersten echten API-Testlauf, 18.08.2026). Den führenden Marker
        # trotzdem abstreifen: das JSON bleibt dann zwar unvollständig und
        # `json.loads` schlägt weiterhin fehl, aber mit einer aussagekräftigen
        # Fehlermeldung ("Unterminated string"/"Expecting ',' delimiter" an
        # der tatsächlichen Abbruchstelle) statt dem irreführenden "line 1
        # column 1", das sonst allein vom führenden ```json-Text kommt.
        text = re.sub(r"^```(?:json)?\s*\n", "", text)
    return json.loads(text)


class _RawBlock:
    """Bildet die Form eines `anthropic`-SDK-Content-Blocks nach
    (`.type`/`.text`), damit `_extract_json_text` beide Antwortformen
    identisch behandeln kann."""

    def __init__(self, raw: dict):
        self.type = raw.get("type")
        self.text = raw.get("text")


class _RawUsage:
    def __init__(self, raw: dict):
        self.input_tokens = raw.get("input_tokens", 0)
        self.output_tokens = raw.get("output_tokens", 0)


class _RawResponse:
    """Bildet die Form eines `anthropic`-SDK-Message-Objekts nach
    (`.content`/`.usage`/`.stop_reason`), erzeugt aus dem rohen
    HTTP-JSON-Body. `stop_reason` wird gebraucht, um "Antwort mitten im
    JSON abgeschnitten, weil `max_tokens` erreicht" (stop_reason ==
    "max_tokens") von echten Formatfehlern zu unterscheiden, s.
    `synthesize_with_claude`."""

    def __init__(self, body: dict):
        self.content = [_RawBlock(b) for b in body.get("content", [])]
        self.usage = _RawUsage(body.get("usage", {}))
        self.stop_reason = body.get("stop_reason")


ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"


def _create_message(
    api_key: str,
    model: str,
    max_tokens: int,
    messages: list[dict],
    tools: list[dict] | None,
):
    """Ruft die Anthropic Messages API auf. Nutzt das offizielle `anthropic`
    SDK, wenn installiert (der Normalfall in jeder regulären Umgebung,
    inkl. eingebautem Retry/Backoff). Ist das SDK nicht installierbar (wie
    in dieser Cloud-Sandbox, s. docs/NETWORK_NOTES.md, PyPI ist blockiert,
    `api.anthropic.com` selbst aber erreichbar), fällt es auf einen
    schlanken direkten HTTP-Call über `requests` zurück (das Paket, das die
    restliche Pipeline ohnehin schon nutzt). Beide Pfade geben ein Objekt
    mit derselben `.content`/`.usage`-Form zurück, der Rest des Moduls muss
    den Unterschied nicht kennen."""
    payload = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if tools:
        payload["tools"] = tools

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        return client.messages.create(**payload)
    except ImportError:
        pass

    import time as _time

    import requests

    headers = {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_API_VERSION,
        "content-type": "application/json",
    }
    last_exc: Exception | None = None
    for backoff_attempt in range(4):
        try:
            r = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload, timeout=180)
        except requests.RequestException as exc:
            last_exc = exc
            _time.sleep(2**backoff_attempt)
            continue
        if r.status_code == 200:
            return _RawResponse(r.json())
        if r.status_code in (429, 500, 502, 503, 529):
            last_exc = RuntimeError(f"Anthropic API {r.status_code}: {r.text[:300]}")
            _time.sleep(2**backoff_attempt)
            continue
        raise RuntimeError(f"Anthropic API Fehler {r.status_code}: {r.text[:500]}")
    raise RuntimeError(f"Anthropic API nach mehreren Versuchen nicht erreichbar: {last_exc}")


def synthesize_with_claude(
    articles: list[dict], config: PipelineConfig = DEFAULT_CONFIG
) -> dict:
    """Ruft die Anthropic API auf (via SDK oder HTTP-Fallback, s.
    `_create_message`). Braucht ANTHROPIC_API_KEY.

    `config.research_depth` steuert, ob das `web_search`-Server-Tool
    gebunden wird (siehe Modul-Docstring Punkt 3). Bei ungültigem JSON in
    der Antwort wird bis zu `config.max_json_retries` mal eine
    Selbstkorrektur-Runde angehängt, statt sofort zu scheitern."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY ist nicht gesetzt.")

    selected = select_representative_articles(articles, config=config)
    prompt = _build_prompt_text(selected, config)

    tools = None
    if config.research_depth == "full" and config.enable_web_search:
        tools = [
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": config.web_search_max_uses,
            }
        ]

    messages = [{"role": "user", "content": prompt}]
    last_error: Exception | None = None
    data: dict | None = None
    resp = None
    # Wächst nur bei stop_reason == "max_tokens" (echtes Budget-Problem),
    # bleibt sonst konstant. Gedeckelt, damit ein einzelner hartnäckiger
    # Cluster nicht unbegrenzt teurer wird als der Rest der Charge.
    current_max_tokens = config.max_output_tokens
    MAX_TOKEN_CEILING = 16000

    for attempt in range(config.max_json_retries + 1):
        resp = _create_message(
            api_key=api_key,
            model=config.model,
            max_tokens=current_max_tokens,
            messages=messages,
            tools=tools,
        )
        try:
            text = _extract_json_text(resp)
            data = _parse_json_loose(text)
            break
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < config.max_json_retries:
                truncated = getattr(resp, "stop_reason", None) == "max_tokens"
                if truncated:
                    # Echtes Budget-Problem (gefunden im ersten echten
                    # API-Testlauf, 18.08.2026: das volle Story-Schema
                    # sprengt bei mehreren historischen Threads/Entities
                    # leicht ein zu knappes `max_output_tokens`). Eine
                    # "gib nur JSON zurück"-Korrekturrunde würde daran
                    # nichts ändern, also stattdessen denselben Prompt
                    # FRISCH (ohne den abgeschnittenen Kontext, der nur
                    # Tokens kostet) mit größerem Budget erneut senden.
                    current_max_tokens = min(
                        int(current_max_tokens * 1.6), MAX_TOKEN_CEILING
                    )
                    messages = [{"role": "user", "content": prompt}]
                else:
                    # Nur die Text-Blöcke zurückspiegeln (als einfacher String,
                    # nicht die rohen Content-Blöcke): das ist für BEIDE
                    # Antwortpfade (SDK-Objekte vs. rohe HTTP-JSON-Blöcke)
                    # gleichermaßen sicher JSON-serialisierbar, verliert dafür
                    # Tool-Use-Details, die für eine reine Format-Korrektur
                    # nicht gebraucht werden.
                    fallback_texts = [
                        b.text for b in resp.content if getattr(b, "type", None) == "text" and b.text
                    ]
                    messages.append(
                        {
                            "role": "assistant",
                            "content": "\n".join(fallback_texts) or "(keine Text-Antwort)",
                        }
                    )
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "Das war kein valides JSON (oder kein Text-Block "
                                "vorhanden). Gib jetzt AUSSCHLIESSLICH das "
                                "JSON-Objekt zurück, ohne Markdown-Codeblock, "
                                "ohne einleitenden oder abschließenden Text."
                            ),
                        }
                    )

    if data is None:
        raise RuntimeError(
            f"Konnte nach {config.max_json_retries + 1} Versuch(en) kein "
            f"valides JSON aus der Modellantwort parsen: {last_error}"
        )

    return _finalize_story_dict(data, selected, config=config, resp=resp)


VALID_THEME_CATEGORIES = {"security", "diplomacy", "trade", "rights", "conflict", "surveillance"}


def _finalize_story_dict(
    data: dict,
    articles: list[dict],
    config: PipelineConfig = DEFAULT_CONFIG,
    resp=None,
) -> dict:
    data["id"] = str(uuid.uuid4())[:8]
    # Zeitstempel, wann diese Story generiert wurde -- gebraucht fuer die
    # Story-AKKUMULATION in run_pipeline.py (neueste zuerst einsortiert)
    # und als ehrliches "Stand"-Datum je Story, nicht nur global im Header.
    data["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    data["sources"] = sorted({a["source"] for a in articles})
    data["article_urls"] = [a.get("link") or a.get("url") for a in articles]

    # HARTE Absicherung (gefunden 23.08.2026): das Frontend filtert Storys
    # client-seitig nach `theme_category` gegen genau diese 6 Werte -- ein
    # fehlender/falscher Wert macht eine sonst valide Story unsichtbar,
    # OHNE Fehler irgendwo im Log. Lieber ein geloggter Fallback als eine
    # stumm verschwindende Story.
    cat = data.get("theme_category")
    if cat not in VALID_THEME_CATEGORIES:
        print(
            f"[warn] Story '{data.get('title', '?')}': ungueltige/fehlende "
            f"theme_category ({cat!r}), fallback auf 'conflict'.",
            file=sys.stderr,
        )
        data["theme_category"] = "conflict"

    # `primary_sources` braucht tool-verifizierte URLs -- in "lite" HART auf
    # leer erzwingen statt dem Modell zu vertrauen, das ist die eigentliche
    # Garantie gegen Halluzination ohne Such-Tool.
    # `market_correlation` bleibt in "lite" dagegen erhalten (Nutzer-
    # Feedback 24.08.2026: "sei sensibler bei Marktkorrelation" -- vorher
    # wurde es hier komplett genullt, obwohl das Modell inzwischen eine
    # ehrliche QUALITATIVE Einschätzung liefern darf, s.
    # STORY_JSON_SCHEMA_HINT_MARKET_LITE). Eine `series` (konkrete
    # Kurszahlen) ist in diesem Modus aber NIE verifiziert -- die wird hier
    # als zweite Absicherung zusätzlich zur Prompt-Anweisung hart entfernt,
    # falls das Modell trotzdem eine geliefert hat.
    if config.research_depth != "full" or not config.enable_web_search:
        data["primary_sources"] = []
        mc = data.get("market_correlation")
        if isinstance(mc, dict):
            mc.pop("series", None)
            mc["verified_live"] = False
            data["market_correlation"] = mc
        else:
            data["market_correlation"] = None
    else:
        mc = data.get("market_correlation")
        if isinstance(mc, dict):
            mc["verified_live"] = True

    if resp is not None and getattr(resp, "usage", None) is not None:
        data["_pipeline_meta"] = {
            "model": config.model,
            "research_depth": config.research_depth,
            "articles_used": len(articles),
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
        }
    return data


if __name__ == "__main__":
    from pathlib import Path

    cluster_file = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not cluster_file:
        print("Usage: python3 synthesize_story.py <cluster.json> [--full]")
        raise SystemExit(1)
    cfg = DEFAULT_CONFIG
    if "--full" in sys.argv:
        from pipeline.config import FULL_DEPTH_CONFIG

        cfg = FULL_DEPTH_CONFIG
    arts = json.loads(cluster_file.read_text())
    try:
        story = synthesize_with_claude(arts, config=cfg)
        print(json.dumps(story, indent=2, ensure_ascii=False))
    except RuntimeError as e:
        print(f"[info] {e}\n--- PROMPT (manuell an ein LLM geben) ---\n")
        print(build_prompt(arts, config=cfg))
