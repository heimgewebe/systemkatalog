from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("legacy_bridge_probe", ROOT / "scripts/prepare_legacy_bridge_probe.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PrepareLegacyBridgeProbeTests(unittest.TestCase):
    def test_prepares_bit_exact_isolated_legacy_claim_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_inputs(Path(temporary))
            result = MODULE.prepare(root, Path("sandbox"))
            archive = root / MODULE.ARCHIVE_CLAIMS_REL
            copied = root / "sandbox" / MODULE.LEGACY_PROBE_CLAIMS_REL
            policy = json.loads((root / "sandbox" / MODULE.LEGACY_PROBE_POLICY_REL).read_text(encoding="utf-8"))
            self.assertEqual(copied.read_bytes(), archive.read_bytes())
            self.assertIn(str(MODULE.LEGACY_PROBE_CLAIMS_REL), policy["allowed_sources"])
            self.assertNotIn(str(MODULE.ARCHIVE_CLAIMS_REL), policy["allowed_sources"])
            self.assertFalse(policy["probe_adapter"]["catalog_authoritative"])
            self.assertFalse(policy["probe_adapter"]["persistent"])
            self.assertTrue(result["catalogClaimsUnchanged"])

    def test_rejects_maintained_policy_exposing_stable_claims(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_inputs(Path(temporary))
            path = root / MODULE.BRIDGE_POLICY_REL
            policy = json.loads(path.read_text(encoding="utf-8"))
            policy["allowed_sources"].append(str(MODULE.LEGACY_PROBE_CLAIMS_REL))
            path.write_text(json.dumps(policy), encoding="utf-8")
            with self.assertRaisesRegex(MODULE.LegacyBridgeProbeError, "stable claims"):
                MODULE.prepare(root, Path("sandbox"))

    def test_rejects_archive_hash_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_inputs(Path(temporary))
            (root / MODULE.ARCHIVE_CLAIMS_REL).write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.LegacyBridgeProbeError, "hash binding"):
                MODULE.prepare(root, Path("sandbox"))

    def test_rejects_nonempty_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = self._copy_inputs(Path(temporary))
            output = root / "sandbox"
            output.mkdir()
            (output / "foreign.txt").write_text("foreign", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.LegacyBridgeProbeError, "not empty"):
                MODULE.prepare(root, Path("sandbox"))

    def _copy_inputs(self, root: Path) -> Path:
        for relative in (MODULE.BRIDGE_POLICY_REL, MODULE.SYSTEM_POLICY_REL, MODULE.ARCHIVE_CLAIMS_REL):
            source = ROOT / relative
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        return root


if __name__ == "__main__":
    unittest.main()
