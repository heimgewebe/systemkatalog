from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "repo:systemkatalog": {
        "repository": "heimgewebe/systemkatalog",
        "commit": "2f1075b15ba79e8c7e435e7c40939dc89520922b",
        "sha256": "aef625fa6dd2b7256893768a7cc244362a5b6961943b01a9988d5edb56d6c8c4",
        "path": "README.md",
    },
    "repo:bureau": {
        "repository": "heimgewebe/bureau",
        "commit": "bfa44a83a76de053991b271883c738e87c854397",
        "sha256": "395960b2ca6a06310216123b7c311ad58fb0fa3adc55837fc26a649ea7c0358c",
        "path": "README.md",
    },
    "repo:commonthing": {
        "repository": "heimgewebe/commonthing",
        "commit": "322655285b520d04363e48487ae64d57264de573",
        "sha256": "a8afc647c472cb16aedd0a5f63a499db4c00676a6bdac800ded531855e26a65f",
        "path": "architecture/weltgewebe-os.md",
    },
    "repo:repoground": {
        "repository": "heimgewebe/repoground",
        "commit": "5548ca2d23a3d22ffe14fb1006363e4078e7c009",
        "sha256": "34de5eedbd3cc9c7340887c12c97e5241b8060c17f2ff90f9facc1e175f03d9c",
        "path": "README.md",
    },
    "repo:reposkop": {
        "repository": "heimgewebe/reposkop",
        "commit": "6c0847c2cbc6ee1d1cff52fc1b4a1c5ee17af487",
        "sha256": "a6b63794cd4ec41e30e979fd524349386d207673700c3bc4c369f3fa0619ae94",
        "path": "README.md",
    },
    "repo:vibe-lab": {
        "repository": "heimgewebe/vibe-lab",
        "commit": "63c3d533dad4d51775aba7746915b5c8c5086f42",
        "sha256": "0949d20b07df77ec2d1976b754258e837ef4b4a0b9a799daa4560f9413300bd8",
        "path": "README.md",
    },
    "repo:schauwerk": {
        "repository": "heimgewebe/schauwerk",
        "commit": "8bdc86d013de3dfde0cb8502291cc8cfee6faba0",
        "sha256": "72fc8e0d66600cefa4a3f01dfda9fc6e95f04067352216da6ffe79edfcd0e9ab",
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
        "commit": "a9d2899f5ed415cafaaa99e6951aeace04d2525a",
        "sha256": "c991fce442acaf58c6ee6ea604da06c0fab93b5175ba04ad0ebb71c0aa32d164",
        "path": "README.md",
    },
    "repo:semantAH": {
        "repository": "heimgewebe/semantAH",
        "commit": "d53000a909946a0381a8b365c4af7abd2456e8f6",
        "sha256": "c982af6c37a5fb316403724f7ce74ad7111e8f6b98f79d8dedadc49af55a4a2e",
        "path": "README.md",
    },
    "repo:sichter": {
        "repository": "heimgewebe/sichter",
        "commit": "f4359f0817d7db6b3f821bcdce7be12c18e561cc",
        "sha256": "4c2e3f51ef816373968b8857023446a0f7422615d22a9090cd7eeb608446f260",
        "path": "README.md",
    },
    "repo:heim-pc": {
        "repository": "heimgewebe/heim-pc",
        "commit": "671565d78b115cf2205d8a05bdeb709ac998f428",
        "sha256": "b8539db377f17808719f59efc33a63fae8fa2ca97f29f674f0824fc843033b94",
        "path": "manifest/operator-entry.v1.json",
    },
    "repo:heimserver": {
        "repository": "heimgewebe/heimserver",
        "commit": "4c4099e234a277b5ea48a28939f0ec4d08711f2a",
        "sha256": "1a6555386d9e641c17485fc76dc6ca00bae3956f78115a06ec10a63095dc02b2",
        "path": "repo.meta.yaml",
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


if __name__ == "__main__":
    unittest.main()
