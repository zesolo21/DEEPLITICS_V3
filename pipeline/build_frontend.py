"""
Baut frontend/index.html aus frontend/index.template.html +
data/stories.json + der Bias-Einordnung aus sources/feeds.py.

Aufruf: python3 pipeline/build_frontend.py
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.sources.feeds import SOURCES  # noqa: E402


def build() -> Path:
    stories = json.loads((ROOT / "data" / "stories.json").read_text())
    tpl = (ROOT / "frontend" / "index.template.html").read_text()
    app_js = (ROOT / "frontend" / "app.js").read_text()

    stories_payload = json.dumps(stories, ensure_ascii=False).replace("</script>", "<\\/script>")

    source_bias = {s.name: s.bias for s in SOURCES}
    bias_payload = json.dumps(source_bias, ensure_ascii=False).replace("</script>", "<\\/script>")

    html = tpl.replace("__STORIES_JSON__", stories_payload)
    html = html.replace("__SOURCE_BIAS_JSON__", bias_payload)
    html = html.replace("__APP_JS__", app_js.replace("</script>", "<\\/script>"))
    # "Stand: ..."-Zeitstempel oben im Frontend: Build-Datum dieses statischen
    # Snapshots, ehrlich als solches gelabelt (kein Live-Update-Zeitstempel,
    # da diese Version ohne Laufzeit-API arbeitet).
    html = html.replace("__BUILD_DATE_ISO__", datetime.date.today().isoformat())

    out_path = ROOT / "frontend" / "index.html"
    out_path.write_text(html)
    print(f"Wrote {len(html)} bytes -> {out_path}")
    return out_path


if __name__ == "__main__":
    build()
