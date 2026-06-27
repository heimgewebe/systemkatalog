from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import repository_observer as observer  # noqa: E402
from repository_observer_fixture import ObserverFixture, run  # noqa: E402


class RepositoryObserverCollectionTests(ObserverFixture, unittest.TestCase):
    def test_collection_is_deterministic_and_allowlisted(self) -> None:
        policy = self.write_policy([self.entry("alpha")])
        self.make_repository("alpha")
        self.make_repository("unapproved")
        first = observer.render_collection(
            observer.collect(
                self.cabinet,
                policy,
                self.sources,
                "2026-06-28T00:00:00+02:00",
            )
        )
        second = observer.render_collection(
            observer.collect(
                self.cabinet, policy, self.sources, "2026-06-27T22:00:00Z"
            )
        )
        self.assertEqual(first, second)
        parsed = json.loads(first)
        self.assertEqual(parsed["observed_at"], "2026-06-27T22:00:00Z")
        self.assertEqual([item["id"] for item in parsed["repositories"]], ["alpha"])
        self.assertNotIn(str(self.sources), first.decode("utf-8"))

    def test_dirty_and_detached_state_are_explicit(self) -> None:
        policy = self.write_policy([self.entry("alpha")])
        self.make_repository("alpha", dirty=True, detached=True)
        value = observer.collect(
            self.cabinet, policy, self.sources, "2026-06-27T22:00:00Z"
        )["repositories"][0]
        self.assertIsNone(value["branch"])
        self.assertEqual(value["head_state"], "detached")
        self.assertEqual(value["worktree"]["state"], "dirty")
        self.assertEqual(value["worktree"]["change_count"], 1)

    def test_origin_mismatch_fails_closed(self) -> None:
        policy = self.write_policy([self.entry("alpha")])
        self.make_repository("alpha", remote="git@github.com:other/alpha.git")
        with self.assertRaisesRegex(observer.CollectorError, "origin mismatch"):
            observer.collect(
                self.cabinet, policy, self.sources, "2026-06-27T22:00:00Z"
            )

    def test_missing_repository_fails_closed(self) -> None:
        policy = self.write_policy([self.entry("alpha")])
        with self.assertRaisesRegex(observer.CollectorError, "is missing"):
            observer.collect(
                self.cabinet, policy, self.sources, "2026-06-27T22:00:00Z"
            )

    def test_symlink_repository_fails_closed(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks unavailable")
        policy = self.write_policy([self.entry("alpha")])
        target = self.root / "outside"
        run("git", "init", "-q", "-b", "main", str(target))
        (self.sources / "alpha").symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(observer.CollectorError, "symlinks"):
            observer.collect(
                self.cabinet, policy, self.sources, "2026-06-27T22:00:00Z"
            )


if __name__ == "__main__":
    unittest.main()
