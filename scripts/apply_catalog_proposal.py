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
import os
import tempfile
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

def validate_report(report: dict) -> None:
    allowed_keys = {"schemaVersion", "kind", "generatedAt", "materialDrift", "changeCount", "changes", "bureauCandidate", "proposal", "doesNotEstablish"}
    if set(report.keys()) != allowed_keys:
        raise ValueError(f"Report has missing or extra fields. Expected: {allowed_keys}, Got: {set(report.keys())}")

    if report.get("schemaVersion") != 1:
        raise ValueError("Invalid report schemaVersion")
    if report.get("kind") != "system_catalog_drift_report":
        raise ValueError("Invalid report kind")
    if not is_iso8601(report.get("generatedAt")):
        raise ValueError("Invalid generatedAt format")
    if not isinstance(report.get("materialDrift"), bool):
        raise ValueError("materialDrift must be a boolean")
    
    changes = report.get("changes")
    if not isinstance(changes, list) or len(changes) == 0:
        raise ValueError("changes must be a non-empty list")
    if report.get("changeCount") != len(changes):
        raise ValueError("changeCount does not match len(changes)")

    dne = report.get("doesNotEstablish")
    if not isinstance(dne, list) or len(dne) == 0:
        raise ValueError("doesNotEstablish must be a non-empty list")

    seen_systems = set()
    for change in changes:
        c_keys = set(change.keys())
        c_allowed = {"kind", "system", "repository", "locatorKind", "path", "boundCommit", "observedCommit", "boundSha256", "observedSha256"}
        if c_keys != c_allowed:
            raise ValueError(f"Change has missing or extra fields. Expected: {c_allowed}, Got: {c_keys}")

        if change.get("kind") != "primary_source_changed":
            raise ValueError(f"Unsupported change kind: {change.get('kind')}")

        system = change.get("system")
        if system in seen_systems:
            raise ValueError(f"Duplicate change for system {system} in report")
        seen_systems.add(system)

        for hash_field, length in [("boundCommit", 40), ("observedCommit", 40), ("boundSha256", 64), ("observedSha256", 64)]:
            if not is_hex(change.get(hash_field), length):
                raise ValueError(f"Invalid {hash_field} for {system} in report")

def validate_review(review: dict, expected_report_sha256: str) -> None:
    allowed_keys = {"schemaVersion", "kind", "decision", "reviewedAt", "reportSha256", "approvedChanges", "doesNotEstablish"}
    if set(review.keys()) != allowed_keys:
        raise ValueError(f"Review has missing or extra fields. Expected: {allowed_keys}, Got: {set(review.keys())}")

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
    
    dne = review.get("doesNotEstablish")
    if not isinstance(dne, list) or len(dne) == 0:
        raise ValueError("doesNotEstablish must be a non-empty list")
    required_dne = {"semantic_change", "merge", "deploy"}
    if not required_dne.issubset(set(dne)):
        raise ValueError(f"doesNotEstablish must exclude at least: {required_dne}")

    changes = review.get("approvedChanges")
    if not isinstance(changes, list) or len(changes) == 0:
        raise ValueError("approvedChanges must be a non-empty list")
    
    seen_systems = set()
    for change in changes:
        c_keys = set(change.keys())
        c_allowed = {"repository", "system", "locatorKind", "path", "boundCommit", "boundSha256", "observedCommit", "observedSha256"}
        if c_keys != c_allowed:
            raise ValueError(f"Review change has missing or extra fields. Expected: {c_allowed}, Got: {c_keys}")
            
        system = change.get("system")
        if system in seen_systems:
            raise ValueError(f"Duplicate change for system {system} in review")
        seen_systems.add(system)
        
        for hash_field, length in [("boundCommit", 40), ("observedCommit", 40), ("boundSha256", 64), ("observedSha256", 64)]:
            if not is_hex(change.get(hash_field), length):
                raise ValueError(f"Invalid {hash_field} for {system} in review")

