from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from write_ecosystem_map_artifact_manifest import (  # noqa: E402
    ARTIFACT_SPECS,
    CONTRACT_VERSION,
    DOES_NOT_ESTABLISH,
    MANIFEST_KIND,
    SCHEMA_PATH,
    EcosystemMapManifestError,
    build_manifest,
    validate_manifest,
    write_manifest,
)

TEST_COMMIT = "a" * 40
TEST_TIME = "2026-07-11T00:00:00Z"


def populate(root: Path) -> None:
    for spec in ARTIFACT_SPECS:
        path = root / spec["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(f"content for {spec['path']}\n", encoding="utf-8")


class EcosystemMapManifestTests(unittest.TestCase):
    def test_manifest_has_neutral_source_and_digests(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            populate(root)
            manifest = build_manifest(root, source_commit=TEST_COMMIT, generated_at=TEST_TIME)
        self.assertEqual(manifest["kind"], MANIFEST_KIND)
        self.assertEqual(manifest["contractVersion"], CONTRACT_VERSION)
        self.assertEqual(manifest["schemaPath"], SCHEMA_PATH)
        self.assertEqual(manifest["source"]["repository"], "heimgewebe/systemkatalog")
        self.assertEqual(manifest["artifactCount"], len(ARTIFACT_SPECS))
        self.assertEqual(tuple(manifest["doesNotEstablish"]), DOES_NOT_ESTABLISH)
        validate_manifest(manifest)

    def test_schema_is_exactly_bound_to_writer_contract(self) -> None:
        schema = json.loads((ROOT / SCHEMA_PATH).read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["kind"]["const"], MANIFEST_KIND)
        self.assertEqual(schema["properties"]["contractVersion"]["const"], CONTRACT_VERSION)
        self.assertEqual(schema["properties"]["artifactCount"]["const"], len(ARTIFACT_SPECS))
        self.assertFalse(schema["properties"]["artifacts"]["items"])

        schema_specs = []
        for item in schema["properties"]["artifacts"]["prefixItems"]:
            definition_name = item["$ref"].rsplit("/", 1)[-1]
            properties = schema["$defs"][definition_name]["allOf"][1]["properties"]
            schema_specs.append(
                {
                    "role": properties["role"]["const"],
                    "path": properties["path"]["const"],
                    "contentType": properties["contentType"]["const"],
                }
            )
        self.assertEqual(schema_specs, list(ARTIFACT_SPECS))
        schema_non_claims = tuple(
            item["const"] for item in schema["properties"]["doesNotEstablish"]["prefixItems"]
        )
        self.assertEqual(schema_non_claims, DOES_NOT_ESTABLISH)

    def test_two_temporary_consumer_roles_share_one_canonical_map(self) -> None:
        self.assertEqual(ARTIFACT_SPECS[0]["path"], "rendered/ecosystem-registry-map.mmd")
        self.assertEqual(ARTIFACT_SPECS[1]["path"], ARTIFACT_SPECS[0]["path"])
        self.assertNotEqual(ARTIFACT_SPECS[0]["role"], ARTIFACT_SPECS[1]["role"])

    def test_missing_artifact_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            populate(root)
            (root / ARTIFACT_SPECS[-1]["path"]).unlink()
            with self.assertRaisesRegex(EcosystemMapManifestError, "missing or empty"):
                build_manifest(root, source_commit=TEST_COMMIT, generated_at=TEST_TIME)

    def test_manifest_role_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            populate(root)
            manifest = build_manifest(root, source_commit=TEST_COMMIT, generated_at=TEST_TIME)
            manifest["artifacts"][0]["role"] = "unbound_role"
            with self.assertRaisesRegex(EcosystemMapManifestError, "artifact contract mismatch"):
                validate_manifest(manifest)

    def test_output_escape_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            populate(root)
            with self.assertRaisesRegex(EcosystemMapManifestError, "escapes repository"):
                write_manifest(root, root.parent / "outside.json")

    def test_repository_manifest_builds(self) -> None:
        manifest = build_manifest(ROOT, source_commit=TEST_COMMIT, generated_at=TEST_TIME)
        self.assertEqual(manifest["source"]["repository"], "heimgewebe/systemkatalog")
        first = ROOT / manifest["artifacts"][0]["path"]
        self.assertEqual(manifest["artifacts"][0]["sha256"], hashlib.sha256(first.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
