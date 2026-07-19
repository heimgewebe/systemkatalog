#!/usr/bin/env python3
"""Apply source binding updates from a drift report proposal.

Ablauf:
1. Reviewgebundene Binding-Aktualisierung (dieses Skript).
2. Normale deterministische Renderer ausführen.
3. Separater Manifestcommit für gerenderte Artefakte.
"""

import argparse
import json
import sys
import hashlib
import re
from datetime import datetime
from pathlib import Path

def is_hex(s: str, length: int) -> bool:
    if not isinstance(s, str):
        return False
    return bool(re.fullmatch(r"[0-9a-f]{%d}" % length, s))

def is_iso8601(s: str) -> bool:
    if not isinstance(s, str):
        return False
    try:
        datetime.fromisoformat(s.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False

def validate_review(review: dict, expected_report_sha256: str) -> None:
    allowed_keys = {"schemaVersion", "kind", "decision", "reviewedAt", "reportSha256", "approvedChanges", "doesNotEstablish"}
    if not set(review.keys()).issubset(allowed_keys):
        raise ValueError(f"Unknown fields in review: {set(review.keys()) - allowed_keys}")

    if review.get("schemaVersion") != 1:
        raise ValueError("Invalid schemaVersion")
    if review.get("kind") != "system_catalog_source_binding_review":
        raise ValueError("Invalid kind")
    if review.get("decision") != "approved_source_binding_refresh":
        raise ValueError("Invalid decision")
    if not is_iso8601(review.get("reviewedAt")):
        raise ValueError("Invalid reviewedAt format")
    if review.get("reportSha256") != expected_report_sha256:
        raise ValueError("reportSha256 does not match the exact report file hash")
    
    changes = review.get("approvedChanges", [])
    if not isinstance(changes, list):
        raise ValueError("approvedChanges must be a list")
    
    seen_changes = set()
    for change in changes:
        c_keys = set(change.keys())
        c_allowed = {"repository", "system", "locatorKind", "path", "approvedCommit", "approvedSha256"}
        if not c_keys.issubset(c_allowed):
            raise ValueError(f"Unknown fields in change: {c_keys - c_allowed}")
            
        system = change.get("system")
        if system in seen_changes:
            raise ValueError(f"Duplicate change for system {system}")
        seen_changes.add(system)
        
        if not is_hex(change.get("approvedCommit"), 40):
            raise ValueError(f"Invalid approvedCommit for {system}")
        if not is_hex(change.get("approvedSha256"), 64):
            raise ValueError(f"Invalid approvedSha256 for {system}")

def apply_proposal(root: Path, report_path: Path, review_path: Path, write: bool) -> int:
    report_bytes = report_path.read_bytes()
    report_sha256 = hashlib.sha256(report_bytes).hexdigest()
    report = json.loads(report_bytes.decode("utf-8"))
    
    review_bytes = review_path.read_bytes()
    review = json.loads(review_bytes.decode("utf-8"))

    try:
        validate_review(review, report_sha256)
    except ValueError as e:
        print(f"Review validation failed: {e}")
        return 1

    if report.get("kind") != "system_catalog_drift_report":
        print("Invalid drift report: incorrect kind")
        return 1

    bindings_path = root / "registry/ecosystem/source-bindings.v1.json"
    bindings = json.loads(bindings_path.read_text(encoding="utf-8"))

    systems_by_name = {b["system"]: b for b in bindings["systems"]}
    review_changes_by_system = {c["system"]: c for c in review.get("approvedChanges", [])}
    
    updated_count = 0

    for change in report.get("changes", []):
        if change.get("kind") != "primary_source_changed":
            continue

        system = change.get("system")
        if system not in review_changes_by_system:
            print(f"Unreviewed change for {system}")
            return 1
            
        r_change = review_changes_by_system[system]
        
        if change.get("observedCommit") != r_change["approvedCommit"]:
            print(f"Observed commit does not match approved for {system}")
            return 1
        if change.get("observedSha256") != r_change["approvedSha256"]:
            print(f"Observed sha256 does not match approved for {system}")
            return 1
            
        if system not in systems_by_name:
            print(f"System {system} not found in bindings")
            return 1
            
        b = systems_by_name[system]
        locator = b["source"]["locator"]
        
        if b["source"]["repository"] != r_change.get("repository"):
            print(f"Repository mismatch for {system}")
            return 1
        if locator.get("kind") != r_change.get("locatorKind"):
            print(f"Locator kind mismatch for {system}")
            return 1
        
        b_path = locator.get("path")
        r_path = r_change.get("path")
        if b_path != r_path:
            print(f"Path mismatch for {system}")
            return 1
            
        if b["source"]["commit"] != change.get("boundCommit"):
            print(f"Stale binding (commit) for {system}: {b['source']['commit']} != {change.get('boundCommit')}")
            return 1
        if locator.get("contentSha256") != change.get("boundSha"):
            print(f"Stale binding (sha) for {system}")
            return 1

        if not is_hex(change.get("observedCommit"), 40):
            print(f"Malformed observedCommit for {system}")
            return 1
        if not is_hex(change.get("observedSha256"), 64):
            print(f"Malformed observedSha256 for {system}")
            return 1

        b["source"]["commit"] = change["observedCommit"]
        locator["contentSha256"] = change["observedSha256"]
        b["reviewedAt"] = review["reviewedAt"]
        updated_count += 1
        
    if "observedAt" in report:
        if not is_iso8601(report["observedAt"]):
            print("Invalid observedAt in report")
            return 1
        bindings["observedAt"] = report["observedAt"]

    if not write:
        print(f"Dry-run: would apply {updated_count} source binding updates.")
        return 0

    if updated_count > 0 or "observedAt" in report:
        encoded = json.dumps(bindings, indent=2) + "\n"
        temp_path = bindings_path.with_suffix(".json.tmp")
        try:
            temp_path.write_text(encoded, encoding="utf-8")
            temp_path.replace(bindings_path)
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            print(f"Failed to write bindings: {e}")
            return 1
            
        print(f"Successfully applied {updated_count} source binding updates.")
    else:
        print("No source binding updates applied.")
    return 0

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--write", action="store_true", help="Explicitly write changes")
    args = parser.parse_args()
    return apply_proposal(args.root, args.report, args.review, args.write)

if __name__ == "__main__":
    sys.exit(main())
