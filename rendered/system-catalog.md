# Systemkatalog

> Automatisch erzeugte, app-unabhängige Leseansicht. Sie beschreibt stabile Rollen und verweist auf Primärquellen; sie enthält keinen Live-, Task- oder Merge-Status.

## Zweck

Der Katalog beantwortet, welche Systeme existieren, welchem Zweck sie dienen, wem welche Wahrheit gehört, welche stabilen Beziehungen bestehen und wo die Einstiegspunkte liegen.

## Systeme

| System | Typ | Zweck |
|---|---|---|
| Ecosystem Map v0 | artifact | machine-readable overview graph and rendered orientation map |
| RepoBrief | concept | public name for context-view layer |
| Alexander | human | meaning, approval and abort authority outside automation |
| Bureau | repository | task cadence, delegation, run reporting |
| Chronik | repository | append-only event ledger and historical evidence axis |
| Device Graph | repository | infrastructure device graph; adjacent but not ecosystem-governance canon |
| Grabowski | repository | operator execution, repo work, review gates |
| heimlern | repository | offline operator-learning and proposal generation |
| Infra | repository | host, network, cockpit and operational runbooks |
| Leitstand | repository | read-only ecosystem observability and status projection |
| Lenskit / RepoBrief implementation | repository | context view and citable repository briefs |
| Plexer | repository | bounded event delivery and queueing gateway |
| Schauwerk | repository | visual surface and projection layer |
| Steuerboard | repository | read-only repo-state signal |
| Systemkatalog | repository | app-independent catalog for system purposes, truth ownership, stable relations and entrypoints |
| Vibe-Lab | repository | method lab and evidence experiments |
| Weltgewebe | repository | product and domain core |
| CI / Checks | service | automated tests, lint, gates and review signals |
| GitHub | service | repository, PR, issue and review state |

## Wahrheitszuständigkeiten

| Bereich | Primärquelle | Nicht-autoritative Projektionen |
|---|---|---|
| `append_only_history` | `chronik` | leitstand |
| `bounded_experiments` | `vibe_lab` | systemkatalog |
| `branches_prs_reviews` | `github` | bureau, leitstand |
| `ecosystem_semantics` | `systemkatalog` | leitstand, schauwerk |
| `general_operator_display` | `leitstand` | — |
| `live_service_state` | `runtime` | leitstand |
| `local_fleet_execution` | `grabowski` | leitstand |
| `offline_learning_proposals` | `heimlern` | systemkatalog |
| `repository_context_citations` | `repobrief_lenskit` | rlens, systemkatalog |
| `repository_observation_readiness` | `steuerboard` | grabowski, leitstand |
| `shared_fleet_ci_checks` | `wgx` | github_ci |
| `specialized_visual_rendering` | `schauwerk` | — |
| `tasks_claims_completion` | `bureau` | leitstand |
| `technical_check_results` | `ci` | github, leitstand |

## Stabile Beziehungen

Nur Beziehungen der Klassen `stable`, `bounded` oder `related` werden angezeigt. Die Klasse beschreibt die Dauerhaftigkeit der Architekturbeziehung, nicht ihren aktuellen Betriebszustand.

| Von | Beziehung | Zu | Klasse | Bedeutung |
|---|---|---|---|---|
| Alexander | `steers` | Systemkatalog | `stable` | Human sense, priority, approval and abort authority stay outside automation. |
| RepoBrief | `provides` | Systemkatalog | `stable` | RepoBrief gives Systemkatalog citable repository context. |
| Bureau | `delegates_to` | Grabowski | `stable` | Bureau can hand scoped work to the operator layer. |
| Bureau | `provides` | Leitstand | `stable` | Bureau may provide read-only task status artifacts. |
| Chronik | `displayed_by` | Leitstand | `stable` | Leitstand may display Chronik state without treating the display as authority. |
| Chronik | `evidence_for` | Bureau | `bounded` | Chronik event presence can support evidence references; Bureau still owns task and verification truth. |
| Chronik | `learning_input_for` | heimlern | `stable` | Heimlern may consume historical outcomes offline; no policy is auto-applied. |
| Chronik | `provides` | Leitstand | `stable` | Chronik provides event trace artifacts for timelines. |
| Chronik | `provides` | Systemkatalog | `stable` | Chronik provides event trace and historical continuity. |
| Device Graph | `scope_boundary` | Ecosystem Map v0 | `related` | Device Graph may describe infrastructure devices; it is not the ecosystem-governance map canon. |
| Grabowski | `emits_to` | Chronik | `bounded` | Grabowski may write task-local agent-run events through an explicit Chronik outbox path. |
| Grabowski | `operates_on` | GitHub | `stable` | PRs, branches, issues and reviews remain GitHub-owned state. |
| Leitstand | `observes` | Ecosystem Map v0 | `stable` | Leitstand observes the map as orientation, not truth. |
| Lenskit / RepoBrief implementation | `implements` | RepoBrief | `stable` | RepoBrief is the public context-view name; Lenskit remains an implementation namespace for now. |
| Plexer | `delivers_to` | Chronik | `stable` | Plexer delivers bounded operational events to Chronik agent.ledger when configured. |
| Schauwerk | `renders` | Ecosystem Map v0 | `stable` | Schauwerk may render map views without owning the map canon. |
| Steuerboard | `observes` | Systemkatalog | `stable` | Steuerboard can provide read-only repo-state signals, not decisions. |
| Systemkatalog | `owns` | Ecosystem Map v0 | `stable` | Systemkatalog owns the map semantics during v0. |
| Systemkatalog | `provides` | Leitstand | `stable` | Systemkatalog provides map artifacts for Leitstand display. |
| Vibe-Lab | `provides` | Systemkatalog | `stable` | Vibe-Lab provides method experiments and evidence patterns. |
| Weltgewebe | `operates_on` | GitHub | `stable` | Weltgewebe product work is still validated through repo, PR and CI state. |
| CI / Checks | `provides` | Leitstand | `stable` | Primary check state can be reflected. |
| GitHub | `provides` | Leitstand | `stable` | Primary repo state can be reflected. |
| GitHub | `validated_by` | CI / Checks | `stable` | Checks and review gates provide hard technical feedback. |

## Einstiegspunkte

| System | Einstieg |
|---|---|
| Bureau | [https://github.com/heimgewebe/bureau](https://github.com/heimgewebe/bureau) |
| GitHub | [https://github.com/heimgewebe](https://github.com/heimgewebe) |
| Grabowski | [https://github.com/heimgewebe/grabowski](https://github.com/heimgewebe/grabowski) |
| Leitstand | [https://github.com/heimgewebe/leitstand](https://github.com/heimgewebe/leitstand) |
| RepoBrief / Lenskit | [https://github.com/heimgewebe/lenskit](https://github.com/heimgewebe/lenskit) |
| Systemkatalog | [README.md](../README.md) |

## Grenzen

- Aufgaben, Queue und Receipts: Bureau.
- Repository-, PR- und Reviewzustand: GitHub.
- Technische Prüfergebnisse: CI und Review-Gates.
- Laufende Dienste: Runtime, Healthchecks, systemd und Logs.
- Lokale und repositorybezogene Ausführung: Grabowski nach Freigabe.
- Konkrete Runtime-Identitäten, Provider-Agenten und Topologie sind keine Katalogsysteme.
- Die frühere Cabinet-Oberfläche ist archiviert; die lokale read-only Oberfläche wird vom Systemkatalogdienst bereitgestellt.
- Frühere dynamische Claims und Radarflächen sind historische Kompatibilität, keine aktuelle Katalogwahrheit.
