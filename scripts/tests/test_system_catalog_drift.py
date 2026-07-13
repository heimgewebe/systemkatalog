from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from system_catalog_drift import build_report  # noqa: E402


def matching_observations() -> dict:
    scope = json.loads((ROOT / "registry/ecosystem/organization-scope.v1.json").read_text(encoding="utf-8"))
    bindings = json.loads((ROOT / "registry/ecosystem/source-bindings.v1.json").read_text(encoding="utf-8"))
    repositories = [
        {
            "nameWithOwner": item["repository"],
            "isArchived": False,
            "isFork": False,
            "visibility": item["visibility"],
        }
        for item in scope["repositories"]
    ]
    observations = []
    for binding in bindings["systems"]:
        source = binding["source"]
        locator = source["locator"]
        if locator["kind"] == "json_pointer":
            continue
        observations.append({
            "repository": source["repository"],
            "commit": source["commit"],
            "defaultBranch": source["defaultBranch"],
            "locator": {"kind": locator["kind"], **({"path": locator["path"]} if "path" in locator else {})},
            "contentSha256": locator["contentSha256"],
        })
    return {"repositories": repositories, "observations": observations}


class SystemCatalogDriftTests(unittest.TestCase):
    def test_matching_observations_have_no_material_drift(self) -> None:
        report = build_report(ROOT, matching_observations())
        self.assertFalse(report["materialDrift"])
        self.assertEqual(report["changeCount"], 0)
        self.assertIsNone(report["bureauCandidate"])
        self.assertTrue(report["proposal"]["proposalOnly"])
        self.assertFalse(report["proposal"]["autoMerge"])

    def test_changed_primary_source_creates_bureau_candidate(self) -> None:
        data = matching_observations()
        file_observation = next(item for item in data["observations"] if item["locator"]["kind"] == "file")
        file_observation["contentSha256"] = "f" * 64
        report = build_report(ROOT, data)
        self.assertTrue(report["materialDrift"])
        self.assertIn("primary_source_changed", {item["kind"] for item in report["changes"]})
        self.assertEqual(report["bureauCandidate"]["candidateId"], "SYSTEMKATALOG-DRIFT-CLOSED-LOOP-V1")

    def test_new_repository_is_unclassified(self) -> None:
        data = matching_observations()
        data["repositories"].append({
            "nameWithOwner": "heimgewebe/new-system",
            "isArchived": False,
            "isFork": False,
            "visibility": "public",
        })
        report = build_report(ROOT, data)
        self.assertIn("repository_unclassified", {item["kind"] for item in report["changes"]})

    def test_default_branch_change_is_reported(self) -> None:
        data = matching_observations()
        data["observations"][0]["defaultBranch"] = "trunk"
        report = build_report(ROOT, data)
        self.assertIn("default_branch_changed", {item["kind"] for item in report["changes"]})


if __name__ == "__main__":
    unittest.main()
