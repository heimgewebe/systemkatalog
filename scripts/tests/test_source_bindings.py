from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from system_catalog_sources import _validate_local_source_bytes  # noqa: E402
from validate_system_catalog import validate  # noqa: E402


class SourceBindingTests(unittest.TestCase):
    def _copy_repository(self, directory: str) -> Path:
        target = Path(directory) / "repo"
        shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        return target

    def test_bindings_cover_all_systems_and_relations(self) -> None:
        result = validate(ROOT)
        self.assertEqual(result["sourceSystemBindings"], result["registrySystems"])
        self.assertEqual(result["sourceRelationBindings"], result["registryRelations"])
        self.assertEqual(result["freshnessRules"], 5)

    def test_private_repository_bindings_publish_no_commit(self) -> None:
        bindings = json.loads((ROOT / "registry/ecosystem/source-bindings.v1.json").read_text(encoding="utf-8"))
        scope = json.loads((ROOT / "registry/ecosystem/organization-scope.v1.json").read_text(encoding="utf-8"))
        private = {item["repository"] for item in scope["repositories"] if item["visibility"] == "private"}
        private_bindings = [item for item in bindings["systems"] if item["source"]["repository"] in private]
        self.assertTrue(private_bindings)
        for item in private_bindings:
            self.assertEqual(item["source"]["commit"], "redacted")
            self.assertEqual(item["source"]["locator"]["kind"], "private_repository_metadata")
            self.assertNotIn("path", item["source"]["locator"])

    def test_missing_system_binding_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = self._copy_repository(directory)
            path = target / "registry/ecosystem/source-bindings.v1.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["systems"].pop()
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source system coverage mismatch"):
                validate(target)

    def test_source_path_escape_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = self._copy_repository(directory)
            path = target / "registry/ecosystem/source-bindings.v1.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            item = next(value for value in data["systems"] if value["source"]["locator"]["kind"] == "file")
            item["source"]["locator"]["path"] = "../README.md"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must stay within its repository"):
                validate(target)

    def test_invalid_default_branch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = self._copy_repository(directory)
            path = target / "registry/ecosystem/source-bindings.v1.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["systems"][0]["source"]["defaultBranch"] = "bad branch"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "defaultBranch"):
                validate(target)

    def test_local_catalog_binding_must_match_git_bytes(self) -> None:
        bindings = json.loads((ROOT / "registry/ecosystem/source-bindings.v1.json").read_text(encoding="utf-8"))
        original = next(item["source"] for item in bindings["systems"] if item["system"] == "repo:systemkatalog")
        source = copy.deepcopy(original)
        source["locator"]["contentSha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "differs from the bound catalog bytes"):
            _validate_local_source_bytes(ROOT, source, "test source")

    def test_freshness_policy_cannot_enable_auto_merge(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = self._copy_repository(directory)
            path = target / "policy/freshness-slo.v1.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["autoMerge"] = True
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "proposal-only"):
                validate(target)


if __name__ == "__main__":
    unittest.main()
