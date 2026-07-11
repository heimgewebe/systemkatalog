# Weltgewebe — Repository Reference

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
| Reviewkarten-SHA-256 | `3fdb2f6952a3147cf46f4b6185ce9955ca038e8a4277a350159fdc17c6b26309` |

## Geprüfter Review-Snapshot

| Feld | Wert |
|---|---|
| Repository | `weltgewebe` |
| Pfad | `/home/alex/repos/weltgewebe` |
| Origin | `github.com:heimgewebe/weltgewebe.git` |
| Branch | `feat/weltweberei-information-surface` |
| HEAD | `bac3c4f7879f9e86b098b081b72bf6c133b44462` |
| Working Tree | `clean:0` |

## Live-Snapshot beim Import

| Feld | Wert |
|---|---|
| Erfasst | `2026-06-23T18:38:45.731368+00:00` |
| Pfad | `/home/alex/repos/weltgewebe` |
| Origin | `github.com:heimgewebe/weltgewebe.git` |
| Branch | `feat/weltweberei-information-surface` |
| HEAD | `bac3c4f7879f9e86b098b081b72bf6c133b44462` |
| Working Tree | `clean:0` |
| Status-SHA-256 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| Upstream | `origin/feat/weltweberei-information-surface` |
| Upstream-HEAD | `bac3c4f7879f9e86b098b081b72bf6c133b44462` |
| Beziehung zum Review | **identisch** |

## Identität

| Feld | Wert |
|---|---|
| Kanonischer Pfad | `/home/alex/repos/weltgewebe` |
| Remote | `github.com:heimgewebe/weltgewebe.git` |
| Default-Branch | `main` |
| Aktueller Branch | `feat/weltweberei-information-surface` |
| HEAD | `bac3c4f7879f9e86b098b081b72bf6c133b44462` |
| Live-Status | `clean:0` |
| Quellenbasis | `Git HEAD` |

## Kanonische Systemrolle

> - Weltgewebe ist ein **eigenständiges Projekt**. Repositories wie `heimgewebe/contracts`, `wgx` oder `hauski` sind optionale Quellen und Werkzeuge, keine monolithische Codebasis.

Beleg:
- Quelle: `README.md:L10`
- Git-Blob: `c0b02fac89d55bd125e37d91ab1ce883be97c010`
- SHA-256: `98414bc71448cb8a6495049c7f679e138783f6b8bfb3a02d0cbea76c3e5dfb63`
- Belegtyp: `explicit-repository-sentence`
- Stärke: `120`
- Status: `—`
- Kanonizität: `—`

## Belegter Zweck

> Agent configuration, operational boundaries, and strict coding guidelines for Weltgewebe. This document defines how agents navigate the repository, canonical files, and the rules for CI-ready code contributions.

Beleg:
- Quelle: `AGENTS.md:L28`
- Git-Blob: `15a48c15379a1096e67a03b632364d256cfc694e`
- SHA-256: `9d316154046d3ffae94e9020280ec6a23708b9738ba0d52c3aa4f0223affa740`
- Belegtyp: `explicit-purpose-section`
- Stärke: `130`
- Status: `active`
- Kanonizität: `canonical`

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
