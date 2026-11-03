"""
Kuratierte Liste politischer Nachrichten-Podcasts.

Podcast-RSS-Feeds sind technisch normale RSS-Feeds, nur mit einem
<enclosure>-Tag pro Episode, das auf eine Audio-Datei zeigt. Das heisst:
der Fetch-Schritt (`fetch_podcasts.py`) ist strukturell fast identisch zu
`fetch_feeds.py` fuer Text-Quellen, nur dass am Ende ein Transkriptions-
schritt (`transcribe.py`) noetig ist, bevor der Inhalt in dieselbe
Cluster-/Synthese-Pipeline wie Artikel einfliessen kann.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PodcastSource:
    name: str
    publisher: str
    feed_url: str
    bias: str = "center"
    lang: str = "en"


PODCASTS: list[PodcastSource] = [
    PodcastSource("Up First", "NPR", "https://feeds.npr.org/510318/podcast.xml", "lean-left"),
    PodcastSource("Global News Podcast", "BBC World Service", "https://podcasts.files.bbci.co.uk/p02nq0gn.rss", "center"),
    PodcastSource("The Daily", "The New York Times", "https://feeds.simplecast.com/54nAGcIl", "lean-left"),
    PodcastSource("Today, Explained", "Vox", "https://feeds.megaphone.fm/VMP5705694065", "left"),
    PodcastSource("The Journal.", "The Wall Street Journal", "https://feeds.megaphone.fm/WSJ6059368487", "lean-right"),
    PodcastSource("Intelligence Squared", "Intelligence Squared", "https://feeds.megaphone.fm/VMP4924125405", "center"),
]

# Wie bei sources/feeds.py: nicht jede URL ist in dieser Sandbox getestet
# (siehe docs/NETWORK_NOTES.md). fetch_podcasts.py ueberspringt kaputte
# Feeds automatisch.
