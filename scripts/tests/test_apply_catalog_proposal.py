import json
import pytest
from pathlib import Path
import tempfile
import hashlib
import sys

# Ensure scripts can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.apply_catalog_proposal import apply_proposal

@pytest.fixture
def workspace():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        registry_dir = root / "registry" / "ecosystem"
        registry_dir.mkdir(parents=True)
        
        bindings = {
            "schemaVersion": 1,
            "observedAt": "2026-07-19T10:00:00Z",
            "systems": [
                {
                    "system": "repo:systemkatalog",
                    "source": {
                        "repository": "heimgewebe/systemkatalog",
                        "commit": "1111111111111111111111111111111111111111",
                        "locator": {
                            "kind": "file",
                            "path": "README.md",
                            "contentSha256": "2222222222222222222222222222222222222222222222222222222222222222"
                        }
                    },
                    "reviewedAt": "2020-01-01T00:00:00Z"
                }
            ]
        }
        
        bindings_path = registry_dir / "source-bindings.v1.json"
        bindings_path.write_text(json.dumps(bindings))
        
        yield root

def create_report_review(root, report_data, review_data):
    report_path = root / "report.json"
    review_path = root / "review.json"
    
    report_bytes = json.dumps(report_data).encode("utf-8")
    report_path.write_bytes(report_bytes)
    report_sha = hashlib.sha256(report_bytes).hexdigest()
    
    if review_data is not None:
        if "reportSha256" not in review_data or review_data["reportSha256"] == "AUTO":
            review_data["reportSha256"] = report_sha
        review_path.write_text(json.dumps(review_data))
        
    return report_path, review_path

def valid_report():
    return {
        "kind": "system_catalog_drift_report",
        "observedAt": "2026-07-20T10:00:00Z",
        "changes": [
            {
                "kind": "primary_source_changed",
                "system": "repo:systemkatalog",
                "locatorKind": "file",
                "path": "README.md",
                "boundCommit": "1111111111111111111111111111111111111111",
                "boundSha": "2222222222222222222222222222222222222222222222222222222222222222",
                "observedCommit": "3333333333333333333333333333333333333333",
                "observedSha256": "4444444444444444444444444444444444444444444444444444444444444444"
            }
        ]
    }

def valid_review():
    return {
        "schemaVersion": 1,
        "kind": "system_catalog_source_binding_review",
        "decision": "approved_source_binding_refresh",
        "reviewedAt": "2026-07-20T11:00:00Z",
        "reportSha256": "AUTO",
        "approvedChanges": [
            {
                "repository": "heimgewebe/systemkatalog",
                "system": "repo:systemkatalog",
                "locatorKind": "file",
                "path": "README.md",
                "approvedCommit": "3333333333333333333333333333333333333333",
                "approvedSha256": "4444444444444444444444444444444444444444444444444444444444444444"
            }
        ],
        "doesNotEstablish": ["claim_truth"]
    }

def test_success_explicit_write(workspace):
    rep, rev = create_report_review(workspace, valid_report(), valid_review())
    assert apply_proposal(workspace, rep, rev, True) == 0
    b = json.loads((workspace / "registry/ecosystem/source-bindings.v1.json").read_text())
    sys_obj = b["systems"][0]
    assert sys_obj["source"]["commit"] == "3333333333333333333333333333333333333333"
    assert sys_obj["reviewedAt"] == "2026-07-20T11:00:00Z"
    assert b["observedAt"] == "2026-07-20T10:00:00Z"

def test_default_dry_run(workspace):
    rep, rev = create_report_review(workspace, valid_report(), valid_review())
    assert apply_proposal(workspace, rep, rev, False) == 0
    b = json.loads((workspace / "registry/ecosystem/source-bindings.v1.json").read_text())
    sys_obj = b["systems"][0]
    assert sys_obj["source"]["commit"] == "1111111111111111111111111111111111111111"
    assert b["observedAt"] == "2026-07-19T10:00:00Z"

def test_stale_binding(workspace):
    rep_data = valid_report()
    rep_data["changes"][0]["boundCommit"] = "9999999999999999999999999999999999999999"
    rep, rev = create_report_review(workspace, rep_data, valid_review())
    assert apply_proposal(workspace, rep, rev, True) == 1

def test_tampered_report_hash_mismatch(workspace):
    rep, rev = create_report_review(workspace, valid_report(), valid_review())
    # Modify report after review is generated
    rep.write_text(json.dumps({"kind": "system_catalog_drift_report", "changes": []}))
    assert apply_proposal(workspace, rep, rev, True) == 1

def test_tampered_review_unknown_field(workspace):
    rev_data = valid_review()
    rev_data["evil"] = "field"
    rep, rev = create_report_review(workspace, valid_report(), rev_data)
    assert apply_proposal(workspace, rep, rev, True) == 1

def test_malformed_hash(workspace):
    rev_data = valid_review()
    rev_data["approvedChanges"][0]["approvedCommit"] = "not-a-hash"
    rep, rev = create_report_review(workspace, valid_report(), rev_data)
    assert apply_proposal(workspace, rep, rev, True) == 1

def test_unreviewed_change(workspace):
    rep_data = valid_report()
    rep_data["changes"].append({
        "kind": "primary_source_changed",
        "system": "repo:other",
        "locatorKind": "file",
        "boundCommit": "1111111111111111111111111111111111111111",
        "boundSha": "2222222222222222222222222222222222222222222222222222222222222222",
        "observedCommit": "3333333333333333333333333333333333333333",
        "observedSha256": "4444444444444444444444444444444444444444444444444444444444444444"
    })
    rep, rev = create_report_review(workspace, rep_data, valid_review())
    assert apply_proposal(workspace, rep, rev, True) == 1

def test_locator_mismatch(workspace):
    rev_data = valid_review()
    rev_data["approvedChanges"][0]["locatorKind"] = "json_pointer"
    rep, rev = create_report_review(workspace, valid_report(), rev_data)
    assert apply_proposal(workspace, rep, rev, True) == 1

def test_repository_mismatch(workspace):
    rev_data = valid_review()
    rev_data["approvedChanges"][0]["repository"] = "wrong/repo"
    rep, rev = create_report_review(workspace, valid_report(), rev_data)
    assert apply_proposal(workspace, rep, rev, True) == 1
