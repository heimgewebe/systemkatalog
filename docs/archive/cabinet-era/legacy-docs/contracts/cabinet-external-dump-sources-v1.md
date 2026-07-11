# Cabinet External Dump Sources v1

Status: draft
Owner: Cabinet
Schema: `docs/contracts/cabinet-external-dump-sources-v1.schema.json`
Registry: `registry/ecosystem/external-dump-sources.json`
Validator: `scripts/validate_external_dump_sources.py`

## Purpose

This contract defines how Cabinet records externally produced RepoBrief/Lenskit dump surfaces.

Cabinet does not produce these dumps. Cabinet records enough source-contract information to decide whether a dump family is observable, fresh enough to use, and still inside its authority boundary.

## Required source information

Each external dump source records:

- source id;
- artifact family;
- producer organ;
- expected cadence;
- maximum age in hours;
- manifest path pattern;
- required manifest kind;
- required artifact suffixes;
- required hash algorithm;
- observation status;
- explicit non-claims.

## Observation states

| Status | Meaning |
|---|---|
| `unobserved` | Cabinet knows the contract, but has not observed a concrete manifest yet. |
| `observed` | Cabinet has a latest manifest path and generated-at timestamp. |
| `disabled` | Source is intentionally ignored for freshness scans. |

An `unobserved` source is not a contract gap anymore. It is a freshness finding: Cabinet knows what to expect, but has not seen the latest artifact.

## Boundary

This contract does not allow Cabinet to generate RepoBrief or Lenskit dumps.

It does not establish:

- dump freshness truth;
- claim truth;
- runtime correctness;
- merge readiness;
- task approval;
- autonomous dispatch;
- that a missing observed manifest is a runtime failure.

## Consumer rules

A Cabinet maintenance report may:

- validate the registry shape;
- validate that an observed manifest file exists at the registered Cabinet-relative path;
- validate the observed manifest surface fields and required artifact suffixes;
- surface unobserved, missing, mismatching or stale dump sources as findings;
- use a latest observed manifest timestamp for freshness classification;
- cite the source registry and observed manifest path as evidence.

It must not:

- create missing dumps;
- dispatch Bureau or Grabowski;
- infer current repo truth from a stale dump;
- treat hash metadata as semantic correctness.
