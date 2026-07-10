# Heimgewebe-Systemkatalog

> Automatisch erzeugte, app-unabhängige Leseansicht. Sie beschreibt stabile Rollen und verweist auf Primärquellen; sie enthält keinen Live-, Task- oder Merge-Status.

## Zweck

Der Katalog beantwortet, welche Systeme existieren, welchem Zweck sie dienen, wem welche Wahrheit gehört, welche stabilen Beziehungen bestehen und wo die Einstiegspunkte liegen.

## Systeme

| System | Typ | Zweck |
|---|---|---|
| Claude | agent | architecture, large refactors, deep concept review |
| Codex | agent | code review, logic bugs, invariant checks |
| Gemini | agent | proposed proposal-only review and scout capacity after capability and sandbox preflight; not verified or schedulable |
| Jules | agent | small clear patches |
| Local agents | agent | cheap prechecks and repetitive scans |
| Ecosystem Map v0 | artifact | machine-readable overview graph and rendered orientation map |
| RepoBrief | concept | public name for context-view layer |
| Alexander | human | sensemaking, priority, approval, abort authority |
| Bureau | repository | task cadence, delegation, run reporting |
| Cabinet | repository | sense, evidence, prioritization, learning, map ownership |
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
| Vibe-Lab | repository | method lab and evidence experiments |
| Weltgewebe | repository | product and domain core |
| heim-pc | runtime | local worktrees, operator cockpit and execution surface |
| heimserver | runtime | home server runtime surface |
| CI / Checks | service | automated tests, lint, gates and review signals |
| GitHub | service | repository, PR, issue and review state |

## Wahrheitszuständigkeiten

| Bereich | Primärquelle | Nicht-autoritative Projektionen |
|---|---|---|
| `append_only_history` | `chronik` | leitstand |
| `bounded_experiments` | `vibe_lab` | cabinet |
| `branches_prs_reviews` | `github` | bureau, cabinet, leitstand |
| `ecosystem_semantics` | `cabinet` | leitstand, schauwerk |
| `general_operator_display` | `leitstand` | — |
| `live_service_state` | `runtime` | leitstand, cabinet |
| `local_fleet_execution` | `grabowski` | leitstand |
| `offline_learning_proposals` | `heimlern` | cabinet |
| `repository_context_citations` | `repobrief_lenskit` | rlens, cabinet |
| `repository_observation_readiness` | `steuerboard` | grabowski, leitstand |
| `shared_fleet_ci_checks` | `wgx` | github_ci |
| `specialized_visual_rendering` | `schauwerk` | — |
| `tasks_claims_completion` | `bureau` | leitstand, cabinet |
| `technical_check_results` | `ci` | github, leitstand |

## Stabile Beziehungen

Nur Beziehungen mit einer stabilen Klasse (`active`, `bounded`, `related`) werden hier angezeigt. Geplante, vorgeschlagene oder rein beobachtete Laufzeitzustände bleiben außerhalb dieser Projektion.

| Von | Beziehung | Zu | Bedeutung |
|---|---|---|---|
| Alexander | `steers` | Cabinet | Human sense, priority, approval and abort authority stay outside automation. |
| Claude | `reports_to` | Grabowski | Agent output is a proposal until evidence and review pass. |
| Codex | `reports_to` | Grabowski | Agent output is a proposal until evidence and review pass. |
| Jules | `reports_to` | Grabowski | Agent output is a proposal until evidence and review pass. |
| Local agents | `reports_to` | Grabowski | Agent output is a proposal until evidence and review pass. |
| RepoBrief | `provides` | Cabinet | RepoBrief gives Cabinet citable repository context. |
| Bureau | `delegates_to` | Grabowski | Bureau can hand scoped work to the operator layer. |
| Cabinet | `provides` | Leitstand | Cabinet provides map artifacts for Leitstand display. |
| Chronik | `evidence_for` | Bureau | Chronik event presence can support evidence references; Bureau still owns task and verification truth. |
| Chronik | `provides` | Cabinet | Chronik provides event trace and historical continuity. |
| Chronik | `provides` | Leitstand | Chronik provides event trace artifacts for timelines. |
| Device Graph | `scope_boundary` | Ecosystem Map v0 | Device Graph may describe infrastructure devices; it is not the ecosystem-governance map canon. |
| Grabowski | `delegates_to` | Claude | Claude is suited for architecture and heavy conceptual review. |
| Grabowski | `delegates_to` | Codex | Codex is suited for review, logic bugs and invariants. |
| Grabowski | `delegates_to` | Jules | Jules is suited for small clear patches. |
| Grabowski | `delegates_to` | Local agents | Local agents are suited for cheap scans and repetitive checks. |
| Grabowski | `operates_on` | GitHub | PRs, branches, issues and reviews remain GitHub-owned state. |
| Infra | `provides` | heim-pc | Infra owns cockpit and host runbook concerns. |
| Infra | `provides` | heimserver | Infra owns server operation knowledge. |
| Leitstand | `observes` | Ecosystem Map v0 | Leitstand observes the map as orientation, not truth. |
| Lenskit / RepoBrief implementation | `implements` | RepoBrief | RepoBrief is the public context-view name; Lenskit remains an implementation namespace for now. |
| Plexer | `delivers_to` | Chronik | Plexer delivers bounded operational events to Chronik agent.ledger when configured. |
| Steuerboard | `observes` | Cabinet | Steuerboard can provide read-only repo-state signals, not decisions. |
| Vibe-Lab | `provides` | Cabinet | Vibe-Lab provides method experiments and evidence patterns. |
| Weltgewebe | `operates_on` | GitHub | Weltgewebe product work is still validated through repo, PR and CI state. |
| CI / Checks | `provides` | Leitstand | Primary check state can be reflected. |
| GitHub | `provides` | Leitstand | Primary repo state can be reflected. |
| GitHub | `validated_by` | CI / Checks | Checks and review gates provide hard technical feedback. |

## Einstiegspunkte

| System | Einstieg |
|---|---|
| Bureau | [https://github.com/heimgewebe/bureau](https://github.com/heimgewebe/bureau) |
| Cabinet / Systemkatalog | [README.md](README.md) |
| GitHub | [https://github.com/heimgewebe](https://github.com/heimgewebe) |
| Grabowski | [https://github.com/heimgewebe/grabowski](https://github.com/heimgewebe/grabowski) |
| Leitstand | [https://github.com/heimgewebe/leitstand](https://github.com/heimgewebe/leitstand) |
| RepoBrief / Lenskit | [https://github.com/heimgewebe/lenskit](https://github.com/heimgewebe/lenskit) |

## Grenzen

- Aufgaben, Queue und Receipts: Bureau.
- Repository-, PR- und Reviewzustand: GitHub.
- Technische Prüfergebnisse: CI und Review-Gates.
- Laufende Dienste: Runtime, Healthchecks, systemd und Logs.
- Lokale und repositorybezogene Ausführung: Grabowski nach Freigabe.
- Die externe Cabinet-App ist nur ein vorübergehender optionaler Viewer und für diese Datei nicht erforderlich.
