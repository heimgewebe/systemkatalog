#!/usr/bin/env python3
"""Validate Cabinet's external dump source registry."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "registry" / "ecosystem" / "external-dump-sources.json"

KIND = "cabinet_external_dump_sources"
CONTRACT_VERSION = "1"
CONTRACT_PATH = "docs/contracts/cabinet-external-dump-sources-v1.md"
SCHEMA_PATH = "docs/contracts/cabinet-external-dump-sources-v1.schema.json"
MODE = "external_dump_source_contract_registry"
AUTO_DISPATCH = "autonomous_" + "dispatch"
REQUIRED_FAMILIES = {"repobrief", "lenskit"}
REQUIRED_NON_CLAIMS = {
    "dump_freshness_truth",
    "claim_truth",
    "runtime_correctness",
    "merge_readiness",
    "task_approval",
    AUTO_DISPATCH,
    "dump_generation_permission",
}
SOURCE_NON_CLAIMS = {
    "dump_freshness_truth",
    "claim_truth",
    "runtime_correctness",
    "semantic_correctness",
    "task_approval",
    "dump_generation_permission",
}


class ExternalDumpSourcesError(ValueError):
    """Raised when the external dump source registry is invalid."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ExternalDumpSourcesError(f"missing external dump source registry: {path}") from None
    except json.JSONDecodeError as exc:
        raise ExternalDumpSourcesError(f"invalid JSON in external dump source registry: {exc}") from None
    if not isinstance(payload, dict):
        raise ExternalDumpSourcesError("external dump source registry must be an object")
    return payload


def _repo_path(repo_root: Path, raw_path: str, label: str) -> Path:
    if not isinstance(raw_path, str) or not raw_path:
        raise ExternalDumpSourcesError(f"{label} must be a non-empty string")
    path = (repo_root / raw_path).resolve()
    try:
        path.relative_to(repo_root)
    except ValueError:
        raise ExternalDumpSourcesError(f"{label} escapes repository: {raw_path}") from None
    return path


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ExternalDumpSourcesError(f"{label} must be a non-empty string")
    return value


def _string_list(value: Any, label: str, *, minimum: int = 1) -> list[str]:
    if not isinstance(value, list):
        raise ExternalDumpSourcesError(f"{label} must be a list")
    if len(value) < minimum:
        raise ExternalDumpSourcesError(f"{label} must contain at least {minimum} item(s)")
    result: list[str] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, str) or not item:
            raise ExternalDumpSourcesError(f"{label} item {index} must be a non-empty string")
        result.append(item)
    if len(set(result)) != len(result):
        raise ExternalDumpSourcesError(f"{label} must not contain duplicates")
    return result


def _string_set(value: Any, label: str, *, minimum: int = 1) -> set[str]:
    return set(_string_list(value, label, minimum=minimum))


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ExternalDumpSourcesError(f"{label} must be an object")
    return value


def _positive_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ExternalDumpSourcesError(f"{label} must be a positive integer")
    return value


def _parse_observed_at(value: str, label: str) -> datetime:
    raw = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ExternalDumpSourcesError(f"{label} must be an ISO timestamp") from exc


def _validate_latest_manifest_path(latest_path: str, pattern: str, family: str, source_id: str) -> None:
    if latest_path != latest_path.strip():
        raise ExternalDumpSourcesError(f"source {source_id} latestManifestPath must not contain surrounding whitespace")
    if "://" in latest_path or latest_path.startswith("//") or Path(latest_path).is_absolute():
        raise ExternalDumpSourcesError(f"source {source_id} latestManifestPath must be a relative registry path")
    if "\\" in latest_path:
        raise ExternalDumpSourcesError(f"source {source_id} latestManifestPath must use forward slashes")
    parts = latest_path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ExternalDumpSourcesError(f"source {source_id} latestManifestPath must not contain empty or traversal segments")
    if not latest_path.endswith("/manifest.json"):
        raise ExternalDumpSourcesError(f"source {source_id} latestManifestPath must end with /manifest.json")
    if f"external/{family}/" not in latest_path:
        raise ExternalDumpSourcesError(f"source {source_id} latestManifestPath must stay under external/{family}/")
    regex = re.escape(pattern)
    regex = regex.replace(re.escape("{repository}"), r"[^/]+")
    regex = regex.replace(re.escape("{ref}"), r"[^/]+")
    if not re.fullmatch(regex, latest_path):
        raise ExternalDumpSourcesError(f"source {source_id} latestManifestPath must match manifestPattern")


