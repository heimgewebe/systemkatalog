# Cabinet rLens Repository Reference Import v1

Status: implemented as a metadata-only importer.

## Purpose

Cabinet can turn an rLens/RepoBrief bundle manifest into a dated Repository Reference or bounded agent briefing.

This is a snapshot-reference import. It is not a live repository observer.

## Inputs

- bundle manifest JSON
- optional bundle health JSON
- explicit repository id

Supported manifest kinds:

- `repolens.bundle.manifest`
- `repobrief_bundle_manifest`
- `lenskit_bundle_manifest`

## Outputs

The importer can write:

- a Markdown rLens Repository Reference
- an optional JSON agent briefing

Both outputs include:

- bundle stem
- manifest hash
- generated timestamp when present
- health status
- freshness class
- explicit non-claims

## Boundary

The importer must not:

- generate or refresh rLens bundles
- inspect live Git state
- claim current repository HEAD
- create Bureau tasks
- approve imports, merges or runtime actions

## Non-claims

The import does not establish live repository state, dump freshness truth, claim truth, runtime correctness, merge readiness, task approval or agent understanding.
