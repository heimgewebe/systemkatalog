from __future__ import annotations

import hashlib
import json
import os
import subprocess
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
    DEFAULT_OUTPUT,
    DOES_NOT_ESTABLISH,
    MANIFEST_KIND,
    SCHEMA_PATH,
    EcosystemMapManifestError,
    build_manifest,
    check_manifest,
    validate_manifest,
    write_manifest,
)

COMMIT_TIME = "2026-07-11T00:00:00+00:00"
EXPECTED_TIME = "2026-07-11T00:00:00Z"
HAS_GIT_HISTORY = subprocess.run(
    ["git", "rev-parse", "--is-inside-work-tree"],
    cwd=ROOT,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    check=False,
).returncode == 0


def populate(root: Path) -> None:
    for spec in ARTIFACT_SPECS:
        path = root / spec["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(f"content for {spec['path']}\n", encoding="utf-8")


def git(root: Path, *args: str, env: dict[str, str] | None = None) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=root,
        text=True,
        env=env,
        stderr=subprocess.DEVNULL,
    ).strip()


def initialize_repository(root: Path) -> str:
    populate(root)
    git(root, "init", "-q")
    git(root, "config", "user.email", "tests@systemkatalog.invalid")
    git(root, "config", "user.name", "Systemkatalog Tests")
    git(root, "add", ".")
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = COMMIT_TIME
    env["GIT_COMMITTER_DATE"] = COMMIT_TIME
    git(root, "commit", "-qm", "catalog artifacts", env=env)
    return git(root, "rev-parse", "HEAD")


def publish_manifest(root: Path, source_commit: str) -> dict[str, object]:
    manifest = write_manifest(root, DEFAULT_OUTPUT, source_commit=source_commit)
    git(root, "add", str(DEFAULT_OUTPUT))
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = "2026-07-11T00:01:00+00:00"
    env["GIT_COMMITTER_DATE"] = "2026-07-11T00:01:00+00:00"
    git(root, "commit", "-qm", "publish manifest", env=env)
    return manifest