def validate_sources(repo_root: Path, registry_path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    path = registry_path if registry_path.is_absolute() else repo_root / registry_path
    registry = _load_json(path)

    if registry.get("schemaVersion") != 1:
        raise ExternalDumpSourcesError("schemaVersion must be 1")
    if registry.get("kind") != KIND:
        raise ExternalDumpSourcesError(f"kind must be {KIND}")
    if registry.get("contractVersion") != CONTRACT_VERSION:
        raise ExternalDumpSourcesError("contractVersion mismatch")
    if registry.get("contractPath") != CONTRACT_PATH:
        raise ExternalDumpSourcesError("contractPath mismatch")
    if registry.get("schemaPath") != SCHEMA_PATH:
        raise ExternalDumpSourcesError("schemaPath mismatch")
    if registry.get("mode") != MODE:
        raise ExternalDumpSourcesError("mode mismatch")
    if registry.get("cabinetGeneratesDumps") is not False:
        raise ExternalDumpSourcesError("cabinetGeneratesDumps must be false")

    for required_path, label in ((CONTRACT_PATH, "contractPath"), (SCHEMA_PATH, "schemaPath")):
        if not _repo_path(repo_root, required_path, label).is_file():
            raise ExternalDumpSourcesError(f"{label} references missing file: {required_path}")

    sources = registry.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ExternalDumpSourcesError("sources must be a non-empty list")
    if registry.get("sourceCount") != len(sources):
        raise ExternalDumpSourcesError("sourceCount must match sources length")

    non_claims = _string_set(registry.get("doesNotEstablish"), "doesNotEstablish")
    missing_non_claims = REQUIRED_NON_CLAIMS - non_claims
    if missing_non_claims:
        raise ExternalDumpSourcesError("doesNotEstablish missing: " + ", ".join(sorted(missing_non_claims)))

    seen_ids: set[str] = set()
    seen_families: set[str] = set()
    for index, source in enumerate(sources, start=1):
        source_obj = _object(source, f"source {index}")
        source_id = _string(source_obj.get("id"), f"source {index} id")
        if not source_id.startswith("external-dump:"):
            raise ExternalDumpSourcesError(f"source {source_id} id must start with external-dump:")
        if source_id in seen_ids:
            raise ExternalDumpSourcesError(f"duplicate source id: {source_id}")
        seen_ids.add(source_id)

        family = _string(source_obj.get("artifactFamily"), f"source {source_id} artifactFamily")
        if family not in REQUIRED_FAMILIES:
            raise ExternalDumpSourcesError(f"source {source_id} artifactFamily is unsupported: {family}")
        seen_families.add(family)
        if source_obj.get("producerOrgan") != "repobrief_lenskit":
            raise ExternalDumpSourcesError(f"source {source_id} producerOrgan must be repobrief_lenskit")
        if source_obj.get("hashAlgorithm") != "sha256":
            raise ExternalDumpSourcesError(f"source {source_id} hashAlgorithm must be sha256")
        if source_obj.get("freshnessBasis") != "manifest_generated_at":
            raise ExternalDumpSourcesError(f"source {source_id} freshnessBasis must be manifest_generated_at")
        if source_obj.get("cabinetStorage") not in {"external_reference_only", "manifest_reference_only"}:
            raise ExternalDumpSourcesError(f"source {source_id} cabinetStorage is invalid")
        if source_obj.get("cadence") not in {"on_repository_change_or_daily", "on_repository_change_or_manual_refresh"}:
            raise ExternalDumpSourcesError(f"source {source_id} cadence is invalid")
        _positive_int(source_obj.get("maxAgeHours"), f"source {source_id} maxAgeHours")

        pattern = _string(source_obj.get("manifestPattern"), f"source {source_id} manifestPattern")
        if "{repository}" not in pattern or "{ref}" not in pattern:
            raise ExternalDumpSourcesError(f"source {source_id} manifestPattern must include {{repository}} and {{ref}}")
        if not pattern.endswith("manifest.json"):
            raise ExternalDumpSourcesError(f"source {source_id} manifestPattern must end with manifest.json")
        _string(source_obj.get("requiredManifestKind"), f"source {source_id} requiredManifestKind")
        _string_list(source_obj.get("requiredArtifactSuffixes"), f"source {source_id} requiredArtifactSuffixes")

        observation = _object(source_obj.get("observation"), f"source {source_id} observation")
        status = observation.get("status")
        latest_path = observation.get("latestManifestPath")
        generated_at = observation.get("latestManifestGeneratedAt")
        if status not in {"unobserved", "observed", "disabled"}:
            raise ExternalDumpSourcesError(f"source {source_id} observation.status is invalid")
        if not isinstance(latest_path, str) or not isinstance(generated_at, str):
            raise ExternalDumpSourcesError(f"source {source_id} observation path/timestamp must be strings")
        if status == "unobserved" and (latest_path or generated_at):
            raise ExternalDumpSourcesError(f"source {source_id} unobserved state must not set latest manifest fields")
        if status == "observed":
            if not latest_path or not generated_at:
                raise ExternalDumpSourcesError(f"source {source_id} observed state requires latest manifest path and timestamp")
            _validate_latest_manifest_path(latest_path, pattern, family, source_id)
            _parse_observed_at(generated_at, f"source {source_id} latestManifestGeneratedAt")
        if status == "disabled" and generated_at:
            _parse_observed_at(generated_at, f"source {source_id} latestManifestGeneratedAt")

        source_non_claims = _string_set(source_obj.get("doesNotEstablish"), f"source {source_id} doesNotEstablish")
        missing_source_non_claims = SOURCE_NON_CLAIMS - source_non_claims
        if missing_source_non_claims:
            raise ExternalDumpSourcesError(
                f"source {source_id} doesNotEstablish missing: " + ", ".join(sorted(missing_source_non_claims))
            )

    missing_families = REQUIRED_FAMILIES - seen_families
    if missing_families:
        raise ExternalDumpSourcesError("missing dump families: " + ", ".join(sorted(missing_families)))

    return registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        registry = validate_sources(args.repo_root, args.registry)
    except ExternalDumpSourcesError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        else:
            print(f"validate_external_dump_sources: {exc}", file=sys.stderr)
        return 1
    payload = {
        "ok": True,
        "kind": registry["kind"],
        "sourceCount": registry["sourceCount"],
        "families": sorted({source["artifactFamily"] for source in registry["sources"]}),
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(
            "External dump source registry: PASS "
            f"({payload['sourceCount']} sources: {', '.join(payload['families'])})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
