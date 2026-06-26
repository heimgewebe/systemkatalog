from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "build-repository-index.py"


def load_entrypoint_module():
    spec = importlib.util.spec_from_file_location(
        "repository_inventory_entrypoint_under_test", SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load repository inventory entrypoint")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


class RepositoryInventoryEntrypointTests(unittest.TestCase):
    def test_failed_implementation_load_is_removed_from_module_cache(self) -> None:
        entrypoint = load_entrypoint_module()
        module_name = "_cabinet_broken_repository_inventory_test"
        sys.modules.pop(module_name, None)

        with tempfile.TemporaryDirectory() as raw_root:
            implementation = Path(raw_root) / "broken_inventory.py"
            implementation.write_text(
                "raise RuntimeError('deliberate import failure')\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "deliberate import failure"):
                entrypoint._load_implementation(module_name, implementation)

        self.assertNotIn(module_name, sys.modules)


if __name__ == "__main__":
    unittest.main()
