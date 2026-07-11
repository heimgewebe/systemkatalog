#!/usr/bin/env python3
"""Prepare an isolated compatibility sandbox for the historical Bureau probe.

The pinned Bureau probe predates the stable Cabinet catalog and requires the
literal source path ``registry/ecosystem/claims.jsonl``. The maintained Cabinet
catalog must not expose its stable architecture claims as task candidates, so
this adapter copies the hash-bound archived dynamic claims into a temporary
sandbox and rewrites only the sandbox policy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_POLICY_REL = Path("registry/ecosystem/bureau-bridge.json")
SYSTEM_POLICY_REL = Path("policy/system-catalog.v1.json")
ARCHIVE_CLAIMS_REL = Path("docs/archive/cabinet-era/ecosystem-dynamic-claims-v0.jsonl")
LEGACY_PROBE_CLAIMS_REL = Path("registry/ecosystem/claims.jsonl")
LEGACY_PROBE_POLICY_REL = Path("registry/ecosystem/bureau-bridge.json")


class LegacyBridgeProbeError(RuntimeError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LegacyBridgeProbeError(f"required input missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LegacyBridgeProbeError(f"invalid JSON in {path}: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise LegacyBridgeProbeError(f"JSON root must be an object: {path}")
    return value


def _resolve_under(root: Path, relative: Path | str, *, label: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise LegacyBridgeProbeError(f"{label} escapes root: {relative}") from exc
    return candidate


def prepare(root: Path = ROOT, output: Path = Path("bridge-probe-sandbox")) -> dict[str, Any]:
    root = root.resolve()
    output_root = output if output.is_absolute() else root / output
    output_root = output_root.resolve()
    try:
        output_root.relative_to(root)
    except ValueError as exc:
        raise LegacyBridgeProbeError(f"output escapes repository root: {output}") from exc
    if output_root.exists() and any(output_root.iterdir()):
        raise LegacyBridgeProbeError(f"output sandbox is not empty: {output_root}")

    bridge = _load(_resolve_under(root, BRIDGE_POLICY_REL, label="bridge policy"))
    catalog_policy = _load(_resolve_under(root, SYSTEM_POLICY_REL, label="system catalog policy"))
    if bridge.get("status") != "legacy_compatibility_only":
        raise LegacyBridgeProbeError("bridge policy must be legacy compatibility only")
    if bridge.get("catalog_authoritative") is not False:
        raise LegacyBridgeProbeError("bridge policy must be non-authoritative for the catalog")
    allowed_sources = bridge.get("allowed_sources")
    if not isinstance(allowed_sources, list):
        raise LegacyBridgeProbeError("bridge allowed_sources must be an array")
    archive_name = str(ARCHIVE_CLAIMS_REL)
    legacy_name = str(LEGACY_PROBE_CLAIMS_REL)
    if archive_name not in allowed_sources:
        raise LegacyBridgeProbeError("bridge policy does not expose the archived dynamic claims")
    if legacy_name in allowed_sources:
        raise LegacyBridgeProbeError("canonical stable claims must not be exposed by the maintained bridge policy")

    archive_path = _resolve_under(root, ARCHIVE_CLAIMS_REL, label="archived claims")
    archive_bytes = archive_path.read_bytes()
    archive_sha = hashlib.sha256(archive_bytes).hexdigest()
    archives = catalog_policy.get("legacySourceArchives")
    if not isinstance(archives, list):
        raise LegacyBridgeProbeError("system catalog policy legacySourceArchives missing")
    expected = next(
        (item.get("sha256") for item in archives if isinstance(item, dict) and item.get("path") == archive_name),
        None,
    )
    if expected != archive_sha:
        raise LegacyBridgeProbeError("archived dynamic claims fail the catalog policy hash binding")

    claims_target = _resolve_under(output_root, LEGACY_PROBE_CLAIMS_REL, label="sandbox claims")
    policy_target = _resolve_under(output_root, LEGACY_PROBE_POLICY_REL, label="sandbox policy")
    claims_target.parent.mkdir(parents=True, exist_ok=True)
    claims_target.write_bytes(archive_bytes)

    sandbox_policy = dict(bridge)
    sandbox_policy["allowed_sources"] = [legacy_name if item == archive_name else item for item in allowed_sources]
    sandbox_policy["probe_adapter"] = {
        "kind": "legacy_claim_path_adapter",
        "source": archive_name,
        "source_sha256": archive_sha,
        "target": legacy_name,
        "catalog_authoritative": False,
        "persistent": False,
    }
    policy_target.write_text(json.dumps(sandbox_policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "status": "prepared",
        "output": str(output_root.relative_to(root)),
        "policy": str(policy_target.relative_to(root)),
        "claims": str(claims_target.relative_to(root)),
        "claimsSha256": archive_sha,
        "catalogClaimsUnchanged": True,
        "persistent": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=Path("bridge-probe-sandbox"))
    args = parser.parse_args()
    print(json.dumps(prepare(args.repo_root, args.output), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
