"""
BEISPIELDATEN, Version 5, Datenstand 16.08.2026.

Vier Storys (unverändert gegenüber v4 in der Auswahl), aber inhaltlich und
strukturell nach v5 überarbeitet, auf ausdrücklichen Nutzerwunsch:

1. `summary` ist jetzt eine Bullet-Liste statt eines Fließtext-Absatzes.
2. SYNTHETISCHER STIL: summary/deep_dive/cui_bono verschmelzen die
   Quellen zu einem Verständnis, statt als "Person X sagte laut Quelle Y"
   geschrieben zu sein. Konkrete Attributionen/Zitate stehen ausschließlich
   in `quotes`.
3. `primary_sources`: echte Regierungsdokumente/offizielle Statements,
   recherchiert am 16.08.2026 (Senatsbriefe, Federal-Register-Einträge,
   Gerichtsentscheidungen, Kongressprotokoll), zusätzlich zu den
   journalistischen `article_urls`. Wo nichts belastbar auffindbar war
   (Story 4), bleibt die Liste ehrlich leer statt einer erfundenen URL.
4. `political_theory`: ordnet jede Story in EIN politikwissenschaftliches
   Konzept ein, im Frontend hinter einem Button versteckt.
5. `market_correlation`: ehrlich recherchiert, nicht erzwungen. Nur Story 1
   hat eine echte, mehrfach belegte Korrelation (Ölpreis + Rüstungsaktien
   nach der Iran-Eskalation vom 28.02.2026, siehe die Reihe dort für
   Quellen und den Näherungshinweis). Storys 2 bis 4 haben
   `has_correlation=False` mit einer kurzen, recherchierten Begründung,
   das ist ein vollwertiges Ergebnis, keine Lücke.

GRUNDFAKTEN, Zitate, Primärquellen und Marktdaten stammen aus echter,
web-gestützter Recherche am 16.08.2026. Die HISTORISCHEN LINIEN
(historical_threads) nutzen etabliertes, allgemein bekanntes historisches
Wissen. Bild-URLs sind, wo nicht per og:image direkt live bestätigt, aus
Wikipedia/Wikimedia-Commons-Recherche abgeleitet und unterschiedlich
sicher. Alle Bilder haben im Frontend einen automatischen Fallback auf
einen Platzhalter, falls eine URL nicht lädt.
"""

import json
from pathlib import Path

FLAG_USA = "https://upload.wikimedia.org/wikipedia/commons/a/a4/Flag_of_the_United_States.svg"
FLAG_IRAN = "https://upload.wikimedia.org/wikipedia/commons/c/ca/Flag_of_Iran.svg"
FLAG_SUDAN = "https://upload.wikimedia.org/wikipedia/commons/0/01/Flag_of_Sudan.svg"
FLAG_UKRAINE = "https://upload.wikimedia.org/wikipedia/commons/4/49/Flag_of_Ukraine.svg"
FLAG_RUSSIA = "https://upload.wikimedia.org/wikipedia/commons/f/f3/Flag_of_Russia.svg"
FLAG_TURKEY = "https://upload.wikimedia.org/wikipedia/commons/b/b4/Flag_of_Turkey.svg"

