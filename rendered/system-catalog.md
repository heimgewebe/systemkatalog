# Systemkatalog

> Automatisch erzeugte, app-unabhängige Leseansicht. Sie beschreibt stabile Rollen und verweist auf Primärquellen; sie enthält keinen Live-, Task- oder Merge-Status.

## Zweck

Der Katalog beantwortet, welche Systeme existieren, welchem Zweck sie dienen, wem welche Wahrheit gehört, welche stabilen Beziehungen bestehen und wo die Einstiegspunkte liegen.

## Systeme

| System | Typ | Kritikalität | Ausfalldomänen | Zweck | Nicht zuständig für | Wahrheitsbesitz | Einstiegspunkte |
|---|---|---|---|---|---|---|---|
| Ecosystem Map v0 | artifact | `optional` | — | machine-readable overview graph and rendered orientation map | claim truth<br>runtime health<br>merge readiness | — | `artifact`: [rendered/ecosystem-registry-map.mmd](../rendered/ecosystem-registry-map.mmd) |
| Alexander | human | `foundational` | human:alexander | meaning, approval and abort authority outside automation | automated execution<br>machine-derived repository or runtime state | — | `authorityPolicy`: [policy/system-catalog.v1.json](../policy/system-catalog.v1.json) |
| Agent Control Surface | repository | `unknown` | identity:github<br>provider:github | local manual control surface for Jules sessions and guarded step-by-step Git workflows | autonomous task dispatch<br>task priority<br>merge authorization<br>remote access security | — | `readme`: [https://github.com/heimgewebe/agent-control-surface/blob/main/README.md](https://github.com/heimgewebe/agent-control-surface/blob/main/README.md)<br>`repository`: [https://github.com/heimgewebe/agent-control-surface](https://github.com/heimgewebe/agent-control-surface)<br>`runbook`: [https://github.com/heimgewebe/agent-control-surface/blob/main/RUNBOOK.md](https://github.com/heimgewebe/agent-control-surface/blob/main/RUNBOOK.md) |
| Außensensor | repository | `unknown` | identity:github<br>provider:github | Curated external signals and event feeds for Chronik | task authority<br>canonical event history<br>merge approval | — | `repository`: [https://github.com/heimgewebe/aussensensor](https://github.com/heimgewebe/aussensensor) |
| Bureau | repository | `foundational` | host:heim-pc<br>data:bureau-state<br>identity:github<br>credentials:operator<br>provider:backup-storage | task cadence, delegation, run reporting | runtime execution<br>Git and review truth<br>ecosystem semantics | tasks_claims_completion | `repository`: [https://github.com/heimgewebe/bureau](https://github.com/heimgewebe/bureau) |
| Chronik | repository | `supporting` | host:heim-pc<br>data:chronik-store<br>provider:backup-storage | append-only event ledger and historical evidence axis | task state<br>policy decisions<br>runtime mutation | append_only_history | `repository`: [https://github.com/heimgewebe/chronik](https://github.com/heimgewebe/chronik) |
| Commonworld | repository | `unknown` | identity:github<br>provider:github | Interactive globe and commons-oriented world exploration | ecosystem governance<br>task state<br>merge authority | — | `repository`: [https://github.com/heimgewebe/commonworld](https://github.com/heimgewebe/commonworld) |
| Contracts Mirror | repository | `unknown` | identity:github<br>provider:github | Validated mirror and publication surface for canonical Metarepo contracts | canonical contract authorship<br>runtime status<br>task authority | — | `repository`: [https://github.com/heimgewebe/contracts-mirror](https://github.com/heimgewebe/contracts-mirror) |
| Device Graph | repository | `unknown` | identity:github<br>provider:github | infrastructure device graph; adjacent but not ecosystem-governance canon | ecosystem governance canon<br>task state<br>merge authority | — | `repository`: [https://github.com/heimgewebe/device-graph](https://github.com/heimgewebe/device-graph) |
| Grabowski | repository | `foundational` | host:heim-pc<br>control:grabowski-runtime<br>credentials:operator<br>network:public-internet<br>provider:backup-storage<br>data:grabowski-outbox | operator execution, repo work, review gates | task priority<br>ecosystem semantics<br>primary Git or runtime truth | agent_routing<br>local_fleet_execution | `repository`: [https://github.com/heimgewebe/grabowski](https://github.com/heimgewebe/grabowski) |
| HausKI | repository | `unknown` | identity:github<br>provider:github | Local offline-first AI orchestration and policy-controlled memory | fleet task authority<br>ecosystem catalog semantics<br>merge approval | — | `repository`: [https://github.com/heimgewebe/hausKI](https://github.com/heimgewebe/hausKI) |
| HausKI Audio | repository | `unknown` | identity:github<br>provider:github | Local audio playback, recording and automation | ecosystem catalog semantics<br>task authority<br>merge approval | — | `repository`: [https://github.com/heimgewebe/hausKI-audio](https://github.com/heimgewebe/hausKI-audio) |
| heim-pc | repository | `unknown` | identity:github<br>provider:github | Versioned local operator entry and host orientation | fleet task authority<br>service runtime truth<br>ecosystem semantics | — | `repository`: [https://github.com/heimgewebe/heim-pc](https://github.com/heimgewebe/heim-pc) |
| Heimgeist | repository | `unknown` | identity:github<br>provider:github | System self-reflection and meta-agent experimentation | production authority<br>task state<br>merge approval | — | `repository`: [https://github.com/heimgewebe/heimgeist](https://github.com/heimgewebe/heimgeist) |
| heimlern | repository | `optional` | provider:github | archived historical reference for the former offline operator-learning implementation | active learning proposals<br>runtime operation<br>automatic policy application<br>task dispatch<br>merge authorization<br>active contract authority<br>new feature development without a separately registered experiment | — | `repository`: [https://github.com/heimgewebe/heimlern](https://github.com/heimgewebe/heimlern) |
| Heimserver | repository | `unknown` | identity:github<br>provider:github | private operations and contract repository for the home-network service layer, edge gateway, DDNS and Weltgewebe infrastructure | runtime health claims without live checks<br>task state<br>ecosystem semantics<br>secret storage in Git | — | `agentEntry`: [https://github.com/heimgewebe/heimserver/blob/main/AGENTS.md](https://github.com/heimgewebe/heimserver/blob/main/AGENTS.md)<br>`readme`: [https://github.com/heimgewebe/heimserver/blob/main/README.md](https://github.com/heimgewebe/heimserver/blob/main/README.md)<br>`repository`: [https://github.com/heimgewebe/heimserver](https://github.com/heimgewebe/heimserver)<br>`systemMap`: [https://github.com/heimgewebe/heimserver/blob/main/SYSTEM_MAP.md](https://github.com/heimgewebe/heimserver/blob/main/SYSTEM_MAP.md) |
| Infra | repository | `unknown` | identity:github<br>provider:github | host, network, cockpit and operational runbooks | task state<br>ecosystem semantics<br>product-domain truth | — | `repository`: [https://github.com/heimgewebe/infra](https://github.com/heimgewebe/infra) |
| Konvergenzregelkreis | repository | `essential` | identity:github<br>provider:github | public stateless convergence protocol and conformance core for evidence-bound closure of ecosystem changes | task state<br>queue or claims<br>execution, leases or recovery<br>merge authorization<br>deployment state or runtime health<br>ecosystem semantics<br>fleet membership<br>event history<br>product telemetry | convergence_protocol | `agentEntry`: [https://github.com/heimgewebe/konvergenzregelkreis/blob/main/AGENTS.md](https://github.com/heimgewebe/konvergenzregelkreis/blob/main/AGENTS.md)<br>`profiles`: [https://github.com/heimgewebe/konvergenzregelkreis/tree/main/profiles](https://github.com/heimgewebe/konvergenzregelkreis/tree/main/profiles)<br>`protocol`: [https://github.com/heimgewebe/konvergenzregelkreis/tree/main/protocol](https://github.com/heimgewebe/konvergenzregelkreis/tree/main/protocol)<br>`readme`: [https://github.com/heimgewebe/konvergenzregelkreis/blob/main/README.md](https://github.com/heimgewebe/konvergenzregelkreis/blob/main/README.md)<br>`repository`: [https://github.com/heimgewebe/konvergenzregelkreis](https://github.com/heimgewebe/konvergenzregelkreis)<br>`roleBoundary`: [https://github.com/heimgewebe/konvergenzregelkreis/blob/main/system/regelkreis-role.v1.json](https://github.com/heimgewebe/konvergenzregelkreis/blob/main/system/regelkreis-role.v1.json) |
| Leitstand | repository | `supporting` | identity:github<br>provider:github | read-only ecosystem observability and status projection | canonical truth ownership<br>task authorization<br>runtime mutation | general_operator_display | `repository`: [https://github.com/heimgewebe/leitstand](https://github.com/heimgewebe/leitstand) |
| Leitwerk | repository | `unknown` | identity:github<br>provider:github | retained normative coordination-contract reference from the pre-Bureau and pre-Grabowski control model | current task or claim state<br>runtime execution<br>merge authorization<br>agent dispatch | — | `readme`: [https://github.com/heimgewebe/leitwerk/blob/main/README.md](https://github.com/heimgewebe/leitwerk/blob/main/README.md)<br>`repository`: [https://github.com/heimgewebe/leitwerk](https://github.com/heimgewebe/leitwerk)<br>`roleBoundary`: [https://github.com/heimgewebe/leitwerk/blob/main/docs/leitwerk.md](https://github.com/heimgewebe/leitwerk/blob/main/docs/leitwerk.md) |
| Metarepo | repository | `essential` | identity:github<br>provider:github | Fleet membership, canonical shared contracts and repository templates | repository purpose semantics<br>runtime health<br>task state | fleet_membership | `repository`: [https://github.com/heimgewebe/metarepo](https://github.com/heimgewebe/metarepo) |
| Mitschreiber | repository | `unknown` | identity:github<br>provider:github | Privacy-first on-device context capture and redacted event production | task authority<br>ecosystem semantics<br>merge approval | — | `repository`: [https://github.com/heimgewebe/mitschreiber](https://github.com/heimgewebe/mitschreiber) |
| Obsidian Bridge | repository | `unknown` | identity:github<br>provider:github | deterministic CLI and artifact bridge for using Obsidian as a projection and observatory interface | vault content truth<br>personal notes<br>task state<br>ecosystem semantics | — | `contracts`: [https://github.com/heimgewebe/obsidian-bridge/tree/main/contracts](https://github.com/heimgewebe/obsidian-bridge/tree/main/contracts)<br>`readme`: [https://github.com/heimgewebe/obsidian-bridge/blob/main/README.md](https://github.com/heimgewebe/obsidian-bridge/blob/main/README.md)<br>`repository`: [https://github.com/heimgewebe/obsidian-bridge](https://github.com/heimgewebe/obsidian-bridge) |
| Plexer | repository | `unknown` | identity:github<br>provider:github | bounded event delivery and queueing gateway | task prioritization<br>canonical history<br>ecosystem semantics | — | `repository`: [https://github.com/heimgewebe/plexer](https://github.com/heimgewebe/plexer) |
| RepoGround | repository | `supporting` | host:heim-pc<br>runtime:repoground<br>runtime:lenskit-legacy | verifiable, citable codebase context for humans and AI systems | repository operational state<br>task priority<br>merge authorization | repository_context_citations | `mcpServer`: [https://github.com/heimgewebe/repoground/blob/main/docs/usage/repobrief-mcp-stdio.md](https://github.com/heimgewebe/repoground/blob/main/docs/usage/repobrief-mcp-stdio.md)<br>`repository`: [https://github.com/heimgewebe/repoground](https://github.com/heimgewebe/repoground) |
| Schauwerk | repository | `optional` | identity:github<br>provider:github | visual surface and projection layer | canonical ecosystem semantics<br>task state<br>execution authority | specialized_visual_rendering | `repository`: [https://github.com/heimgewebe/schauwerk](https://github.com/heimgewebe/schauwerk) |
| semantAH | repository | `unknown` | identity:github<br>provider:github | Semantic index, embeddings and knowledge-graph pipeline | task authority<br>canonical event history<br>runtime health | — | `repository`: [https://github.com/heimgewebe/semantAH](https://github.com/heimgewebe/semantAH) |
| Sichter | repository | `unknown` | identity:github<br>provider:github | Code-review and pull-request automation prototype | merge authority<br>task priority<br>runtime truth | — | `repository`: [https://github.com/heimgewebe/sichter](https://github.com/heimgewebe/sichter) |
| Snippet Engine Control | repository | `unknown` | identity:github<br>provider:github | engine-neutral contract, diagnostics and diffable export-planning layer for text-expansion systems | the text-expansion runtime itself<br>automatic writes without explicit apply<br>task state<br>ecosystem semantics | — | `contracts`: [https://github.com/heimgewebe/snippet-engine-control/tree/main/contracts](https://github.com/heimgewebe/snippet-engine-control/tree/main/contracts)<br>`readme`: [https://github.com/heimgewebe/snippet-engine-control/blob/main/README.md](https://github.com/heimgewebe/snippet-engine-control/blob/main/README.md)<br>`repository`: [https://github.com/heimgewebe/snippet-engine-control](https://github.com/heimgewebe/snippet-engine-control) |
| Steuerboard | repository | `unknown` | identity:github<br>provider:github | read-only repo-state signal | task authorization<br>merge approval<br>runtime mutation | repository_observation_readiness | `repository`: [https://github.com/heimgewebe/steuerboard](https://github.com/heimgewebe/steuerboard) |
| Systemkatalog | repository | `essential` | identity:github<br>provider:github | app-independent catalog for system purposes, truth ownership, stable relations and entrypoints | task priority or status<br>runtime health<br>merge readiness<br>agent dispatch | ecosystem_semantics | `agentEntry`: [AGENTS.md](../AGENTS.md)<br>`readme`: [README.md](../README.md)<br>`repository`: [https://github.com/heimgewebe/systemkatalog](https://github.com/heimgewebe/systemkatalog) |
| Vault Gewebe | repository | `unknown` | identity:github<br>provider:github | Versioned shared knowledge vault and design source material | task status<br>runtime truth<br>merge authority | — | `repository`: [https://github.com/heimgewebe/vault-gewebe](https://github.com/heimgewebe/vault-gewebe) |
| Vibe-Lab | repository | `optional` | identity:github<br>provider:github | bounded prospective experiments, evidence review and proposal-ready learning candidates | production authority<br>task status<br>automatic policy or routing application<br>append-only historical truth | bounded_experiments<br>reviewed_learning_proposals | `repository`: [https://github.com/heimgewebe/vibe-lab](https://github.com/heimgewebe/vibe-lab) |
| Weltgewebe | repository | `essential` | host:wg-prod-1<br>data:weltgewebe-postgresql<br>stream:weltgewebe-jetstream<br>network:public-internet<br>credentials:operator<br>provider:backup-storage | federated map and coordination system for collective goods, local relationships and community action | ecosystem governance<br>fleet task orchestration | — | `repository`: [https://github.com/heimgewebe/weltgewebe](https://github.com/heimgewebe/weltgewebe)<br>`targetArchitecture`: [https://github.com/heimgewebe/weltgewebe/blob/main/architecture/weltgewebe-os.md](https://github.com/heimgewebe/weltgewebe/blob/main/architecture/weltgewebe-os.md) |
| WGX | repository | `unknown` | identity:github<br>provider:github | Fleet CLI and reusable repository workflow engine | repository purpose semantics<br>runtime truth<br>task priority | shared_fleet_ci_checks | `repository`: [https://github.com/heimgewebe/wgx](https://github.com/heimgewebe/wgx) |
| CI / Checks | service | `supporting` | provider:github<br>network:public-internet | automated tests, lint, gates and review signals | merge authorization<br>runtime health<br>task priority | technical_check_results | `checks`: [https://github.com/heimgewebe](https://github.com/heimgewebe) |
| GitHub | service | `foundational` | provider:github<br>network:public-internet<br>credentials:operator | repository, PR, issue and review state | local runtime health<br>task priority<br>ecosystem semantics | branches_prs_reviews | `organization`: [https://github.com/heimgewebe](https://github.com/heimgewebe) |

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
| heimlern | `heimgewebe/heimlern` | `archived-reference` | [https://github.com/heimgewebe/heimlern](https://github.com/heimgewebe/heimlern) |
| Heimserver | `heimgewebe/heimserver` | `catalog-only` | [https://github.com/heimgewebe/heimserver](https://github.com/heimgewebe/heimserver) |
| Infra | `heimgewebe/infra` | `catalog-only` | [https://github.com/heimgewebe/infra](https://github.com/heimgewebe/infra) |
| Konvergenzregelkreis | `heimgewebe/konvergenzregelkreis` | `fleet` | [https://github.com/heimgewebe/konvergenzregelkreis](https://github.com/heimgewebe/konvergenzregelkreis) |
| Leitstand | `heimgewebe/leitstand` | `fleet` | [https://github.com/heimgewebe/leitstand](https://github.com/heimgewebe/leitstand) |
| Leitwerk | `heimgewebe/leitwerk` | `catalog-only` | [https://github.com/heimgewebe/leitwerk](https://github.com/heimgewebe/leitwerk) |
| Metarepo | `heimgewebe/metarepo` | `fleet` | [https://github.com/heimgewebe/metarepo](https://github.com/heimgewebe/metarepo) |
| Mitschreiber | `heimgewebe/mitschreiber` | `fleet` | [https://github.com/heimgewebe/mitschreiber](https://github.com/heimgewebe/mitschreiber) |
| Obsidian Bridge | `heimgewebe/obsidian-bridge` | `catalog-only` | [https://github.com/heimgewebe/obsidian-bridge](https://github.com/heimgewebe/obsidian-bridge) |
| Plexer | `heimgewebe/plexer` | `fleet` | [https://github.com/heimgewebe/plexer](https://github.com/heimgewebe/plexer) |
| RepoGround | `heimgewebe/repoground` | `fleet` | [https://github.com/heimgewebe/repoground](https://github.com/heimgewebe/repoground) |
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

Explizit ohne aktive Fleet-Mitgliedschaft:

- `heimlern` — Archived historical reference explicitly marked status: archived-reference and fleet: false in the bound Metarepo source.
- `vault-privat` — Private related repository explicitly marked fleet: false in Metarepo.

## Organisationsumfang

Der GitHub-Snapshot umfasst 35 nicht geforkte Repositories. Davon sind 32 aktive Katalogsysteme, 1 archivierte Referenz und 2 begründet ausgeschlossen.

Archivierte Referenzen ohne aktive Betriebsautorität:

- `heimgewebe/heimlern` (`public`) — archived historical reference for retired offline learning and proposal experiments; no active runtime or contract authority

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
| `repository_context_citations` | `repoground` | repoground, systemkatalog |
| `repository_observation_readiness` | `steuerboard` | grabowski, leitstand |
| `reviewed_learning_proposals` | `vibe_lab` | bureau, systemkatalog |
| `shared_fleet_ci_checks` | `wgx` | github_ci |
| `specialized_visual_rendering` | `schauwerk` | — |
| `tasks_claims_completion` | `bureau` | leitstand |
| `technical_check_results` | `ci` | github, leitstand |

## Stabile Beziehungen

Nur Beziehungen der Klassen `stable`, `bounded` oder `related` werden angezeigt. Die Klasse beschreibt die Dauerhaftigkeit der Architekturbeziehung, nicht ihren aktuellen Betriebszustand. Resilienzfelder erscheinen nur für fachlich geprüfte, ausfall- oder autoritätsrelevante Kanten; `—` bedeutet nicht geprüft, nicht automatisch harmlos.

| Von | Beziehung | Zu | Klasse | Kopplung | Ausfallpolitik | Autoritätsrichtung | Recovery | Bedeutung |
|---|---|---|---|---|---|---|---|---|
| Alexander | `steers` | Systemkatalog | `stable` | `manual` | `block` | `from-to` | `—` | Human sense, priority, approval and abort authority stay outside automation. |
| Agent Control Surface | `operates_on` | GitHub | `bounded` | `—` | `—` | `—` | `—` | The manual local control surface can prepare guarded Git work while GitHub remains primary state. |
| Außensensor | `delivers_to` | Chronik | `stable` | `—` | `—` | `—` | `—` | Curated external events are delivered to Chronik as the historical ingest authority. |
| Bureau | `delegates_to` | Grabowski | `stable` | `synchronous-blocking` | `block` | `from-to` | `—` | Bureau can hand scoped work to the operator layer. |
| Bureau | `provides` | Leitstand | `stable` | `observational` | `degrade` | `from-to` | `—` | Bureau may provide read-only task status artifacts. |
| Chronik | `displayed_by` | Leitstand | `stable` | `—` | `—` | `—` | `—` | Leitstand may display Chronik state without treating the display as authority. |
| Chronik | `evidence_for` | Bureau | `bounded` | `observational` | `degrade` | `from-to` | `—` | Chronik event presence can support evidence references; Bureau still owns task and verification truth. |
| Chronik | `learning_input_for` | Vibe-Lab | `bounded` | `observational` | `degrade` | `from-to` | `—` | Chronik may supply frozen historical outcome cohorts as evidence for prospectively registered Vibe-Lab experiments; no policy or task is auto-applied. |
| Chronik | `provides` | Leitstand | `stable` | `observational` | `degrade` | `from-to` | `—` | Chronik provides event trace artifacts for timelines. |
| Chronik | `provides` | Systemkatalog | `stable` | `—` | `—` | `—` | `—` | Chronik provides event trace and historical continuity. |
| Commonworld | `operates_on` | GitHub | `stable` | `—` | `—` | `—` | `—` | Commonworld product work is versioned and validated through repository, pull-request and CI state. |
| Contracts Mirror | `validated_by` | CI / Checks | `stable` | `—` | `—` | `—` | `—` | Mirrored contracts are checked against their fixtures and source contract. |
| Device Graph | `scope_boundary` | Ecosystem Map v0 | `related` | `—` | `—` | `—` | `—` | Device Graph may describe infrastructure devices; it is not the ecosystem-governance map canon. |
| Grabowski | `emits_to` | Chronik | `bounded` | `asynchronous-durable` | `queue` | `from-to` | `chronik-durable-outbox` | Grabowski may write task-local agent-run events through an explicit Chronik outbox path. |
| Grabowski | `operates_on` | GitHub | `stable` | `synchronous-blocking` | `block` | `to-from` | `—` | PRs, branches, issues and reviews remain GitHub-owned state. |
| HausKI Audio | `provides` | HausKI | `related` | `—` | `—` | `—` | `—` | HausKI Audio is the bounded audio and automation surface adjacent to the local AI stack. |
| heim-pc | `observes` | Ecosystem Map v0 | `stable` | `—` | `—` | `—` | `—` | The local operator entry points to the canonical ecosystem map without duplicating it. |
| Heimgeist | `observes` | Ecosystem Map v0 | `related` | `—` | `—` | `—` | `—` | Heimgeist may inspect catalog projections for reflection but does not own catalog truth. |
| Heimserver | `scope_boundary` | Infra | `related` | `—` | `—` | `—` | `—` | Heimserver retains the private service-layer and edge contracts; Infra remains the broader host and network runbook surface. |
| Konvergenzregelkreis | `scope_boundary` | Bureau | `stable` | `manual` | `block` | `none` | `—` | Konvergenzregelkreis assesses submitted evidence; Bureau remains the sole owner of tasks, claims and completion. |
| Leitstand | `observes` | Ecosystem Map v0 | `stable` | `—` | `—` | `—` | `—` | Leitstand observes the map as orientation, not truth. |
| Leitwerk | `scope_boundary` | Bureau | `related` | `—` | `—` | `—` | `—` | Leitwerk is retained as a normative reference; Bureau owns current task, claim and completion state. |
| Leitwerk | `scope_boundary` | Konvergenzregelkreis | `related` | `—` | `—` | `—` | `—` | Leitwerk remains a historical pre-Bureau reference; Konvergenzregelkreis is an independent public protocol and inherits no Leitwerk authority. |
| Metarepo | `provides` | Contracts Mirror | `stable` | `—` | `—` | `—` | `—` | Canonical contracts originate in Metarepo and are mirrored for validation and publication. |
| Metarepo | `provides` | Systemkatalog | `stable` | `asynchronous-durable` | `block` | `from-to` | `—` | Metarepo provides Fleet membership; Systemkatalog remains authority for purpose, relations and entrypoints. |
| Mitschreiber | `emits_to` | Chronik | `stable` | `—` | `—` | `—` | `—` | Redacted on-device context events are emitted to Chronik. |
| Mitschreiber | `provides` | semantAH | `bounded` | `—` | `—` | `—` | `—` | Redacted embeddings and context signals can feed semantic indexing without raw-text authority. |
| Obsidian Bridge | `provides` | Vault Gewebe | `bounded` | `—` | `—` | `—` | `—` | Obsidian Bridge projects machine artifacts into the vault interface without owning vault content. |
| Plexer | `delivers_to` | Chronik | `stable` | `asynchronous-durable` | `queue` | `from-to` | `—` | Plexer delivers bounded operational events to Chronik agent.ledger when configured. |
| RepoGround | `provides` | Systemkatalog | `stable` | `—` | `—` | `—` | `—` | RepoGround provides Systemkatalog with verifiable, citable codebase context. |
| Schauwerk | `renders` | Ecosystem Map v0 | `stable` | `observational` | `degrade` | `to-from` | `—` | Schauwerk may render map views without owning the map canon. |
| semantAH | `provides` | HausKI | `stable` | `—` | `—` | `—` | `—` | semantAH provides the semantic memory and knowledge-graph layer used by HausKI. |
| Sichter | `operates_on` | GitHub | `bounded` | `—` | `—` | `—` | `—` | Sichter reviews repository changes and may prepare pull requests within policy boundaries. |
| Snippet Engine Control | `provides` | heim-pc | `bounded` | `—` | `—` | `—` | `—` | Snippet Engine Control provides contract-first diagnostics and export planning for the local interaction layer. |
| Steuerboard | `observes` | Systemkatalog | `stable` | `—` | `—` | `—` | `—` | Steuerboard can provide read-only repo-state signals, not decisions. |
| Systemkatalog | `owns` | Ecosystem Map v0 | `stable` | `—` | `—` | `—` | `—` | Systemkatalog owns the map semantics during v0. |
| Systemkatalog | `provides` | Leitstand | `stable` | `asynchronous-durable` | `degrade` | `from-to` | `—` | Systemkatalog provides map artifacts for Leitstand display. |
| Vault Gewebe | `scope_boundary` | Systemkatalog | `related` | `—` | `—` | `—` | `—` | Vault material may inform catalog edits but is not active catalog canon. |
| Vibe-Lab | `exports_candidate_to` | Bureau | `bounded` | `manual` | `degrade` | `from-to` | `—` | Vibe-Lab may export reviewed proposal-ready candidates; Bureau alone decides whether they become work. |
| Vibe-Lab | `provides` | Systemkatalog | `stable` | `—` | `—` | `—` | `—` | Vibe-Lab provides method experiments and evidence patterns. |
| Weltgewebe | `operates_on` | GitHub | `stable` | `synchronous-blocking` | `block` | `to-from` | `—` | Weltgewebe product work is still validated through repo, PR and CI state. |
| WGX | `provides` | CI / Checks | `stable` | `—` | `—` | `—` | `—` | WGX provides reusable Fleet checks and repository workflow mechanics. |
| CI / Checks | `provides` | Leitstand | `stable` | `observational` | `degrade` | `from-to` | `—` | Primary check state can be reflected. |
| GitHub | `provides` | Leitstand | `stable` | `observational` | `degrade` | `from-to` | `—` | Primary repo state can be reflected. |
| GitHub | `validated_by` | CI / Checks | `stable` | `synchronous-blocking` | `block` | `to-from` | `—` | Checks and review gates provide hard technical feedback. |

## Ausfalldomänen

Ausfalldomänen beschreiben stabile gemeinsame Abhängigkeiten. Sie sind keine Aussage über aktuellen Ausfall oder Gesundheit.

| ID | Art | Bedeutung |
|---|---|---|
| `control:grabowski-runtime` | `control` | Grabowski deployment, operator service, tunnel and typed execution surface. |
| `credentials:operator` | `credentials` | Operator-held credentials required for authenticated mutation or recovery. |
| `data:bureau-state` | `data` | Bureau operational SQLite state, envelopes, claims and receipts. |
| `data:chronik-store` | `data` | Chronik append-only event data and integrity metadata. |
| `data:grabowski-outbox` | `data` | Durable local outbox used when downstream event delivery is unavailable. |
| `data:weltgewebe-postgresql` | `data` | Weltgewebe relational authority stored in PostgreSQL. |
| `host:heim-pc` | `host` | The primary local operator host and its user-scoped state. |
| `host:wg-prod-1` | `host` | The current Weltgewebe production reference host or cell. |
| `human:alexander` | `human` | Human sense, approval and abort authority. |
| `identity:github` | `identity` | GitHub repository, branch, pull-request and review identity. |
| `network:public-internet` | `network` | External network reachability required for hosted services and public endpoints. |
| `provider:backup-storage` | `provider` | Backup storage and restore inputs outside the active primary data path. |
| `provider:github` | `provider` | GitHub-hosted collaboration, CI control and repository metadata. |
| `runtime:lenskit-legacy` | `runtime` | The bounded legacy Lenskit/rLens runtime retained for rollback during cutover. |
| `runtime:repoground` | `runtime` | The replacement RepoGround runtime and its serving identity. |
| `stream:weltgewebe-jetstream` | `stream` | Weltgewebe durable event and stream state in JetStream. |

## Deklarierte Recoverymodi

Ein Recoverymodus beschreibt einen zulässigen Pfad und seine gemeinsamen Fehlerursachen. Er belegt weder aktuelle Bereitschaft noch Ausführungsautorität.

| Modus | System | Art | Unabhängigkeit | Gemeinsame Ausfalldomänen | Rückkehrbedingung |
|---|---|---|---|---|---|
| `bureau-state-restore` | `repo:bureau` | `restore` | `partially-shared` | credentials:operator | Bureau validation, task and receipt integrity, claim reconciliation and a bounded operational readback all pass. |
| `chronik-durable-outbox` | `repo:grabowski` | `durable-queue` | `partially-shared` | host:heim-pc | Bounded retry succeeds, idempotency is preserved and the durable outbox is drained with a receipt. |
| `chronik-state-restore` | `repo:chronik` | `restore` | `partially-shared` | host:heim-pc | Append-only integrity, provenance, retention and bounded query readbacks pass on the restored target. |
| `grabowski-release-rollback` | `repo:grabowski` | `rollback` | `same-failure-domain` | host:heim-pc<br>credentials:operator | The previous manifest-bound release is active, healthy, audit-valid and consumer-compatible. |
| `grabowski-state-restore` | `repo:grabowski` | `restore` | `partially-shared` | credentials:operator | A clean target passes deployment, audit, recovery-gate and typed operation readbacks without secret exposure. |
| `repoground-legacy-rollback` | `repo:repoground` | `rollback` | `same-failure-domain` | host:heim-pc | The legacy runtime serves the expected identity and all bounded consumers return to their prior verified behavior. |
| `weltgewebe-jetstream-recovery` | `repo:weltgewebe` | `restore` | `partially-shared` | credentials:operator | Stream consumers, deduplication, ordering and representative end-to-end behavior pass without split brain. |
| `weltgewebe-postgresql-restore` | `repo:weltgewebe` | `restore` | `partially-shared` | credentials:operator | A clean target passes schema, integrity, representative API, authentication and domain readbacks. |

## Einstiegspunkte

| System | Einstieg |
|---|---|
| Bureau | [https://github.com/heimgewebe/bureau](https://github.com/heimgewebe/bureau) |
| GitHub | [https://github.com/heimgewebe](https://github.com/heimgewebe) |
| Grabowski | [https://github.com/heimgewebe/grabowski](https://github.com/heimgewebe/grabowski) |
| Grabowski Agent-Routing | [https://github.com/heimgewebe/grabowski/blob/main/docs/generated/operator-context.v1.json](https://github.com/heimgewebe/grabowski/blob/main/docs/generated/operator-context.v1.json) |
| Leitstand | [https://github.com/heimgewebe/leitstand](https://github.com/heimgewebe/leitstand) |
| Metarepo Fleet-Mitgliedschaft | [https://github.com/heimgewebe/metarepo/blob/main/fleet/repos.yml](https://github.com/heimgewebe/metarepo/blob/main/fleet/repos.yml) |
| RepoGround | [https://github.com/heimgewebe/repoground](https://github.com/heimgewebe/repoground) |
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
