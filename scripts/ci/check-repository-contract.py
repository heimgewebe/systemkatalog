#!/usr/bin/env python3
"""Validate the tracked Systemkatalog repository and runtime manifest."""

from __future__ import annotations

import argparse
import json
import posixpath
import subprocess
from pathlib import Path

LEGACY_ROOTS = {
    "bestand", "pruefung", "steuerung", "vorzimmer", "heimgewebe",
    "weltgewebe", "werkstatt", "labor", "betrieb",
}
LEGACY_MARKERS = {".cabinet", ".home", ".agents", ".jobs", "Cabinet-Modell.md"}


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
        elif ".cabinet-state" in parts:
            errors.append(f"runtime state: {path}")
        elif basename in {".env", ".cabinet.env", "runtime.env"} or basename.startswith(".env."):
            errors.append(f"env file: {path}")
        elif basename.endswith((".pem", ".key")):
            errors.append(f"key file: {path}")
    if errors:
        fail("forbidden tracked path:\n  " + "\n  ".join(errors))


def validate_source(tree: dict[str, dict[str, str]], source: str, expected_mode: str) -> None:
    if not source or posixpath.isabs(source) or ".." in source.split("/") or "" in source.split("/"):
        fail(f"invalid manifest source: {source}")
    if source not in tree or tree[source]["type"] != "blob":
        fail(f"manifest source not a tracked file: {source}")
    if tree[source]["mode"] != expected_mode:
        fail(f"git mode mismatch for {source}: {tree[source]['mode']} != {expected_mode}")


def check_manifest(tree: dict[str, dict[str, str]], repo: Path, treeish: str) -> None:
    path = "ops/manifest.json"
    if path not in tree:
        fail(f"{path} missing")
    manifest = json.loads(git_text(repo, treeish, path))
    expected_fields = {
        "schema", "runtime_version", "repository_root", "service",
        "executables", "retirement", "retired_runtime_paths", "preserved_private_paths",
    }
    if set(manifest) != expected_fields:
        fail("manifest top-level fields mismatch")
    if manifest["schema"] != "systemkatalog.runtime.v1":
        fail(f"manifest.schema: {manifest['schema']}")
    if manifest["runtime_version"] != "1" or manifest["repository_root"] != "~/repos/systemkatalog":
        fail("manifest runtime identity mismatch")
    expected_service = {
        "name": "systemkatalog.service",
        "template": "ops/systemd/systemkatalog.service.tmpl",
        "destination": "~/.config/systemd/user/systemkatalog.service",
        "bind": "127.0.0.1",
        "port": 4001,
        "mode": "0644",
    }
    if manifest["service"] != expected_service:
        fail(f"manifest.service mismatch: {manifest['service']}")
    validate_source(tree, expected_service["template"], "100644")
    expected_exec = {
        "ops/bin/systemkatalog": ("~/.local/bin/systemkatalog", "0755"),
        "ops/bin/systemkatalogctl": ("~/.local/bin/systemkatalogctl", "0755"),
    }
    actual_exec = {
        item.get("source"): (item.get("destination"), item.get("mode"))
        for item in manifest["executables"] if isinstance(item, dict)
    }
    if actual_exec != expected_exec:
        fail(f"manifest.executables mismatch: {actual_exec}")
    for source in expected_exec:
        validate_source(tree, source, "100755")
    expected_retirement = {
        "script": "ops/install/retire-local-runtime.sh",
        "mode": "0755",
        "backup_root": "~/.local/state/systemkatalog/runtime-retirements/",
        "requires_authorization_reference": True,
        "requires_expected_head": True,
    }
    if manifest["retirement"] != expected_retirement:
        fail(f"manifest.retirement mismatch: {manifest['retirement']}")
    validate_source(tree, expected_retirement["script"], "100755")
    validate_source(tree, "scripts/ci/test-retire-local-runtime.sh", "100755")
    expected_retired = {
        "~/.config/systemd/user/heimgewebe-systemkatalog.service",
        "~/.local/bin/heimgewebe-systemkatalog",
        "~/.config/systemd/user/cabinet.service",
        "~/.config/systemd/user/cabinet.service.d/",
        "~/.local/bin/cabinet", "~/.local/bin/cabinet-session",
        "~/.local/bin/cabinetctl", "~/.local/bin/cabinet-security-gate",
    }
    if set(manifest["retired_runtime_paths"]) != expected_retired:
        fail("manifest.retired_runtime_paths mismatch")
    expected_preserved = {"~/.config/cabinet/", "~/.local/state/cabinet/", "~/.cabinet/", ".cabinet-state/"}
    if set(manifest["preserved_private_paths"]) != expected_preserved:
        fail("manifest.preserved_private_paths mismatch")
    forbidden_sources = {
        "ops/bin/heimgewebe-systemkatalog", "ops/systemd/heimgewebe-systemkatalog.service.tmpl",
        "ops/bin/cabinet", "ops/bin/cabinet-session", "ops/bin/cabinetctl",
        "ops/bin/cabinet-security-gate", "ops/systemd/cabinet.service.tmpl",
    }
    present = sorted(forbidden_sources & set(tree))
    if present:
        fail(f"retired runtime source still tracked: {present}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--tree-ish", required=True)
    args = parser.parse_args()
    tree = git_tree(args.repo_root, args.tree_ish)
    check_layout_and_forbidden_paths(tree)
    check_manifest(tree, args.repo_root, args.tree_ish)
    print("SYSTEMKATALOG-MANIFEST-AND-PATH-CONTRACT: PASS")


if __name__ == "__main__":
    main()
