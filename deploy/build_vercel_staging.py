"""Build the public prototype UI with synthetic stories for Vercel staging."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "public"


def inject_staging_data(template_html: str, app_js: str, stories: list[dict]) -> str:
    """Build the prototype UI with synthetic data and its existing frontend logic."""
    if not stories or any(
        not str(story.get("id", "")).startswith("demo-")
        or not str(story.get("title", "")).startswith("Demo:")
        for story in stories
    ):
        raise ValueError("Vercel staging accepts only explicitly synthetic Demo stories.")

    build_date = datetime.now(timezone.utc).date().isoformat()
    replacements = {
        "__STORIES_JSON__": json.dumps(stories, ensure_ascii=False, separators=(",", ":")),
        "__SOURCE_BIAS_JSON__": "{}",
        "__APP_JS__": app_js.replace("</script>", "<\\/script>"),
        "__BUILD_DATE_ISO__": build_date,
    }
    html = template_html
    for marker, value in replacements.items():
        if marker not in html:
            raise RuntimeError(f"Could not find prototype template marker {marker}.")
        html = html.replace(marker, value)
    return html


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)

    app_output = OUTPUT / "app"
    app_output.mkdir(parents=True)

    staging_payload = json.loads((ROOT / "deploy" / "staging-stories.json").read_text(encoding="utf-8"))
    if staging_payload.get("environment") != "staging":
        raise ValueError("Refusing to build Vercel output from a non-staging story snapshot.")
    template_html = (ROOT / "frontend" / "index.template.html").read_text(encoding="utf-8")
    app_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    index_html = inject_staging_data(template_html, app_js, staging_payload.get("stories", []))

    body_marker = "<body>"
    style_marker = "</style>"
    if body_marker not in index_html or style_marker not in index_html:
        raise RuntimeError("Could not find the prototype's body and style sections.")

    banner = (
        '<div class="staging-banner" role="status">'
        "STAGING PREVIEW · Synthetic demo stories only"
        "</div>"
    )
    banner_css = (
        "\n.staging-banner{padding:9px 16px;background:#f0bd69;color:#211a10;"
        "text-align:center;font-size:12px;font-weight:800;letter-spacing:.035em}\n"
    )
    index_html = index_html.replace(body_marker, f"{body_marker}\n{banner}", 1)
    index_html = index_html.replace(style_marker, f"{banner_css}{style_marker}", 1)
    (app_output / "index.html").write_text(index_html, encoding="utf-8")


if __name__ == "__main__":
    main()
