"""
Verifizierte Marktdaten via yfinance (Nutzer-Feedback 24.08.2026: "sei
sensibler bei Marktkorrelation!" und, nachdem ein anderer Chat dabei ein
Chaos angerichtet hat, "überlege dir wie man wirklich die yfinance
Einbindung machen kann").

WICHTIG -- bewusst ANDERS gebaut als der Vorschlag aus dem anderen Chat:
Dort wurde ein komplett neues, paralleles Datenfeld `story.market_impacts`
eingeführt (Liste von Ticker-Karten), erzeugt aus einem hartkodierten
Text-Keyword->Ticker-Dictionary (`TICKER_MAPPING = {"Tesla": "TSLA", ...}`),
UND `app.js::marketHtml` komplett umgeschrieben, um dieses neue Feld statt
des bestehenden `market_correlation` zu rendern. Das hätte zwei
konkurrierende Markt-Datenmodelle im selben Projekt geschaffen und alles
bisher gebaute UI (Bauhaus-Chart-Card, "Einschätzung aus Allgemeinwissen"-
Badge, echte vs. qualitative Unterscheidung, s. synthesize_story.py)
stillschweigend überschrieben. Keywords aus dem Story-Text zu grep'en ist
außerdem viel ungenauer als das Modell selbst zu fragen, das den vollen
Kontext der Story kennt.

Deshalb hier stattdessen: dieses Modul ERGÄNZT nur das BESTEHENDE
`market_correlation`-Feld. Das Modell selbst darf in seiner JSON-Antwort
optional ein paar echte Yahoo-Finance-Ticker nennen, wenn es einen klaren
Marktbezug sieht (s. `STORY_JSON_SCHEMA_HINT_MARKET_LITE` und
`STORY_JSON_SCHEMA_HINT_RESEARCH` in synthesize_story.py, Feld
`market_correlation.tickers`). Dieses Modul holt für genau diese Ticker
ECHTE historische Kursdaten von Yahoo Finance (yfinance, kostenlos, kein
API-Key nötig) und füllt damit `market_correlation.series` -- im EXAKT
selben Format, das `app.js::marketHtml`/`drawMarketChart` bereits für
`research_depth="full"` rendert. Keine neue Datenstruktur, KEINE
Frontend-Änderung nötig: eine bisher nur qualitative Einschätzung (lite-
Modus) wird dadurch zu einem echten, mit Zahlen belegten Chart aufgewertet,
`verified_live` wechselt von False auf True.

Läuft NACH der Synthese (s. run_pipeline.py), pro Story, mit try/except
drumherum -- ein yfinance-Ausfall (Rate-Limit, Netzwerk, ungültiger
Ticker) darf niemals den Lauf oder die Story selbst zum Absturz bringen,
die Story bleibt dann einfach bei ihrer bisherigen qualitativen
Einschätzung ohne Chart.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

# Sicherheitsgrenze: nicht mehr als ein paar Ticker pro Story abfragen,
# auch wenn das Modell mehr genannt hat -- yfinance-Aufrufe sind zwar
# kostenlos, aber nicht kostenlos an ZEIT (mehrere sequentielle HTTP-Calls
# pro Story), und niemand braucht 10 Charts auf einer Story-Seite.
MAX_TICKERS_PER_STORY = 3
LOOKBACK_DAYS = 10
LOOKAHEAD_DAYS = 10


def _parse_center_date(story: dict) -> datetime:
    """Story-Datum als Mittelpunkt fuers Kursfenster, Fallback auf heute
    falls fehlend/kaputt -- besser ein leicht falsches Fenster als ein
    kompletter Absturz."""
    raw = story.get("generated_at")
    if raw:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _fetch_ticker_series(ticker: str, center: datetime) -> dict | None:
    """Echte Tagesschlusskurse fuer EINEN Ticker im Fenster um `center`,
    im Format, das app.js::drawMarketChart erwartet. None bei jedem
    Fehlschlag (falscher/erfundener Ticker, kein Handel in dem Zeitraum,
    Netzwerk/Rate-Limit) -- wird vom Aufrufer als "kein Ticker" behandelt,
    nicht als harter Fehler."""
    try:
        import yfinance as yf
    except ImportError:
        print("[info] yfinance nicht installiert -- Marktdaten-Verifizierung übersprungen.", file=sys.stderr)
        return None

    try:
        start = (center - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")
        # +1 Tag, damit `end` (yfinance-Semantik: exklusiv) den letzten
        # gewuenschten Tag noch mit einschliesst.
        end = (center + timedelta(days=LOOKAHEAD_DAYS + 1)).strftime("%Y-%m-%d")
        hist = yf.Ticker(ticker).history(start=start, end=end, interval="1d")
        if hist is None or hist.empty or "Close" not in hist.columns:
            return None
        points = [
            {"date": idx.strftime("%Y-%m-%d"), "value": round(float(close), 2)}
            for idx, close in hist["Close"].items()
        ]
        # Ein einzelner Punkt ergibt keinen sinnvollen Chart/keine
        # erkennbare Bewegung -- dann lieber gar nicht anzeigen.
        if len(points) < 2:
            return None
        return {
            "label": ticker,
            "raw_unit": "USD",
            "points": points,
            "source_url": f"https://finance.yahoo.com/quote/{ticker}",
        }
    except Exception as exc:  # noqa: BLE001 - jeder yfinance-Fehler ist hier nicht-fatal
        print(f"    [warn] yfinance-Abruf für Ticker '{ticker}' fehlgeschlagen: {exc}", file=sys.stderr)
        return None


def enrich_market_data(story: dict) -> bool:
    """Veredelt `story['market_correlation']` mit echten yfinance-Daten,
    falls das Modell `tickers` genannt UND noch keine `series` vorhanden
    ist (in research_depth="full" kann bereits eine web_search-basierte
    `series` existieren -- die wird NICHT überschrieben, um keine bereits
    recherchierte Einordnung zu verlieren). Mutiert `story` in-place.
    Gibt True zurück, wenn mindestens ein Ticker erfolgreich verifiziert
    wurde (rein informativ fürs Logging)."""
    mc = story.get("market_correlation")
    if not isinstance(mc, dict) or not mc.get("has_correlation"):
        return False
    if mc.get("series"):
        # Schon eine (z.B. recherchierte) series vorhanden -- nicht anfassen.
        mc.pop("tickers", None)
        return False

    tickers = [t for t in (mc.get("tickers") or []) if isinstance(t, str) and t.strip()]
    mc.pop("tickers", None)  # internes Zwischenfeld, nie ins finale JSON/Frontend
    if not tickers:
        return False

    center = _parse_center_date(story)
    series = []
    for ticker in tickers[:MAX_TICKERS_PER_STORY]:
        s = _fetch_ticker_series(ticker.strip(), center)
        if s:
            series.append(s)

    if not series:
        return False

    mc["series"] = series
    mc["verified_live"] = True
    note = (mc.get("note") or "").strip()
    verified_note = "Kursdaten via Yahoo Finance (yfinance), echte Tagesschlusskurse."
    mc["note"] = f"{note} {verified_note}".strip() if note else verified_note
    return True


def enrich_all_stories(stories: list[dict]) -> list[dict]:
    """Batch-Variante über eine ganze Story-Liste, mutiert und gibt
    dieselbe Liste zurück -- ein einzelner Story-Fehlschlag darf die
    anderen Storys nicht mit runterreissen."""
    n_ok = 0
    for story in stories:
        try:
            if enrich_market_data(story):
                n_ok += 1
        except Exception as exc:  # noqa: BLE001
            print(f"    [warn] Marktdaten-Anreicherung für '{story.get('title', '?')}' fehlgeschlagen: {exc}", file=sys.stderr)
    if n_ok:
        print(f"[info] {n_ok} Storys mit echten Yahoo-Finance-Kursdaten verifiziert.", file=sys.stderr)
    return stories
