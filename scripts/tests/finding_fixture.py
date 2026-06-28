from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import finding_model  # noqa: E402

CLI_PATH = SCRIPTS / "validate-finding.py"
SPEC = importlib.util.spec_from_file_location("validate_finding", CLI_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load validate-finding.py")
CLI = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CLI
SPEC.loader.exec_module(CLI)


def base_finding(
    *,
    confirmed: bool = False,
    evidence: bool = True,
) -> dict[str, object]:
    value: dict[str, object] = {
        "schema": finding_model.FINDING_SCHEMA,
        "fingerprint": "",
        "rule_id": "repository.head.detached",
        "subject": {"kind": "repository", "id": "lenskit"},
        "scope": {"kind": "field", "value": "head_state"},
        "expectation_code": "repository-head-on-branch",
        "status": "confirmed" if confirmed else "hint",
        "severity": "medium",
        "confidence": "high",
        "summary": "Repository HEAD is detached",
        "observation": {"expected": "branch", "actual": "detached"},
        "observed_at": "2026-06-28T00:00:00Z",
        "evidence": [
            {
                "type": "repository_observation",
                "source": "collection.json#repositories/lenskit",
                "digest": {"algorithm": "sha256", "value": "a" * 64},
                "captured_at": "2026-06-28T00:00:00Z",
            }
        ]
        if evidence
        else [],
        "confirmation": {
            "actor_type": "human",
            "actor_id": "alex",
            "confirmed_at": "2026-06-28T00:01:00Z",
            "method": "human-review",
        }
        if confirmed
        else None,
        "next_check": "Return the repository to a named branch.",
    }
    value["fingerprint"] = finding_model.compute_fingerprint(value)
    return value
