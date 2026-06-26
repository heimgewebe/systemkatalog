"""Test import adapter for the adjacent repository inventory implementation."""

from scripts.repository_inventory import (
    InventoryError,
    _atomic_write,
    _open_parent_directory,
    _open_reference_file,
    _open_root_directory,
    _reference_path_components,
    _split_table_cells,
    main,
    os,
    parse_reference,
    read_worktree_reference,
)
