import unittest


def load_tests(loader, tests, pattern):
    for name in (
        "test_snapshot_review_model_hardening",
        "test_snapshot_review_io_hardening",
        "test_snapshot_review_write_rollback",
    ):
        tests.addTests(loader.loadTestsFromName(name))
    return tests
