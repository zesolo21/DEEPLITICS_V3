"""
Einmaliger Anreicherungsschritt (19.08.2026): macht die Bullet-Zusammenfassungen
im Uebersicht-Tab etwas ausfuehrlicher und "schoener" zu lesen, wie vom
Nutzer gewuenscht ("ein kleines bisschen laengere Texte... nicht so ganz,
ganz kurz").

Wichtig fuer die Ehrlichkeits-Rigor des Projekts: KEINE neuen, aussenstehenden
Fakten werden erfunden. Jede Ergaenzung stammt direkt aus bereits in derselben
Story vorhandenen Feldern (deep_dive, cui_bono, quotes) -- die Bullets werden
also nur um bereits recherchierten/verifizierten Kontext derselben Story
verlaengert, nicht um neues Wissen.

Nur Stories, deren Bullets im Vergleich noch auffaellig kurz waren, wurden
ueberarbeitet (uss-lincoln, afghan-siv, sudan, ukraine-strikes, cia-ecuador,
eu-sanctions, gaza-roadmap). Stories, deren Bullets bereits ausfuehrlich
waren (putin-kuril, us-canada-tariffs, dhs-minnesota), bleiben unveraendert,
um sie nicht unnoetig aufzublaehen.

Vorgehen: einfacher Full-Replace der `summary`-Liste pro Story-ID, wie beim
Glossar-Skript nur fuer `summary` statt `political_theory`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NEW_SUMMARIES: dict[str, list[str]] = {
    "uss-lincoln-oversight-2026-08": [
        "Die [[USS Abraham Lincoln]] ist seit über 250 Tagen im Nahost-Einsatz und seit mehr als 200 Tagen ohne Hafenaufenthalt auf See, ein Rekordwert für einen US-Flugzeugträger, der auf wiederholte Verschiebungen des eigentlich für Mai geplanten Ablöseturnus im Zuge der Spannungen mit [[Iran]] zurückgeht.",
        "Berichte aus der Besatzung nennen Versorgungsengpässe, defekte sanitäre Anlagen, Schimmelbefall und psychische Belastung — Zustände, auf die inzwischen drei Senatoren unabhängig voneinander öffentlich reagiert haben.",
        "[[Richard Blumenthal]] verlangt in einem offiziellen Schreiben Antworten zu Einsatzverlängerung, Wohnbedingungen und Besatzungsmoral, mit Frist zum 27. August.",
        "[[Ruben Gallego]] fordert unabhängig davon einen offiziellen Aufsichtsbesuch einer überparteilichen Kongressdelegation an Bord und wirft der Marineführung vor, ohne erkennbaren Plan zu improvisieren.",
        "[[Mark Kelly]], selbst ehemaliger Marineoffizier, äußert sich öffentlich besorgt über die Lage der Besatzung, was der Kritik zusätzliches fachliches Gewicht verleiht.",
        "[[Pete Hegseth]] und das Verteidigungsministerium weisen die Darstellung der Zustände als übertrieben zurück und betonen, jedes Schiff und jede Besatzung erhalte alles Notwendige.",
    ],
    "afghan-siv-revocations-2026-08": [
        "Hunderte Afghanen mit bereits erteilten, über das [[Special Immigrant Visa (SIV) Programm]] erhaltenen Green Cards erhalten Schreiben, die ihren Aufenthaltsstatus rückwirkend infrage stellen — obwohl das 2009 als Dank für afghanische Ortskräfte geschaffene Programm seit Ende 2025 für neue Anträge bereits geschlossen ist.",
        "Grundlage ist eine Anordnung der [[Trump-Regierung]] zur umfassenden Neuüberprüfung von Green-Card-Inhabern aus als sicherheitsrelevant eingestuften Ländern, die denselben Personenkreis nun als potenzielles Risiko statt als Kriegsverbündete behandelt.",
        "Ein Bundesgericht erklärte im Juni 2026 Teile dieser pauschalen Überprüfungspolitik bereits für rechtswidrig, was die praktische Wirkung der aktuellen Widerrufswelle zusätzlich unklar macht.",
        "Rechtsorganisationen wie die [[International Refugee Assistance Project (IRAP)]] und [[AfghanEvac]] bezeichnen den nachträglichen Widerruf bereits erteilter Visa als verfahrensrechtlich neuartig — einen Widerruf Jahre nach der eigentlichen Visaerteilung habe es zuvor in diesem Umfang nicht gegeben.",
        "Betroffene berichten von Unsicherheit im Alltag zwischen Arbeit, Familie und der Suche nach rechtlichem Beistand, ohne selbst Einfluss auf die politische Linie zu haben, der sie unterliegen.",
    ],
    "sudan-national-dialogue-2026-08": [
        "[[Abdel Fattah al-Burhan]] kündigt einen landesweiten, inklusiven Dialog mit politischen und zivilen Parteien an, mit rechtlichen, politischen, sicherheitsbezogenen und logistischen Garantien durch den Staat.",
        "Teilnehmenden mit laufenden Strafverfahren soll für die Dauer des Dialogs eine befristete Aussetzung dieser Verfahren gewährt werden — ausdrücklich kein Straferlass, sondern eine zeitlich begrenzte Geste.",
        "Ein Frieden, der die [[Rapid Support Forces (RSF)]] unter [[Mohamed Hamdan Dagalo]] zurück an die Macht bringen würde, wird ausdrücklich ausgeschlossen — eine klare Linie angesichts des seit April 2023 andauernden Machtkampfs zwischen beiden Lagern.",
        "Die [[Sudanesische Armee (SAF)]] kündigt gleichzeitig an, den militärischen Kampf gegen die RSF fortzusetzen, während zivile Gruppen wie das Bündnis Somoud bereits vor der Ankündigung Vorbehalte gegen einen von der Militärführung initiierten Dialog äußerten.",
        "Die Ankündigung fällt zeitlich mit einem Besuch einer Delegation der Afrikanischen Union und Sudans Bitte um Aufhebung seiner seit dem Putsch von 2021 bestehenden Suspendierung zusammen.",
    ],
    "ukraine-long-range-strikes-2026-08": [
        "Ukrainische, im eigenen Land entwickelte [[Flamingo-Marschflugkörper]] treffen das [[Progress-Raumfahrtzentrum]] in der russischen Region Samara sowie den Luftwaffenstützpunkt Sawasleika, von dem aus Kinschal-Trägerjets starten — ein weiterer Beleg für die wachsende eigenständige Reichweite ukrainischer Waffensysteme.",
        "Russland reagiert in derselben Nacht mit einem Großangriff von 152 Drohnen auf ukrainische Städte, einem der massivsten Drohnenangriffe der letzten Zeit.",
        "Parallel dazu protestiert Russland gegen eine über die [[Türkei]] laufende Lieferung von ATACMS-Raketen, M270-Systemen und Munition aus den [[USA]] an die [[Ukraine]] und zeigt damit, wie Drittstaaten inzwischen als Zwischenstationen für westliche Rüstungslieferungen dienen.",
        "Russland droht mit Schäden an den bilateralen Beziehungen zu Washington und Ankara.",
        "Die Angriffe und der Waffenlieferungsstreit fallen zeitlich zusammen, sind aber unabhängige Entwicklungen entlang zweier getrennter Eskalationslinien — der militärischen und der diplomatischen.",
    ],
    "cia-ecuador-drone-strikes-2026-08": [
        "Zwischen Januar und März 2026 griffen bewaffnete Kräfte mindestens drei ecuadorianische Fischerboote rund 170 Meilen vor den Galápagos-Inseln, innerhalb der ecuadorianischen Wirtschaftszone, mit kleinen, kissengroßen Drohnen an, die Sprengsätze auf die zivilen Boote abwarfen.",
        "Überlebende berichten, nach den Angriffen von bewaffneten Männern in Tarnkleidung mit US-Flaggen-Patches gefesselt, mit Kapuzen versehen und an Bord eines Schiffes gefoltert worden zu sein, bevor man sie zu einem Flughafen in El Salvador brachte.",
        "Die Angriffe verlaufen Berichten zufolge über ein separates, verdecktes CIA-Programm, parallel zur offiziell erklärten Militäroperation Southern Spear der Trump-Regierung gegen mutmaßliche Drogenschmuggler, die sich auf eine geheime Präsidialanordnung und ein klassifiziertes Rechtsgutachten stützt.",
        "Die ecuadorianische Staatsanwältin [[Alexandra Bravo]], die die Vorfälle untersuchte und Aussagen von 36 Überlebenden zu mutmaßlicher Folter gesammelt hatte, wurde im Juni 2026 erschossen, nachdem man sie zuvor von den Ermittlungen abgezogen hatte.",
        "Die US-Regierung hat bislang keine Beweise für eine Verbindung der betroffenen Boote zu Drogenhandel vorgelegt, während Verteidigungsminister [[Pete Hegseth]] die Vorwürfe zurückweist.",
        "Im Rahmen der gesamten Bootsangriffs-Kampagne seit September 2025 wurden über 200 Menschen getötet, was im US-Senat Kritik an der fehlenden Rechtsgrundlage auslöst — [[Tim Kaine]] bezeichnete die Toten als Mordopfer und forderte ein Ende der Operation.",
    ],
    "eu-21st-russia-sanctions-2026-08": [
        "Die [[Europäische Union]] plant nach Aussage von Außenbeauftragter [[Kaja Kallas]] die Sanktionierung von etwa 1.600 russischen Personen und Entitäten mit Fokus auf den militärisch-industriellen Komplex — die bislang größte Einzelerweiterung der Sanktionsliste.",
        "Die neuen Designierungen würden die Gesamtzahl sanktionierter russischer Einheiten um etwa ein Drittel erhöhen und umfassen Reiseverbote, Transaktionsbeschränkungen und Vermögenssperren; die Konzentration auf Einzelpersonen statt breiter Sektormaßnahmen soll die Verabschiedung beschleunigen.",
        "Der [[Europäischer Auswärtiger Dienst]] soll die Liste Anfang September vorlegen, mit angestrebter Verabschiedung im Oktober 2026 — vorausgesetzt, alle 27 Mitgliedstaaten stimmen wie bei jedem Sanktionspaket einstimmig zu.",
        "Im Juli 2026 hatte die [[Europäische Union]] bereits ihr 21. Sanktionspaket verabschiedet, das die Preisobergrenze für russisches Rohöl bei 44 Dollar pro Barrel einfriert; die EU beziffert die wirtschaftlichen Gesamtkosten der bisherigen Sanktionen für Russland auf über eine Billion Euro.",
        "Die Verhandlungen zum 21. Paket zeigten die wachsenden Schwierigkeiten einstimmiger Beschlüsse: [[Griechenland]] erhielt Ausnahmen für LNG-Transporte, [[Bulgarien]] blockierte Sanktionen gegen [[Patriarch Kirill]], [[Portugal]] und [[Frankreich]] verhinderten Fischimport-Verbote.",
    ],
    "gaza-roadmap-netanyahu-standoff-2026-08": [
        "Sieben mehrheitlich muslimische Staaten — [[Ägypten]], [[Jordanien]], die [[Vereinigten Arabischen Emiraten]], [[Katar]], die [[Türkei]], [[Pakistan]] und [[Indonesien]] — verurteilen [[Israel]]s Ablehnung von [[Donald Trump]]s Gaza-Friedensplan gemeinsam und machen [[Benjamin Netanyahu]] für das Scheitern der Friedensbemühungen verantwortlich.",
        "[[Benjamin Netanyahu]] besteht öffentlich auf vollständiger Entwaffnung der [[Hamas]] vor jedem Rückzug und widerspricht damit dem gestaffelten Ansatz des Plans — eine harte Linie, die er vor allem gegenüber seinen rechtsextremen Koalitionspartnern vor den Parlamentswahlen im Oktober braucht.",
        "Hinter den Kulissen bereitet die [[IDF]] weiterhin die zweite Phase vor: Wiederaufbauarbeiten in Rafah laufen mit geheimer Zustimmung von [[Benjamin Netanyahu]] und Verteidigungsminister [[Israel Katz]], während die öffentliche Rhetorik unverändert hart bleibt.",
        "Die Zahl palästinensischer Todesopfer fiel von 47 auf 8 pro Woche, die [[IDF]] baut Infrastruktur wieder auf und plant eine Basis für eine internationale Stabilisierungstruppe bis Ende August — eine faktische Deeskalation, die mit Netanyahus öffentlicher Haltung kaum zusammenpasst.",
        "[[Jared Kushner]] trifft [[Hamas]]-Führer [[Khalil al-Hayya]] am 16. August in [[Ägypten]] und drängt auf den Beginn der Entwaffnung sowie ein Ende bewaffneter Auftritte in Gaza — eine direkte US-Verhandlung mit der Hamas-Führung, wie sie frühere US-Regierungen so nicht geführt hätten.",
    ],
}


# Bonus-Fund waehrend dieser Anreicherung: ein paar bereits VORHANDENE
# [[...]]-Markierungen in deep_dive/cui_bono matchen keine Entitaet in
# `entities[]` und werden von linkify() deshalb nie zu Links -- entweder
# weil die alte "[[Name|Anzeigetext]]"-Pipe-Syntax verwendet wurde (von
# linkify() nicht unterstuetzt) oder weil eine Kurzform ("Netanyahu" statt
# "Benjamin Netanyahu") nicht exakt dem Entitaetsnamen entspricht. Da das
# dieselbe Anklickbarkeits-Funktion betrifft, die der Nutzer in dieser
# Runde ausdruecklich hervorgehoben hat, werden diese toten Links hier
# gleich mit repariert -- reine Syntaxkorrektur, kein neuer Text.
LINK_FIXES: list[tuple[str, str, str, str]] = [
    # (story_id, field, alt_text, neu_text)
    (
        "eu-21st-russia-sanctions-2026-08", "deep_dive",
        "[[Patriarch Kirill|Moskauer Patriarchen Kirill]]", "[[Patriarch Kirill]]",
    ),
    (
        "eu-21st-russia-sanctions-2026-08", "cui_bono",
        "[[Europäische Union|EU-Institutionen]]", "[[Europäische Union]]",
    ),
    (
        "eu-21st-russia-sanctions-2026-08", "cui_bono",
        "[[Europäischer Auswärtiger Dienst|EEAS]]", "[[Europäischer Auswärtiger Dienst]]",
    ),
    (
        "gaza-roadmap-netanyahu-standoff-2026-08", "deep_dive",
        "[[Netanyahu]] steht vor Parlamentswahlen", "[[Benjamin Netanyahu]] steht vor Parlamentswahlen",
    ),
    (
        "gaza-roadmap-netanyahu-standoff-2026-08", "deep_dive",
        "den [[Netanyahu]] später als eigenen Erfolg", "den [[Benjamin Netanyahu]] später als eigenen Erfolg",
    ),
    (
        "gaza-roadmap-netanyahu-standoff-2026-08", "deep_dive",
        "die mit [[Netanyahu]]s harter Rhetorik", "die mit [[Benjamin Netanyahu]]s harter Rhetorik",
    ),
    (
        "gaza-roadmap-netanyahu-standoff-2026-08", "deep_dive",
        "Dies würde [[Netanyahu]] erlauben", "Dies würde [[Benjamin Netanyahu]] erlauben",
    ),
]


def run() -> None:
    path = ROOT / "data" / "stories.json"
    stories = json.loads(path.read_text())
    by_id = {s["id"]: s for s in stories}

    n_changed = 0
    for story_id, new_summary in NEW_SUMMARIES.items():
        story = by_id.get(story_id)
        if story is None:
            raise SystemExit(f"Story nicht gefunden: {story_id}")
        story["summary"] = new_summary
        n_changed += 1

    n_fixed = 0
    for story_id, field, old, new in LINK_FIXES:
        story = by_id.get(story_id)
        if story is None:
            raise SystemExit(f"Story nicht gefunden: {story_id}")
        text = story.get(field, "")
        if old not in text:
            raise SystemExit(f"Link-Fix-Substring nicht gefunden: {old!r} in {story_id}.{field}")
        story[field] = text.replace(old, new, 1)
        n_fixed += 1

    # Konsistenzcheck: JEDE [[...]]-Markierung in summary/deep_dive/cui_bono
    # muss jetzt exakt einen Entitaetsnamen treffen.
    for story in stories:
        ents = {e["name"] for e in story["entities"]}
        for field in ("deep_dive", "cui_bono"):
            for name in re.findall(r"\[\[(.+?)\]\]", story.get(field, "") or ""):
                if name not in ents:
                    raise SystemExit(f"Weiterhin toter Link: {story['id']}.{field} -> {name!r}")
        for b in story.get("summary", []):
            for name in re.findall(r"\[\[(.+?)\]\]", b):
                if name not in ents:
                    raise SystemExit(f"Weiterhin toter Link: {story['id']}.summary -> {name!r}")

    path.write_text(json.dumps(stories, ensure_ascii=False, indent=2))
    print(f"{n_changed} Stories mit ausfuehrlicheren Bullet-Zusammenfassungen aktualisiert, "
          f"{n_fixed} tote [[...]]-Links repariert -> {path}")


if __name__ == "__main__":
    run()
