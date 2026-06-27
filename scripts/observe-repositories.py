#!/usr/bin/env python3
"""Validate or run the Cabinet Repository State Observer v1."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate-policy":
            policy = observer.load_policy(args.repo_root, args.policy)
            print("REPOSITORY-OBSERVER-POLICY: PASS")
            print(f"Approved repositories: {len(policy.entries)}")
            return 0

        value = observer.collect(
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
