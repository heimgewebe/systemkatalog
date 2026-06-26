from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from workspace_default_cutover import (
    CutoverError,
    apply_cutover,
    check_cutover,
    rollback_cutover,
    run_layout_validator,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


class RepositoryPhaseFourContractTests(unittest.TestCase):
    def test_versioned_default_is_steuerung(self) -> None:
        policy = json.loads(
            (REPO_ROOT / "policy/cabinet-layout.json").read_text(encoding="utf-8")
        )
        home = json.loads(
            (REPO_ROOT / ".home/home.json").read_text(encoding="utf-8")
        )
        self.assertEqual(policy["defaultRoom"], "steuerung")
        self.assertEqual(home["defaultRoom"], "steuerung")
        self.assertEqual(home["lastActiveRoom"], "steuerung")

    def test_vorzimmer_remains_a_real_room(self) -> None:
        policy = json.loads(
            (REPO_ROOT / "policy/cabinet-layout.json").read_text(encoding="utf-8")
        )
        manifest = REPO_ROOT / "vorzimmer/.cabinet"
        self.assertIn("vorzimmer", policy["rooms"])
        self.assertTrue(manifest.is_file())
        self.assertFalse(manifest.is_symlink())

    def test_blueprint_names_executable_cutover_contract(self) -> None:
        blueprint = (
            REPO_ROOT / "docs/blueprints/repository-oversight-layout-v1.md"
        ).read_text(encoding="utf-8")
        self.assertIn("scripts/workspace_default_cutover.py", blueprint)
        self.assertIn("~/.local/state/cabinet/workspace-cutovers", blueprint)
        self.assertIn("vor dem Merge", blueprint)
        self.assertNotIn("versionierte und technische Default", blueprint)


class PhaseFourLayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "repo"
        self.state = Path(self.temporary.name) / "state"
        self.root.mkdir()
        self._write_contract()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_contract(self) -> None:
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

    def _write_workspace(self, slug: str = "vorzimmer") -> Path:
        path = self.root / ".agents/.config/workspace.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "room": {"slug": slug, "label": "kept"},
                    "provider": {"name": "local"},
                    "unknown": [1, 2, 3],
                },
                ensure_ascii=False,
                indent=4,
            )
            + "\n",
            encoding="utf-8",
        )
        os.chmod(path, 0o640)
        return path

    def test_apply_preserves_unknown_fields_and_records_backup(self) -> None:
        workspace = self._write_workspace()
        original = workspace.read_bytes()
        backup_id = apply_cutover(
            self.root,
            self.state,
            validator=lambda _: None,
            now=datetime(2026, 6, 26, 20, 0, tzinfo=timezone.utc),
        )
        self.assertIsNotNone(backup_id)
        updated = json.loads(workspace.read_text(encoding="utf-8"))
        self.assertEqual(updated["room"]["slug"], "steuerung")
        self.assertEqual(updated["room"]["label"], "kept")
        self.assertEqual(updated["provider"], {"name": "local"})
        self.assertEqual(updated["unknown"], [1, 2, 3])
        self.assertEqual(stat.S_IMODE(os.lstat(workspace).st_mode), 0o640)

        backup_dir = self.state / str(backup_id)
        self.assertEqual((backup_dir / "workspace.json").read_bytes(), original)
        manifest = json.loads(
            (backup_dir / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["status"], "applied")
        self.assertEqual(manifest["previous_room"], "vorzimmer")
        self.assertEqual(manifest["target_room"], "steuerung")
        self.assertEqual(manifest["original_mode"], "0640")
        self.assertEqual(
            manifest["original_sha256"], hashlib.sha256(original).hexdigest()
        )
        self.assertEqual(stat.S_IMODE(os.lstat(backup_dir).st_mode), 0o700)
        self.assertEqual(
            stat.S_IMODE(os.lstat(backup_dir / "workspace.json").st_mode), 0o600
        )

    def test_apply_is_idempotent_when_already_aligned(self) -> None:
        self._write_workspace("steuerung")
        calls: list[Path] = []
        result = apply_cutover(
            self.root,
            self.state,
            validator=lambda root: calls.append(root),
        )
        self.assertIsNone(result)
        self.assertEqual(calls, [self.root])
        self.assertFalse(self.state.exists())

    def test_validator_failure_restores_exact_bytes_and_mode(self) -> None:
        workspace = self._write_workspace()
        original = workspace.read_bytes()

        def fail(_: Path) -> None:
            raise CutoverError("forced validator failure")

        with self.assertRaisesRegex(CutoverError, "original state restored"):
            apply_cutover(self.root, self.state, validator=fail)
        self.assertEqual(workspace.read_bytes(), original)
        self.assertEqual(stat.S_IMODE(os.lstat(workspace).st_mode), 0o640)
        backup_dir = next(self.state.iterdir())
        manifest = json.loads(
            (backup_dir / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["status"], "rolled-back")

    def test_invalid_workspace_json_creates_no_backup(self) -> None:
        workspace = self._write_workspace()
        workspace.write_text("{broken", encoding="utf-8")
        original = workspace.read_bytes()
        with self.assertRaisesRegex(CutoverError, "not valid UTF-8 JSON"):
            apply_cutover(self.root, self.state, validator=lambda _: None)
        self.assertEqual(workspace.read_bytes(), original)
        self.assertFalse(self.state.exists())

    def test_workspace_symlink_is_rejected(self) -> None:
        real = Path(self.temporary.name) / "workspace-real.json"
        real.write_text('{"room":{"slug":"vorzimmer"}}\n', encoding="utf-8")
        path = self.root / ".agents/.config/workspace.json"
        path.parent.mkdir(parents=True)
        path.symlink_to(real)
        with self.assertRaisesRegex(CutoverError, "may not contain symlinks"):
            apply_cutover(self.root, self.state, validator=lambda _: None)
        self.assertFalse(self.state.exists())

    def test_explicit_rollback_restores_exact_original(self) -> None:
        workspace = self._write_workspace()
        original = workspace.read_bytes()
        backup_id = apply_cutover(
            self.root,
            self.state,
            validator=lambda _: None,
        )
        assert backup_id is not None
        rollback_cutover(self.root, self.state, backup_id)
        self.assertEqual(workspace.read_bytes(), original)
        self.assertEqual(stat.S_IMODE(os.lstat(workspace).st_mode), 0o640)
        manifest = json.loads(
            (self.state / backup_id / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["status"], "rolled-back-explicitly")

    def test_check_rejects_drift_without_mutation(self) -> None:
        workspace = self._write_workspace()
        original = workspace.read_bytes()
        with self.assertRaisesRegex(CutoverError, "expected 'steuerung'"):
            check_cutover(self.root, validator=lambda _: None)
        self.assertEqual(workspace.read_bytes(), original)

    def test_state_root_inside_repository_is_rejected(self) -> None:
        self._write_workspace()
        with self.assertRaisesRegex(CutoverError, "outside the repository"):
            apply_cutover(
                self.root,
                self.root / ".cabinet-state/workspace-cutovers",
                validator=lambda _: None,
            )

    def test_real_validator_subprocess_is_invoked(self) -> None:
        self._write_workspace("steuerung")
        validator = self.root / "scripts/check-cabinet-layout.py"
        validator.parent.mkdir()
        validator.write_text(
            "import sys\nprint('CABINET-LAYOUT-GUARD: PASS')\nraise SystemExit(0)\n",
            encoding="utf-8",
        )
        run_layout_validator(self.root)

    def test_cabinetctl_applies_and_checks_workspace(self) -> None:
        workspace = self._write_workspace()
        scripts = self.root / "scripts"
        scripts.mkdir()
        (scripts / "workspace_default_cutover.py").write_bytes(
            (SCRIPT_DIR / "workspace_default_cutover.py").read_bytes()
        )
        (scripts / "check-cabinet-layout.py").write_text(
            "import sys\nprint('CABINET-LAYOUT-GUARD: PASS')\nraise SystemExit(0)\n",
            encoding="utf-8",
        )
        environment = os.environ.copy()
        environment.update(
            {
                "HOME": str(Path(self.temporary.name) / "home"),
                "CABINET_REPO_ROOT": str(self.root),
                "CABINET_WORKSPACE_CUTOVER_STATE_ROOT": str(self.state),
            }
        )
        control = REPO_ROOT / "ops/bin/cabinetctl"
        applied = subprocess.run(
            [str(control), "workspace-apply"],
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(applied.returncode, 0, applied.stdout)
        self.assertIn(
            "TARGET-PROOF: CABINET WORKSPACE DEFAULT IS STEUERUNG",
            applied.stdout,
        )
        self.assertEqual(
            json.loads(workspace.read_text(encoding="utf-8"))["room"]["slug"],
            "steuerung",
        )
        checked = subprocess.run(
            [str(control), "workspace-check"],
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(checked.returncode, 0, checked.stdout)

    def test_tampered_backup_is_rejected(self) -> None:
        self._write_workspace()
        backup_id = apply_cutover(
            self.root,
            self.state,
            validator=lambda _: None,
        )
        assert backup_id is not None
        backup = self.state / backup_id / "workspace.json"
        backup.write_bytes(backup.read_bytes() + b"tampered")
        with self.assertRaisesRegex(CutoverError, "hash does not match"):
            rollback_cutover(self.root, self.state, backup_id)

    def test_invalid_backup_id_is_rejected(self) -> None:
        self._write_workspace("steuerung")
        with self.assertRaisesRegex(CutoverError, "invalid backup id"):
            rollback_cutover(self.root, self.state, "../../escape")


if __name__ == "__main__":
    unittest.main()
