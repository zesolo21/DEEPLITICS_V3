"""
FESTE TEST-ARTIKELMENGE (Bauanleitung Abschnitt 1 + 7: "zum Start reichen
... eine feste Test-Datenmenge", "ein einziger fest hinterlegter Nutzer,
kein Login-System, damit die inhaltliche Logik zuerst ueberpruefbar ist").

WICHTIG, ehrlich offengelegt: Diese Artikel sind SYNTHETISCH / FIKTIV,
von mir fuer diese Sitzung erfunden, um die Pipeline-Logik (Clustering,
Extraktion, Tagging, Scoring, Feeds) ohne echten RSS-Zugriff end-to-end
testen zu koennen. Sie sind KEINE echten Presseartikel und sollen auch
nicht als solche missverstanden werden. Quellen-Namen sind reale deutsche
Medienmarken (fuer realistische Bias-/Perspektiven-Vielfalt), die
ZITIERTEN INHALTE sind aber erfunden.

Absichtlich enthalten:
- 6 thematisch klar unterscheidbare Themenstraenge (fuer Clustering-Tests)
- Mehrere unabhaengige Quellen pro Strang (fuer den Quellen-Zahl-Score)
- Ein Meinungsstueck (fuer das Fakt/Meinung-Flag)
- Je ein Artikel mit gesetztem source_dissenting=True pro relevantem
  Strang (fuer den Perspektivenbreite-Regler)
- Ein einzelner Singleton-Strang mit nur einer Quelle (fuer den unteren
  Rand des Wichtigkeits-Scores)
"""

from __future__ import annotations

from pipeline.models import Article

