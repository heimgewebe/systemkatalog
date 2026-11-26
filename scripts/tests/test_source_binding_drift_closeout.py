from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "repo:systemkatalog": {
        "repository": "heimgewebe/systemkatalog",
        "commit": "42f9d709fb33c7e39ff3f84e70a7e04dbd5d7c3f",
        "sha256": "541160f1d97019e917e9ebdd3c53b4933ae4002abaf68b829fcacda034f8097d",
        "path": "README.md",
    },
    "repo:bureau": {
        "repository": "heimgewebe/bureau",
        "commit": "2b1295d40165fa3d5b3596d6f94ae8080b9fefa7",
        "sha256": "36a175d29ccd4571d04db092baf404bc6607872f28aef791fc5de492cf58016b",
        "path": "README.md",
    },
    "repo:commonthing": {
        "repository": "heimgewebe/commonthing",
        "commit": "1ad6f258b0d3634f338c72f7472ffd8ea4ec4042",
        "sha256": "23c632da37de6a3e7b3914365bff305315d8c35683386cfc204c68c624bdc9a3",
        "path": "architecture/commonthing-os.md",
    },
    "repo:repoground": {
        "repository": "heimgewebe/repoground",
        "commit": "e4bf307dd70f34be3f99f9817000cac1d62e6219",
        "sha256": "735f822843c13958a236cb65d5034b352829187ce8e10692cde091d5ba606974",
        "path": "README.md",
    },
    "repo:reposkop": {
        "repository": "heimgewebe/reposkop",
        "commit": "94cba1d55ed6e562701d0fda7ea117af3dfcc9e1",
        "sha256": "e17c6d4d6fdb14a74af50606c8bf7efad04d71ad524763fc5c4f8e02b68e1a29",
        "path": "README.md",
    },
    "repo:labor": {
        "repository": "heimgewebe/labor",
        "commit": "0ac4cbb64e2822cdd4d517dfd42ba6e49afb074e",
        "sha256": "b0a3fdc3ab3231ea963b6a0ee91c5c39db66f2f3b2dda7ae342435e5ef9f67da",
        "path": "README.md",
    },
    "repo:schauwerk": {
        "repository": "heimgewebe/schauwerk",
        "commit": "88cb97cdbf3c8bf317b7d44df409b2c5fc8b91f5",
        "sha256": "ab97ff76e55f92c921bb8ba89b8ecd09b7c52868642b7b9223fbf7ba9e5bb47a",
        "path": "README.md",
    },
    "repo:leitstand": {
        "repository": "heimgewebe/leitstand",
        "commit": "362dda6ac161bf275a38682d18998fc284eebe52",
        "sha256": "6fcc6537ade5c39ac1a9427d0a0da4423b836886d760835a458e731fd1450848",
        "path": "README.md",
    },
    "repo:metarepo": {
        "repository": "heimgewebe/metarepo",
        "commit": "f3524f9b040be957cfead5b80f7a683d0ea6df72",
        "sha256": "9f22e6414f841ed017589586d655fbcbe636c14a54ad02c09a7408c095fe9ffe",
        "path": "system/metarepo-role.v1.json",
    },
    "repo:wgx": {
        "repository": "heimgewebe/wgx",
        "commit": "254d4fa821f50b88362793c9ccd37082e2d0ed9d",
        "sha256": "c27918129cb962871cddfbb224d7d5bf9c3063af766dfbbe53231c1913879f05",
        "path": "README.md",
    },
    "repo:audio": {
        "repository": "heimgewebe/audio",
        "commit": "13fa9ac827f6012aded490b2590c6b39296beb91",
        "sha256": "75cf9eb19637e884f7aa9b15dd1de67eee8f9a7ec7016803b020836bd7a230aa",
        "path": "README.md",
    },
    "repo:semantAH": {
        "repository": "heimgewebe/semantAH",
        "commit": "d53000a909946a0381a8b365c4af7abd2456e8f6",
        "sha256": "c982af6c37a5fb316403724f7ce74ad7111e8f6b98f79d8dedadc49af55a4a2e",
        "path": "README.md",
    },
    "repo:heim-pc": {
        "repository": "heimgewebe/heim-pc",
        "commit": "8a8ba30aec53a732c1dc170f690b61773fc541c5",
        "sha256": "ff2b197f473cac119348c98d30090c3db40bd0acb164f2c649f3739e06141b17",
        "path": "manifest/operator-entry.v1.json",
    },
    "repo:commonworld": {
        "repository": "heimgewebe/commonworld",
        "commit": "43e773a9f118865d4177a763c2c6eae23db04487",
        "sha256": "898b89cfa9c52985f58004f37f96d195aca151230cb7a6cadc2b596581f26c34",
        "path": "README.md",
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
                self.assertEqual(source["locator"]["path"], expected["path"])
                self.assertEqual(
                    source["locator"]["contentSha256"], expected["sha256"]
                )
                self.assertIsInstance(binding["reviewedAt"], str)

        self.assertNotIn("repo:heimserver", systems)


if __name__ == "__main__":
    unittest.main()
