"""
Einmaliger Anreicherungsschritt (19.08.2026): macht die zentralen Fachbegriffe
in `political_theory.theory` / `.points` jeder Story anklickbar.

Hintergrund: der Nutzer wollte, dass wichtige Begriffe in der politischen
Theorie -- Fachbegriffe, benannte Konzepte, Denkschulen -- genau wie
Entitaeten im Fliesstext anklickbar sind und eine Begriffserklaerung
liefern, plus (wo verifiziert vorhanden) einen Wikipedia-Link.

Vorgehen:
1. Fuer jede Story werden 1-3 neue "concept"-Entitaeten zu `entities[]`
   hinzugefuegt (Theorie-Fachbegriffe), mit von mir selbst geschriebenem
   Erklaertext (echtes politikwissenschaftliches Wissen, keine
   Erfindung) und -- wo per Recherche-Agent tatsaechlich verifiziert --
   einem echten Wikipedia-Link. Wo keine verifizierte Seite gefunden
   wurde (z.B. "Begrenzte Zugangsordnungen"), bleibt wikipedia_url
   bewusst leer statt geraten.
2. In `political_theory.theory` bzw. `.points` wird der exakte
   Text-Ausschnitt, der dem neuen Begriff entspricht, mit `[[...]]`
   markiert -- demselben Inline-Link-Format, das `linkify()` im Frontend
   bereits fuer `summary`/`deep_dive`/`cui_bono`/`one_line` nutzt.
   `theoryHtml()` im Frontend wird in diesem Zug ebenfalls auf
   `linkify()` umgestellt (vorher nur `escapeHtml()`, siehe app.js-Diff).

Ehrlichkeits-Prinzip wie beim Rest des Projekts: keine geratenen
Wikipedia-URLs, jede URL wurde von einem Recherche-Agenten mit echtem
Web-Zugriff gegen die tatsaechliche Wikipedia-Seite verifiziert.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (story_id, entity_name, type, profile, wikipedia_url_or_None,
#  [(field, exact_substring_to_bracket), ...])
GLOSSARY: list[tuple] = [
    (
        "uss-lincoln-oversight-2026-08",
        "Prinzipal-Agent-Theorie",
        "concept",
        "Beschreibt Situationen, in denen ein Auftraggeber (Prinzipal) eine Aufgabe an einen Ausführenden (Agent) delegiert, dessen laufendes Handeln er wegen eines Informationsvorsprungs nicht vollständig überwachen kann — ein Kernproblem demokratischer Kontrolle von Exekutive und Militär.",
        "https://de.wikipedia.org/wiki/Prinzipal-Agent-Theorie",
        [("theory", "Prinzipal-Agent-Theorie"), ("points", "War Powers Resolution")],
    ),
    (
        "afghan-siv-revocations-2026-08",
        "Versicherheitlichung (Securitization Theory)",
        "concept",
        "Konzept der Kopenhagener Schule der Sicherheitsstudien: Ein Thema wird 'versicherheitlicht', wenn ein politischer Akteur es erfolgreich als existenzielle Bedrohung rahmt und damit Maßnahmen rechtfertigt, die außerhalb normaler rechtsstaatlicher Verfahren liegen würden.",
        "https://de.wikipedia.org/wiki/Versicherheitlichung",
        [("theory", "Versicherheitlichung (Securitization Theory)"), ("points", "Kopenhagener Schule")],
    ),
    (
        "afghan-siv-revocations-2026-08",
        "Kopenhagener Schule",
        "concept",
        "Denkschule der internationalen Sicherheitsstudien (u.a. Barry Buzan, Ole Wæver), die untersucht, wie Themen durch politische Sprechakte zu 'Sicherheitsfragen' erklärt werden und damit außergewöhnliche Maßnahmen jenseits normaler demokratischer Kontrolle legitimieren.",
        "https://en.wikipedia.org/wiki/Copenhagen_School_(international_relations)",
        [],
    ),
    (
        "sudan-national-dialogue-2026-08",
        "Begrenzte Zugangsordnungen (Limited Access Orders)",
        "concept",
        "Konzept von Douglass North, John Wallis und Barry Weingast: Gesellschaften, in denen politische Stabilität nicht über unpersönliche Institutionen, sondern über die gezielte Verteilung von Renten und Privilegien an mächtige, oft bewaffnete Gruppen organisiert wird.",
        None,
        [("theory", "Begrenzte Zugangsordnungen (Limited Access Orders)")],
    ),
    (
        "ukraine-long-range-strikes-2026-08",
        "Eskalationsdominanz",
        "concept",
        "Strategisches Konzept: die Fähigkeit, auf jeder Stufe einer Eskalation die überlegene Handlungsoption zu behalten, sodass der Gegner keinen Vorteil aus einer weiteren Eskalation ziehen kann.",
        "https://de.wikipedia.org/wiki/Eskalationsdominanz",
        [("theory", "Eskalationsdominanz"), ("points", "Eskalationsdominanz")],
    ),
    (
        "cia-ecuador-drone-strikes-2026-08",
        "Prinzipal-Agent-Problem",
        "concept",
        "Beschreibt Situationen, in denen ein Auftraggeber (hier: Kongress/Öffentlichkeit) eine Aufgabe an einen Ausführenden (hier: Exekutive/Geheimdienste) delegiert, dessen Handeln er wegen Geheimhaltung und Informationsvorsprungs kaum wirksam kontrollieren kann.",
        "https://de.wikipedia.org/wiki/Prinzipal-Agent-Theorie",
        [("theory", "Prinzipal-Agent-Problem")],
    ),
    (
        "putin-kuril-islands-visit-2026-08",
        "Irredentismus",
        "concept",
        "Politische Bewegung oder Forderung, Gebiete, die als historisch oder ethnisch zugehörig betrachtet werden, aber unter fremder Souveränität stehen, dem eigenen Staat anzugliedern.",
        "https://de.wikipedia.org/wiki/Irredentismus",
        [("theory", "Irredentismus")],
    ),
    (
        "us-canada-section-338-tariffs-2026-08",
        "Weaponized Interdependence",
        "concept",
        "Von Henry Farrell und Abraham Newman geprägtes Konzept: Staaten mit Kontrolle über zentrale Knotenpunkte globaler Netzwerke (Finanzsysteme, Lieferketten, Handelsbeziehungen) können diese gezielt als Druckmittel gegen wirtschaftlich eng verflochtene Partner einsetzen.",
        "https://en.wikipedia.org/wiki/Weaponized_interdependence",
        [("theory", "Weaponized Interdependence")],
    ),
    (
        "dhs-minnesota-surveillance-2026-08",
        "Versicherheitlichung (Securitization)",
        "concept",
        "Konzept der Kopenhagener Schule der Sicherheitsstudien: Ein Thema wird 'versicherheitlicht', wenn ein politischer Akteur es erfolgreich als existenzielle Bedrohung rahmt und damit Maßnahmen rechtfertigt, die außerhalb normaler demokratischer Kontrolle liegen.",
        "https://de.wikipedia.org/wiki/Versicherheitlichung",
        [("theory", "Versicherheitlichung (Securitization)"), ("points", "Kopenhagener Schule")],
    ),
    (
        "dhs-minnesota-surveillance-2026-08",
        "Kopenhagener Schule",
        "concept",
        "Denkschule der internationalen Sicherheitsstudien (u.a. Barry Buzan, Ole Wæver), die untersucht, wie Themen durch politische Sprechakte zu 'Sicherheitsfragen' erklärt werden und damit außergewöhnliche Maßnahmen jenseits normaler demokratischer Kontrolle legitimieren.",
        "https://en.wikipedia.org/wiki/Copenhagen_School_(international_relations)",
        [],
    ),
    (
        "dhs-minnesota-surveillance-2026-08",
        "Chilling Effect",
        "concept",
        "Beschreibt, wie schon das Wissen um mögliche Überwachung oder Sanktionierung Menschen von der Ausübung eigentlich geschützter Rechte (z.B. Versammlungsfreiheit, freie Meinungsäußerung) abhält — unabhängig davon, ob am Ende tatsächlich eingeschritten wird.",
        "https://de.wikipedia.org/wiki/Chilling_effect",
        [("points", "Chilling Effect")],
    ),
    (
        "eu-21st-russia-sanctions-2026-08",
        "Collective Action Problem",
        "concept",
        "Beschreibt Situationen, in denen alle Beteiligten von gemeinsamem Handeln profitieren würden, jeder Einzelne aber Anreize hat, sich der Kooperation zu entziehen oder Ausnahmen für sich durchzusetzen — ein zentrales Problem internationaler Koordination.",
        "https://en.wikipedia.org/wiki/Collective_action_problem",
        [("theory", "Collective Action Problem")],
    ),
    (
        "gaza-roadmap-netanyahu-standoff-2026-08",
        "Two-Level Game (Putnam)",
        "concept",
        "Von Robert Putnam (1988) entwickeltes Modell internationaler Verhandlungen: Politische Führungen verhandeln gleichzeitig auf internationaler Ebene mit anderen Staaten UND auf innenpolitischer Ebene mit der eigenen Wählerschaft oder Koalition — beide Ebenen begrenzen sich gegenseitig.",
        "https://en.wikipedia.org/wiki/Two-level_game_theory",
        [("theory", "Two-Level Game (Putnam)")],
    ),
    (
        "gaza-roadmap-netanyahu-standoff-2026-08",
        "Win-Set",
        "concept",
        "Fachbegriff innerhalb der Two-Level-Game-Theorie: die Menge aller auf internationaler Ebene ausgehandelten Vereinbarungen, die auf der innenpolitischen Ebene tatsächlich ratifiziert bzw. akzeptiert würden. Ein enges Win-Set schränkt den Verhandlungsspielraum stark ein.",
        None,
        [("points", "Win-Set")],
    ),
]


def bracket_once(text: str, needle: str) -> str:
    """Ersetzt die ERSTE Fundstelle von `needle` in `text` durch
    `[[needle]]`. Wirft, wenn `needle` nicht gefunden wird oder bereits
    geklammert ist -- damit ein Tippfehler nicht still verpufft."""
    bracketed = f"[[{needle}]]"
    if bracketed in text:
        return text  # bereits gesetzt (z.B. zweiter Lauf des Skripts)
    idx = text.find(needle)
    if idx == -1:
        raise SystemExit(f"Substring nicht gefunden: {needle!r} in {text!r}")
    return text[:idx] + bracketed + text[idx + len(needle):]


def run() -> None:
    path = ROOT / "data" / "stories.json"
    stories = json.loads(path.read_text())
    by_id = {s["id"]: s for s in stories}

    n_entities = 0
    n_brackets = 0
    for story_id, name, etype, profile, wiki, targets in GLOSSARY:
        story = by_id[story_id]
        existing = next((e for e in story["entities"] if e["name"] == name), None)
        if existing is None:
            entity = {
                "name": name, "type": etype,
                "role_in_story": "Zentraler Fachbegriff der politikwissenschaftlichen Einordnung dieser Story.",
                "profile": profile,
            }
            if wiki:
                entity["wikipedia_url"] = wiki
            story["entities"].append(entity)
            n_entities += 1

        theory = story["political_theory"]
        for field, needle in targets:
            if field == "theory":
                theory["theory"] = bracket_once(theory["theory"], needle)
                n_brackets += 1
            elif field == "points":
                # In den ERSTEN passenden Punkt einsetzen, der die
                # Zeichenkette unmarkiert enthaelt.
                for i, p in enumerate(theory["points"]):
                    if needle in p and f"[[{needle}]]" not in p:
                        theory["points"][i] = bracket_once(p, needle)
                        n_brackets += 1
                        break
                else:
                    if not any(f"[[{needle}]]" in p for p in theory["points"]):
                        raise SystemExit(f"Substring nicht in points gefunden: {needle!r} ({story_id})")

    path.write_text(json.dumps(stories, ensure_ascii=False, indent=2))
    print(f"{n_entities} neue Glossar-Entitaeten, {n_brackets} [[...]]-Markierungen gesetzt -> {path}")


if __name__ == "__main__":
    run()