ARTICLES: list[Article] = [
    # ---- Strang 1: EU-Asylreform / GEAS (Topic: migration) ----
    Article(
        id="a01", source="Tagesschau",
        url="https://example-tagesschau.test/geas-vorschlag",
        title="EU-Kommission schlägt beschleunigte Grenzverfahren für Asylanträge vor",
        text=(
            "Die EU-Kommission hat einen Gesetzesvorschlag vorgelegt, der schnellere "
            "Grenzverfahren für Asylanträge aus Ländern mit niedriger Anerkennungsquote "
            "vorsieht. Antragstellende sollen künftig innerhalb von zwölf Wochen an den "
            "Außengrenzen der EU bearbeitet werden, statt wie bisher ins Landesinnere "
            "weiterzureisen. Migrationskommissarin Ylva Berg sagte, das Ziel sei ein "
            "gerechteres und schnelleres System für alle Mitgliedstaaten. Die Bundesregierung "
            "begrüßte den Vorschlag grundsätzlich, mahnte aber ausreichende "
            "Rechtsschutzgarantien an. Menschenrechtsorganisationen kritisierten das "
            "Verfahren als zu kurz für eine sorgfältige Einzelfallprüfung."
        ),
        published_at="2026-08-15", source_dissenting=False,
    ),
    Article(
        id="a02", source="Süddeutsche Zeitung",
        url="https://example-sz.test/asylreform-laender-reaktionen",
        title="Asylreform: Mitgliedstaaten uneins über Grenzverfahren",
        text=(
            "Nach dem Vorschlag der EU-Kommission zu beschleunigten Grenzverfahren für "
            "Asylanträge zeichnet sich unter den Mitgliedstaaten keine einheitliche Linie "
            "ab. Italien und Griechenland begrüßten die Pläne als Entlastung für "
            "Ankunftsländer, Polen und Ungarn lehnen jede zusätzliche Verpflichtung ab. "
            "Deutschland fordert Nachbesserungen beim Rechtsschutz für Antragstellende. "
            "Das Europaparlament will den Vorschlag im September beraten, eine Einigung "
            "gilt als frühestens für 2027 realistisch. Beobachter verweisen darauf, dass "
            "frühere Reformversuche des Gemeinsamen Europäischen Asylsystems (GEAS) "
            "wiederholt an genau diesen Verteilungsfragen gescheitert waren."
        ),
        published_at="2026-08-16", source_dissenting=False,
    ),
    Article(
        id="a03", source="Junge Freiheit",
        url="https://example-jf.test/asylreform-kommentar",
        title="Asylreform light: Warum die EU-Pläne zu kurz greifen",
        text=(
            "Der Vorschlag der EU-Kommission zu beschleunigten Grenzverfahren wird von "
            "manchen als Durchbruch gefeiert, greift aus Sicht von Kritikern aber deutlich "
            "zu kurz. Zwölf Wochen Bearbeitungszeit an der Grenze änderten nichts an der "
            "grundsätzlichen Anreizstruktur, so ein Sprecher mehrerer osteuropäischer "
            "Regierungen. Auch die Zahl faktisch durchgesetzter Rückführungen bleibe von "
            "der Reform unberührt. Die eigentliche Kontroverse werde erst im "
            "Europaparlament im Herbst offen ausgetragen."
        ),
        published_at="2026-08-17", source_dissenting=True,
    ),

    # ---- Strang 2: Bundeshaushalt / Schuldenbremse (Topic: wirtschaft) ----
    Article(
        id="a04", source="Handelsblatt",
        url="https://example-hb.test/haushalt-schuldenbremse",
        title="Kabinett beschließt Aussetzung der Schuldenbremse für Verteidigungsausgaben",
        text=(
            "Das Bundeskabinett hat am Mittwoch die teilweise Aussetzung der "
            "Schuldenbremse für zusätzliche Verteidigungsausgaben beschlossen. Damit "
            "sollen bis 2029 rund 45 Milliarden Euro zusätzlich für die Bundeswehr "
            "bereitgestellt werden können, ohne den regulären Bundeshaushalt zu belasten. "
            "Finanzminister Jonas Reuter sprach von einer 'verantwortungsvollen Reaktion "
            "auf eine veränderte Sicherheitslage'. Die Opposition kritisierte fehlende "
            "Gegenfinanzierung, die Koalitionsfraktionen verteidigten den Schritt als "
            "notwendig und verfassungsrechtlich gedeckt."
        ),
        published_at="2026-08-14", source_dissenting=False,
    ),
    Article(
        id="a05", source="taz",
        url="https://example-taz.test/schuldenbremse-kritik",
        title="Sozialverbände warnen vor Verteilungskonflikt im Haushalt",
        text=(
            "Nach dem Kabinettsbeschluss zur teilweisen Aussetzung der Schuldenbremse für "
            "Verteidigungsausgaben warnen Sozialverbände vor einem Verteilungskonflikt. "
            "Der Paritätische Wohlfahrtsverband forderte, vergleichbare Ausnahmen auch für "
            "Investitionen in Bildung und sozialen Wohnungsbau zu prüfen. Aus der "
            "Koalition hieß es, eine Ausweitung auf weitere Bereiche werde derzeit nicht "
            "erwogen, das laufende Haushaltsverfahren solle nicht weiter verzögert werden."
        ),
        published_at="2026-08-15", source_dissenting=False,
    ),
    Article(
        id="a06", source="Bild",
        url="https://example-bild.test/haushalt-buerger-reaktionen",
        title="45 Milliarden für die Bundeswehr: Was bedeutet das für die Bürger?",
        text=(
            "Nach dem Kabinettsbeschluss zu zusätzlichen Verteidigungsausgaben von rund "
            "45 Milliarden Euro bis 2029 fragen sich viele Bürgerinnen und Bürger, was "
            "die Entscheidung konkret bedeutet. Steuererhöhungen seien laut Finanz-"
            "ministerium nicht geplant, die Mittel würden über neue Schulden "
            "finanziert. Wirtschaftsverbände begrüßten die Investitionen in die "
            "Rüstungsindustrie, Verbraucherschützer verwiesen auf die langfristige "
            "Zinslast für kommende Haushalte."
        ),
        published_at="2026-08-18", source_dissenting=False,
    ),

    # ---- Strang 3: Vorgezogener Kohleausstieg (Topic: klima) ----
    Article(
        id="a07", source="Der Spiegel",
        url="https://example-spiegel.test/kohleausstieg-vorgezogen",
        title="Zwei Bundesländer ziehen Kohleausstieg auf 2030 vor",
        text=(
            "Nordrhein-Westfalen und Brandenburg haben angekündigt, den Ausstieg aus der "
            "Kohleverstromung in ihren Bundesländern auf das Jahr 2030 vorzuziehen, fünf "
            "Jahre früher als im bisherigen Bundesgesetz vorgesehen. Das "
            "Bundeswirtschaftsministerium erklärte, man unterstütze den Schritt und "
            "prüfe zusätzliche Strukturhilfen für betroffene Regionen. Gewerkschaften "
            "warnten vor Arbeitsplatzverlusten, sollten die Hilfen nicht rechtzeitig "
            "fließen. Umweltverbände begrüßten die Ankündigung als überfälliges Signal."
        ),
        published_at="2026-08-16", source_dissenting=False,
    ),
    Article(
        id="a08", source="Welt",
        url="https://example-welt.test/kohleausstieg-kommentar",
        title="Kommentar: Der vorgezogene Kohleausstieg ist ein teures Symbol",
        text=(
            "Meinung: Der von Nordrhein-Westfalen und Brandenburg angekündigte vorgezogene "
            "Kohleausstieg klingt gut, löst aber das eigentliche Problem nicht. Ohne "
            "verlässliche Netzkapazitäten und ausreichend Speicherkapazität drohen in "
            "sonnen- und windarmen Wochen Versorgungsengpässe. Bevor Bundesländer mit "
            "vorgezogenen Zieldaten um die Wette symbolpolitisieren, sollte zuerst der "
            "Netzausbau Priorität bekommen. Alles andere ist Ankündigungspolitik auf "
            "Kosten der Versorgungssicherheit."
        ),
        published_at="2026-08-17", source_dissenting=False,
    ),

    # ---- Strang 4: NATO-Gipfel Verteidigungsausgaben (Topic: sicherheit) ----
    Article(
        id="a09", source="Deutsche Welle",
        url="https://example-dw.test/nato-gipfel-ziel",
        title="NATO-Gipfel beschließt neues 3,5-Prozent-Ausgabenziel",
        text=(
            "Die NATO-Mitgliedstaaten haben sich auf ein neues Ausgabenziel von 3,5 "
            "Prozent des Bruttoinlandsprodukts für Kernverteidigung geeinigt, zusätzlich "
            "zu 1,5 Prozent für breiter gefasste sicherheitsrelevante Infrastruktur. "
            "NATO-Generalsekretär Lars Eriksen sprach von der 'größten "
            "Verteidigungsanpassung seit dem Kalten Krieg'. Deutschland sagte zu, das "
            "neue Ziel bis 2032 zu erreichen. Mehrere südeuropäische Mitgliedstaaten "
            "äußerten Vorbehalte wegen ihrer angespannten Haushaltslage."
        ),
        published_at="2026-08-14", source_dissenting=False,
    ),
    Article(
        id="a10", source="Frankfurter Allgemeine",
        url="https://example-faz.test/nato-ziel-deutschland",
        title="Was das neue NATO-Ziel für den deutschen Haushalt bedeutet",
        text=(
            "Nach der Einigung der NATO-Staaten auf ein neues Ausgabenziel von 3,5 "
            "Prozent des BIP für Kernverteidigung rechnen Haushaltsexperten mit "
            "erheblichem zusätzlichem Finanzierungsbedarf für Deutschland. Bis 2032 "
            "müssten die Verteidigungsausgaben nach aktuellen Schätzungen um weitere "
            "60 bis 80 Milliarden Euro jährlich steigen. Das Verteidigungsministerium "
            "verwies auf die bereits beschlossene Aussetzung der Schuldenbremse für "
            "Verteidigungsausgaben als ersten Schritt zur Gegenfinanzierung."
        ),
        published_at="2026-08-15", source_dissenting=False,
    ),
    Article(
        id="a11", source="Compact",
        url="https://example-compact.test/nato-ziel-kritik",
        title="3,5 Prozent: Wer bezahlt am Ende die Aufrüstungsspirale?",
        text=(
            "Während die NATO ihr neues Ausgabenziel von 3,5 Prozent des "
            "Bruttoinlandsprodukts als historischen Erfolg feiert, wächst die Kritik an "
            "der langfristigen Tragfähigkeit dieser Zusage. Kritiker sprechen von einer "
            "Aufrüstungsspirale ohne erkennbares Ende und verweisen auf ausbleibende "
            "gleichzeitige Zusagen für Rüstungskontrolle oder diplomatische Initiativen. "
            "Die Bundesregierung weist solche Vergleiche zurück und betont die "
            "veränderte Sicherheitslage in Europa."
        ),
        published_at="2026-08-16", source_dissenting=True,
    ),

    # ---- Strang 5: Digitalpakt Schule 2.0 / Lehrermangel (Topic: bildung) ----
    Article(
        id="a12", source="Zeit Online",
        url="https://example-zeit.test/digitalpakt-schule-2",
        title="Kultusministerkonferenz beschließt Digitalpakt Schule 2.0",
        text=(
            "Die Kultusministerkonferenz hat den Digitalpakt Schule 2.0 beschlossen, mit "
            "dem Bund und Länder in den kommenden fünf Jahren rund 6 Milliarden Euro in "
            "digitale Infrastruktur und Lehrkräftefortbildung investieren wollen. Ein "
            "eigener Schwerpunkt liegt auf IT-Support an Schulen, der bislang häufig "
            "ehrenamtlich von Lehrkräften übernommen wurde. Der Lehrerverband begrüßte "
            "den Beschluss, mahnte aber an, dass Investitionen in Technik den akuten "
            "Personalmangel an Schulen nicht ersetzen könnten."
        ),
        published_at="2026-08-17", source_dissenting=False,
    ),
    Article(
        id="a13", source="Bayerischer Rundfunk",
        url="https://example-br.test/lehrermangel-digitalpakt-reaktion",
        title="Lehrerverbände: Digitalpakt löst Personalmangel nicht",
        text=(
            "Nach dem Beschluss zum Digitalpakt Schule 2.0 fordern Lehrerverbände "
            "zusätzliche Maßnahmen gegen den akuten Lehrermangel. Bundesweit fehlen "
            "nach aktuellen Schätzungen rund 35.000 Lehrkräfte, besonders an "
            "Grundschulen und in strukturschwachen Regionen. Die Kultusministerkonferenz "
            "verwies auf parallel laufende Programme zur Gewinnung von Quereinsteigenden, "
            "räumte aber ein, dass kurzfristige Entlastung kaum zu erwarten sei."
        ),
        published_at="2026-08-18", source_dissenting=False,
    ),

    # ---- Strang 6: Ständiger Bürgerrat / Demokratiereform (Topic: demokratie) ----
    Article(
        id="a14", source="Deutschlandfunk",
        url="https://example-dlf.test/buergerrat-demokratiereform",
        title="Bundesregierung richtet ständigen Bürgerrat ein",
        text=(
            "Die Bundesregierung hat die Einrichtung eines ständigen Bürgerrats "
            "beschlossen, der künftig regelmäßig Empfehlungen zu Demokratie- und "
            "Wahlrechtsfragen erarbeiten soll. Die 160 Mitglieder werden per Losverfahren "
            "aus der Bevölkerung ausgewählt. Kritiker bezweifeln, dass die "
            "Empfehlungen eines beratenden Gremiums tatsächlich politisches Gewicht "
            "entfalten werden, Befürworter sehen darin einen wichtigen Baustein gegen "
            "wachsende Politikverdrossenheit."
        ),
        published_at="2026-08-13", source_dissenting=False,
    ),
    Article(
        id="a15", source="Tagesspiegel",
        url="https://example-tsp.test/buergerrat-erste-themen",
        title="Bürgerrat nimmt Arbeit zu Wahlrecht und Parteienfinanzierung auf",
        text=(
            "Der neu eingerichtete ständige Bürgerrat hat mit seiner Arbeit begonnen und "
            "sich zunächst auf zwei Themenfelder verständigt: eine mögliche "
            "Wahlrechtsreform sowie mehr Transparenz bei der Parteienfinanzierung. Erste "
            "Empfehlungen werden für Frühjahr 2027 erwartet. Verfassungsrechtler weisen "
            "darauf hin, dass die Empfehlungen rechtlich unverbindlich bleiben und der "
            "Bundestag am Ende frei über eine Umsetzung entscheidet."
        ),
        published_at="2026-08-18", source_dissenting=False,
    ),

    # ---- Singleton: einzelner Artikel ohne weitere Quelle (Topic: digitales) ----
    # Bewusst als Einzelfall gehalten, um den unteren Rand des
    # Wichtigkeits-Scores zu testen (wenige Quellen, keine offizielle
    # Handlung, keine belegte grosse Betroffenenzahl).
    Article(
        id="a16", source="Netzpolitik.org",
        url="https://example-netzpolitik.test/ki-gesetz-evaluierung",
        title="Erster Evaluierungsbericht zum KI-Gesetz vorgelegt",
        text=(
            "Ein Jahr nach Inkrafttreten des nationalen KI-Gesetzes hat eine "
            "unabhängige Kommission einen ersten Evaluierungsbericht vorgelegt. Der "
            "Bericht attestiert der Behördenpraxis uneinheitliche Auslegung bei "
            "Hochrisiko-Anwendungen, spricht aber noch keine konkreten "
            "Reformempfehlungen aus. Ein Sprecher des Digitalministeriums kündigte an, "
            "den Bericht 'sorgfältig zu prüfen', ohne einen Zeitplan für mögliche "
            "Anpassungen zu nennen."
        ),
        published_at="2026-08-12", source_dissenting=False,
    ),
]


def get_test_articles() -> list[Article]:
    """Frische Kopien zurueckgeben, damit Tests sich nicht gegenseitig
    ueber gemeinsam referenzierte Objekte beeinflussen."""
    import copy

    return copy.deepcopy(ARTICLES)
