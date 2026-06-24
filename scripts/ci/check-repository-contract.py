#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
import posixpath
from pathlib import Path

def get_git_tree(tree_ish: str, repo_root: Path) -> dict:
    cmd = ["git", "ls-tree", "-rz", "--full-tree", tree_ish]
    res = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=True)
    tree = {}
    for entry in res.stdout.split("\0"):
        if not entry:
            continue
        metadata, path = entry.split("\t", 1)
        mode, obj_type, obj_hash = metadata.split(" ", 2)
        tree[path] = {"mode": mode, "type": obj_type, "hash": obj_hash}
    return tree

def get_file_content(tree_ish: str, repo_root: Path, path: str) -> str:
    cmd = ["git", "show", f"{tree_ish}:{path}"]
    res = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=True)
    return res.stdout

def check_forbidden_paths(tree: dict):
    errors = []
    for path in tree:
        if path == "ops/env/runtime.env.example":
            continue

        parts = path.split("/")
        basename = parts[-1]

        if basename == ".cabinet.db" or basename.startswith(".cabinet.db-"):
            errors.append(f"database file: {path}")
            continue
        if ".cabinet.db" in parts or any(p.startswith(".cabinet.db-") for p in parts):
            errors.append(f"database file: {path}")
            continue

        if ".cabinet-state" in parts:
            errors.append(f"runtime state: {path}")
            continue

        for i in range(len(parts) - 1):
            if parts[i] == ".agents" and parts[i+1] in [".runtime", ".conversations", ".memory", ".messages", ".config"]:
                errors.append(f"agent runtime/config: {path}")
                break

        if path.endswith(".agents/.config.json"):
            errors.append(f"local agent config: {path}")
            continue

        if parts[0] == ".global-agents" or ".global-agents" in parts:
            errors.append(f"global agents: {path}")
            continue

        if basename in [".env", ".cabinet.env", "runtime.env"]:
            errors.append(f"env file: {path}")
            continue
        if basename.startswith(".env."):
            errors.append(f"env file: {path}")
            continue
        if basename.endswith(".pem") or basename.endswith(".key"):
            errors.append(f"key file: {path}")
            continue

    if errors:
        print("FAIL: forbidden tracked path:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)

def check_manifest(tree: dict, tree_ish: str, repo_root: Path):
    manifest_path = "ops/manifest.json"
    if manifest_path not in tree:
        print(f"FAIL: {manifest_path} fehlt im Git-Baum")
        sys.exit(1)

    content = get_file_content(tree_ish, repo_root, manifest_path)
    try:
        manifest = json.loads(content)
    except Exception as e:
        print(f"FAIL: manifest.json invalid json: {e}")
        sys.exit(1)

    if not isinstance(manifest, dict):
        print(f"FAIL: manifest: erwartet object, gefunden {type(manifest).__name__}")
        sys.exit(1)

    expected_top_level = {"schema", "cabinet_version", "repository_root", "templates", "executables", "symlinks", "local_only"}
    actual_top_level = set(manifest.keys())
    if actual_top_level != expected_top_level:
        print(f"FAIL: manifest top-level fields: gefunden={sorted(actual_top_level)}, erwartet={sorted(expected_top_level)}")
        sys.exit(1)

    for field in ["schema", "cabinet_version", "repository_root"]:
        if not isinstance(manifest[field], str):
            print(f"FAIL: manifest.{field}: erwartet string, gefunden {type(manifest[field]).__name__}")
            sys.exit(1)

    for field in ["templates", "executables", "symlinks", "local_only"]:
        if not isinstance(manifest[field], list):
            print(f"FAIL: manifest.{field}: erwartet list, gefunden {type(manifest[field]).__name__}")
            sys.exit(1)

    if manifest["schema"] != "cabinet.local-runtime.v1":
        print(f"FAIL: manifest.schema: gefunden={manifest['schema']}, erwartet=cabinet.local-runtime.v1")
        sys.exit(1)
    if manifest["cabinet_version"] != "0.4.4":
        print(f"FAIL: manifest.cabinet_version: gefunden={manifest['cabinet_version']}, erwartet=0.4.4")
        sys.exit(1)
    if manifest["repository_root"] != "~/repos/cabinet":
        print(f"FAIL: manifest.repository_root: gefunden={manifest['repository_root']}, erwartet=~/repos/cabinet")
        sys.exit(1)

    def validate_source(src):
        if not src:
            print("FAIL: manifest: source path is empty")
            sys.exit(1)
        if posixpath.isabs(src):
            print(f"FAIL: manifest: source path is absolute: {src}")
            sys.exit(1)
        if ".." in src.split("/"):
            print(f"FAIL: manifest: source path contains ..: {src}")
            sys.exit(1)
        if "" in src.split("/"):
            print(f"FAIL: manifest: source path contains empty segment: {src}")
            sys.exit(1)
        if src not in tree:
            print(f"FAIL: manifest: source not in git tree: {src}")
            sys.exit(1)
        if tree[src]["type"] != "blob":
            print(f"FAIL: manifest: source is not a regular file: {src}")
            sys.exit(1)

    def validate_list_entries(field_name, entries, expected_fields):
        sources = []
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                print(f"FAIL: manifest.{field_name}[{i}]: erwartet object, gefunden {type(entry).__name__}")
                sys.exit(1)
            actual_fields = set(entry.keys())
            if actual_fields != set(expected_fields):
                missing = sorted(set(expected_fields) - actual_fields)
                unexpected = sorted(actual_fields - set(expected_fields))
                if unexpected:
                    print(f"FAIL: manifest.{field_name}[{i}].fields: gefunden={sorted(actual_fields)}, erwartet={sorted(expected_fields)}")
                    sys.exit(1)
                else:
                    print(f"FAIL: manifest.{field_name}[{i}].fields: fehlend={missing}, unerwartet={unexpected}")
                    sys.exit(1)
            sources.append(entry.get("source"))

        dup_sources = [s for s in set(sources) if sources.count(s) > 1]
        if dup_sources:
            print(f"FAIL: manifest.{field_name}: duplicate source: {dup_sources[0]}")
            sys.exit(1)
        return sources

    expected_templates = {
        "ops/systemd/cabinet.service.tmpl": {"destination": "~/.config/systemd/user/cabinet.service", "mode": "0644", "git_mode": "100644"},
        "ops/systemd/cabinet.service.d/10-loopback-gate.conf.tmpl": {"destination": "~/.config/systemd/user/cabinet.service.d/10-loopback-gate.conf", "mode": "0644", "git_mode": "100644"}
    }
    actual_templates = manifest["templates"]
    actual_sources = validate_list_entries("templates", actual_templates, ["source", "destination", "mode"])

    if set(actual_sources) != set(expected_templates.keys()):
        missing = sorted(set(expected_templates.keys()) - set(actual_sources))
        unexpected = sorted(set(actual_sources) - set(expected_templates.keys()))
        print(f"FAIL: manifest.templates.sources: fehlend={missing}, unerwartet={unexpected}")
        sys.exit(1)

    for t in actual_templates:
        src = t["source"]
        validate_source(src)
        exp = expected_templates[src]
        if t["destination"] != exp["destination"]:
            print(f"FAIL: manifest.templates[{src}].destination: gefunden={t['destination']}, erwartet={exp['destination']}")
            sys.exit(1)
        if t["mode"] != exp["mode"]:
            print(f"FAIL: manifest.templates[{src}].mode: gefunden={t['mode']}, erwartet={exp['mode']}")
            sys.exit(1)
        git_mode = tree[src]["mode"]
        if git_mode != exp["git_mode"]:
            print(f"FAIL: manifest.templates[{src}].git_mode: gefunden={git_mode}, erwartet={exp['git_mode']}")
            sys.exit(1)

    expected_executables = {
        "ops/bin/cabinet": {"destination": "~/.local/bin/cabinet", "mode": "0755", "git_mode": "100755"},
        "ops/bin/cabinet-session": {"destination": "~/.local/bin/cabinet-session", "mode": "0755", "git_mode": "100755"},
        "ops/bin/cabinetctl": {"destination": "~/.local/bin/cabinetctl", "mode": "0755", "git_mode": "100755"},
        "ops/bin/cabinet-security-gate": {"destination": "~/.local/bin/cabinet-security-gate", "mode": "0755", "git_mode": "100755"}
    }
    actual_executables = manifest["executables"]
    actual_sources = validate_list_entries("executables", actual_executables, ["source", "destination", "mode"])

    if set(actual_sources) != set(expected_executables.keys()):
        missing = sorted(set(expected_executables.keys()) - set(actual_sources))
        unexpected = sorted(set(actual_sources) - set(expected_executables.keys()))
        print(f"FAIL: manifest.executables.sources: fehlend={missing}, unerwartet={unexpected}")
        sys.exit(1)

    for e in actual_executables:
        src = e["source"]
        validate_source(src)
        exp = expected_executables[src]
        if e["destination"] != exp["destination"]:
            print(f"FAIL: manifest.executables[{src}].destination: gefunden={e['destination']}, erwartet={exp['destination']}")
            sys.exit(1)
        if e["mode"] != exp["mode"]:
            print(f"FAIL: manifest.executables[{src}].mode: gefunden={e['mode']}, erwartet={exp['mode']}")
            sys.exit(1)
        git_mode = tree[src]["mode"]
        if git_mode != exp["git_mode"]:
            print(f"FAIL: manifest.executables[{src}].git_mode: gefunden={git_mode}, erwartet={exp['git_mode']}")
            sys.exit(1)

    expected_symlinks = {
        "scripts/cabinet-safe-export.sh": {"destination": "~/.local/bin/cabinet-safe-export", "git_mode": "100755"}
    }
    actual_symlinks = manifest["symlinks"]
    actual_sources = validate_list_entries("symlinks", actual_symlinks, ["source", "destination"])

    if set(actual_sources) != set(expected_symlinks.keys()):
        missing = sorted(set(expected_symlinks.keys()) - set(actual_sources))
        unexpected = sorted(set(actual_sources) - set(expected_symlinks.keys()))
        print(f"FAIL: manifest.symlinks.sources: fehlend={missing}, unerwartet={unexpected}")
        sys.exit(1)

    for s in actual_symlinks:
        src = s["source"]
        validate_source(src)
        exp = expected_symlinks[src]
        if s["destination"] != exp["destination"]:
            print(f"FAIL: manifest.symlinks[{src}].destination: gefunden={s['destination']}, erwartet={exp['destination']}")
            sys.exit(1)
        git_mode = tree[src]["mode"]
        if git_mode != exp["git_mode"]:
            print(f"FAIL: manifest.symlinks[{src}].git_mode: gefunden={git_mode}, erwartet={exp['git_mode']}")
            sys.exit(1)

    expected_local = [
        "~/.config/cabinet/runtime.env",
        "~/.local/state/cabinet/",
        "~/.cabinet/",
        ".cabinet-state/"
    ]
    actual_local = manifest["local_only"]
    for i, e in enumerate(actual_local):
        if not isinstance(e, str):
            print(f"FAIL: manifest.local_only[{i}]: erwartet string, gefunden {type(e).__name__}")
            sys.exit(1)

    if set(actual_local) != set(expected_local) or len(actual_local) != len(expected_local):
        print(f"FAIL: manifest.local_only: gefunden={sorted(actual_local)}, erwartet={sorted(expected_local)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--tree-ish", type=str, required=True)
    args = parser.parse_args()

    tree = get_git_tree(args.tree_ish, args.repo_root)
    check_forbidden_paths(tree)
    check_manifest(tree, args.tree_ish, args.repo_root)

    print("MANIFEST-AND-PATH-CONTRACT: PASS")

if __name__ == "__main__":
    main()
