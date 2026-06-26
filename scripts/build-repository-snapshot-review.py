#!/usr/bin/env python3
"""Stable entrypoint for the Cabinet repository snapshot review generator."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import repository_snapshot_review as implementation

InventoryError = implementation.InventoryError
RepositoryRecord = implementation.RepositoryRecord
SnapshotAssessment = implementation.SnapshotAssessment
assess_record = implementation.assess_record
build_assessments = implementation.build_assessments
priority_order = implementation.priority_order
render_review = implementation.render_review
render_lage = implementation.render_lage
main = implementation.main


if __name__ == "__main__":
    raise SystemExit(main())
