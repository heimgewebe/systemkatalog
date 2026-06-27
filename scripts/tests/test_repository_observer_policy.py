from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import repository_observer as observer  # noqa: E402
from repository_observer_fixture import ObserverFixture  # noqa: E402


class RepositoryObserverPolicyTests(ObserverFixture, unittest.TestCase):
    def test_policy_sorts_approved_repositories(self) -> None:
        policy = self.write_policy([self.entry("zeta"), self.entry("alpha")])
        loaded = observer.load_policy(self.cabinet, policy)
        self.assertEqual([entry.id for entry in loaded.entries], ["alpha", "zeta"])
        self.assertEqual(
            loaded.sha256,
            hashlib.sha256((self.cabinet / policy).read_bytes()).hexdigest(),
        )

    def test_reference_identity_drift_fails_closed(self) -> None:
        entry = self.entry("alpha")
        reference = self.cabinet / entry["reference"]
        reference.write_text(
            reference.read_text(encoding="utf-8").replace("`alpha`", "`beta`"),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(observer.CollectorError, "does not confirm"):
            observer.load_policy(self.cabinet, self.write_policy([entry]))

    def test_duplicate_repository_id_fails_closed(self) -> None:
        first = self.entry("alpha")
        second = dict(first)
        second["directory"] = "alpha-copy"
        second["reference"] = self.make_reference(
            "alpha-copy", first["expected_remote"]
        )
        with self.assertRaisesRegex(observer.CollectorError, "duplicate repository id"):
            observer.load_policy(self.cabinet, self.write_policy([first, second]))


if __name__ == "__main__":
    unittest.main()
