#!/usr/bin/env python3
"""Stable entrypoint for the Cabinet repository inventory generator."""

from repository_inventory import (
    InventoryError,
    _atomic_write,
    _open_parent_directory,
    _open_root_directory,
    _reference_path_components,
    _split_table_cells,
    main,
    os,
    parse_reference,
    read_worktree_reference,
)


class _Implementation:
    pass


_implementation = _Implementation()
_implementation._open_root_directory = _open_root_directory
_implementation._open_parent_directory = _open_parent_directory


if __name__ == "__main__":
    raise SystemExit(main())
