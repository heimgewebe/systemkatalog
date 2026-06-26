from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

IMPLEMENTATION_PATH = Path(__file__).resolve().parents[1] / "repository_snapshot_review.py"


def load_implementation():
    spec = importlib.util.spec_from_file_location(
        "snapshot_review_rollback_under_test",
        IMPLEMENTATION_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load snapshot review implementation")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


class SnapshotReviewWriteRollbackTests(unittest.TestCase):
    def test_second_write_failure_restores_first_output(self) -> None:
        module = load_implementation()
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            review = root / "review.md"
            lage = root / "lage.md"
            review.write_text("old review\n", encoding="utf-8")
            lage.write_text("old lage\n", encoding="utf-8")
            original_write = module.inventory._atomic_write
            calls = 0

            def flaky_write(path: Path, content: str) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("deliberate second write failure")
                original_write(path, content)

            with mock.patch.object(
                module.inventory,
                "_atomic_write",
                side_effect=flaky_write,
            ):
                with self.assertRaisesRegex(OSError, "second write failure"):
                    module._write_outputs(
                        {
                            review: "new review\n",
                            lage: "new lage\n",
                        }
                    )

            self.assertEqual(
                review.read_text(encoding="utf-8"),
                "old review\n",
            )
            self.assertEqual(
                lage.read_text(encoding="utf-8"),
                "old lage\n",
            )


if __name__ == "__main__":
    unittest.main()
