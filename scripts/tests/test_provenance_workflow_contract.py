from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from system_catalog_provenance import (  # noqa: E402
    PROVENANCE_TAG_NAMESPACE,
    provenance_tag_name,
)


class ProvenanceWorkflowContractTests(unittest.TestCase):
    def test_provenance_tag_name_is_commit_derived(self) -> None:
        commit = "a" * 40
        self.assertEqual(
            provenance_tag_name(commit),
            f"{PROVENANCE_TAG_NAMESPACE}/{commit}",
        )

    def test_primary_validation_workflows_fetch_and_bind_base_tags(self) -> None:
        for relative in (
            ".github/workflows/validate.yml",
            ".github/workflows/ecosystem-map.yml",
        ):
            with self.subTest(workflow=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                self.assertEqual(text.count("          fetch-tags: true\n"), 1)
                self.assertIn("PR_BASE_REPOSITORY:", text)
                self.assertIn("PR_BASE_SHA:", text)
                self.assertIn(
                    '"+refs/heads/$PR_BASE_REF:refs/remotes/origin/main"',
                    text,
                )
                self.assertIn(
                    'observed_base="$(git rev-parse refs/remotes/origin/main)"',
                    text,
                )
                self.assertIn(
                    'if [[ "$observed_base" != "$PR_BASE_SHA" ]]; then',
                    text,
                )


if __name__ == "__main__":
    unittest.main()
