# Warum die Sandbox hier keinen freien Internetzugriff hat

Diese Cloud-Sandbox (in der Claude gerade arbeitet) hat aus Sicherheitsgründen
nur eingeschränkten Netzwerkzugriff:

- `bash`/`requests`/`curl` können NUR auf eine Allowlist von Paket-Registries
  zugreifen (z.B. für `pip`/`npm`-Installationen) — Zugriffe auf normale
  Webseiten (Nachrichtenseiten, CDNs wie `cdnjs.cloudflare.com`, sogar
  `pypi.org` im Test heute) werden mit `403 host_not_allowed` blockiert.
- Das `WebFetch`-Tool (das Claude direkt nutzen kann) hat einen anderen,
  breiteren Zugriffspfad und konnte heute z.B. BBC, NPR und Al Jazeera live
  erreichen — aber nicht jede Seite (z.B. Reuters, The Guardian, Deutsche
  Welle wurden blockiert).

**Das betrifft NUR diese Entwicklungsumgebung.** Der geschriebene Code
(`pipeline/fetch_feeds.py`, `pipeline/extract_article.py`, ...) verwendet
ganz normale `requests`-Aufrufe und wird auf jedem regulären Rechner, Server
oder in einer CI-Pipeline (GitHub Actions, Vercel Cron, eigener VPS) ohne
diese Einschränkung laufen.

**Praktische Konsequenz für heute:** Statt die Pipeline hier automatisiert
laufen zu lassen, hat Claude die realen Artikel-Inhalte über `WebFetch`
manuell geholt und den Cluster- + Synthese-Schritt live durchgespielt
(`pipeline/demo_live_run.py`), um zu beweisen, dass das Konzept funktioniert
— mit echten, aktuellen Daten vom 15.08.2026, nicht mit Fake-Daten.
