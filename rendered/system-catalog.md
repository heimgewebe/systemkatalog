# Systemkatalog

> Automatisch erzeugte, app-unabhängige Leseansicht. Sie beschreibt stabile Rollen und verweist auf Primärquellen; sie enthält keinen Live-, Task- oder Merge-Status.

## Zweck

Der Katalog beantwortet, welche Systeme existieren, welchem Zweck sie dienen, wem welche Wahrheit gehört, welche stabilen Beziehungen bestehen und wo die Einstiegspunkte liegen.

## Systeme

| System | Typ | Zweck | Nicht zuständig für | Wahrheitsbesitz | Einstiegspunkte |
|---|---|---|---|---|---|
| Ecosystem Map v0 | artifact | machine-readable overview graph and rendered orientation map | claim truth<br>runtime health<br>merge readiness | — | `artifact`: [rendered/ecosystem-registry-map.mmd](../rendered/ecosystem-registry-map.mmd) |
| RepoBrief | concept | public name for context-view layer | repository mutation<br>runtime health<br>task dispatch | — | `implementation`: [https://github.com/heimgewebe/lenskit](https://github.com/heimgewebe/lenskit) |
| Alexander | human | meaning, approval and abort authority outside automation | automated execution<br>machine-derived repository or runtime state | — | `authorityPolicy`: [policy/system-catalog.v1.json](../policy/system-catalog.v1.json) |
| Agent Control Surface | repository | local manual control surface for Jules sessions and guarded step-by-step Git workflows | autonomous task dispatch<br>task priority<br>merge authorization<br>remote access security | — | `readme`: [https://github.com/heimgewebe/agent-control-surface/blob/main/README.md](https://github.com/heimgewebe/agent-control-surface/blob/main/README.md)<br>`repository`: [https://github.com/heimgewebe/agent-control-surface](https://github.com/heimgewebe/agent-control-surface)<br>`runbook`: [https://github.com/heimgewebe/agent-control-surface/blob/main/RUNBOOK.md](https://github.com/heimgewebe/agent-control-surface/blob/main/RUNBOOK.md) |
| Außensensor | repository | Curated external signals and event feeds for Chronik | task authority<br>canonical event history<br>merge approval | — | `repository`: [https://github.com/heimgewebe/aussensensor](https://github.com/heimgewebe/aussensensor) |
| Bureau | repository | task cadence, delegation, run reporting | runtime execution<br>Git and review truth<br>ecosystem semantics | tasks_claims_completion | `repository`: [https://github.com/heimgewebe/bureau](https://github.com/heimgewebe/bureau) |
| Chronik | repository | append-only event ledger and historical evidence axis | task state<br>policy decisions<br>runtime mutation | append_only_history | `repository`: [https://github.com/heimgewebe/chronik](https://github.com/heimgewebe/chronik) |
| Commonworld | repository | Interactive globe and commons-oriented world exploration | ecosystem governance<br>task state<br>merge authority | — | `repository`: [https://github.com/heimgewebe/commonworld](https://github.com/heimgewebe/commonworld) |
| Contracts Mirror | repository | Validated mirror and publication surface for canonical Metarepo contracts | canonical contract authorship<br>runtime status<br>task authority | — | `repository`: [https://github.com/heimgewebe/contracts-mirror](https://github.com/heimgewebe/contracts-mirror) |
| Device Graph | repository | infrastructure device graph; adjacent but not ecosystem-governance canon | ecosystem governance canon<br>task state<br>merge authority | — | `repository`: [https://github.com/heimgewebe/device-graph](https://github.com/heimgewebe/device-graph) |
| Grabowski | repository | operator execution, repo work, review gates | task priority<br>ecosystem semantics<br>primary Git or runtime truth | agent_routing<br>local_fleet_execution | `repository`: [https://github.com/heimgewebe/grabowski](https://github.com/heimgewebe/grabowski) |
| HausKI | repository | Local offline-first AI orchestration and policy-controlled memory | fleet task authority<br>ecosystem catalog semantics<br>merge approval | — | `repository`: [https://github.com/heimgewebe/hausKI](https://github.com/heimgewebe/hausKI) |
| HausKI Audio | repository | Local audio playback, recording and automation | ecosystem catalog semantics<br>task authority<br>merge approval | — | `repository`: [https://github.com/heimgewebe/hausKI-audio](https://github.com/heimgewebe/hausKI-audio) |
| heim-pc | repository | Versioned local operator entry and host orientation | fleet task authority<br>service runtime truth<br>ecosystem semantics | — | `repository`: [https://github.com/heimgewebe/heim-pc](https://github.com/heimgewebe/heim-pc) |
| Heimgeist | repository | System self-reflection and meta-agent experimentation | production authority<br>task state<br>merge approval | — | `repository`: [https://github.com/heimgewebe/heimgeist](https://github.com/heimgewebe/heimgeist) |
| heimlern | repository | retired reference for the former offline operator-learning implementation | active learning proposals<br>runtime operation<br>automatic policy application<br>task dispatch<br>merge authorization | — | `repository`: [https://github.com/heimgewebe/heimlern](https://github.com/heimgewebe/heimlern) |
| Heimserver | repository | private operations and contract repository for the home-network service layer, edge gateway, DDNS and Weltgewebe infrastructure | runtime health claims without live checks<br>task state<br>ecosystem semantics<br>secret storage in Git | — | `agentEntry`: [https://github.com/heimgewebe/heimserver/blob/main/AGENTS.md](https://github.com/heimgewebe/heimserver/blob/main/AGENTS.md)<br>`readme`: [https://github.com/heimgewebe/heimserver/blob/main/README.md](https://github.com/heimgewebe/heimserver/blob/main/README.md)<br>`repository`: [https://github.com/heimgewebe/heimserver](https://github.com/heimgewebe/heimserver)<br>`systemMap`: [https://github.com/heimgewebe/heimserver/blob/main/SYSTEM_MAP.md](https://github.com/heimgewebe/heimserver/blob/main/SYSTEM_MAP.md) |
| Infra | repository | host, network, cockpit and operational runbooks | task state<br>ecosystem semantics<br>product-domain truth | — | `repository`: [https://github.com/heimgewebe/infra](https://github.com/heimgewebe/infra) |
| Konvergenzregelkreis | repository | public stateless convergence protocol and conformance core for evidence-bound closure of ecosystem changes | task state<br>queue or claims<br>execution, leases or recovery<br>merge authorization<br>deployment state or runtime health<br>ecosystem semantics<br>fleet membership<br>event history<br>product telemetry | convergence_protocol | `agentEntry`: [https://github.com/heimgewebe/konvergenzregelkreis/blob/main/AGENTS.md](https://github.com/heimgewebe/konvergenzregelkreis/blob/main/AGENTS.md)<br>`profiles`: [https://github.com/heimgewebe/konvergenzregelkreis/tree/main/profiles](https://github.com/heimgewebe/konvergenzregelkreis/tree/main/profiles)<br>`protocol`: [https://github.com/heimgewebe/konvergenzregelkreis/tree/main/protocol](https://github.com/heimgewebe/konvergenzregelkreis/tree/main/protocol)<br>`readme`: [https://github.com/heimgewebe/konvergenzregelkreis/blob/main/README.md](https://github.com/heimgewebe/konvergenzregelkreis/blob/main/README.md)<br>`repository`: [https://github.com/heimgewebe/konvergenzregelkreis](https://github.com/heimgewebe/konvergenzregelkreis)<br>`roleBoundary`: [https://github.com/heimgewebe/konvergenzregelkreis/blob/main/system/regelkreis-role.v1.json](https://github.com/heimgewebe/konvergenzregelkreis/blob/main/system/regelkreis-role.v1.json) |
| Leitstand | repository | read-only ecosystem observability and status projection | canonical truth ownership<br>task authorization<br>runtime mutation | general_operator_display | `repository`: [https://github.com/heimgewebe/leitstand](https://github.com/heimgewebe/leitstand) |
| Leitwerk | repository | retained normative coordination-contract reference from the pre-Bureau and pre-Grabowski control model | current task or claim state<br>runtime execution<br>merge authorization<br>agent dispatch | — | `readme`: [https://github.com/heimgewebe/leitwerk/blob/main/README.md](https://github.com/heimgewebe/leitwerk/blob/main/README.md)<br>`repository`: [https://github.com/heimgewebe/leitwerk](https://github.com/heimgewebe/leitwerk)<br>`roleBoundary`: [https://github.com/heimgewebe/leitwerk/blob/main/docs/leitwerk.md](https://github.com/heimgewebe/leitwerk/blob/main/docs/leitwerk.md) |
| Lenskit / RepoBrief implementation | repository | context views, citable repository briefs and read-only agent context serving | repository operational state<br>task priority<br>merge authorization | repository_context_citations | `mcpServer`: [https://github.com/heimgewebe/lenskit/blob/main/docs/usage/repobrief-mcp-stdio.md](https://github.com/heimgewebe/lenskit/blob/main/docs/usage/repobrief-mcp-stdio.md)<br>`repository`: [https://github.com/heimgewebe/lenskit](https://github.com/heimgewebe/lenskit) |
| Metarepo | repository | Fleet membership, canonical shared contracts and repository templates | repository purpose semantics<br>runtime health<br>task state | fleet_membership | `repository`: [https://github.com/heimgewebe/metarepo](https://github.com/heimgewebe/metarepo) |
| Mitschreiber | repository | Privacy-first on-device context capture and redacted event production | task authority<br>ecosystem semantics<br>merge approval | — | `repository`: [https://github.com/heimgewebe/mitschreiber](https://github.com/heimgewebe/mitschreiber) |
| Obsidian Bridge | repository | deterministic CLI and artifact bridge for using Obsidian as a projection and observatory interface | vault content truth<br>personal notes<br>task state<br>ecosystem semantics | — | `contracts`: [https://github.com/heimgewebe/obsidian-bridge/tree/main/contracts](https://github.com/heimgewebe/obsidian-bridge/tree/main/contracts)<br>`readme`: [https://github.com/heimgewebe/obsidian-bridge/blob/main/README.md](https://github.com/heimgewebe/obsidian-bridge/blob/main/README.md)<br>`repository`: [https://github.com/heimgewebe/obsidian-bridge](https://github.com/heimgewebe/obsidian-bridge) |
| Plexer | repository | bounded event delivery and queueing gateway | task prioritization<br>canonical history<br>ecosystem semantics | — | `repository`: [https://github.com/heimgewebe/plexer](https://github.com/heimgewebe/plexer) |
| Schauwerk | repository | visual surface and projection layer | canonical ecosystem semantics<br>task state<br>execution authority | specialized_visual_rendering | `repository`: [https://github.com/heimgewebe/schauwerk](https://github.com/heimgewebe/schauwerk) |
| semantAH | repository | Semantic index, embeddings and knowledge-graph pipeline | task authority<br>canonical event history<br>runtime health | — | `repository`: [https://github.com/heimgewebe/semantAH](https://github.com/heimgewebe/semantAH) |
| Sichter | repository | Code-review and pull-request automation prototype | merge authority<br>task priority<br>runtime truth | — | `repository`: [https://github.com/heimgewebe/sichter](https://github.com/heimgewebe/sichter) |
| Snippet Engine Control | repository | engine-neutral contract, diagnostics and diffable export-planning layer for text-expansion systems | the text-expansion runtime itself<br>automatic writes without explicit apply<br>task state<br>ecosystem semantics | — | `contracts`: [https://github.com/heimgewebe/snippet-engine-control/tree/main/contracts](https://github.com/heimgewebe/snippet-engine-control/tree/main/contracts)<br>`readme`: [https://github.com/heimgewebe/snippet-engine-control/blob/main/README.md](https://github.com/heimgewebe/snippet-engine-control/blob/main/README.md)<br>`repository`: [https://github.com/heimgewebe/snippet-engine-control](https://github.com/heimgewebe/snippet-engine-control) |
| Steuerboard | repository | read-only repo-state signal | task authorization<br>merge approval<br>runtime mutation | repository_observation_readiness | `repository`: [https://github.com/heimgewebe/steuerboard](https://github.com/heimgewebe/steuerboard) |
| Systemkatalog | repository | app-independent catalog for system purposes, truth ownership, stable relations and entrypoints | task priority or status<br>runtime health<br>merge readiness<br>agent dispatch | ecosystem_semantics | `agentEntry`: [AGENTS.md](../AGENTS.md)<br>`readme`: [README.md](../README.md)<br>`repository`: [https://github.com/heimgewebe/systemkatalog](https://github.com/heimgewebe/systemkatalog) |
| Vault Gewebe | repository | Versioned shared knowledge vault and design source material | task status<br>runtime truth<br>merge authority | — | `repository`: [https://github.com/heimgewebe/vault-gewebe](https://github.com/heimgewebe/vault-gewebe) |
| Vibe-Lab | repository | bounded prospective experiments, evidence review and proposal-ready learning candidates | production authority<br>task status<br>automatic policy or routing application<br>append-only historical truth | bounded_experiments<br>reviewed_learning_proposals | `repository`: [https://github.com/heimgewebe/vibe-lab](https://github.com/heimgewebe/vibe-lab) |
| Weltgewebe | repository | federated map and coordination system for collective goods, local relationships and community action | ecosystem governance<br>fleet task orchestration | — | `repository`: [https://github.com/heimgewebe/weltgewebe](https://github.com/heimgewebe/weltgewebe)<br>`targetArchitecture`: [https://github.com/heimgewebe/weltgewebe/blob/main/architecture/weltgewebe-os.md](https://github.com/heimgewebe/weltgewebe/blob/main/architecture/weltgewebe-os.md) |
| WGX | repository | Fleet CLI and reusable repository workflow engine | repository purpose semantics<br>runtime truth<br>task priority | shared_fleet_ci_checks | `repository`: [https://github.com/heimgewebe/wgx](https://github.com/heimgewebe/wgx) |
| CI / Checks | service | automated tests, lint, gates and review signals | merge authorization<br>runtime health<br>task priority | technical_check_results | `checks`: [https://github.com/heimgewebe](https://github.com/heimgewebe) |
| GitHub | service | repository, PR, issue and review state | local runtime health<br>task priority<br>ecosystem semantics | branches_prs_reviews | `organization`: [https://github.com/heimgewebe](https://github.com/heimgewebe) |

## Repository-Abdeckung

Metarepo ist Primärquelle für die Fleet-Mitgliedschaft. Der Systemkatalog bleibt Primärquelle für Zweck, Beziehungen, Wahrheitszuständigkeiten und Einstiegspunkte.

| System | Repository | Einordnung | Einstieg |
|---|---|---|---|
| Agent Control Surface | `heimgewebe/agent-control-surface` | `catalog-only` | [https://github.com/heimgewebe/agent-control-surface](https://github.com/heimgewebe/agent-control-surface) |
| Außensensor | `heimgewebe/aussensensor` | `fleet` | [https://github.com/heimgewebe/aussensensor](https://github.com/heimgewebe/aussensensor) |
| Bureau | `heimgewebe/bureau` | `catalog-only` | [https://github.com/heimgewebe/bureau](https://github.com/heimgewebe/bureau) |
| Chronik | `heimgewebe/chronik` | `fleet` | [https://github.com/heimgewebe/chronik](https://github.com/heimgewebe/chronik) |
| Commonworld | `heimgewebe/commonworld` | `catalog-only` | [https://github.com/heimgewebe/commonworld](https://github.com/heimgewebe/commonworld) |
| Contracts Mirror | `heimgewebe/contracts-mirror` | `fleet` | [https://github.com/heimgewebe/contracts-mirror](https://github.com/heimgewebe/contracts-mirror) |
| Device Graph | `heimgewebe/device-graph` | `catalog-only` | [https://github.com/heimgewebe/device-graph](https://github.com/heimgewebe/device-graph) |
| Grabowski | `heimgewebe/grabowski` | `catalog-only` | [https://github.com/heimgewebe/grabowski](https://github.com/heimgewebe/grabowski) |
| HausKI | `heimgewebe/hausKI` | `fleet` | [https://github.com/heimgewebe/hausKI](https://github.com/heimgewebe/hausKI) |
| HausKI Audio | `heimgewebe/hausKI-audio` | `fleet` | [https://github.com/heimgewebe/hausKI-audio](https://github.com/heimgewebe/hausKI-audio) |
| heim-pc | `heimgewebe/heim-pc` | `fleet` | [https://github.com/heimgewebe/heim-pc](https://github.com/heimgewebe/heim-pc) |
| Heimgeist | `heimgewebe/heimgeist` | `fleet` | [https://github.com/heimgewebe/heimgeist](https://github.com/heimgewebe/heimgeist) |
| heimlern | `heimgewebe/heimlern` | `fleet` | [https://github.com/heimgewebe/heimlern](https://github.com/heimgewebe/heimlern) |
| Heimserver | `heimgewebe/heimserver` | `catalog-only` | [https://github.com/heimgewebe/heimserver](https://github.com/heimgewebe/heimserver) |
| Infra | `heimgewebe/infra` | `catalog-only` | [https://github.com/heimgewebe/infra](https://github.com/heimgewebe/infra) |
| Konvergenzregelkreis | `heimgewebe/konvergenzregelkreis` | `fleet` | [https://github.com/heimgewebe/konvergenzregelkreis](https://github.com/heimgewebe/konvergenzregelkreis) |
| Leitstand | `heimgewebe/leitstand` | `fleet` | [https://github.com/heimgewebe/leitstand](https://github.com/heimgewebe/leitstand) |
| Leitwerk | `heimgewebe/leitwerk` | `catalog-only` | [https://github.com/heimgewebe/leitwerk](https://github.com/heimgewebe/leitwerk) |
| Lenskit / RepoBrief implementation | `heimgewebe/lenskit` | `fleet` | [https://github.com/heimgewebe/lenskit](https://github.com/heimgewebe/lenskit) |
| Metarepo | `heimgewebe/metarepo` | `fleet` | [https://github.com/heimgewebe/metarepo](https://github.com/heimgewebe/metarepo) |
| Mitschreiber | `heimgewebe/mitschreiber` | `fleet` | [https://github.com/heimgewebe/mitschreiber](https://github.com/heimgewebe/mitschreiber) |
| Obsidian Bridge | `heimgewebe/obsidian-bridge` | `catalog-only` | [https://github.com/heimgewebe/obsidian-bridge](https://github.com/heimgewebe/obsidian-bridge) |
| Plexer | `heimgewebe/plexer` | `fleet` | [https://github.com/heimgewebe/plexer](https://github.com/heimgewebe/plexer) |
| Schauwerk | `heimgewebe/schauwerk` | `catalog-only` | [https://github.com/heimgewebe/schauwerk](https://github.com/heimgewebe/schauwerk) |
| semantAH | `heimgewebe/semantAH` | `fleet` | [https://github.com/heimgewebe/semantAH](https://github.com/heimgewebe/semantAH) |
| Sichter | `heimgewebe/sichter` | `fleet` | [https://github.com/heimgewebe/sichter](https://github.com/heimgewebe/sichter) |
| Snippet Engine Control | `heimgewebe/snippet-engine-control` | `catalog-only` | [https://github.com/heimgewebe/snippet-engine-control](https://github.com/heimgewebe/snippet-engine-control) |
| Steuerboard | `heimgewebe/steuerboard` | `catalog-only` | [https://github.com/heimgewebe/steuerboard](https://github.com/heimgewebe/steuerboard) |
| Systemkatalog | `heimgewebe/systemkatalog` | `catalog-only` | [https://github.com/heimgewebe/systemkatalog](https://github.com/heimgewebe/systemkatalog) |
| Vault Gewebe | `heimgewebe/vault-gewebe` | `fleet` | [https://github.com/heimgewebe/vault-gewebe](https://github.com/heimgewebe/vault-gewebe) |
| Vibe-Lab | `heimgewebe/vibe-lab` | `catalog-only` | [https://github.com/heimgewebe/vibe-lab](https://github.com/heimgewebe/vibe-lab) |
| Weltgewebe | `heimgewebe/weltgewebe` | `related` | [https://github.com/heimgewebe/weltgewebe](https://github.com/heimgewebe/weltgewebe) |
| WGX | `heimgewebe/wgx` | `fleet` | [https://github.com/heimgewebe/wgx](https://github.com/heimgewebe/wgx) |

Explizit außerhalb der Fleet-Quelle:

- `vault-privat` — Private related repository explicitly marked fleet: false in Metarepo.

## Organisationsumfang

Der GitHub-Snapshot umfasst 35 aktive, nicht geforkte Repositories. Davon sind 33 als Systeme katalogisiert und 2 begründet ausgeschlossen.

Begründete Ausschlüsse:

- `heimgewebe/demo-repository` (`public`) — GitHub demonstration scaffold; it is not a Heimgewebe system, authority source or production component.
- `heimgewebe/vault-privat` (`private`) — Private content repository; it contains personal and domain material rather than system implementation or canonical ecosystem semantics.

## Wahrheitszuständigkeiten

| Bereich | Primärquelle | Nicht-autoritative Projektionen |
|---|---|---|
| `agent_routing` | `grabowski` | bureau, systemkatalog |
| `append_only_history` | `chronik` | leitstand |
| `bounded_experiments` | `vibe_lab` | systemkatalog |
| `branches_prs_reviews` | `github` | bureau, leitstand |
| `convergence_protocol` | `konvergenzregelkreis` | — |
| `ecosystem_semantics` | `systemkatalog` | leitstand, schauwerk |
| `fleet_membership` | `metarepo` | systemkatalog |
| `general_operator_display` | `leitstand` | — |
| `live_service_state` | `runtime` | leitstand |
| `local_fleet_execution` | `grabowski` | leitstand |
| `repository_context_citations` | `repobrief_lenskit` | rlens, systemkatalog |
| `repository_observation_readiness` | `steuerboard` | grabowski, leitstand |
| `reviewed_learning_proposals` | `vibe_lab` | bureau, systemkatalog |
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
| Agent Control Surface | `operates_on` | GitHub | `bounded` | The manual local control surface can prepare guarded Git work while GitHub remains primary state. |
| Außensensor | `delivers_to` | Chronik | `stable` | Curated external events are delivered to Chronik as the historical ingest authority. |
| Bureau | `delegates_to` | Grabowski | `stable` | Bureau can hand scoped work to the operator layer. |
| Bureau | `provides` | Leitstand | `stable` | Bureau may provide read-only task status artifacts. |
| Chronik | `displayed_by` | Leitstand | `stable` | Leitstand may display Chronik state without treating the display as authority. |
| Chronik | `evidence_for` | Bureau | `bounded` | Chronik event presence can support evidence references; Bureau still owns task and verification truth. |
| Chronik | `learning_input_for` | Vibe-Lab | `bounded` | Chronik may supply frozen historical outcome cohorts as evidence for prospectively registered Vibe-Lab experiments; no policy or task is auto-applied. |
| Chronik | `provides` | Leitstand | `stable` | Chronik provides event trace artifacts for timelines. |
| Chronik | `provides` | Systemkatalog | `stable` | Chronik provides event trace and historical continuity. |
| Commonworld | `operates_on` | GitHub | `stable` | Commonworld product work is versioned and validated through repository, pull-request and CI state. |
| Contracts Mirror | `validated_by` | CI / Checks | `stable` | Mirrored contracts are checked against their fixtures and source contract. |
| Device Graph | `scope_boundary` | Ecosystem Map v0 | `related` | Device Graph may describe infrastructure devices; it is not the ecosystem-governance map canon. |
| Grabowski | `emits_to` | Chronik | `bounded` | Grabowski may write task-local agent-run events through an explicit Chronik outbox path. |
| Grabowski | `operates_on` | GitHub | `stable` | PRs, branches, issues and reviews remain GitHub-owned state. |
| HausKI Audio | `provides` | HausKI | `related` | HausKI Audio is the bounded audio and automation surface adjacent to the local AI stack. |
| heim-pc | `observes` | Ecosystem Map v0 | `stable` | The local operator entry points to the canonical ecosystem map without duplicating it. |
| Heimgeist | `observes` | Ecosystem Map v0 | `related` | Heimgeist may inspect catalog projections for reflection but does not own catalog truth. |
| Heimserver | `scope_boundary` | Infra | `related` | Heimserver retains the private service-layer and edge contracts; Infra remains the broader host and network runbook surface. |
| Konvergenzregelkreis | `scope_boundary` | Bureau | `stable` | Konvergenzregelkreis assesses submitted evidence; Bureau remains the sole owner of tasks, claims and completion. |
| Leitstand | `observes` | Ecosystem Map v0 | `stable` | Leitstand observes the map as orientation, not truth. |
| Leitwerk | `scope_boundary` | Bureau | `related` | Leitwerk is retained as a normative reference; Bureau owns current task, claim and completion state. |
| Leitwerk | `scope_boundary` | Konvergenzregelkreis | `related` | Leitwerk remains a historical pre-Bureau reference; Konvergenzregelkreis is an independent public protocol and inherits no Leitwerk authority. |
| Lenskit / RepoBrief implementation | `implements` | RepoBrief | `stable` | RepoBrief is the public context-view name; Lenskit remains an implementation namespace for now. |
| Metarepo | `provides` | Contracts Mirror | `stable` | Canonical contracts originate in Metarepo and are mirrored for validation and publication. |
| Metarepo | `provides` | Systemkatalog | `stable` | Metarepo provides Fleet membership; Systemkatalog remains authority for purpose, relations and entrypoints. |
| Mitschreiber | `emits_to` | Chronik | `stable` | Redacted on-device context events are emitted to Chronik. |
| Mitschreiber | `provides` | semantAH | `bounded` | Redacted embeddings and context signals can feed semantic indexing without raw-text authority. |
| Obsidian Bridge | `provides` | Vault Gewebe | `bounded` | Obsidian Bridge projects machine artifacts into the vault interface without owning vault content. |
| Plexer | `delivers_to` | Chronik | `stable` | Plexer delivers bounded operational events to Chronik agent.ledger when configured. |
| Schauwerk | `renders` | Ecosystem Map v0 | `stable` | Schauwerk may render map views without owning the map canon. |
| semantAH | `provides` | HausKI | `stable` | semantAH provides the semantic memory and knowledge-graph layer used by HausKI. |
| Sichter | `operates_on` | GitHub | `bounded` | Sichter reviews repository changes and may prepare pull requests within policy boundaries. |
| Snippet Engine Control | `provides` | heim-pc | `bounded` | Snippet Engine Control provides contract-first diagnostics and export planning for the local interaction layer. |
| Steuerboard | `observes` | Systemkatalog | `stable` | Steuerboard can provide read-only repo-state signals, not decisions. |
| Systemkatalog | `owns` | Ecosystem Map v0 | `stable` | Systemkatalog owns the map semantics during v0. |
| Systemkatalog | `provides` | Leitstand | `stable` | Systemkatalog provides map artifacts for Leitstand display. |
| Vault Gewebe | `scope_boundary` | Systemkatalog | `related` | Vault material may inform catalog edits but is not active catalog canon. |
| Vibe-Lab | `exports_candidate_to` | Bureau | `bounded` | Vibe-Lab may export reviewed proposal-ready candidates; Bureau alone decides whether they become work. |
| Vibe-Lab | `provides` | Systemkatalog | `stable` | Vibe-Lab provides method experiments and evidence patterns. |
| Weltgewebe | `operates_on` | GitHub | `stable` | Weltgewebe product work is still validated through repo, PR and CI state. |
| WGX | `provides` | CI / Checks | `stable` | WGX provides reusable Fleet checks and repository workflow mechanics. |
| CI / Checks | `provides` | Leitstand | `stable` | Primary check state can be reflected. |
| GitHub | `provides` | Leitstand | `stable` | Primary repo state can be reflected. |
| GitHub | `validated_by` | CI / Checks | `stable` | Checks and review gates provide hard technical feedback. |

## Einstiegspunkte

| System | Einstieg |
|---|---|
| Bureau | [https://github.com/heimgewebe/bureau](https://github.com/heimgewebe/bureau) |
| GitHub | [https://github.com/heimgewebe](https://github.com/heimgewebe) |
| Grabowski | [https://github.com/heimgewebe/grabowski](https://github.com/heimgewebe/grabowski) |
| Grabowski Agent-Routing | [https://github.com/heimgewebe/grabowski/blob/main/docs/generated/operator-context.v1.json](https://github.com/heimgewebe/grabowski/blob/main/docs/generated/operator-context.v1.json) |
| Leitstand | [https://github.com/heimgewebe/leitstand](https://github.com/heimgewebe/leitstand) |
| Metarepo Fleet-Mitgliedschaft | [https://github.com/heimgewebe/metarepo/blob/main/fleet/repos.yml](https://github.com/heimgewebe/metarepo/blob/main/fleet/repos.yml) |
| RepoBrief / Lenskit | [https://github.com/heimgewebe/lenskit](https://github.com/heimgewebe/lenskit) |
| Systemkatalog | [README.md](../README.md) |

## Grenzen

- Aufgaben, Queue und Receipts: Bureau.
- Repository-, PR- und Reviewzustand: GitHub.
- Technische Prüfergebnisse: CI und Review-Gates.
- Laufende Dienste: Runtime, Healthchecks, systemd und Logs.
- Lokale und repositorybezogene Ausführung: Grabowski nach Freigabe.
- Konkrete Runtime-Identitäten, Provider-Agenten und Topologie sind keine Katalogsysteme.
- Die frühere Cabinet-Oberfläche ist archiviert; der Katalog wird ausschließlich als versionierte Markdown-, Mermaid- und JSON-Artefakte bereitgestellt.
- Frühere dynamische Claims und Radarflächen sind historische Kompatibilität, keine aktuelle Katalogwahrheit.
