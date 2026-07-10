from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import private_cabinet_archive as ARCHIVE  # noqa: E402


class PrivateCabinetArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.repo = self.root / "workspace"
        self.app = self.root / "application"
        self.home.mkdir()
        self.repo.mkdir()
        self.app.mkdir()
        git_binary = shutil.which("git")
        self.assertIsNotNone(git_binary)
        subprocess.run(  # noqa: S603
            [str(git_binary), "init", "--quiet", str(self.repo)],
            check=True,
            capture_output=True,
        )

        runtime_config = self.home / ".config/cabinet"
        runtime_config.mkdir(parents=True)
        (runtime_config / "runtime.env").write_text(
            "PRIVATE_VALUE=test\n", encoding="utf-8"
        )
        runtime_state = self.home / ".local/state/cabinet"
        runtime_state.mkdir(parents=True)
        (runtime_state / "rollback.json").write_text(
            '{"state":"ready"}\n', encoding="utf-8"
        )
        private_agent = self.repo / ".agents/.runtime"
        private_agent.mkdir(parents=True)
        (private_agent / "session.json").write_text('{"session":1}\n', encoding="utf-8")
        (self.repo / "local-note.txt").write_text(
            "workspace local data\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _create_wal_database(
        self, path: Path
    ) -> tuple[sqlite3.Connection, sqlite3.Connection]:
        path.parent.mkdir(parents=True, exist_ok=True)
        writer = sqlite3.connect(path)
        self.assertEqual(writer.execute("PRAGMA journal_mode=WAL").fetchone()[0], "wal")
        writer.execute(
            "CREATE TABLE messages(id INTEGER PRIMARY KEY, body TEXT NOT NULL)"
        )
        writer.execute("INSERT INTO messages(body) VALUES ('first')")
        writer.commit()
        reader = sqlite3.connect(path)
        reader.execute("BEGIN")
        reader.execute("SELECT COUNT(*) FROM messages").fetchone()
        writer.execute("INSERT INTO messages(body) VALUES ('second')")
        writer.commit()
        self.assertTrue(path.with_name(path.name + "-wal").is_file())
        self.assertGreater(path.with_name(path.name + "-wal").stat().st_size, 0)
        return writer, reader

    def _export(
        self, destination_name: str = "archive"
    ) -> tuple[Path, dict[str, object]]:
        destination = self.root / destination_name
        receipt = ARCHIVE.export_archive(
            home=self.home,
            repo=self.repo,
            app_root=self.app,
            destination=destination,
        )
        return destination, receipt

    def _manifest(self, archive: Path) -> dict[str, object]:
        return json.loads((archive / "manifest.json").read_text(encoding="utf-8"))

    def test_export_uses_online_backup_for_live_wal_database(self) -> None:
        writer, reader = self._create_wal_database(self.repo / ".cabinet.db")
        try:
            archive, receipt = self._export()
        finally:
            reader.close()
            writer.close()

        manifest = self._manifest(archive)
        database_entries = [
            entry for entry in manifest["entries"] if entry["kind"] == "sqlite"
        ]
        self.assertTrue(database_entries)
        active = next(
            entry
            for entry in database_entries
            if entry["source_class"] == "repository_private"
        )
        self.assertEqual(active["capture_method"], "sqlite_online_backup")
        self.assertEqual(active["database_integrity"], "ok")
        archived_database = archive / active["archive_path"]
        with sqlite3.connect(archived_database) as connection:
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0], 2
            )
            self.assertEqual(
                connection.execute("PRAGMA quick_check").fetchone()[0], "ok"
            )
        self.assertEqual(receipt["status"], "exported")
        self.assertFalse(receipt["backup_status"]["service_mutated"])
        self.assertGreaterEqual(
            receipt["backup_status"]["excluded_live_sqlite_sidecars"], 1
        )

    def test_export_refuses_known_coverage_gaps(self) -> None:
        destination = self.root / "incomplete-export"
        with self.assertRaisesRegex(ARCHIVE.ArchiveError, "coverage_gaps_present"):
            ARCHIVE.export_archive(
                home=self.home,
                repo=self.repo,
                app_root=self.app,
                destination=destination,
            )
        self.assertFalse(destination.exists())

    def test_destination_is_absolute_create_only_and_outside_repositories(self) -> None:
        writer, reader = self._create_wal_database(self.repo / ".cabinet.db")
        reader.close()
        writer.close()
        with self.assertRaisesRegex(
            ARCHIVE.ArchiveError, "destination_must_be_absolute"
        ):
            ARCHIVE.export_archive(
                home=self.home,
                repo=self.repo,
                app_root=self.app,
                destination=Path("relative-archive"),
            )
        existing = self.root / "existing"
        existing.mkdir()
        with self.assertRaisesRegex(ARCHIVE.ArchiveError, "destination_must_not_exist"):
            ARCHIVE.export_archive(
                home=self.home,
                repo=self.repo,
                app_root=self.app,
                destination=existing,
            )
        with self.assertRaisesRegex(ARCHIVE.ArchiveError, "destination_inside_source"):
            ARCHIVE.export_archive(
                home=self.home,
                repo=self.repo,
                app_root=self.app,
                destination=self.repo / "private-archive",
            )

    def test_archive_and_payload_permissions_are_owner_only(self) -> None:
        writer, reader = self._create_wal_database(self.repo / ".cabinet.db")
        try:
            archive, _ = self._export()
        finally:
            reader.close()
            writer.close()
        for directory, dirnames, filenames in os.walk(archive):
            directory_path = Path(directory)
            self.assertEqual(stat.S_IMODE(directory_path.stat().st_mode) & 0o077, 0)
            for dirname in dirnames:
                self.assertEqual(
                    stat.S_IMODE((directory_path / dirname).stat().st_mode) & 0o077,
                    0,
                )
            for filename in filenames:
                self.assertEqual(
                    stat.S_IMODE((directory_path / filename).stat().st_mode) & 0o077,
                    0,
                )

    def test_tampered_payload_fails_verification(self) -> None:
        writer, reader = self._create_wal_database(self.repo / ".cabinet.db")
        try:
            archive, _ = self._export()
        finally:
            reader.close()
            writer.close()
        manifest = self._manifest(archive)
        regular_entry = next(
            entry for entry in manifest["entries"] if entry["kind"] == "regular"
        )
        target = archive / regular_entry["archive_path"]
        target.write_bytes(target.read_bytes() + b"tampered")
        with self.assertRaisesRegex(ARCHIVE.ArchiveError, "archive_size_mismatch"):
            ARCHIVE.verify_archive(archive)

    def test_manifest_path_escape_fails_even_with_rebound_digest(self) -> None:
        writer, reader = self._create_wal_database(self.repo / ".cabinet.db")
        try:
            archive, _ = self._export()
        finally:
            reader.close()
            writer.close()
        manifest_path = archive / "manifest.json"
        manifest = self._manifest(archive)
        manifest["entries"][0]["archive_path"] = "payload/../escape"
        manifest_bytes = (
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        manifest_path.write_bytes(manifest_bytes)
        (archive / "manifest.sha256").write_text(
            hashlib.sha256(manifest_bytes).hexdigest() + "\n",
            encoding="ascii",
        )
        with self.assertRaisesRegex(ARCHIVE.ArchiveError, "unsafe_relative_path"):
            ARCHIVE.verify_archive(archive)

    def test_source_symlink_is_rejected(self) -> None:
        target = self.root / "outside.txt"
        target.write_text("outside\n", encoding="utf-8")
        (self.home / ".config/cabinet/link").symlink_to(target)
        with self.assertRaisesRegex(ARCHIVE.ArchiveError, "source_symlink_rejected"):
            ARCHIVE.plan_archive(home=self.home, repo=self.repo, app_root=self.app)

    def test_source_drift_fails_closed(self) -> None:
        source = self.root / "source.txt"
        destination = self.root / "copy.txt"
        source.write_text("data\n", encoding="utf-8")
        with (
            mock.patch.object(
                ARCHIVE,
                "_fingerprint",
                side_effect=[(1, 2, 3, 4), (1, 2, 3, 5)],
            ),
            self.assertRaisesRegex(ARCHIVE.ArchiveError, "source_drift_detected"),
        ):
            ARCHIVE._copy_regular_file(source, destination)

    def test_sqlite_source_replacement_fails_closed(self) -> None:
        database = self.repo / "replaceable.db"
        connection = sqlite3.connect(database)
        connection.execute("CREATE TABLE sample(id INTEGER PRIMARY KEY)")
        connection.commit()
        connection.close()
        destination = self.root / "database-copy.db"
        original_lstat = Path.lstat
        database_calls = 0

        def changed_inode(path: Path) -> os.stat_result:
            nonlocal database_calls
            result = original_lstat(path)
            if path == database:
                database_calls += 1
                if database_calls == 2:
                    values = list(result)
                    values[1] += 1
                    return os.stat_result(values)
            return result

        with (
            mock.patch.object(Path, "lstat", new=changed_inode),
            self.assertRaisesRegex(ARCHIVE.ArchiveError, "sqlite_source_replaced"),
        ):
            ARCHIVE._backup_sqlite(database, destination)

    def test_reinstallable_application_payload_is_excluded(self) -> None:
        writer, reader = self._create_wal_database(self.repo / ".cabinet.db")
        application_version = self.app / "v1"
        dependency = application_version / "node_modules/package"
        dependency.mkdir(parents=True)
        (dependency / "large.js").write_text("reinstallable\n", encoding="utf-8")
        (application_version / "source.js").write_text("source\n", encoding="utf-8")
        application_database = application_version / "data/.cabinet.db"
        application_database.parent.mkdir(parents=True)
        app_connection = sqlite3.connect(application_database)
        app_connection.execute("CREATE TABLE legacy(id INTEGER PRIMARY KEY)")
        app_connection.commit()
        app_connection.close()
        try:
            archive, _ = self._export()
        finally:
            reader.close()
            writer.close()
        manifest_text = (archive / "manifest.json").read_text(encoding="utf-8")
        self.assertIn("application_private", manifest_text)
        self.assertNotIn("node_modules", manifest_text)
        self.assertNotIn("large.js", manifest_text)
        self.assertNotIn("source.js", manifest_text)

    def test_public_receipt_contains_no_paths_or_private_names(self) -> None:
        writer, reader = self._create_wal_database(self.repo / ".cabinet.db")
        try:
            _, receipt = self._export()
        finally:
            reader.close()
            writer.close()
        serialized = json.dumps(receipt, sort_keys=True)
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn("runtime.env", serialized)
        self.assertNotIn(".cabinet.db", serialized)
        self.assertNotIn("session.json", serialized)
        self.assertNotIn("PRIVATE_VALUE", serialized)
        self.assertEqual(
            set(receipt),
            {
                "schema_version",
                "kind",
                "status",
                "classification",
                "scope",
                "backup_status",
                "coverage_gaps",
                "does_not_establish",
            },
        )

    def test_restore_is_isolated_create_only_and_verified(self) -> None:
        writer, reader = self._create_wal_database(self.repo / ".cabinet.db")
        try:
            archive, _ = self._export()
        finally:
            reader.close()
            writer.close()
        target = self.root / "isolated-restore"
        receipt = ARCHIVE.restore_archive(archive=archive, target=target)
        self.assertEqual(receipt["status"], "restored")
        self.assertTrue((target / "restore-verification.json").is_file())
        restored_database = target / "repository-private/.cabinet.db"
        with sqlite3.connect(restored_database) as connection:
            self.assertEqual(
                connection.execute("PRAGMA quick_check").fetchone()[0], "ok"
            )
        with self.assertRaisesRegex(ARCHIVE.ArchiveError, "destination_must_not_exist"):
            ARCHIVE.restore_archive(archive=archive, target=target)

    def test_archive_root_symlink_is_rejected(self) -> None:
        writer, reader = self._create_wal_database(self.repo / ".cabinet.db")
        try:
            archive, _ = self._export()
        finally:
            reader.close()
            writer.close()
        link = self.root / "archive-link"
        link.symlink_to(archive, target_is_directory=True)
        with self.assertRaisesRegex(ARCHIVE.ArchiveError, "archive_symlink_rejected"):
            ARCHIVE.verify_archive(link)

    def test_total_size_limit_fails_closed(self) -> None:
        (self.repo / "large-one.bin").write_bytes(b"a" * 700)
        (self.repo / "large-two.bin").write_bytes(b"b" * 700)
        with self.assertRaisesRegex(ARCHIVE.ArchiveError, "selected_total_too_large"):
            ARCHIVE.plan_archive(
                home=self.home,
                repo=self.repo,
                app_root=self.app,
                max_file_bytes=1000,
                max_total_bytes=1000,
            )

    def test_app_root_symlink_is_rejected(self) -> None:
        shutil.rmtree(self.app)
        real_app = self.root / "real-application"
        real_app.mkdir()
        self.app.symlink_to(real_app, target_is_directory=True)
        with self.assertRaisesRegex(ARCHIVE.ArchiveError, "app_root_invalid"):
            ARCHIVE.plan_archive(
                home=self.home,
                repo=self.repo,
                app_root=self.app,
            )

    def test_incomplete_archive_is_rejected(self) -> None:
        writer, reader = self._create_wal_database(self.repo / ".cabinet.db")
        try:
            archive, _ = self._export()
        finally:
            reader.close()
            writer.close()
        marker_path = archive / ".incomplete"
        marker_path.write_text("interrupted\n", encoding="utf-8")
        os.chmod(marker_path, 0o600)
        with self.assertRaisesRegex(ARCHIVE.ArchiveError, "archive_incomplete"):
            ARCHIVE.verify_archive(archive)

    def test_unexpected_cli_error_is_redacted(self) -> None:
        stderr = io.StringIO()
        with (
            mock.patch.object(
                ARCHIVE,
                "plan_archive",
                side_effect=OSError("/private/secret/runtime.env"),
            ),
            redirect_stderr(stderr),
        ):
            return_code = ARCHIVE.main(
                [
                    "plan",
                    "--home",
                    str(self.home),
                    "--repo",
                    str(self.repo),
                    "--app-root",
                    str(self.app),
                ]
            )
        output = stderr.getvalue()
        self.assertEqual(return_code, 2)
        self.assertIn("unexpected_failure", output)
        self.assertNotIn("/private/secret", output)
        self.assertNotIn("runtime.env", output)


if __name__ == "__main__":
    unittest.main()
