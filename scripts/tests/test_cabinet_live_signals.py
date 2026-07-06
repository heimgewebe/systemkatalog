"""Tests for the Cabinet live signal producer."""

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

from validate_ecosystem_signals import validate_signal  # noqa: E402
from write_cabinet_live_signals import build_rows, source_rows, write_jsonl  # noqa: E402


def registry_payload(status: str = "observed") -> dict[str, Any]:
    return {
        "sources": [
            {
                "id": "external-dump:repobrief",
                "artifactFamily": "repobrief",
                "observation": {
                    "status": status,
                    "latestManifestPath": "external/repobrief/cabinet/main/manifest.json" if status == "observed" else "",
                    "latestManifestGeneratedAt": "2026-07-06T16:01:58Z" if status == "observed" else "",
                },
            }
        ]
    }


class CabinetLiveSignalTests(unittest.TestCase):
    def test_source_rows_emit_valid_observed_external_dump_signal(self) -> None:
        rows = source_rows(registry_payload(), "2026-07-06T16:10:00Z")
        self.assertEqual(len(rows), 1)
        validate_signal(rows[0])
        self.assertEqual(rows[0]["predicate"], "external_dump_manifest_status")
        self.assertEqual(rows[0]["object"], "observed")
        self.assertEqual(rows[0]["effectFlags"]["dumpGenerationAllowed"], False)

    def test_write_jsonl_round_trips_rows(self) -> None:
        rows = source_rows(registry_payload(), "2026-07-06T16:10:00Z")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "signals.jsonl"
            write_jsonl(rows, path)
            loaded = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(loaded, rows)

    def test_build_rows_against_repository_outputs_valid_signals(self) -> None:
        rows = build_rows(ROOT, "2026-07-06T16:10:00Z")
        self.assertGreaterEqual(len(rows), 3)
        for row in rows:
            validate_signal(row)
        predicates = {row["predicate"] for row in rows}
        self.assertIn("external_dump_manifest_status", predicates)
        self.assertIn("cabinet_maintenance_report_status", predicates)


if __name__ == "__main__":
    unittest.main()
