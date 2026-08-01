#!/usr/bin/env python3
"""Git-native durable provenance refs for internal Systemkatalog source commits."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

SHA40 = re.compile(r"^[0-9a-f]{40}$")
PROVENANCE_TAG_NAMESPACE = "systemkatalog-provenance-v1"
DEFAULT_PROVENANCE_BASE_REF = "refs/remotes/origin/main"


class ProvenanceTagError(ValueError):
    pass


def provenance_tag_name(commit: str) -> str:
    if SHA40.fullmatch(commit) is None:
        raise ProvenanceTagError("provenance commit must be a lowercase 40 character Git SHA")
    return f"{PROVENANCE_TAG_NAMESPACE}/{commit}"


def provenance_tag_ref(commit: str) -> str:
    return f"refs/tags/{provenance_tag_name(commit)}"


def _resolve_commit(root: Path, revision: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{revision}^{{commit}}"],
            cwd=root,
            check=False,
            text=True,
            capture_output=True,
        )
    except OSError as exc:
        raise ProvenanceTagError("could not inspect Git provenance refs") from exc
    if result.returncode == 1:
        return None
    if result.returncode != 0:
        raise ProvenanceTagError("could not inspect Git provenance refs")
    value = result.stdout.strip()
    if SHA40.fullmatch(value) is None:
        raise ProvenanceTagError(f"Git provenance ref resolves to an invalid commit: {revision}")
    return value


def provenance_baseline(root: Path, fallback_revision: str) -> str:
    return (
        DEFAULT_PROVENANCE_BASE_REF
        if _resolve_commit(root, DEFAULT_PROVENANCE_BASE_REF) is not None
        else fallback_revision
    )


def _is_ancestor(root: Path, commit: str, descendant: str) -> bool | None:
    try:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, descendant],
            cwd=root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise ProvenanceTagError("could not inspect Git provenance ancestry") from exc
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    if _resolve_commit(root, commit) is None:
        return None
    raise ProvenanceTagError("could not inspect Git provenance ancestry")


def require_durable_provenance_tag(
    root: Path,
    commit: str,
    baseline_revision: str,
    *,
    label: str,
) -> str | None:
    """Require a deterministic tag for source commits outside the durable baseline history."""
    if SHA40.fullmatch(commit) is None:
        raise ProvenanceTagError(f"{label} commit must be a lowercase 40 character Git SHA")
    baseline_commit = _resolve_commit(root, baseline_revision)
    if baseline_commit is None:
        raise ProvenanceTagError(f"{label} cannot resolve provenance baseline {baseline_revision}")
    if commit == baseline_commit or _is_ancestor(root, commit, baseline_commit) is True:
        return None
    tag_ref = provenance_tag_ref(commit)
    tag_commit = _resolve_commit(root, tag_ref)
    if tag_commit is None:
        raise ProvenanceTagError(f"{label} requires durable provenance tag {tag_ref}")
    if tag_commit != commit:
        raise ProvenanceTagError(
            f"{label} durable provenance tag {tag_ref} resolves to {tag_commit}, expected {commit}"
        )
    return tag_ref
