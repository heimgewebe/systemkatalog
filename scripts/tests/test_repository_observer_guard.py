from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