def apply_proposal(root: Path, report_path: Path, review_path: Path, expected_report_sha256: str, expected_review_sha256: str, write: bool) -> int:
    try:
        report_bytes = report_path.read_bytes()
        review_bytes = review_path.read_bytes()
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return 1

    actual_report_sha256 = hashlib.sha256(report_bytes).hexdigest()
    if actual_report_sha256 != expected_report_sha256:
        print(f"Report hash mismatch. Expected: {expected_report_sha256}, Actual: {actual_report_sha256}")
        return 1

    actual_review_sha256 = hashlib.sha256(review_bytes).hexdigest()
    if actual_review_sha256 != expected_review_sha256:
        print(f"Review hash mismatch. Expected: {expected_review_sha256}, Actual: {actual_review_sha256}")
        return 1

    report = json.loads(report_bytes.decode("utf-8"))
    review = json.loads(review_bytes.decode("utf-8"))

    try:
        validate_report(report)
        validate_review(review, actual_report_sha256)
    except ValueError as e:
        print(f"Validation failed: {e}")
        return 1

    report_changes = report.get("changes", [])
    review_changes = review.get("approvedChanges", [])
    if len(report_changes) != len(review_changes):
        print(f"Mismatch in number of changes. Report: {len(report_changes)}, Review: {len(review_changes)}")
        return 1

    report_changes_by_system = {c["system"]: c for c in report_changes}
    review_changes_by_system = {c["system"]: c for c in review_changes}

    if set(report_changes_by_system.keys()) != set(review_changes_by_system.keys()):
        print("Mismatch in systems between report and review")
        return 1

    for system, r_change in report_changes_by_system.items():
        rev_change = review_changes_by_system[system]
        for field in ["repository", "locatorKind", "path", "boundCommit", "boundSha256", "observedCommit", "observedSha256"]:
            if r_change.get(field) != rev_change.get(field):
                print(f"Mismatch in field {field} for system {system} between report and review")
                return 1

    bindings_path = root / "registry/ecosystem/source-bindings.v1.json"
    try:
        bindings = json.loads(bindings_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Failed to read bindings: {e}")
        return 1

    systems_by_name = {b["system"]: b for b in bindings.get("systems", [])}
    
    updated_count = 0

    for change in report_changes:
        system = change.get("system")
        if system not in systems_by_name:
            print(f"System {system} not found in bindings")
            return 1
            
        b = systems_by_name[system]
        locator = b["source"]["locator"]
        
        if b["source"]["repository"] != change.get("repository"):
            print(f"Repository mismatch for {system}")
            return 1
        if locator.get("kind") != change.get("locatorKind"):
            print(f"Locator kind mismatch for {system}")
            return 1
        
        b_path = locator.get("path")
        if b_path != change.get("path"):
            print(f"Path mismatch for {system}")
            return 1
            
        if b["source"]["commit"] != change.get("boundCommit"):
            print(f"Stale binding (commit) for {system}: {b['source']['commit']} != {change.get('boundCommit')}")
            return 1
        if locator.get("contentSha256") != change.get("boundSha256"):
            print(f"Stale binding (sha) for {system}")
            return 1

        b["source"]["commit"] = change["observedCommit"]
        locator["contentSha256"] = change["observedSha256"]
        b["reviewedAt"] = review["reviewedAt"]
        updated_count += 1
        
    bindings["observedAt"] = report["generatedAt"]

    if not write:
        print(f"Dry-run: would apply {updated_count} source binding updates.")
        return 0

    if updated_count > 0:
        encoded = json.dumps(bindings, indent=2) + "\n"
        fd, temp_path_str = tempfile.mkstemp(dir=bindings_path.parent, prefix="source-bindings.v1.", suffix=".json.tmp")
        temp_path = Path(temp_path_str)
        try:
            with os.fdopen(fd, 'w', encoding="utf-8") as f:
                f.write(encoded)
            os.replace(temp_path, bindings_path)
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
    parser.add_argument("--expected-report-sha256", type=str, required=True, help="Expected SHA256 hash of the report file")
    parser.add_argument("--expected-review-sha256", type=str, required=True, help="Expected SHA256 hash of the review file")
    parser.add_argument("--write", action="store_true", help="Explicitly write changes")
    args = parser.parse_args()

    if not is_hex(args.expected_report_sha256, 64):
        print("--expected-report-sha256 must be a 64-character hex string")
        return 1
    if not is_hex(args.expected_review_sha256, 64):
        print("--expected-review-sha256 must be a 64-character hex string")
        return 1

    return apply_proposal(args.root, args.report, args.review, args.expected_report_sha256, args.expected_review_sha256, args.write)

if __name__ == "__main__":
    sys.exit(main())
