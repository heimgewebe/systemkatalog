from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "repo:systemkatalog": {
        "repository": "heimgewebe/systemkatalog",
        "commit": "e0e8ae9baf9d93e4792c6acb8e4dbee1e2a9cccd",
        "sha256": "644c819b59d75d03c28f5ba88fd498932949fbbae52f36d9d642f3c2fcfcd4ba",
    },
    "repo:schauwerk": {
        "repository": "heimgewebe/schauwerk",
        "commit": "a4aca3e22e2cb58f484e428901051309e65522c1",
        "sha256": "213cac171ec7eb6d3c49835da1c68b69fd84ea8081d7e93c440e2418a41a9db1",
    },
    "repo:commonworld": {
        "repository": "heimgewebe/commonworld",
        "commit": "c0c18c87e034120903f4e6aa7467822e4390e210",
        "sha256": "4a860538245912e8980f376dbb5c3499207f21f355fe2b1eb8f6647d6b0ef23f",
    },
}


class SourceBindingDriftCloseoutTests(unittest.TestCase):
    def test_reviewed_primary_sources_are_commit_and_content_bound(self) -> None:
        document = json.loads(
            (ROOT / "registry/ecosystem/source-bindings.v1.json").read_text(
                encoding="utf-8"
            )
        )
        systems = {item["system"]: item for item in document["systems"]}

        for system, expected in EXPECTED.items():
            with self.subTest(system=system):
                binding = systems[system]
                source = binding["source"]
                self.assertEqual(source["repository"], expected["repository"])
                self.assertEqual(source["commit"], expected["commit"])
                self.assertEqual(source["defaultBranch"], "main")
                self.assertEqual(source["locator"]["kind"], "file")
                self.assertEqual(source["locator"]["path"], "README.md")
                self.assertEqual(
                    source["locator"]["contentSha256"], expected["sha256"]
                )
                self.assertEqual(binding["reviewedAt"], "2026-07-17T16:59:07Z")


if __name__ == "__main__":
    unittest.main()
