# Lenskit — Repository Reference

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
| Import-Snapshot erfasst | `2026-06-23T18:38:45.731368+00:00` |
| Reviewkarten-SHA-256 | `69044379fdbc23bba97c37b4dfeca1d092d3fb238b48470a0e1601911744f030` |

## Geprüfter Review-Snapshot

| Feld | Wert |
|---|---|
| Repository | `lenskit` |
| Pfad | `/home/alex/repos/lenskit` |
| Origin | `github.com:heimgewebe/lenskit.git` |
| Branch | `docs/proof-correct-commands` |
| HEAD | `c692cfc7c51cdb898e95e7df9ebc762190c0767e` |
| Working Tree | `dirty:6` |

## Live-Snapshot beim Import

| Feld | Wert |
|---|---|
| Erfasst | `2026-06-23T18:38:45.731368+00:00` |
| Pfad | `/home/alex/repos/lenskit` |
| Origin | `github.com:heimgewebe/lenskit.git` |
| Branch | `docs/proof-correct-commands` |
| HEAD | `c692cfc7c51cdb898e95e7df9ebc762190c0767e` |
| Working Tree | `dirty:6` |
| Status-SHA-256 | `304e56e90c89df43647caf821f3c97c1defbe9efd67bbc3ec77f514b5b422800` |
| Upstream | `<fehlt>` |
| Upstream-HEAD | `<fehlt>` |
| Beziehung zum Review | **identisch** |

## Identität

| Feld | Wert |
|---|---|
| Kanonischer Pfad | `/home/alex/repos/lenskit` |
| Remote | `github.com:heimgewebe/lenskit.git` |
| Default-Branch | `main` |
| Aktueller Branch | `docs/proof-correct-commands` |
| HEAD | `c692cfc7c51cdb898e95e7df9ebc762190c0767e` |
| Live-Status | `dirty:6` |
| Quellenbasis | `Git HEAD` |

## Kanonische Systemrolle

> `merger.lenskit.frontends.pythonista.repolens` ist der direkte repoLens Dump-/Bundle-Emitter für lokale Modulaufrufe, insbesondere aus Pythonista/iPad-Kontexten.

Beleg:
- Quelle: `README.md:L21`
- Git-Blob: `79b52bcfa0ebdebffdb0d73d7103b18c58662cdb`
- SHA-256: `8e15c2e5af59b2d9f3e954073db12db694f432f4afe997fca2e37f856ba697d1`
- Belegtyp: `explicit-repository-sentence`
- Stärke: `120`
- Status: `—`
- Kanonizität: `—`

## Belegter Zweck

> python3 -m merger.lenskit.frontends.pythonista.repolens . --level overview

Beleg:
- Quelle: `README.md:L26`
- Git-Blob: `79b52bcfa0ebdebffdb0d73d7103b18c58662cdb`
- SHA-256: `8e15c2e5af59b2d9f3e954073db12db694f432f4afe997fca2e37f856ba697d1`
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
