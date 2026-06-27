from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import observer_guard  # noqa: E402
from repository_observer_fixture import ObserverFixture, run  # noqa: E402


class RepositoryObserverGuardTests(ObserverFixture, unittest.TestCase):
    def initialize_cabinet_git(self) -> None:
        run("git", "init", "-q", "-b", "main", str(self.cabinet))
        run("git", "-C", str(self.cabinet), "config", "user.name", "Guard Test")
        run(
            "git",
            "-C",
            str(self.cabinet),
            "config",
            "user.email",
            "guard@example.invalid",
        )

    def commit_inputs(self, policy: Path) -> None:
        run("git", "-C", str(self.cabinet), "add", policy.as_posix(), "references")
        run("git", "-C", str(self.cabinet), "commit", "-q", "-m", "inputs")

    def test_index_identical_policy_and_reference_pass(self) -> None:
        policy = self.write_policy([self.entry("alpha")])
        self.initialize_cabinet_git()
        self.commit_inputs(policy)
        loaded = observer_guard.load_verified_policy(self.cabinet, policy)
        self.assertEqual([entry.id for entry in loaded.entries], ["alpha"])

    def test_untracked_policy_fails_closed(self) -> None:
        policy = self.write_policy([self.entry("alpha")])
        self.initialize_cabinet_git()
        with self.assertRaisesRegex(observer_guard.ObserverGuardError, "ls-files"):
            observer_guard.load_verified_policy(self.cabinet, policy)

    def test_policy_working_tree_drift_fails_closed(self) -> None:
        policy = self.write_policy([self.entry("alpha")])
        self.initialize_cabinet_git()
        self.commit_inputs(policy)
        path = self.cabinet / policy
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        with self.assertRaisesRegex(observer_guard.ObserverGuardError, "indexed Git blob"):
            observer_guard.load_verified_policy(self.cabinet, policy)

    def test_reference_working_tree_drift_fails_closed(self) -> None:
        entry = self.entry("alpha")
        policy = self.write_policy([entry])
        self.initialize_cabinet_git()
        self.commit_inputs(policy)
        reference = self.cabinet / entry["reference"]
        reference.write_text(
            reference.read_text(encoding="utf-8") + "drift\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(observer_guard.ObserverGuardError, "indexed Git blob"):
            observer_guard.load_verified_policy(self.cabinet, policy)

    def test_tracked_symlink_is_not_an_approval_file(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks unavailable")
        self.initialize_cabinet_git()
        target = self.cabinet / "target.json"
        target.write_text("{}\n", encoding="utf-8")
        policy = Path("policy/repository-observation.json")
        path = self.cabinet / policy
        path.unlink(missing_ok=True)
        path.symlink_to(target)
        run("git", "-C", str(self.cabinet), "add", policy.as_posix())
        with self.assertRaisesRegex(observer_guard.ObserverGuardError, "regular Git blob"):
            observer_guard.require_index_identical(
                self.cabinet, policy, "versioned observation policy"
            )

    def test_remote_parent_segment_fails_closed(self) -> None:
        with self.assertRaisesRegex(observer_guard.ObserverGuardError, "unsafe remote path"):
            observer_guard.require_strict_remote(
                "github.com:../repo.git", "expected remote"
            )

    def test_git_environment_isolated_from_ambient_routing(self) -> None:
        ambient = {
            "GIT_DIR": "/tmp/other.git",
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.fsmonitor",
            "GIT_CONFIG_VALUE_0": "dangerous-command",
        }
        with mock.patch.dict(os.environ, ambient, clear=True):
            observer_guard.install_safe_git_environment()
            self.assertNotIn("GIT_DIR", os.environ)
            self.assertEqual(os.environ["GIT_CONFIG_NOSYSTEM"], "1")
            self.assertEqual(os.environ["GIT_CONFIG_GLOBAL"], os.devnull)
            self.assertEqual(
                os.environ["GIT_CONFIG_COUNT"],
                str(len(observer_guard._SAFE_GIT_CONFIG)),
            )
            self.assertNotIn("dangerous-command", set(os.environ.values()))

    def test_output_must_be_outside_managed_trees(self) -> None:
        for output in (
            self.cabinet / "observation.json",
            self.sources / "alpha" / "observation.json",
        ):
            with self.subTest(output=output):
                with self.assertRaisesRegex(
                    observer_guard.ObserverGuardError, "must be outside"
                ):
                    observer_guard.require_external_output_path(
                        output, self.cabinet, self.sources
                    )
        observer_guard.require_external_output_path(
            self.root / "state/observation.json",
            self.cabinet,
            self.sources,
        )


if __name__ == "__main__":
    unittest.main()
