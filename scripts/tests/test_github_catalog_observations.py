from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
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

    def test_global_deadline_caps_individual_command_timeout(self) -> None:
        success = subprocess.CompletedProcess(
            args=["gh", "api", "example"],
            returncode=0,
            stdout="{}",
            stderr="",
        )
        with (
            mock.patch.object(observer.time, "monotonic", return_value=100.0),
            mock.patch.object(observer.subprocess, "run", return_value=success) as run,
        ):
            self.assertEqual(
                observer._run(["gh", "api", "example"], deadline=102.5), "{}"
            )
        self.assertEqual(run.call_args.kwargs["timeout"], 2.5)

    def test_global_budget_exhaustion_stops_before_subprocess(self) -> None:
        with (
            mock.patch.object(observer.time, "monotonic", return_value=100.0),
            mock.patch.object(observer.subprocess, "run") as run,
        ):
            with self.assertRaisesRegex(
                observer.ObservationBudgetExceeded, "budget exhausted"
            ):
                observer._run(["gh", "api", "example"], deadline=100.0)
        run.assert_not_called()

    def _catalog_root(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        registry = root / "registry/ecosystem"
        registry.mkdir(parents=True)
        bindings = {
            "systems": [
                {
                    "source": {
                        "repository": "heimgewebe/public",
                        "locator": {"kind": "file", "path": "README.md"},
                    }
                },
                {
                    "source": {
                        "repository": "heimgewebe/public",
                        "locator": {"kind": "repository_metadata"},
                    }
                },
                {
                    "source": {
                        "repository": "heimgewebe/private",
                        "locator": {"kind": "private_repository_metadata"},
                    }
                },
                {
                    "source": {
                        "repository": "heimgewebe/public",
                        "locator": {"kind": "json_pointer"},
                    }
                },
            ]
        }
        scope = {
            "repositories": [
                {
                    "repository": "heimgewebe/private",
                    "visibility": "private",
                    "classification": "internal",
                    "node": "private-node",
                }
            ]
        }
        (registry / "source-bindings.v1.json").write_text(
            json.dumps(bindings), encoding="utf-8"
        )
        (registry / "organization-scope.v1.json").write_text(
            json.dumps(scope), encoding="utf-8"
        )
        return temp

    def _repo_list(self) -> str:
        return json.dumps(
            [
                {
                    "nameWithOwner": "heimgewebe/public",
                    "description": "public repo",
                    "visibility": "PUBLIC",
                    "isArchived": False,
                    "defaultBranchRef": {"name": "main"},
                },
                {
                    "nameWithOwner": "heimgewebe/private",
                    "description": None,
                    "visibility": "PRIVATE",
                    "isArchived": False,
                    "defaultBranchRef": {"name": "main"},
                },
            ]
        )

    def test_observe_preserves_order_and_deduplicates_head_lookup(self) -> None:
        commit = "a" * 40
        with self._catalog_root() as root_name:
            root = Path(root_name)
            with (
                mock.patch.object(observer, "_run", return_value=self._repo_list()),
                mock.patch.object(
                    observer,
                    "_gh_json",
                    return_value={"sha": commit},
                ) as gh_json,
                mock.patch.object(observer, "_run_bytes", return_value=b"hello") as run_bytes,
            ):
                result = observer.observe(root, budget_seconds=100)
        self.assertEqual(len(result["observations"]), 3)
        self.assertEqual(
            [item["locator"]["kind"] for item in result["observations"]],
            ["file", "repository_metadata", "private_repository_metadata"],
        )
        self.assertEqual(
            result["observations"][0]["contentSha256"],
            hashlib.sha256(b"hello").hexdigest(),
        )
        self.assertEqual(gh_json.call_count, 2)
        self.assertEqual(
            result["observations"][2]["defaultBranch"], "main"
        )
        run_bytes.assert_called_once()

    def test_observe_partial_provider_failure_is_fail_closed(self) -> None:
        commit = "b" * 40
        with self._catalog_root() as root_name:
            root = Path(root_name)
            with (
                mock.patch.object(observer, "_run", return_value=self._repo_list()),
                mock.patch.object(observer, "_gh_json", return_value={"sha": commit}),
                mock.patch.object(
                    observer, "_run_bytes", side_effect=RuntimeError("provider failed")
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "provider failed"):
                    observer.observe(root, budget_seconds=100)


if __name__ == "__main__":
    unittest.main()
