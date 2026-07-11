from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("authority", ROOT / "scripts/validate_ecosystem_authority.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EcosystemAuthorityTests(unittest.TestCase):
    def test_authority_and_usage_contracts_are_valid(self) -> None:
        result = MODULE.validate()
        self.assertEqual(
            result,
            {
                "status": "valid",
                "authorityDomains": 14,
                "surfaces": 9,
                "publicRuntimeDetails": "redacted",
                "coverageLocations": 4,
                "consumerClasses": {
                    "declared_only": 1,
                    "runtime_observed": 4,
                    "source_integrated": 4,
                },
                "usageClasses": {
                    "automated_activity_only": 2,
                    "no_runtime_activity_observed": 5,
                    "recent_access_observed": 1,
                    "runtime_without_operator_access_signal": 1,
                },
            },
        )

    def test_single_canonical_map_is_registry_derived(self) -> None:
        matrix = MODULE._load(MODULE.MATRIX)
        self.assertEqual(matrix["canonicalMap"], "rendered/ecosystem-registry-map.mmd")
        self.assertTrue(all(view["authoritative"] is False for view in matrix["specializedViews"]))

    def test_public_usage_snapshot_is_explicitly_redacted_and_hash_bound(self) -> None:
        usage = MODULE._load(MODULE.USAGE)
        self.assertEqual(usage["visibility"], "public_redacted_summary")
        self.assertEqual(usage["snapshotRole"], "dated_decision_evidence_not_live_status")
        self.assertTrue(usage["privateEvidence"]["storedOutsideRepository"])
        self.assertTrue(usage["privateEvidence"]["publicDetailsRedacted"])
        self.assertRegex(usage["privateEvidence"]["evidenceSha256"], r"^[0-9a-f]{64}$")
        MODULE._validate_public_usage(usage)

    def test_invalid_observation_timestamp_fails_closed(self) -> None:
        usage = copy.deepcopy(MODULE._load(MODULE.USAGE))
        usage["observedAt"] = "latest"
        with self.assertRaisesRegex(ValueError, "UTC timestamp"):
            MODULE._validate_public_usage(usage)

    def test_private_runtime_keys_fail_closed(self) -> None:
        usage = copy.deepcopy(MODULE._load(MODULE.USAGE))
        usage["hosts"] = [{"id": "private-location"}]
        with self.assertRaisesRegex(ValueError, "private runtime keys"):
            MODULE._validate_public_usage(usage)

    def test_private_runtime_values_fail_closed(self) -> None:
        usage = copy.deepcopy(MODULE._load(MODULE.USAGE))
        usage["surfaces"][0]["usageSignal"] = "observed sensitive.service"
        with self.assertRaisesRegex(ValueError, "private runtime values"):
            MODULE._validate_public_usage(usage)

    def test_unknown_consumer_class_fails_closed(self) -> None:
        usage = copy.deepcopy(MODULE._load(MODULE.USAGE))
        usage["surfaces"][0]["consumerClass"] = "probably_active"
        with self.assertRaisesRegex(ValueError, "unknown consumer class"):
            MODULE._validate_public_usage(usage)

    def test_duplicate_surface_id_fails_closed(self) -> None:
        usage = copy.deepcopy(MODULE._load(MODULE.USAGE))
        usage["surfaces"][1]["id"] = usage["surfaces"][0]["id"]
        with self.assertRaisesRegex(ValueError, "surface ids must be unique"):
            MODULE._validate_public_usage(usage)

    def test_malformed_private_evidence_hash_fails_closed(self) -> None:
        usage = copy.deepcopy(MODULE._load(MODULE.USAGE))
        usage["privateEvidence"]["evidenceSha256"] = "not-a-hash"
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            MODULE._validate_public_usage(usage)

    def test_location_coverage_mismatch_fails_closed(self) -> None:
        usage = copy.deepcopy(MODULE._load(MODULE.USAGE))
        usage["coverageSummary"]["registeredLocations"] += 1
        with self.assertRaisesRegex(ValueError, "location count mismatch"):
            MODULE._validate_public_usage(usage)

    def test_missing_source_repository_fails_closed(self) -> None:
        usage = copy.deepcopy(MODULE._load(MODULE.USAGE))
        usage["sourceSnapshot"].pop("metarepo")
        with self.assertRaisesRegex(ValueError, "repository coverage mismatch"):
            MODULE._validate_public_usage(usage)

    def test_invalid_source_commit_fails_closed(self) -> None:
        usage = copy.deepcopy(MODULE._load(MODULE.USAGE))
        usage["sourceSnapshot"]["cabinet"] = "main"
        with self.assertRaisesRegex(ValueError, "full commit hashes"):
            MODULE._validate_public_usage(usage)


if __name__ == "__main__":
    unittest.main()
