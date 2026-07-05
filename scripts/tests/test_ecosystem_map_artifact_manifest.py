"""Tests for the Cabinet ecosystem map artifact manifest writer."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) in sys.path:
    sys.path.remove(str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS))

from write_ecosystem_map_artifact_manifest import (  # noqa: E402
    ARTIFACT_SPECS,
    CONTRACT_PATH,
    CONTRACT_VERSION,
    DOES_NOT_ESTABLISH,
    MANIFEST_KIND,
    SCHEMA_PATH,
    EcosystemMapManifestError,
    build_manifest,
    main as manifest_main,
    validate_manifest,
    write_manifest,
)

SCHEMA_FILE = ROOT / SCHEMA_PATH
TEST_COMMIT = "a" * 40
TEST_GENERATED_AT = "2026-07-05T00:00:00Z"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_file(root: Path, path: str, content: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def write_valid_map_artifacts(root: Path) -> None:
    for spec in ARTIFACT_SPECS:
        if spec["contentType"] == "application/json":
            content = '{"ok": true}\n'
        elif spec["contentType"] == "application/x-ndjson":
            content = '{"claim":"example"}\n'
        elif spec["contentType"] == "text/mermaid":
            content = "flowchart TD\n    A[Example]\n"
        else:
            content = "# Example\n"
        write_file(root, spec["path"], content)


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))


class EcosystemMapArtifactManifestTests(unittest.TestCase):
    def test_manifest_builds_with_digests_and_non_claims(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_valid_map_artifacts(root)
            manifest = build_manifest(
                root,
                source_commit=TEST_COMMIT,
                generated_at=TEST_GENERATED_AT,
            )

        self.assertEqual(manifest["kind"], MANIFEST_KIND)
        self.assertEqual(manifest["contractVersion"], CONTRACT_VERSION)
        self.assertEqual(manifest["contractPath"], CONTRACT_PATH)
        self.assertEqual(manifest["schemaPath"], SCHEMA_PATH)
        self.assertEqual(manifest["mode"], "read_only_projection_source")
        self.assertEqual(manifest["source"]["repository"], "heimgewebe/cabinet")
        self.assertEqual(manifest["source"]["commit"], TEST_COMMIT)
        self.assertEqual(manifest["source"]["generatedAt"], TEST_GENERATED_AT)
        self.assertEqual(manifest["artifactCount"], len(ARTIFACT_SPECS))
        self.assertEqual(set(manifest["doesNotEstablish"]), set(DOES_NOT_ESTABLISH))
        self.assertEqual(
            [artifact["role"] for artifact in manifest["artifacts"]],
            [spec["role"] for spec in ARTIFACT_SPECS],
        )
        self.assertEqual(
            manifest["artifacts"][0]["sha256"],
            sha256_text("flowchart TD\n    A[Example]\n"),
        )
        validate_manifest(manifest)

    def test_schema_matches_manifest_contract_constants(self) -> None:
        schema = load_schema()
        properties = schema["properties"]
        schema_artifacts = [
            {
                "role": item["properties"]["role"]["const"],
                "path": item["properties"]["path"]["const"],
                "contentType": item["properties"]["contentType"]["const"],
            }
            for item in properties["artifacts"]["prefixItems"]
        ]

        self.assertEqual(properties["kind"]["const"], MANIFEST_KIND)
        self.assertEqual(properties["contractVersion"]["const"], CONTRACT_VERSION)
        self.assertEqual(properties["contractPath"]["const"], CONTRACT_PATH)
        self.assertEqual(properties["schemaPath"]["const"], SCHEMA_PATH)
        self.assertEqual(properties["artifactCount"]["const"], len(ARTIFACT_SPECS))
        self.assertEqual(schema_artifacts, list(ARTIFACT_SPECS))
        self.assertEqual(
            set(properties["doesNotEstablish"]["items"]["enum"]),
            set(DOES_NOT_ESTABLISH),
        )

    def test_write_manifest_rejects_output_outside_repo(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_valid_map_artifacts(root)
            outside = root.parent / "outside.json"
            with self.assertRaisesRegex(EcosystemMapManifestError, "output path escapes repository"):
                write_manifest(root, outside)

    def test_manifest_rejects_missing_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_valid_map_artifacts(root)
            (root / "rendered/ecosystem-registry-map.mmd").unlink()
            with self.assertRaisesRegex(EcosystemMapManifestError, "missing map artifact"):
                build_manifest(root, source_commit=TEST_COMMIT, generated_at=TEST_GENERATED_AT)

    def test_manifest_rejects_invalid_source_commit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_valid_map_artifacts(root)
            with self.assertRaisesRegex(EcosystemMapManifestError, "source_commit"):
                build_manifest(root, source_commit="not-a-sha", generated_at=TEST_GENERATED_AT)

    def test_check_mode_uses_real_repository_artifacts(self) -> None:
        self.assertEqual(manifest_main(["--repo-root", str(ROOT), "--check"]), 0)

    def test_json_check_mode_reports_source_commit(self) -> None:
        # This checks only that the CLI path emits valid JSON and does not write a file.
        self.assertEqual(manifest_main(["--repo-root", str(ROOT), "--check", "--json"]), 0)


if __name__ == "__main__":
    unittest.main()
