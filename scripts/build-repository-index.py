#!/usr/bin/env python3
"""Stable entrypoint for the Cabinet repository inventory generator."""

from repository_inventory import (
    InventoryError,
    _atomic_write,
    _reference_path_components,
    _split_table_cells,
    main,
    os,
    parse_reference,
    read_worktree_reference,
)


if __name__ == "__main__":
    raise SystemExit(main())
