#!/usr/bin/env python3
"""Stable entrypoint for the Cabinet repository inventory generator."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

MODULE_NAME = "scripts.repository_inventory"
IMPLEMENTATION_PATH = Path(__file__).resolve().with_name("repository_inventory.py")


def _load_implementation(module_name: str, implementation_path: Path) -> ModuleType:
    """Load one implementation module without caching a failed partial import."""
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing

    spec = importlib.util.spec_from_file_location(module_name, implementation_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load repository inventory implementation")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


implementation = _load_implementation(MODULE_NAME, IMPLEMENTATION_PATH)

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
