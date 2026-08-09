from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WGX_COMMIT = "254d4fa821f50b88362793c9ccd37082e2d0ed9d"


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class WgxCatalogRoleTests(unittest.TestCase):
    def test_wgx_role_is_profile_runner_not_shared_fleet_ci_authority(self) -> None:
        nodes = {node["id"]: node for node in load("registry/ecosystem/nodes.json")["nodes"]}
        wgx = nodes["repo:wgx"]
        self.assertEqual(
            wgx["purpose"],
            "WGX-v1 profile compatibility and repository-declared validation/task runner",
        )
        self.assertEqual(wgx["truthOwnership"], ["wgx_profile_runner_contract"])
        self.assertIn("fleet or policy truth", wgx["notResponsibleFor"])
        self.assertIn("git, worktree, process or deployment authority", wgx["notResponsibleFor"])
        self.assertIn("cross-repository code context", wgx["notResponsibleFor"])
        self.assertEqual(
            wgx["lifecycle"]["evidenceRefs"],
            [f"https://github.com/heimgewebe/wgx/blob/{WGX_COMMIT}/README.md"],
        )

        authorities = load("registry/ecosystem/authority-matrix.v1.json")["authorities"]
        by_domain = {item["domain"]: item for item in authorities}
        self.assertNotIn("shared_fleet_ci_checks", by_domain)
        self.assertEqual(
            by_domain["wgx_profile_runner_contract"],
            {"domain": "wgx_profile_runner_contract", "owner": "wgx", "projections": ["github_ci"]},
        )

        edge = next(
            item
            for item in load("registry/ecosystem/edges.json")["edges"]
            if item["from"] == "repo:wgx"
            and item["to"] == "service:ci"
            and item["type"] == "provides"
        )
        self.assertIn("repository-declared WGX profile validation", edge["meaning"])
        self.assertIn("target repositories own task declarations", edge["meaning"])
        self.assertIn("CI owns result truth", edge["meaning"])


if __name__ == "__main__":
    unittest.main()
