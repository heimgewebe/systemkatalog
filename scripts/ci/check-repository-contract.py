#!/usr/bin/env python3
import argparse
import json
import posixpath
import subprocess
from pathlib import Path


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def git_tree(repo: Path, treeish: str) -> dict[str, dict[str, str]]:
    result = subprocess.run(
        ["git", "ls-tree", "-rz", "--full-tree", treeish],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
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


def check_forbidden_paths(tree: dict[str, dict[str, str]]) -> None:
    errors: list[str] = []
    for path in tree:
        parts = path.split("/")
        basename = parts[-1]
        if basename == ".cabinet.db" or basename.startswith(".cabinet.db-"):
            errors.append(f"database file: {path}")
        elif ".cabinet-state" in parts:
            errors.append(f"runtime state: {path}")
        elif any(parts[index] == ".agents" and parts[index + 1] in {".runtime", ".conversations", ".memory", ".messages", ".config"} for index in range(len(parts) - 1)):
            errors.append(f"agent runtime/config: {path}")
        elif path.endswith(".agents/.config.json"):
            errors.append(f"local agent config: {path}")
        elif ".global-agents" in parts:
            errors.append(f"global agents: {path}")
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
        fail(f"{path} fehlt im Git-Baum")
    manifest = json.loads(git_text(repo, treeish, path))
    expected_fields = {"schema", "runtime_version", "repository_root", "service", "executables", "retired_runtime_paths", "preserved_private_paths"}
    if set(manifest) != expected_fields:
        fail(f"manifest top-level fields: {sorted(manifest)} != {sorted(expected_fields)}")
    if manifest["schema"] != "heimgewebe.system-catalog-runtime.v1":
        fail(f"manifest.schema: {manifest['schema']}")
    if manifest["runtime_version"] != "1":
        fail(f"manifest.runtime_version: {manifest['runtime_version']}")
    if manifest["repository_root"] != "~/repos/cabinet":
        fail(f"manifest.repository_root: {manifest['repository_root']}")
    service = manifest["service"]
    expected_service = {
        "name": "heimgewebe-systemkatalog.service",
        "compatibility_alias": "cabinet.service",
        "template": "ops/systemd/heimgewebe-systemkatalog.service.tmpl",
        "destination": "~/.config/systemd/user/heimgewebe-systemkatalog.service",
        "bind": "127.0.0.1",
        "port": 4001,
        "mode": "0644",
    }
    if service != expected_service:
        fail(f"manifest.service mismatch: {service}")
    validate_source(tree, service["template"], "100644")
    expected_exec = {
        "ops/bin/heimgewebe-systemkatalog": ("~/.local/bin/heimgewebe-systemkatalog", "0755"),
        "ops/bin/systemkatalogctl": ("~/.local/bin/systemkatalogctl", "0755"),
    }
    actual_exec = {item.get("source"): (item.get("destination"), item.get("mode")) for item in manifest["executables"] if isinstance(item, dict)}
    if actual_exec != expected_exec:
        fail(f"manifest.executables mismatch: {actual_exec}")
    for source in expected_exec:
        validate_source(tree, source, "100755")
    expected_retired = {
        "~/.config/systemd/user/cabinet.service",
        "~/.config/systemd/user/cabinet.service.d/",
        "~/.local/bin/cabinet",
        "~/.local/bin/cabinet-session",
        "~/.local/bin/cabinetctl",
        "~/.local/bin/cabinet-security-gate",
    }
    if set(manifest["retired_runtime_paths"]) != expected_retired:
        fail("manifest.retired_runtime_paths mismatch")
    expected_preserved = {"~/.config/cabinet/", "~/.local/state/cabinet/", "~/.cabinet/", ".cabinet-state/"}
    if set(manifest["preserved_private_paths"]) != expected_preserved:
        fail("manifest.preserved_private_paths mismatch")
    forbidden_runtime_sources = {
        "ops/bin/cabinet",
        "ops/bin/cabinet-session",
        "ops/bin/cabinetctl",
        "ops/bin/cabinet-security-gate",
        "ops/systemd/cabinet.service.tmpl",
        "ops/systemd/cabinet.service.d/10-loopback-gate.conf.tmpl",
        "ops/patches/cabinet-v0.4.4-dark-default.py",
        "ops/env/runtime.env.example",
    }
    present = sorted(forbidden_runtime_sources & set(tree))
    if present:
        fail(f"retired external-app source still tracked: {present}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--tree-ish", required=True)
    args = parser.parse_args()
    tree = git_tree(args.repo_root, args.tree_ish)
    check_forbidden_paths(tree)
    check_manifest(tree, args.repo_root, args.tree_ish)
    print("MANIFEST-AND-PATH-CONTRACT: PASS")


if __name__ == "__main__":
    main()
