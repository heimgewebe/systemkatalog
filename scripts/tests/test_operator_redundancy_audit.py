from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/validate_operator_redundancy_audit.py"
SPEC = importlib.util.spec_from_file_location("validate_operator_redundancy_audit", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class OperatorRedundancyAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = json.loads((ROOT / "registry/ecosystem/operator-redundancy-audit.v1.json").read_text(encoding="utf-8"))

    def test_repository_audit_is_valid(self) -> None:
        MODULE.validate(self.payload)

    def test_duplicate_evidence_ref_fails_closed(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["evidenceRefs"].append(copy.deepcopy(payload["evidenceRefs"][0]))
        with self.assertRaisesRegex(MODULE.AuditError, "duplicate evidence id"):
            MODULE.validate(payload)

    def test_missing_organ_fails_closed(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["organs"] = [organ for organ in payload["organs"] if organ["id"] != "steuerboard"]
        with self.assertRaisesRegex(MODULE.AuditError, "organ set mismatch"):
            MODULE.validate(payload)

    def test_duplicate_action_fails_closed(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["actions"].append(copy.deepcopy(payload["actions"][0]))
        with self.assertRaisesRegex(MODULE.AuditError, "duplicate action id"):
            MODULE.validate(payload)

    def test_confidence_outside_range_fails_closed(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["organs"][0]["confidence"] = 1.1
        with self.assertRaisesRegex(MODULE.AuditError, "outside 0..1"):
            MODULE.validate(payload)

    def test_shutdown_assessment_is_required(self) -> None:
        payload = copy.deepcopy(self.payload)
        del payload["organs"][0]["shutdown"]
        with self.assertRaisesRegex(MODULE.AuditError, "shutdown must be an object"):
            MODULE.validate(payload)


if __name__ == "__main__":
    unittest.main()
