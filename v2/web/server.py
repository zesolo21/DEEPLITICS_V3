"""
Schritt 6: Frontend -- Dashboard, Themen-Ansicht, Thread-Detail-Ansicht,
Einstellungsseite (Bauanleitung Abschnitt 5).

Bewusst als serverseitig gerendertes Flask + Jinja2 ohne eigenes
JavaScript-Framework gehalten -- passend zur MVP-Vorgabe aus Abschnitt 7
("beginne mit einer lauffaehigen, aber bewusst kleinen Version").
Einstellungen werden per einfachem POST-Formular geaendert (kein AJAX
noetig fuer Version 1).

Aufruf: python3 web/server.py  ->  http://127.0.0.1:5057
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from flask import Flask, abort, redirect, render_template, request, url_for

from pipeline import store
from pipeline.config import DEFAULT_CONFIG, DEFAULT_USER_ID, TOPIC_LABELS, TOPICS
from pipeline.feeds import apply_perspective_breadth, count_new_per_topic, get_top_feed, get_topic_feed

DB_PATH = ROOT / "deeplitics_v2.db"

app = Flask(__name__)


def get_conn():
    if not DB_PATH.exists():
        abort(500, "Datenbank nicht gefunden. Zuerst `python3 pipeline/run_pipeline.py` ausfuehren.")
    return store.connect(DB_PATH)


@app.route("/")
def dashboard():
    conn = get_conn()
    threads = store.load_threads(conn)
    user = store.load_user(conn, DEFAULT_USER_ID)
    conn.close()

    top_feed = get_top_feed(threads, DEFAULT_CONFIG)
    new_counts = count_new_per_topic(threads, user)

    pinned = [
        {"key": key, "label": TOPIC_LABELS[key], "new_count": new_counts.get(key, 0)}
        for key in user.pinned_topics
    ]
    return render_template(
        "dashboard.html", top_feed=top_feed, pinned=pinned,
        today=datetime.date.today().strftime("%d.%m.%Y"),
    )


@app.route("/topic/<topic_key>")
def topic_view(topic_key: str):
    if topic_key not in TOPIC_LABELS:
        abort(404)
    conn = get_conn()
    threads = store.load_threads(conn)
    articles = store.load_articles(conn)
    user = store.load_user(conn, DEFAULT_USER_ID)
    conn.close()

    by_id = {a.id: a for a in articles}
    feed = get_topic_feed(threads, by_id, topic_key, user)
    return render_template(
        "topic.html", topic_label=TOPIC_LABELS[topic_key], topic_key=topic_key, feed=feed,
    )


@app.route("/thread/<thread_id>")
def thread_detail(thread_id: str):
    conn = get_conn()
    thread = store.load_thread(conn, thread_id)
    if not thread:
        conn.close()
        abort(404)
    articles = store.load_articles_for_thread(conn, thread_id)
    user = store.load_user(conn, DEFAULT_USER_ID)

    # "welche Threads zuletzt gesehen wurden" fortschreiben (fuer die
    # "neu seit letztem Besuch"-Markierung, Abschnitt 2/4).
    if thread_id not in user.last_seen_thread_ids:
        user.last_seen_thread_ids.append(thread_id)
        store.save_user(conn, user)
    conn.close()

    source_views = apply_perspective_breadth(articles, user)
    return render_template(
        "thread.html", thread=thread, source_views=source_views,
        topic_label=TOPIC_LABELS.get(thread.topic, thread.topic),
        detail_level=user.detail_level,
    )


@app.route("/settings")
def settings():
    conn = get_conn()
    user = store.load_user(conn, DEFAULT_USER_ID)
    conn.close()
    topics = [{"key": t.key, "label": t.label, "pinned": t.key in user.pinned_topics} for t in TOPICS]
    return render_template("settings.html", topics=topics, user=user)


@app.route("/settings/pin", methods=["POST"])
def toggle_pin():
    conn = get_conn()
    user = store.load_user(conn, DEFAULT_USER_ID)
    key = request.form["topic_key"]
    if key in user.pinned_topics:
        user.pinned_topics.remove(key)
    else:
        user.pinned_topics.append(key)
    store.save_user(conn, user)
    conn.close()
    return redirect(url_for("settings"))


@app.route("/settings/sliders", methods=["POST"])
def update_sliders():
    conn = get_conn()
    user = store.load_user(conn, DEFAULT_USER_ID)
    detail_level = request.form.get("detail_level")
    perspective_breadth = request.form.get("perspective_breadth")
    if detail_level in ("short", "medium", "full"):
        user.detail_level = detail_level
    if perspective_breadth in ("narrow", "wide"):
        user.perspective_breadth = perspective_breadth
    store.save_user(conn, user)
    conn.close()
    return redirect(url_for("settings"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5057, debug=True)
