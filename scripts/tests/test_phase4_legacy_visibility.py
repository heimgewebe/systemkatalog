from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / "scripts/check-cabinet-layout.py"


class LegacyRoomVisibilityContractTests(unittest.TestCase):
    def _load(self, relative: str) -> dict:
        return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))

    def test_only_three_manifests_are_active_rooms(self) -> None:
        navigation = self._load("policy/cabinet-navigation.json")
        policy = self._load("policy/cabinet-layout.json")
        active = set(navigation["activeRooms"])
        legacy = set(navigation["legacyCollections"])
        self.assertEqual(active, {"bestand", "pruefung", "steuerung"})
        self.assertEqual(set(policy["activeRooms"]), active)
        self.assertEqual(set(policy["rooms"]), active)
        for slug in active:
            manifest = (REPO_ROOT / slug / ".cabinet").read_text(encoding="utf-8")
            self.assertIn("kind: room", manifest)
        for slug in legacy:
            manifest = (REPO_ROOT / slug / ".cabinet").read_text(encoding="utf-8")
            self.assertIn("kind: legacy-collection", manifest)
            self.assertNotIn("kind: room", manifest)

    def test_registry_marks_active_manifests_retired(self) -> None:
        registry = self._load("docs/migrations/legacy-room-cutover-v1.json")
        self.assertEqual(registry["status"], "active-manifests-retired")
        self.assertEqual(registry["runtimeVerification"], "pending-local-smoke")

    def test_repository_layout_guard_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CHECKER), "--mode", "repository", str(REPO_ROOT)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Rooms: bestand, pruefung, steuerung", result.stdout)

    def _copy_repo(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name) / "repo"
        shutil.copytree(
            REPO_ROOT,
            root,
            ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
        )
        return temporary, root

    def test_reactivated_legacy_room_is_rejected(self) -> None:
        temporary, root = self._copy_repo()
        try:
            path = root / "vorzimmer/.cabinet"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "kind: legacy-collection", "kind: room"
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(root / "scripts/check-cabinet-layout.py"), "--mode", "repository", str(root)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Legacy-Sammlung ist als Room aktiv", result.stdout)
        finally:
            temporary.cleanup()

    def test_missing_legacy_collection_is_rejected(self) -> None:
        temporary, root = self._copy_repo()
        try:
            shutil.rmtree(root / "vorzimmer")
            result = subprocess.run(
                [sys.executable, str(root / "scripts/check-cabinet-layout.py"), "--mode", "repository", str(root)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Room-Menge weicht ab", result.stdout)
        finally:
            temporary.cleanup()

    def test_registry_drift_is_rejected(self) -> None:
        temporary, root = self._copy_repo()
        try:
            path = root / "docs/migrations/legacy-room-cutover-v1.json"
            registry = json.loads(path.read_text(encoding="utf-8"))
            registry["legacyCollections"]["labor"]["successor"] = "bestand"
            path.write_text(json.dumps(registry), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(root / "scripts/check-cabinet-layout.py"), "--mode", "repository", str(root)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Registry-Drift", result.stdout)
        finally:
            temporary.cleanup()


if __name__ == "__main__":
    unittest.main()
