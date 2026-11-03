"""
Transkriptions-Schritt: wandelt eine Podcast-Episode (Audio) in Text um,
damit sie danach wie ein ganz normaler Artikel geclustert/synthetisiert
werden kann.

WICHTIG (ehrlich benannt): Diese Sandbox hat weder ein STT-Modell noch
Zugriff auf einen externen Transkriptions-Dienst (kein API-Key konfiguriert,
kein Netzwerkzugriff für so etwas wie die OpenAI-Whisper-API oder
AssemblyAI). Dieses Modul ist deshalb bewusst als PLUGGABLE INTERFACE
gebaut, exakt nach demselben Muster wie `synthesize_story.py` mit dem
fehlenden `ANTHROPIC_API_KEY`: der Code ist vollständig und lauffähig,
sobald in einer normalen Umgebung eine der Backend-Funktionen unten mit
echten Zugangsdaten aufgerufen wird. Ohne das liefert
`transcribe_episode()` einen klar erkennbaren Platzhalter statt stillem
Fehlschlag oder erfundenem Text.

Unterstützte Backends (auswählbar über `backend=`):
  - "whisper_api"   -> OpenAI Whisper API (braucht OPENAI_API_KEY)
  - "whisper_local" -> lokales `openai-whisper`/`faster-whisper` Modell
                       (braucht das pip-Paket + ggf. GPU)
  - "assemblyai"    -> AssemblyAI API (braucht ASSEMBLYAI_API_KEY)

Alle drei geben dieselbe Struktur zurück (`Transcript`), damit
`fetch_podcasts.py` -> `transcribe.py` -> `episode_to_article_stub()` ->
Cluster-/Synthese-Pipeline nahtlos ineinandergreifen, unabhängig vom
gewählten Backend.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from pipeline.fetch_podcasts import PodcastEpisode
from pipeline.schema import Article


@dataclass
class Transcript:
    text: str
    backend: str
    is_placeholder: bool = False  # True = kein echtes Transkript, nur ein Hinweistext


def _transcribe_whisper_api(audio_url: str, timeout: int = 300) -> str:
    """OpenAI Whisper API. Braucht `openai` Paket + OPENAI_API_KEY."""
    import tempfile

    import requests

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY ist nicht gesetzt.")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Paket 'openai' nicht installiert.") from exc

    client = OpenAI(api_key=api_key)
    with tempfile.NamedTemporaryFile(suffix=".mp3") as tmp:
        resp = requests.get(audio_url, timeout=timeout)
        resp.raise_for_status()
        tmp.write(resp.content)
        tmp.flush()
        with open(tmp.name, "rb") as f:
            result = client.audio.transcriptions.create(model="whisper-1", file=f)
    return result.text


def _transcribe_whisper_local(audio_url: str) -> str:
    """Lokales Whisper-Modell (`pip install openai-whisper`)."""
    import tempfile

    import requests

    try:
        import whisper
    except ImportError as exc:
        raise RuntimeError("Paket 'openai-whisper' nicht installiert.") from exc

    with tempfile.NamedTemporaryFile(suffix=".mp3") as tmp:
        resp = requests.get(audio_url, timeout=300)
        resp.raise_for_status()
        tmp.write(resp.content)
        tmp.flush()
        model = whisper.load_model("base")
        result = model.transcribe(tmp.name)
    return result["text"]


def _transcribe_assemblyai(audio_url: str, timeout: int = 300) -> str:
    """AssemblyAI API. Braucht `assemblyai` Paket + ASSEMBLYAI_API_KEY."""
    api_key = os.environ.get("ASSEMBLYAI_API_KEY")
    if not api_key:
        raise RuntimeError("ASSEMBLYAI_API_KEY ist nicht gesetzt.")
    try:
        import assemblyai as aai
    except ImportError as exc:
        raise RuntimeError("Paket 'assemblyai' nicht installiert.") from exc

    aai.settings.api_key = api_key
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_url)
    return transcript.text


_BACKENDS = {
    "whisper_api": _transcribe_whisper_api,
    "whisper_local": _transcribe_whisper_local,
    "assemblyai": _transcribe_assemblyai,
}


def transcribe_episode(episode: PodcastEpisode, backend: str = "whisper_api") -> Transcript:
    """Versucht, eine Episode zu transkribieren. Fällt bei fehlendem
    Backend/Key auf einen klar markierten Platzhalter zurück (Titel +
    Shownotes-Beschreibung), statt Text zu erfinden oder die Pipeline
    abstürzen zu lassen."""
    if not episode.audio_url:
        return Transcript(
            text=f"{episode.title}\n\n{episode.description}",
            backend="none",
            is_placeholder=True,
        )
    fn = _BACKENDS.get(backend)
    if fn is None:
        raise ValueError(f"Unbekanntes Backend: {backend!r}. Wähle aus {list(_BACKENDS)}.")
    try:
        text = fn(episode.audio_url)
        return Transcript(text=text, backend=backend, is_placeholder=False)
    except RuntimeError as exc:
        # Kein Key/Paket verfügbar -> transparenter Platzhalter statt Absturz.
        print(f"[info] Transkription übersprungen ({exc}); nutze Shownotes als Platzhalter.")
        return Transcript(
            text=f"{episode.title}\n\n{episode.description}",
            backend="none",
            is_placeholder=True,
        )


def episode_to_article_stub(episode: PodcastEpisode, transcript: Transcript) -> Article:
    """Wandelt eine transkribierte Episode in ein normales `Article`-Objekt
    um, damit sie in `cluster.py`/`synthesize_story.py` genauso behandelt
    wird wie ein Textartikel. `is_placeholder`-Transkripte fließen bewusst
    NICHT in eine echte Synthese ein (siehe `run_pipeline.py`), nur echte."""
    return Article(
        source=f"{episode.podcast_name} ({episode.publisher})",
        country="?",
        title=episode.title,
        url=episode.episode_page_url or episode.audio_url or "",
        published=episode.published,
        text=transcript.text,
    )


if __name__ == "__main__":
    print(
        "transcribe.py ist ein pluggable Interface. In dieser Sandbox ist "
        "kein STT-Backend verfügbar (kein API-Key, kein Netzwerkzugriff auf "
        "Whisper/AssemblyAI). Mit OPENAI_API_KEY oder ASSEMBLYAI_API_KEY in "
        "einer normalen Umgebung funktioniert transcribe_episode() direkt."
    )
