"""
Kuratierte Liste englischsprachiger Nachrichtenquellen.

Jetzt ~32 Outlets (vorher 22): größerer Pool für robusteres
Multi-Source-Clustering UND bewusst über das politische Spektrum gestreut
(inspiriert von Aggregatoren wie Particle/AllSides, die pro Story mehrere
politische Perspektiven zeigen) — damit eine Story nicht nur "von vielen
Quellen bestätigt", sondern auch "aus verschiedenen politischen
Blickwinkeln berichtet" markiert werden kann.

`bias` ist eine GROBE, WEIT VERBREITETE Kategorisierung (Kategorien wie bei
AllSides Media Bias Ratings: left / lean-left / center / lean-right /
right) — KEINE eigene redaktionelle Bewertung von Deeplitics, sondern eine
Näherung basierend auf allgemein bekannten, oft zitierten Einordnungen.
Für ein echtes Produkt sollte das durch einen gepflegten, belegten Datensatz
ersetzt werden (z.B. eine lizenzierte AllSides/Ad-Fontes-Anbindung), nicht
durch diese handkuratierte Liste.

WICHTIG: Nicht alle Feed-URLs sind in dieser Sandbox getestet (siehe
docs/NETWORK_NOTES.md) — bekannt funktionierend: BBC, NPR, Al Jazeera.
`fetch_feeds.py` überspringt kaputte/tote Feeds automatisch.
"""

from dataclasses import dataclass

BIAS_LABELS = {
    "left": "Left",
    "lean-left": "Lean Left",
    "center": "Center",
    "lean-right": "Lean Right",
    "right": "Right",
}


@dataclass(frozen=True)
class Source:
    name: str
    country: str
    feed_url: str
    bias: str = "center"  # left | lean-left | center | lean-right | right
    lang: str = "en"


SOURCES: list[Source] = [
    # --- Center / Nachrichtenagenturen ---
    Source("Reuters – World", "US/UK", "https://www.reuters.com/world/rss", "center"),
    Source("AP News – Top Stories", "US", "https://apnews.com/apf-topnews?format=rss", "center"),
    Source("BBC News – World", "UK", "https://feeds.bbci.co.uk/news/world/rss.xml", "center"),
    Source("BBC News – Politics", "UK", "https://feeds.bbci.co.uk/news/politics/rss.xml", "center"),
    Source("Axios", "US", "https://api.axios.com/feed/", "center"),
    Source("The Hill", "US", "https://thehill.com/feed/", "center"),
    Source("Deutsche Welle – World (EN)", "DE", "https://rss.dw.com/rdf/rss-en-world", "center"),
    Source("France24 – World (EN)", "FR", "https://www.france24.com/en/rss", "center"),
    Source("USA Today – World", "US", "https://rssfeeds.usatoday.com/usatoday-newstopstories", "center"),
    Source("Bloomberg – Politics", "US", "https://feeds.bloomberg.com/politics/news.rss", "center"),
    Source("Foreign Policy", "US", "https://foreignpolicy.com/feed/", "center"),
    # --- Lean Left / Left ---
    Source("NPR – World", "US", "https://feeds.npr.org/1004/rss.xml", "lean-left"),
    Source("NPR – Politics", "US", "https://feeds.npr.org/1014/rss.xml", "lean-left"),
    Source("The Guardian – World", "UK", "https://www.theguardian.com/world/rss", "lean-left"),
    Source("The Guardian – Politics", "UK", "https://www.theguardian.com/politics/rss", "lean-left"),
    Source("CNN – World", "US", "http://rss.cnn.com/rss/cnn_world.rss", "lean-left"),
    Source("The New York Times – World", "US", "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "lean-left"),
    Source("The Washington Post – Politics", "US", "https://feeds.washingtonpost.com/rss/politics", "lean-left"),
    Source("The Atlantic", "US", "https://www.theatlantic.com/feed/all/", "lean-left"),
    Source("Vox", "US", "https://www.vox.com/rss/index.xml", "left"),
    Source("MSNBC", "US", "https://feeds.nbcnews.com/nbcnews/public/msnbc", "left"),
    Source("CBS News – World", "US", "https://www.cbsnews.com/latest/rss/world", "lean-left"),
    Source("ABC News – International", "US", "https://abcnews.go.com/abcnews/internationalheadlines", "lean-left"),
    Source("Politico – Politics", "US", "https://rss.politico.com/politics-news.xml", "lean-left"),
    Source("Politico – Congress", "US", "https://rss.politico.com/congress.xml", "lean-left"),
    # --- Lean Right / Right ---
    Source("The Wall Street Journal – World", "US", "https://feeds.a.dj.com/rss/RSSWorldNews.xml", "lean-right"),
    Source("New York Post – World", "US", "https://nypost.com/world-news/feed/", "lean-right"),
    Source("The Economist – International", "UK", "https://www.economist.com/international/rss.xml", "lean-right"),
    Source("Washington Examiner", "US", "https://www.washingtonexaminer.com/tag/news.rss", "right"),
    Source("Fox News – World", "US", "https://moxie.foxnews.com/google-publisher/world.xml", "right"),
    Source("National Review", "US", "https://www.nationalreview.com/feed/", "right"),
    # --- Weitere geografische Perspektiven (weiterhin englischsprachig) ---
    Source("Al Jazeera – All", "QA", "https://www.aljazeera.com/xml/rss/all.xml", "lean-left"),
    Source("South China Morning Post – China", "HK", "https://www.scmp.com/rss/91/feed", "center"),
    Source("Times of India – World", "IN", "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms", "center"),
    Source("Euronews", "FR", "https://www.euronews.com/rss", "center"),
    Source("Kyiv Independent", "UA", "https://kyivindependent.com/feed/", "center"),
    Source("Asharq Al-Awsat English", "SA", "https://english.aawsat.com/feed", "center"),
]

# Empfehlung für einen echten Lauf: vor dem ersten produktiven Einsatz jede
# URL einmal mit `python3 pipeline/fetch_feeds.py` prüfen, tote Links
# aktualisieren/entfernen, und die Bias-Labels ggf. durch eine echte,
# belegte Quelle ersetzen.
