from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import read_github_catalog_observations as observer  # noqa: E402


class GithubCatalogObservationTests(unittest.TestCase):
    def test_binary_command_retries_transient_failure(self) -> None:
        failure = subprocess.CompletedProcess(
            args=["gh", "api", "example"],
            returncode=1,
            stdout=b"",
            stderr=b"temporary 502",
        )
        success = subprocess.CompletedProcess(
            args=["gh", "api", "example"],
            returncode=0,
            stdout=b"payload",
            stderr=b"",
        )
        with (
            mock.patch.object(observer.subprocess, "run", side_effect=[failure, success]) as run,
            mock.patch.object(observer.time, "sleep") as sleep,
        ):
            self.assertEqual(observer._run_bytes(["gh", "api", "example"]), b"payload")
        self.assertEqual(run.call_count, 2)
        sleep.assert_called_once_with(1)
        self.assertEqual(run.call_args.kwargs["timeout"], observer.COMMAND_TIMEOUT_SECONDS)

    def test_timeout_is_retried_and_then_succeeds(self) -> None:
        timeout = subprocess.TimeoutExpired(cmd=["gh", "api", "example"], timeout=20)
        success = subprocess.CompletedProcess(
            args=["gh", "api", "example"],
            returncode=0,
            stdout="{}",
            stderr="",
        )
        with (
            mock.patch.object(observer.subprocess, "run", side_effect=[timeout, success]),
            mock.patch.object(observer.time, "sleep") as sleep,
        ):
            self.assertEqual(observer._run(["gh", "api", "example"]), "{}")
        sleep.assert_called_once_with(1)

    def test_repeated_failure_is_explicit_not_a_missing_observation(self) -> None:
        failure = subprocess.CompletedProcess(
            args=["gh", "api", "example"],
            returncode=1,
            stdout=b"",
            stderr=b"upstream unavailable",
        )
        with (
            mock.patch.object(
                observer.subprocess,
                "run",
                side_effect=[failure, failure, failure],
            ),
            mock.patch.object(observer.time, "sleep"),
        ):
            with self.assertRaisesRegex(RuntimeError, "failed after 3 attempts"):
                observer._run_bytes(["gh", "api", "example"])


if __name__ == "__main__":
    unittest.main()