class EcosystemMapManifestTests(unittest.TestCase):
    def test_manifest_has_neutral_source_and_digests(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commit = initialize_repository(root)
            manifest = build_manifest(root, source_commit=commit)
        self.assertEqual(manifest["kind"], MANIFEST_KIND)
        self.assertEqual(manifest["contractVersion"], CONTRACT_VERSION)
        self.assertEqual(manifest["schemaPath"], SCHEMA_PATH)
        self.assertEqual(manifest["source"]["repository"], "heimgewebe/systemkatalog")
        self.assertEqual(manifest["source"]["generatedAt"], EXPECTED_TIME)
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

    def test_exactly_one_canonical_map_role_remains(self) -> None:
        map_specs = [
            spec for spec in ARTIFACT_SPECS
            if spec["path"] == "rendered/ecosystem-registry-map.mmd"
        ]
        self.assertEqual(
            map_specs,
            [
                {
                    "role": "canonical_ecosystem_map_mermaid",
                    "path": "rendered/ecosystem-registry-map.mmd",
                    "contentType": "text/mermaid",
                }
            ],
        )
        roles = {spec["role"] for spec in ARTIFACT_SPECS}
        self.assertNotIn("readable_overview_mermaid", roles)
        self.assertNotIn("generated_registry_projection_mermaid", roles)

    def test_missing_artifact_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commit = initialize_repository(root)
            (root / ARTIFACT_SPECS[-1]["path"]).unlink()
            with self.assertRaisesRegex(EcosystemMapManifestError, "missing or empty"):
                build_manifest(root, source_commit=commit)

    def test_manifest_role_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commit = initialize_repository(root)
            manifest = build_manifest(root, source_commit=commit)
            manifest["artifacts"][0]["role"] = "unbound_role"
            with self.assertRaisesRegex(EcosystemMapManifestError, "artifact contract mismatch"):
                validate_manifest(manifest)

    def test_non_hex_artifact_digest_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commit = initialize_repository(root)
            manifest = build_manifest(root, source_commit=commit)
            manifest["artifacts"][0]["sha256"] = "z" * 64
            with self.assertRaisesRegex(EcosystemMapManifestError, "artifact digest invalid"):
                validate_manifest(manifest)

    def test_output_escape_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commit = initialize_repository(root)
            with self.assertRaisesRegex(EcosystemMapManifestError, "escapes repository"):
                write_manifest(root, root.parent / "outside.json", source_commit=commit)

    def test_check_requires_published_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            initialize_repository(root)
            with self.assertRaisesRegex(EcosystemMapManifestError, "published manifest missing"):
                check_manifest(root)

    def test_check_accepts_published_commit_bound_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commit = initialize_repository(root)
            published = publish_manifest(root, commit)
            checked = check_manifest(root)
        self.assertEqual(checked, published)

    def test_check_rejects_current_artifact_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commit = initialize_repository(root)
            publish_manifest(root, commit)
            artifact = root / ARTIFACT_SPECS[0]["path"]
            artifact.write_text("changed after publication\n", encoding="utf-8")
            with self.assertRaisesRegex(EcosystemMapManifestError, "stale for current artifacts"):
                check_manifest(root)

    def test_write_rejects_feature_commit_not_on_origin_main(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base_commit = initialize_repository(root)
            git(root, "update-ref", "refs/remotes/origin/main", base_commit)
            git(root, "switch", "-qc", "feature")
            (root / "feature-note.txt").write_text("temporary branch commit\n", encoding="utf-8")
            git(root, "add", "feature-note.txt")
            git(root, "commit", "-qm", "feature-only commit")
            feature_commit = git(root, "rev-parse", "HEAD")
            with self.assertRaisesRegex(
                EcosystemMapManifestError,
                "not an ancestor of durable ref refs/remotes/origin/main",
            ):
                write_manifest(root, DEFAULT_OUTPUT, source_commit=feature_commit)

    def test_write_accepts_source_commit_on_published_remote_feature_ref(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base_commit = initialize_repository(root)
            git(root, "update-ref", "refs/remotes/origin/main", base_commit)
            git(root, "switch", "-qc", "feature")
            (root / "feature-note.txt").write_text("published feature branch\n", encoding="utf-8")
            git(root, "add", "feature-note.txt")
            git(root, "commit", "-qm", "feature-only commit")
            feature_commit = git(root, "rev-parse", "HEAD")
            durable_ref = "refs/remotes/pull-request/head"
            git(root, "update-ref", durable_ref, feature_commit)
            manifest = write_manifest(
                root,
                DEFAULT_OUTPUT,
                source_commit=feature_commit,
                durable_source_ref=durable_ref,
            )
            checked = check_manifest(
                root, DEFAULT_OUTPUT, durable_source_ref=durable_ref
            )
            with self.assertRaisesRegex(
                EcosystemMapManifestError,
                "not an ancestor of durable ref refs/remotes/origin/main",
            ):
                check_manifest(root)
        self.assertEqual(manifest, checked)

    def test_explicit_local_branch_ref_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commit = initialize_repository(root)
            with self.assertRaisesRegex(
                EcosystemMapManifestError,
                "must be a remote-tracking origin or pull-request ref",
            ):
                write_manifest(
                    root,
                    DEFAULT_OUTPUT,
                    source_commit=commit,
                    durable_source_ref="refs/heads/main",
                )

    def test_missing_explicit_remote_ref_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commit = initialize_repository(root)
            with self.assertRaisesRegex(
                EcosystemMapManifestError,
                "durable source ref is missing or invalid",
            ):
                write_manifest(
                    root,
                    DEFAULT_OUTPUT,
                    source_commit=commit,
                    durable_source_ref="refs/remotes/origin/missing",
                )

    def test_write_accepts_origin_main_commit_from_feature_branch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base_commit = initialize_repository(root)
            git(root, "update-ref", "refs/remotes/origin/main", base_commit)
            git(root, "switch", "-qc", "feature")
            (root / "feature-note.txt").write_text("temporary branch commit\n", encoding="utf-8")
            git(root, "add", "feature-note.txt")
            git(root, "commit", "-qm", "feature-only commit")
            manifest = write_manifest(root, DEFAULT_OUTPUT, source_commit=base_commit)
            self.assertEqual(manifest["source"]["commit"], base_commit)

    def test_check_rejects_source_commit_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old_commit = initialize_repository(root)
            artifact = root / ARTIFACT_SPECS[0]["path"]
            artifact.write_text("new committed content\n", encoding="utf-8")
            git(root, "add", str(artifact.relative_to(root)))
            git(root, "commit", "-qm", "change artifact")
            with self.assertRaisesRegex(EcosystemMapManifestError, "bound source commit"):
                write_manifest(root, DEFAULT_OUTPUT, source_commit=old_commit)

    @unittest.skipUnless(HAS_GIT_HISTORY, "repository Git history is unavailable in archive validation")
    def test_repository_manifest_is_published_and_current(self) -> None:
        durable_ref = os.environ.get("SYSTEMKATALOG_DURABLE_SOURCE_REF")
        manifest = check_manifest(ROOT, durable_source_ref=durable_ref)
        first = ROOT / manifest["artifacts"][0]["path"]
        self.assertEqual(manifest["artifacts"][0]["sha256"], hashlib.sha256(first.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
