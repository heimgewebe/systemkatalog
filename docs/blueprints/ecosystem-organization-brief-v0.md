# ORG v0

Status: draft
Datum: 2026-07-04
Owner: Cabinet

## These

Das wachsende Heimgewebe-Oekosystem braucht eine Karte, weil sonst Rollen, Belege, Agentenauftraege und PR-Zustaende auseinanderlaufen.

## Antithese

Eine eigene Karte als eigenes Repository waere im Moment verfrueht. Sie wuerde eine weitere Wahrheitsflaeche erzeugen, bevor die vorhandenen Organe stabil zusammenspielen.

## Synthese

Die Ecosystem Map v0 wird in Cabinet gepflegt. Der intendierte lokale Pflegeort ist `/home/alex/repos/cabinet`. Ein eigenes Map-Repo bleibt eine spaetere Reifeentscheidung.

## Rollen

Rollen werden getrennt und ueber Belege verbunden.

- Cabinet: Sinn, Evidenz, Priorisierung, Lernen, Map-Semantik.
- Bureau: Aufgaben, Taktung, Delegation, Rueckmeldung.
- Grabowski / Operator: Ausfuehrung, Repo-Arbeit, Review-Gates.
- RepoBrief: Kontextansicht und zitierfaehige Repository-Briefs.
- Steuerboard: read-only Repo-State-Signal.
- Vibe-Lab: Methoden- und Evidence-Lab.
- Chronik: Event-Trace.
- GitHub / CI: harte technische Realitaetspruefung.
- Externe Agenten: Draft, Review, Patchvorschlag.

RepoBrief ist der oeffentliche Name der Context-View-Schicht. Lenskit bleibt bis zu einer spaeteren Rename-Entscheidung Legacy-Repository und Implementierungsnamespace.

## Map-Dateien

- `docs/blueprints/ecosystem-map-v0.md`
- `registry/ecosystem/nodes.json`
- `registry/ecosystem/edges.json`
- `registry/ecosystem/claims.jsonl`
- `rendered/ecosystem-map.mmd`
- `scripts/validate_ecosystem_map.py`

## Wahrheitsgrenze

Cabinet darf die Aussagen verbinden, aber nicht alle Wahrheit besitzen. GitHub, CI, Runtime, Contracts und menschliche Entscheidungen bleiben in ihrer Domaene primaer.
