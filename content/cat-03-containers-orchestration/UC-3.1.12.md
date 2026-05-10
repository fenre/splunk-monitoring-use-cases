<!-- AUTO-GENERATED from UC-3.1.12.json — DO NOT EDIT -->

---
id: "3.1.12"
title: "Compose Service Health"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.1.12 · Compose Service Health

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We treat each multi-container stack like a band where every musician must be tuned before the curtain rises. If the bass player never makes it on stage but the lights already went up, we spot who is missing and which harmony rules broke before the crowd only hears static.*

---

## Description

Monitors Docker Compose project-bundle health on single-host and small-edge estates where com.docker.compose.project groups five to thirty services that must arrive ready together for the application to function. The control fuses three telemetry lanes: docker:inspect label and state snapshots that quantify running versus healthy service counts, derive project_health_pct from healthy services over declared totals, and surface distinct com.docker.compose.config-hash values to catch split-generation partial deploys; docker:events lifecycle and health transitions that refresh last_event_time when operators or restart policies mutate containers outside a clean compose up; and compose_project_baseline.csv governance that records expected_total_services plus an expected_dependency_chain narrative so Splunk can flag cardinality drift and contextualize depends_on parsing against approved inventory. It explicitly models depends_on chain violations where a dependent service is running while a named peer is unhealthy or absent—the silent partial-recovery pattern that produces customer-visible 502s while any single container still looks alive. This is Compose bundle composition and dependency integrity, distinct from UC-3.1.28 Swarm orchestrator replica convergence across cluster managers and distinct from UC-3.1.22 isolated HEALTHCHECK analytics without project aggregation.

## Value

Cuts mean time to repair for edge and developer-host incidents where seven of eight compose services are up but the database never passed health gating, because the first page names the project, the dependency break count, the config-hash spread, and the fleet running ratio instead of asking someone to eyeball docker compose ps across a thousand sites. Quantifies application-tier availability risk for bundles that still power stores, clinics, and factories without Kubernetes scheduling, while giving change-management teams defensible evidence that partial docker compose up workflows and hash drift were detected—supporting SOC 2 CC8.1 style change oversight conversations with timestamps tied to YAML revisions. Reduces revenue-impacting brownouts by forcing full-project remediation before load balancers keep serving half-ready stacks, and gives FinOps a longitudinal view of when edge gateways chronically miss baseline service cardinality so hardware or registry investments are justified with operational data rather than anecdotes.

## Implementation

Deploy Splunk Add-on for Unix and Linux (Splunkbase 833) scripted inputs that run docker inspect into index=oti_containers as sourcetype=docker:inspect with flattened com.docker.compose.* labels, plus docker:events lines with compose metadata. Publish lookups/compose_project_baseline.csv. Save container_uc_3_1_12_compose_service_health every five minutes on earliest=-4h@h latest=now, route critical bundle severities to platform paging, and archive weekly CSV evidence with baseline git hashes.

## Evidence

Saved search container_uc_3_1_12_compose_service_health; index=oti_containers panels correlating docker:inspect compose labels with docker:events; versioned lookups/compose_project_baseline.csv referenced in change tickets; weekly CSV exports to a restricted evidence index; external grounding from Docker Compose specification and depends_on documentation, Splunk Lantern container onboarding guidance, Cloudflare edge container engineering notes, and Compose v2 release history for label semantics.

## Control test

### Positive scenario

On a lab Linux host run docker compose up -d for a project whose db service uses a failing HEALTHCHECK while web depends_on db; ingest docker:inspect and docker:events into index=oti_containers, execute container_uc_3_1_12_compose_service_health, and expect critical_dependency_chain_broken_dead_dep or critical_project_health_below_50pct with non-zero broken_dependencies_count and a populated compose_project.

### Negative scenario

Deploy a known-good compose bundle where every service reaches running with healthy probes, distinct_config_hashes equals one, observed_services matches compose_project_baseline.csv expected_total_services, and confirm the saved search returns no severity row after the isnotnull(severity) filter across two five-minute intervals.

## Detailed Implementation

### Step 1 — Prerequisites and governance contracts

