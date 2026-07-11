from __future__ import annotations

import copy
import hashlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_runtime_retirement_preflight as VALIDATOR  # noqa: E402
import write_runtime_retirement_preflight as WRITER  # noqa: E402


class RuntimeRetirementPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.private_path = self.root / "private.json"
        self.public_path = self.root / "public.json"
        self.private = self._private_fixture()
        self._write_private(self.private)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _private_fixture(self) -> dict[str, object]:
        false_effects = {
            "service_mutation_performed": False,
            "runtime_mutation_performed": False,
            "private_data_mutation_performed": False,
            "backup_or_restore_performed": False,
            "retention_change_performed": False,
            "repository_rename_performed": False,
            "effect_authorized": False,
        }
        return {
            "schema_version": 1,
            "kind": "cabinet_runtime_retirement_private_preflight",
            "task_id": "OPERATOR-ECOSYSTEM-REDUNDANCY-V1-T013",
            "observed_at": "2026-07-11T07:30:00Z",
            "repository": {
                "path": "/home/test/repos/cabinet",
                "head": "0" * 40,
                "clean": True,
            },
            "service": {
                "unit": "cabinet.service",
                "properties": {
                    "LoadState": "loaded",
                    "ActiveState": "active",
                    "SubState": "running",
                    "UnitFileState": "enabled",
                    "Result": "success",
                    "NRestarts": "0",
                    "MainPID": "101",
                    "FragmentPath": "/home/test/.config/systemd/user/cabinet.service",
                    "DropInPaths": "/home/test/.config/systemd/user/cabinet.service.d/gate.conf",
                },
                "key_files": [
                    {
                        "path": "/home/test/.local/bin/cabinet",
                        "bytes": 42,
                        "mode": "0o755",
                        "sha256": "a" * 64,
                    }
                ],
                "enabled_link": "/home/test/.config/systemd/user/default.target.wants/cabinet.service",
            },
            "runtime": {
                "observed_version": "0.5.0",
                "repository_contract_version": "0.4.4",
                "processes": [
                    {
                        "pid": 101,
                        "ppid": 1,
                        "command": "node",
                        "argv": "/usr/bin/node /home/test/app/index.js",
                    },
                    {
                        "pid": 102,
                        "ppid": 101,
                        "command": "node",
                        "argv": "next dev -H 127.0.0.1 -p 45001",
                    },
                ],
                "listeners": [
                    {
                        "address": "127.0.0.1",
                        "port": 45001,
                        "raw_sha256": "b" * 64,
                    },
                    {
                        "address": "127.0.0.1",
                        "port": 45002,
                        "raw_sha256": "c" * 64,
                    },
                ],
                "trees": {
                    "app_runtime": {
                        "path": "/home/test/.cabinet/app/v0.5.0",
                        "exists": True,
                        "regular_files": 20,
                        "directories": 4,
                        "symlinks": 2,
                        "bytes": 2_000_000,
                    },
                    "cli_distribution": {
                        "path": "/home/test/.local/share/cabinet/cabinetai-0.5.0",
                        "exists": True,
                        "regular_files": 3,
                        "directories": 1,
                        "symlinks": 0,
                        "bytes": 250_000,
                    },
                    "state": {
                        "path": "/home/test/.local/state/cabinet",
                        "exists": True,
                        "regular_files": 7,
                        "directories": 2,
                        "symlinks": 0,
                        "bytes": 10_000,
                    },
                    "config": {
                        "path": "/home/test/.config/cabinet",
                        "exists": True,
                        "regular_files": 2,
                        "directories": 1,
                        "symlinks": 0,
                        "bytes": 500,
                    },
                },
                "private_log": {
                    "exists": True,
                    "path": "/home/test/.local/state/cabinet/cabinet.log",
                    "bytes": 1000,
                    "mode": "0o600",
                    "sha256": "d" * 64,
                    "start_markers": 4,
                    "last_start_marker": "2026-07-08T20:05:18+02:00",
                    "stop_markers": 0,
                    "error_word_lines": 0,
                },
            },
            "existing_runtime_audit": {
                "returncode": 1,
                "first_stop_reason": "Lokales Werkzeug driftet: cabinet",
                "stdout_sha256": "e" * 64,
                "stderr_sha256": "f" * 64,
            },
            "dependencies": {
                "T004": {"state": "verified", "merge_commit": "1" * 40},
                "T007": {
                    "state": "verified",
                    "public_snapshot_sha256": "2" * 64,
                    "private_evidence_sha256": "3" * 64,
                },
                "T012": {"state": "verified", "receipt_sha256": "4" * 64},
                "T018": {"state": "verified", "receipt_sha256": "5" * 64},
            },
            "effect_boundary": false_effects,
            "residual_uncertainty": [
                "one registered location unreachable",
                "Cabinet human use not directly measured",
            ],
        }

    def _write_private(self, value: dict[str, object]) -> None:
        self.private_path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _write_public(self, value: dict[str, object]) -> None:
        self.public_path.write_text(
            WRITER.render(value),
            encoding="utf-8",
        )

    def test_repository_snapshot_is_valid(self) -> None:
        result = VALIDATOR.validate(VALIDATOR.DEFAULT_INPUT)
        snapshot = json.loads(VALIDATOR.DEFAULT_INPUT.read_text(encoding="utf-8"))
        self.assertTrue(result["valid"])
        self.assertEqual(result["processCount"], 8)
        self.assertEqual(result["listenerCount"], 2)
        self.assertEqual(
            snapshot["privateEvidenceSha256"],
            "d152176b79dd2365a31ea0dc34a8c5049a6bff456fd2616bc17ff1d99d8a060b",
        )
        self.assertFalse(result["runtimeEffectAuthorized"])
        self.assertFalse(result["repositoryRenameAuthorized"])

    def test_repository_wiring_keeps_preflight_non_authoritative(self) -> None:
        workflow = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        index = (ROOT / "index.md").read_text(encoding="utf-8")
        authorization = (
            ROOT / "docs/migration/cabinet-runtime-retirement-authorization-v1.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Validate Runtime Retirement Preflight", workflow)
        self.assertIn("Test Runtime Retirement Preflight", workflow)
        self.assertIn("keine Live- oder Abschaltautorität", agents)
        self.assertIn("autorisiert jedoch keine Wirkung", readme)
        self.assertIn("ohne Abschaltfreigabe", index)
        self.assertIn("nicht autorisiert und nicht ausgeführt", authorization)

    def test_projection_redacts_paths_ports_and_process_ids(self) -> None:
        snapshot = WRITER.build_public_snapshot(self.private_path)
        text = WRITER.render(snapshot)
        self.assertNotIn("/home/test", text)
        self.assertNotIn("127.0.0.1", text)
        self.assertNotIn('"port"', text.lower())
        self.assertNotIn('"pid"', text.lower())
        self.assertNotIn('"argv"', text.lower())
        self.assertEqual(snapshot["runtimeObservation"]["processCount"], 2)
        self.assertEqual(snapshot["runtimeObservation"]["listenerCount"], 2)
        self.assertEqual(
            snapshot["privateEvidenceSha256"],
            hashlib.sha256(self.private_path.read_bytes()).hexdigest(),
        )
        self._write_public(snapshot)
        self.assertTrue(VALIDATOR.validate(self.public_path)["valid"])

    def test_projection_refuses_any_effect_or_authorization(self) -> None:
        for key in self.private["effect_boundary"]:
            changed = copy.deepcopy(self.private)
            changed["effect_boundary"][key] = True
            self._write_private(changed)
            with (
                self.subTest(key=key),
                self.assertRaisesRegex(
                    WRITER.PreflightProjectionError,
                    "no-effect, unauthorized preflight",
                ),
            ):
                WRITER.build_public_snapshot(self.private_path)

    def test_projection_refuses_non_loopback_listener(self) -> None:
        changed = copy.deepcopy(self.private)
        changed["runtime"]["listeners"][0]["address"] = "0.0.0.0"
        self._write_private(changed)
        with self.assertRaisesRegex(WRITER.PreflightProjectionError, "loopback-only"):
            WRITER.build_public_snapshot(self.private_path)

    def test_validator_refuses_runtime_or_rename_authorization(self) -> None:
        for key in ("runtimeEffectAuthorized", "repositoryRenameAuthorized"):
            snapshot = WRITER.build_public_snapshot(self.private_path)
            snapshot["decision"][key] = True
            self._write_public(snapshot)
            with (
                self.subTest(key=key),
                self.assertRaisesRegex(
                    VALIDATOR.PreflightValidationError, "must remain unauthorized"
                ),
            ):
                VALIDATOR.validate(self.public_path)

    def test_validator_refuses_private_path_and_port_detail(self) -> None:
        for field, value in (
            ("privatePath", "/home/test/private"),
            ("listenerDetail", "127.0.0.1:45001"),
        ):
            snapshot = WRITER.build_public_snapshot(self.private_path)
            snapshot["runtimeObservation"][field] = value
            self._write_public(snapshot)
            with (
                self.subTest(field=field),
                self.assertRaises(VALIDATOR.PreflightValidationError),
            ):
                VALIDATOR.validate(self.public_path)

    def test_validator_refuses_executed_rollback_phase(self) -> None:
        snapshot = WRITER.build_public_snapshot(self.private_path)
        snapshot["rollbackPlan"]["phaseA"]["executed"] = True
        self._write_public(snapshot)
        with self.assertRaisesRegex(
            VALIDATOR.PreflightValidationError, "must remain unexecuted"
        ):
            VALIDATOR.validate(self.public_path)

    def test_writer_check_mode_detects_staleness(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(
                WRITER.main(
                    [
                        "--private-evidence",
                        str(self.private_path),
                        "--output",
                        str(self.public_path),
                    ]
                ),
                0,
            )
        with redirect_stdout(io.StringIO()):
            self.assertEqual(
                WRITER.main(
                    [
                        "--private-evidence",
                        str(self.private_path),
                        "--output",
                        str(self.public_path),
                        "--check",
                    ]
                ),
                0,
            )
        self.public_path.write_text("{}\n", encoding="utf-8")
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(
                WRITER.main(
                    [
                        "--private-evidence",
                        str(self.private_path),
                        "--output",
                        str(self.public_path),
                        "--check",
                    ]
                ),
                1,
            )
        self.assertIn("stale", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
