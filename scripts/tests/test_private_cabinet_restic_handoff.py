from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import private_cabinet_archive as ARCHIVE  # noqa: E402
import private_cabinet_restic_handoff as HANDOFF  # noqa: E402


class PrivateCabinetResticHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.repo = self.root / "workspace"
        self.app = self.root / "application"
        self.tmpfs = self.root / "tmpfs"
        self.home.mkdir()
        self.repo.mkdir()
        self.app.mkdir()
        self.tmpfs.mkdir()
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
        connection = sqlite3.connect(self.repo / ".cabinet.db")
        connection.execute("CREATE TABLE messages(id INTEGER PRIMARY KEY, body TEXT)")
        connection.execute("INSERT INTO messages(body) VALUES ('private')")
        connection.commit()
        connection.close()

        self.restic_binary = self.root / "restic"
        self.restic_binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        os.chmod(self.restic_binary, 0o700)
        self.password_file = self.root / "restic-password"
        self.password_file.write_text("synthetic-password\n", encoding="utf-8")
        os.chmod(self.password_file, 0o600)
        self.environment = {
            "RESTIC_REPOSITORY": "rest:synthetic-repository",
            "RESTIC_PASSWORD_FILE": str(self.password_file),
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _plan_ready(self) -> dict[str, object]:
        return {
            "status": "ready",
            "restic": {"snapshot_count_bucket": "single_digit"},
        }

    def _execute(
        self,
        run_restic: mock.Mock,
        *,
        snapshot_id: str = "a" * 64,
        tagged_snapshot_ids: list[str] | None = None,
    ) -> dict[str, object]:
        with (
            mock.patch.dict(os.environ, self.environment, clear=True),
            mock.patch.object(
                HANDOFF,
                "plan_handoff",
                return_value=self._plan_ready(),
            ),
            mock.patch.object(HANDOFF, "_validate_tmpfs"),
            mock.patch.object(HANDOFF, "_run_restic", run_restic),
            mock.patch.object(HANDOFF, "_restic_tag_is_unused", return_value=True),
            mock.patch.object(
                HANDOFF,
                "_restic_snapshot_ids_for_tag",
                return_value=(
                    [snapshot_id]
                    if tagged_snapshot_ids is None
                    else tagged_snapshot_ids
                ),
            ),
            mock.patch.object(
                HANDOFF,
                "_exclusive_execution_lock",
                return_value=contextlib.nullcontext(),
            ),
        ):
            return HANDOFF.execute_handoff(
                home=self.home,
                repo=self.repo,
                app_root=self.app,
                tmpfs_root=self.tmpfs,
                restic_binary=self.restic_binary,
                max_file_bytes=1024 * 1024,
                max_total_bytes=16 * 1024 * 1024,
                confirmation=HANDOFF.EXECUTION_CONFIRMATION,
                tag="cabinet-t012-test",
            )

    def test_module_disables_bytecode_writes_before_archive_import(self) -> None:
        self.assertTrue(HANDOFF.sys.dont_write_bytecode)

    def test_process_tmpdir_is_private_and_environment_is_restored(self) -> None:
        process_tmp = self.tmpfs / "process-tmp"
        process_tmp.mkdir(mode=0o700)
        original_tempdir = tempfile.tempdir
        with mock.patch.dict(
            os.environ,
            {
                "TMPDIR": "/previous/tmp",
                "TEMP": "/previous/temp",
                "TMP": "/previous/tmp-short",
                "SQLITE_TMPDIR": "/previous/sqlite",
            },
            clear=False,
        ):
            with HANDOFF._temporary_process_tmpdir(process_tmp):
                for key in ("TMPDIR", "TEMP", "TMP", "SQLITE_TMPDIR"):
                    self.assertEqual(os.environ[key], str(process_tmp))
                self.assertIsNone(tempfile.tempdir)
            self.assertEqual(os.environ["TMPDIR"], "/previous/tmp")
            self.assertEqual(os.environ["TEMP"], "/previous/temp")
            self.assertEqual(os.environ["TMP"], "/previous/tmp-short")
            self.assertEqual(os.environ["SQLITE_TMPDIR"], "/previous/sqlite")
            self.assertEqual(tempfile.tempdir, original_tempdir)

    def test_core_dump_disable_failure_blocks_execute(self) -> None:
        with (
            mock.patch.object(
                HANDOFF.resource,
                "setrlimit",
                side_effect=OSError("synthetic"),
            ),
            mock.patch.object(HANDOFF, "plan_handoff") as plan,
            self.assertRaisesRegex(HANDOFF.HandoffError, "core_dump_disable_failed"),
        ):
            HANDOFF.execute_handoff(
                home=self.home,
                repo=self.repo,
                app_root=self.app,
                tmpfs_root=self.tmpfs,
                restic_binary=self.restic_binary,
                max_file_bytes=1024,
                max_total_bytes=4096,
                confirmation=HANDOFF.EXECUTION_CONFIRMATION,
                tag="cabinet-test",
            )
        plan.assert_not_called()

    def test_help_and_unknown_arguments_never_enter_work_functions(self) -> None:
        with (
            mock.patch.object(HANDOFF, "plan_handoff") as plan,
            mock.patch.object(HANDOFF, "execute_handoff") as execute,
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            with self.assertRaises(SystemExit) as help_exit:
                HANDOFF.main(["--help"])
            self.assertEqual(help_exit.exception.code, 0)
            with self.assertRaises(SystemExit) as unknown_exit:
                HANDOFF.main(["probe"])
            self.assertEqual(unknown_exit.exception.code, 2)
        plan.assert_not_called()
        execute.assert_not_called()

    def test_execute_requires_confirmation_before_plan_or_staging(self) -> None:
        with (
            mock.patch.object(HANDOFF, "plan_handoff") as plan,
            self.assertRaisesRegex(
                HANDOFF.HandoffError, "execution_confirmation_missing"
            ),
        ):
            HANDOFF.execute_handoff(
                home=self.home,
                repo=self.repo,
                app_root=self.app,
                tmpfs_root=self.tmpfs,
                restic_binary=self.restic_binary,
                max_file_bytes=1024,
                max_total_bytes=4096,
                confirmation="NO",
                tag="cabinet-test",
            )
        plan.assert_not_called()
        self.assertEqual(list(self.tmpfs.iterdir()), [])

    def test_restic_context_rejects_inline_or_command_passwords(self) -> None:
        base = {
            "RESTIC_REPOSITORY": "rest:synthetic",
            "RESTIC_PASSWORD_FILE": str(self.password_file),
        }
        with (
            mock.patch.dict(
                os.environ, {**base, "RESTIC_PASSWORD": "secret"}, clear=True
            ),
            self.assertRaisesRegex(
                HANDOFF.HandoffError, "inline_restic_password_rejected"
            ),
        ):
            HANDOFF._restic_context(self.restic_binary)
        with (
            mock.patch.dict(
                os.environ,
                {**base, "RESTIC_PASSWORD_COMMAND": "echo secret"},
                clear=True,
            ),
            self.assertRaisesRegex(
                HANDOFF.HandoffError, "restic_password_command_rejected"
            ),
        ):
            HANDOFF._restic_context(self.restic_binary)

    def test_password_file_parent_symlink_is_rejected(self) -> None:
        real_parent = self.root / "real-password-parent"
        real_parent.mkdir()
        password = real_parent / "password"
        password.write_text("secret\n", encoding="utf-8")
        os.chmod(password, 0o600)
        linked_parent = self.root / "linked-password-parent"
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        environment = {
            "RESTIC_REPOSITORY": "rest:synthetic",
            "RESTIC_PASSWORD_FILE": str(linked_parent / "password"),
        }
        with (
            mock.patch.dict(os.environ, environment, clear=True),
            self.assertRaisesRegex(
                HANDOFF.HandoffError,
                "restic_password_parent_symlink_rejected",
            ),
        ):
            HANDOFF._restic_context(self.restic_binary)

    def test_tag_probe_is_read_only_and_requires_empty_result(self) -> None:
        with mock.patch.dict(os.environ, self.environment, clear=True):
            context = HANDOFF._restic_context(self.restic_binary)
        run = mock.Mock(
            side_effect=[
                subprocess.CompletedProcess([], 0, "[]", ""),
                subprocess.CompletedProcess([], 0, json.dumps([{"id": "c" * 64}]), ""),
            ]
        )
        with mock.patch.object(HANDOFF, "_run_restic", run):
            self.assertTrue(HANDOFF._restic_tag_is_unused(context, "unique-tag"))
            self.assertFalse(HANDOFF._restic_tag_is_unused(context, "used-tag"))
        self.assertEqual(
            run.call_args_list[0].args[1],
            ["snapshots", "--tag", "unique-tag", "--json"],
        )
        self.assertTrue(run.call_args_list[0].kwargs["read_only"])

    def test_plan_is_read_only_and_reports_blocked_coverage(self) -> None:
        run = mock.Mock(
            return_value=subprocess.CompletedProcess(
                args=[], returncode=0, stdout="[]", stderr=""
            )
        )
        archive_receipt = {
            "scope": {"entries": 2, "bytes": 20, "databases": 1},
            "backup_status": {
                "manifest_present": False,
                "integrity_verified": False,
                "live_database_method": "sqlite_online_backup",
            },
            "coverage_gaps": ["runtime_state_missing"],
        }
        with (
            mock.patch.dict(os.environ, self.environment, clear=True),
            mock.patch.object(
                HANDOFF,
                "_validate_tmpfs",
                return_value={
                    "filesystem": "tmpfs",
                    "swap_policy": "none_or_encrypted",
                    "capacity_sufficient": True,
                },
            ),
            mock.patch.object(HANDOFF, "_run_restic", run),
            mock.patch.object(
                ARCHIVE, "plan_archive", return_value=archive_receipt
            ) as archive_plan,
        ):
            receipt = HANDOFF.plan_handoff(
                home=self.home,
                repo=self.repo,
                app_root=self.app,
                tmpfs_root=self.tmpfs,
                restic_binary=self.restic_binary,
                max_file_bytes=1024,
                max_total_bytes=4096,
            )
        self.assertEqual(receipt["status"], "blocked")
        self.assertEqual(run.call_count, 1)
        arguments = run.call_args.args[1]
        self.assertEqual(arguments, ["snapshots", "--json"])
        self.assertTrue(run.call_args.kwargs["read_only"])
        archive_plan.assert_called_once()
        self.assertEqual(list(self.tmpfs.iterdir()), [])

    def test_plan_blocks_without_symlink_safe_cleanup(self) -> None:
        with (
            mock.patch.object(
                shutil.rmtree,
                "avoids_symlink_attacks",
                False,
                create=True,
            ),
            self.assertRaisesRegex(
                HANDOFF.HandoffError,
                "safe_staging_cleanup_unavailable",
            ),
        ):
            HANDOFF._validate_tmpfs(self.tmpfs, 4096)

    def test_zram_swap_is_accepted_without_lsblk_probe(self) -> None:
        swapon = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="/dev/zram0\n", stderr=""
        )
        with (
            mock.patch.object(shutil, "which", side_effect=lambda name: f"/{name}"),
            mock.patch.object(subprocess, "run", return_value=swapon) as run,
        ):
            self.assertTrue(HANDOFF._active_swap_is_safe())
        run.assert_called_once()

    def test_plain_swap_is_rejected(self) -> None:
        responses = [
            subprocess.CompletedProcess(
                args=[], returncode=0, stdout="/dev/sda2\n", stderr=""
            ),
            subprocess.CompletedProcess(
                args=[], returncode=0, stdout="part\n", stderr=""
            ),
        ]
        with (
            mock.patch.object(shutil, "which", side_effect=lambda name: f"/{name}"),
            mock.patch.object(subprocess, "run", side_effect=responses),
        ):
            self.assertFalse(HANDOFF._active_swap_is_safe())

    def test_execution_lock_rejects_parallel_handoff(self) -> None:
        with (
            mock.patch.object(HANDOFF, "_filesystem_type", return_value="tmpfs"),
            HANDOFF._exclusive_execution_lock(self.tmpfs),
            self.assertRaisesRegex(HANDOFF.HandoffError, "handoff_already_running"),
            HANDOFF._exclusive_execution_lock(self.tmpfs),
        ):
            self.fail("parallel lock unexpectedly acquired")
        with (
            mock.patch.object(HANDOFF, "_filesystem_type", return_value="tmpfs"),
            HANDOFF._exclusive_execution_lock(self.tmpfs),
        ):
            pass
        lock_path = self.tmpfs / ".cabinet-private-restic-handoff.lock"
        self.assertTrue(lock_path.is_file())
        self.assertEqual(lock_path.stat().st_mode & 0o077, 0)

    def test_existing_tag_blocks_before_staging(self) -> None:
        with (
            mock.patch.dict(os.environ, self.environment, clear=True),
            mock.patch.object(HANDOFF, "plan_handoff", return_value=self._plan_ready()),
            mock.patch.object(HANDOFF, "_validate_tmpfs"),
            mock.patch.object(HANDOFF, "_restic_tag_is_unused", return_value=False),
            mock.patch.object(
                HANDOFF,
                "_exclusive_execution_lock",
                return_value=contextlib.nullcontext(),
            ),
            self.assertRaisesRegex(HANDOFF.HandoffError, "snapshot_tag_already_exists"),
        ):
            HANDOFF.execute_handoff(
                home=self.home,
                repo=self.repo,
                app_root=self.app,
                tmpfs_root=self.tmpfs,
                restic_binary=self.restic_binary,
                max_file_bytes=1024,
                max_total_bytes=4096,
                confirmation=HANDOFF.EXECUTION_CONFIRMATION,
                tag="cabinet-test",
            )
        self.assertEqual(list(self.tmpfs.iterdir()), [])

    def test_restic_context_detects_binary_or_password_replacement(self) -> None:
        with mock.patch.dict(os.environ, self.environment, clear=True):
            context = HANDOFF._restic_context(self.restic_binary)
            self.restic_binary.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            with self.assertRaisesRegex(HANDOFF.HandoffError, "restic_binary_changed"):
                HANDOFF._run_restic(context, ["snapshots", "--json"], read_only=True)

            context = HANDOFF._restic_context(self.restic_binary)
            self.password_file.write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(
                HANDOFF.HandoffError, "restic_password_file_changed"
            ):
                HANDOFF._run_restic(context, ["snapshots", "--json"], read_only=True)

    def test_snapshot_summary_parser_accepts_short_and_full_ids(self) -> None:
        short_id = "a1b2c3d4"
        full_id = "b" * 64
        for snapshot_id in (short_id, full_id.upper()):
            output = json.dumps({"message_type": "summary", "snapshot_id": snapshot_id})
            self.assertEqual(
                HANDOFF._parse_snapshot_summary_id(output),
                snapshot_id.lower(),
            )

    def test_snapshot_summary_parser_rejects_missing_malformed_or_ambiguous_ids(
        self,
    ) -> None:
        cases = [
            ("{}\n", "restic_snapshot_id_missing"),
            (
                json.dumps({"message_type": "summary", "snapshot_id": "abc1234"}),
                "restic_snapshot_id_invalid",
            ),
            (
                json.dumps({"message_type": "summary", "snapshot_id": "g" * 8}),
                "restic_snapshot_id_invalid",
            ),
            (
                "\n".join(
                    [
                        json.dumps({"message_type": "summary", "snapshot_id": "a" * 8}),
                        json.dumps({"message_type": "summary", "snapshot_id": "b" * 8}),
                    ]
                ),
                "restic_snapshot_id_ambiguous",
            ),
        ]
        for output, error_code in cases:
            with (
                self.subTest(error_code=error_code),
                self.assertRaisesRegex(HANDOFF.HandoffError, error_code),
            ):
                HANDOFF._parse_snapshot_summary_id(output)

    def test_full_snapshot_resolution_requires_one_matching_tagged_id(self) -> None:
        full_id = "abc12345" + "d" * 56
        self.assertEqual(
            HANDOFF._resolve_full_snapshot_id("abc12345", [full_id]),
            full_id,
        )
        self.assertEqual(
            HANDOFF._resolve_full_snapshot_id(full_id, [full_id]),
            full_id,
        )
        for tagged_ids in ([], [full_id, "e" * 64], ["short-id"]):
            with (
                self.subTest(tagged_ids=tagged_ids),
                self.assertRaisesRegex(
                    HANDOFF.HandoffError, "snapshot_tag_binding_failed"
                ),
            ):
                HANDOFF._resolve_full_snapshot_id("abc12345", tagged_ids)
        with self.assertRaisesRegex(
            HANDOFF.HandoffError, "snapshot_summary_id_mismatch"
        ):
            HANDOFF._resolve_full_snapshot_id("deadbeef", [full_id])

    def test_short_summary_id_restores_exact_full_tagged_snapshot(self) -> None:
        snapshot_id = "abc12345" + "f" * 56
        snapshot_store = self.root / "short-id-snapshot-store"
        commands: list[list[str]] = []

        def run_restic(
            _context: HANDOFF.ResticContext,
            arguments: list[str],
            *,
            read_only: bool,
            timeout_seconds: int = 120,
        ) -> subprocess.CompletedProcess[str]:
            del _context, timeout_seconds
            self.assertFalse(read_only)
            commands.append(arguments)
            if arguments[0] == "backup":
                shutil.copytree(Path(arguments[-1]), snapshot_store)
                output = json.dumps(
                    {"message_type": "summary", "snapshot_id": "abc12345"}
                )
                return subprocess.CompletedProcess([], 0, output + "\n", "")
            if arguments[0] == "restore":
                self.assertEqual(arguments[1], snapshot_id)
                target = Path(arguments[arguments.index("--target") + 1])
                shutil.copytree(snapshot_store, target / "archive")
                return subprocess.CompletedProcess([], 0, "", "")
            self.fail(f"unexpected Restic command: {arguments}")

        receipt = self._execute(
            mock.Mock(side_effect=run_restic),
            snapshot_id=snapshot_id,
        )
        self.assertEqual(receipt["status"], "snapshot_verified")
        self.assertEqual([command[0] for command in commands], ["backup", "restore"])
        self.assertEqual(
            receipt["snapshot"]["id_sha256"], HANDOFF._sha256_text(snapshot_id)
        )

    def test_short_summary_prefix_mismatch_stops_before_restore(self) -> None:
        full_id = "abc12345" + "f" * 56
        run = mock.Mock(
            return_value=subprocess.CompletedProcess(
                [],
                0,
                json.dumps({"message_type": "summary", "snapshot_id": "deadbeef"})
                + "\n",
                "",
            )
        )
        with self.assertRaises(HANDOFF.HandoffError) as raised:
            self._execute(run, snapshot_id=full_id)
        self.assertEqual(raised.exception.code, "snapshot_summary_id_mismatch")
        self.assertTrue(raised.exception.snapshot_may_exist)
        self.assertEqual(run.call_count, 1)

    def test_execute_creates_one_snapshot_restores_verifies_and_cleans(self) -> None:
        snapshot_id = "a" * 64
        snapshot_store = self.root / "snapshot-store"
        commands: list[list[str]] = []

        def run_restic(
            _context: HANDOFF.ResticContext,
            arguments: list[str],
            *,
            read_only: bool,
            timeout_seconds: int = 120,
        ) -> subprocess.CompletedProcess[str]:
            del timeout_seconds
            self.assertFalse(read_only)
            self.assertIn("TMPDIR", _context.environment)
            self.assertTrue(Path(_context.environment["TMPDIR"]).is_dir())
            self.assertEqual(os.environ.get("TMPDIR"), os.environ.get("SQLITE_TMPDIR"))
            self.assertTrue(
                str(os.environ.get("SQLITE_TMPDIR", "")).startswith(str(self.tmpfs))
            )
            self.assertTrue(
                str(_context.environment["TMPDIR"]).startswith(str(self.tmpfs))
            )
            commands.append(arguments)
            if arguments[0] == "backup":
                source = Path(arguments[-1])
                shutil.copytree(source, snapshot_store)
                output = json.dumps(
                    {"message_type": "summary", "snapshot_id": snapshot_id}
                )
                return subprocess.CompletedProcess([], 0, output + "\n", "")
            if arguments[0] == "restore":
                target = Path(arguments[arguments.index("--target") + 1])
                shutil.copytree(snapshot_store, target / "archive")
                return subprocess.CompletedProcess([], 0, "", "")
            self.fail(f"unexpected Restic command: {arguments}")

        receipt = self._execute(mock.Mock(side_effect=run_restic))
        self.assertEqual(receipt["status"], "snapshot_verified")
        self.assertTrue(receipt["snapshot"]["exact_restore_verified"])
        self.assertTrue(receipt["staging"]["removed"])
        self.assertFalse(receipt["retention_mutated"])
        self.assertEqual([command[0] for command in commands], ["backup", "restore"])
        self.assertFalse(
            any(
                item.name.startswith("cabinet-private-restic-")
                for item in self.tmpfs.iterdir()
            )
        )
        serialized = json.dumps(receipt, sort_keys=True)
        self.assertNotIn(snapshot_id, serialized)
        self.assertNotIn("cabinet-t012-test", serialized)
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn("synthetic-repository", serialized)
        self.assertNotIn(self.password_file.name, serialized)

    def test_success_without_snapshot_id_reports_snapshot_may_exist_and_cleans(
        self,
    ) -> None:
        run = mock.Mock(return_value=subprocess.CompletedProcess([], 0, "{}\n", ""))
        with self.assertRaises(HANDOFF.HandoffError) as raised:
            self._execute(run)
        self.assertEqual(raised.exception.code, "restic_snapshot_id_missing")
        self.assertTrue(raised.exception.snapshot_may_exist)
        self.assertFalse(raised.exception.staging_cleanup_required)
        self.assertEqual(run.call_count, 1)
        self.assertFalse(
            any(
                item.name.startswith("cabinet-private-restic-")
                for item in self.tmpfs.iterdir()
            )
        )

    def test_invalid_summary_stops_after_one_backup_without_restore(self) -> None:
        run = mock.Mock(
            return_value=subprocess.CompletedProcess(
                [],
                0,
                json.dumps({"message_type": "summary", "snapshot_id": "not-hex-id"})
                + "\n",
                "",
            )
        )
        with self.assertRaises(HANDOFF.HandoffError) as raised:
            self._execute(run)
        self.assertEqual(raised.exception.code, "restic_snapshot_id_invalid")
        self.assertTrue(raised.exception.snapshot_may_exist)
        self.assertEqual(run.call_count, 1)

    def test_restore_failure_reports_snapshot_may_exist_and_cleans(self) -> None:
        snapshot_id = "b" * 64
        responses = [
            subprocess.CompletedProcess(
                [],
                0,
                json.dumps({"message_type": "summary", "snapshot_id": snapshot_id})
                + "\n",
                "",
            ),
            subprocess.CompletedProcess([], 1, "", "restore failed"),
        ]
        with self.assertRaises(HANDOFF.HandoffError) as raised:
            self._execute(mock.Mock(side_effect=responses), snapshot_id=snapshot_id)
        self.assertEqual(raised.exception.code, "restic_restore_failed")
        self.assertTrue(raised.exception.snapshot_may_exist)
        self.assertEqual(
            raised.exception.snapshot_id_sha256,
            HANDOFF._sha256_text(snapshot_id),
        )
        self.assertFalse(
            any(
                item.name.startswith("cabinet-private-restic-")
                for item in self.tmpfs.iterdir()
            )
        )

    def test_archive_error_is_preserved_and_stage_is_removed(self) -> None:
        with (
            mock.patch.dict(os.environ, self.environment, clear=True),
            mock.patch.object(HANDOFF, "plan_handoff", return_value=self._plan_ready()),
            mock.patch.object(HANDOFF, "_validate_tmpfs"),
            mock.patch.object(
                ARCHIVE,
                "export_archive",
                side_effect=ARCHIVE.ArchiveError("coverage_gaps_present"),
            ),
            mock.patch.object(HANDOFF, "_restic_tag_is_unused", return_value=True),
            mock.patch.object(
                HANDOFF,
                "_exclusive_execution_lock",
                return_value=contextlib.nullcontext(),
            ),
            self.assertRaisesRegex(
                HANDOFF.HandoffError, "archive_coverage_gaps_present"
            ),
        ):
            HANDOFF.execute_handoff(
                home=self.home,
                repo=self.repo,
                app_root=self.app,
                tmpfs_root=self.tmpfs,
                restic_binary=self.restic_binary,
                max_file_bytes=1024,
                max_total_bytes=4096,
                confirmation=HANDOFF.EXECUTION_CONFIRMATION,
                tag="cabinet-test",
            )
        self.assertEqual(list(self.tmpfs.iterdir()), [])

    def test_cleanup_failure_is_explicit(self) -> None:
        with (
            mock.patch.dict(os.environ, self.environment, clear=True),
            mock.patch.object(HANDOFF, "plan_handoff", return_value=self._plan_ready()),
            mock.patch.object(HANDOFF, "_validate_tmpfs"),
            mock.patch.object(
                ARCHIVE,
                "export_archive",
                side_effect=ARCHIVE.ArchiveError("synthetic"),
            ),
            mock.patch.object(HANDOFF, "_remove_stage", return_value=False),
            mock.patch.object(HANDOFF, "_restic_tag_is_unused", return_value=True),
            mock.patch.object(
                HANDOFF,
                "_exclusive_execution_lock",
                return_value=contextlib.nullcontext(),
            ),
            self.assertRaises(HANDOFF.HandoffError) as raised,
        ):
            HANDOFF.execute_handoff(
                home=self.home,
                repo=self.repo,
                app_root=self.app,
                tmpfs_root=self.tmpfs,
                restic_binary=self.restic_binary,
                max_file_bytes=1024,
                max_total_bytes=4096,
                confirmation=HANDOFF.EXECUTION_CONFIRMATION,
                tag="cabinet-test",
            )
        self.assertEqual(raised.exception.code, "staging_cleanup_failed")
        self.assertTrue(raised.exception.staging_cleanup_required)

    def test_backup_nonzero_conservatively_reports_snapshot_may_exist(self) -> None:
        run = mock.Mock(
            return_value=subprocess.CompletedProcess([], 3, "", "partial backup")
        )
        with self.assertRaises(HANDOFF.HandoffError) as raised:
            self._execute(run)
        self.assertEqual(raised.exception.code, "restic_backup_failed")
        self.assertTrue(raised.exception.snapshot_may_exist)
        self.assertFalse(raised.exception.staging_cleanup_required)
        self.assertFalse(
            any(
                item.name.startswith("cabinet-private-restic-")
                for item in self.tmpfs.iterdir()
            )
        )

    def test_backup_command_uncertainty_reports_snapshot_may_exist(self) -> None:
        run = mock.Mock(side_effect=HANDOFF.HandoffError("restic_command_failed"))
        with self.assertRaises(HANDOFF.HandoffError) as raised:
            self._execute(run)
        self.assertEqual(raised.exception.code, "restic_command_failed")
        self.assertTrue(raised.exception.snapshot_may_exist)
        self.assertFalse(
            any(
                item.name.startswith("cabinet-private-restic-")
                for item in self.tmpfs.iterdir()
            )
        )

    def test_post_backup_tag_collision_blocks_restore_and_reports_snapshot(
        self,
    ) -> None:
        snapshot_id = "d" * 64
        run = mock.Mock(
            return_value=subprocess.CompletedProcess(
                [],
                0,
                json.dumps({"message_type": "summary", "snapshot_id": snapshot_id})
                + "\n",
                "",
            )
        )
        with self.assertRaises(HANDOFF.HandoffError) as raised:
            self._execute(
                run,
                snapshot_id=snapshot_id,
                tagged_snapshot_ids=[snapshot_id, "e" * 64],
            )
        self.assertEqual(raised.exception.code, "snapshot_tag_binding_failed")
        self.assertTrue(raised.exception.snapshot_may_exist)
        self.assertEqual(
            raised.exception.snapshot_id_sha256,
            HANDOFF._sha256_text(snapshot_id),
        )
        self.assertEqual(run.call_count, 1)

    def test_stage_setup_error_is_cleaned(self) -> None:
        with (
            mock.patch.dict(os.environ, self.environment, clear=True),
            mock.patch.object(HANDOFF, "plan_handoff", return_value=self._plan_ready()),
            mock.patch.object(HANDOFF, "_validate_tmpfs"),
            mock.patch.object(HANDOFF, "_restic_tag_is_unused", return_value=True),
            mock.patch.object(
                HANDOFF,
                "_context_with_tmpdir",
                side_effect=HANDOFF.HandoffError("restic_tmpdir_invalid"),
            ),
            mock.patch.object(
                HANDOFF,
                "_exclusive_execution_lock",
                return_value=contextlib.nullcontext(),
            ),
            self.assertRaisesRegex(HANDOFF.HandoffError, "restic_tmpdir_invalid"),
        ):
            HANDOFF.execute_handoff(
                home=self.home,
                repo=self.repo,
                app_root=self.app,
                tmpfs_root=self.tmpfs,
                restic_binary=self.restic_binary,
                max_file_bytes=1024,
                max_total_bytes=4096,
                confirmation=HANDOFF.EXECUTION_CONFIRMATION,
                tag="cabinet-test",
            )
        self.assertEqual(list(self.tmpfs.iterdir()), [])

    def test_tmpfs_is_revalidated_inside_execution_lock(self) -> None:
        locked_execute = mock.Mock()
        with (
            mock.patch.object(HANDOFF, "plan_handoff", return_value=self._plan_ready()),
            mock.patch.object(
                HANDOFF,
                "_exclusive_execution_lock",
                return_value=contextlib.nullcontext(),
            ),
            mock.patch.object(
                HANDOFF,
                "_validate_tmpfs",
                side_effect=HANDOFF.HandoffError("unencrypted_swap_active"),
            ),
            mock.patch.object(HANDOFF, "_execute_handoff_locked", locked_execute),
            self.assertRaisesRegex(HANDOFF.HandoffError, "unencrypted_swap_active"),
        ):
            HANDOFF.execute_handoff(
                home=self.home,
                repo=self.repo,
                app_root=self.app,
                tmpfs_root=self.tmpfs,
                restic_binary=self.restic_binary,
                max_file_bytes=1024,
                max_total_bytes=4096,
                confirmation=HANDOFF.EXECUTION_CONFIRMATION,
                tag="cabinet-test",
            )
        locked_execute.assert_not_called()

    def test_stage_creation_identity_failure_removes_empty_directory(self) -> None:
        with (
            mock.patch.object(
                HANDOFF,
                "_stage_identity",
                side_effect=HANDOFF.HandoffError("staging_identity_invalid"),
            ),
            self.assertRaisesRegex(HANDOFF.HandoffError, "staging_identity_invalid"),
        ):
            HANDOFF._create_stage(self.tmpfs)
        self.assertEqual(list(self.tmpfs.iterdir()), [])

    def test_stage_creation_cleanup_failure_is_explicit(self) -> None:
        with (
            mock.patch.object(
                HANDOFF,
                "_stage_identity",
                side_effect=HANDOFF.HandoffError("staging_identity_invalid"),
            ),
            mock.patch.object(Path, "rmdir", side_effect=OSError("synthetic")),
            self.assertRaises(HANDOFF.HandoffError) as raised,
        ):
            HANDOFF._create_stage(self.tmpfs)
        self.assertEqual(raised.exception.code, "staging_create_cleanup_failed")
        self.assertTrue(raised.exception.staging_cleanup_required)

    def test_restored_tree_symlink_and_ambiguity_are_rejected(self) -> None:
        restore = self.root / "restore"
        first = restore / "one"
        first.mkdir(parents=True)
        (first / "manifest.json").write_text("{}", encoding="utf-8")
        (first / "manifest.sha256").write_text("x", encoding="utf-8")
        (first / "payload").mkdir()
        outside = self.root / "outside"
        outside.mkdir()
        (restore / "link").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(
            HANDOFF.HandoffError, "restored_archive_symlink_rejected"
        ):
            HANDOFF._find_restored_archive(restore)
        (restore / "link").unlink()
        second = restore / "two"
        shutil.copytree(first, second)
        with self.assertRaisesRegex(HANDOFF.HandoffError, "restored_archive_ambiguous"):
            HANDOFF._find_restored_archive(restore)

    def test_source_contains_no_retention_commands(self) -> None:
        source = (ROOT / "scripts/private_cabinet_restic_handoff.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn('"forget"', source)
        self.assertNotIn('"prune"', source)

    def test_execute_error_receipt_uses_hashes_not_raw_locator(self) -> None:
        stderr = io.StringIO()
        snapshot_id_sha256 = "f" * 64
        raw_tag = "private-cabinet-tag"
        with (
            mock.patch.object(
                HANDOFF,
                "execute_handoff",
                side_effect=HANDOFF.HandoffError(
                    "restic_restore_failed",
                    snapshot_may_exist=True,
                    snapshot_id_sha256=snapshot_id_sha256,
                ),
            ),
            contextlib.redirect_stderr(stderr),
        ):
            result = HANDOFF.main(
                [
                    "execute",
                    "--home",
                    str(self.home),
                    "--repo",
                    str(self.repo),
                    "--confirm",
                    HANDOFF.EXECUTION_CONFIRMATION,
                    "--tag",
                    raw_tag,
                ]
            )
        receipt = json.loads(stderr.getvalue())
        self.assertEqual(result, 2)
        self.assertTrue(receipt["snapshot_may_exist"])
        self.assertEqual(receipt["snapshot_id_sha256"], snapshot_id_sha256)
        self.assertEqual(receipt["tag_sha256"], HANDOFF._sha256_text(raw_tag))
        self.assertNotIn(raw_tag, stderr.getvalue())

    def test_cli_error_receipt_is_redacted(self) -> None:
        stderr = io.StringIO()
        with (
            mock.patch.object(
                HANDOFF,
                "plan_handoff",
                side_effect=OSError("/private/secret/repository"),
            ),
            contextlib.redirect_stderr(stderr),
        ):
            result = HANDOFF.main(
                [
                    "plan",
                    "--home",
                    str(self.home),
                    "--repo",
                    str(self.repo),
                ]
            )
        output = stderr.getvalue()
        self.assertEqual(result, 2)
        self.assertIn("unexpected_failure", output)
        self.assertNotIn("/private/secret", output)
        self.assertNotIn("repository", output.replace(HANDOFF.RECEIPT_KIND, ""))


if __name__ == "__main__":
    unittest.main()
