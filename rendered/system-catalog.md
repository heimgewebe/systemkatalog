# Systemkatalog

> Automatisch erzeugte, app-unabhängige Leseansicht. Sie beschreibt stabile Rollen und verweist auf Primärquellen; sie enthält keinen Live-, Task- oder Merge-Status.

## Zweck

Der Katalog beantwortet, welche Systeme existieren, welchem Zweck sie dienen, wem welche Wahrheit gehört, welche stabilen Beziehungen bestehen und wo die Einstiegspunkte liegen.

## Systeme

| System | Typ | Lebenszyklus | Kritikalität | Ausfalldomänen | Zweck | Nicht zuständig für | Wahrheitsbesitz | Einstiegspunkte |
|---|---|---|---|---|---|---|---|---|
| Ecosystem Map v0 | artifact | `active` · geprüft 2026-07-26 | `optional` | — | machine-readable overview graph and rendered orientation map | claim truth<br>runtime health<br>merge readiness | — | `artifact`: [rendered/ecosystem-registry-map.mmd](../rendered/ecosystem-registry-map.mmd) |
| GewebeZell-Betreiberrolle | concept | `active` · geprüft 2026-08-01 | `supporting` | — | local responsibility for cell infrastructure, moderation, rules, data boundaries and explicitly allowed federation relationships | canonical truth of foreign cells<br>global ecosystem governance<br>authority derived only from technical reachability<br>Bureau task state or Grabowski execution authorization | — | `architecture`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/architecture/weltgewebe-os.md](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/architecture/weltgewebe-os.md)<br>`incidentResponse`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/runbooks/incident-response.md](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/runbooks/incident-response.md)<br>`operatorRunbook`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/runbook.md](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/runbook.md) |
| GewebeZelle | concept | `active` · geprüft 2026-08-01 | `supporting` | — | autonomous operational and social domain with local data sovereignty, moderation, rules, infrastructure boundaries and explicit federation relationships | global multi-primary truth<br>canonical state of foreign cells<br>implicit sharing of private data<br>claims about a cell runtime without primary-source observation | weltgewebe_cell_domain_truth | `architecture`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/architecture/weltgewebe-os.md](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/architecture/weltgewebe-os.md)<br>`cellDescriptor`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/contracts/federation/v1/cell-descriptor.schema.json](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/contracts/federation/v1/cell-descriptor.schema.json)<br>`federationDecision`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/adr/ADR-0011__foederierte-gewebezellen.md](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/adr/ADR-0011__foederierte-gewebezellen.md) |
| Weltgewebe OS | concept | `active` · geprüft 2026-08-01 | `supporting` | — | canonical target architecture for a federated, locally sovereign and globally connected societal coordination layer | device operating systems<br>claims that the current runtime already satisfies the target architecture<br>live Kubernetes, high-availability or public federation status | — | `architecture`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/architecture/weltgewebe-os.md](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/architecture/weltgewebe-os.md)<br>`foundationStatus`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/reports/weltgewebe-os-foundation-status.md](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/reports/weltgewebe-os-foundation-status.md)<br>`masterplan`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/blueprints/weltgewebe-os-masterplan.md](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/blueprints/weltgewebe-os-masterplan.md) |
| Weltgewebe-Föderationsebenen | concept | `active` · geprüft 2026-08-01 | `supporting` | — | separation of same-operator infrastructure federation, trusted-neighbour event federation and public domain federation between independent cells | global primary truth<br>unrestricted internal Kubernetes or NATS access between operators<br>claims that public cell federation is already operational | — | `architecture`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/architecture/weltgewebe-os.md](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/architecture/weltgewebe-os.md)<br>`federationDecision`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/adr/ADR-0011__foederierte-gewebezellen.md](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/adr/ADR-0011__foederierte-gewebezellen.md)<br>`wireContract`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/specs/federation-wire-v1.md](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/specs/federation-wire-v1.md) |
| Weltgewebe-Plattformziel | concept | `transition` · geprüft 2026-08-01 | `supporting` | — | Kubernetes- and GitOps-based target platform for staging and production while Compose remains a real, bounded development and recovery profile | claiming that Kubernetes production operation is already proven<br>live deployment or cluster health<br>manual runtime changes as durable desired state | — | `architecture`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/architecture/weltgewebe-os.md](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/architecture/weltgewebe-os.md)<br>`foundationStatus`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/reports/kubernetes-platform-foundation-status.md](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/reports/kubernetes-platform-foundation-status.md)<br>`platformDecision`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/adr/ADR-0010__kubernetes-kanonische-plattform.md](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/adr/ADR-0010__kubernetes-kanonische-plattform.md)<br>`recoveryProof`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/runbooks/kubernetes-ha-recovery-proof.md](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/runbooks/kubernetes-ha-recovery-proof.md) |
| Alexander | human | `active` · geprüft 2026-07-26 | `foundational` | human:alexander | meaning, approval and abort authority outside automation | automated execution<br>machine-derived repository or runtime state | — | `authorityPolicy`: [policy/system-catalog.v1.json](../policy/system-catalog.v1.json) |
| Agent Control Surface | repository | `transition` · geprüft 2026-07-26 | `unknown` | identity:github<br>provider:github | local manual control surface for Jules sessions and guarded step-by-step Git workflows | autonomous task dispatch<br>task priority<br>merge authorization<br>remote access security | — | `readme`: [https://github.com/heimgewebe/agent-control-surface/blob/main/README.md](https://github.com/heimgewebe/agent-control-surface/blob/main/README.md)<br>`repository`: [https://github.com/heimgewebe/agent-control-surface](https://github.com/heimgewebe/agent-control-surface)<br>`runbook`: [https://github.com/heimgewebe/agent-control-surface/blob/main/RUNBOOK.md](https://github.com/heimgewebe/agent-control-surface/blob/main/RUNBOOK.md) |
| Alpha Lab | repository | `active` · geprüft 2026-08-07 | `optional` | identity:github<br>provider:github | read-only research tool for reproducible point-in-time analysis of public filings and deterministic shadow evaluation | production execution<br>task state<br>ecosystem semantics<br>claims of proven research outcomes | — | `repository`: [https://github.com/heimgewebe/alpha-lab](https://github.com/heimgewebe/alpha-lab) |
| audio | repository | `active` · geprüft 2026-08-01 | `supporting` | host:heim-pc<br>identity:github<br>provider:github | Canonical Heim-PC audio configuration, recording, playback, instruments and experimental music systems | live hardware presence without current observation<br>runtime audio health without live checks<br>task authority<br>merge approval | — | `readme`: [https://github.com/heimgewebe/audio/blob/404736337ec315eb0af556b412c68136e49c1159/README.md](https://github.com/heimgewebe/audio/blob/404736337ec315eb0af556b412c68136e49c1159/README.md)<br>`repository`: [https://github.com/heimgewebe/audio](https://github.com/heimgewebe/audio) |
| Außensensor | repository | `active` · geprüft 2026-07-26 | `unknown` | identity:github<br>provider:github | Curated external signals and event feeds for Chronik | task authority<br>canonical event history<br>merge approval | — | `repository`: [https://github.com/heimgewebe/aussensensor](https://github.com/heimgewebe/aussensensor) |
| Bureau | repository | `active` · geprüft 2026-07-26 | `foundational` | host:heim-pc<br>data:bureau-state<br>identity:github<br>credentials:operator<br>provider:backup-storage | task cadence, delegation, run reporting | runtime execution<br>Git and review truth<br>ecosystem semantics | tasks_claims_completion | `repository`: [https://github.com/heimgewebe/bureau](https://github.com/heimgewebe/bureau) |
| Chronik | repository | `active` · geprüft 2026-07-26 | `supporting` | host:heim-pc<br>data:chronik-store<br>provider:backup-storage | append-only event ledger and historical evidence axis | task state<br>policy decisions<br>runtime mutation | append_only_history | `repository`: [https://github.com/heimgewebe/chronik](https://github.com/heimgewebe/chronik) |
| Commonworld | repository | `active` · geprüft 2026-08-01 | `unknown` | identity:github<br>provider:github | Interactive globe and evidence-bound catalog and admission rules for physical, digital, local and global commons | ecosystem governance<br>universal commons authority outside the published Commonworld admission contract<br>task state<br>merge authority | commonworld_commons_admission | `repository`: [https://github.com/heimgewebe/commonworld](https://github.com/heimgewebe/commonworld) |
| Contracts Mirror | repository | `active` · geprüft 2026-07-26 | `unknown` | identity:github<br>provider:github | Validated mirror and publication surface for canonical Metarepo contracts | canonical contract authorship<br>runtime status<br>task authority | — | `repository`: [https://github.com/heimgewebe/contracts-mirror](https://github.com/heimgewebe/contracts-mirror) |
| Device Graph | repository | `active` · geprüft 2026-07-26 | `unknown` | identity:github<br>provider:github | infrastructure device graph; adjacent but not ecosystem-governance canon | ecosystem governance canon<br>task state<br>merge authority | — | `repository`: [https://github.com/heimgewebe/device-graph](https://github.com/heimgewebe/device-graph) |
| Grabowski | repository | `active` · geprüft 2026-07-26 | `foundational` | host:heim-pc<br>control:grabowski-runtime<br>credentials:operator<br>network:public-internet<br>provider:backup-storage<br>data:grabowski-outbox | operator execution, repo work, review gates | task priority<br>ecosystem semantics<br>primary Git or runtime truth | agent_routing<br>local_fleet_execution | `repository`: [https://github.com/heimgewebe/grabowski](https://github.com/heimgewebe/grabowski) |
| HausKI | repository | `active` · geprüft 2026-07-26 | `unknown` | identity:github<br>provider:github | Local offline-first AI orchestration and policy-controlled memory | fleet task authority<br>ecosystem catalog semantics<br>merge approval | — | `repository`: [https://github.com/heimgewebe/hausKI](https://github.com/heimgewebe/hausKI) |
| HausKI Audio | repository | `retired` · geprüft 2026-07-28 | `optional` | identity:github<br>provider:github | Retired historical donor and provenance reference for the canonical heimgewebe/audio repository | current audio product truth<br>runtime audio configuration<br>new maintenance work<br>task authority<br>merge approval | — | `repository`: [https://github.com/heimgewebe/hausKI-audio](https://github.com/heimgewebe/hausKI-audio) |
| heim-pc | repository | `active` · geprüft 2026-07-26 | `unknown` | identity:github<br>provider:github | Versioned local operator entry and host orientation | fleet task authority<br>service runtime truth<br>ecosystem semantics | — | `repository`: [https://github.com/heimgewebe/heim-pc](https://github.com/heimgewebe/heim-pc) |
| Heimgeist | repository | `transition` · geprüft 2026-07-26 | `unknown` | identity:github<br>provider:github | System self-reflection and meta-agent experimentation | production authority<br>task state<br>merge approval | — | `repository`: [https://github.com/heimgewebe/heimgeist](https://github.com/heimgewebe/heimgeist) |
| heimlern | repository | `archived` · geprüft 2026-07-26 | `optional` | provider:github | archived historical reference for the former offline operator-learning implementation | active learning proposals<br>runtime operation<br>automatic policy application<br>task dispatch<br>merge authorization<br>active contract authority<br>new feature development without a separately registered experiment | — | `repository`: [https://github.com/heimgewebe/heimlern](https://github.com/heimgewebe/heimlern) |
| Heimserver | repository | `retired` · geprüft 2026-08-01 | `unknown` | identity:github<br>provider:github | retired historical operations and contract reference for the former home-network service layer, edge gateway, DDNS and Weltgewebe infrastructure | runtime health claims without live checks<br>task state<br>ecosystem semantics<br>secret storage in Git | — | `agentEntry`: [https://github.com/heimgewebe/heimserver/blob/main/AGENTS.md](https://github.com/heimgewebe/heimserver/blob/main/AGENTS.md)<br>`readme`: [https://github.com/heimgewebe/heimserver/blob/main/README.md](https://github.com/heimgewebe/heimserver/blob/main/README.md)<br>`repository`: [https://github.com/heimgewebe/heimserver](https://github.com/heimgewebe/heimserver)<br>`systemMap`: [https://github.com/heimgewebe/heimserver/blob/main/SYSTEM_MAP.md](https://github.com/heimgewebe/heimserver/blob/main/SYSTEM_MAP.md) |
| Infra | repository | `active` · geprüft 2026-07-26 | `unknown` | identity:github<br>provider:github | host, network, cockpit and operational runbooks | task state<br>ecosystem semantics<br>product-domain truth | — | `repository`: [https://github.com/heimgewebe/infra](https://github.com/heimgewebe/infra) |
| Konvergenzregelkreis | repository | `active` · geprüft 2026-07-26 | `essential` | identity:github<br>provider:github | public stateless convergence protocol and conformance core for evidence-bound closure of ecosystem changes | task state<br>queue or claims<br>execution, leases or recovery<br>merge authorization<br>deployment state or runtime health<br>ecosystem semantics<br>fleet membership<br>event history<br>product telemetry | convergence_protocol | `agentEntry`: [https://github.com/heimgewebe/konvergenzregelkreis/blob/main/AGENTS.md](https://github.com/heimgewebe/konvergenzregelkreis/blob/main/AGENTS.md)<br>`profiles`: [https://github.com/heimgewebe/konvergenzregelkreis/tree/main/profiles](https://github.com/heimgewebe/konvergenzregelkreis/tree/main/profiles)<br>`protocol`: [https://github.com/heimgewebe/konvergenzregelkreis/tree/main/protocol](https://github.com/heimgewebe/konvergenzregelkreis/tree/main/protocol)<br>`readme`: [https://github.com/heimgewebe/konvergenzregelkreis/blob/main/README.md](https://github.com/heimgewebe/konvergenzregelkreis/blob/main/README.md)<br>`repository`: [https://github.com/heimgewebe/konvergenzregelkreis](https://github.com/heimgewebe/konvergenzregelkreis)<br>`roleBoundary`: [https://github.com/heimgewebe/konvergenzregelkreis/blob/main/system/regelkreis-role.v1.json](https://github.com/heimgewebe/konvergenzregelkreis/blob/main/system/regelkreis-role.v1.json) |
| Leitstand | repository | `active` · geprüft 2026-08-01 | `supporting` | identity:github<br>provider:github | read-only ecosystem observability and status projection | canonical truth ownership<br>task authorization<br>runtime mutation | general_operator_display | `repository`: [https://github.com/heimgewebe/leitstand](https://github.com/heimgewebe/leitstand) |
| Leitwerk | repository | `archived` · geprüft 2026-07-29 | `optional` | provider:github | archived historical reference for the former pre-Bureau and pre-Grabowski coordination model | active contract or policy authority<br>current task or claim state<br>runtime execution<br>merge authorization<br>agent dispatch<br>new feature development | — | `archiveEvidence`: [https://github.com/heimgewebe/leitwerk/blob/1449145af543b78c0d3813942f1d6d95ddb33c4a/ARCHIVE.md](https://github.com/heimgewebe/leitwerk/blob/1449145af543b78c0d3813942f1d6d95ddb33c4a/ARCHIVE.md)<br>`readme`: [https://github.com/heimgewebe/leitwerk/blob/1449145af543b78c0d3813942f1d6d95ddb33c4a/README.md](https://github.com/heimgewebe/leitwerk/blob/1449145af543b78c0d3813942f1d6d95ddb33c4a/README.md)<br>`repository`: [https://github.com/heimgewebe/leitwerk](https://github.com/heimgewebe/leitwerk) |
| Metarepo | repository | `active` · geprüft 2026-08-01 | `essential` | identity:github<br>provider:github | Fleet membership, canonical shared contracts and repository templates | repository purpose semantics<br>runtime health<br>task state | fleet_membership | `repository`: [https://github.com/heimgewebe/metarepo](https://github.com/heimgewebe/metarepo) |
| Mitschreiber | repository | `active` · geprüft 2026-07-26 | `unknown` | identity:github<br>provider:github | Privacy-first on-device context capture and redacted event production | task authority<br>ecosystem semantics<br>merge approval | — | `repository`: [https://github.com/heimgewebe/mitschreiber](https://github.com/heimgewebe/mitschreiber) |
| Obsidian Bridge | repository | `active` · geprüft 2026-07-26 | `unknown` | identity:github<br>provider:github | deterministic CLI and artifact bridge for using Obsidian as a projection and observatory interface | vault content truth<br>personal notes<br>task state<br>ecosystem semantics | — | `contracts`: [https://github.com/heimgewebe/obsidian-bridge/tree/main/contracts](https://github.com/heimgewebe/obsidian-bridge/tree/main/contracts)<br>`readme`: [https://github.com/heimgewebe/obsidian-bridge/blob/main/README.md](https://github.com/heimgewebe/obsidian-bridge/blob/main/README.md)<br>`repository`: [https://github.com/heimgewebe/obsidian-bridge](https://github.com/heimgewebe/obsidian-bridge) |
| Plexer | repository | `active` · geprüft 2026-07-26 | `unknown` | identity:github<br>provider:github | bounded event delivery and queueing gateway | task prioritization<br>canonical history<br>ecosystem semantics | — | `repository`: [https://github.com/heimgewebe/plexer](https://github.com/heimgewebe/plexer) |
| RepoGround | repository | `active` · geprüft 2026-08-03 | `supporting` | host:heim-pc<br>runtime:repoground | verifiable, citable repository context for humans and AI systems under one canonical RepoGround product identity | repository operational state<br>task priority<br>merge authorization<br>parallel product identities or active aliases for superseded names | repository_context_citations | `architecture`: [https://github.com/heimgewebe/repoground/blob/5548ca2d23a3d22ffe14fb1006363e4078e7c009/docs/architecture/repoground.md](https://github.com/heimgewebe/repoground/blob/5548ca2d23a3d22ffe14fb1006363e4078e7c009/docs/architecture/repoground.md)<br>`compatibilityExit`: [https://github.com/heimgewebe/repoground/blob/5548ca2d23a3d22ffe14fb1006363e4078e7c009/docs/contracts/repoground-compatibility-exit.v1.json](https://github.com/heimgewebe/repoground/blob/5548ca2d23a3d22ffe14fb1006363e4078e7c009/docs/contracts/repoground-compatibility-exit.v1.json)<br>`mcpServer`: [https://github.com/heimgewebe/repoground/blob/5548ca2d23a3d22ffe14fb1006363e4078e7c009/docs/usage/repoground-mcp-stdio.md](https://github.com/heimgewebe/repoground/blob/5548ca2d23a3d22ffe14fb1006363e4078e7c009/docs/usage/repoground-mcp-stdio.md)<br>`namingHardCut`: [https://github.com/heimgewebe/repoground/blob/5548ca2d23a3d22ffe14fb1006363e4078e7c009/docs/contracts/repoground-naming-hard-cut.v1.json](https://github.com/heimgewebe/repoground/blob/5548ca2d23a3d22ffe14fb1006363e4078e7c009/docs/contracts/repoground-naming-hard-cut.v1.json)<br>`repository`: [https://github.com/heimgewebe/repoground](https://github.com/heimgewebe/repoground) |
| Reposkop | repository | `active` · geprüft 2026-08-01 | `unknown` | identity:github<br>provider:github | canonical local checkout identity, transition and continuity truth for explicitly selected repository targets | task authorization<br>pull request or merge truth<br>remote repository freshness<br>runtime mutation<br>effect authorization | repository_checkout_identity_continuity | `readme`: [https://github.com/heimgewebe/reposkop/blob/6c0847c2cbc6ee1d1cff52fc1b4a1c5ee17af487/README.md](https://github.com/heimgewebe/reposkop/blob/6c0847c2cbc6ee1d1cff52fc1b4a1c5ee17af487/README.md)<br>`repository`: [https://github.com/heimgewebe/reposkop](https://github.com/heimgewebe/reposkop) |
| Schauwerk | repository | `active` · geprüft 2026-07-26 | `optional` | identity:github<br>provider:github | visual surface and projection layer | canonical ecosystem semantics<br>task state<br>execution authority | specialized_visual_rendering | `repository`: [https://github.com/heimgewebe/schauwerk](https://github.com/heimgewebe/schauwerk) |
| semantAH | repository | `active` · geprüft 2026-07-26 | `unknown` | identity:github<br>provider:github | Semantic index, embeddings and knowledge-graph pipeline | task authority<br>canonical event history<br>runtime health | — | `repository`: [https://github.com/heimgewebe/semantAH](https://github.com/heimgewebe/semantAH) |
| Sichter | repository | `active` · geprüft 2026-07-26 | `unknown` | identity:github<br>provider:github | Code-review and pull-request automation prototype | merge authority<br>task priority<br>runtime truth | — | `repository`: [https://github.com/heimgewebe/sichter](https://github.com/heimgewebe/sichter) |
| Snippet Engine Control | repository | `active` · geprüft 2026-07-26 | `unknown` | identity:github<br>provider:github | engine-neutral contract, diagnostics and diffable export-planning layer for text-expansion systems | the text-expansion runtime itself<br>automatic writes without explicit apply<br>task state<br>ecosystem semantics | — | `contracts`: [https://github.com/heimgewebe/snippet-engine-control/tree/main/contracts](https://github.com/heimgewebe/snippet-engine-control/tree/main/contracts)<br>`readme`: [https://github.com/heimgewebe/snippet-engine-control/blob/main/README.md](https://github.com/heimgewebe/snippet-engine-control/blob/main/README.md)<br>`repository`: [https://github.com/heimgewebe/snippet-engine-control](https://github.com/heimgewebe/snippet-engine-control) |
| Systemkatalog | repository | `active` · geprüft 2026-08-01 | `essential` | identity:github<br>provider:github | app-independent catalog for system purposes, truth ownership, stable relations and entrypoints | task priority or status<br>runtime health<br>merge readiness<br>agent dispatch | ecosystem_semantics | `agentEntry`: [AGENTS.md](../AGENTS.md)<br>`readme`: [README.md](../README.md)<br>`repository`: [https://github.com/heimgewebe/systemkatalog](https://github.com/heimgewebe/systemkatalog) |
| Vault Gewebe | repository | `active` · geprüft 2026-07-26 | `unknown` | identity:github<br>provider:github | Versioned shared knowledge vault and design source material | task status<br>runtime truth<br>merge authority | — | `repository`: [https://github.com/heimgewebe/vault-gewebe](https://github.com/heimgewebe/vault-gewebe) |
| Vibe-Lab | repository | `active` · geprüft 2026-07-26 | `optional` | identity:github<br>provider:github | bounded prospective experiments, evidence review and proposal-ready learning candidates | production authority<br>task status<br>automatic policy or routing application<br>append-only historical truth | bounded_experiments<br>reviewed_learning_proposals | `repository`: [https://github.com/heimgewebe/vibe-lab](https://github.com/heimgewebe/vibe-lab) |
| Weltgewebe | repository | `active` · geprüft 2026-08-01 | `essential` | host:wg-prod-1<br>data:weltgewebe-postgresql<br>stream:weltgewebe-jetstream<br>network:public-internet<br>credentials:operator<br>provider:backup-storage | federated map and coordination system implementing the Weltgewebe OS product and domain core | ecosystem governance<br>fleet task orchestration<br>global multi-primary domain truth<br>claims about live Kubernetes, high-availability or public federation readiness | weltgewebe_target_architecture | `federationContract`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/contracts/federation/v1](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/contracts/federation/v1)<br>`foundationStatus`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/reports/weltgewebe-os-foundation-status.md](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/reports/weltgewebe-os-foundation-status.md)<br>`operatorRunbook`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/runbook.md](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/runbook.md)<br>`recoveryRunbook`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/runbooks/kubernetes-ha-recovery-proof.md](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/docs/runbooks/kubernetes-ha-recovery-proof.md)<br>`repository`: [https://github.com/heimgewebe/weltgewebe](https://github.com/heimgewebe/weltgewebe)<br>`targetArchitecture`: [https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/architecture/weltgewebe-os.md](https://github.com/heimgewebe/weltgewebe/blob/322655285b520d04363e48487ae64d57264de573/architecture/weltgewebe-os.md) |
| WGX | repository | `active` · geprüft 2026-08-01 | `unknown` | identity:github<br>provider:github | Repository verification adapter and reusable CI frontdoor router | repository purpose semantics<br>task coordination or priority<br>host, process or deployment effects<br>runtime or Fleet health | shared_fleet_ci_checks | `repository`: [https://github.com/heimgewebe/wgx](https://github.com/heimgewebe/wgx) |
| CI / Checks | service | `active` · geprüft 2026-07-26 | `supporting` | provider:github<br>network:public-internet | automated tests, lint, gates and review signals | merge authorization<br>runtime health<br>task priority | technical_check_results | `checks`: [https://github.com/heimgewebe](https://github.com/heimgewebe) |
| GitHub | service | `active` · geprüft 2026-07-26 | `foundational` | provider:github<br>network:public-internet<br>credentials:operator | repository, PR, issue and review state | local runtime health<br>task priority<br>ecosystem semantics | branches_prs_reviews | `organization`: [https://github.com/heimgewebe](https://github.com/heimgewebe) |

## Repository-Abdeckung

Metarepo ist Primärquelle für die Fleet-Mitgliedschaft. Der Systemkatalog bleibt Primärquelle für Zweck, Beziehungen, Wahrheitszuständigkeiten und Einstiegspunkte.

| System | Repository | Einordnung | Einstieg |
|---|---|---|---|
| Agent Control Surface | `heimgewebe/agent-control-surface` | `catalog-only` | [https://github.com/heimgewebe/agent-control-surface](https://github.com/heimgewebe/agent-control-surface) |
| Alpha Lab | `heimgewebe/alpha-lab` | `catalog-only` | [https://github.com/heimgewebe/alpha-lab](https://github.com/heimgewebe/alpha-lab) |
| audio | `heimgewebe/audio` | `fleet` | [https://github.com/heimgewebe/audio](https://github.com/heimgewebe/audio) |
| Außensensor | `heimgewebe/aussensensor` | `fleet` | [https://github.com/heimgewebe/aussensensor](https://github.com/heimgewebe/aussensensor) |
| Bureau | `heimgewebe/bureau` | `catalog-only` | [https://github.com/heimgewebe/bureau](https://github.com/heimgewebe/bureau) |
| Chronik | `heimgewebe/chronik` | `fleet` | [https://github.com/heimgewebe/chronik](https://github.com/heimgewebe/chronik) |
| Commonworld | `heimgewebe/commonworld` | `catalog-only` | [https://github.com/heimgewebe/commonworld](https://github.com/heimgewebe/commonworld) |
| Contracts Mirror | `heimgewebe/contracts-mirror` | `fleet` | [https://github.com/heimgewebe/contracts-mirror](https://github.com/heimgewebe/contracts-mirror) |
| Device Graph | `heimgewebe/device-graph` | `catalog-only` | [https://github.com/heimgewebe/device-graph](https://github.com/heimgewebe/device-graph) |
| Grabowski | `heimgewebe/grabowski` | `catalog-only` | [https://github.com/heimgewebe/grabowski](https://github.com/heimgewebe/grabowski) |
| HausKI | `heimgewebe/hausKI` | `fleet` | [https://github.com/heimgewebe/hausKI](https://github.com/heimgewebe/hausKI) |
| HausKI Audio | `heimgewebe/hausKI-audio` | `catalog-only` | [https://github.com/heimgewebe/hausKI-audio](https://github.com/heimgewebe/hausKI-audio) |
| heim-pc | `heimgewebe/heim-pc` | `fleet` | [https://github.com/heimgewebe/heim-pc](https://github.com/heimgewebe/heim-pc) |
| Heimgeist | `heimgewebe/heimgeist` | `fleet` | [https://github.com/heimgewebe/heimgeist](https://github.com/heimgewebe/heimgeist) |
| heimlern | `heimgewebe/heimlern` | `archived-reference` | [https://github.com/heimgewebe/heimlern](https://github.com/heimgewebe/heimlern) |
| Heimserver | `heimgewebe/heimserver` | `catalog-only` | [https://github.com/heimgewebe/heimserver](https://github.com/heimgewebe/heimserver) |
| Infra | `heimgewebe/infra` | `catalog-only` | [https://github.com/heimgewebe/infra](https://github.com/heimgewebe/infra) |
| Konvergenzregelkreis | `heimgewebe/konvergenzregelkreis` | `fleet` | [https://github.com/heimgewebe/konvergenzregelkreis](https://github.com/heimgewebe/konvergenzregelkreis) |
| Leitstand | `heimgewebe/leitstand` | `fleet` | [https://github.com/heimgewebe/leitstand](https://github.com/heimgewebe/leitstand) |
| Leitwerk | `heimgewebe/leitwerk` | `archived-reference` | [https://github.com/heimgewebe/leitwerk](https://github.com/heimgewebe/leitwerk) |
| Metarepo | `heimgewebe/metarepo` | `fleet` | [https://github.com/heimgewebe/metarepo](https://github.com/heimgewebe/metarepo) |
| Mitschreiber | `heimgewebe/mitschreiber` | `fleet` | [https://github.com/heimgewebe/mitschreiber](https://github.com/heimgewebe/mitschreiber) |
| Obsidian Bridge | `heimgewebe/obsidian-bridge` | `catalog-only` | [https://github.com/heimgewebe/obsidian-bridge](https://github.com/heimgewebe/obsidian-bridge) |
| Plexer | `heimgewebe/plexer` | `fleet` | [https://github.com/heimgewebe/plexer](https://github.com/heimgewebe/plexer) |
| RepoGround | `heimgewebe/repoground` | `fleet` | [https://github.com/heimgewebe/repoground](https://github.com/heimgewebe/repoground) |
| Reposkop | `heimgewebe/reposkop` | `catalog-only` | [https://github.com/heimgewebe/reposkop](https://github.com/heimgewebe/reposkop) |
| Schauwerk | `heimgewebe/schauwerk` | `catalog-only` | [https://github.com/heimgewebe/schauwerk](https://github.com/heimgewebe/schauwerk) |
| semantAH | `heimgewebe/semantAH` | `fleet` | [https://github.com/heimgewebe/semantAH](https://github.com/heimgewebe/semantAH) |
| Sichter | `heimgewebe/sichter` | `fleet` | [https://github.com/heimgewebe/sichter](https://github.com/heimgewebe/sichter) |
| Snippet Engine Control | `heimgewebe/snippet-engine-control` | `catalog-only` | [https://github.com/heimgewebe/snippet-engine-control](https://github.com/heimgewebe/snippet-engine-control) |
| Systemkatalog | `heimgewebe/systemkatalog` | `catalog-only` | [https://github.com/heimgewebe/systemkatalog](https://github.com/heimgewebe/systemkatalog) |
| Vault Gewebe | `heimgewebe/vault-gewebe` | `fleet` | [https://github.com/heimgewebe/vault-gewebe](https://github.com/heimgewebe/vault-gewebe) |
| Vibe-Lab | `heimgewebe/vibe-lab` | `catalog-only` | [https://github.com/heimgewebe/vibe-lab](https://github.com/heimgewebe/vibe-lab) |
| Weltgewebe | `heimgewebe/weltgewebe` | `related` | [https://github.com/heimgewebe/weltgewebe](https://github.com/heimgewebe/weltgewebe) |
| WGX | `heimgewebe/wgx` | `fleet` | [https://github.com/heimgewebe/wgx](https://github.com/heimgewebe/wgx) |

Explizit ohne aktive Fleet-Mitgliedschaft:

- `hausKI-audio` — Historical donor repository explicitly marked status: related and fleet: false in the bound Metarepo source; current audio product truth belongs to heimgewebe/audio.
- `heimlern` — Archived historical reference explicitly marked status: archived-reference and fleet: false in the bound Metarepo source.
- `leitwerk` — Archived historical reference explicitly marked status: archived-reference and fleet: false in the bound Metarepo source.
- `vault-privat` — Private related repository explicitly marked fleet: false in Metarepo.

## Organisationsumfang

Der GitHub-Snapshot umfasst 37 nicht geforkte Repositories. Davon sind 33 aktive Katalogsysteme, 2 archivierte Referenzen und 2 begründet ausgeschlossen.

Archivierte Referenzen ohne aktive Betriebsautorität:

- `heimgewebe/heimlern` (`public`) — archived historical reference for retired offline learning and proposal experiments; no active runtime or contract authority
- `heimgewebe/leitwerk` (`public`) — archived historical reference for the retired Leitwerk coordination model; no active runtime, task, policy or contract authority

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
| `commonworld_commons_admission` | `commonworld` | — |
| `convergence_protocol` | `konvergenzregelkreis` | — |
| `ecosystem_semantics` | `systemkatalog` | leitstand, schauwerk |
| `fleet_membership` | `metarepo` | systemkatalog |
| `general_operator_display` | `leitstand` | — |
| `live_service_state` | `runtime` | leitstand |
| `local_fleet_execution` | `grabowski` | leitstand |
| `repository_checkout_identity_continuity` | `reposkop` | grabowski, leitstand |
| `repository_context_citations` | `repoground` | repoground, systemkatalog |
| `reviewed_learning_proposals` | `vibe_lab` | bureau, systemkatalog |
| `shared_fleet_ci_checks` | `wgx` | github_ci |
| `specialized_visual_rendering` | `schauwerk` | — |
| `tasks_claims_completion` | `bureau` | leitstand |
| `technical_check_results` | `ci` | github, leitstand |
| `weltgewebe_cell_domain_truth` | `gewebezelle` | weltgewebe |
| `weltgewebe_target_architecture` | `weltgewebe` | systemkatalog |

## Stabile Beziehungen

Nur Beziehungen der Klassen `stable`, `bounded` oder `related` werden angezeigt. Die Klasse beschreibt die Dauerhaftigkeit der Architekturbeziehung, nicht ihren aktuellen Betriebszustand. Resilienzfelder erscheinen nur für fachlich geprüfte, ausfall- oder autoritätsrelevante Kanten; `—` bedeutet nicht geprüft, nicht automatisch harmlos.

| Von | Beziehung | Zu | Klasse | Kopplung | Ausfallpolitik | Autoritätsrichtung | Recovery | Bedeutung |
|---|---|---|---|---|---|---|---|---|
| Alexander | `steers` | Systemkatalog | `stable` | `manual` | `block` | `from-to` | `—` | Human sense, priority, approval and abort authority stay outside automation. |
| GewebeZelle | `operates_on` | Weltgewebe-Föderationsebenen | `bounded` | `—` | `—` | `—` | `—` | Each cell chooses explicit federation relationships, event classes, visibility and blocking rules. |
| GewebeZell-Betreiberrolle | `operates_on` | GewebeZelle | `stable` | `—` | `—` | `—` | `—` | A cell operator governs one cell boundary and does not acquire authority over foreign cell truth. |
| Weltgewebe OS | `provides` | GewebeZelle | `stable` | `—` | `—` | `—` | `—` | Weltgewebe OS defines autonomous cells as the unit of local truth, moderation, infrastructure boundaries and federation policy. |
| Weltgewebe OS | `provides` | Weltgewebe-Föderationsebenen | `stable` | `—` | `—` | `—` | `—` | Weltgewebe OS keeps infrastructure, event and public domain federation as separate connection planes. |
| Weltgewebe OS | `provides` | Weltgewebe-Plattformziel | `stable` | `—` | `—` | `—` | `—` | Weltgewebe OS defines Kubernetes and GitOps as the target platform without claiming current production readiness. |
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
| Grabowski | `operates_on` | Weltgewebe-Plattformziel | `bounded` | `—` | `—` | `—` | `—` | Grabowski may execute scoped platform changes only through explicit authority, evidence and rollback boundaries. |
| Grabowski | `operates_on` | GitHub | `stable` | `synchronous-blocking` | `block` | `to-from` | `—` | PRs, branches, issues and reviews remain GitHub-owned state. |
| HausKI Audio | `provides` | audio | `related` | `—` | `—` | `—` | `—` | HausKI Audio is retained only as a reviewed historical donor and provenance source for the canonical audio repository. |
| heim-pc | `observes` | Ecosystem Map v0 | `stable` | `—` | `—` | `—` | `—` | The local operator entry points to the canonical ecosystem map without duplicating it. |
| Heimgeist | `observes` | Ecosystem Map v0 | `related` | `—` | `—` | `—` | `—` | Heimgeist may inspect catalog projections for reflection but does not own catalog truth. |
| Heimserver | `scope_boundary` | Infra | `related` | `—` | `—` | `—` | `—` | Heimserver retains the private service-layer and edge contracts; Infra remains the broader host and network runbook surface. |
| Konvergenzregelkreis | `scope_boundary` | Bureau | `stable` | `manual` | `block` | `none` | `—` | Konvergenzregelkreis assesses submitted evidence; Bureau remains the sole owner of tasks, claims and completion. |
| Leitstand | `observes` | Ecosystem Map v0 | `stable` | `—` | `—` | `—` | `—` | Leitstand observes the map as orientation, not truth. |
| Leitwerk | `scope_boundary` | Bureau | `related` | `—` | `—` | `—` | `—` | Archived Leitwerk documents predate Bureau; Bureau owns current task, claim and completion truth and inherits no Leitwerk authority. |
| Leitwerk | `scope_boundary` | Konvergenzregelkreis | `related` | `—` | `—` | `—` | `—` | Archived Leitwerk is historical provenance only; Konvergenzregelkreis is an independent protocol and inherits no Leitwerk authority. |
| Metarepo | `provides` | Contracts Mirror | `stable` | `—` | `—` | `—` | `—` | Canonical contracts originate in Metarepo and are mirrored for validation and publication. |
| Metarepo | `provides` | Systemkatalog | `stable` | `asynchronous-durable` | `block` | `from-to` | `—` | Metarepo provides Fleet membership; Systemkatalog remains authority for purpose, relations and entrypoints. |
| Mitschreiber | `emits_to` | Chronik | `stable` | `—` | `—` | `—` | `—` | Redacted on-device context events are emitted to Chronik. |
| Mitschreiber | `provides` | semantAH | `bounded` | `—` | `—` | `—` | `—` | Redacted embeddings and context signals can feed semantic indexing without raw-text authority. |
| Obsidian Bridge | `provides` | Vault Gewebe | `bounded` | `—` | `—` | `—` | `—` | Obsidian Bridge projects machine artifacts into the vault interface without owning vault content. |
| Plexer | `delivers_to` | Chronik | `stable` | `asynchronous-durable` | `queue` | `from-to` | `—` | Plexer delivers bounded operational events to Chronik agent.ledger when configured. |
| RepoGround | `provides` | Systemkatalog | `stable` | `—` | `—` | `—` | `—` | RepoGround provides Systemkatalog with verifiable, citable codebase context. |
| Reposkop | `observes` | Systemkatalog | `stable` | `—` | `—` | `—` | `—` | Reposkop provides canonical, target-bound local checkout identity, transition and continuity truth for Systemkatalog checkouts, but no effect authority. |
| Schauwerk | `renders` | Ecosystem Map v0 | `stable` | `observational` | `degrade` | `to-from` | `—` | Schauwerk may render map views without owning the map canon. |
| semantAH | `provides` | HausKI | `stable` | `—` | `—` | `—` | `—` | semantAH provides the semantic memory and knowledge-graph layer used by HausKI. |
| Sichter | `operates_on` | GitHub | `bounded` | `—` | `—` | `—` | `—` | Sichter reviews repository changes and may prepare pull requests within policy boundaries. |
| Snippet Engine Control | `provides` | heim-pc | `bounded` | `—` | `—` | `—` | `—` | Snippet Engine Control provides contract-first diagnostics and export planning for the local interaction layer. |
| Systemkatalog | `owns` | Ecosystem Map v0 | `stable` | `—` | `—` | `—` | `—` | Systemkatalog owns the map semantics during v0. |
| Systemkatalog | `provides` | Leitstand | `stable` | `asynchronous-durable` | `degrade` | `from-to` | `—` | Systemkatalog provides map artifacts for Leitstand display. |
| Vault Gewebe | `scope_boundary` | Systemkatalog | `related` | `—` | `—` | `—` | `—` | Vault material may inform catalog edits but is not active catalog canon. |
| Vibe-Lab | `exports_candidate_to` | Bureau | `bounded` | `manual` | `degrade` | `from-to` | `—` | Vibe-Lab may export reviewed proposal-ready candidates; Bureau alone decides whether they become work. |
| Vibe-Lab | `provides` | Systemkatalog | `stable` | `—` | `—` | `—` | `—` | Vibe-Lab provides method experiments and evidence patterns. |
| Weltgewebe | `operates_on` | GitHub | `stable` | `synchronous-blocking` | `block` | `to-from` | `—` | Weltgewebe product work is still validated through repo, PR and CI state. |
| Weltgewebe | `provides` | Weltgewebe OS | `stable` | `—` | `—` | `—` | `—` | The Weltgewebe repository carries the normative Weltgewebe OS target architecture and its product implementation. |
| WGX | `provides` | CI / Checks | `stable` | `—` | `—` | `—` | `—` | WGX provides shared static checks and routes CI to repository-owned verification frontdoors without taking task, runtime or deployment authority. |
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
| `runtime:repoground` | `runtime` | The canonical RepoGround runtime and service identity. |
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
| `repoground-release-rollback` | `repo:repoground` | `rollback` | `same-failure-domain` | host:heim-pc | A previous verified RepoGround commit and release serve the canonical RepoGround identity and bounded consumers return to their prior verified behavior. |
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