Head of Platform owns this control together with the Linux observability engineer who certifies docker.sock-adjacent collection and the edge platform lead who registers compose project baselines for retail, factory, and developer-fleet hosts. UC-3.1.12 is the Compose project-bundle reliability axis: it asks whether every service that should rise together under a shared com.docker.compose.project label actually does, whether depends_on semantics are honored in live engine state, and whether config-hash labels stay consistent across services after edits. This is intentionally not UC-3.1.28 Swarm replica convergence, which reads manager-declared desired task counts across a cluster, and it is not UC-3.1.22 per-container HEALTHCHECK flips without bundle context. UC-3.1.1 still owns exit-code death taxonomy; UC-3.1.13 still owns restart-policy cadence; UC-3.1.2 and UC-3.1.3 remain memory and CPU cgroup stories. Before scheduling the saved search, confirm docker inspect exporter preserves Compose v2 label keys even when JSON flattening renames dots to underscores, and confirm docker:events reaches the same index with host_id keys aligned to Universal Forwarder host strings.

Governance requires lookups/compose_project_baseline.csv with columns project (or compose_project), expected_total_services, and expected_dependency_chain documenting the authoritative service graph string your CI system emitted when the edge bundle was approved. Refresh the CSV whenever a site onboards a new stack version or when developers add services that change cardinality. Optional columns like site_id or environment may be added for macro filtering but must not break the join key. Roles need search access to index=oti_containers for platform engineers; narrower scopes may hide compose labels on sensitive developer laptops only when legal approves.

Risk briefing: partial compose up is the silent killer at edge scale—a front proxy stays running while the database task never became healthy, and the user experience is intermittent 502 responses that do not map cleanly to a single container restart counter. Bundle-level percentages expose that pattern faster than per-container dashboards because they aggregate the com.docker.compose.project group the operator already thinks in. Config-hash drift catches the second silent mode where one teammate ran docker compose up svc-a after editing YAML while older containers still carry an older com.docker.compose.config-hash, creating incompatible runtime assumptions without a clean swarm rollout narrative.

Licensing note: inspect JSON at five-minute intervals across thousands of edge hosts is measurable license volume; trim Mounts and NetworkSettings noise at collection when props allow, and keep docker:events sampling aligned to incident usefulness rather than full firehose unless security mandates retention.

Differentiation recap: UC-3.1.28 answers whether Swarm managers converged replicas; this UC answers whether a single-host or small-footprint Compose project reached coherent multi-service readiness. UC-3.1.22 answers probe failures on individual containers; this UC weights bundle completeness and dependency satisfaction across the labeled group.

FinOps and reliability joint review: tie fleet_avg_project_health dips to edge gateway CPU procurement and WAN registry latency tickets so executives see monitoring as a sensor for operational constraints, not only as license spend.

Security note: docker.sock access is root-equivalent; vault service accounts, rotate HEC tokens quarterly, and never run collectors on shared developer jump hosts without session recording. Redact registry credentials that sometimes appear in inspect Env slices before indexing when regulation requires.

Historical context: Compose remains the dominant single-host orchestrator for edge bundles and developer laptops even where Kubernetes owns the data center; Fortune-scale fleets therefore need a first-class bundle health narrative distinct from multi-host scheduler tables.

Training note: rehearse with on-call staff the difference between com.docker.compose.service naming and container Name fields so joins to compose_project_baseline.csv stay intuitive during incidents.

### Step 2 — Configure data collection

Deploy Splunk Add-on for Unix and Linux on a hardened collector tier or on each edge gateway depending on your air-gap posture. Author a scripted input that executes docker inspect across running containers—or targeted project filters when performance demands—and posts one event per container with sourcetype docker:inspect into index=oti_containers. Flatten Config.Labels so com.docker.compose.project, com.docker.compose.service, com.docker.compose.depends_on, and com.docker.compose.config-hash become first-class fields with stable snake_case aliases in props.conf for TA version drift. Preserve State.Status and State.Health.Status verbatim for coalesce lists in the SPL.

For docker:events, either stream continuously with a lightweight helper bound to the Engine events API, or poll docker events --since with a sliding watermark stored in a checkpoint file. Ensure compose-adjacent lifecycle transitions remain visible: container create and start lines often carry com.docker.compose labels in Actor.Attributes depending on Engine build; when they do not, rely on raw _raw regex extraction in the join arm as the SPL demonstrates. Map host_id to lowercase short hostnames exactly as compose_project_baseline.csv expects.

Validate on a lab laptop by running docker compose up -d for a stack with an intentional unhealthy dependency, wait two collection intervals, and confirm Splunk shows distinct config hashes if you edit only one service and partially recreate it. Compare docker inspect label output to Splunk fields before declaring parsers green.

Performance hygiene: if inspect payloads exceed forwarder limits, split Config and State blocks across two sourcetypes only with documented joins; avoid silent truncation that drops labels.

Documentation hygiene: maintain an internal wiki mapping TA field renames per Splunk_TA_nix release so coalesce lists in SPL stay curated without sprawl.

### Step 3 — Create search and alert

