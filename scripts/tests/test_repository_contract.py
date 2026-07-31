from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/ci/check-repository-contract.py"
SPEC = importlib.util.spec_from_file_location("systemkatalog_repository_contract", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RepositoryContractTests(unittest.TestCase):
    def test_generic_secret_and_temp_patterns_remain_allowed(self) -> None:
        MODULE.check_gitignore_text(".env\n.env.*\n*.pem\n*.log\n")

    def test_negated_legacy_pattern_remains_allowed(self) -> None:
        MODULE.check_gitignore_text("!.agents/\n!docs/archive/cabinet-era/**/.agents/\n")

    def test_cabinet_runtime_patterns_may_not_be_hidden(self) -> None:
        with self.assertRaisesRegex(SystemExit, "must remain visible"):
            MODULE.check_gitignore_text(".cabinet.db\n.cabinet-state/\n")

    def test_root_gitignore_requires_python_cache_hygiene(self) -> None:
        with self.assertRaisesRegex(SystemExit, "generated Python artifacts"):
            MODULE.check_root_gitignore_hygiene("*.log\n")

    def test_root_gitignore_accepts_python_cache_hygiene(self) -> None:
        MODULE.check_root_gitignore_hygiene("__pycache__/\n*.py[cod]\n")

    def test_root_gitignore_rejects_effective_python_cache_reinclusion(self) -> None:
        with self.assertRaisesRegex(SystemExit, "effectively ignore"):
            MODULE.check_root_gitignore_hygiene(
                "__pycache__/\n*.py[cod]\n!keep.pyc\n"
            )

    def test_nested_cabinet_directory_is_forbidden(self) -> None:
        tree = {
            "docs/archive/cabinet-era/README.md": {"type": "blob"},
            "foo/.cabinet/state.txt": {"type": "blob"},
        }
        with self.assertRaisesRegex(SystemExit, "legacy agent/runtime state"):
            MODULE.check_layout_and_forbidden_paths(tree)

    def test_all_active_nested_gitignore_files_are_discovered(self) -> None:
        tree = {
            ".gitignore": {"type": "blob"},
            "docs/.gitignore": {"type": "blob"},
            "docs/archive/cabinet-era/.gitignore": {"type": "blob"},
            "README.md": {"type": "blob"},
        }
        self.assertEqual(
            MODULE.active_gitignore_paths(tree),
            [".gitignore", "docs/.gitignore"],
        )

    def test_agent_runtime_patterns_may_not_be_hidden(self) -> None:
        with self.assertRaisesRegex(SystemExit, "must remain visible"):
            MODULE.check_gitignore_text("**/.agents/.runtime/\n.global-agents/\n")

    def test_validation_buffers_passing_unit_test_output(self) -> None:
        validation_script = (ROOT / "scripts/ci/validate-repository.sh").read_text()
        self.assertIn(
            "python3 -m unittest discover --buffer -s scripts/tests -p 'test_*.py'",
            validation_script,
        )


if __name__ == "__main__":
    unittest.main()
