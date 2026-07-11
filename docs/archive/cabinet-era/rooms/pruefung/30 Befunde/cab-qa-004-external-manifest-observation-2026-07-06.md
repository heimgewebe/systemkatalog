# Befund — CAB-QA-004 externe Manifestreferenzen

Datum: 2026-07-06

CAB-QA-004 wurde beobachtet. Es wurde kein contract-konformes externes RepoBrief- oder Lenskit-Manifest fuer cabinet/main gefunden. Die Registry bleibt unveraendert; beide Quellen bleiben unobserved.

## These / Antithese / Synthese

These: CAB-QA-004 kann nur dann eine beobachtete Quelle registrieren, wenn ein konkreter relativer Manifestpfad und ein belegter Generierungszeitpunkt vorliegen.

Antithese: Alte Health-Sidecars, Schema-Dateien oder beliebige Manifest-Dateien koennen wie ein Beleg aussehen, sind aber keine Cabinet-Manifestreferenz im Sinne des Contracts.

Synthese: Keine Registry-Mutation. Fehlende Evidenz bleibt als Leerstelle sichtbar.

## Belegte Beobachtung

- GitHub: offene Cabinet-PRs 0.
- `origin/main`: `348ed0a6945b6e8d7b28d585f843b2425c3c93a5`.
- Nach CAB-QA-006 liegen auf `main` weitere Merges: #77 und #78.
- Der Hauptcheckout war sauber, aber auf dem alten Branch `docs/cabqa4`; gearbeitet wurde deshalb im separaten Worktree `cab-qa-004-manifest-observation-v1`.
- Im aktuellen Cabinet-Worktree existiert kein `external/`-Manifestpfad.

## Dump- und Manifestbefund

- Unter `/home/alex/repos/merges` wurden fuer Cabinet nur alte `cabinet-max-*_merge.output_health.json`-Sidecars vom 2026-06-24 bis 2026-06-26 gefunden.
- Zu diesen Cabinet-Stems wurden keine passenden `*_merge.md`, `*_merge.json`, `*_merge.bundle.manifest.json` oder `*_merge.agent_entry_manifest.json` gefunden.
- In `heimgewebe/lenskit` auf `main` gibt es Manifest-Contract-Dateien, aber kein Cabinet-Dumpmanifest.
- In `/home/alex/iCloud/Drive` fanden sich Lenskit-Schema-Dateien und fachfremde Manifeste, aber kein Cabinet-RepoBrief-/Lenskit-Dumpmanifest.

## Nicht als Evidenz akzeptiert

- `*_merge.output_health.json` allein: Health-Pass beweist keine aktuelle Manifestreferenz und kein Repo-Verstaendnis.
- Lenskit-Contract- oder Schema-Dateien: Sie beschreiben eine Form, liefern aber keine Cabinet-Instanz.
- `ops/manifest.json`, Web-App-Manifeste oder Import-Manifeste: anderer Zweck, anderer Contract.
- Der alte lokale Branch `docs/cabqa4`: er basiert vor PR #75/#76/#77/#78 und wuerde aktuelle Dateien entfernen.

## Ergebnis

`registry/ecosystem/external-dump-sources.json` bleibt unveraendert:

- `external-dump:repobrief` bleibt `observation.status = unobserved`.
- `external-dump:lenskit` bleibt `observation.status = unobserved`.
- `latestManifestPath` und `latestManifestGeneratedAt` bleiben leer.

Fehlende Evidenz wird nicht in eine beobachtete Quelle uebersetzt.

## Validierung

- `python3 scripts/validate_external_dump_sources.py --json` -> PASS, 2 Quellen (`lenskit`, `repobrief`).
- `python3 scripts/write_cabinet_maintenance_report.py --check --json` -> PASS/WARN: 2 Findings, 0 epistemische Gaps.
- Erwartete Findings:
  - `cabqa:freshness:external-dump:lenskit:manifest-unobserved`
  - `cabqa:freshness:external-dump:repobrief:manifest-unobserved`

## Leerstelle

Manifestpfad und Zeitstempel fehlen. Noetig fuer Freshness-Pruefung ueber konkrete Dumps.