STORIES = [
    # -----------------------------------------------------------------
    # STORY 1, USS Abraham Lincoln: Zustände an Bord, Kongressaufsicht
    # -----------------------------------------------------------------
    {
        "id": "uss-lincoln-oversight-2026-08",
        "title": "Nach Berichten über Zustände an Bord: Senatoren fordern Aufsicht über die USS Abraham Lincoln",
        "one_line": (
            "Nachdem Berichte über Versorgungsengpässe und psychische Belastung "
            "an Bord der [[USS Abraham Lincoln]] öffentlich wurden, verlangen "
            "mehrere Senatoren unabhängig voneinander Aufklärung, das Pentagon "
            "weist die Darstellung zurück."
        ),
        "summary": [
            "Die [[USS Abraham Lincoln]] ist seit über 250 Tagen im Nahost-Einsatz und seit mehr als 200 Tagen ohne Hafenaufenthalt auf See, ein Rekordwert für einen US-Flugzeugträger.",
            "Berichte aus der Besatzung nennen Versorgungsengpässe, defekte sanitäre Anlagen, Schimmelbefall und psychische Belastung.",
            "[[Richard Blumenthal]] verlangt in einem offiziellen Schreiben Antworten zu Einsatzverlängerung, Wohnbedingungen und Besatzungsmoral, mit Frist zum 27. August.",
            "[[Ruben Gallego]] fordert unabhängig davon einen offiziellen Aufsichtsbesuch einer überparteilichen Kongressdelegation an Bord.",
            "[[Mark Kelly]] äußert sich öffentlich besorgt über die Lage der Besatzung.",
            "Das Verteidigungsministerium weist die Darstellung der Zustände als übertrieben zurück.",
        ],
        "deep_dive": (
            "Diese Story ist auf den ersten Blick ein Streit um Fürsorgepflicht "
            "an Bord eines einzelnen Schiffs. Auf der tieferen Ebene zeigt sie "
            "ein wiederkehrendes Muster in der Beziehung zwischen dem "
            "[[Kongress]] und der Exekutive bei Militäreinsätzen: Seit der "
            "[[War Powers Resolution]] von 1973 versucht der Kongress immer "
            "wieder, über Anhörungen, Briefe und Delegationsbesuche Einfluss "
            "auf Entscheidungen zu behalten, die formal beim Präsidenten und "
            "dem Verteidigungsministerium liegen. Eine bindende Abstimmung "
            "über den Einsatz selbst findet dabei so gut wie nie statt, "
            "stattdessen setzen einzelne Abgeordnete auf öffentlichen Druck, "
            "in diesem Fall gleich mit drei unterschiedlichen Werkzeugen "
            "desselben Instrumentariums: einem formellen Aufsichtsbrief, "
            "einer Forderung nach einem Delegationsbesuch und einer "
            "öffentlichen Stellungnahme, jeweils unabhängig voneinander.\n\n"
            "Der eigentliche Auslöser der Krise an Bord liegt in der "
            "Eskalation des [[US-Israel-Iran-Konflikt]]s vom Februar 2026: Der "
            "ursprünglich für Mai geplante Ablöseturnus der "
            "[[USS Abraham Lincoln]] wurde wiederholt verschoben, weil die "
            "Trägerkampfgruppe im Rahmen der Spannungen mit [[Iran]] gebunden "
            "blieb. Das erklärt sowohl die außergewöhnliche Einsatzdauer als "
            "auch, warum nun die [[USS George Washington]] aus dem Pazifik "
            "abgezogen werden muss, um die Lücke zu schließen.\n\n"
            "Dass mehrere Senatoren gleichzeitig aktiv werden, darunter mit "
            "[[Mark Kelly]] ein ehemaliger Marineoffizier, deutet darauf hin, "
            "dass die Kritik über reine Parteipolitik hinausgeht und auch "
            "grundsätzliche Fragen zur Belastbarkeit der Flotte berührt, "
            "insbesondere wenn militärische Präsenz gleichzeitig in mehreren "
            "Weltregionen aufrechterhalten werden muss."
        ),
        "cui_bono": (
            "Für [[Ruben Gallego]], [[Richard Blumenthal]] und [[Mark Kelly]] "
            "bietet die Situation, jeweils unabhängig voneinander, eine "
            "Gelegenheit, sich als Verfechter der Fürsorgepflicht gegenüber "
            "Truppen zu positionieren, unabhängig vom Ausgang einer möglichen "
            "Untersuchung. Für [[Pete Hegseth]] und das Pentagon steht vor "
            "allem die eigene Handlungsfähigkeit auf dem Spiel: Eine schnelle, "
            "entschiedene Zurückweisung der Berichte vermeidet, dass die "
            "strukturelle Überlastung der Flotte, verursacht durch die "
            "gleichzeitige Bindung im [[US-Israel-Iran-Konflikt]] und im "
            "Pazifik, zum eigentlichen Thema wird."
        ),
        "historical_threads": [
            {
                "id": "usa-iran",
                "title": "USA-Iran-Konflikt",
                "entries": [
                    {
                        "date": "1979",
                        "title": "Islamische Revolution & Geiselnahme von Teheran",
                        "one_line": "Der Sturz des US-gestützten Schahs und die anschließende Geiselnahme in der US-Botschaft besiegeln den bis heute andauernden Bruch zwischen den USA und Iran.",
                        "extended": (
                            "444 Tage lang wurden 52 US-Diplomaten festgehalten. Seither "
                            "bestehen keine offiziellen diplomatischen Beziehungen zwischen "
                            "beiden Staaten, die strukturelle Grundlage jeder späteren "
                            "Eskalation."
                        ),
                    },
                    {
                        "date": "2015",
                        "title": "Atomabkommen (JCPOA)",
                        "one_line": "Iran und mehrere Weltmächte einigen sich auf eine Begrenzung des iranischen Atomprogramms gegen Sanktionserleichterungen.",
                        "extended": None,
                    },
                    {
                        "date": "2018",
                        "title": "US-Ausstieg aus dem Atomabkommen",
                        "one_line": "Die erste Trump-Administration steigt einseitig aus dem JCPOA aus und verhängt eine Sanktionskampagne unter dem Namen 'Maximum Pressure'.",
                        "extended": (
                            "Die Kampagne zielte darauf, Irans Ölexporte auf nahe null zu "
                            "drücken. Iran reagierte mit schrittweiser Wiederaufnahme der "
                            "Urananreicherung, dem Beginn der aktuellen Eskalationsspirale."
                        ),
                    },
                    {
                        "date": "2020",
                        "title": "Tötung von Qassem Soleimani",
                        "one_line": "Ein US-Drohnenangriff tötet den iranischen General Qassem Soleimani, die bis dahin schärfste direkte Konfrontation.",
                        "extended": None,
                    },
                    {
                        "date": "2026-02-28",
                        "title": "Gemeinsame US-israelische Angriffe auf Iran",
                        "one_line": "Gemeinsame US-israelische Luftschläge treffen iranische Ziele, das Weiße Haus meldet dem Kongress die Angriffe unter Berufung auf die Befugnisse des Präsidenten als Oberbefehlshaber.",
                        "extended": (
                            "Genau diese Eskalation ist der unmittelbare Auslöser der "
                            "jetzigen Story: Sie verlängerte den Lincoln-Einsatz auf "
                            "unbestimmte Zeit und löste die Krise an Bord aus, die jetzt "
                            "Senatoren auf den Plan ruft. An den Finanzmärkten war die "
                            "Eskalation direkt sichtbar, siehe die Marktkorrelation unten."
                        ),
                    },
                ],
            },
            {
                "id": "congressional-oversight",
                "title": "Kongressaufsicht über Militäreinsätze",
                "entries": [
                    {
                        "date": "1973",
                        "title": "War Powers Resolution",
                        "one_line": "Der Kongress verabschiedet gegen ein Veto von Präsident Nixon die War Powers Resolution, die Unterrichtungs- und Konsultationspflichten der Exekutive bei Truppeneinsätzen festschreibt.",
                        "extended": (
                            "Ausgelöst durch die Erfahrung des Vietnamkriegs, in dem sich "
                            "der Kongress systematisch übergangen sah. Bindende "
                            "Vorabzustimmungen zu einzelnen Einsätzen blieben aber die "
                            "Ausnahme, das Gesetz wurde seither von jeder Administration "
                            "unterschiedlich ausgelegt."
                        ),
                    },
                    {
                        "date": "1991",
                        "title": "Autorisierung des Golfkriegs",
                        "one_line": "Der Kongress stimmt vor dem Zweiten Golfkrieg erstmals seit Vietnam wieder förmlich über eine Kriegsermächtigung ab, ein seltener Fall direkter Mitsprache statt bloßer Aufsicht.",
                        "extended": None,
                    },
                    {
                        "date": "2001-2002",
                        "title": "Kriegsermächtigungen nach dem 11. September",
                        "one_line": "Zwei breit gefasste Ermächtigungen zum Einsatz militärischer Gewalt geben der Exekutive über zwei Jahrzehnte weiten Spielraum, der Kongress verlagert sich zunehmend auf nachträgliche Aufsicht statt Vorabkontrolle.",
                        "extended": (
                            "Diese Ermächtigungen wurden seither von mehreren "
                            "Administrationen als Rechtsgrundlage für Einsätze weit über "
                            "den ursprünglichen Anlass hinaus herangezogen, was die "
                            "Kontrollfunktion des Kongresses in der Praxis weiter "
                            "schwächte."
                        ),
                    },
                    {
                        "date": "2026-03",
                        "title": "Kongressdebatte über eine War-Powers-Resolution zu Iran",
                        "one_line": "Nach den Angriffen vom 28. Februar meldet das Weiße Haus die Angriffe formal an den Kongress, mehrere Abgeordnete bringen eine Resolution zur Beendigung der Feindseligkeiten ein.",
                        "extended": (
                            "Die Debatte im Repräsentantenhaus zeigt die klassische Grenze "
                            "des Instruments: Die Resolution wird diskutiert, ändert aber "
                            "nichts an der fortgesetzten Bindung der Flotte im Nahen Osten, "
                            "die wenige Monate später zur Ausgangslage der jetzigen "
                            "Lincoln-Krise wird."
                        ),
                    },
                    {
                        "date": "2026-08",
                        "title": "Senatoren fordern Aufsicht über die USS Abraham Lincoln",
                        "one_line": "Statt einer bindenden Resolution setzen mehrere Senatoren, unabhängig voneinander, auf die klassischen Werkzeuge der nachträglichen Aufsicht: Briefe, öffentliche Kritik und die Forderung nach einem Delegationsbesuch.",
                        "extended": None,
                    },
                ],
            },
        ],
        "quotes": [
            {
                "text": "That's not proper leadership.",
                "attribution": "Senator Ruben Gallego (Demokrat, Arizona)",
                "context": "Kritisiert die Reaktion der Marineführung auf die Berichte über die Zustände an Bord der USS Abraham Lincoln.",
                "source_url": "https://www.npr.org/2026/08/14/nx-s1-5930365/uss-abraham-lincoln-iran-navy-ruben-gallego",
            },
            {
                "text": "They're just kind of winging it right now.",
                "attribution": "Senator Ruben Gallego (Demokrat, Arizona)",
                "context": "",
                "source_url": "https://www.npr.org/2026/08/14/nx-s1-5930365/uss-abraham-lincoln-iran-navy-ruben-gallego",
            },
            {
                "text": "We make sure that every ship, every crew, every captain has everything we can provide them.",
                "attribution": "Pete Hegseth, US-Verteidigungsminister",
                "context": "Reaktion auf die Kritik an den Zuständen an Bord der USS Abraham Lincoln.",
                "source_url": "https://www.cbsnews.com/news/uss-abraham-lincoln-democratic-senators-inquiry-demand/",
            },
        ],
        "entities": [
            {
                "name": "USS Abraham Lincoln",
                "type": "organization",
                "role_in_story": "Seit über 250 Tagen im Nahost-Einsatz und über 200 Tagen ohne Hafenaufenthalt, Ausgangspunkt der Berichte über Versorgungsengpässe und psychische Belastung.",
                "profile": "Flugzeugträger der Nimitz-Klasse, seit 1989 im Dienst, einer der älteren aktiven US-Flugzeugträger.",
                "established": "1989",
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/d/db/USS_Abraham_Lincoln_(CVN-72)_underway_in_the_Atlantic_Ocean_on_30_January_2019_(190130-N-PW716-1312).JPG",
            },
            {
                "name": "USS George Washington",
                "type": "organization",
                "role_in_story": "Soll die Lincoln ablösen, verlässt dafür den Pazifik.",
                "profile": "Flugzeugträger der Nimitz-Klasse, seit 1992 im Dienst, regulär in Yokosuka (Japan) stationiert als Teil der US-Vorwärtspräsenz im Pazifik.",
                "established": "1992",
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/a/af/Flickr_-_Official_U.S._Navy_Imagery_-_USS_George_Washington_is_in_the_East_China_Sea_during_a_trilateral_exercise_with_the_Japan_Maritime_Self_Defence_Force_and_Republic_of_Korea_Navy..jpg",
            },
            {
                "name": "Ruben Gallego",
                "type": "person",
                "role_in_story": "Kritisiert die Marineführung öffentlich am schärfsten und fordert einen Delegationsbesuch an Bord.",
                "profile": "US-Senator (Demokrat, Arizona), Marine-Corps-Veteran mit Irak-Einsatz, tritt wiederholt zu Fragen militärischer Fürsorgepflicht auf.",
                "established": None,
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/b/b7/Senator_Ruben_Gallego_Official_Portrait.jpg",
            },
            {
                "name": "Richard Blumenthal",
                "type": "person",
                "role_in_story": "Schickt ein offizielles Schreiben an das Verteidigungsministerium mit der Forderung nach Aufklärung bis zum 27. August.",
                "profile": "US-Senator (Demokrat, Connecticut), tritt regelmäßig bei Fragen der Aufsicht über Behörden und Streitkräfte auf.",
                "established": None,
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/4/46/Senator_Richard_Blumenthal_at_the_White_House%2C_2024_%28cropped%29.jpg",
            },
            {
                "name": "Mark Kelly",
                "type": "person",
                "role_in_story": "Äußert sich öffentlich besorgt über die Berichte über die Zustände an Bord.",
                "profile": "US-Senator (Demokrat, Arizona), ehemaliger Navy-Kampfpilot und Astronaut, seine Kritik hat wegen der eigenen Militärlaufbahn besonderes Gewicht.",
                "established": None,
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/e1/Mark_Kelly%2C_Official_Portrait_117th.jpg",
            },
            {
                "name": "Pete Hegseth",
                "type": "person",
                "role_in_story": "Weist als US-Verteidigungsminister die Berichte über schlechte Zustände an Bord zurück.",
                "profile": "US-Verteidigungsminister, verteidigt öffentlich typischerweise die Einsatzbereitschaft des Militärs gegen kritische Berichterstattung.",
                "established": None,
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/a/a4/Secretary_of_Defense_Pete_Hegseth_official_portrait_(cropped).jpg",
            },
            {
                "name": "Iran",
                "type": "country",
                "role_in_story": "Gegner im Konflikt, der die Lincoln im Nahen Osten bindet.",
                "profile": "Regionalmacht im Nahen Osten, seit Februar 2026 in eskalierter Konfrontation mit den USA und Israel, Beziehungen zu den USA seit 1979 grundlegend zerrüttet.",
                "established": None,
                "image_url": FLAG_IRAN,
            },
            {
                "name": "Kongress",
                "type": "organization",
                "role_in_story": "Übt über einzelne Senatoren Aufsicht über die Verhältnisse an Bord aus.",
                "profile": "Gesetzgebendes Organ der USA, versucht seit der War Powers Resolution von 1973 wiederkehrend, über Anhörungen und Aufsicht Einfluss auf Militäreinsätze der Exekutive zu behalten.",
                "established": "1789",
                "image_url": None,
            },
            {
                "name": "War Powers Resolution",
                "type": "concept",
                "role_in_story": "Rechtlicher Hintergrund, vor dem die heutige Aufsichtsforderung einzuordnen ist.",
                "profile": "US-Bundesgesetz von 1973, das Unterrichtungs- und Konsultationspflichten der Exekutive gegenüber dem Kongress bei Truppeneinsätzen festschreibt, aber keine bindende Vorabzustimmung erzwingt.",
                "established": "1973",
                "image_url": None,
            },
            {
                "name": "US-Israel-Iran-Konflikt",
                "type": "event",
                "role_in_story": "Bindet seit Februar 2026 US-Trägerkapazitäten im Nahen Osten und ist der eigentliche Auslöser der jetzigen Krise an Bord.",
                "profile": "Militärische Eskalation seit den gemeinsamen US-israelischen Angriffen vom 28. Februar 2026, Auslöser der Verlängerung des Lincoln-Einsatzes und einer sichtbaren Reaktion an den Finanzmärkten.",
                "established": "2026-02-28",
                "image_url": None,
            },
        ],
        "connections": [
            {"source": "USS George Washington", "target": "USS Abraham Lincoln", "relation": "soll ablösen"},
            {"source": "USS Abraham Lincoln", "target": "US-Israel-Iran-Konflikt", "relation": "im Einsatz seit Februar-Eskalation"},
            {"source": "Ruben Gallego", "target": "Kongress", "relation": "fordert als Mitglied eine Aufsichtsdelegation"},
            {"source": "Richard Blumenthal", "target": "Pete Hegseth", "relation": "verlangt in einem offiziellen Schreiben Aufklärung von"},
            {"source": "Kongress", "target": "War Powers Resolution", "relation": "stützt seine Aufsichtsrolle auf"},
        ],
        "sources": ["NPR – Politics", "Al Jazeera – All", "CBS News – World"],
        "article_urls": [
            "https://www.npr.org/2026/08/14/nx-s1-5930365/uss-abraham-lincoln-iran-navy-ruben-gallego",
            "https://www.aljazeera.com/news/2026/8/13/reports-of-us-sailors-in-middle-east-trying-to-jump-ship-spark-outcry",
            "https://www.cbsnews.com/news/uss-abraham-lincoln-democratic-senators-inquiry-demand/",
            "https://www.npr.org/2026/08/13/g-s1-138591/uss-abraham-lincoln-conditions",
        ],
        "countries_covered": ["USA", "Iran"],
        "primary_sources": [
            {
                "title": "Brief an Verteidigungsminister Hegseth und die amtierende Marine-Staatssekretärin zu den Zuständen an Bord der USS Abraham Lincoln",
                "issuer": "Büro von Senator Richard Blumenthal",
                "url": "https://www.blumenthal.senate.gov/imo/media/doc/2026-8-12_letter_to_sec_hegseth__cao_re_uss_lincoln.pdf",
                "date": "2026-08-12",
                "note": "Amtliches PDF, stellt sechs konkrete Fragen mit Frist zum 27.08.2026.",
            },
            {
                "title": "Pressemitteilung: Forderung nach einem offiziellen Aufsichtsbesuch an Bord",
                "issuer": "Büro von Senator Ruben Gallego",
                "url": "https://www.gallego.senate.gov/news/press-releases/senator-gallego-on-reporting-of-abysmal-uss-lincoln-conditions-i-am-seeking-an-official-oversight-visit/",
                "date": "2026-08-12",
                "note": "",
            },
            {
                "title": "Kongressprotokoll: Debatte über eine War-Powers-Resolution zur Beendigung der Feindseligkeiten mit Iran",
                "issuer": "U.S. Congressional Record (govinfo.gov)",
                "url": "https://www.govinfo.gov/content/pkg/CREC-2026-03-04/html/CREC-2026-03-04-pt1-PgH2395.htm",
                "date": "2026-03-04",
                "note": "Offizielles Kongressprotokoll zu H. Con. Res. 38.",
            },
        ],
        "political_theory": {
            "theory": "Prinzipal-Agent-Theorie in der zivil-militärischen Aufsicht",
            "points": [
                "Der Kongress (Prinzipal) beauftragt Exekutive und Militär (Agent) mit der Durchführung von Einsätzen, kann deren laufende Entscheidungen aber nicht direkt kontrollieren, ein klassisches Informationsgefälle.",
                "Weil eine bindende Vorabkontrolle einzelner Einsätze politisch fast nie durchsetzbar ist, greift der Kongress auf schwächere Instrumente zurück: Anhörungen, Briefe, Delegationsbesuche.",
                "Die War Powers Resolution von 1973 sollte dieses Ungleichgewicht beheben, wurde aber seither von jeder Administration unterschiedlich ausgelegt, ein Beispiel dafür, wie Kontrollmechanismen ohne Durchsetzungsmacht erodieren.",
                "Dass drei Senatoren unabhängig voneinander tätig werden, zeigt, dass Aufsicht in der Praxis oft fragmentiert und individuell erfolgt, statt als koordinierte institutionelle Reaktion.",
            ],
        },
        "market_correlation": {
            "has_correlation": True,
            "explanation": (
                "Nicht die heutige Meldung selbst, sondern die zugrunde liegende "
                "Eskalation vom 28. Februar 2026 zeigt einen klaren, mehrfach "
                "belegten Marktzusammenhang: Am ersten Handelstag danach (2. März "
                "2026) stieg der Ölpreis deutlich, und Rüstungsaktien wie Lockheed "
                "Martin erreichten Rekordstände. Das illustriert, wie diese "
                "historische Linie über die Berichterstattung hinaus messbare "
                "wirtschaftliche Folgen hatte."
            ),
            "series": [
                {
                    "label": "Brent Crude Oil",
                    "raw_unit": "USD/Barrel",
                    "points": [
                        {"date": "2026-02-24", "value": 99.5},
                        {"date": "2026-02-25", "value": 100.3},
                        {"date": "2026-02-26", "value": 99.8},
                        {"date": "2026-02-27", "value": 100.0},
                        {"date": "2026-03-02", "value": 108.2},
                        {"date": "2026-03-03", "value": 106.5},
                    ],
                    "source_url": "https://finance.yahoo.com/news/oil-prices-surge-to-cross-80-after-us-iran-conflict-engulfs-middle-east-and-strait-of-hormuz-233642824.html",
                },
                {
                    "label": "Lockheed Martin (LMT)",
                    "raw_unit": "USD",
                    "points": [
                        {"date": "2026-02-24", "value": 99.2},
                        {"date": "2026-02-25", "value": 99.6},
                        {"date": "2026-02-26", "value": 100.1},
                        {"date": "2026-02-27", "value": 100.0},
                        {"date": "2026-03-02", "value": 104.4},
                        {"date": "2026-03-03", "value": 105.1},
                    ],
                    "source_url": "https://www.schaeffersresearch.com/content/news/2026/03/02/lockheed-martin-stock-hits-record-as-iran-conflict-heightens",
                },
            ],
            "note": (
                "Werte indexiert auf 100 = Schlusskurs 27.02.2026 (letzter "
                "Handelstag vor der Eskalation vom 28.02.). Der Verlauf vor der "
                "Eskalation ist als nahezu flach angenähert, nicht einzeln "
                "tagesgenau belegt. Die Bewegung zum 2.3.2026 entspricht den "
                "berichteten Werten: Brent Crude etwa +8% auf rund 79 "
                "US-Dollar (intraday bis zu +13%), Lockheed Martin +4,4% auf ein "
                "Rekordhoch von 692 US-Dollar."
            ),
        },
        "image_url": (
            "https://npr.brightspotcdn.com/dims3/default/strip/false/crop/4719x2654+0+492/"
            "resize/1400/quality/85/format/jpeg/?url=http%3A%2F%2Fnpr-brightspot.s3.amazonaws.com"
            "%2F54%2F0f%2F60a111394423be133b8000d80b81%2Fap26060522777051.jpg"
        ),
    },
    # -----------------------------------------------------------------
    # STORY 2, Widerruf von Green Cards afghanischer SIV-Empfänger
    # -----------------------------------------------------------------
    {
        "id": "afghan-siv-revocations-2026-08",
        "title": "Fünf Jahre nach der Evakuierung: USA stellen Green Cards afghanischer Kriegsverbündeter infrage",
        "one_line": (
            "Hunderte Afghanen, die über das "
            "[[Special Immigrant Visa (SIV) Programm]] als Kriegsverbündete "
            "der [[USA]] eingewandert waren, erhalten Schreiben, die ihre "
            "bereits erteilten Green Cards infrage stellen, Ergebnis der "
            "verschärften Überprüfungspolitik der [[Trump-Regierung]]."
        ),
        "summary": [
            "Hunderte Afghanen mit bereits erteilten, über das [[Special Immigrant Visa (SIV) Programm]] erhaltenen Green Cards erhalten Schreiben, die ihren Aufenthaltsstatus rückwirkend infrage stellen.",
            "Grundlage ist eine Anordnung der [[Trump-Regierung]] zur umfassenden Neuüberprüfung von Green-Card-Inhabern aus als sicherheitsrelevant eingestuften Ländern.",
            "Ein Bundesgericht erklärte im Juni 2026 Teile dieser pauschalen Überprüfungspolitik für rechtswidrig.",
            "Rechtsorganisationen wie die [[International Refugee Assistance Project (IRAP)]] bezeichnen den nachträglichen Widerruf bereits erteilter Visa als verfahrensrechtlich neuartig.",
            "Betroffene berichten von Unsicherheit im Alltag zwischen Arbeit, Familie und der Suche nach rechtlichem Beistand.",
        ],
        "deep_dive": (
            "Diese Story ist der jüngste Punkt zweier eigenständiger "
            "Entwicklungslinien. Die eine ist die institutionelle Geschichte "
            "des [[Special Immigrant Visa (SIV) Programm]]s selbst: 2009 als "
            "Dank und Schutz für afghanische Ortskräfte geschaffen, seit "
            "jeher von Bearbeitungsstaus geprägt, seit der überstürzten "
            "Evakuierung 2021 stark ausgeweitet und seit Ende 2025 für neue "
            "Anträge geschlossen. Die andere ist eine deutlich jüngere, "
            "unabhängige Linie: die sicherheitsgetriebene Verschärfung der "
            "US-Einwanderungspolitik seit 2025, ausgelöst durch einen "
            "einzelnen Vorfall und seither auf ganze Bevölkerungsgruppen "
            "ausgeweitet.\n\n"
            "Beide Linien betreffen dieselben Menschen, folgen aber "
            "unterschiedlichen Logiken: Das SIV-Programm ist als Belohnung "
            "für geleistete Kriegsunterstützung gedacht, die neue "
            "Überprüfungspolitik behandelt denselben Personenkreis als "
            "potenzielles Sicherheitsrisiko. Ein Bundesgericht erklärte im "
            "Juni 2026 Teile der pauschalen Überprüfungspolitik für "
            "rechtswidrig, was die praktische Wirkung der aktuellen "
            "Widerrufswelle zusätzlich unklar macht.\n\n"
            "Rechtsorganisationen wie die "
            "[[International Refugee Assistance Project (IRAP)]] bezeichnen "
            "die Praxis als verfahrensrechtlich neuartig: Ein Widerruf einer "
            "Zulassung Jahre nach der eigentlichen Visaerteilung hat es in "
            "diesem Umfang zuvor nicht gegeben."
        ),
        "cui_bono": (
            "Für die migrationspolitische Linie der [[Trump-Regierung]] "
            "dient die umfassende Überprüfung als sichtbares Zeichen "
            "konsequenter Sicherheitspolitik, unabhängig davon, wie viele "
            "der überprüften Fälle am Ende tatsächlich einen Betrugs- oder "
            "Sicherheitsbezug haben. Organisationen wie die "
            "[[International Refugee Assistance Project (IRAP)]] und "
            "[[AfghanEvac]] gewinnen durch ihre Fürsprecherrolle an "
            "Sichtbarkeit und politischem Gewicht. Die unmittelbar "
            "betroffenen ehemaligen afghanischen Kriegsverbündeten tragen "
            "dagegen die Kosten der Unsicherheit, ohne selbst Einfluss auf "
            "die politische Linie zu haben, der sie unterliegen."
        ),
        "historical_threads": [
            {
                "id": "siv-programme",
                "title": "SIV-Einwanderungsprogramm",
                "entries": [
                    {
                        "date": "2009",
                        "title": "Afghan Allies Protection Act",
                        "one_line": "Der US-Kongress schafft das Special-Immigrant-Visa-Programm für afghanische Staatsbürger, die für die US-Regierung oder das US-Militär gearbeitet haben.",
                        "extended": (
                            "Gedacht als Dank und Schutz für Ortskräfte (Dolmetscher, "
                            "Fahrer, Kontaktpersonen), die durch ihre Zusammenarbeit mit "
                            "den USA in ihrer Heimat gefährdet waren."
                        ),
                    },
                    {
                        "date": "2013",
                        "title": "Bearbeitungsstau wird öffentlich",
                        "one_line": "Berichte über jahrelange Wartezeiten und einen riesigen SIV-Antragsstau häufen sich.",
                        "extended": None,
                    },
                    {
                        "date": "2021-08",
                        "title": "Evakuierungswelle",
                        "one_line": "Im Chaos des US-Abzugs werden zehntausende Afghanen im Eilverfahren über das SIV-Programm evakuiert.",
                        "extended": (
                            "Viele Verfahren wurden unter enormem Zeitdruck abgeschlossen, "
                            "genau diese beschleunigten Fälle stehen laut heutigen "
                            "Berichten jetzt besonders im Fokus der rückwirkenden "
                            "Prüfungen."
                        ),
                    },
                    {
                        "date": "2022",
                        "title": "Afghan Adjustment Act scheitert im Kongress",
                        "one_line": "Ein Gesetzesvorschlag, der evakuierten Afghanen einen dauerhaften Rechtsstatus verschaffen sollte, findet keine Mehrheit.",
                        "extended": (
                            "Viele Evakuierte blieben dadurch auf befristete, konditionale "
                            "Status angewiesen, die rechtliche Unsicherheit, die die "
                            "heutigen Widerrufe erst möglich macht."
                        ),
                    },
                    {
                        "date": "2025-12",
                        "title": "Programm stoppt neue Anträge",
                        "one_line": "Das SIV-Programm nimmt nach über 15 Jahren keine neuen Anträge über den diplomatischen Weg mehr an.",
                        "extended": None,
                    },
                ],
            },
            {
                "id": "immigration-crackdown",
                "title": "Verschärfte Sicherheitsüberprüfung (2025/26)",
                "entries": [
                    {
                        "date": "2025",
                        "title": "Schusswaffenvorfall und Überprüfungsanordnung",
                        "one_line": "Nach einem Schusswaffenvorfall mit Beteiligung eines afghanischen Asylbewerbers und Angehörigen der Nationalgarde von West Virginia ordnet die Trump-Regierung eine umfassende Neuüberprüfung von Green-Card-Inhabern aus als sicherheitsrelevant eingestuften Ländern an.",
                        "extended": (
                            "Die zuständige Einwanderungsbehörde begründete den Schritt "
                            "damit, dass die Sicherheit der amerikanischen Bevölkerung "
                            "immer an erster Stelle stehe."
                        ),
                    },
                    {
                        "date": "2025-12",
                        "title": "Ausgeweiteter Einreisestopp",
                        "one_line": "Ein per Proklamation erweiterter Einreisestopp, der auch afghanische Staatsbürger betrifft, wird verkündet und tritt zum Jahreswechsel in Kraft.",
                        "extended": None,
                    },
                    {
                        "date": "2026-06",
                        "title": "Bundesgericht kippt Teile der Politik",
                        "one_line": "Ein Bundesgericht in Rhode Island erklärt mehrere USCIS-Politiken zur pauschalen Aussetzung und Überprüfung für rechtswidrig.",
                        "extended": None,
                    },
                    {
                        "date": "2026-08",
                        "title": "Hunderte Widerrufsschreiben",
                        "one_line": "Hunderte Inhaber afghanistanbezogener Green Cards erhalten Schreiben, die ihre Zulassung rückwirkend infrage stellen.",
                        "extended": None,
                    },
                ],
            },
        ],
        "quotes": [
            {
                "text": (
                    "We are trying to work, study, raise our children and build a "
                    "normal life in the U.S. But now we are also trying to find "
                    "lawyers, contact congressional offices and understand what "
                    "may happen to our green cards."
                ),
                "attribution": "M., afghanischer Staatsbürger mit widerrufener SIV-Zusage (vollständiger Name laut NPR aus Sicherheitsgründen nicht genannt)",
                "context": "",
                "source_url": "https://www.npr.org/2026/08/15/nx-s1-5897606/afghanistan-visa-green-card-deport",
            },
            {
                "text": "To get a withdrawal of approval letter years after the actual visa has been issued is something we haven't ever seen before.",
                "attribution": "Jennifer Patota, stellvertretende Direktorin für US-Rechtsdienste, International Refugee Assistance Project (IRAP)",
                "context": "",
                "source_url": "https://www.npr.org/2026/08/15/nx-s1-5897606/afghanistan-visa-green-card-deport",
            },
        ],
        "entities": [
            {
                "name": "Special Immigrant Visa (SIV) Programm",
                "type": "concept",
                "role_in_story": "Programm, über das afghanische Kriegsverbündete US-Visa erhalten hatten, dessen Zusagen jetzt rückwirkend geprüft werden.",
                "profile": "Seit 2009 laufendes US-Einwanderungsprogramm für afghanische und irakische Staatsbürger, die für die US-Regierung oder das US-Militär gearbeitet haben, seit Ende 2025 für neue Anträge geschlossen.",
                "established": "2009",
                "image_url": None,
            },
            {
                "name": "USA",
                "type": "country",
                "role_in_story": "Stellt fünf Jahre nach dem Abzug aus Afghanistan bereits erteilte Aufenthaltszusagen an ehemalige Verbündete infrage.",
                "profile": "Führte 2001 bis 2021 den längsten Auslandseinsatz seiner Geschichte in Afghanistan.",
                "established": None,
                "image_url": FLAG_USA,
            },
            {
                "name": "Trump-Regierung",
                "type": "organization",
                "role_in_story": "Ordnet die umfassende Neuüberprüfung an, aus der die aktuellen Widerrufsschreiben hervorgehen.",
                "profile": "Aktuelle US-Regierung, verfolgt eine Linie deutlich verschärfter Einwanderungskontrolle.",
                "established": None,
                "image_url": None,
            },
            {
                "name": "USCIS",
                "type": "organization",
                "role_in_story": "Führt die Neuüberprüfung durch und verschickt die Widerrufsschreiben.",
                "profile": "US-Einwanderungsbehörde (U.S. Citizenship and Immigration Services), zuständig für die Bearbeitung und Überprüfung von Einwanderungsanträgen.",
                "established": "2003",
                "image_url": None,
            },
            {
                "name": "International Refugee Assistance Project (IRAP)",
                "type": "organization",
                "role_in_story": "Vertritt betroffene Visa-Inhaber rechtlich und ordnet die Widerrufspraxis öffentlich ein.",
                "profile": "Gemeinnützige Rechtsorganisation, die Geflüchtete und Einwanderer, darunter viele ehemalige afghanische Kriegsverbündete, in Einwanderungsverfahren vertritt.",
                "established": None,
                "image_url": None,
            },
            {
                "name": "AfghanEvac",
                "type": "organization",
                "role_in_story": "Setzt sich als Fürsprecher für die Rechte betroffener Afghanen ein.",
                "profile": "Veteranengeführte Koalition, die sich seit der Evakuierung 2021 für die Neuansiedlung afghanischer Kriegsverbündeter in den USA einsetzt.",
                "established": "2021",
                "image_url": None,
            },
        ],
        "connections": [
            {"source": "Trump-Regierung", "target": "Special Immigrant Visa (SIV) Programm", "relation": "ordnet rückwirkende Überprüfung von Visa aus diesem Programm an"},
            {"source": "USCIS", "target": "Special Immigrant Visa (SIV) Programm", "relation": "führt die Neuüberprüfung der erteilten Visa durch"},
            {"source": "International Refugee Assistance Project (IRAP)", "target": "Special Immigrant Visa (SIV) Programm", "relation": "vertritt betroffene Visa-Inhaber rechtlich"},
            {"source": "AfghanEvac", "target": "USA", "relation": "setzt sich für die Neuansiedlung afghanischer Kriegsverbündeter ein in"},
        ],
        "sources": ["NPR – World", "Fox News – World"],
        "article_urls": [
            "https://www.npr.org/2026/08/15/nx-s1-5897606/afghanistan-visa-green-card-deport",
            "https://www.foxnews.com/politics/how-green-card-can-revoked-where-trumps-new-review-order-fits-process",
            "https://support.iraplegalinfo.org/hc/en-us/articles/43977659159188-What-do-the-recent-U-S-immigration-changes-mean-for-Afghans",
        ],
        "countries_covered": ["Afghanistan", "USA"],
        "primary_sources": [
            {
                "title": "Proclamation 10998: Ausweitung der Einreisebeschränkungen auf 39 Länder",
                "issuer": "Federal Register / The White House",
                "url": "https://www.federalregister.gov/documents/2025/12/19/2025-23570/restricting-and-limiting-the-entry-of-foreign-nationals-to-protect-the-security-of-the-united-states",
                "date": "2025-12-19",
                "note": "",
            },
            {
                "title": "Beendigung des Temporary Protected Status für Afghanistan",
                "issuer": "U.S. Department of Homeland Security / Federal Register",
                "url": "https://www.federalregister.gov/documents/2025/05/13/2025-08201/termination-of-the-designation-of-afghanistan-for-temporary-protected-status",
                "date": "2025-05-13",
                "note": "",
            },
            {
                "title": "Dorcas International Institute of Rhode Island v. USCIS (Az. 1:26-cv-00132)",
                "issuer": "U.S. District Court, District of Rhode Island",
                "url": "https://www.nixonpeabody.com/insights/alerts/2026/06/08/rhode-island-federal-court-vacates-uscis-immigration-benefit-freeze-policies",
                "date": "2026-06-05",
                "note": "Volltext des Urteils ist über PACER zugänglich, verlinkt ist eine Kanzlei-Zusammenfassung mit direkten Zitaten aus der Entscheidung.",
            },
        ],
        "political_theory": {
            "theory": "Versicherheitlichung (Securitization Theory)",
            "points": [
                "Nach der Kopenhagener Schule wird ein Thema 'versicherheitlicht', wenn ein politischer Akteur es erfolgreich als existenzielle Bedrohung rahmt und damit Maßnahmen rechtfertigt, die außerhalb normaler rechtsstaatlicher Verfahren liegen würden.",
                "Ein einzelner Vorfall wird hier zum Auslöser, eine ganze, bereits rechtmäßig im Land lebende Bevölkerungsgruppe pauschal neu zu überprüfen, ein typisches Muster versicherheitlichter Politik.",
                "Die Gerichtsentscheidung vom Juni 2026 zeigt die Gegenkraft zur Versicherheitlichung: rechtsstaatliche Institutionen, die die pauschale Einstufung als Sicherheitsrisiko wieder an individuelle Prüfung binden.",
                "Das SIV-Programm selbst entstand aus der gegenteiligen Logik, Zugehörigkeit durch Verdienst um die USA, ein Beispiel dafür, wie sich politische Rahmungen desselben Personenkreises über Zeit umkehren können.",
            ],
        },
        "market_correlation": {
            "has_correlation": False,
            "explanation": (
                "Es wurde geprüft, ob sich diese Politik in Aktien von privaten "
                "Haftanstaltsbetreibern wie GEO Group oder CoreCivic "
                "niederschlägt, da diese Unternehmen auf allgemeine "
                "Einwanderungsvollzugspolitik reagieren. Für die SIV-"
                "Widerrufswelle speziell wurde jedoch keine erkennbare "
                "Marktreaktion gefunden: Die Betroffenen sind eine kleine, "
                "bereits legal im Land lebende Gruppe ohne Bezug zu neuer "
                "Haftkapazität, ein plausibler Grund für das Ausbleiben einer "
                "messbaren Reaktion."
            ),
            "series": [],
            "note": "",
        },
        "image_url": (
            "https://npr.brightspotcdn.com/dims3/default/strip/false/crop/5400x3038+0+281/"
            "resize/1400/quality/85/format/jpeg/?url=http%3A%2F%2Fnpr-brightspot.s3.amazonaws.com"
            "%2F2f%2F10%2F1044f9c34be8bd15a6eac178a202%2Fgettyimages-1234325178.jpg"
        ),
    },
    # -----------------------------------------------------------------
    # STORY 3, Sudan: al-Burhan verspricht Dialog, schließt RSF-Rückkehr aus
    # -----------------------------------------------------------------
    {
        "id": "sudan-national-dialogue-2026-08",
        "title": "Sudans Armeechef verspricht Dialog und Immunität, schließt Rückkehr der RSF an die Macht aus",
        "one_line": (
            "[[Abdel Fattah al-Burhan]] kündigt einen landesweiten Dialog mit "
            "befristeter Immunität für Teilnehmende an, macht aber klar, dass "
            "er keinen Frieden akzeptiert, der die "
            "[[Rapid Support Forces (RSF)]] unter "
            "[[Mohamed Hamdan Dagalo]] zurück an die Macht bringt."
        ),
        "summary": [
            "[[Abdel Fattah al-Burhan]] kündigt einen landesweiten, inklusiven Dialog mit politischen und zivilen Parteien an, mit rechtlichen, politischen, sicherheitsbezogenen und logistischen Garantien durch den Staat.",
            "Teilnehmenden mit laufenden Strafverfahren soll für die Dauer des Dialogs eine befristete Aussetzung dieser Verfahren gewährt werden, ausdrücklich kein Straferlass.",
            "Ein Frieden, der die [[Rapid Support Forces (RSF)]] unter [[Mohamed Hamdan Dagalo]] zurück an die Macht bringen würde, wird ausdrücklich ausgeschlossen.",
            "Die [[Sudanesische Armee (SAF)]] kündigt gleichzeitig an, den militärischen Kampf gegen die RSF fortzusetzen.",
            "Die Ankündigung fällt zeitlich mit einem Besuch einer Delegation der Afrikanischen Union und Sudans Bitte um Aufhebung seiner seit 2021 bestehenden Suspendierung zusammen.",
        ],
        "deep_dive": (
            "Diese Story ist der jüngste Punkt zweier miteinander "
            "verflochtener, aber unterscheidbarer Linien. Die eine ist der "
            "Bürgerkrieg selbst: Der offene Machtkampf zwischen "
            "[[Sudanesische Armee (SAF)]] und "
            "[[Rapid Support Forces (RSF)]] brach im April 2023 aus, nachdem "
            "beide Seiten zuvor gemeinsam den zivilen Übergang nach dem "
            "Sturz von Omar al-Bashir 2019 per Putsch beendet hatten. Die "
            "andere, viel längere Linie ist das wiederkehrende Muster "
            "sudanesischer Politik seit der Unabhängigkeit 1956: "
            "Volksaufstände stürzen Militärregime, eine zivile "
            "Übergangsphase folgt, und ein neuer Putsch beendet sie wieder, "
            "ein Zyklus, der sich seit den 1950er-Jahren mehrfach "
            "wiederholt hat.\n\n"
            "Das jetzige Dialogangebot fällt in eine Phase, in der "
            "[[Sudanesische Armee (SAF)]] gleichzeitig militärisch "
            "weiterkämpft und diplomatisch um internationale Anerkennung "
            "wirbt, sichtbar am zeitgleichen Besuch einer Delegation der "
            "Afrikanischen Union und Sudans Bitte um Aufhebung seiner seit "
            "dem Putsch von 2021 bestehenden Suspendierung.\n\n"
            "Zivile Gruppen wie die Bündnisallianz Somoud reagierten "
            "bereits vor der offiziellen Ankündigung mit Vorbehalten. Aus "
            "ihrer Sicht ist ein von der Militärführung initiierter Dialog "
            "schwer von einer Vereinnahmung des zivilen Übergangs zu "
            "unterscheiden, die genau diesem Muster wiederholter Putsche "
            "entspricht."
        ),
        "cui_bono": (
            "Für [[Abdel Fattah al-Burhan]] bietet die Dialoginitiative die "
            "Möglichkeit, sich international als Befürworter einer "
            "politischen Lösung zu positionieren, während die "
            "[[Sudanesische Armee (SAF)]] militärisch weiterkämpft, ein "
            "doppeltes Signal an unterschiedliche Adressaten: an "
            "ausländische Vermittler und an die eigene Basis. Für die "
            "[[Demokratische Blockpartei]], die die Ankündigung begrüßte, "
            "bedeutet Teilnahme am Dialog eine Gelegenheit zu politischem "
            "Einfluss, birgt aber das Risiko, eine militärisch dominierte "
            "Prozessführung zu legitimieren. Zivile Kräfte, die sich aus "
            "Sorge vor genau dieser Legitimierung fernhalten, laufen "
            "umgekehrt Gefahr, von der Gestaltung eines möglichen "
            "Übergangs ausgeschlossen zu bleiben."
        ),
        "historical_threads": [
            {
                "id": "sudan-civil-war",
                "title": "Sudans Bürgerkrieg (SAF gegen RSF)",
                "entries": [
                    {
                        "date": "2019",
                        "title": "Sturz von Omar al-Bashir",
                        "one_line": "Ein Volksaufstand stürzt den langjährigen Machthaber Omar al-Bashir, SAF und RSF übernehmen gemeinsam mit zivilen Kräften einen Übergangsprozess.",
                        "extended": None,
                    },
                    {
                        "date": "2021-10",
                        "title": "Militärputsch beendet zivilen Übergang",
                        "one_line": "SAF unter al-Burhan und RSF unter Hemedti stürzen gemeinsam die zivil geführte Übergangsregierung.",
                        "extended": (
                            "Der gemeinsame Putsch der beiden späteren Kriegsgegner zeigt, "
                            "dass der heutige Konflikt kein von Anfang an angelegter "
                            "Gegensatz war, sondern aus einem späteren Machtkampf zwischen "
                            "denselben Verbündeten entstand."
                        ),
                    },
                    {
                        "date": "2023-04",
                        "title": "Ausbruch des offenen Bürgerkriegs",
                        "one_line": "Kämpfe zwischen SAF und RSF um die Kontrolle über den Staat brechen offen aus, beginnend in Khartum.",
                        "extended": None,
                    },
                    {
                        "date": "2023-2025",
                        "title": "Vertreibung und humanitäre Krise",
                        "one_line": "Millionen Menschen werden landesweit vertrieben, weite Landesteile geraten unter wechselnde Kontrolle beider Kriegsparteien.",
                        "extended": None,
                    },
                    {
                        "date": "2026-08",
                        "title": "Dialogangebot bei fortgesetztem Kampf",
                        "one_line": "Al-Burhan bietet einen zivilen Dialog mit befristeter Immunität an, kündigt aber gleichzeitig die Fortsetzung des militärischen Kampfes gegen die RSF an.",
                        "extended": None,
                    },
                ],
            },
            {
                "id": "sudan-coup-cycle",
                "title": "Sudans Zyklus aus Militärherrschaft und Aufständen",
                "entries": [
                    {
                        "date": "1956",
                        "title": "Unabhängigkeit Sudans",
                        "one_line": "Der Sudan wird unabhängig, die junge Demokratie wird bereits 1958 durch den ersten Militärputsch beendet.",
                        "extended": None,
                    },
                    {
                        "date": "1969 & 1989",
                        "title": "Weitere Militärputsche",
                        "one_line": "Zwei weitere Putsche etablieren jeweils langjährige Militärregime, zuletzt unter Omar al-Bashir ab 1989.",
                        "extended": None,
                    },
                    {
                        "date": "2018-2019",
                        "title": "Volksaufstand gegen al-Bashir",
                        "one_line": "Monatelange Massenproteste zwingen das Militär, al-Bashir abzusetzen, eine zivil-militärische Übergangsregierung wird vereinbart.",
                        "extended": None,
                    },
                    {
                        "date": "2021-10",
                        "title": "Putsch beendet den Übergang erneut",
                        "one_line": "Wie schon 1958 folgt auf eine zivile Öffnung ein Putsch, diesmal von SAF und RSF gemeinsam getragen.",
                        "extended": None,
                    },
                    {
                        "date": "2026-08",
                        "title": "Neues Dialogangebot unter Kriegsbedingungen",
                        "one_line": "Ein neuer ziviler Dialog wird angeboten, diesmal während eines laufenden Krieges statt nach einem abgeschlossenen Machtwechsel, ein Novum in diesem wiederkehrenden Muster.",
                        "extended": None,
                    },
                ],
            },
        ],
        "quotes": [
            {
                "text": "an incomplete peace",
                "attribution": "Abdel Fattah al-Burhan, Vorsitzender des sudanesischen Übergangssouveränitätsrats",
                "context": "Bezeichnung für ein Friedensszenario, das die RSF zurück an die Macht bringen würde und das er ausschließt.",
                "source_url": "https://www.aljazeera.com/news/2026/8/15/sudans-al-burhan-pledges-immunity-for-dialogue-rules-out-hemedti-return",
            },
            {
                "text": "is not considered a pardon, but rather means suspending the criminal proceedings",
                "attribution": "Abdel Fattah al-Burhan, Vorsitzender des sudanesischen Übergangssouveränitätsrats",
                "context": "Erklärung zur angebotenen befristeten Immunität für Dialogteilnehmende.",
                "source_url": "https://english.aawsat.com/arab-world/5307459-sudan%E2%80%99s-al-burhan-backs-inclusive-dialogue-pledges-continue-fighting-rsf",
            },
            {
                "text": "a significant step towards addressing the crisis",
                "attribution": "Mohamed Zakaria, Sprecher der Demokratischen Blockpartei",
                "context": "Reaktion auf die Ankündigung al-Burhans.",
                "source_url": "https://english.aawsat.com/arab-world/5307459-sudan%E2%80%99s-al-burhan-backs-inclusive-dialogue-pledges-continue-fighting-rsf",
            },
        ],
        "entities": [
            {
                "name": "Abdel Fattah al-Burhan",
                "type": "person",
                "role_in_story": "Kündigt den Dialog und die befristete Immunität an, schließt eine Rückkehr der RSF an die Macht aus.",
                "profile": "Vorsitzender des sudanesischen Übergangssouveränitätsrats und Oberbefehlshaber der Sudanesischen Armee, an der Macht seit dem Putsch von 2021.",
                "established": None,
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/3/37/Abdel_Fattah_al-Burhan_in_April_2025_%28cropped%29.jpg",
            },
            {
                "name": "Rapid Support Forces (RSF)",
                "type": "organization",
                "role_in_story": "Kriegsgegner der Sudanesischen Armee, deren Rückkehr an die Macht al-Burhan ausschließt.",
                "profile": "Paramilitärische Truppe, ging aus den Dschandschawid-Milizen hervor, seit April 2023 im offenen Krieg gegen die Sudanesische Armee.",
                "established": None,
                "image_url": None,
            },
            {
                "name": "Mohamed Hamdan Dagalo",
                "type": "person",
                "role_in_story": "Führt als 'Hemedti' die RSF an, deren Rückkehr an die Macht al-Burhan explizit ausschließt.",
                "profile": "Kommandeur der Rapid Support Forces, war bis 2023 gemeinsam mit al-Burhan Teil der herrschenden Militärführung, seither dessen Kriegsgegner.",
                "established": None,
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/7/72/Mohamed_Hamdan_Dagalo_2022_%28cropped%29.jpg",
            },
            {
                "name": "Sudanesische Armee (SAF)",
                "type": "organization",
                "role_in_story": "Kämpft unter al-Burhans Führung weiter gegen die RSF, während der Staat zivilen Dialog anbietet.",
                "profile": "Reguläre Streitkräfte Sudans, seit April 2023 im offenen Bürgerkrieg gegen die Rapid Support Forces.",
                "established": None,
                "image_url": None,
            },
            {
                "name": "Demokratische Blockpartei",
                "type": "organization",
                "role_in_story": "Begrüßt al-Burhans Dialogangebot öffentlich als bedeutenden Schritt.",
                "profile": "Sudanesische politische Gruppierung, die sich zum Dialogangebot der Übergangsführung positioniert.",
                "established": None,
                "image_url": None,
            },
            {
                "name": "Sudan",
                "type": "country",
                "role_in_story": "Schauplatz des Bürgerkriegs und des jetzt angebotenen Dialogs.",
                "profile": "Nordostafrikanisches Land, seit der Unabhängigkeit 1956 von wiederkehrenden Militärputschen und zivilen Übergangsphasen geprägt.",
                "established": "1956",
                "image_url": FLAG_SUDAN,
            },
        ],
        "connections": [
            {"source": "Abdel Fattah al-Burhan", "target": "Sudanesische Armee (SAF)", "relation": "befehligt als Oberbefehlshaber"},
            {"source": "Mohamed Hamdan Dagalo", "target": "Rapid Support Forces (RSF)", "relation": "führt als Kommandeur"},
            {"source": "Sudanesische Armee (SAF)", "target": "Rapid Support Forces (RSF)", "relation": "bekämpft seit April 2023 im Bürgerkrieg"},
            {"source": "Demokratische Blockpartei", "target": "Abdel Fattah al-Burhan", "relation": "begrüßt dessen Dialogangebot"},
            {"source": "Abdel Fattah al-Burhan", "target": "Sudan", "relation": "regiert als Vorsitzender des Übergangssouveränitätsrats"},
        ],
        "sources": ["Al Jazeera – All", "Asharq Al-Awsat English"],
        "article_urls": [
            "https://www.aljazeera.com/news/2026/8/15/sudans-al-burhan-pledges-immunity-for-dialogue-rules-out-hemedti-return",
            "https://english.aawsat.com/arab-world/5307459-sudan%E2%80%99s-al-burhan-backs-inclusive-dialogue-pledges-continue-fighting-rsf",
            "https://sudantribune.com/article/317214",
        ],
        "countries_covered": ["Sudan"],
        "primary_sources": [
            {
                "title": "Offizielle Statements des sudanesischen Armeechefs zur Bedingung für Dialog und Frieden",
                "issuer": "SUNA, Sudan News Agency (staatliche Nachrichtenagentur)",
                "url": "https://suna-sd.net",
                "date": "2026-08-15",
                "note": "Offizieller Regierungskanal, verifiziert erreichbar; die konkrete Rede vom 15.08. war über automatisierten Abruf nicht einzeln als Dokument auffindbar.",
            },
            {
                "title": "Treffen einer AU-Delegation mit al-Burhan, Bekräftigung von Sudans Souveränität",
                "issuer": "African Union Peace and Security Council (über sudanesische Staatsmedien berichtet)",
                "url": "https://allafrica.com/stories/202608170084.html",
                "date": "2026-08-16",
                "note": "Keine direkt von der AU selbst gehostete Version des Statements gefunden, nur die staatsmedial verbreitete Zusammenfassung.",
            },
        ],
        "political_theory": {
            "theory": "Begrenzte Zugangsordnungen (Limited Access Orders) und neopatrimoniale Konfliktzyklen",
            "points": [
                "Nach North, Wallis und Weingast organisieren 'begrenzte Zugangsordnungen' politische Stabilität über die Verteilung von Renten und Privilegien an bewaffnete Machtgruppen statt über unpersönliche Institutionen, das erklärt, warum Machtkämpfe hier häufig in Gewalt statt in Wahlen ausgetragen werden.",
                "Der gemeinsame Putsch von SAF und RSF 2021 gegen die eigene zivile Übergangsregierung zeigt das Muster: Koalitionen bewaffneter Akteure halten nur so lange, wie die Verteilung von Macht und Ressourcen zwischen ihnen stimmt.",
                "Ein von der Militärführung selbst initiierter ziviler Dialog lässt sich in diesem Rahmen doppelt lesen: als echter Öffnungsversuch oder als Versuch, die eigene Zugangsordnung durch kontrollierte Einbindung ziviler Kräfte zu stabilisieren, ohne sie tatsächlich zu teilen.",
                "Die wiederholten Zyklen aus Aufstand, Übergang und Putsch seit 1956 legen nahe, dass die entscheidende Frage nicht ist, ob Dialog stattfindet, sondern ob er die zugrunde liegende Verteilung von Zwangsmitteln verändert.",
            ],
        },
        "market_correlation": {
            "has_correlation": False,
            "explanation": (
                "Es wurde geprüft, ob sich Sudans Bürgerkrieg oder die aktuelle "
                "Dialoginitiative im globalen Goldpreis, in Währungs- oder "
                "Anleihemärkten niederschlagen. Beim Goldpreis verläuft der "
                "recherchierbare Zusammenhang tatsächlich umgekehrt: Sudans "
                "Kriegsökonomie wird durch den ohnehin hohen globalen "
                "Goldpreis mitfinanziert, nicht umgekehrt. Ein liquide "
                "gehandelter sudanesischer Staatsanleihenmarkt existiert "
                "nicht mehr, der sudanesische Pfund verfällt strukturell seit "
                "Kriegsbeginn, aber ohne belegbaren Ausschlag speziell zur "
                "aktuellen Dialogankündigung."
            ),
            "series": [],
            "note": "",
        },
        "image_url": (
            "https://www.aljazeera.com/wp-content/uploads/2024/11/"
            "AFP__20241111__36M82QJ__v1__Preview__SaudiOicArabLeagueDiplomacyIsraelPalestinianLeb-1731481504.jpg"
            "?resize=1200%2C630"
        ),
    },
    # -----------------------------------------------------------------
    # STORY 4, Ukraine: Langstreckenschläge, US-Waffenlieferung über die Türkei
    # -----------------------------------------------------------------
    {
        "id": "ukraine-long-range-strikes-2026-08",
        "title": "Ukraine trifft mit Langstreckenraketen Ziele tief in Russland, Streit um US-Waffenlieferung über die Türkei",
        "one_line": (
            "Ukrainische [[Flamingo-Marschflugkörper]] treffen das russische "
            "Progress-Raumfahrtzentrum und den Luftwaffenstützpunkt "
            "Sawasleika, während Russland [[USA]] und [[Türkei]] wegen einer "
            "geplanten Waffenlieferung an die [[Ukraine]] mit Schäden an den "
            "bilateralen Beziehungen droht."
        ),
        "summary": [
            "Ukrainische [[Flamingo-Marschflugkörper]] treffen das [[Progress-Raumfahrtzentrum]] in der russischen Region Samara sowie den Luftwaffenstützpunkt Sawasleika, von dem aus Kinschal-Trägerjets starten.",
            "Russland reagiert in derselben Nacht mit einem Großangriff von 152 Drohnen auf ukrainische Städte.",
            "Parallel dazu protestiert Russland gegen eine über die [[Türkei]] laufende Lieferung von ATACMS-Raketen, M270-Systemen und Munition aus den [[USA]] an die [[Ukraine]].",
            "Russland droht mit Schäden an den bilateralen Beziehungen zu Washington und Ankara.",
            "Die Angriffe und der Waffenlieferungsstreit fallen zeitlich zusammen, sind aber unabhängige Entwicklungen.",
        ],
        "deep_dive": (
            "Diese Story verbindet zwei eigenständige Linien, die an diesem "
            "Tag zufällig zusammenfielen. Die eine ist die militärische "
            "Eskalationslogik des Krieges selbst, der seit der Annexion der "
            "Krim 2014 und dem Beginn des Kriegs im Donbass in mehreren "
            "Phasen verlief und seit der vollumfänglichen Invasion im "
            "Februar 2022 offen geführt wird: Ukrainische Angriffe reichen "
            "inzwischen mit im eigenen Land entwickelten "
            "Langstreckensystemen wie den [[Flamingo-Marschflugkörper]]n "
            "Hunderte Kilometer tief nach Russland hinein.\n\n"
            "Die andere Linie ist die politisch-diplomatische Geschichte "
            "westlicher Waffenlieferungen an die [[Ukraine]]: von anfänglich "
            "zurückhaltenden Lieferungen leichter Panzerabwehrwaffen 2022 "
            "über die Debatte um weitreichende Systeme wie ATACMS bis zur "
            "aktuellen, über die [[Türkei]] abgewickelten Lieferung, die "
            "zeigt, wie Drittstaaten inzwischen als Zwischenstationen für "
            "westliche Rüstungslieferungen dienen und damit selbst zur "
            "Zielscheibe russischer diplomatischer Proteste werden.\n\n"
            "Dass Russland am selben Tag sowohl mit einem der größten "
            "Drohnenangriffe der letzten Zeit reagierte als auch "
            "diplomatisch gegen die Türkei protestierte, zeigt zwei "
            "parallele Reaktionskanäle auf denselben grundlegenden Trend: "
            "die wachsende Reichweite und Substanz westlicher "
            "beziehungsweise ukrainischer Waffenfähigkeiten."
        ),
        "cui_bono": (
            "Für [[Ukraine]] demonstrieren die Treffer tief in Russland "
            "hinein die wachsende eigenständige Fähigkeit, unabhängig von "
            "der jeweils aktuellen Lieferbereitschaft westlicher Partner. "
            "Für Russland dient sowohl der Drohnengroßangriff als auch der "
            "diplomatische Protest gegen [[Türkei]] und [[USA]] dazu, den "
            "Preis weiterer westlicher Unterstützung sichtbar zu erhöhen, "
            "militärisch für die ukrainische Bevölkerung, diplomatisch für "
            "die beteiligten Drittstaaten. Für die [[Türkei]] wiederum ist "
            "ihre Rolle als Transitstaat für US-Waffenlieferungen eine "
            "Gelegenheit, sich als unverzichtbarer Vermittler und Partner "
            "beider Seiten zu positionieren, auch wenn das diplomatische "
            "Kosten mit Russland mit sich bringt."
        ),
        "historical_threads": [
            {
                "id": "russia-ukraine-invasion",
                "title": "Russlands Krieg gegen die Ukraine",
                "entries": [
                    {
                        "date": "2014-03",
                        "title": "Annexion der Krim",
                        "one_line": "Russland annektiert die ukrainische Halbinsel Krim nach einem international nicht anerkannten Referendum.",
                        "extended": None,
                    },
                    {
                        "date": "2014-04",
                        "title": "Beginn des Kriegs im Donbass",
                        "one_line": "Von Russland unterstützte Separatisten rufen abtrünnige Gebiete in der Ostukraine aus, ein jahrelanger, zunächst begrenzter Krieg beginnt.",
                        "extended": None,
                    },
                    {
                        "date": "2022-02",
                        "title": "Vollumfängliche Invasion",
                        "one_line": "Russland startet eine landesweite Invasion der Ukraine, der Krieg wird von einem begrenzten zu einem offenen, landesweiten Konflikt.",
                        "extended": None,
                    },
                    {
                        "date": "2023-2025",
                        "title": "Stellungskrieg und Zermürbung",
                        "one_line": "Der Krieg entwickelt sich zu einem langwierigen Abnutzungskrieg entlang weitgehend stabiler Frontlinien, mit wiederholten Luftangriffen auf beiden Seiten.",
                        "extended": None,
                    },
                    {
                        "date": "2026-08",
                        "title": "Ukrainische Langstreckenschläge tief in Russland",
                        "one_line": "Ukraine trifft mit selbst entwickelten Flamingo-Marschflugkörpern Ziele Hunderte Kilometer hinter der Front, während Russland mit einem Großangriff von 152 Drohnen antwortet.",
                        "extended": None,
                    },
                ],
            },
            {
                "id": "western-arms-supply",
                "title": "Westliche Waffenlieferungen und Russlands Reaktion",
                "entries": [
                    {
                        "date": "2022",
                        "title": "Erste westliche Waffenlieferungen",
                        "one_line": "Westliche Staaten liefern zunächst vor allem leichte Panzerabwehrwaffen und Flugabwehrsysteme, aus Sorge vor einer Eskalation mit Russland zunächst ohne weitreichende Systeme.",
                        "extended": None,
                    },
                    {
                        "date": "2023",
                        "title": "Debatte um weitreichende Systeme",
                        "one_line": "Die Diskussion um die Lieferung von Kampfpanzern und später weitreichenden Raketensystemen wie ATACMS nimmt zu, begleitet von wiederholten russischen Eskalationswarnungen.",
                        "extended": None,
                    },
                    {
                        "date": "2024",
                        "title": "Erlaubnis für Angriffe auf russisches Gebiet",
                        "one_line": "Mehrere westliche Partner erlauben der Ukraine erstmals den begrenzten Einsatz gelieferter Waffensysteme gegen Ziele auf russischem Staatsgebiet.",
                        "extended": None,
                    },
                    {
                        "date": "2026-08",
                        "title": "Über die Türkei abgewickelte US-Waffenlieferung",
                        "one_line": "Russland protestiert öffentlich gegen eine über die Türkei laufende Lieferung von ATACMS-Raketen, M270-Systemen und Munition aus den USA an die Ukraine und droht mit Schäden an den Beziehungen zu beiden Staaten.",
                        "extended": None,
                    },
                ],
            },
        ],
        "quotes": [
            {
                "text": "Our plan of long-range sanctions against Russia for this war is being implemented, and it is important that Russia's war potential be reduced.",
                "attribution": "Wolodymyr Selenskyj, Präsident der Ukraine",
                "context": "",
                "source_url": "https://kyivindependent.com/ukraine-reportedly-strikes-russian-military-airbase-behind-ballistic-missile-attacks-as-rockets-target-samara-oblast/",
            },
            {
                "text": "The progress center, which was involved, among other things in producing electronics, was hit. Flamingo missiles were used, a good achievement.",
                "attribution": "Wolodymyr Selenskyj, Präsident der Ukraine",
                "context": "Übersetzte Aussage, kleinere Grammatikkorrektur gegenüber der Originalwiedergabe.",
                "source_url": "https://kyivindependent.com/ukraine-reportedly-strikes-russian-military-airbase-behind-ballistic-missile-attacks-as-rockets-target-samara-oblast/",
            },
            {
                "text": "Attempts to use peace-promoting rhetoric while simultaneously supplying weapons to Ukraine inevitably erode mutual trust.",
                "attribution": "Maria Sacharowa, Sprecherin des russischen Außenministeriums",
                "context": "Reaktion auf eine über die Türkei laufende US-Waffenlieferung an die Ukraine.",
                "source_url": "https://kyivindependent.com/russia-threatens-serious-damage-to-relations-with-us-turkey-over-weapons-shipment-to-ukraine/",
            },
        ],
        "entities": [
            {
                "name": "Wolodymyr Selenskyj",
                "type": "person",
                "role_in_story": "Bestätigt die ukrainischen Treffer auf das Progress-Raumfahrtzentrum und den Stützpunkt Sawasleika.",
                "profile": "Präsident der Ukraine seit 2019, seit Februar 2022 zentrale Figur der ukrainischen Kriegsführung und internationalen Diplomatie.",
                "established": None,
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/9/9c/Volodymyr_Zelensky_Official_portrait.jpg",
            },
            {
                "name": "Progress-Raumfahrtzentrum",
                "type": "organization",
                "role_in_story": "Ziel des ukrainischen Angriffs, laut Selenskyj auch an der Produktion von Elektronik beteiligt.",
                "profile": "Russische Roscosmos-Einrichtung in der Region Samara, stellt regulär Trägerraketen her.",
                "established": None,
                "image_url": None,
            },
            {
                "name": "Flamingo-Marschflugkörper",
                "type": "concept",
                "role_in_story": "Von der Ukraine selbst entwickeltes Waffensystem, mit dem die Angriffe geflogen wurden.",
                "profile": "In der Ukraine entwickelter Marschflugkörper mit großer Reichweite, ermöglicht Angriffe tief im russischen Hinterland ohne Abhängigkeit von westlichen Lieferungen.",
                "established": None,
                "image_url": None,
            },
            {
                "name": "Maria Sacharowa",
                "type": "person",
                "role_in_story": "Protestiert namens des russischen Außenministeriums gegen die über die Türkei laufende Waffenlieferung.",
                "profile": "Sprecherin des russischen Außenministeriums, tritt regelmäßig als offizielle Stimme der russischen Außenpolitik auf.",
                "established": None,
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/f/f4/%D0%9C%D0%B0%D1%80%D0%B8%D1%8F_%D0%97%D0%B0%D1%85%D0%B0%D1%80%D0%BE%D0%B2%D0%B0_%2828-11-2024%29_%28cropped%29.jpg",
            },
            {
                "name": "Ukraine",
                "type": "country",
                "role_in_story": "Führt die Langstreckenangriffe aus und ist Empfänger der umstrittenen US-Waffenlieferung.",
                "profile": "Osteuropäisches Land, seit Februar 2022 im offenen Verteidigungskrieg gegen die russische Invasion.",
                "established": None,
                "image_url": FLAG_UKRAINE,
            },
            {
                "name": "USA",
                "type": "country",
                "role_in_story": "Liefert die Waffensysteme, gegen deren Weitergabe über die Türkei Russland protestiert.",
                "profile": "Größter westlicher Einzellieferant militärischer Unterstützung an die Ukraine seit 2022.",
                "established": None,
                "image_url": FLAG_USA,
            },
            {
                "name": "Türkei",
                "type": "country",
                "role_in_story": "Dient als Transitstaat für die US-Waffenlieferung an die Ukraine und gerät dadurch selbst ins Visier russischer Kritik.",
                "profile": "Nato-Mitglied mit eigenständiger Vermittlerrolle im Ukraine-Krieg, unterhält gleichzeitig Beziehungen zu Russland und der Ukraine.",
                "established": None,
                "image_url": FLAG_TURKEY,
            },
        ],
        "connections": [
            {"source": "Wolodymyr Selenskyj", "target": "Progress-Raumfahrtzentrum", "relation": "bestätigt Treffer auf"},
            {"source": "Flamingo-Marschflugkörper", "target": "Progress-Raumfahrtzentrum", "relation": "wird laut Selenskyj für den Angriff auf eingesetzt"},
            {"source": "Maria Sacharowa", "target": "Türkei", "relation": "protestiert gegen deren Rolle bei einer US-Waffenlieferung an die Ukraine"},
            {"source": "USA", "target": "Ukraine", "relation": "liefert über die Türkei Raketensysteme und Munition an"},
            {"source": "Ukraine", "target": "Progress-Raumfahrtzentrum", "relation": "greift mit Langstreckenwaffen an"},
        ],
        "sources": ["Al Jazeera – All", "Euronews", "Kyiv Independent"],
        "article_urls": [
            "https://kyivindependent.com/ukraine-reportedly-strikes-russian-military-airbase-behind-ballistic-missile-attacks-as-rockets-target-samara-oblast/",
            "https://www.euronews.com/my-europe/2026/08/15/ukraine-says-it-has-struck-russian-rocket-and-space-centre",
            "https://www.aljazeera.com/news/2026/8/15/ukraine-hits-russian-starlink-style-network-moscow-tracks-arms-package",
            "https://kyivindependent.com/russia-threatens-serious-damage-to-relations-with-us-turkey-over-weapons-shipment-to-ukraine/",
        ],
        "countries_covered": ["Ukraine", "Russland", "USA", "Türkei"],
        "primary_sources": [],
        "political_theory": {
            "theory": "Eskalationsdominanz und Signalisierungstheorie",
            "points": [
                "Beide Seiten setzen in dieser Episode auf Signale, die mehr zeigen sollen als militärische Wirkung: die ukrainischen Schläge demonstrieren eigenständige Reichweite unabhängig von westlicher Lieferbereitschaft, der russische Großangriff und der diplomatische Protest demonstrieren Handlungsfähigkeit auf zwei Ebenen gleichzeitig.",
                "Der Begriff der Eskalationsdominanz beschreibt den Versuch, auf jeder Eskalationsstufe die überlegene Antwortoption zu behalten, hier sichtbar daran, dass Russland sowohl militärisch mit einem Drohnenangriff als auch diplomatisch mit einem Protest gegen Drittstaaten gleichzeitig reagiert.",
                "Dass Russland die Türkei als Transitstaat diplomatisch adressiert statt nur die USA, zeigt eine klassische Drittstaaten-Strategie: Kosten für die Unterstützung einer Kriegspartei nicht nur bei der Kriegspartei selbst, sondern auch bei ihren Vermittlern zu erzeugen.",
                "Langstreckenfähigkeiten wie die Flamingo-Marschflugkörper verschieben die Signalisierungslogik: Abschreckung hängt zunehmend weniger ausschließlich von der Lieferbereitschaft externer Partner ab.",
            ],
        },
        "market_correlation": {
            "has_correlation": False,
            "explanation": (
                "Es wurde geprüft, ob sich die Schläge auf das "
                "Progress-Raumfahrtzentrum und Sawasleika oder die "
                "ATACMS/M270-Lieferung in Ölpreisen, Rüstungsaktien oder dem "
                "russischen Rubel/MOEX-Index niederschlagen. Für diese "
                "beiden konkreten Ereignisse wurde keine belegbare "
                "Marktreaktion gefunden. Die im gleichen Zeitraum gemeldeten "
                "Bewegungen bei Öl, Rubel und Rüstungsaktien werden in der "
                "verfügbaren Berichterstattung auf andere Ursachen "
                "zurückgeführt (russische Raffinerie-Angriffe, ein "
                "Diesel-Exportstopp, allgemeine Rüstungshaushalts- und "
                "Friedensverhandlungs-Schlagzeilen), nicht auf diese Episode."
            ),
            "series": [],
            "note": "",
        },
        "image_url": "https://www.aljazeera.com/wp-content/uploads/2026/08/afp_6a8076e0b081-1786803936.jpg?resize=1920%2C1440",
    },
]

if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "data" / "stories.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(STORIES, indent=2, ensure_ascii=False))
    print(f"Wrote {len(STORIES)} example stories -> {out}")
