# Bureau Reference Refresh Proposal 2026-07-03

## Status

Vorschlag, nicht angewendet.

Dieser Vorschlag ändert keine Repository Reference.

## Zweck

Aus dem Bureau-Refresh-Plan wird ein prüfbarer Vorher/Nachher-Entwurf abgeleitet.

## Eingaben

- Plan: `steuerung/20 Aufgaben/bureau-reference-refresh-plan-2026-07-03.md`
- Befund: `pruefung/30 Befunde/bureau-candidate-live-refresh-2026-07-03.md`
- Betroffene Reference: `steuerung/40 Organe/Bureau/Repository Reference.md`


## Vorher

Gespeicherter Stand.

```text
review_time: 2026-07-02T12:54:24Z
import_time: 2026-07-02T12:54:24Z
branch: feat/codex-bridge-readonly-v1
head: cf0fef56e194dcbe0c5e9c9674a814beed157a7a
stored_status: one local change recorded
upstream: missing
relation: identical
```

## Nachher-Entwurf

Geprüfter Live-Hinweis aus dem Befund.

```text
local_branch: feat/codex-bridge-readonly-v1
local_head: cf0fef56e194dcbe0c5e9c9674a814beed157a7a
origin_main: ffdd791434d0
local_delta: none
remote_branch: absent
prs_for_branch: none returned
```

## Vorgeschlagene Interpretation

- Der alte Status bleibt als historischer Importbefund erhalten.
- Der neue Live-Hinweis sagt nur: der alte lokale Delta-Zustand wurde nicht reproduziert.
- Eine spätere Aktualisierung darf diese zwei Ebenen nicht vermischen.

## Nicht anwenden

- Diese Datei ändert die Bureau Reference nicht.
- Diese Datei erzeugt keinen Bureau-Auftrag.
- Diese Datei behauptet keine Bureau-Runtime-Prüfung.

## Review-Kriterien

- Quelle ist genannt.
- Live-Hinweis ist genannt.
- Betroffene Karte ist genannt.
- Grenze ist genannt.
- Vorher und Nachher bleiben getrennt.

## Stop-Kriterium

Stop bei uneindeutiger Lesart.

## Target-Proof

Der Vorschlag gilt als prüfbar, wenn Quelle, Live-Hinweis, Grenze, Stop-Kriterium und betroffene Karte im Dokument sichtbar sind.
