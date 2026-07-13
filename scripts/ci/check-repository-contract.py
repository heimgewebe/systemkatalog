#!/usr/bin/env python3
"""Validate the tracked static Systemkatalog repository contract."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

LEGACY_ROOTS = {
    "bestand", "pruefung", "steuerung", "vorzimmer", "heimgewebe",
    "weltgewebe", "werkstatt", "labor", "betrieb",
}
LEGACY_MARKERS = {".cabinet", ".home", ".agents", ".global-agents", ".jobs", "Cabinet-Modell.md"}
LEGACY_RUNTIME_PARTS = {".agents", ".global-agents", ".cabinet", ".cabinet-state"}
LEGACY_IGNORE_MARKERS = (".cabinet", ".agents", ".global-agents")
REQUIRED_STATIC_SURFACES = {
    "README.md",
    "AGENTS.md",
    "index.md",
    "catalog/system-catalog.schema.v1.json",
    "catalog/system-catalog.example.v1.json",
    "catalog/ecosystem-map-artifact-manifest.schema.v1.json",
    "policy/system-catalog.v1.json",
    "policy/ecosystem-map-view.v1.json",
    "registry/ecosystem/nodes.json",
    "registry/ecosystem/edges.json",
    "registry/ecosystem/claims.jsonl",
    "registry/ecosystem/authority-matrix.v1.json",
    "registry/ecosystem/fleet-coverage.v1.json",
    "registry/ecosystem/organization-scope.v1.json",
    "rendered/system-catalog.md",
    "rendered/ecosystem-registry-map.mmd",
    "rendered/ecosystem-map-artifact-manifest.json",
    "scripts/validate_system_catalog.py",
    "scripts/system_catalog_scope.py",
    "scripts/check_organization_scope.py",
    "scripts/render_system_catalog.py",
    "scripts/render_ecosystem_registry_map.py",
    "scripts/write_ecosystem_map_artifact_manifest.py",
}
RETIRED_RUNTIME_PATHS = {
    "ops/README.md",
    "ops/manifest.json",
    "ops/bin/systemkatalog",
    "ops/bin/systemkatalogctl",
    "ops/install/audit-local-runtime.sh",
    "ops/install/install-local-runtime.sh",
    "ops/install/retire-local-runtime.sh",
    "ops/systemd/systemkatalog.service.tmpl",
    "scripts/serve_system_catalog.py",
    "scripts/tests/test_system_catalog_service.py",
    "scripts/ci/check-installed-runtime.py",
    "scripts/ci/test-install-local-runtime.sh",
    "scripts/ci/test-retire-local-runtime.sh",
}
RUNTIME_BASENAMES = {
    "systemkatalog.service",
    "systemkatalog.service.tmpl",
    "systemkatalogctl",
    "serve_system_catalog.py",
    "test_system_catalog_service.py",
    "install-local-runtime.sh",
    "audit-local-runtime.sh",
    "retire-local-runtime.sh",
    "test-install-local-runtime.sh",
    "test-retire-local-runtime.sh",
    "check-installed-runtime.py",
}


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def git_tree(repo: Path, treeish: str) -> dict[str, dict[str, str]]:
    result = subprocess.run(
        ["git", "ls-tree", "-rz", "--full-tree", treeish],
        cwd=repo, capture_output=True, text=True, check=True,
    )
    tree: dict[str, dict[str, str]] = {}
    for entry in result.stdout.split("\0"):
        if not entry:
            continue
        metadata, path = entry.split("\t", 1)
        mode, object_type, object_hash = metadata.split(" ", 2)
        tree[path] = {"mode": mode, "type": object_type, "hash": object_hash}
    return tree


def git_text(repo: Path, treeish: str, path: str) -> str:
    return subprocess.check_output(["git", "show", f"{treeish}:{path}"], cwd=repo, text=True)


def active(path: str) -> bool:
    return not path.startswith("docs/archive/cabinet-era/")


def check_layout_and_forbidden_paths(tree: dict[str, dict[str, str]]) -> None:
    errors: list[str] = []
    roots = {path.split("/", 1)[0] for path in tree}
    for name in sorted(LEGACY_ROOTS & roots):
        errors.append(f"legacy room root: {name}")
    for marker in sorted(LEGACY_MARKERS & roots):
        errors.append(f"legacy active marker: {marker}")
    if "docs/archive/cabinet-era/README.md" not in tree:
        errors.append("archive boundary README missing")
    for path in tree:
        if not active(path):
            continue
        parts = path.split("/")
        basename = parts[-1]
        if basename == ".cabinet.db" or basename.startswith(".cabinet.db-"):
            errors.append(f"database file: {path}")
        elif LEGACY_RUNTIME_PARTS.intersection(parts):
            errors.append(f"legacy agent/runtime state: {path}")
        elif basename in {".env", ".cabinet.env", "runtime.env"} or basename.startswith(".env."):
            errors.append(f"env file: {path}")
        elif basename.endswith((".pem", ".key")):
            errors.append(f"key file: {path}")
    if errors:
        fail("forbidden tracked path:\n  " + "\n  ".join(errors))


def check_gitignore_text(text: str, *, source: str = ".gitignore") -> None:
    patterns = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    stale = sorted(
        pattern
        for pattern in patterns
        if not pattern.startswith("!")
        and any(marker in pattern for marker in LEGACY_IGNORE_MARKERS)
    )
    if stale:
        fail(
            f"legacy runtime path must remain visible instead of ignored in {source}: "
            + ", ".join(stale)
        )


def active_gitignore_paths(tree: dict[str, dict[str, str]]) -> list[str]:
    return sorted(
        path
        for path, entry in tree.items()
        if active(path)
        and entry["type"] == "blob"
        and path.rsplit("/", 1)[-1] == ".gitignore"
    )


def check_static_surface(tree: dict[str, dict[str, str]], repo: Path, treeish: str) -> None:
    missing = sorted(path for path in REQUIRED_STATIC_SURFACES if path not in tree or tree[path]["type"] != "blob")
    if missing:
        fail("required static surface missing:\n  " + "\n  ".join(missing))

    runtime_sources = sorted(
        path
        for path in tree
        if active(path)
        and (path in RETIRED_RUNTIME_PATHS or path.rsplit("/", 1)[-1] in RUNTIME_BASENAMES)
    )
    if runtime_sources:
        fail("retired Systemkatalog runtime source still tracked:\n  " + "\n  ".join(runtime_sources))

    gitignore_paths = active_gitignore_paths(tree)
    if ".gitignore" not in gitignore_paths:
        fail("root .gitignore missing")
    for path in gitignore_paths:
        check_gitignore_text(git_text(repo, treeish, path), source=path)

    policy = json.loads(git_text(repo, treeish, "policy/system-catalog.v1.json"))
    if "runtimeProjection" in policy:
        fail("runtimeProjection must remain absent from the static catalog policy")
    maintained = policy.get("maintainedCatalogSurfaces")
    if not isinstance(maintained, list) or any(not isinstance(path, str) for path in maintained):
        fail("maintainedCatalogSurfaces must be a string array")
    stale = sorted(
        path
        for path in maintained
        if path in RETIRED_RUNTIME_PATHS or path.rsplit("/", 1)[-1] in RUNTIME_BASENAMES
    )
    if stale:
        fail("runtime surface remains in maintainedCatalogSurfaces: " + ", ".join(stale))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--tree-ish", required=True)
    args = parser.parse_args()
    tree = git_tree(args.repo_root, args.tree_ish)
    check_layout_and_forbidden_paths(tree)
    check_static_surface(tree, args.repo_root, args.tree_ish)
    print("SYSTEMKATALOG-STATIC-MANIFEST-AND-PATH-CONTRACT: PASS")


if __name__ == "__main__":
    main()
