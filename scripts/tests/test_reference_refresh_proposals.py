from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "check-reference-refresh-proposals.py"


def load_guard_module():
    spec = importlib.util.spec_from_file_location("proposal_guard_under_test", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


def valid_proposal() -> str:
    return """# Bureau Reference Refresh Proposal 2026-07-03

## Status

Vorschlag, nicht angewendet.

Dieser Vorschlag ändert keine Repository Reference.

## Eingaben

- Plan: `steuerung/20 Aufgaben/bureau-reference-refresh-plan-2026-07-03.md`
- Befund: `pruefung/30 Befunde/bureau-candidate-live-refresh-2026-07-03.md`
- Betroffene Reference: `steuerung/40 Organe/Bureau/Repository Reference.md`

## Vorher

Gespeicherter Stand.

## Nachher-Entwurf

Geprüfter Live-Hinweis aus dem Befund.

## Nicht anwenden

- Diese Datei ändert die Bureau Reference nicht.

## Review-Kriterien

- Quelle ist genannt.
- Live-Hinweis ist genannt.
- Vorher und Nachher bleiben getrennt.

## Stop-Kriterium

Stop bei uneindeutiger Lesart.

## Target-Proof

Der Vorschlag gilt als prüfbar.
"""


class ReferenceRefreshProposalGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.proposal_dir = self.root / "steuerung/20 Aufgaben"
        self.proposal_dir.mkdir(parents=True)
        self.guard = load_guard_module()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_proposal(self, text: str) -> Path:
        path = self.proposal_dir / "bureau-reference-refresh-proposal-2026-07-03.md"
        path.write_text(text, encoding="utf-8")
        return path

    def messages(self, text: str) -> list[str]:
        path = self.write_proposal(text)
        return [finding.message for finding in self.guard.check_proposal(path, self.root)]

    def test_valid_proposal_passes(self) -> None:
        self.write_proposal(valid_proposal())
        self.assertEqual([], self.guard.run(self.root))

    def test_missing_required_section_fails(self) -> None:
        text = valid_proposal().replace("## Target-Proof", "## Nachweis")
        self.assertIn("missing section: ## Target-Proof", self.messages(text))

    def test_missing_evidence_path_fails(self) -> None:
        text = valid_proposal().replace("pruefung/30 Befunde/", "pruefung/30/", 1)
        self.assertIn("missing required text: pruefung/30 Befunde/", self.messages(text))

    def test_applied_state_text_fails(self) -> None:
        text = valid_proposal() + "\n## Angewendet\n\nReference wurde aktualisiert.\n"
        messages = self.messages(text)
        self.assertIn("forbidden applied-state text: ## Angewendet", messages)
        self.assertIn("forbidden applied-state text: Reference wurde aktualisiert", messages)

    def test_before_after_order_fails(self) -> None:
        text = valid_proposal()
        text = text.replace("## Vorher", "## TMP", 1)
        text = text.replace("## Nachher-Entwurf", "## Nachher-Entwurf\n\n## Vorher", 1)
        text = text.replace("## TMP", "", 1)
        self.assertIn("Nachher-Entwurf appears before Vorher", self.messages(text))


if __name__ == "__main__":
    unittest.main()