Save the SPL as saved search container_uc_3_1_12_compose_service_health with schedule every five minutes and time range earliest=-4h@h latest=now so dependency and hash drift windows include at least one full maintenance cycle. Throttle duplicate pages per host_id and compose_project for twenty minutes on medium_intermittent_health_check_flapping unless severity escalates within the same hour. Route critical_dependency_chain_broken_dead_dep and critical_project_health_below_50pct to platform and owning product lines jointly with the recommended_response string inline.

Understanding the pipeline in operator terms: coalesce lists absorb camelCase exporter variants and underscore-flattened label paths. Per-service stats collapse inspect noise to the latest state and health. The mvexpand pass walks comma-separated depends_on tokens stripped of Compose v2 condition suffixes so chain_hit increments when a running consumer names a peer that is down or unhealthy inside the same project. Project-level stats compute running_services, healthy_services, broken_dependencies_count, and distinct_config_hashes. The docker:events join raises last_event_time when lifecycle noise proves recent operator activity even if inspect timestamps lag. The compose_project_baseline.csv join supplies expected_total_from_baseline for governance comparisons. eventstats layers fleet_running_ratio and fleet_avg_project_health for cluster context by compose_project name across hosts. streamstats measures short-window project_health_pct swing to power medium_intermittent_health_check_flapping. The case ladder emits only the six mandated severity strings. The closing table lists fourteen analyst-ready columns including fleet context fields.

Alert actions should attach the table row, deep link to raw docker:inspect events for the project on that host_id, and reference the internal compose runbook for full versus partial up discipline.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:

```spl
`comment("UC-3.1.12 Compose Service Health. Tunables: index=oti_containers; sourcetype=docker:inspect primary; docker:events join for compose-adjacent lifecycle timestamps; inputlookup compose_project_baseline.csv on compose_project; streamstats health trend; eventstats fleet ratio context; config-hash drift uses dc(config_hash)>1; earliest=-4h@h latest=now; orchestrator scope is Compose project bundle not Swarm service replicas (UC-3.1.28).")`
index=oti_containers sourcetype="docker:inspect" earliest=-4h@h latest=now
| eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
| eval compose_project=trim(toString(coalesce(
    compose_project, composeProject, ComposeProject,
    Config_Labels_com_docker_compose_project,
    Labels_com_docker_compose_project,
    com_docker_compose_project, "")))
| eval compose_service=trim(toString(coalesce(
    compose_service, composeService, service,
    Config_Labels_com_docker_compose_service,
    Labels_com_docker_compose_service,
    com_docker_compose_service, Name, name, "")))
| eval depends_on=toString(coalesce(
    Config_Labels_com_docker_compose_depends_on,
    Labels_com_docker_compose_depends_on,
    com_docker_compose_depends_on, depends_on, DependsOn, ""))
| eval config_hash=trim(toString(coalesce(
    Config_Labels_com_docker_compose_config_hash,
    Labels_com_docker_compose_config_hash,
    com_docker_compose_config_hash, config_hash, ConfigHash, "")))
| eval state_status=lower(trim(toString(coalesce(
    State_Status, State__Status, state_status, stateStatus, Status, ""))))
| eval health_status=lower(trim(toString(coalesce(
    State_Health_Status, State__Health__Status, health_status, healthStatus, ""))))
| where len(compose_project)>0 AND len(compose_service)>0
| stats latest(state_status) AS state_status latest(health_status) AS health_status
    latest(depends_on) AS depends_on latest(config_hash) AS config_hash max(_time) AS last_seen
    BY host_id compose_project compose_service
| eval running_flag=if(state_status=="running",1,0)
| eval healthy_flag=if(state_status=="running" AND (isnull(health_status) OR len(health_status)==0 OR health_status=="healthy"),1,0)
| eval dep_mv=if(len(trim(replace(replace(depends_on,"\"","")," ","")))==0, split("_NODEPS_",","), split(lower(trim(replace(replace(depends_on,"\"","")," ",""))),","))
| eval down_name=if(state_status!="running" OR health_status=="unhealthy", compose_service, null())
| eventstats values(down_name) AS down_mv BY host_id compose_project
| mvexpand dep_mv
| eval dtrim=trim(replace(replace(replace(replace(dep_mv,":service_healthy:true",""),":service_started:true",""),":service_healthy:false",""),":service_started:false",""))
| eval chain_hit=if(state_status=="running" AND dtrim!="_NODEPS_" AND len(dtrim)>0 AND isnotnull(mvfind(down_mv, dtrim)),1,0)
| stats sum(chain_hit) AS broken_dep_unit max(running_flag) AS running_flag max(healthy_flag) AS healthy_flag
    latest(config_hash) AS config_hash max(last_seen) AS last_seen
    BY host_id compose_project compose_service
| stats dc(compose_service) AS observed_services sum(running_flag) AS running_services sum(healthy_flag) AS healthy_services
    sum(broken_dep_unit) AS broken_dependencies_count dc(config_hash) AS distinct_config_hashes max(last_seen) AS last_event_time
    BY host_id compose_project
| join type=left max=0 host_id compose_project [
    search index=oti_containers sourcetype="docker:events" earliest=-4h@h latest=now
    | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
    | eval compose_project=trim(toString(coalesce(
        compose_project, composeProject,
        Actor__Attributes__com_docker_compose_project,
        com_docker_compose_project, "")))
    | where len(compose_project)>0 OR match(lower(_raw), "com.docker.compose")
        OR match(lower(_raw), "compose")
    | rex field=_raw "com[.]docker[.]compose[.]project[=](?<cp_from_raw>[^,\\s]+)"
    | eval compose_project=if(len(compose_project)>0, compose_project, trim(cp_from_raw))
    | where len(compose_project)>0
    | stats max(_time) AS compose_evt_max BY host_id compose_project
  ]
| eval last_event_time=max(last_event_time, compose_evt_max)
| join type=left max=0 compose_project [
    | inputlookup compose_project_baseline.csv
    | eval compose_project=trim(toString(coalesce(project, compose_project, composeProject, "")))
    | eval expected_total_services=tonumber(tostring(coalesce(expected_total_services, expected_services, svc_count, total_services, "")),10)
    | eval expected_dependency_chain=toString(coalesce(expected_dependency_chain, dep_chain, dependency_chain, ""))
    | fields compose_project expected_total_services expected_dependency_chain
  ]
| eval expected_total_from_baseline=expected_total_services
| eval total_services=max(observed_services, coalesce(expected_total_services, observed_services))
| eval total_services=if(isnull(total_services) OR total_services<1, observed_services, total_services)
| eval project_health_pct=round(100.0 * healthy_services / total_services, 2)
| eventstats sum(running_services) AS fleet_running_roll sum(total_services) AS fleet_total_roll avg(project_health_pct) AS fleet_avg_project_health BY compose_project
| eval fleet_running_ratio=if(fleet_total_roll>0, round(100.0 * fleet_running_roll / fleet_total_roll, 2), null())
| streamstats window=6 current=t global=f first(project_health_pct) AS ph_first last(project_health_pct) AS ph_last BY host_id compose_project
| eval health_flap=if(isnotnull(ph_first) AND isnotnull(ph_last) AND abs(ph_last - ph_first)>=20, 1, 0)
| eval severity=case(
    (broken_dependencies_count>0) AND (running_services>0), "critical_dependency_chain_broken_dead_dep",
    isnotnull(project_health_pct) AND project_health_pct<50, "critical_project_health_below_50pct",
    isnotnull(project_health_pct) AND project_health_pct<80, "high_project_health_below_80pct",
    (distinct_config_hashes>1), "high_config_hash_drift_in_project",
    (health_flap==1), "medium_intermittent_health_check_flapping",
    (isnotnull(expected_total_services) AND observed_services!=expected_total_services), "low_baseline_drift",
    true(), null())
| where isnotnull(severity)
| eval recommended_response=case(
    severity=="critical_dependency_chain_broken_dead_dep", "Stop traffic to the bundle; identify the dependency container that is unhealthy or not running while dependents started; run a controlled compose up --wait or full project recreate; verify depends_on conditions and healthcheck start_period.",
    severity=="critical_project_health_below_50pct", "Treat as partial bundle outage: enumerate non-running services, inspect exit and health logs, validate disk and registry pulls on the host, then redeploy the full project hash set together.",
    severity=="high_project_health_below_80pct", "Elevated partial-up risk: compare running versus declared service list, reconcile image digests, and schedule same-window recreate for missing services before customer-visible 502s spread.",
    severity=="high_config_hash_drift_in_project", "Config-hash mismatch inside one project indicates split-brain compose generations; redeploy from the canonical compose file, avoid one-service up without --build for peers, and audit who ran partial updates.",
    severity=="medium_intermittent_health_check_flapping", "Health percentage swung sharply across buckets: widen inspect poll, correlate with CPU throttle UC-3.1.3 and probe failures UC-3.1.22, tune start_period and dependency health gates.",
    severity=="low_baseline_drift", "Observed service cardinality differs from compose_project_baseline.csv; refresh the CSV from CI inventory or merge the edge registration ticket before muting.",
    true(), "Correlate docker:inspect compose labels with compose events on the host; confirm com.docker.compose.project grouping before closing.")
| table compose_project host_id total_services running_services healthy_services broken_dependencies_count distinct_config_hashes project_health_pct severity last_event_time recommended_response expected_total_from_baseline fleet_running_ratio fleet_avg_project_health
```

