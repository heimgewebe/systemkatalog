from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class UnregisteredRoomContractTest(unittest.TestCase):
    def test_unregistered_top_level_room_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            shutil.copytree(
                REPO_ROOT,
                root,
                ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
            )
            room = root / "extra-room"
            room.mkdir()
            (room / ".cabinet").write_text(
                "schemaVersion: 1\n"
                'id: "extra-room"\n'
                'name: "Extra Room"\n'
                "kind: room\n"
                'version: "0.1.0"\n'
                "entry: index.md\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts/check-cabinet-layout.py"),
                    "--mode",
                    "repository",
                    str(root),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unerwarteter aktiver Top-Level-Room: extra-room", result.stdout)


if __name__ == "__main__":
    unittest.main()
