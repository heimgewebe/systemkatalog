"""Contract tests for CAB-ECO-001 ecosystem intelligence schemas."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas"

SCHEMA_FILES = {
    "ecosystem-node.v1.json": "ecosystem_node",
    "ecosystem-claim.v1.json": "ecosystem_claim",
    "task-candidate.v1.json": "task_candidate",
    "agent-briefing.v1.json": "agent_briefing",
}


def load_schema(name: str) -> dict[str, Any]:
    with (SCHEMA_DIR / name).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise AssertionError(f"{name} is not a JSON object")
    return value


class EcosystemIntelligenceSchemaTests(unittest.TestCase):
    def test_schema_files_exist_and_are_draft_2020_12_objects(self) -> None:
        for filename in SCHEMA_FILES:
            with self.subTest(filename=filename):
                schema = load_schema(filename)
                self.assertEqual(
                    schema["$schema"],
                    "https://json-schema.org/draft/2020-12/schema",
                )
                self.assertEqual(schema["type"], "object")
                self.assertIs(schema["additionalProperties"], False)
                self.assertIn("$id", schema)
                self.assertIn("required", schema)
                self.assertIn("properties", schema)
                self.assertIn("$defs", schema)

    def test_each_schema_has_strict_identity_fields(self) -> None:
        for filename, kind in SCHEMA_FILES.items():
            with self.subTest(filename=filename):
                schema = load_schema(filename)
                props = schema["properties"]
                self.assertEqual(props["schemaVersion"], {"const": 1})
                self.assertEqual(props["kind"], {"const": kind})
                self.assertIn("schemaVersion", schema["required"])
                self.assertIn("kind", schema["required"])
                self.assertIn("id", schema["required"])

    def test_claim_statuses_preserve_epistemic_boundaries(self) -> None:
        schema = load_schema("ecosystem-claim.v1.json")
        statuses = schema["properties"]["status"]["enum"]
        self.assertEqual(
            statuses,
            [
                "observed",
                "plausible",
                "evidenced",
                "validated",
                "canonical",
                "stale",
                "contradicted",
                "refuted",
            ],
        )
        self.assertIn("evidence", schema["required"])
        self.assertEqual(schema["properties"]["confidence"]["minimum"], 0)
        self.assertEqual(schema["properties"]["confidence"]["maximum"], 1)

    def test_task_candidate_keeps_approval_and_target_proof_explicit(self) -> None:
        schema = load_schema("task-candidate.v1.json")
        props = schema["properties"]
        self.assertIn("approved", props["status"]["enum"])
        self.assertIn("requiresHumanApproval", props)
        self.assertIn("targetProof", schema["required"])
        self.assertIn("acceptance", schema["required"])
        self.assertEqual(props["acceptance"]["minItems"], 1)

    def test_agent_briefing_requires_scope_non_goals_and_evidence(self) -> None:
        schema = load_schema("agent-briefing.v1.json")
        required = set(schema["required"])
        self.assertIn("allowedScope", required)
        self.assertIn("forbiddenChanges", required)
        self.assertIn("acceptanceTests", required)
        self.assertIn("evidenceRequired", required)
        self.assertIn("outputContract", required)
        self.assertEqual(schema["properties"]["allowedScope"]["minItems"], 1)
        self.assertEqual(schema["properties"]["forbiddenChanges"]["minItems"], 1)


if __name__ == "__main__":
    unittest.main()