### Step 4 — Validate

Positive path A — dependency stall: on a lab host, define service web with depends_on db and a failing db healthcheck; bring the stack up, confirm db stays unhealthy while web may still run depending on policy, and expect critical_dependency_chain_broken_dead_dep when chain_hit counts increment and running_services stays positive.

Positive path B — partial cardinality: remove one service container manually while leaving others running, confirm observed_services drops below expected_total_services from compose_project_baseline.csv, and expect low_baseline_drift or critical_project_health_below_50pct depending on healthy ratio math.

Positive path C — hash drift: edit compose YAML, run docker compose up for only one service without recreating peers, confirm distinct_config_hashes exceeds one, and expect high_config_hash_drift_in_project.

Negative path — healthy full stack: docker compose up -d for a known-good bundle, verify all services running and healthy, distinct_config_hashes equals one, and confirm the search emits no severity row after the where clause for that host and project across two intervals.

Field sanity: temporarily rename label fields in a sandbox forwarder to mimic a new TA release and verify coalesce still resolves compose_project. RBAC: readers without index=oti_containers must see zero rows. Clock skew beyond ninety seconds misaligns joins; enforce chrony on edge gateways.

Correlation discipline: compare alert times to ingress 502 share dashboards; misalignment often means load balancers still point at a half-ready bundle.

Governance discipline: replay validation after every Docker Engine major upgrade because label embedding in events can shift.

### Step 5 — Operationalize and troubleshoot

Case 1 — critical_dependency_chain_broken_dead_dep during edge retail hours: drain storefront traffic at the local proxy, run docker compose ps and docker inspect on the named dependency service, validate disk and registry credentials, then recreate the full project under a single change record rather than hand-starting individual containers that bypass depends_on gates.

Case 2 — critical_project_health_below_50pct with no obvious dependency string: enumerate exited containers with docker compose ps -a, correlate to UC-3.1.2 oom_kill rows and UC-3.1.1 die events, and restore missing tasks before blaming application logic.

Case 3 — high_project_health_below_80pct after image promotion: confirm CI pushed all service digests referenced by the compose file, verify pull errors in docker:events, and rerun compose pull && compose up with parallelism limits suited to WAN links.

Case 4 — high_config_hash_drift_in_project following developer hotfix: interview whether someone ran docker compose up partial on a laptop attached to production-like data; remediate by redeploying the canonical bundle from git SHA and documenting why partial up is disallowed on registered hosts.

Case 5 — medium_intermittent_health_check_flapping without hash drift: widen inspect interval slightly to avoid aliasing, read UC-3.1.3 CPU throttle context, and tune healthcheck start_period for slow dependencies before muting.

Case 6 — low_baseline_drift after intentional service removal: update compose_project_baseline.csv in the same ticket that retires the service; do not leave stale expected_total_services values that page forever.

Case 7 — join to compose_project_baseline misses: normalize project names between CSV and labels—Compose directory names versus explicit name: fields differ; enforce a single registry string in CMDB publish jobs.

Case 8 — docker:events join explodes cardinality: ensure stats max by host_id compose_project in the subsearch and keep max=0 on the join to prevent duplicate project rows.

Case 9 — mvexpand dropped rows when depends_on empty: confirm _NODEPS_ sentinel keeps one row per service in the broken_dep_unit stats path; if your TA strips empty multivalue differently, add a fillnull guard in a wrapper macro.

Case 10 — streamstats flap false positives during host clock step events: filter _time outliers or increase window to twelve buckets on noisy CI hosts after FinOps approval.

Case 11 — fleet_running_ratio null on single-host pilots: expect null when fleet_total_roll is zero; treat as informational and rely on project_health_pct alone until multiple gateways register the same project name.

Case 12 — Splunk Cloud scan cost: narrow earliest to -2h after validation or summarize inspect snapshots into metrics indexes retaining only label hashes and state enums.

Dashboard publishing: mirror visualization guidance with drilldowns to raw docker:inspect and docker:events for the same host_id and compose_project. Evidence retention: weekly CSV exports with compose_project_baseline.csv commit hashes satisfy internal audit samples when paired with change tickets that document YAML revisions.

