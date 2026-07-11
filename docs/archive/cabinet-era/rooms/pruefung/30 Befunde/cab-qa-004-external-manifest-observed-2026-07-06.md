# Befund — CAB-QA-004 externe Manifestreferenzen beobachtet

Datum: 2026-07-06
Status: observed

## These / Antithese / Synthese

These: Nach Lenskit PR #897/#898/#899 kann RepoBrief/Lenskit aus einem bestehenden Bundle-Manifest externe Manifestreferenzen fuer Cabinet erzeugen.

Antithese: Eine beobachtete Manifestreferenz ist noch keine Claim-Wahrheit. Sie belegt nur eine konkrete, datierte Artefaktoberflaeche.

Synthese: Cabinet registriert die beobachteten relativen Manifestpfade, aber uebernimmt keine Dump-Erzeugung und leitet keine semantische Wahrheit ab.

## Beobachtete externe Manifestreferenzen

- `external/repobrief/cabinet/main/manifest.json`
  - `kind`: `repobrief_bundle_manifest`
  - `generatedAt`: `2026-07-06T16:01:58Z`
  - lokale Beobachtungsquelle: `/home/alex/repos/merges/cab-main-260706-1801-repobrief/external/repobrief/cabinet/main/manifest.json`
- `external/lenskit/cabinet/main/manifest.json`
  - `kind`: `lenskit_bundle_manifest`
  - `generatedAt`: `2026-07-06T16:01:58Z`
  - lokale Beobachtungsquelle: `/home/alex/repos/merges/cab-main-260706-1801-repobrief/external/lenskit/cabinet/main/manifest.json`

## Produzentenbeleg

- Lenskit `origin/main` nach PR #899: `b21a37f9e3be676e8490e9b08068fd724b580ece`.
- Cabinet Snapshot-Quelle: `/tmp/cab-src-main` bei `61189494b0682568e00618f5ff53eb72529956b0`.
- RepoBrief Snapshot-Bundle: `/home/alex/repos/merges/cab-main-260706-1801-repobrief/cab-src-main-max-260706-1601_merge.bundle.manifest.json`.
- RepoBrief Snapshot Status: `ok`.
- RepoBrief Required Reading fuer `basic_repo_question`: `pass`.
- Profile Evaluation fuer `full-max`: `warn`, weil `relation_cards_jsonl` empfohlen, aber nicht vorhanden ist. Keine required-Artefakte fehlen.

## Registry-Entscheidung

`registry/ecosystem/external-dump-sources.json` wird fuer beide Quellen auf `observed` gesetzt. `latestManifestGeneratedAt` wird aus den externen Manifesten uebernommen.

## Nicht etabliert

Die beobachteten Manifestreferenzen etablieren nicht Claim-Wahrheit, Runtime-Korrektheit, semantische Vollstaendigkeit, Merge-Faehigkeit, Bureau-Import oder Dump-Erzeugung durch Cabinet.

## Epistemische Leere

Ein stabiler dauerhafter Publikationsort ausserhalb des lokalen `/home/alex/repos/merges`-Laufs ist noch nicht als Infrastruktur garantiert. Noetig fuer wiederholbare Freshness-Automation.
