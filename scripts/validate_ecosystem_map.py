#!/usr/bin/env python3
"""Validate the canonical Systemkatalog registry and generated map boundary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_system_catalog import validate as validate_system_catalog  # noqa: E402


def validate(root: Path = ROOT) -> dict[str, object]:
    catalog = validate_system_catalog(root.resolve())
    return {
        "status": "valid",
        "nodes": catalog["registrySystems"],
        "edges": catalog["registryRelations"],
        "stableClaims": catalog["stableClaims"],
        "authorityDomains": catalog["authorityDomains"],
        "projection": "non_authoritative_read_only",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True))