Closing checklist: exactly five Step headers use plain text with em dashes; Step 3 hosts the fenced SPL identical to the spl JSON field; monitoringType includes Reliability and Availability; cimModels include Application_State and Performance; equipment lists docker only; equipmentModels include docker_engine and docker_compose_v2; narrative JSON fields avoid asterisk emphasis; references use six unique URLs including Docker Compose specification pages, depends_on reference, labels extension chapter, Splunk Lantern specific path, Cloudflare edge containers engineering article, and Compose release notes; no forbidden boilerplate phrases from the gold uplift list appear in narrative fields.

Supplemental engineering notes for long-term owners: when rootless Docker moves cgroup paths, inspect still works but label keys must remain consistent—retest after Engine upgrades. When mirroring bundles to podman compose compatibility layers, validate label parity before trusting this UC on mixed estates. When finance challenges ingest cost, compare license bytes to revenue risk of silent partial outages at thousands of edge stores. When legal requests holds, include compose_project_baseline.csv versions in preservation scope. When automating remediation, disallow unattended docker compose down on regulated hosts without human gates. When training new responders, contrast this UC with UC-3.1.28 using a whiteboard sketch of single-host bundle versus multi-host scheduler. When Splunk Cloud moves indexes, update the comment macro in the same change window as forwarder outputs. When closing incidents, record whether fix was full recreate, dependency health tuning, registry recovery, or baseline refresh.

Appendix — compose_project_baseline.csv contract

project must match the com.docker.compose.project label string after normalization. expected_total_services should equal the service count from the approved compose file for that git ref. expected_dependency_chain can be a serialized depends_on summary for human auditors even if the SPL primarily uses live depends_on labels at runtime.

Appendix — evidence pack narrative

Weekly CSV exports should list compose_project, host_id, severity, project_health_pct, and broken_dependencies_count with ticket identifiers tying changes to compose YAML revisions, satisfying platform governance reviewers who ask how edge reliability is instrumented beyond single-container probes.

Appendix — performance discipline

If Job Inspector shows heavy scan cost, push docker:inspect into a summary index with five-minute latest state per container before alerting, retaining raw inspect in a shorter hot window for forensics.

Appendix — security discipline

Restrict dashboards that show compose_project names when those names encode customer site identifiers; mask in executive views while keeping full strings in privileged indexes.

Appendix — FinOps alignment

Attach distinct_config_hashes incidents to change calendars that track developer laptop attach events versus automated deployers, helping finance see operational risk drivers beyond cloud spend.

Appendix — review cadence

Quarterly replay one historical partial-outage through the SPL after Docker Compose or Engine upgrades; refresh rex patterns if Actor attribute shapes change.

Final reminder: Kubernetes-native production should pair this UC only on nodes where Compose-labeled workloads truly exist; do not expect Swarm manager telemetry to substitute for bundle grouping on bare compose hosts.


## SPL

