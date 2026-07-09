"""Tests for the Cabinet Maintenance Radar policy validator."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) in sys.path:
    sys.path.remove(str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS))

from validate_cabinet_maintenance_radar import (  # noqa: E402
    MaintenanceRadarPolicyError,
    validate_policy,
)

SOURCE_POLICY = ROOT / "policy" / "cabinet-maintenance-radar.json"
SOURCE_DOC = ROOT / "docs" / "blueprints" / "cabinet-maintenance-radar-v0.md"
SOURCE_BOUNDARY_DOC = ROOT / "docs" / "blueprints" / "cabinet-role-boundary-v1.md"


def write_fixture(root: Path) -> dict[str, Any]:
    policy = json.loads(SOURCE_POLICY.read_text(encoding="utf-8"))
    target_doc = root / policy["canonical_doc"]
    target_doc.parent.mkdir(parents=True, exist_ok=True)
    target_doc.write_text(SOURCE_DOC.read_text(encoding="utf-8"), encoding="utf-8")
    target_boundary_doc = root / policy["role_boundary_doc"]
    target_boundary_doc.parent.mkdir(parents=True, exist_ok=True)
    target_boundary_doc.write_text(SOURCE_BOUNDARY_DOC.read_text(encoding="utf-8"), encoding="utf-8")
    target_policy = root / "policy" / "cabinet-maintenance-radar.json"
    target_policy.parent.mkdir(parents=True, exist_ok=True)
    target_policy.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    return policy


def write_policy(root: Path, policy: dict[str, Any]) -> Path:
    path = root / "policy" / "cabinet-maintenance-radar.json"
    path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    return path


class CabinetMaintenanceRadarPolicyTests(unittest.TestCase):
    def test_repository_policy_is_valid(self) -> None:
        policy = validate_policy(ROOT, SOURCE_POLICY)
        self.assertEqual(policy["id"], "cabinet_maintenance_radar_v0")

    def test_fixture_policy_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = write_fixture(root)
            loaded = validate_policy(root, root / "policy" / "cabinet-maintenance-radar.json")

        self.assertEqual(loaded["allowed_scan_classes"], policy["allowed_scan_classes"])


    def test_rejects_missing_role_boundary_doc(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = write_fixture(root)
            (root / policy["role_boundary_doc"]).unlink()
            path = write_policy(root, policy)

            with self.assertRaises(MaintenanceRadarPolicyError):
                validate_policy(root, path)

    def test_rejects_removed_role_boundary_non_canon(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = write_fixture(root)
            policy["role_decision"]["cabinet_not_canon_for"].remove("task_queue")
            path = write_policy(root, policy)

            with self.assertRaises(MaintenanceRadarPolicyError):
                validate_policy(root, path)

    def test_rejects_wrong_default_tool_routing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = write_fixture(root)
            policy["default_tool_routing"]["task_queue"] = "cabinet"
            path = write_policy(root, policy)

            with self.assertRaises(MaintenanceRadarPolicyError):
                validate_policy(root, path)

    def test_rejects_replacement_gate_activation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = write_fixture(root)
            policy["replacement_gate"]["cabinet_replacement_allowed"] = True
            path = write_policy(root, policy)

            with self.assertRaises(MaintenanceRadarPolicyError):
                validate_policy(root, path)

    def test_rejects_removed_dashboard_non_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = write_fixture(root)
            policy["does_not_establish"].remove("dashboard_truth")
            path = write_policy(root, policy)

            with self.assertRaises(MaintenanceRadarPolicyError):
                validate_policy(root, path)

    def test_rejects_cabinet_dump_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = write_fixture(root)
            policy["cabinet_generates_repobrief_lenskit_dumps"] = True
            path = write_policy(root, policy)

            with self.assertRaises(MaintenanceRadarPolicyError):
                validate_policy(root, path)

    def test_rejects_removed_prohibition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = write_fixture(root)
            policy["prohibited_effects"].pop()
            path = write_policy(root, policy)

            with self.assertRaises(MaintenanceRadarPolicyError):
                validate_policy(root, path)

    def test_rejects_heimlern_direct_application(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = write_fixture(root)
            policy["heimlern_bridge"]["direct_policy_application_allowed"] = True
            path = write_policy(root, policy)

            with self.assertRaises(MaintenanceRadarPolicyError):
                validate_policy(root, path)

    def test_rejects_task_creation_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = write_fixture(root)
            policy["handoff"]["task_creation_allowed"] = True
            path = write_policy(root, policy)

            with self.assertRaises(MaintenanceRadarPolicyError):
                validate_policy(root, path)


if __name__ == "__main__":
    unittest.main()
