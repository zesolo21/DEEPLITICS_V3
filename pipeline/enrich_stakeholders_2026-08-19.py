"""
Einmaliger Anreicherungsschritt (19.08.2026): fuegt jeder Story ein
`stakeholders`-Feld hinzu: { pro: [{entity, reason}], con: [{entity, reason}],
note?: str }.

Hintergrund: der Nutzer wollte den bisherigen neutralen "Akteure"-Tab durch
einen "Stakeholders"-Tab ersetzen, der explizit zeigt, wer von einer Story
PROFITIERT und wer NICHT (oder darunter leidet) -- nicht nur ein einseitiger
"Gewinner"-Blick.

Es gibt keine Laufzeit-API in dieser Version, also wird hier NICHT neu vom
Modell synthetisiert. Stattdessen wird das bereits vorhandene `cui_bono`-Feld
jeder Story (das schon eine Wer-profitiert-Analyse in Fliesstext enthaelt)
von mir als Autor gelesen und in eine strukturierte Pro/Con-Liste umgesetzt,
die ausschliesslich bereits im `cui_bono`/`deep_dive`-Text vorhandene Aussagen
paraphrasiert -- keine neuen Fakten. Das ist bewusst als redaktioneller
Restrukturierungsschritt gehalten, nicht als neue Recherche.

Wo eine Story echte Ambivalenz enthaelt (z.B. ein Akteur gewinnt kurzfristig,
riskiert aber langfristig etwas), wird das in `reason` als ein Satz
ausformuliert, statt eine erzwungene Pro-ODER-Con-Entscheidung zu treffen.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STAKEHOLDERS = {
    "uss-lincoln-oversight-2026-08": {
        "pro": [
            {"entity": "Ruben Gallego", "reason": "Positioniert sich unabhängig vom Ausgang einer Untersuchung als schärfster Verfechter der Fürsorgepflicht gegenüber der Truppe."},
            {"entity": "Richard Blumenthal", "reason": "Gewinnt politisches Profil durch das offizielle Aufklärungs-Schreiben ans Verteidigungsministerium."},
            {"entity": "Mark Kelly", "reason": "Positioniert sich als besorgter Fürsprecher der Besatzung, unabhängig vom weiteren Verlauf."},
        ],
        "con": [
            {"entity": "USS Abraham Lincoln", "reason": "Die Besatzung selbst trägt die eigentliche Last: über 250 Tage Einsatz, über 200 Tage ohne Hafenaufenthalt, im Zentrum der Vorwürfe."},
            {"entity": "Pete Hegseth", "reason": "Riskiert Glaubwürdigkeit, falls sich die zurückgewiesenen Berichte über die Zustände an Bord später als zutreffend erweisen."},
        ],
        "note": "Kein klarer Konflikt zwischen zwei Lagern, eher mehrere Akteure, die dieselbe Krise für unterschiedliche eigene Positionierungen nutzen.",
    },
    "afghan-siv-revocations-2026-08": {
        "pro": [
            {"entity": "Trump-Regierung", "reason": "Die Überprüfung dient als sichtbares Zeichen konsequenter Sicherheitspolitik, unabhängig vom tatsächlichen Anteil begründeter Fälle."},
            {"entity": "International Refugee Assistance Project (IRAP)", "reason": "Gewinnt durch die Fürsprecherrolle für Betroffene an Sichtbarkeit und politischem Gewicht."},
            {"entity": "AfghanEvac", "reason": "Gewinnt ebenfalls an Sichtbarkeit und politischem Gewicht durch die öffentliche Fürsprecherrolle."},
        ],
        "con": [
            {"entity": "USA", "reason": "Die unmittelbar betroffenen ehemaligen afghanischen Kriegsverbündeten (vertreten durch das SIV-Programm, über das sie einreisten) tragen die Kosten der Unsicherheit, ohne selbst Einfluss auf die politische Linie zu haben."},
        ],
    },
    "sudan-national-dialogue-2026-08": {
        "pro": [
            {"entity": "Abdel Fattah al-Burhan", "reason": "Kann sich international als Befürworter einer politischen Lösung positionieren, während die Armee militärisch weiterkämpft."},
        ],
        "con": [
            {"entity": "Demokratische Blockpartei", "reason": "Teilnahme am Dialog bietet Einfluss, birgt aber das Risiko, eine militärisch dominierte Prozessführung zu legitimieren."},
        ],
        "note": "Zivile Kräfte, die sich aus Sorge vor genau dieser Legitimierung vom Dialog fernhalten, laufen umgekehrt Gefahr, von der Gestaltung eines möglichen Übergangs ausgeschlossen zu bleiben – im Datensatz aber keine eigene benannte Entität.",
    },
    "ukraine-long-range-strikes-2026-08": {
        "pro": [
            {"entity": "Ukraine", "reason": "Demonstriert wachsende eigenständige militärische Fähigkeit, unabhängig von der aktuellen Lieferbereitschaft westlicher Partner."},
            {"entity": "Türkei", "reason": "Kann sich als unverzichtbarer Vermittler und Partner beider Seiten positionieren, trotz diplomatischer Kosten mit Russland."},
            {"entity": "Maria Sacharowa", "reason": "Der diplomatische Protest gegen Türkei und USA dient Russland dazu, den politischen Preis weiterer westlicher Unterstützung sichtbar zu erhöhen."},
        ],
        "con": [],
        "note": "Kein klar benannter Verlierer in dieser Story – die Eskalationskosten tragen vor allem nicht einzeln benannte Zivilbevölkerungen auf beiden Seiten.",
    },
    "cia-ecuador-drone-strikes-2026-08": {
        "pro": [
            {"entity": "Donald Trump", "reason": "Die Exekutive kann eine harte Anti-Kartell-Politik demonstrieren, ohne eine Kriegsermächtigung durch den Kongress einholen zu müssen."},
            {"entity": "CIA", "reason": "Geheimdienstbehörden erweitern ihren operativen Spielraum und ihre Budgets."},
            {"entity": "Daniel Noboa", "reason": "Profitiert kurzfristig von US-Sicherheitsunterstützung gegen Bandengewalt – riskiert dafür aber eigene Souveränität und Glaubwürdigkeit."},
        ],
        "con": [
            {"entity": "Alexandra Bravo", "reason": "Die ermittelnde Staatsanwältin wurde ermordet, nachdem sie Folter-Aussagen von 36 Überlebenden gesammelt hatte – der klarste Verlust in dieser Story."},
            {"entity": "Tim Kaine", "reason": "Steht stellvertretend für die parlamentarische Kontrolle in Washington, die bei einer auf klassifizierten Rechtsgutachten statt öffentlichen Gesetzen gestützten Operation umgangen wird."},
        ],
    },
    "putin-kuril-islands-visit-2026-08": {
        "pro": [
            {"entity": "Wladimir Putin", "reason": "Kostengünstige Gelegenheit, innenpolitisch Stärke und Kontrolle über umkämpftes Territorium zu demonstrieren."},
            {"entity": "Sanae Takaichi", "reason": "Kann die Empörung nutzen, um den ohnehin laufenden Kurs der Aufrüstung und engeren US-Anbindung politisch weiter zu legitimieren."},
        ],
        "con": [],
        "note": "Der Vorstoß kann für Putin auch nach hinten losgehen, falls der Westen sichtbare Konsequenzen zieht – das Ergebnis ist zum jetzigen Zeitpunkt offen.",
    },
    "us-canada-section-338-tariffs-2026-08": {
        "pro": [
            {"entity": "Donald Trump", "reason": "Zusätzliches Druckmittel in den USMCA/CUSMA-Verhandlungen, unabhängig von der vom Supreme Court blockierten IEEPA-Notstandsvollmacht, innenpolitisch als konsequente Zollagenda präsentierbar."},
            {"entity": "Mark Carney", "reason": "Kann sich innenpolitisch als Verteidiger kanadischer Interessen profilieren."},
            {"entity": "Doug Ford", "reason": "Kann sich ebenfalls innenpolitisch als Verteidiger kanadischer Interessen profilieren."},
        ],
        "con": [
            {"entity": "Kanada", "reason": "Zielland der neuen 50-Prozent-Zölle auf Autos, Milchprodukte und Alkohol – die wirtschaftlichen Kosten tragen am Ende Konsumenten auf beiden Seiten der Grenze."},
        ],
    },
    "dhs-minnesota-surveillance-2026-08": {
        "pro": [
            {"entity": "U.S. Department of Homeland Security (DHS)", "reason": "Der Fall erschwert Organisationswiderstand gegen die Einwanderungspolitik und stärkt langfristig die institutionelle Reichweite von DHS und HSI."},
            {"entity": "ACLU of Minnesota", "reason": "Kann die Vorfälle politisch als Beleg für eine autoritäre Schlagseite der Regierung nutzen, um Spenden, Mobilisierung und rechtliche Gegenwehr zu organisieren."},
        ],
        "con": [
            {"entity": "Minnesota AFL-CIO", "reason": "Finanzunterlagen wurden laut Gerichtsdokumenten von HSI angefordert – direkt von der Überwachung betroffen."},
            {"entity": "Twin Cities Democratic Socialists of America", "reason": "Eine von 18 in einer internen HSI-Übersicht erfassten linken Gruppen – direkt von der Überwachung betroffen."},
        ],
    },
    "eu-21st-russia-sanctions-2026-08": {
        "pro": [
            {"entity": "Kaja Kallas", "reason": "Die schrittweise Sanktionsstrategie stärkt die Position der EU-Institutionen als eigenständige außenpolitische Akteure."},
            {"entity": "Griechenland", "reason": "Erhielt eine Ausnahme, die eigenen Schifffahrtsunternehmen den Weitertransport von russischem Flüssiggas erlaubt."},
            {"entity": "Bulgarien", "reason": "Nutzt seine Vetomacht, um eine Sanktionierung von Patriarch Kirill zu verhindern."},
            {"entity": "Frankreich", "reason": "Verhindert gemeinsam mit Portugal ein Importverbot für russischen Kabeljau und Alaska-Seelachs."},
            {"entity": "Portugal", "reason": "Verhindert gemeinsam mit Frankreich dasselbe Importverbot."},
            {"entity": "Patriarch Kirill", "reason": "Entgeht dank des bulgarischen Vetos vorerst der EU-Sanktionsliste."},
        ],
        "con": [],
    },
    "gaza-roadmap-netanyahu-standoff-2026-08": {
        "pro": [
            {"entity": "Benjamin Netanyahu", "reason": "Gewinnt Zeit und Flexibilität: Härte gegenüber der rechten Basis, während die Option offenbleibt, später als Friedensbringer aufzutreten."},
            {"entity": "Donald Trump", "reason": "Profitiert von einem möglichen außenpolitischen Durchbruch vor den US-Wahlen 2028."},
            {"entity": "Hamas", "reason": "Legitimiert sich durch Akzeptanz des Plans als verhandlungsfähiger Akteur und schiebt die Verantwortung für eine Fortsetzung des Konflikts auf Israel."},
            {"entity": "Ägypten", "reason": "Stärkt seinen Einfluss als unverzichtbare diplomatische Vermittlungsplattform."},
            {"entity": "Katar", "reason": "Stärkt ebenfalls seinen Einfluss als unverzichtbare diplomatische Vermittlungsplattform."},
        ],
        "con": [
            {"entity": "Israel", "reason": "Steht im Zentrum der Kritik von sieben muslimischen Staaten wegen der öffentlichen Ablehnung des Plans – trotz stiller Deeskalation und Vorbereitung auf dessen Umsetzung."},
        ],
    },
}


def run() -> None:
    path = ROOT / "data" / "stories.json"
    stories = json.loads(path.read_text())
    by_id = {s["id"]: s for s in stories}
    missing = [sid for sid in STAKEHOLDERS if sid not in by_id]
    if missing:
        raise SystemExit(f"Unbekannte Story-IDs in STAKEHOLDERS: {missing}")
    not_covered = [s["id"] for s in stories if s["id"] not in STAKEHOLDERS]
    if not_covered:
        raise SystemExit(f"Stories ohne Stakeholder-Eintrag: {not_covered}")

    n = 0
    for sid, sh in STAKEHOLDERS.items():
        by_id[sid]["stakeholders"] = sh
        n += 1

    path.write_text(json.dumps(stories, ensure_ascii=False, indent=2))
    print(f"Stakeholders (Pro/Con) fuer {n}/{len(stories)} Storys ergaenzt -> {path}")


if __name__ == "__main__":
    run()
