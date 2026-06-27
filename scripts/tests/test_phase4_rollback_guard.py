from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from workspace_default_cutover import (
    CutoverError,
    apply_cutover,
    rollback_cutover,
)


class PhaseFourRollbackGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "repo"
        self.state = Path(self.temporary.name) / "state"
        self.root.mkdir()
        (self.root / "policy").mkdir()
        (self.root / ".home").mkdir()
        (self.root / "steuerung").mkdir()
        (self.root / "steuerung/.cabinet").write_text(
            "schemaVersion: 1\nkind: room\n", encoding="utf-8"
        )
        (self.root / "policy/cabinet-layout.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "defaultRoom": "steuerung",
                    "rooms": {"steuerung": {"id": "steuerung-room"}},
                }
            ),
            encoding="utf-8",
        )
        (self.root / ".home/home.json").write_text(
            json.dumps(
                {
                    "defaultRoom": "steuerung",
                    "lastActiveRoom": "steuerung",
                    "schemaVersion": 1,
                }
            ),
            encoding="utf-8",
        )
        self.workspace = self.root / ".agents/.config/workspace.json"
        self.workspace.parent.mkdir(parents=True)
        self.workspace.write_text(
            json.dumps(
                {
                    "room": {"slug": "vorzimmer"},
                    "userSetting": "before-cutover",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        os.chmod(self.workspace, 0o640)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_rollback_refuses_to_clobber_post_cutover_changes(self) -> None:
        backup_id = apply_cutover(
            self.root,
            self.state,
            validator=lambda _: None,
        )
        assert backup_id is not None
        changed = json.loads(self.workspace.read_text(encoding="utf-8"))
        changed["userSetting"] = "changed-after-cutover"
        self.workspace.write_text(json.dumps(changed, indent=2) + "\n", encoding="utf-8")
        os.chmod(self.workspace, 0o640)
        before = self.workspace.read_bytes()

        with self.assertRaisesRegex(CutoverError, "refusing rollback to avoid data loss"):
            rollback_cutover(self.root, self.state, backup_id)

        self.assertEqual(self.workspace.read_bytes(), before)
        manifest = json.loads(
            (self.state / backup_id / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["status"], "applied")

    def test_existing_overpermissive_state_root_is_rejected_without_chmod(self) -> None:
        self.state.mkdir(mode=0o755)
        os.chmod(self.state, 0o755)

        with self.assertRaisesRegex(CutoverError, "permissions are too broad"):
            apply_cutover(self.root, self.state, validator=lambda _: None)

        self.assertEqual(stat.S_IMODE(os.lstat(self.state).st_mode), 0o755)
        self.assertEqual(
            json.loads(self.workspace.read_text(encoding="utf-8"))["room"]["slug"],
            "vorzimmer",
        )


if __name__ == "__main__":
    unittest.main()
