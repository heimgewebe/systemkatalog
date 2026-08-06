from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from systemkatalog_query import query, query_safe  # noqa: E402


class SystemkatalogQueryTests(unittest.TestCase):
    def _copy_catalog(self, destination: Path) -> Path:
        shutil.copytree(ROOT / "registry", destination / "registry")
        shutil.copytree(ROOT / "rendered", destination / "rendered")
        return destination

    def test_system_query_returns_source_binding_and_resilience(self) -> None:
        result = query(ROOT, "system", "grabowski")
        self.assertEqual(result["schemaVersion"], 2)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["result"]["system"]["id"], "repo:grabowski")
        self.assertEqual(
            result["result"]["sourceBinding"]["system"], "repo:grabowski"
        )
        self.assertEqual(
            result["result"]["resilience"]["criticality"], "foundational"
        )
        self.assertIn(
            "registry/ecosystem/resilience.v1.json", result["sourcePaths"]
        )
        self.assertNotIn("registry/ecosystem/edges.json", result["sourcePaths"])
        self.assertEqual(
            result["catalogRepository"], "heimgewebe/systemkatalog"
        )

    def test_source_evidence_is_query_specific_and_digest_bound(self) -> None:
        result = query(ROOT, "failure-domain", "host:heim-pc")
        self.assertEqual(
            result["sourcePaths"],
            ["registry/ecosystem/resilience.v1.json"],
        )
        evidence = result["sourceEvidence"][0]
        self.assertEqual(
            evidence["path"], "registry/ecosystem/resilience.v1.json"
        )
        self.assertEqual(len(evidence["sha256"]), 64)
        self.assertGreater(evidence["bytes"], 0)

    def test_catalog_identity_binds_artifact_manifest(self) -> None:
        result = query(ROOT, "system", "grabowski")
        manifest = result["catalogIdentity"]["artifactManifest"]
        self.assertEqual(
            manifest["path"],
            "rendered/ecosystem-map-artifact-manifest.json",
        )
        self.assertEqual(len(manifest["sha256"]), 64)
        self.assertEqual(
            manifest["source"]["repository"], "heimgewebe/systemkatalog"
        )
        self.assertEqual(len(manifest["source"]["commit"]), 40)

    def test_repository_query_exposes_target_criticality(self) -> None:
        result = query(ROOT, "repository", "weltgewebe")
        self.assertEqual(
            result["result"]["resilience"]["criticality"], "essential"
        )

    def test_truth_owner_uses_authority_matrix_and_node_truth_ownership(self) -> None:
        result = query(ROOT, "truth-owner", "agent_routing")
        self.assertEqual(result["result"]["authority"]["owner"], "grabowski")
        self.assertEqual(
            result["result"]["ownerSystem"]["id"], "repo:grabowski"
        )
        self.assertEqual(
            result["result"]["ownerResilience"]["criticality"],
            "foundational",
        )

    def test_authority_matrix_query_is_bounded(self) -> None:
        result = query(ROOT, "authority-matrix")
        self.assertTrue(result["result"]["authorities"])
        self.assertEqual(
            result["sourcePaths"],
            ["registry/ecosystem/authority-matrix.v1.json"],
        )

    def test_relations_preserve_source_bindings_and_add_optional_resilience(
        self,
    ) -> None:
        result = query(ROOT, "relations", "grabowski")
        relations = result["result"]["relations"]
        self.assertTrue(relations)
        self.assertTrue(
            all(
                item["sourceBinding"]["relation"]
                == {
                    "from": item["relation"]["from"],
                    "to": item["relation"]["to"],
                    "type": item["relation"]["type"],
                }
                for item in relations
            )
        )
        chronik = next(
            item
            for item in relations
            if item["relation"]["to"] == "repo:chronik"
        )
        self.assertEqual(
            chronik["resilience"]["coupling"], "asynchronous-durable"
        )
        self.assertEqual(chronik["resilience"]["failurePolicy"], "queue")
        self.assertEqual(
            chronik["resilience"]["recoveryModeRef"],
            "chronik-durable-outbox",
        )

    def test_failure_domain_query_returns_affected_systems_and_recovery_modes(
        self,
    ) -> None:
        result = query(ROOT, "failure-domain", "host:heim-pc")
        self.assertIn("repo:grabowski", result["result"]["systems"])
        self.assertIn(
            "grabowski-release-rollback", result["result"]["recoveryModes"]
        )

    def test_recovery_mode_query_preserves_epistemic_limits(self) -> None:
        result = query(
            ROOT, "recovery-mode", "grabowski-release-rollback"
        )
        self.assertEqual(
            result["result"]["independence"], "same-failure-domain"
        )
        self.assertIn(
            "automatic rollback authority",
            result["result"]["doesNotEstablish"],
        )

    def test_manifest_query_verifies_current_artifact_bytes(self) -> None:
        result = query(ROOT, "manifest")
        manifest = result["result"]["manifest"]
        checks = result["result"]["artifactChecks"]
        self.assertEqual(len(checks), manifest["artifactCount"])
        self.assertTrue(all(len(item["sha256"]) == 64 for item in checks))

    def test_missing_source_returns_typed_degraded_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_catalog(Path(temporary))
            (
                root / "registry/ecosystem/resilience.v1.json"
            ).unlink()
            result = query_safe(root, "system", "grabowski")
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["error"]["code"], "source_missing")
        self.assertEqual(
            result["error"]["path"],
            "registry/ecosystem/resilience.v1.json",
        )

    def test_malformed_source_returns_typed_degraded_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_catalog(Path(temporary))
            (root / "registry/ecosystem/nodes.json").write_text(
                "{", encoding="utf-8"
            )
            result = query_safe(root, "system", "grabowski")
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["error"]["code"], "source_malformed")

    def test_missing_source_binding_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_catalog(Path(temporary))
            path = root / "registry/ecosystem/source-bindings.v1.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["systems"] = [
                item
                for item in payload["systems"]
                if item["system"] != "repo:grabowski"
            ]
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            result = query_safe(root, "system", "grabowski")
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["error"]["code"], "inconsistent_catalog")
        self.assertEqual(
            result["error"]["details"]["relationship"], "source binding"
        )

    def test_missing_truth_owner_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_catalog(Path(temporary))
            path = root / "registry/ecosystem/nodes.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            grabowski = next(
                item
                for item in payload["nodes"]
                if item["id"] == "repo:grabowski"
            )
            grabowski["truthOwnership"].remove("agent_routing")
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            result = query_safe(root, "truth-owner", "agent_routing")
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["error"]["code"], "inconsistent_catalog")
        self.assertEqual(result["error"]["details"]["matchCount"], 0)

    def test_multiple_truth_owners_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_catalog(Path(temporary))
            path = root / "registry/ecosystem/nodes.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            bureau = next(
                item for item in payload["nodes"] if item["id"] == "repo:bureau"
            )
            bureau["truthOwnership"].append("agent_routing")
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            result = query_safe(root, "truth-owner", "agent_routing")
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["error"]["code"], "inconsistent_catalog")
        self.assertEqual(
            result["error"]["details"]["domain"], "agent_routing"
        )

    def test_manifest_drift_returns_typed_degraded_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_catalog(Path(temporary))
            path = root / "rendered/system-catalog.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "\nchanged\n",
                encoding="utf-8",
            )
            result = query_safe(root, "manifest")
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(
            result["error"]["code"], "artifact_manifest_stale"
        )
        self.assertTrue(result["error"]["details"]["mismatches"])

    def test_unknown_query_fails_with_machine_readable_error(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "systemkatalog_query.py"),
                "system",
                "does-not-exist",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 3)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["kind"], "system_catalog_query_error")
        self.assertEqual(payload["status"], "degraded")
        self.assertEqual(payload["error"]["code"], "query_not_unique")


if __name__ == "__main__":
    unittest.main()
