from __future__ import annotations

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

from render_system_catalog import render_text  # noqa: E402
from validate_system_catalog import validate  # noqa: E402


class SystemCatalogTests(unittest.TestCase):
    def _copy_repository(self, directory: str) -> Path:
        target = Path(directory) / "repo"
        shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        return target

    def test_repository_catalog_is_valid_and_roomless(self) -> None:
        result = validate(ROOT)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["registrySystems"], 43)
        self.assertEqual(result["registryRelations"], 52)
        self.assertEqual(result["authorityDomains"], 20)
        self.assertEqual(result["catalogRepositories"], 34)
        self.assertEqual(result["fleetRepositories"], 18)
        self.assertEqual(result["fleetExclusions"], 4)
        self.assertEqual(result["organizationRepositories"], 36)
        self.assertEqual(result["organizationCatalogRepositories"], 32)
        self.assertEqual(result["organizationArchivedReferences"], 2)
        self.assertEqual(result["organizationExclusions"], 2)
        self.assertEqual(result["activeLegacyRooms"], 0)
        for room in (
            "bestand",
            "pruefung",
            "steuerung",
            "vorzimmer",
            "heimgewebe",
            "weltgewebe",
            "werkstatt",
            "labor",
            "betrieb",
        ):
            self.assertFalse((ROOT / room).exists())

    def test_rendered_projection_matches_generator(self) -> None:
        actual = (ROOT / "rendered/system-catalog.md").read_text(encoding="utf-8")
        expected = render_text(ROOT)
        self.assertEqual(actual, expected)
        self.assertIn("# Systemkatalog", actual)
        self.assertNotIn("# Heimgewebe-Systemkatalog", actual)
        self.assertIn("## Repository-Abdeckung", actual)
        self.assertIn("`heimgewebe/metarepo`", actual)
        self.assertIn("`vault-privat`", actual)
        self.assertIn("`heimgewebe/demo-repository`", actual)
        self.assertIn("## Organisationsumfang", actual)
        self.assertIn("Archivierte Referenzen ohne aktive Betriebsautorität", actual)
        self.assertIn("`heimgewebe/heimlern` (`public`)", actual)
        self.assertIn("`archived-reference`", actual)
        self.assertNotIn("35 aktive, nicht geforkte Repositories", actual)

    def test_entrypoint_href_uses_raw_target_not_markdown_escape(self) -> None:
        from render_system_catalog import _entrypoints_cell

        rendered = _entrypoints_cell({"docs": "docs/a|b.md"})
        self.assertIn(r"[docs/a\|b.md]", rendered)
        self.assertIn("(../docs/a%7Cb.md)", rendered)
        self.assertNotIn(r"(../docs/a\|b.md)", rendered)

    def test_canonical_nodes_implement_the_full_system_contract(self) -> None:
        data = json.loads((ROOT / "registry/ecosystem/nodes.json").read_text(encoding="utf-8"))
        required = {
            "id", "name", "type", "purpose", "lifecycle",
            "notResponsibleFor", "truthOwnership", "entrypoints",
        }
        self.assertEqual(len(data["nodes"]), 43)
        for node in data["nodes"]:
            self.assertEqual(set(node), required)
            self.assertTrue(node["notResponsibleFor"])
            self.assertTrue(node["entrypoints"])
            self.assertIn(node["lifecycle"]["state"], {"active", "transition", "reference", "archived", "retired"})
            self.assertIn(node["lifecycle"]["reviewedAt"], {"2026-07-26", "2026-07-28", "2026-07-29", "2026-08-01", "2026-08-02", "2026-08-03"})
            self.assertTrue(node["lifecycle"]["evidenceRefs"])
        self.assertIn("Nicht zuständig für", (ROOT / "rendered/system-catalog.md").read_text(encoding="utf-8"))
        rendered = (ROOT / "rendered/system-catalog.md").read_text(encoding="utf-8")
        self.assertIn("Wahrheitsbesitz", rendered)
        self.assertIn("Lebenszyklus", rendered)
        self.assertIn(
            "| Heimserver | repository | `retired` · geprüft 2026-08-01 |",
            rendered,
        )
        self.assertIn(
            "| HausKI Audio | repository | `retired` · geprüft 2026-07-28 |",
            rendered,
        )

    def test_reviewed_role_boundaries_are_explicit(self) -> None:
        nodes = json.loads((ROOT / "registry/ecosystem/nodes.json").read_text(encoding="utf-8"))["nodes"]
        by_id = {node["id"]: node for node in nodes}
        self.assertEqual(
            by_id["repo:wgx"]["purpose"],
            "Repository verification adapter and reusable CI frontdoor router",
        )
        self.assertIn("task coordination or priority", by_id["repo:wgx"]["notResponsibleFor"])
        self.assertEqual(
            by_id["repo:commonworld"]["truthOwnership"],
            ["commonworld_commons_admission"],
        )
        self.assertIn("evidence-bound", by_id["repo:commonworld"]["purpose"])
        self.assertEqual(
            by_id["repo:reposkop"]["truthOwnership"],
            ["repository_checkout_identity_continuity"],
        )
        self.assertIn("checkout identity", by_id["repo:reposkop"]["purpose"])
        self.assertIn(
            "remote repository freshness",
            by_id["repo:reposkop"]["notResponsibleFor"],
        )
        edges = json.loads(
            (ROOT / "registry/ecosystem/edges.json").read_text(encoding="utf-8")
        )["edges"]
        reposkop_relation = next(
            edge
            for edge in edges
            if edge["from"] == "repo:reposkop"
            and edge["to"] == "repo:systemkatalog"
        )
        self.assertIn("checkout identity", reposkop_relation["meaning"])
        self.assertIn("no effect authority", reposkop_relation["meaning"])

    def test_missing_canonical_system_field_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = self._copy_repository(directory)
            path = target / "registry/ecosystem/nodes.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            del data["nodes"][0]["notResponsibleFor"]
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "node 1 fields mismatch"):
                validate(target)

    def test_invalid_lifecycle_state_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = self._copy_repository(directory)
            path = target / "registry/ecosystem/nodes.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["nodes"][0]["lifecycle"]["state"] = "running"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "lifecycle.state unsupported"):
                validate(target)

    def test_invalid_lifecycle_date_fails_closed(self) -> None:
        for reviewed_at in ("yesterday", "20260726", "2026-W30-7", "2026-02-30"):
            with self.subTest(reviewed_at=reviewed_at), tempfile.TemporaryDirectory() as directory:
                target = self._copy_repository(directory)
                path = target / "registry/ecosystem/nodes.json"
                data = json.loads(path.read_text(encoding="utf-8"))
                data["nodes"][0]["lifecycle"]["reviewedAt"] = reviewed_at
                path.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "reviewedAt must use exact YYYY-MM-DD format"):
                    validate(target)

    def test_truth_ownership_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = self._copy_repository(directory)
            path = target / "registry/ecosystem/nodes.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            systemkatalog = next(node for node in data["nodes"] if node["id"] == "repo:systemkatalog")
            systemkatalog["truthOwnership"] = []
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "truth ownership differs from authority matrix"):
                validate(target)

    def test_unknown_authority_owner_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = self._copy_repository(directory)
            path = target / "registry/ecosystem/authority-matrix.v1.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["authorities"][0]["owner"] = "unknown_owner"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "neither a catalog system nor an external principal"):
                validate(target)

    def test_repository_entrypoint_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = self._copy_repository(directory)
            path = target / "registry/ecosystem/nodes.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            systemkatalog = next(node for node in data["nodes"] if node["id"] == "repo:systemkatalog")
            systemkatalog["entrypoints"]["repository"] = "https://example.invalid/wrong"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "repository entrypoint mismatch"):
                validate(target)

    def test_active_room_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = self._copy_repository(directory)
            (target / "steuerung").mkdir()
            (target / "steuerung/index.md").write_text("# stale room\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "legacy room roots remain active"):
                validate(target)

    def test_operational_field_in_registry_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = self._copy_repository(directory)
            path = target / "registry/ecosystem/nodes.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["nodes"][0]["runtimeHealth"] = "green"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "prohibited operational fields"):
                validate(target)

    def test_runtime_projection_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = self._copy_repository(directory)
            path = target / "policy/system-catalog.v1.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["runtimeProjection"] = {"service": "systemkatalog.service"}
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "runtimeProjection must remain absent"):
                validate(target)

    def test_old_repository_identity_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = self._copy_repository(directory)
            path = target / "policy/system-catalog.v1.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["repository"] = "heimgewebe/heimgewebe-katalog"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "repository identity mismatch"):
                validate(target)

    def test_second_authority_matrix_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = self._copy_repository(directory)
            source = target / "registry/ecosystem/authority-matrix.v1.json"
            duplicate = target / "policy/competing-authority.json"
            duplicate.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exactly one active system_catalog_authority_matrix"):
                validate(target)

    def test_manual_authority_assignment_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = self._copy_repository(directory)
            path = target / "policy/manual-authority.json"
            path.write_text(
                json.dumps({"kind": "other", "authorities": [{"domain": "runtime", "owner": "catalog"}]}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "manual authority assignments outside the matrix"):
                validate(target)

    def test_legacy_catalog_kind_outside_archive_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = self._copy_repository(directory)
            path = target / "policy/legacy-catalog.json"
            path.write_text(json.dumps({"kind": "heimgewebe_system_catalog_policy"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "legacy catalog kinds remain active outside the archive"):
                validate(target)


if __name__ == "__main__":
    unittest.main()
