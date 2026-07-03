# Infra — Repository Reference

> **Semantik:** Diese Seite verbindet einen geprüften Review-Snapshot
> mit einem separat zum Importzeitpunkt erfassten Live-Snapshot.
> **Git bleibt die Source of Truth.**
> Die Seite ist keine laufend aktualisierte Statusanzeige.

## Provenienz

| Feld | Wert |
|---|---|
| Registry-ID | `repo-registry-20260623-192948` |
| Registry-Hash | `308b5a60a9ef291081549ea66bd51413f66cb433e1d3696c445eab5e915fad7a` |
| Source-ID | `cabinet-source-cards-20260623-192948` |
| Review-ID | `cabinet-source-cards-reviewed-20260623-192948` |
| Review-Hash | `52f380ddecdf37df22de9db78a3a1c1f38e64583352c8d2a3b9819c7959bd811` |
| Review erzeugt | `2026-06-23T17:29:51.347286+00:00` |
| Import-Snapshot erfasst | `2026-07-03T20:24:19Z` |
| Reviewkarten-SHA-256 | `0d2c99280a0772bc19e37f107fdd0be6dede2929964458a1d2c19ded99f75aea` |

## Geprüfter Review-Snapshot

| Feld | Wert |
|---|---|
| Repository | `infra` |
| Pfad | `/home/alex/repos/infra` |
| Origin | `github.com:heimgewebe/infra.git` |
| Branch | `feat/ssh-cockpit-shell-handover` |
| HEAD | `5d9b7f840fcd59742b75ce19ba2f90fa396ddee8` |
| Working Tree | `clean:0` |

## Live-Snapshot beim Import

| Feld | Wert |
|---|---|
| Erfasst | `2026-07-03T20:24:19Z` |
| Pfad | `/home/alex/repos/infra` |
| Origin | `github.com:heimgewebe/infra.git` |
| Branch | `main` |
| HEAD | `627923f09b2b3b5e0d25aa8a61af8a2b79cdd711` |
| Working Tree | `clean:0` |
| Status-SHA-256 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| Upstream | `origin/main` |
| Upstream-HEAD | `627923f09b2b3b5e0d25aa8a61af8a2b79cdd711` |
| Beziehung zum Review | **Live-Stand enthält Review-Stand** |

## Identität

| Feld | Wert |
|---|---|
| Kanonischer Pfad | `/home/alex/repos/infra` |
| Remote | `github.com:heimgewebe/infra.git` |
| Default-Branch | `main` |
| Aktueller Branch | `main` |
| HEAD | `627923f09b2b3b5e0d25aa8a61af8a2b79cdd711` |
| Live-Status | `clean:0` |
| Quellenbasis | `Git HEAD` |

## Kanonische Systemrolle

> Access Layer

Beleg:
- Quelle: `docs/infra/blueprint.md:L68`
- Git-Blob: `80e284e080cbfb36026d81eec1387bfe54fbbc3e`
- SHA-256: `90186432b33c3c9baaafebafcb982f4cdb9bdfd0a804c7990942a7cd3f74c1e7`
- Belegtyp: `explicit-role-table`
- Stärke: `125`
- Status: `active`
- Kanonizität: `canonical`

## Belegter Zweck

> Nur drei Ziele sind erlaubt: Recovery verbessern Drift verhindern falsche Runtime-Aussagen unmöglich machen

Beleg:
- Quelle: `README.md:L8-L11`
- Git-Blob: `c02b763f89ad7a3ecebb125d4852c557d9a58a7e`
- SHA-256: `0514f6415a323fd9c0d8f9567a44266adad343daf3b5199d0ffb3090843826e6`
- Belegtyp: `explicit-purpose-section`
- Stärke: `130`
- Status: `—`
- Kanonizität: `—`

## Abgrenzung

- Diese Karte beschreibt die belegte Repository-Rolle.
- Sie behauptet keinen aktuellen Runtime-Zustand.
- Worktrees sind operative Ableitungen und keine eigenständigen Projekte.
- Uncommittete Inhalte werden nicht als kanonischer Rollenbeleg verwendet.
- Branch- und HEAD-Zustände bleiben explizit sichtbar.

## Import-Gate

**READY:** Rolle und Zweck besitzen hinreichende, commit-verankerte Belege.

## Pflegevertrag

- Git und die jeweiligen Repository-Dokumente bleiben kanonisch.
- Der Review-Snapshot wird nicht nachträglich als Live-Zustand umgedeutet.
- Der Import-Snapshot ist ebenfalls nur auf seinen Erfassungszeitpunkt bezogen.
- Eine spätere Aktualisierung erfolgt als neuer, datierter Snapshot.
- Repository-, Runtime- oder Contract-Aussagen benötigen weiterhin eigene Belege.

## Refresh-Beleg 2026-07-03

Der Import-Snapshot wurde aus dem Live-Befund `pruefung/30 Befunde/access-refresh-readiness-2026-07-03.md` aktualisiert. Der geprüfte Review-Snapshot bleibt historisch.

Grenze: Diese Aktualisierung behauptet keine Runtime-Prüfung und erzeugt keinen Bureau-Task.
