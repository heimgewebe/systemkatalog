# Befund — CAB-QA-008 externe Manifestreferenzen refreshed

Datum: 2026-07-09
Status: refreshed

## These / Antithese / Synthese

These: Der Maintenance Report darf nur dann `pass` melden, wenn eine beobachtete externe RepoBrief-/Lenskit-Manifestreferenz auch als konkrete Manifestdatei im Cabinet-Repo nachweisbar ist.

Antithese: Eine frische Manifestdatei ist keine semantische Wahrheit. Sie beweist nur, dass eine datierte Artefaktoberfläche referenzierbar ist.

Synthese: Cabinet speichert begrenzte externe Manifestreferenzen und prüft deren Oberfläche. Cabinet erzeugt keine Dumps, leitet daraus keine Claim-Wahrheit ab und dispatcht kein Bureau oder Grabowski.

## Beobachtete Referenzquelle

- Ausgangsbundle: `/home/alex/repos/merges/cabinet-max-260709-0938_merge.bundle.manifest.json`
- Bundle `created_at`: `2026-07-09T09:38:19Z`
- Live-Repo-Head bei Refresh: `08f0d9ae3b777c5a24c3444f1603c1871f1f632d`

## Geschriebene externe Manifestreferenzen

- `external/repobrief/cabinet/main/manifest.json`
  - `kind`: `repobrief_bundle_manifest`
  - `generatedAt`: `2026-07-09T09:38:19Z`
- `external/lenskit/cabinet/main/manifest.json`
  - `kind`: `lenskit_bundle_manifest`
  - `generatedAt`: `2026-07-09T09:38:19Z`

## Registry-Entscheidung

`registry/ecosystem/external-dump-sources.json` wurde für beide Quellen auf das neue `generatedAt` aktualisiert. Die Pfade bleiben relativ und entsprechen dem bestehenden Contract-Muster.

## Prüfverstärkung

Der Maintenance Report prüft beobachtete Manifestreferenzen nun nicht nur gegen die Registry, sondern auch gegen die referenzierte Manifestdatei:

- Manifestdatei vorhanden;
- valides JSON-Objekt;
- `kind` entspricht `requiredManifestKind`;
- `artifactFamily`, `repository`, `ref` und `generatedAt` passen zur Registry-Beobachtung.

Fehlt die Datei oder widerspricht sie der Registry, entsteht ein P2-Freshness-Finding statt eines Schein-`pass`.

## Ergebnis

- `scripts/validate_external_dump_sources.py --json`: PASS
- `scripts/write_cabinet_maintenance_report.py --check --json`: PASS, `findingCount=0`, `status=pass`
- `scripts/write_cabinet_live_signals.py`: drei valide read-only Signale

## Nicht etabliert

Dieser Befund etabliert nicht Claim-Wahrheit, Runtime-Korrektheit, semantische Vollständigkeit, Merge-Fähigkeit, Bureau-Import, Task-Freigabe oder Dump-Erzeugung durch Cabinet.

## Epistemische Leere

Die wiederkehrende Publikation frischer Manifestreferenzen bleibt eine Aufgabe des zuständigen Produzentenpfads RepoBrief/Lenskit. Dieser Slice macht nur die Cabinet-Konsumoberfläche frisch und prüfbarer.
