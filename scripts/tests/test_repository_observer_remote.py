from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import observer_origin  # noqa: E402
import repository_observer as observer  # noqa: E402
from repository_observer_fixture import ObserverFixture, run  # noqa: E402


class RepositoryObserverRemoteTests(ObserverFixture, unittest.TestCase):
    def policy_entry(self) -> observer.PolicyEntry:
        item = self.entry("alpha")
        return observer.PolicyEntry(
            item["id"],
            item["directory"],
            item["expected_remote"],
            item["reference"],
        )

    def test_expected_stored_remote_passes(self) -> None:
        self.make_repository("alpha")
        observer_origin.require_expected_origin(self.sources, self.policy_entry())

    def test_url_rewrite_cannot_hide_stored_remote(self) -> None:
        repository = self.make_repository("alpha", remote="alias:alpha")
        run(
            "git",
            "-C",
            str(repository),
            "config",
            "url.github.com:heimgewebe/alpha.git.insteadOf",
            "alias:",
        )
        with self.assertRaisesRegex(observer.CollectorError, "unsupported repository remote"):
            observer_origin.require_expected_origin(self.sources, self.policy_entry())


if __name__ == "__main__":
    unittest.main()
