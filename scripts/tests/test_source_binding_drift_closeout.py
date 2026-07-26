from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "repo:systemkatalog": {
        "repository": "heimgewebe/systemkatalog",
        "commit": "1cda4ee29aacb39d99a5ab415611fff6da6c54aa",
        "sha256": "dbd566b6d8337f5238313386537eece250c9ad05f92c1a6cab780d77f1679457",
        "path": "README.md",
    },
    "repo:bureau": {
        "repository": "heimgewebe/bureau",
        "commit": "bfa44a83a76de053991b271883c738e87c854397",
        "sha256": "395960b2ca6a06310216123b7c311ad58fb0fa3adc55837fc26a649ea7c0358c",
        "path": "README.md",
    },
    "repo:weltgewebe": {
        "repository": "heimgewebe/weltgewebe",
        "commit": "9fda211859e0cdca9decf8e159ea6a630c4ea086",
        "sha256": "dadcfe97ed4ae110533f51f5c3d256ef5157fcf8578cbc5c2a3177f81f65ecd6",
        "path": "README.md",
    },
    "repo:repoground": {
        "repository": "heimgewebe/repoground",
        "commit": "40dd1088a642370c5a7cc0dfd19dbd59e6395a35",
        "sha256": "34de5eedbd3cc9c7340887c12c97e5241b8060c17f2ff90f9facc1e175f03d9c",
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
        "commit": "a85c14d0df83da61c68e43fe814a19d483f3f6f2",
        "sha256": "be0fd2f4b5c4829fab65e1e6c0f732827c79edf779f04ad3760b49bfc1c98655",
        "path": "README.md",
    },
    "repo:wgx": {
        "repository": "heimgewebe/wgx",
        "commit": "5c14e53674193446b8832eca6e312bcf58190248",
        "sha256": "b7103c3519a9470bfecf7c75b10ce837223ea6ce88b90289162063ae2e875357",
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
        "commit": "446dcef499147970ca3bc7abc1d95f551be8d279",
        "sha256": "480a23722c17a0ec8cfa67a69389ebba22a95f83ccac0631b6a2a3b44eeb03bb",
        "path": "manifest/operator-entry.v1.json",
    },
    "repo:commonworld": {
        "repository": "heimgewebe/commonworld",
        "commit": "47b6e82c6e359dda1b03737ab45de0dbbca8f794",
        "sha256": "1465617e273db98b25a3bc1390502a74a07581c3d0bd8c20e2e82a2b27fe9ed7",
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
