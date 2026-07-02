#!/usr/bin/env python3
"""Validate non-circular evidence and review dates for Project Card v1."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_DIR = Path("bestand/20 Projekte")
CARD_VALIDATOR = Path(__file__).resolve().with_name("check-project-cards.py")


class CardPolicyError(RuntimeError):
    """Raised when a project card violates evidence policy."""


def _load_cards(repo_root: Path) -> list[dict[str, Any]]:
    spec = importlib.util.spec_from_file_location("project_card_validator", CARD_VALIDATOR)
    if spec is None or spec.loader is None:
        raise CardPolicyError("cannot load project card validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    try:
        return module.validate_project_cards(repo_root)
    except module.ProjectCardError as exc:
        raise CardPolicyError(str(exc)) from exc


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def validate_policy(cards: list[dict[str, Any]], *, today: date | None = None) -> None:
    effective_today = _utc_today() if today is None else today
    for metadata in cards:
        card_id = metadata["id"]
        reviewed_at = date.fromisoformat(metadata["reviewed_at"])
        if reviewed_at > effective_today:
            raise CardPolicyError(
                f"project card {card_id!r} reviewed_at is after the validation date"
            )
        for raw_source in metadata["sources"]:
            if Path(raw_source).is_relative_to(PROJECT_DIR):
                raise CardPolicyError(
                    f"project card {card_id!r} cites the project-card directory: "
                    f"{raw_source}"
                )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument(
        "--as-of",
        type=date.fromisoformat,
        help="validation date in ISO format; defaults to the current UTC date",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cards = _load_cards(args.repo_root)
        validate_policy(cards, today=args.as_of)
    except (CardPolicyError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print("PROJECT-CARD-POLICY: PASS")
    print(f"Cards: {len(cards)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
