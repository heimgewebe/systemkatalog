#!/usr/bin/env python3
"""Stable entrypoint for the Cabinet repository inventory generator."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_NAME = "scripts.repository_inventory"
IMPLEMENTATION_PATH = Path(__file__).resolve().with_name("repository_inventory.py")

implementation = sys.modules.get(MODULE_NAME)
if implementation is None:
    spec = importlib.util.spec_from_file_location(MODULE_NAME, IMPLEMENTATION_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load repository inventory implementation")
    implementation = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = implementation
    spec.loader.exec_module(implementation)

InventoryError = implementation.InventoryError
_atomic_write = implementation._atomic_write
_reference_path_components = implementation._reference_path_components
_split_table_cells = implementation._split_table_cells
main = implementation.main
os = implementation.os
parse_reference = implementation.parse_reference
read_worktree_reference = implementation.read_worktree_reference


if __name__ == "__main__":
    raise SystemExit(main())
