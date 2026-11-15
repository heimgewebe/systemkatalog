from __future__ import annotations

import copy
import hashlib
import json
import os
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

from system_catalog_drift import build_report  # noqa: E402


def matching_observations() -> dict:
    scope = json.loads((ROOT / "registry/ecosystem/organization-scope.v1.json").read_text(encoding="utf-8"))
    bindings = json.loads((ROOT / "registry/ecosystem/source-bindings.v1.json").read_text(encoding="utf-8"))
    repositories = [
        {
            "nameWithOwner": item["repository"],
            "isArchived": item["classification"] in {"archived_reference", "archived_excluded"},
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

    def test_primary_source_change_is_advisory_not_silent(self) -> None:
        data = matching_observations()
        original = next(row for row in data["observations"] if row["locator"]["kind"] == "file")
        original["contentSha256"] = "f" * 64
        report = build_report(ROOT, data)
        self.assertTrue(report["materialDrift"])
        self.assertEqual(report["changeCount"], 1)
        self.assertEqual(
            set(report),
            {
                "schemaVersion", "kind", "generatedAt", "materialDrift",
                "changeCount", "changes", "bureauCandidate", "proposal",
                "doesNotEstablish",
            },
        )
        self.assertIsNotNone(report["bureauCandidate"])
        with tempfile.TemporaryDirectory() as raw_tmp:
            path = Path(raw_tmp) / "observations.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable, str(SCRIPTS / "system_catalog_drift.py"),
                    "--root", str(ROOT),
                    "--github-observations", str(path),
                    "--check",
                ],
                cwd=ROOT, text=True, capture_output=True, check=False,
                env={**os.environ, "GITHUB_ACTIONS": "true"},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("::warning title=Systemkatalog source review::1", result.stderr)
            cli_report = json.loads(result.stdout)
            self.assertEqual(cli_report["changeCount"], 1)
            self.assertTrue(cli_report["materialDrift"])

    def test_structural_or_unobserved_source_drift_still_fails_check(self) -> None:
        for drift in ("unclassified", "source_missing", "branch_changed"):
            with self.subTest(drift=drift):
                data = matching_observations()
                if drift == "unclassified":
                    data["repositories"].append({
                        "nameWithOwner": "heimgewebe/unclassified",
                        "isArchived": False, "isFork": False, "visibility": "public",
                    })
                elif drift == "source_missing":
                    data["observations"].pop()
                else:
                    data["observations"][0]["defaultBranch"] = "trunk"
                report = build_report(ROOT, data)
                self.assertTrue(report["materialDrift"])
                self.assertGreater(report["changeCount"], 0)
                with tempfile.TemporaryDirectory() as raw_tmp:
                    path = Path(raw_tmp) / "observations.json"
                    path.write_text(json.dumps(data), encoding="utf-8")
                    result = subprocess.run(
                        [
                            sys.executable, str(SCRIPTS / "system_catalog_drift.py"),
                            "--root", str(ROOT),
                            "--github-observations", str(path),
                            "--check",
                        ],
                        cwd=ROOT, text=True, capture_output=True, check=False,
                    )
                    self.assertEqual(result.returncode, 2, result.stderr)

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

    def test_deleted_repository_reappearance_is_reported(self) -> None:
        data = matching_observations()
        data["repositories"].append(
            {
                "nameWithOwner": "heimgewebe/heimlern",
                "isArchived": False,
                "isFork": False,
                "visibility": "public",
            }
        )
        report = build_report(ROOT, data)
        self.assertIn(
            "repository_unclassified",
            {item["kind"] for item in report["changes"]},
        )

    def test_default_branch_change_is_reported(self) -> None:
        data = matching_observations()
        data["observations"][0]["defaultBranch"] = "trunk"
        report = build_report(ROOT, data)
        self.assertIn("default_branch_changed", {item["kind"] for item in report["changes"]})

    def test_canonical_drift_process_leaves_no_python_cache(self) -> None:
        coverage = json.loads(
            (ROOT / "registry/ecosystem/fleet-coverage.v1.json").read_text(encoding="utf-8")
        )
        lines = ["repos:"]
        for row in coverage["repositories"]:
            if row["membership"] not in {"fleet", "related"}:
                continue
            name = row["repository"].split("/", 1)[1]
            lines.append(f"  - name: {name}")
            if row["membership"] == "related":
                lines.append("    status: related")
        archived_names = {
            row["repository"].split("/", 1)[1]
            for row in coverage["repositories"]
            if row["membership"] == "archived-reference"
        }
        for item in coverage["sourceExclusions"]:
            lines.append(f"  - name: {item['name']}")
            if item["name"] in archived_names:
                lines.append("    status: archived-reference")
            lines.append("    fleet: false")
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            shutil.copytree(ROOT / "scripts", tmp / "scripts", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            shutil.copytree(ROOT / "registry", tmp / "registry")
            observations = tmp / "observations.json"
            observations.write_text(
                json.dumps(matching_observations(), ensure_ascii=False), encoding="utf-8"
            )
            fleet = tmp / "repos.yml"
            fleet.write_text("\n".join(lines) + "\n", encoding="utf-8")
            fixture_coverage_path = tmp / "registry/ecosystem/fleet-coverage.v1.json"
            fixture_coverage = json.loads(
                fixture_coverage_path.read_text(encoding="utf-8")
            )
            fixture_coverage["membershipAuthority"]["contentSha256"] = (
                hashlib.sha256(fleet.read_bytes()).hexdigest()
            )
            fixture_coverage_path.write_text(
                json.dumps(fixture_coverage, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report = tmp / "report.json"
            env = os.environ.copy()
            env.pop("PYTHONDONTWRITEBYTECODE", None)
            env.pop("PYTHONPYCACHEPREFIX", None)
            result = subprocess.run(
                [
                    sys.executable,
                    str(tmp / "scripts/system_catalog_drift.py"),
                    "--root",
                    str(tmp),
                    "--github-observations",
                    str(observations),
                    "--fleet-file",
                    str(fleet),
                    "--output",
                    str(report),
                    "--check",
                ],
                cwd=tmp,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            diagnostic = result.stdout + result.stderr
            if report.exists():
                diagnostic += report.read_text(encoding="utf-8")
            self.assertEqual(result.returncode, 0, diagnostic)
            self.assertFalse(
                list((tmp / "scripts").rglob("__pycache__")),
                "canonical drift process created Python bytecode cache",
            )


if __name__ == "__main__":
    unittest.main()