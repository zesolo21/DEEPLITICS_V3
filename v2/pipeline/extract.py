"""
Schritt 3: LLM-gestuetzte Extraktion (Bauanleitung Abschnitt 3).

Fuer jeden Thread wird aus den zugehoerigen Artikeln extrahiert:
- der aktuelle Faktenkern (2-3 Saetze, bei jedem relevanten Update neu
  geschrieben)
- ein neuer Zeitleisten-Eintrag pro Artikel (was war an diesem Tag neu)
- die beteiligten Akteure

Der Systemprompt weist das Modell ausdruecklich an, NUR belegbare Fakten
aus den Artikeln zu verwenden und keine eigenen Bewertungen einzufuegen
(Abschnitt 6: technisch/prompt-seitig durchgesetzte Regel).

Pluggable: mit gesetztem ANTHROPIC_API_KEY laeuft ein echter API-Call
(HTTP-Fallback-Pattern wie im v1-Prototyp, siehe
../../pipeline/synthesize_story.py). Ohne Key wird auf die unten
hinterlegten Fixtures zurueckgegriffen -- das sind ECHTE, von mir (als
das die Bauanleitung umsetzende LLM) unter Beachtung derselben Regel
(nur Fakten aus den Artikeln, keine Wertung) erstellte Extraktionen fuer
genau die Testartikel aus test_articles.py, keine Platzhalter-Mocks.
Siehe v2/README.md fuer die vollstaendige Begruendung dieser Entscheidung.
"""

from __future__ import annotations

import json
import os
from typing import Optional

import requests

from pipeline.models import Article

SYSTEM_PROMPT = (
    "Du extrahierst aus mehreren Nachrichtenartikeln zum selben Ereignisstrang "
    "einen Faktenkern (2-3 Saetze), einen Zeitleisten-Eintrag pro Artikel "
    "(Datum + kurze Beschreibung, was an diesem Tag neu war) und eine Liste "
    "beteiligter Akteure (Personen, Institutionen, Laender). Nutze "
    "AUSSCHLIESSLICH Informationen, die tatsaechlich in den gegebenen "
    "Artikeln stehen. Fuege KEINE eigenen Bewertungen, Einschaetzungen oder "
    "nicht belegte Zusatzinformationen hinzu. Antworte ausschliesslich mit "
    "einem JSON-Objekt der Form "
    '{"fact_core": str, "timeline": [{"date": str, "description": str}], '
    '"actors": [str]}.'
)


def extract_thread_fields(
    articles: list[Article], api_key: Optional[str] = None
) -> dict:
    """Gibt {"fact_core", "timeline", "actors"} fuer die gegebenen Artikel
    eines Threads zurueck."""

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return _extract_via_api(articles, key)
    return _extract_offline(articles)


def _extract_via_api(articles: list[Article], api_key: str) -> dict:
    articles_blob = "\n\n".join(
        f"[Artikel {a.id} | Quelle: {a.source} | Datum: {a.published_at}]\n"
        f"Titel: {a.title}\n{a.text}"
        for a in articles
    )
    payload = {
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": 1200,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": articles_blob}],
    }
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def _extract_offline(articles: list[Article]) -> dict:
    key = tuple(sorted(a.id for a in articles))
    fixture = _OFFLINE_EXTRACTIONS.get(key)
    if fixture is None:
        # Fallback fuer unbekannte Artikel-Kombinationen (z.B. bei echten,
        # nicht in den Fixtures hinterlegten RSS-Daten ohne API-Key):
        # ehrlich leer/minimal statt zu erfinden.
        return {
            "fact_core": "",
            "timeline": [
                {"date": a.published_at, "description": a.title} for a in articles
            ],
            "actors": [],
        }
    return fixture


