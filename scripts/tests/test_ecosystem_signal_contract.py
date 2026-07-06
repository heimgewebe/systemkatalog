"""Tests for the Cabinet ecosystem signal contract."""

from __future__ import annotations

import contextlib
import io
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
    main,
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
        "subject": "pr:heimgewebe/bureau#95",
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

    def test_load_signals_reports_invalid_json_line(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "signals.jsonl"
            path.write_text('{"broken"\n', encoding="utf-8")
            with self.assertRaisesRegex(EcosystemSignalError, "line 1: invalid JSON"):
                load_signals(path)

    def test_load_signals_reports_validation_line(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "signals.jsonl"
            signal = valid_signal()
            del signal["kind"]
            path.write_text(json.dumps(signal, sort_keys=True) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(EcosystemSignalError, "line 1: .*missing fields: kind"):
                load_signals(path)

    def test_effect_flag_true_blocks_signal(self) -> None:
        signal = valid_signal()
        signal["effectFlags"]["taskCreationAllowed"] = True
        with self.assertRaises(EcosystemSignalError):
            validate_signal(signal)

    def test_evidence_url_must_be_http_url_when_present(self) -> None:
        for bad_url in ("", " https://github.com/heimgewebe/bureau/pull/95 ", 7, "not-a-url", "ftp://example.invalid/x"):
            with self.subTest(bad_url=bad_url):
                signal = valid_signal()
                signal["evidence"][0]["url"] = bad_url
                with self.assertRaises(EcosystemSignalError):
                    validate_signal(signal)

    def test_evidence_url_may_be_absent(self) -> None:
        signal = valid_signal()
        del signal["evidence"][0]["url"]
        validate_signal(signal)

    def test_observed_at_requires_rfc3339_timestamp(self) -> None:
        valid_values = ["2026-07-05T16:38:42Z", "2026-07-05T16:38:42.123Z", "2026-07-05T16:38:42+02:00"]
        for observed_at in valid_values:
            with self.subTest(observed_at=observed_at):
                signal = valid_signal()
                signal["observedAt"] = observed_at
                validate_signal(signal)
        invalid_values = ["2026-07-05 16:38:42Z", "2026-07-05T16:38:42"]
        for observed_at in invalid_values:
            with self.subTest(observed_at=observed_at):
                signal = valid_signal()
                signal["observedAt"] = observed_at
                with self.assertRaises(EcosystemSignalError):
                    validate_signal(signal)

    def test_pr_predicates_require_pr_subject(self) -> None:
        signal = valid_signal()
        signal["subject"] = "repo:bureau"
        with self.assertRaisesRegex(EcosystemSignalError, "PR predicates"):
            validate_signal(signal)

    def test_top_level_field_errors_are_specific(self) -> None:
        missing = valid_signal()
        del missing["kind"]
        with self.assertRaisesRegex(EcosystemSignalError, "missing fields: kind"):
            validate_signal(missing)
        unexpected = valid_signal()
        unexpected["tags"] = []
        with self.assertRaisesRegex(EcosystemSignalError, "unexpected fields: tags"):
            validate_signal(unexpected)

    def test_fixture_source_requires_explicit_allowance(self) -> None:
        signal = valid_signal()
        signal["sourceSystem"] = "fixture"
        with self.assertRaisesRegex(EcosystemSignalError, "fixture sourceSystem"):
            validate_signal(signal)
        validate_signal(signal, allow_fixture_source=True)

    def test_does_not_establish_must_be_exact_unique_set(self) -> None:
        missing = valid_signal()
        missing["doesNotEstablish"] = list(DOES_NOT_ESTABLISH[:-1])
        with self.assertRaises(EcosystemSignalError):
            validate_signal(missing)
        duplicate = valid_signal()
        duplicate["doesNotEstablish"] = list(DOES_NOT_ESTABLISH[:-1]) + [DOES_NOT_ESTABLISH[0]]
        with self.assertRaises(EcosystemSignalError):
            validate_signal(duplicate)

    def test_schema_constants_match_validator(self) -> None:
        schema = json.loads((ROOT / SCHEMA_PATH).read_text(encoding="utf-8"))
        properties = schema["properties"]
        self.assertEqual(properties["kind"]["const"], KIND)
        self.assertEqual(properties["contractVersion"]["const"], CONTRACT_VERSION)
        self.assertEqual(properties["contractPath"]["const"], CONTRACT_PATH)
        self.assertEqual(properties["schemaPath"]["const"], SCHEMA_PATH)
        for field in EFFECT_FLAGS:
            self.assertFalse(properties["effectFlags"]["properties"][field]["const"])
        self.assertEqual(set(properties["doesNotEstablish"]["items"]["enum"]), set(DOES_NOT_ESTABLISH))
        self.assertEqual(properties["doesNotEstablish"]["minItems"], len(DOES_NOT_ESTABLISH))
        self.assertEqual(properties["doesNotEstablish"]["maxItems"], len(DOES_NOT_ESTABLISH))

    def test_cli_requires_input_path(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                main([])
        self.assertNotEqual(caught.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
