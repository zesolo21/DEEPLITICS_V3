"""Build the public, synthetic-data-only Vercel staging preview."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "public"


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)

    app_output = OUTPUT / "app"
    api_output = OUTPUT / "api" / "v1"
    app_output.mkdir(parents=True)
    api_output.mkdir(parents=True)

    for filename in ("index.html", "app.js", "styles.css"):
        shutil.copy2(ROOT / "v3" / filename, app_output / filename)

    index_path = app_output / "index.html"
    index_html = index_path.read_text(encoding="utf-8")
    marker = "<body>"
    banner = (
        '<div class="staging-banner" role="status">'
        "STAGING PREVIEW · Synthetic demo stories only · Sign-in and saving are disabled"
        "</div>"
    )
    if marker not in index_html:
        raise RuntimeError("Could not find the app body to label the staging preview.")
    index_path.write_text(index_html.replace(marker, f"{marker}\n  {banner}", 1), encoding="utf-8")

    styles_path = app_output / "styles.css"
    with styles_path.open("a", encoding="utf-8") as styles:
        styles.write(
            "\n.staging-banner{position:sticky;top:0;z-index:20;padding:9px 16px;"
            "background:#f0bd69;color:#211a10;text-align:center;font-size:12px;"
            "font-weight:800;letter-spacing:.035em}\n"
        )

    for source_name in ("staging-public-config.json", "staging-stories.json"):
        payload = json.loads((ROOT / "deploy" / source_name).read_text(encoding="utf-8"))
        target_name = "public-config.json" if "public-config" in source_name else "stories.json"
        (api_output / target_name).write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
