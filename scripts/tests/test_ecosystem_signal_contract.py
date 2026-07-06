"""Tests for the Cabinet ecosystem signal contract."""

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

from validate_ecosystem_signals import (  # noqa: E402
    CONTRACT_PATH,
    CONTRACT_VERSION,
    DOES_NOT_ESTABLISH,
    EFFECT_FLAGS,
    KIND,
    SCHEMA_PATH,
    EcosystemSignalError,
    load_signals,
    validate_signal,
)


def valid_signal() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": KIND,
        "contractVersion": CONTRACT_VERSION,
        "contractPath": CONTRACT_PATH,
        "schemaPath": SCHEMA_PATH,
        "id": "signal:github:heimgewebe.bureau:pr:95:state:5e832b320786",
        "observedAt": "2026-07-05T16:38:42Z",
        "sourceSystem": "github",
        "subject": "repo:bureau",
        "predicate": "github_pr_state",
        "object": "open",
        "evidence": [{
            "type": "github_pr",
            "ref": "heimgewebe/bureau#95",
            "url": "https://github.com/heimgewebe/bureau/pull/95",
            "observedHeadSha": "5e832b320786180bb142be565f0f7b58c6aa6e38",
        }],
        "freshness": {"basis": "observedAt", "maxAgeHours": 24},
        "confidence": 0.82,
        "effectFlags": {field: False for field in EFFECT_FLAGS},
        "doesNotEstablish": list(DOES_NOT_ESTABLISH),
    }


class EcosystemSignalContractTests(unittest.TestCase):
    def test_validate_signal_accepts_read_only_github_signal(self) -> None:
        validate_signal(valid_signal())

    def test_load_signals_accepts_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "signals.jsonl"
            path.write_text(json.dumps(valid_signal(), sort_keys=True) + "\n", encoding="utf-8")
            rows = load_signals(path)
        self.assertEqual(len(rows), 1)

    def test_effect_flag_true_blocks_signal(self) -> None:
        signal = valid_signal()
        signal["effectFlags"]["taskCreationAllowed"] = True
        with self.assertRaises(EcosystemSignalError):
            validate_signal(signal)

    def test_evidence_url_must_be_non_empty_string_when_present(self) -> None:
        for bad_url in ("", " https://github.com/heimgewebe/bureau/pull/95 ", 7):
            with self.subTest(bad_url=bad_url):
                signal = valid_signal()
                signal["evidence"][0]["url"] = bad_url
                with self.assertRaises(EcosystemSignalError):
                    validate_signal(signal)

    def test_evidence_url_may_be_absent(self) -> None:
        signal = valid_signal()
        del signal["evidence"][0]["url"]
        validate_signal(signal)

    def test_schema_constants_match_validator(self) -> None:
        schema = json.loads((ROOT / SCHEMA_PATH).read_text(encoding="utf-8"))
        properties = schema["properties"]
        self.assertEqual(properties["kind"]["const"], KIND)
        self.assertEqual(properties["contractVersion"]["const"], CONTRACT_VERSION)
        self.assertEqual(properties["contractPath"]["const"], CONTRACT_PATH)
        self.assertEqual(properties["schemaPath"]["const"], SCHEMA_PATH)
        for field in EFFECT_FLAGS:
            self.assertFalse(properties["effectFlags"]["properties"][field]["const"])


if __name__ == "__main__":
    unittest.main()
