from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import finding_model
from finding_fixture import base_finding


class FindingPathGuardTests(unittest.TestCase):
    def test_linked_input_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target.json"
            target.write_text(json.dumps(base_finding()), encoding="utf-8")
            linked = root / "finding.json"
            linked.symlink_to(target)
            with self.assertRaisesRegex(finding_model.FindingError, "symlinks"):
                finding_model.load_finding(linked)


if __name__ == "__main__":
    unittest.main()
