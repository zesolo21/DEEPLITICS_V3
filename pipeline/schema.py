"""
Datenmodelle für Deeplitics, Version 5.

Kernänderung gegenüber v2: Eine Story hat nicht mehr EINE historische
Linie, sondern MEHRERE, unabhängige (`historical_threads`). Der Gedanke:
eine Meldung ist fast nie das Ergebnis nur EINER Vorgeschichte, sondern der
Konvergenzpunkt mehrerer unabhängiger Entwicklungslinien. Beispiel: eine
Meldung über widerrufene Afghanistan-Visa in den USA ist gleichzeitig der
jüngste Punkt (a) der Geschichte Afghanistans unter den Taliban UND (b) der
Geschichte der US-Einwanderungspolitik gegenüber Kriegsverbündeten, zwei
komplett unabhängige Linien, die zufällig in derselben Meldung
zusammenlaufen.

Version 4 ergänzte: `Quote` (echte, belegbare Zitate je Story) und
`Story.image_url` (ein Hero-Bild je Story, aus dem og:image der
Hauptquelle, siehe `pipeline/extract_article.py::extract_og_image`).

Version 5 ergänzt, auf ausdrücklichen Nutzerwunsch:

- `Story.summary` ist jetzt eine BULLET-LISTE (`list[str]`) statt eines
  Fließtext-Absatzes: die Meldung selbst soll knapp und scanbar sein, der
  Fließtext bleibt dem `deep_dive` vorbehalten.
- `PrimarySource` + `Story.primary_sources`: echte Primärquellen
  (Regierungsdokumente, offizielle Statements, Gerichtsentscheidungen),
  zusätzlich zu den journalistischen `article_urls`. Der Gedanke: Medien
  berichten meist ÜBER Primärquellen, Deeplitics soll wo möglich direkt
  dorthin verweisen.
- `PoliticalTheoryNote` + `Story.political_theory`: ein optionaler,
  bewusst vom Hauptinhalt getrennter Hintergrund, der die Story durch die
  Linse eines politikwissenschaftlichen Konzepts einordnet. Wird im
  Frontend hinter einem Button versteckt, nicht standardmäßig angezeigt,
  jede Story ist keine Vorlesung.
- `MarketSeries`/`MarketCorrelation` + `Story.market_correlation`: eine
  EHRLICHE Prüfung, ob sich ein Ereignis in Finanzmärkten (Aktien,
  Rohstoffe, Indizes) niedergeschlagen hat. `has_correlation=False` ist ein
  vollwertiges, erwartetes Ergebnis, keine erzwungene Korrelation. Wenn
  `has_correlation=True`, referenzieren `series` echte, recherchierte
  Kursbewegungen (siehe `note` für Genauigkeits-/Näherungshinweise).

Jeder Thread wird "vertikal" gelesen (chronologisch, Meilenstein für
Meilenstein bis "heute"). "Horizontal" (im UI: als Tabs) wählt man
zwischen den verschiedenen Threads, die alle in derselben Story enden.

Jeder Meilenstein ist ein Schlaglicht (`one_line`) UND extendable: ein
optionales `extended`-Feld für alle, die tiefer gehen wollen.

STILREGEL (gilt für summary/deep_dive/cui_bono, s. auch
`synthesize_story.py`): Der Text soll die Einzelartikel zu EINEM
synthetischen Verständnis verschmelzen, nicht als Mosaik aus
Einzelzitaten/Personen-Attributionen ("X sagte laut Artikel Y...")
geschrieben sein. Konkrete, wörtliche Aussagen gehören ausschließlich in
`quotes`, nicht in die Fließtext-/Bullet-Felder.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class Article:
    source: str
    country: str
    title: str
    url: str
    published: str | None  # ISO 8601 string, falls bekannt
    text: str  # extrahierter Volltext (oder Summary als Fallback)
    fetched_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Entity:
    name: str
    type: str  # "person" | "organization" | "country" | "concept" | "event"
    role_in_story: str = ""
    # 2-4 Sätze strategisches Profil: wer/was ist das, welche Interessen/
    # welches Muster verfolgt diese Entität typischerweise.
    profile: str = ""
    established: str | None = None  # Gründungs-/Bau-/Geburtsdatum, falls zutreffend
    # Bevorzugt eine echte, frei lizenzierte Bild-URL (z.B. Wikimedia
    # Commons). Der Browser des Nutzers lädt das Bild direkt, nicht
    # dieser Pipeline-Code. Null = Platzhalter im Frontend.
    image_url: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Connection:
    """Eine Kante: verbindet zwei Entitäten oder zwei Storys."""
    source: str
    target: str
    relation: str


@dataclass
class ThreadEntry:
    """Ein Meilenstein innerhalb EINER historischen Linie."""
    date: str  # grobe Zeitangabe reicht, z.B. "1979", "1996", "2022-08"
    title: str
    one_line: str  # das Schlaglicht, immer sichtbar
    extended: str | None = None  # optionale Vertiefung, erst nach Klick sichtbar


@dataclass
class HistoricalThread:
    """EINE unabhängige historische Linie, die (unter anderen) in dieser
    Story mündet. Eine Story hat i.d.R. 2-5 davon, nie erfunden, nur wenn
    tatsächlich eine eigenständige, klar unterscheidbare Entwicklungslinie
    vorliegt."""
    id: str
    title: str  # kurzer Label für den Tab, z.B. "USA-Iran-Konflikt"
    entries: list[ThreadEntry]


@dataclass
class Quote:
    """Ein wörtliches Zitat aus einem der Quellartikel: ein wichtiger
    O-Ton einer beteiligten Person ODER eine besonders treffende
    Einordnung eines Journalisten/einer Journalistin. Muss ein ECHTES,
    belegbares Zitat aus einem der `article_urls` sein, nie erfunden oder
    paraphrasiert. Das ist bewusst der EINZIGE Ort, an dem eine konkrete
    Person/Aussage im Vordergrund steht, siehe Stilregel oben."""
    text: str
    attribution: str  # z.B. "Senator Ruben Gallego" oder "NPR"
    context: str = ""  # optionaler 1-Satz-Kontext, wer/was das ist
    source_url: str = ""


@dataclass
class PrimarySource:
    """Eine echte Primärquelle: Regierungsdokument, offizielles Statement,
    Gerichtsentscheidung, Pressemitteilung einer Behörde/Institution -
    keine journalistische Berichterstattung DARÜBER (die gehört in
    `Story.article_urls`/`sources`). Der Gedanke: Medien berichten meist
    ÜBER Primärquellen, Deeplitics soll wo auffindbar direkt dorthin
    verweisen, weil das ist, worauf sich alle Zweitquellen beziehen."""
    title: str  # z.B. "Blumenthal-Brief an Verteidigungsminister Hegseth"
    issuer: str  # z.B. "Büro von Senator Richard Blumenthal" oder "U.S. Federal Register"
    url: str
    date: str | None = None
    note: str = ""  # optionaler 1-Satz-Hinweis, z.B. bei eingeschränkter Zugänglichkeit


@dataclass
class PoliticalTheoryNote:
    """Ordnet die Story durch die Linse EINES politikwissenschaftlichen
    Konzepts ein. Bewusst kurz und als Bullet-Points, kein Essay. Im
    Frontend hinter einem eigenen Button versteckt, nicht Teil der
    Standardansicht."""
    theory: str  # kurzer Name des Konzepts, z.B. "Prinzipal-Agent-Theorie (zivil-militärische Aufsicht)"
    points: list[str]  # 3-5 Bullet-Points, die die Story an das Konzept anschließen


@dataclass
class MarketDataPoint:
    date: str
    value: float  # indexierter Wert (Basis 100 = erster Punkt), nicht der Rohkurs


@dataclass
class MarketSeries:
    label: str  # z.B. "Brent Crude Oil"
    raw_unit: str  # z.B. "USD/Barrel", für die Erklärung, was der Index abbildet
    points: list[MarketDataPoint]
    source_url: str = ""


@dataclass
class MarketCorrelation:
    """Ehrliche Prüfung: gibt es eine recherchierbare Marktreaktion auf
    dieses Ereignis? `has_correlation=False` ist ein vollwertiges Ergebnis,
    KEINE Korrelation zu erzwingen ist Teil der Formel, nicht ein Fehler."""
    has_correlation: bool
    explanation: str  # 2-4 Sätze, was der Zusammenhang ist (oder warum keiner gefunden wurde)
    series: list[MarketSeries] = field(default_factory=list)
    note: str = ""  # z.B. Hinweise zu Näherungen/Indexierung


@dataclass
class Story:
    id: str
    title: str
    one_line: str
    summary: list[str]  # Bullet-Points, nutzt [[Entity]]-Inline-Referenzen je Punkt
    deep_dive: str  # Fließtext, nutzt [[Entity]]-Inline-Referenzen
    cui_bono: str  # quellenübergreifende "wem nützt das?"-Analyse
    historical_threads: list[HistoricalThread]
    quotes: list[Quote]
    entities: list[Entity]
    connections: list[Connection]
    sources: list[str]
    article_urls: list[str]
    countries_covered: list[str]
    primary_sources: list[PrimarySource] = field(default_factory=list)
    political_theory: PoliticalTheoryNote | None = None
    market_correlation: MarketCorrelation | None = None
    # Bevorzugt das og:image der Haupt-Quelle (das Vorschaubild, das die
    # Publikation selbst für Social-Media-Vorschauen hinterlegt hat), frei
    # verfügbar, kein Wikimedia-Suchaufwand pro Story nötig.
    image_url: str | None = None
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)
