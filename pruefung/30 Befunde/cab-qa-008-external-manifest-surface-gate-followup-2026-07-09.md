# Befund — CAB-QA-008 External Manifest Surface Gate Follow-up

Datum: 2026-07-09
Status: fixed

## Anlass

Nach Merge von CAB-QA-008 zeigte der Diff-Review eine Contract-Luecke: Der Maintenance Report pruefte beobachtete Manifestdateien gegen Top-Level-Felder, aber nicht gegen die in `registry/ecosystem/external-dump-sources.json` definierten `requiredArtifactSuffixes`.

## Entscheidung

Der Maintenance Report prueft beobachtete externe Manifestreferenzen jetzt auch gegen die Artefaktliste:

- `artifacts` muss eine Liste sein;
- fuer jedes `requiredArtifactSuffixes` der Registry muss mindestens ein `artifacts[].path` mit diesem Suffix existieren;
- fehlt ein Pflichtartefakt, entsteht ein P2-Freshness-Finding statt eines Schein-`pass`.

## Manifest-Oberflaeche

Die existierende `cabinet-max-260709-0938_merge.bundle_health.post.json` wurde in beide externen Manifestreferenzen aufgenommen.

Die Registry-Pflicht fuer `_merge.claim_evidence_map.json` wurde fuer `lenskit` entfernt, weil dieser konkrete Cabinet-Bundle kein solches Artefakt enthaelt. Cabinet erzeugt es nicht nachtraeglich und erfindet keine Dump-Sidecars.

## Ergebnisgrenze

Dieser Follow-up etabliert weiterhin keine Claim-Wahrheit, keine Runtime-Korrektheit, keine Merge-Faehigkeit und keine Dump-Erzeugung durch Cabinet. Er macht nur die beobachtete Manifestoberflaeche strenger pruefbar.

## Hinweis zu Live-Signal-Artefakten

Ein im Git-Commit gespeichertes Signal kann nicht zugleich den Hash genau desselben finalen Commits enthalten, weil der Commit-Hash vom Dateiinhalt abhaengt. Head-gebundene Signal-Evidence muss deshalb als nachgelagertes Run-/PR-Review-Artefakt erzeugt werden, nicht als selbstreferenzieller Dateiinhalt im selben Commit.