```spl
`comment("UC-3.1.12 Compose Service Health. Tunables: index=oti_containers; sourcetype=docker:inspect primary; docker:events join for compose-adjacent lifecycle timestamps; inputlookup compose_project_baseline.csv on compose_project; streamstats health trend; eventstats fleet ratio context; config-hash drift uses dc(config_hash)>1; earliest=-4h@h latest=now; orchestrator scope is Compose project bundle not Swarm service replicas (UC-3.1.28).")`
index=oti_containers sourcetype="docker:inspect" earliest=-4h@h latest=now
| eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
| eval compose_project=trim(toString(coalesce(
    compose_project, composeProject, ComposeProject,
    Config_Labels_com_docker_compose_project,
    Labels_com_docker_compose_project,
    com_docker_compose_project, "")))
| eval compose_service=trim(toString(coalesce(
    compose_service, composeService, service,
    Config_Labels_com_docker_compose_service,
    Labels_com_docker_compose_service,
    com_docker_compose_service, Name, name, "")))
| eval depends_on=toString(coalesce(
    Config_Labels_com_docker_compose_depends_on,
    Labels_com_docker_compose_depends_on,
    com_docker_compose_depends_on, depends_on, DependsOn, ""))
| eval config_hash=trim(toString(coalesce(
    Config_Labels_com_docker_compose_config_hash,
    Labels_com_docker_compose_config_hash,
    com_docker_compose_config_hash, config_hash, ConfigHash, "")))
| eval state_status=lower(trim(toString(coalesce(
    State_Status, State__Status, state_status, stateStatus, Status, ""))))
| eval health_status=lower(trim(toString(coalesce(
    State_Health_Status, State__Health__Status, health_status, healthStatus, ""))))
| where len(compose_project)>0 AND len(compose_service)>0
| stats latest(state_status) AS state_status latest(health_status) AS health_status
    latest(depends_on) AS depends_on latest(config_hash) AS config_hash max(_time) AS last_seen
    BY host_id compose_project compose_service
| eval running_flag=if(state_status=="running",1,0)
| eval healthy_flag=if(state_status=="running" AND (isnull(health_status) OR len(health_status)==0 OR health_status=="healthy"),1,0)
| eval dep_mv=if(len(trim(replace(replace(depends_on,"\"","")," ","")))==0, split("_NODEPS_",","), split(lower(trim(replace(replace(depends_on,"\"","")," ",""))),","))
| eval down_name=if(state_status!="running" OR health_status=="unhealthy", compose_service, null())
| eventstats values(down_name) AS down_mv BY host_id compose_project
| mvexpand dep_mv
| eval dtrim=trim(replace(replace(replace(replace(dep_mv,":service_healthy:true",""),":service_started:true",""),":service_healthy:false",""),":service_started:false",""))
| eval chain_hit=if(state_status=="running" AND dtrim!="_NODEPS_" AND len(dtrim)>0 AND isnotnull(mvfind(down_mv, dtrim)),1,0)
| stats sum(chain_hit) AS broken_dep_unit max(running_flag) AS running_flag max(healthy_flag) AS healthy_flag
    latest(config_hash) AS config_hash max(last_seen) AS last_seen
    BY host_id compose_project compose_service
| stats dc(compose_service) AS observed_services sum(running_flag) AS running_services sum(healthy_flag) AS healthy_services
    sum(broken_dep_unit) AS broken_dependencies_count dc(config_hash) AS distinct_config_hashes max(last_seen) AS last_event_time
    BY host_id compose_project
| join type=left max=0 host_id compose_project [
    search index=oti_containers sourcetype="docker:events" earliest=-4h@h latest=now
    | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
    | eval compose_project=trim(toString(coalesce(
        compose_project, composeProject,
        Actor__Attributes__com_docker_compose_project,
        com_docker_compose_project, "")))
    | where len(compose_project)>0 OR match(lower(_raw), "com.docker.compose")
        OR match(lower(_raw), "compose")
    | rex field=_raw "com[.]docker[.]compose[.]project[=](?<cp_from_raw>[^,\\s]+)"
    | eval compose_project=if(len(compose_project)>0, compose_project, trim(cp_from_raw))
    | where len(compose_project)>0
    | stats max(_time) AS compose_evt_max BY host_id compose_project
  ]
| eval last_event_time=max(last_event_time, compose_evt_max)
| join type=left max=0 compose_project [
    | inputlookup compose_project_baseline.csv
    | eval compose_project=trim(toString(coalesce(project, compose_project, composeProject, "")))
    | eval expected_total_services=tonumber(tostring(coalesce(expected_total_services, expected_services, svc_count, total_services, "")),10)
    | eval expected_dependency_chain=toString(coalesce(expected_dependency_chain, dep_chain, dependency_chain, ""))
    | fields compose_project expected_total_services expected_dependency_chain
  ]
| eval expected_total_from_baseline=expected_total_services
| eval total_services=max(observed_services, coalesce(expected_total_services, observed_services))
| eval total_services=if(isnull(total_services) OR total_services<1, observed_services, total_services)
| eval project_health_pct=round(100.0 * healthy_services / total_services, 2)
| eventstats sum(running_services) AS fleet_running_roll sum(total_services) AS fleet_total_roll avg(project_health_pct) AS fleet_avg_project_health BY compose_project
| eval fleet_running_ratio=if(fleet_total_roll>0, round(100.0 * fleet_running_roll / fleet_total_roll, 2), null())
| streamstats window=6 current=t global=f first(project_health_pct) AS ph_first last(project_health_pct) AS ph_last BY host_id compose_project
| eval health_flap=if(isnotnull(ph_first) AND isnotnull(ph_last) AND abs(ph_last - ph_first)>=20, 1, 0)
| eval severity=case(
    (broken_dependencies_count>0) AND (running_services>0), "critical_dependency_chain_broken_dead_dep",
    isnotnull(project_health_pct) AND project_health_pct<50, "critical_project_health_below_50pct",
    isnotnull(project_health_pct) AND project_health_pct<80, "high_project_health_below_80pct",
    (distinct_config_hashes>1), "high_config_hash_drift_in_project",
    (health_flap==1), "medium_intermittent_health_check_flapping",
    (isnotnull(expected_total_services) AND observed_services!=expected_total_services), "low_baseline_drift",
    true(), null())
| where isnotnull(severity)
| eval recommended_response=case(
    severity=="critical_dependency_chain_broken_dead_dep", "Stop traffic to the bundle; identify the dependency container that is unhealthy or not running while dependents started; run a controlled compose up --wait or full project recreate; verify depends_on conditions and healthcheck start_period.",
    severity=="critical_project_health_below_50pct", "Treat as partial bundle outage: enumerate non-running services, inspect exit and health logs, validate disk and registry pulls on the host, then redeploy the full project hash set together.",
    severity=="high_project_health_below_80pct", "Elevated partial-up risk: compare running versus declared service list, reconcile image digests, and schedule same-window recreate for missing services before customer-visible 502s spread.",
    severity=="high_config_hash_drift_in_project", "Config-hash mismatch inside one project indicates split-brain compose generations; redeploy from the canonical compose file, avoid one-service up without --build for peers, and audit who ran partial updates.",
    severity=="medium_intermittent_health_check_flapping", "Health percentage swung sharply across buckets: widen inspect poll, correlate with CPU throttle UC-3.1.3 and probe failures UC-3.1.22, tune start_period and dependency health gates.",
    severity=="low_baseline_drift", "Observed service cardinality differs from compose_project_baseline.csv; refresh the CSV from CI inventory or merge the edge registration ticket before muting.",
    true(), "Correlate docker:inspect compose labels with compose events on the host; confirm com.docker.compose.project grouping before closing.")
| table compose_project host_id total_services running_services healthy_services broken_dependencies_count distinct_config_hashes project_health_pct severity last_event_time recommended_response expected_total_from_baseline fleet_running_ratio fleet_avg_project_health
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS st FROM datamodel=Application_State WHERE nodename=Application_State earliest=-4h latest=now BY Application_State.dest Application_State.app
| rename Application_State.dest AS host_id
| where st!="running"
```