# Von mir (als LLM) direkt erstellte, echte Extraktionen der Testartikel --
# key = sortiertes Tupel der Artikel-IDs, die zu genau diesem Thread
# gehoeren (stabil ueber Clustering-Laeufe hinweg, im Gegensatz zur
# zufaellig generierten Thread-ID).
_OFFLINE_EXTRACTIONS: dict[tuple, dict] = {
    ("a01", "a02", "a03"): {
        "fact_core": (
            "Die EU-Kommission hat einen Gesetzesvorschlag für beschleunigte "
            "Grenzverfahren bei Asylanträgen aus Ländern mit niedriger "
            "Anerkennungsquote vorgelegt (Bearbeitung binnen zwölf Wochen an "
            "der Außengrenze). Die Mitgliedstaaten sind uneins: Italien und "
            "Griechenland begrüßen den Vorschlag, Polen und Ungarn lehnen "
            "zusätzliche Verpflichtungen ab, Deutschland fordert "
            "Nachbesserungen beim Rechtsschutz. Das Europaparlament berät den "
            "Vorschlag im September, eine Einigung gilt frühestens für 2027 "
            "als realistisch."
        ),
        "timeline": [
            {"date": "2026-08-15", "description": "EU-Kommission legt Vorschlag für beschleunigte Grenzverfahren vor."},
            {"date": "2026-08-16", "description": "Mitgliedstaaten reagieren uneinheitlich, Deutschland fordert Nachbesserungen beim Rechtsschutz."},
            {"date": "2026-08-17", "description": "Kritik an begrenzter Reichweite der Reform, Beratung im Europaparlament für September angekündigt."},
        ],
        "actors": ["EU-Kommission", "Ylva Berg", "Deutschland", "Italien", "Griechenland", "Polen", "Ungarn", "Europaparlament"],
    },
    ("a04", "a05", "a06"): {
        "fact_core": (
            "Das Bundeskabinett hat die teilweise Aussetzung der "
            "Schuldenbremse für zusätzliche Verteidigungsausgaben beschlossen, "
            "um bis 2029 rund 45 Milliarden Euro zusätzlich für die Bundeswehr "
            "bereitzustellen. Die Opposition kritisiert fehlende "
            "Gegenfinanzierung. Sozialverbände fordern vergleichbare "
            "Ausnahmen für Bildung und sozialen Wohnungsbau, was die "
            "Koalition derzeit ablehnt; laut Finanzministerium sind keine "
            "Steuererhöhungen geplant, die Mittel werden über neue Schulden "
            "finanziert."
        ),
        "timeline": [
            {"date": "2026-08-14", "description": "Kabinett beschließt Aussetzung der Schuldenbremse für 45 Milliarden Euro zusätzliche Verteidigungsausgaben bis 2029."},
            {"date": "2026-08-15", "description": "Sozialverbände fordern vergleichbare Ausnahmen für Bildung und sozialen Wohnungsbau."},
            {"date": "2026-08-18", "description": "Finanzministerium bestätigt Finanzierung über neue Schulden statt Steuererhöhungen."},
        ],
        "actors": ["Bundeskabinett", "Jonas Reuter", "Bundeswehr", "Paritätischer Wohlfahrtsverband"],
    },
    ("a09", "a10", "a11"): {
        "fact_core": (
            "Die NATO-Mitgliedstaaten haben ein neues Ausgabenziel von 3,5 "
            "Prozent des BIP für Kernverteidigung plus 1,5 Prozent für "
            "sicherheitsrelevante Infrastruktur beschlossen. Deutschland "
            "sagte zu, das Ziel bis 2032 zu erreichen, was laut "
            "Haushaltsexperten zusätzlich 60 bis 80 Milliarden Euro jährlich "
            "erfordert. Mehrere südeuropäische Mitgliedstaaten äußerten wegen "
            "ihrer Haushaltslage Vorbehalte, Kritiker verweisen auf "
            "ausbleibende begleitende Rüstungskontroll-Initiativen."
        ),
        "timeline": [
            {"date": "2026-08-14", "description": "NATO-Gipfel beschließt neues 3,5-Prozent-Ausgabenziel, Deutschland sagt Erreichung bis 2032 zu."},
            {"date": "2026-08-15", "description": "Haushaltsexperten schätzen zusätzlichen Finanzierungsbedarf von 60-80 Milliarden Euro jährlich für Deutschland."},
            {"date": "2026-08-16", "description": "Kritik an ausbleibenden begleitenden Rüstungskontroll-Initiativen wird lauter."},
        ],
        "actors": ["NATO", "Lars Eriksen", "Deutschland", "Bundesverteidigungsministerium"],
    },
    ("a07", "a08"): {
        "fact_core": (
            "Nordrhein-Westfalen und Brandenburg haben angekündigt, den "
            "Kohleausstieg in ihren Bundesländern auf 2030 vorzuziehen, fünf "
            "Jahre früher als im Bundesgesetz vorgesehen. Das "
            "Bundeswirtschaftsministerium unterstützt den Schritt und prüft "
            "zusätzliche Strukturhilfen; Gewerkschaften warnen vor "
            "Arbeitsplatzverlusten ohne rechtzeitige Hilfen."
        ),
        "timeline": [
            {"date": "2026-08-16", "description": "NRW und Brandenburg ziehen Kohleausstieg auf 2030 vor, Bundeswirtschaftsministerium prüft Strukturhilfen."},
            {"date": "2026-08-17", "description": "Kommentar kritisiert fehlenden Netzausbau als eigentliches Problem hinter der Ankündigung."},
        ],
        "actors": ["Nordrhein-Westfalen", "Brandenburg", "Bundeswirtschaftsministerium"],
    },
    ("a12", "a13"): {
        "fact_core": (
            "Die Kultusministerkonferenz hat den Digitalpakt Schule 2.0 "
            "beschlossen: Bund und Länder wollen in den kommenden fünf "
            "Jahren rund 6 Milliarden Euro in digitale Infrastruktur, "
            "IT-Support und Lehrkräftefortbildung investieren. Der "
            "Lehrerverband begrüßt den Beschluss, weist aber darauf hin, "
            "dass er den akuten Lehrkräftemangel (bundesweit rund 35.000 "
            "fehlende Stellen) nicht löst."
        ),
        "timeline": [
            {"date": "2026-08-17", "description": "Kultusministerkonferenz beschließt Digitalpakt Schule 2.0 mit rund 6 Milliarden Euro über fünf Jahre."},
            {"date": "2026-08-18", "description": "Lehrerverbände fordern zusätzliche Maßnahmen gegen den akuten Lehrkräftemangel."},
        ],
        "actors": ["Kultusministerkonferenz", "Lehrerverband"],
    },
    ("a14", "a15"): {
        "fact_core": (
            "Die Bundesregierung hat einen ständigen, per Losverfahren aus "
            "160 Bürgerinnen und Bürgern besetzten Bürgerrat eingerichtet, "
            "der Empfehlungen zu Demokratie- und Wahlrechtsfragen erarbeiten "
            "soll. Erste Themen sind eine mögliche Wahlrechtsreform und mehr "
            "Transparenz bei der Parteienfinanzierung, erste Empfehlungen "
            "werden für Frühjahr 2027 erwartet; die Empfehlungen sind "
            "rechtlich unverbindlich, der Bundestag entscheidet frei über "
            "eine Umsetzung."
        ),
        "timeline": [
            {"date": "2026-08-13", "description": "Bundesregierung richtet ständigen, per Losverfahren besetzten Bürgerrat ein."},
            {"date": "2026-08-18", "description": "Bürgerrat nimmt Arbeit auf, erste Themen: Wahlrechtsreform und Parteienfinanzierung."},
        ],
        "actors": ["Bundesregierung", "Bürgerrat", "Bundestag"],
    },
    ("a16",): {
        "fact_core": (
            "Ein Jahr nach Inkrafttreten des nationalen KI-Gesetzes hat eine "
            "unabhängige Kommission einen ersten Evaluierungsbericht "
            "vorgelegt, der uneinheitliche Behördenpraxis bei "
            "Hochrisiko-Anwendungen feststellt, aber noch keine konkreten "
            "Reformempfehlungen ausspricht. Das Digitalministerium kündigte "
            "an, den Bericht zu prüfen, nannte aber keinen Zeitplan für "
            "mögliche Anpassungen."
        ),
        "timeline": [
            {"date": "2026-08-12", "description": "Unabhängige Kommission legt ersten Evaluierungsbericht zum KI-Gesetz vor."},
        ],
        "actors": ["Digitalministerium", "Evaluierungskommission KI-Gesetz"],
    },
}
