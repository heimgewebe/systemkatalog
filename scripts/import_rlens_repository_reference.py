#!/usr/bin/env python3
"""Render dated Cabinet Repository References from rLens/RepoBrief bundle metadata.

The importer is intentionally metadata-only. It does not inspect a live checkout,
refresh a dump, or promote bundle health into live repository truth.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUPPORTED_KINDS = {
    "repolens.bundle.manifest",
    "repobrief_bundle_manifest",
    "lenskit_bundle_manifest",
}
DOES_NOT_ESTABLISH = (
    "live_repository_state",
    "dump_freshness_truth",
    "claim_truth",
    "runtime_correctness",
    "merge_readiness",
    "task_approval",
    "agent_understanding",
)
COMMIT_RE = re.compile(r"^[0-9a-f]{40,64}$")


class RlensReferenceError(RuntimeError):
    """Raised when rLens metadata cannot be imported safely."""


@dataclass(frozen=True)
class BundleMetadata:
    repository: str
    manifest_path: Path
    manifest_sha256: str
    manifest_kind: str
    bundle_stem: str
    generated_at: str
    generator_name: str
    source_commit: str | None
    source_dirty: bool | None
    health_status: str
    freshness_class: str


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - exact parser detail not relevant
        raise RlensReferenceError(f"cannot parse {label}: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RlensReferenceError(f"{label} must be one JSON object: {path}")
    return value


def _sha256_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bundle_stem(manifest_path: Path, manifest: dict[str, Any]) -> str:
    run_id = manifest.get("run_id")
    if isinstance(run_id, str) and run_id.strip():
        return run_id.strip()
    name = manifest_path.name
    for suffix in ("_merge.bundle.manifest.json", ".bundle.manifest.json", "manifest.json"):
        if name.endswith(suffix):
            return name[: -len(suffix)].rstrip("-_") or manifest_path.parent.name
    return manifest_path.stem


def _generated_at(manifest: dict[str, Any]) -> str:
    for key in ("created_at", "generated_at", "updatedAt", "updated_at"):
        value = manifest.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "unknown"


def _runtime(manifest: dict[str, Any]) -> dict[str, Any]:
    generator = manifest.get("generator") if isinstance(manifest.get("generator"), dict) else {}
    runtime = generator.get("runtime") if isinstance(generator.get("runtime"), dict) else {}
    return runtime if isinstance(runtime, dict) else {}


def _generator_name(manifest: dict[str, Any]) -> str:
    generator = manifest.get("generator") if isinstance(manifest.get("generator"), dict) else {}
    value = generator.get("name") if isinstance(generator, dict) else None
    if isinstance(value, str) and value.strip():
        return value.strip()
    kind = manifest.get("kind")
    return str(kind) if kind else "unknown"


def _source_commit(manifest: dict[str, Any], repository: str) -> str | None:
    provenance = manifest.get("snapshot_provenance")
    if isinstance(provenance, dict):
        repos = provenance.get("repositories")
        if isinstance(repos, list):
            for item in repos:
                if not isinstance(item, dict):
                    continue
                name = item.get("name") or item.get("repo") or item.get("id")
                if name == repository:
                    commit = item.get("git_commit") or item.get("commit")
                    if isinstance(commit, str) and COMMIT_RE.fullmatch(commit):
                        return commit
    runtime = _runtime(manifest)
    commit = runtime.get("git_commit")
    if isinstance(commit, str) and COMMIT_RE.fullmatch(commit):
        return commit
    return None


def _source_dirty(manifest: dict[str, Any], repository: str) -> bool | None:
    provenance = manifest.get("snapshot_provenance")
    if isinstance(provenance, dict):
        repos = provenance.get("repositories")
        if isinstance(repos, list):
            for item in repos:
                if not isinstance(item, dict):
                    continue
                name = item.get("name") or item.get("repo") or item.get("id")
                if name == repository and isinstance(item.get("git_dirty"), bool):
                    return item["git_dirty"]
    runtime = _runtime(manifest)
    dirty = runtime.get("git_dirty")
    return dirty if isinstance(dirty, bool) else None


def _health_status(health: dict[str, Any] | None) -> str:
    if not health:
        return "unknown"
    for key in ("status", "verdict", "result"):
        value = health.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "unknown"


def _freshness_class(generated_at: str, source_commit: str | None, health_status: str) -> str:
    if generated_at == "unknown" or source_commit is None:
        return "unknown_dated_snapshot"
    if health_status in {"fail", "failed", "error"}:
        return "dated_snapshot_health_failed"
    return "dated_snapshot"


def read_bundle_metadata(
    manifest_path: str | Path,
    *,
    repository: str,
    health_path: str | Path | None = None,
) -> BundleMetadata:
    manifest_path = Path(manifest_path)
    manifest = _load_json(manifest_path, "bundle manifest")
    kind = manifest.get("kind")
    if not isinstance(kind, str) or kind not in SUPPORTED_KINDS:
        raise RlensReferenceError(f"unsupported bundle manifest kind: {kind!r}")
    health = _load_json(Path(health_path), "bundle health") if health_path else None
    generated_at = _generated_at(manifest)
    source_commit = _source_commit(manifest, repository)
    health_status = _health_status(health)
    return BundleMetadata(
        repository=repository,
        manifest_path=manifest_path,
        manifest_sha256=_sha256_bytes(manifest_path),
        manifest_kind=kind,
        bundle_stem=_bundle_stem(manifest_path, manifest),
        generated_at=generated_at,
        generator_name=_generator_name(manifest),
        source_commit=source_commit,
        source_dirty=_source_dirty(manifest, repository),
        health_status=health_status,
        freshness_class=_freshness_class(generated_at, source_commit, health_status),
    )


def render_reference(metadata: BundleMetadata) -> str:
    commit = metadata.source_commit or "<unknown>"
    dirty = "unknown" if metadata.source_dirty is None else str(metadata.source_dirty).lower()
    return "\n".join(
        [
            f"# {metadata.repository} — rLens Repository Reference",
            "",
            "> **Semantik:** Diese Seite ist ein datierter rLens/RepoBrief-Snapshot-Beleg.",
            "> Sie behauptet keinen aktuellen Live-Zustand des Repositories.",
            "> Git und explizite Live-Pruefungen bleiben fuer aktuellen Zustand massgeblich.",
            "",
            "## rLens Bundle-Provenienz",
            "",
            "| Feld | Wert |",
            "|---|---|",
            f"| Repository | `{metadata.repository}` |",
            f"| Bundle-Stem | `{metadata.bundle_stem}` |",
            f"| Manifest | `{metadata.manifest_path.as_posix()}` |",
            f"| Manifest-SHA-256 | `{metadata.manifest_sha256}` |",
            f"| Manifest-Kind | `{metadata.manifest_kind}` |",
            f"| Generator | `{metadata.generator_name}` |",
            f"| Erzeugt | `{metadata.generated_at}` |",
            f"| Health | `{metadata.health_status}` |",
            f"| Freshness-Klasse | `{metadata.freshness_class}` |",
            "",
            "## Datiertes Repository-Snapshot-Signal",
            "",
            "| Feld | Wert |",
            "|---|---|",
            f"| Snapshot-Commit | `{commit}` |",
            f"| Snapshot-Dirty | `{dirty}` |",
            "| Live-Zustand behauptet | `false` |",
            "| Cabinet-generiert Dump | `false` |",
            "",
            "## Agent-Briefing-Hinweis",
            "",
            "Diese Referenz kann als Cabinet-Agent-Briefing-Quelle verwendet werden, wenn ein Agent einen datierten Repo-Kontext braucht. Sie ist kein Ersatz fuer Live-Git-Pruefung, PR-Diff oder Runtime-Beobachtung.",
            "",
            "## Abgrenzung",
            "",
            "- Diese Referenz importiert nur Bundle-Metadaten.",
            "- Sie erzeugt keinen Dump und aktualisiert keine rLens-Artefakte.",
            "- Sie wertet Health nicht als Repo-Verstaendnis oder Merge-Freigabe.",
            "- Sie behauptet keinen aktuellen HEAD, wenn kein separater Live-Check vorliegt.",
            "",
            "## Does not establish",
            "",
            *[f"- `{item}`" for item in DOES_NOT_ESTABLISH],
            "",
        ]
    )


def build_agent_briefing(metadata: BundleMetadata) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "cabinet_rlens_repository_agent_briefing",
        "repository": metadata.repository,
        "bundleStem": metadata.bundle_stem,
        "manifestSha256": metadata.manifest_sha256,
        "generatedAt": metadata.generated_at,
        "freshnessClass": metadata.freshness_class,
        "health": metadata.health_status,
        "sourceCommit": metadata.source_commit,
        "liveStateClaimed": False,
        "doesNotEstablish": list(DOES_NOT_ESTABLISH),
    }


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        tmp = Path(handle.name)
        handle.write(text)
        handle.flush()
    try:
        tmp.replace(path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--health")
    parser.add_argument("--output")
    parser.add_argument("--agent-briefing-output")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    metadata = read_bundle_metadata(args.manifest, repository=args.repository, health_path=args.health)
    reference = render_reference(metadata)
    briefing = build_agent_briefing(metadata)

    if args.output:
        output = Path(args.output)
        if args.check:
            existing = output.read_text(encoding="utf-8") if output.exists() else ""
            if existing != reference:
                raise RlensReferenceError(f"{output}: rLens Repository Reference is not current")
        else:
            _atomic_write(output, reference)
    if args.agent_briefing_output:
        content = json.dumps(briefing, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        output = Path(args.agent_briefing_output)
        if args.check:
            existing = output.read_text(encoding="utf-8") if output.exists() else ""
            if existing != content:
                raise RlensReferenceError(f"{output}: rLens agent briefing is not current")
        else:
            _atomic_write(output, content)
    if args.json:
        reference = dict(metadata.__dict__)
        reference["manifest_path"] = metadata.manifest_path.as_posix()
        print(
            json.dumps(
                {"reference": reference, "agentBriefing": briefing},
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    try:
        raise SystemExit(main())
    except RlensReferenceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
