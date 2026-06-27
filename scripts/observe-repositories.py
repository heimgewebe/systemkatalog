#!/usr/bin/env python3
"""Validate or run the Cabinet Repository State Observer v1."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any

import observer_guard
import repository_observer as observer

DEFAULT_POLICY = Path("policy/repository-observation.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate-policy")
    validate.add_argument("--repo-root", type=Path, default=Path.cwd())
    validate.add_argument("--policy", type=Path, default=DEFAULT_POLICY)

    collect = subparsers.add_parser("collect")
    collect.add_argument("--repo-root", type=Path, default=Path.cwd())
    collect.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    collect.add_argument("--source-root", type=Path, required=True)
    collect.add_argument("--observed-at", required=True)
    collect.add_argument("--output", type=Path)
    return parser


def collect_verified(
    repo_root: Path,
    policy_relative: Path,
    source_root: Path,
    observed_at: str,
) -> dict[str, Any]:
    policy = observer_guard.load_verified_policy(repo_root, policy_relative)
    body: dict[str, Any] = {
        "observed_at": observer.normalize_observed_at(observed_at),
        "path_scope": "source-root-relative",
        "policy_sha256": policy.sha256,
        "repositories": [
            observer.collect_entry(source_root, entry) for entry in policy.entries
        ],
        "schema": observer.OUTPUT_SCHEMA,
    }
    digest = hashlib.sha256(observer.canonical_json(body)).hexdigest()
    body["collection_id"] = f"repository-collection-{digest[:16]}"
    return body


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate-policy":
            policy = observer_guard.load_verified_policy(args.repo_root, args.policy)
            print("REPOSITORY-OBSERVER-POLICY: PASS")
            print(f"Approved repositories: {len(policy.entries)}")
            return 0

        value = collect_verified(
            args.repo_root,
            args.policy,
            args.source_root,
            args.observed_at,
        )
        rendered = observer.render_collection(value)
        if args.output is None:
            sys.stdout.buffer.write(rendered)
        else:
            observer.write_atomic(args.output, rendered)
            print("REPOSITORY-OBSERVER: PASS")
            print(f"Collection: {value['collection_id']}")
            print(f"Repositories: {len(value['repositories'])}")
            print(f"Output: {args.output}")
        return 0
    except (observer.CollectorError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
