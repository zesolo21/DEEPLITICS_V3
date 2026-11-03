# Hosting: reicht Claude allein, oder braucht es einen externen Anbieter?

**Kurz: Für den jetzigen Prototyp-Loop reicht Claude allein — für eine
echte, öffentlich erreichbare Website/App später braucht es einen externen
Hosting-Anbieter.** Beides schließt sich nicht aus, es sind zwei Phasen.

## Phase 1 — jetzt: Vorschau direkt hier (gewählt)

`frontend/index.html` ist ein einziges, selbstständiges HTML-File (kein
Server, keine Installation, keine externen Skripte). Claude kann es:

- direkt als Vorschau schicken, die man im Browser öffnen kann,
- bei jeder Änderung neu rendern und wieder schicken — das ist der
  gewünschte kleine Feedback-Loop: Änderung -> sofort sichtbar.

Nachteil: Es ist (noch) keine öffentliche URL, die man z.B. an andere
Personen schicken kann, und es läuft nicht automatisch/regelmäßig (die
Extraction-Pipeline muss manuell angestoßen werden).

## Phase 2 — später: echtes Live-Deployment

Claude selbst kann keinen dauerhaft erreichbaren, öffentlichen Server
betreiben — dafür braucht es einen Hosting-Anbieter. Realistischer Aufbau:

- **Frontend (die Website):** ein Git-Repository (GitHub) + **Vercel** oder
  **Netlify** — beide haben kostenlose Stufen, verbinden sich direkt mit
  GitHub, und jeder `git push` deployed automatisch live. Das ist der
  Standard-Weg für genau so ein Projekt und passt gut zum gewünschten
  schnellen Feedback-Loop (push -> in ~1 Minute live).
- **Backend/Pipeline (RSS holen, Volltext extrahieren, clustern,
  LLM-Synthese):** kann als geplanter Job laufen — z.B. **GitHub Actions**
  (kostenlos, stündlich/täglich per Cron) oder ein kleiner Dienst wie
  **Render**/**Railway**/**Fly.io**. Ergebnis (die Story-JSON-Daten) landet
  z.B. in einer kleinen Datenbank oder einfach als Datei, die das Frontend
  lädt.
- **Domain:** optional, später über einen Registrar (Namecheap, Google
  Domains-Nachfolger, etc.) — nicht nötig, um loszulegen.

## Für die spätere App (iOS/Android)

Sobald aus der Website eine App werden soll: entweder als **PWA**
(Progressive Web App — die bestehende Website wird "installierbar", kein
separates App-Store-Listing nötig) oder als native App mit z.B.
**React Native**/**Flutter**, die dieselbe Backend-API nutzt. Das ist ein
späterer Schritt und beeinflusst die jetzige Architektur kaum, solange
Frontend und Backend sauber getrennt bleiben (was hier schon der Fall ist:
`pipeline/` liefert Daten, `frontend/` zeigt sie an).

## Empfehlung für den nächsten Schritt

Sobald der Prototyp inhaltlich gut genug ist: GitHub-Repo anlegen, Code
hochladen, mit Vercel verbinden (paar Klicks, du brauchst nur einen
kostenlosen Vercel-Account) — dann hat der Feedback-Loop zusätzlich eine
echte URL, die auch von unterwegs/anderen Personen aufrufbar ist.