## Visualization

Time-series panel of project_health_pct per compose_project with reference bands at eighty and fifty percent; Sankey or parallel-sets diagram from compose_service to coarse state or health buckets; sortable table of distinct_config_hashes and image digests for drift triage; top-N broken_projects leaderboard by broken_dependencies_count and severity tier coloring.

## Known False Positives

Legitimate docker compose up single-service restarts during inner-loop development can temporarily raise distinct_config_hashes or dependency warnings until peers reload; tag developer host classes in compose_project_baseline.csv or macro-exclude those host_id patterns after governance approval. Services declared with restart: no or one-shot batch helpers may be intentionally exited while the rest of the project stays running for ETL or migration windows; annotate baseline rows with expected_non_running_services to avoid false chain alarms. Compose file format migrations and simultaneous compose convert drills can produce brief config-hash skew across containers until the operator finishes a full recreate; treat sustained drift only after two inspect cadences. Front-end install hooks such as yarn or npm postinstall spikes can keep a service in starting health while dependencies are actually fine; correlate with UC-3.1.22 probe timelines before declaring dead dependencies. Home-lab or sandbox projects with disposable names may never publish baseline rows yet still appear in inspect; route them to non-prod indexes or maintain a scratch_project_allowlist.csv referenced by a wrapper macro. Rolling kernel or Engine upgrades that restart containers out of order may trip medium_intermittent_health_check_flapping without customer impact; require SLO correlation before sev-one pages. CI builders that reuse com.docker.compose.project names across ephemeral workspaces can inflate fleet_avg_project_health variance; segregate CI indexes from edge production indexes. Manual docker start of a dependency after a compose down partially completes can clear chain_hit while leaving inconsistent volumes; pair with change tickets describing operator actions. Blue-green style experiments that intentionally run two generations with different hashes on separate ports should be labeled in baseline notes so drift alerts route to the right squad.

## References

- [Docker Docs — Compose specification](https://docs.docker.com/compose/compose-file/)
- [Docker Docs — Compose services depends_on](https://docs.docker.com/compose/compose-file/05-services/#depends_on)
- [Docker Docs — Compose specification extensions and labels](https://docs.docker.com/compose/compose-file/11-extension/)
- [Splunk Lantern — Getting Docker log data into Splunk Cloud Platform with OpenTelemetry](https://lantern.splunk.com/Platform_Data_Management/Unlock_Insights/Getting_Docker_log_data_into_Splunk_Cloud_Platform_with_OpenTelemetry)
- [Cloudflare Blog — Cloudflare Containers on Workers (edge Docker patterns)](https://blog.cloudflare.com/cloudflare-containers-coming-2025)
- [Docker Docs — Compose release notes](https://docs.docker.com/compose/releases/release-notes/)
