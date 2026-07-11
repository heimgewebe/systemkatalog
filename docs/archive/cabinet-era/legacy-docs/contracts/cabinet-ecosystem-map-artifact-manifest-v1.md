# Cabinet Ecosystem Map Artifact Manifest v1

Status: draft
Owner: Cabinet
Schema: `docs/contracts/cabinet-ecosystem-map-artifact-manifest-v1.schema.json`

## Purpose

This contract describes a generated manifest for Cabinet ecosystem-map artifacts consumed by read-only viewers such as Leitstand.

The manifest records:

- the Cabinet repository identity;
- the Cabinet source commit used to produce the manifest;
- the generation timestamp;
- the readable Mermaid overview;
- the generated registry Mermaid projection;
- the map blueprint;
- the registry inputs used by the projection;
- SHA-256 and byte metadata for each artifact;
- explicit non-claims.

## Boundary

The manifest is a source and provenance contract. It is not a second ecosystem map and not a truth oracle.

It does not establish:

- claim truth;
- runtime correctness;
- merge readiness;
- Cabinet registry correctness;
- Leitstand view correctness;
- that render success validates the map.

## Producer

Cabinet owns the map semantics and produces or validates this manifest through:

```bash
python3 scripts/write_ecosystem_map_artifact_manifest.py --check
```

A consumer or release job may write a concrete manifest artifact with:

```bash
python3 scripts/write_ecosystem_map_artifact_manifest.py --output rendered/ecosystem-map-artifact-manifest.json
```

The written manifest is intentionally generated. It contains the current Git commit and generation timestamp, so it should normally be produced by a job or operator action, not hand-edited.

## Consumer rules

Consumers such as Leitstand may:

- read a pinned manifest;
- display the source commit, artifact paths, byte counts, digests, and freshness state;
- render or display referenced artifacts read-only;
- link back to Cabinet as the canonical source.

Consumers must not:

- edit Cabinet map content;
- treat a rendered diagram as proof of runtime state;
- infer claim truth from a Mermaid edge;
- auto-repair stale manifests;
- dispatch tasks or mutate repositories from the map view.

## Artifact order

The manifest lists artifacts in this order:

1. `readable_overview_mermaid` — `rendered/ecosystem-map.mmd`
2. `generated_registry_projection_mermaid` — `rendered/ecosystem-registry-map.mmd`
3. `map_blueprint` — `docs/blueprints/ecosystem-map-v0.md`
4. `registry_nodes` — `registry/ecosystem/nodes.json`
5. `registry_edges` — `registry/ecosystem/edges.json`
6. `registry_claims` — `registry/ecosystem/claims.jsonl`

The order is part of the contract to simplify deterministic downstream checks.
