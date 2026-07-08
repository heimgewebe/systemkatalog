from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from import_rlens_repository_reference import (  # noqa: E402
    DOES_NOT_ESTABLISH,
    RlensReferenceError,
    build_agent_briefing,
    read_bundle_metadata,
    render_reference,
)


class RlensRepositoryReferenceImportTests(unittest.TestCase):
    def manifest(self, root: Path, **updates: object) -> Path:
        payload = {
            "kind": "repolens.bundle.manifest",
            "run_id": "lenskit-max-260708-1200",
            "created_at": "2026-07-08T12:00:00Z",
            "generator": {
                "name": "repolens",
                "runtime": {"git_commit": "a" * 40, "git_dirty": False},
            },
            "artifacts": [],
        }
        payload.update(updates)
        path = root / "lenskit-max-260708-1200_merge.bundle.manifest.json"
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        return path

    def test_renders_dated_reference_with_bundle_stem_freshness_health_and_non_claims(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.manifest(root)
            health = root / "health.json"
            health.write_text(json.dumps({"status": "pass"}), encoding="utf-8")

            metadata = read_bundle_metadata(manifest, repository="lenskit", health_path=health)
            rendered = render_reference(metadata)

        self.assertIn("| Bundle-Stem | `lenskit-max-260708-1200` |", rendered)
        self.assertIn("| Freshness-Klasse | `dated_snapshot` |", rendered)
        self.assertIn("| Health | `pass` |", rendered)
        self.assertIn("| Live-Zustand behauptet | `false` |", rendered)
        for item in DOES_NOT_ESTABLISH:
            self.assertIn(f"- `{item}`", rendered)

    def test_agent_briefing_is_bounded_and_does_not_claim_live_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            metadata = read_bundle_metadata(self.manifest(root), repository="lenskit")

        briefing = build_agent_briefing(metadata)

        self.assertEqual(briefing["kind"], "cabinet_rlens_repository_agent_briefing")
        self.assertFalse(briefing["liveStateClaimed"])
        self.assertEqual(briefing["freshnessClass"], "dated_snapshot")
        self.assertIn("merge_readiness", briefing["doesNotEstablish"])

    def test_missing_commit_degrades_to_unknown_dated_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.manifest(root, generator={"name": "repolens", "runtime": {}})
            metadata = read_bundle_metadata(manifest, repository="lenskit")

        self.assertEqual(metadata.source_commit, None)
        self.assertEqual(metadata.freshness_class, "unknown_dated_snapshot")

    def test_rejects_unsupported_manifest_kind(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.manifest(root, kind="random")
            with self.assertRaisesRegex(RlensReferenceError, "unsupported bundle manifest kind"):
                read_bundle_metadata(manifest, repository="lenskit")

    def test_cli_writes_and_checks_reference_and_agent_briefing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = self.manifest(root)
            reference = root / "Repository Reference.md"
            briefing = root / "briefing.json"
            cmd = [
                sys.executable,
                str(ROOT / "scripts/import_rlens_repository_reference.py"),
                "--manifest",
                str(manifest),
                "--repository",
                "lenskit",
                "--output",
                str(reference),
                "--agent-briefing-output",
                str(briefing),
            ]
            subprocess.run(cmd, check=True)
            subprocess.run([*cmd, "--check"], check=True)
            json_result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/import_rlens_repository_reference.py"),
                    "--manifest",
                    str(manifest),
                    "--repository",
                    "lenskit",
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            data = json.loads(briefing.read_text(encoding="utf-8"))
            rendered = reference.read_text(encoding="utf-8")
            json_payload = json.loads(json_result.stdout)

        self.assertTrue(rendered.startswith("# lenskit"))
        self.assertFalse(data["liveStateClaimed"])
        self.assertEqual(json_payload["reference"]["repository"], "lenskit")
        self.assertTrue(json_payload["reference"]["manifest_path"].endswith(".json"))


if __name__ == "__main__":
    unittest.main()
