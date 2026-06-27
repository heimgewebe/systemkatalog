# Heimgewebe

<!-- cabinet-project-card-v1
{
  "schema": "cabinet.project-card.v1",
  "id": "heimgewebe",
  "title": "Heimgewebe",
  "evidence_status": "partial",
  "reviewed_at": "2026-06-27",
  "repositories": [
    {
      "name": "metarepo",
      "role": "Fleet, interne Contracts und gemeinsam mit WGX Fleet- und CI-Motorik",
      "evidence": "heimgewebe/Sources of Truth.md"
    },
    {
      "name": "contracts-mirror",
      "role": "Externe API-Contracts",
      "evidence": "heimgewebe/Sources of Truth.md"
    },
    {
      "name": "wgx",
      "role": "Gemeinsam mit Metarepo Fleet- und CI-Motorik",
      "evidence": "heimgewebe/Sources of Truth.md"
    },
    {
      "name": "cabinet",
      "role": "Kontext, Entscheidungen und Übergaben",
      "evidence": "heimgewebe/Sources of Truth.md"
    }
  ],
  "sources": [
    "heimgewebe/Start Here.md",
    "heimgewebe/Sources of Truth.md"
  ]
}
-->

## Ziel

Heimgewebe als zusammenhängenden Organismus beschreiben und die Verantwortung zwischen Fleet, Contracts, Implementierung, CI-Motorik und Cabinet nachvollziehbar halten.

## Repositorybeziehungen

| Repository | Belegte Rolle | Evidenzgrenze |
|---|---|---|
| `metarepo` | Fleet, interne Contracts sowie gemeinsam mit `wgx` Fleet- und CI-Motorik | Aus der versionierten Legacy-Quelle übernommen; keine aktuelle Repository Reference in Cabinet. |
| `contracts-mirror` | Externe API-Contracts | Aus der versionierten Legacy-Quelle übernommen; keine aktuelle Repository Reference in Cabinet. |
| `wgx` | Gemeinsam mit `metarepo` Fleet- und CI-Motorik | Aus der versionierten Legacy-Quelle übernommen; keine aktuelle Repository Reference in Cabinet. |
| `cabinet` | Kontext, Entscheidungen und Übergaben | Belegte Systemrolle in der Legacy-Quelle; kein aktueller Laufzeit- oder Git-Zustand. |

Die Quelle nennt zusätzlich „jeweiliges Owner-Repository“ für die Implementierung. Diese offene Repositoryklasse wird nicht als konkrete Beziehung ausgegeben, solange keine explizite Liste vorliegt.

## Belegter Stand

Die Rollenverteilung ist in `heimgewebe/Sources of Truth.md` ausdrücklich dokumentiert. `heimgewebe/Start Here.md` beschreibt den Heimgewebe-Organismus und trennt Implementierungsaufträge, Experimente und Laufzeiteingriffe organisatorisch. Die Karte bestätigt nur diese versionierten Aussagen; sie bestätigt keine Aktualität der beteiligten Repositories.

## Blocker und Risiken

- Für `metarepo`, `contracts-mirror` und `wgx` fehlen importierte Repository References mit Commit- und Frischebezug.
- Die Menge der „jeweiligen Owner-Repositories“ ist nicht explizit aufgelöst.
- Es gibt noch keinen freigegebenen Sammler für aktuelle Git-, CI- oder Runtime-Zustände.
- Änderungen der Legacy-Quellen können die Karte veralten lassen, ohne dass sich ein Quell-Repository ändert.

## Nächste Aktion

Repository References für `metarepo`, `contracts-mirror` und `wgx` importieren und die Owner-Repositories explizit registrieren. Erst danach kann die Karte von `partial` auf `bounded` angehoben werden.

## Quellen

- [`heimgewebe/Start Here.md`](../../heimgewebe/Start%20Here.md)
- [`heimgewebe/Sources of Truth.md`](../../heimgewebe/Sources%20of%20Truth.md)
