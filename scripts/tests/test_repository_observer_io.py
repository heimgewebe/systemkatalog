from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import repository_observer as observer  # noqa: E402
from repository_observer_fixture import ObserverFixture  # noqa: E402


class RepositoryObserverIoTests(ObserverFixture, unittest.TestCase):
    def test_observed_at_requires_timezone(self) -> None:
        with self.assertRaisesRegex(observer.CollectorError, "timezone"):
            observer.normalize_observed_at("2026-06-27T22:00:00")

    def test_observed_at_requires_whole_seconds(self) -> None:
        with self.assertRaisesRegex(observer.CollectorError, "whole seconds"):
            observer.normalize_observed_at("2026-06-27T22:00:00.1Z")

    def test_atomic_output_uses_private_mode(self) -> None:
        output_dir = self.root / "output"
        output_dir.mkdir()
        output = output_dir / "collection.json"
        observer.write_atomic(output, b"{}\n")
        self.assertEqual(output.read_bytes(), b"{}\n")
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
