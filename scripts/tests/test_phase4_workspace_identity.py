from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class WorkspaceIdentityContractTest(unittest.TestCase):
    def test_local_guard_rejects_stale_room_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            shutil.copytree(
                REPO_ROOT,
                root,
                ignore=shutil.ignore_patterns(
                    ".git", "__pycache__", ".pytest_cache"
                ),
            )
            workspace_path = root / ".agents/.config/workspace.json"
            workspace_path.parent.mkdir(parents=True, exist_ok=True)
            workspace_path.write_text(
                json.dumps(
                    {
                        "room": {
                            "slug": "steuerung",
                            "id": "vorzimmer-room",
                            "name": "Vorzimmer",
                            "type": "blank",
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts/check-cabinet-layout.py"),
                    "--mode",
                    "local",
                    str(root),
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "Workspace room.id='vorzimmer-room', "
                "erwartet 'steuerung-room'",
                result.stdout,
            )
            self.assertIn(
                "Workspace room.name='Vorzimmer', erwartet 'Steuerung'",
                result.stdout,
            )


if __name__ == "__main__":
    unittest.main()
