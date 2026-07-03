# Bureau Reference Refresh Plan 2026-07-03

## Status

Beispielplan zum `Reference Refresh Contract 2026-07-03`.

Dieser Plan ist keine Reference-Aktualisierung und keine Ausführung.

## Ziel

Den Bureau-Live-Befund in einen begrenzten Refresh-Plan überführen, ohne die betroffene Repository Reference zu ändern.

## Eingaben

- Contract: `steuerung/20 Aufgaben/reference-refresh-contract-2026-07-03.md`
- Befund: `pruefung/30 Befunde/bureau-candidate-live-refresh-2026-07-03.md`
- Betroffene Reference: `steuerung/40 Organe/Bureau/Repository Reference.md`

## Live-Beleg aus dem Befund

```text
local branch: feat/codex-bridge-readonly-v1
local HEAD: cf0fef56e194dcbe0c5e9c9674a814beed157a7a
origin/main: ffdd791434d0
unstaged diff: clean
staged diff: clean
untracked files: 0
remote branch origin/feat/codex-bridge-readonly-v1: absent
open/closed PRs for feat/codex-bridge-readonly-v1: none returned by gh pr list
```

## Refresh-Plan

1. Reference nicht direkt bearbeiten.
2. Zuerst einen datierten Refresh-Vorschlag erzeugen.
3. Vorschlag muss alte Snapshot-Felder und neue Live-Belege getrennt zeigen.
4. Vorschlag muss klar sagen, welche Aussage weiterhin historisch ist.
5. Erst nach Review darf eine spätere Aktualisierung geplant werden.

## Grenze

- Kein Bureau-Task.
- Kein Quellrepo-Fix.
- Kein Dispatch.
- Kein manuelles Überschreiben generierter Reports.
- Keine Behauptung, dass die aktuelle Bureau-Runtime geprüft wurde.

## Stop-Kriterium

Stop, wenn Live-Beleg, Quelle, betroffene Reference oder Grenze fehlen.

## Target-Proof

Der Plan nennt Quelle, Live-Beleg, Grenze, Stop-Kriterium und betroffene Reference.
