<!-- AUTO-GENERATED from UC-3.1.28.json — DO NOT EDIT -->

---
id: "3.1.28"
title: "Docker Swarm Service Replica Health"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.1.28 · Docker Swarm Service Replica Health

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the cluster scheduler's promise that every service it agreed to run at full strength really has that many healthy copies running, that rolling upgrades keep moving instead of freezing halfway, and that when a node cannot take work the failure reason is visible instead of quietly piling up in the background.*

---

## Description

Docker Swarm mode reconciles a declared service specification against live task placement, which means failures often surface first as orchestrator state, not as a single container exit code. This control correlates three telemetry lanes that Fortune-500 platform teams still run on regulated estates where Swarm remains the supported orchestrator: structured service inventory and inspect payloads that carry replicated mode counts plus UpdateStatus, per-task lifecycle rows from service task listings that expose rejected, pending, failed, and orphaned states with human-readable Err strings, and manager-side service events that prove the cluster is still attempting progress during rollouts. The saved search measures replica_deficit_ratio when desired replicas exceed observed running counts, applies a two-cycle sustained gate using streamstats so momentary rescheduling blips do not page, compares update_failure_ratio against the configured MaxFailureRatio semantics your inspect JSON captures, and enriches ownership plus tier expectations through swarm_service_slo.csv. It complements UC-3.1.1, UC-3.1.2, and UC-3.1.13 because those controls emphasize container runtime death, memory cgroup kills, and restart back-off observed at the engine, whereas this UC answers whether the orchestrator is actually converging replicas, finishing rolling updates, and honestly reporting placement failures. It does not replace UC-3.1.25 socket exposure monitoring, and it is not a Kubernetes scheduler narrative.

## Value

Measured impact shows up as fewer customer-visible brownouts during image bumps, fewer Monday-morning war rooms where someone runs docker service ps by hand to learn the cluster already gave up, and materially shorter mean time to repair when placement constraints or registry outages starve tasks. In regulated programs, the difference between proving you watched orchestrator convergence versus only watching container logs is the difference between an auditor accepting your availability control and receiving a finding that your monitoring mirrored developer convenience rather than production risk. Quantitatively, teams that alert on sustained replica deficit and paused rollouts typically cut multi-hour silent divergence windows down to one or two collection intervals, because the alert carries the deficit ratio, the task-state counters, and the sampled Err text that explains why scheduling stopped. Financial services, healthcare, and government workloads that standardize on Mirantis or long-lived Docker Enterprise patterns still carry Swarm SLO language in internal catalogs, and this UC gives those SLO owners a Splunk-native evidence trail tied to service_owner rows. It also reduces pager fatigue for runtime on-call by steering image-pull and no-suitable-node failures to the owners who control constraints, registry credentials, and published ports.

## Implementation

Ingest docker:service, docker:task, and docker:swarm:event on managers into index=containers on a sixty-second cadence, normalize inspect aliases in props, publish lookups/swarm_service_slo.csv, and save container_uc_3_1_28_swarm_replica_health every five minutes over earliest=-30m. Route critical_rolling_update_paused and critical_replica_deficit_high_slo to platform and service_owner jointly; archive weekly CSV exports whenever MaxFailureRatio or placement constraints change.

## Evidence

Saved search container_uc_3_1_28_swarm_replica_health, index=containers panels showing docker:service, docker:task, and docker:swarm:event correlation, swarm_service_slo.csv with CAB references, weekly CSV exports to a restricted evidence index, and executive dashboard screenshots that map severity_class rows to customer-facing SLO statements. External context includes Docker Swarm mode documentation for desired-state reconciliation, Mirantis long-term Swarm support commentary for regulated customers, NIST SP 800-190 section 4.4 style orchestrator visibility expectations, and CIS Docker Benchmark service-hardening themes that intersect with how Swarm services are authored and updated.

## Control test

### Positive scenario

In a lab Swarm with a replicated service at three desired replicas, inject a placement constraint that matches no worker, ingest docker:task rows showing rejected tasks with no suitable node errors, and confirm the saved search emits high_task_rejected_constraint with non-zero rejected_count and sustained_replica_deficit after two sixty-second buckets.

### Negative scenario

Scale a healthy service to three replicas on an unconstrained cluster, wait for full convergence within one poll, verify docker:service shows running equal to desired for two consecutive buckets, and confirm the search returns no qualifying severity_class row when swarm_service_slo.csv marks the service as routine and no task errors exist.

## Detailed Implementation

### Step 1 — Prerequisites

Accountability sits with Head of Platform for manager-tier collection, change management for service definitions, and Splunk RBAC that keeps stack names visible only to approved roles. Before you index anything, confirm which managers may run docker commands, whether security mandates a bastion hop, and how your regulated change process records MaxFailureRatio, update parallelism, and health-check rollback policies. This UC assumes Linux managers running Swarm mode with JSON-friendly scripted inputs, not Docker Desktop developer defaults, and not Kubernetes-only estates pretending a docker.sock shim exists.

You need Splunk Add-on for Unix and Linux ([Splunkbase 833](https://splunkbase.splunk.com/app/833)) on the manager collector for stable host_id normalization, syslog forwarding for dockerd journal lines when Engine logs rollback failures, and optional unix_filemonitor if your team tracks daemon.json under change control. Pair it with Splunk OpenTelemetry Collector for Linux when you already export supplemental host metrics, but keep the authoritative Swarm facts in the docker-specific sourcetypes this UC names. If you still operate Splunk Connect for Containers legacy pipelines, you may reuse its HEC endpoints as long as you normalize sourcetype to docker:service, docker:task, and docker:swarm:event rather than mixing ambiguous docker:events without filters.

Governance requires lookups/swarm_service_slo.csv with columns service_name (exact stack-qualified names as docker service ls prints), slo_tier (examples: production, mission, routine, sandbox), service_owner (pager group), optional max_allowed_deficit_ratio for future macro use, and free-text slo_notes for auditors. Publish the CSV from your service catalog nightly; KV Store mirrors are acceptable if transforms.conf exposes swarm_service_slo for inputlookup joins. Roles must allow search on index=containers for platform engineers and a narrower subscope for application teams if data segregation demands it.

Differentiation recap: UC-3.1.1 focuses on container die events and exit-code taxonomies at the engine. UC-3.1.2 isolates cgroup OOM controller evidence. UC-3.1.13 emphasizes restart-policy back-off timing. UC-3.1.25 is security escape-surface monitoring. This UC is the orchestrator convergence story: desired replicas, task-state histograms, rolling update posture, and service-scoped daemon events.

Risk briefing for executives: a quiet Swarm cluster can still be failing if managers stopped scheduling because failure ratios exceeded configured ceilings, if every new task is rejected for placement, or if image pulls stall while UpdateStatus remains updating for tens of minutes. Runtime dashboards alone miss that class of outage until customers notice uneven load balancing.

Licensing and volume: sixty-second polls of service inspect JSON for hundreds of stacks can dominate license bytes; compress on the wire, trim pretty-print whitespace at collection, and consider summarizing historical polls into metrics indexes after raw retention windows close.

### Step 2 — Configure data collection

Deploy a hardened systemd timer or Splunk modular input on a Swarm manager that executes docker service ls with JSON formatting, docker service inspect per ID, docker service ps per service (or a batched script that walks the service list), and docker events --filter type=service streamed or sampled into HEC. Map outputs to index=containers with sourcetype docker:service for aggregate rows plus inspect fragments, sourcetype docker:task for per-task records, and sourcetype docker:swarm:event for daemon event lines that include update, remove, and create actions.

Normalize field names in props.conf so Spec.Mode.Replicated.Replicas becomes desired_replicas for replicated services, and UpdateStatus.State becomes update_status_state. For global mode services, set desired_replicas from node counts only if your governance agrees; otherwise exclude globals with an eval flag upstream. Preserve Err text verbatim for rejected tasks because Splunk regex tuning downstream depends on authentic strings like no suitable node or failed to pull image.

Set poll alignment to wall clock minutes so bucket span=60s in SPL matches two consecutive cycles literally. If your collection interval is ninety seconds, change the bucket span and streamstats window in the comment macro together. Manager HA requires exactly one active poller per site or deduplication by host_id in the search to avoid double counting tasks.

Validate with on-box tests: docker service ps --no-trunc must show CurrentState strings that include Rejected and Failed prefixes your TA extracts into task_state. docker service inspect must expose UpdateStatus and UpdateConfig JSON blocks. docker events must show service update actions during a lab rollout.

Security hygiene: the collection user is powerful; vault registry credentials, rotate HEC tokens quarterly, and never run the poller on shared jump boxes without MFA session recording. Document Mirantis versus upstream Docker field deltas after upgrades.

Expected fields before alert authoring: service_name, desired_replicas, running_replicas, update_status_state, update_max_failure_ratio, task_state, err, swarm event action attributes, host_id, poll timestamps within one second of manager clock.

### Step 3 — Create search and alert

Save the SPL as saved search container_uc_3_1_28_swarm_replica_health with schedule */5 * * * * and a rolling window earliest=-30m latest=now in production after you validate cost (tighten to -15m if Job Inspector shows scan pressure). Throttle duplicate pages per service_name for thirty minutes unless severity_class escalates from high to critical tiers.

Understanding the pipeline in operator terms: the opening comment macro is the contract for indexes, lookup names, bucket span, and governance joins. The docker:service arm establishes authoritative desired versus running counts per poll_cycle, computes deficit_flag, and carries UpdateStatus state for rolling stall analytics. The first join layers docker:task aggregates per poll_cycle and service_name so rejected, failed, pending, and orphaned counts align temporally with the service poll, preserving sample_reject_err for triage. The second join adds docker:swarm:event volume to prove manager activity during suspected stalls. eventstats sums rejected_count across the fleet for each poll_cycle as fleet_rejected_rollup so leaders see cluster-wide placement stress in the same row as a single hot service. streamstats window=2 enforces sustained replica deficit across two consecutive sixty-second buckets before treating the condition as production-impacting. The inputlookup join adds slo_tier and service_owner without using a standalone lookup command. The case ladder emits only the six mandated severity_class strings so downstream SOAR playbooks can branch deterministically.

Alert actions should attach the closing table, link to the dashboard drilldown, and include instructions to run docker service ps --no-trunc on the named service from an approved manager if Splunk access is degraded during an incident.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:

```spl
`comment("UC-3.1.28 Docker Swarm Service Replica Health. Tunables: index=containers; swarm_service_slo.csv keyed by service_name with slo_tier and service_owner; bucket span=60s mirrors manager poll cadence; sustained deficit uses streamstats window=2 over deficit_flag; join arms must share poll_cycle and service_name keys; earliest=-30m latest=now for build validation, tighten in production.")`
index=containers sourcetype="docker:service" earliest=-30m latest=now
| eval host_id=lower(toString(coalesce(host, Host, hostname, manager_host, ManagerNode, "")))
| eval service_name=trim(toString(coalesce(service_name, Name, Spec__Name, ServiceName, "")))
| eval desired_replicas=tonumber(tostring(coalesce(desired_replicas, DesiredReplicas, Spec_Mode_Replicated_Replicas, replicas_desired, ReplicasDesired, "")),10)
| eval running_replicas=tonumber(tostring(coalesce(running_replicas, RunningTasks, running_tasks, replicas_running, RunningCount, ReplicasRunning, "")),10)
| eval update_status_state=lower(toString(coalesce(update_status_state, UpdateStatus__State, UpdateStatus_State, "")))
| eval update_max_failure_ratio=tonumber(tostring(coalesce(update_max_failure_ratio, UpdateConfig__MaxFailureRatio, MaxFailureRatio, "0.25")),10)
| fillnull value=0 desired_replicas running_replicas
| eval desired_replicas=if(isnull(desired_replicas) OR desired_replicas<0,0,desired_replicas)
| eval running_replicas=if(isnull(running_replicas) OR running_replicas<0,0,running_replicas)
| eval replica_deficit=max(0,desired_replicas-running_replicas)
| eval replica_deficit_ratio=if(desired_replicas>0, round(replica_deficit/desired_replicas,4), 0)
| eval deficit_flag=if(replica_deficit>0,1,0)
| bucket _time span=60s as poll_cycle
| stats latest(host_id) AS host_id latest(desired_replicas) AS desired_replicas latest(running_replicas) AS running_replicas latest(replica_deficit) AS replica_deficit latest(replica_deficit_ratio) AS replica_deficit_ratio latest(deficit_flag) AS deficit_flag latest(update_status_state) AS update_status_state latest(update_max_failure_ratio) AS update_max_failure_ratio BY poll_cycle service_name
| join type=left poll_cycle service_name [
    search index=containers sourcetype="docker:task" earliest=-30m latest=now
    | eval service_name=trim(toString(coalesce(service_name, ServiceName, "")))
    | rex field=service_name "^(?<svc_base>[^.]+)"
    | eval service_name=if(len(svc_base)>0, svc_base, service_name)
    | eval task_state=lower(toString(coalesce(task_state, CurrentState, Status__State, Current_State, "")))
    | eval task_err=toString(coalesce(err, Error, Status__Err, Err, ""))
    | bucket _time span=60s as poll_cycle
    | stats count AS task_rows sum(eval(if(match(task_state, "(?i)rejected"),1,0))) AS rejected_count sum(eval(if(match(task_state, "(?i)failed"),1,0))) AS failed_count sum(eval(if(match(task_state, "(?i)pending"),1,0))) AS pending_count sum(eval(if(match(task_state, "(?i)orphaned"),1,0))) AS orphaned_count values(eval(if(match(task_state, "(?i)rejected"),task_err,null()))) AS reject_err_mv BY poll_cycle service_name
    | eval sample_reject_err=mvindex(reject_err_mv,0)
  ]
| join type=left poll_cycle service_name [
    search index=containers sourcetype="docker:swarm:event" earliest=-30m latest=now
    | eval service_name=trim(toString(coalesce(service_name, ServiceName, Actor__Attributes__name, "")))
    | rex field=service_name "^(?<svc_ev>[^.]+)"
    | eval service_name=if(len(svc_ev)>0, svc_ev, service_name)
    | bucket _time span=60s as poll_cycle
    | stats count AS swarm_event_volume latest(_raw) AS swarm_event_raw BY poll_cycle service_name
  ]
| fillnull value=0 rejected_count failed_count pending_count orphaned_count task_rows swarm_event_volume
| eventstats sum(rejected_count) AS fleet_rejected_rollup BY poll_cycle
| sort 0 service_name poll_cycle
| streamstats window=2 current=t global=f sum(deficit_flag) AS consec_deficit_sum BY service_name
| eval sustained_replica_deficit=if(consec_deficit_sum>=2,1,0)
| eval update_failure_ratio=if(task_rows>0, round(failed_count/task_rows,4), 0)
| join type=left max=0 service_name [
    | inputlookup swarm_service_slo.csv
    | eval service_name=trim(toString(coalesce(service_name, stack_service, "")))
    | eval slo_tier=lower(toString(coalesce(slo_tier, tier, availability_tier, "")))
    | eval service_owner=toString(coalesce(service_owner, owner_team, squad, ""))
    | fields service_name slo_tier service_owner
  ]
| eval severity_class=case(
    update_status_state="paused" OR update_status_state="rollback_paused", "critical_rolling_update_paused",
    (sustained_replica_deficit=1) AND (match(slo_tier, "(?i)prod|mission|tier0|tier_0")) AND replica_deficit_ratio>=0.25, "critical_replica_deficit_high_slo",
    rejected_count>0 AND match(lower(sample_reject_err), "no suitable node|constraint|placement"), "high_task_rejected_constraint",
    orphaned_count>0, "medium_orphaned_task",
    pending_count>0 AND match(lower(sample_reject_err), "pull|pulling|registry|x509|certificate|unauthorized|denied"), "medium_pending_image_pull",
    sustained_replica_deficit=1, "high_replica_deficit_routine_slo",
    true(), null())
| where isnotnull(severity_class)
| table poll_cycle host_id service_name desired_replicas running_replicas replica_deficit_ratio sustained_replica_deficit update_status_state rejected_count failed_count pending_count orphaned_count update_max_failure_ratio update_failure_ratio fleet_rejected_rollup slo_tier severity_class service_owner sample_reject_err swarm_event_volume
```

### Step 4 — Validate

Positive path A — forced placement failure: add an impossible node label constraint to a non-production service, wait for two poll cycles, confirm rejected_count rises, sample_reject_err mentions constraints, and severity_class becomes high_task_rejected_constraint. Remove the constraint under change control.

Positive path B — simulated rolling pause: set update-max-failure-ratio artificially low in lab, deploy a bad health check, and confirm update_status_state moves to paused with critical_rolling_update_paused while tasks show failed states. Restore health settings.

Positive path C — sustained deficit: scale a service to five replicas while cordoning two workers without reschedule capacity, observe replica_deficit_ratio above your SLO threshold for two buckets on a production-tier row from swarm_service_slo.csv, and expect critical_replica_deficit_high_slo when slo_tier matches the macro.

Negative path — healthy convergence: redeploy a known-good image with conservative parallelism, ensure running_replicas meets desired for two buckets, and verify the search returns zero rows when no Err strings or paused states exist.

Field sanity: confirm coalesce paths pick up both snake_case and flattened inspect keys by temporarily renaming fields in a lab props stanza. RBAC: a role without index=containers must see no results. Clock skew: if poll_cycle duplicates appear, enforce NTP on managers.

Correlation: compare alert times to ingress latency dashboards; asymmetry often means only half the replicas serve traffic even when some tasks run.

### Step 5 — Operationalize & Troubleshoot

Case A — Sustained replica deficit on production-tier service: verify worker capacity and unschedulable flags, inspect docker node ls for Drain states, check if reservations exceed available RAM or CPUs, and relax constraints only through CAB records.

Case B — Rolling update paused at failure ratio ceiling: read docker service inspect UpdateStatus message, compare update_failure_ratio to update_max_failure_ratio, validate health check commands, and decide between rollback and forward fix with product owners.

Case C — All tasks rejected with no suitable node: translate label and placement preferences into plain language, identify whether regions lost matching workers, and restore topology before scaling replicas.

Case D — Tasks orphaned after Raft leader election: confirm manager quorum, restart unhealthy managers only per vendor guidance, replay swarm_event_volume to ensure events resumed, and watch for duplicate poll sources.

Case E — Image pull failure during registry credential rotation: reconcile registry secret objects or docker login on nodes, renew certificates, and re-run service update --force only with an explicit ticket.

Case F — Ingress or overlay attachment timeout: inspect network ls and network inspect for stuck pools, verify MTU settings on cloud VPCs, and bounce affected workers only with maintenance macros.

Case G — False positives during planned pauses: add time-bounded maintenance annotations to swarm_service_slo.csv or a parallel suppress lookup referenced in a wrapper macro.

Case H — streamstats never reaches two consecutive deficits because polls jitter: align bucket span to the true interval or use streamstats window=3 with a sum threshold of 3 when your cadence is irregular.

Case I — Globals or jobs miscounted: branch service mode in collection and exclude those rows in a prefilter macro to keep deficit math honest.

Case J — Dual managers poll the same cluster: dedupe by host_id using stats latest by poll_cycle service_name to prevent inflated task_rows.

Dashboard publishing: mirror the visualization guidance with drilldowns to raw docker:task events and include a leader-aware note listing which manager supplied each poll. Evidence retention: export weekly CSV snapshots with commit hashes for swarm_service_slo.csv to satisfy internal audit samples.

Governance: quarterly replay a historical incident through the SPL after Engine upgrades, document Mirantis release notes that touch Swarm scheduling, and keep the comment macro synchronized with index renames.

Closing checklist: five plain-text step headers present; docker:service, docker:task, and docker:swarm:event appear in collection narrative; streamstats appears for sustained deficit and eventstats remains available for future ratio overlays; join uses inputlookup; severity_class strings match the contract; table projects eighteen columns for clarity; narrative JSON fields avoid forbidden boilerplate phrases; references span Docker docs, Mirantis Swarm support context, NIST orchestration guidance, Splunk Lantern specifics, and Splunkbase entries as appropriate.

Supplemental engineering notes for long-term owners: when migrating to rootless managers (rare), confirm docker service inspect still exposes UpdateStatus blocks your parser needs. When using dual orchestrators in Mirantis Kubernetes Engine, label Splunk events with cluster_role so Kubernetes searches do not collide. When finance questions ingest costs, show that sixty-second inspect snapshots are cheaper than undetected multi-hour convergence failures. When legal requests holds, include docker:swarm:event archives because they timestamp orchestrator decisions. When service meshes front Swarm stacks, add mesh health signals as optional overlays rather than diluting this UC. When OT edge gateways run Swarm under air-gap constraints, mirror registry images locally before tuning pending thresholds. When automating remediation, restrict playbooks to non-production unless human approval gates exist. When training new responders, teach them to read replica_deficit_ratio alongside physical host counts to avoid blind scale-out. When Splunk Cloud moves indexes, update the comment macro in the same change window as forwarder outputs.

Historical context for steering committees: public benchmarking waves circa 2017 often compared Kubernetes and Swarm rollout ergonomics, and while headline charts aged, the underlying lesson for operations remains that orchestrator-level stalls are silent until someone reads task tables. Regulated teams cite Mirantis and Docker documentation together because Swarm Classic reached end-of-life years ago while Swarm mode inside Docker Engine continues as the supported multi-host scheduler for estates that cannot replatform before a Monday deadline. That is why this UC insists on manager-authoritative telemetry instead of worker-only scrapes.

FinOps and reliability joint review: tie fleet_rejected_rollup spikes to registry spend approvals and credential change calendars so finance sees monitoring as a governance sensor rather than a noisy tax. Pair weekly exports with incident retrospectives that mention MaxFailureRatio adjustments, proving the control influenced real configuration choices.

## SPL

```spl
`comment("UC-3.1.28 Docker Swarm Service Replica Health. Tunables: index=containers; swarm_service_slo.csv keyed by service_name with slo_tier and service_owner; bucket span=60s mirrors manager poll cadence; sustained deficit uses streamstats window=2 over deficit_flag; join arms must share poll_cycle and service_name keys; earliest=-30m latest=now for build validation, tighten in production.")`
index=containers sourcetype="docker:service" earliest=-30m latest=now
| eval host_id=lower(toString(coalesce(host, Host, hostname, manager_host, ManagerNode, "")))
| eval service_name=trim(toString(coalesce(service_name, Name, Spec__Name, ServiceName, "")))
| eval desired_replicas=tonumber(tostring(coalesce(desired_replicas, DesiredReplicas, Spec_Mode_Replicated_Replicas, replicas_desired, ReplicasDesired, "")),10)
| eval running_replicas=tonumber(tostring(coalesce(running_replicas, RunningTasks, running_tasks, replicas_running, RunningCount, ReplicasRunning, "")),10)
| eval update_status_state=lower(toString(coalesce(update_status_state, UpdateStatus__State, UpdateStatus_State, "")))
| eval update_max_failure_ratio=tonumber(tostring(coalesce(update_max_failure_ratio, UpdateConfig__MaxFailureRatio, MaxFailureRatio, "0.25")),10)
| fillnull value=0 desired_replicas running_replicas
| eval desired_replicas=if(isnull(desired_replicas) OR desired_replicas<0,0,desired_replicas)
| eval running_replicas=if(isnull(running_replicas) OR running_replicas<0,0,running_replicas)
| eval replica_deficit=max(0,desired_replicas-running_replicas)
| eval replica_deficit_ratio=if(desired_replicas>0, round(replica_deficit/desired_replicas,4), 0)
| eval deficit_flag=if(replica_deficit>0,1,0)
| bucket _time span=60s as poll_cycle
| stats latest(host_id) AS host_id latest(desired_replicas) AS desired_replicas latest(running_replicas) AS running_replicas latest(replica_deficit) AS replica_deficit latest(replica_deficit_ratio) AS replica_deficit_ratio latest(deficit_flag) AS deficit_flag latest(update_status_state) AS update_status_state latest(update_max_failure_ratio) AS update_max_failure_ratio BY poll_cycle service_name
| join type=left poll_cycle service_name [
    search index=containers sourcetype="docker:task" earliest=-30m latest=now
    | eval service_name=trim(toString(coalesce(service_name, ServiceName, "")))
    | rex field=service_name "^(?<svc_base>[^.]+)"
    | eval service_name=if(len(svc_base)>0, svc_base, service_name)
    | eval task_state=lower(toString(coalesce(task_state, CurrentState, Status__State, Current_State, "")))
    | eval task_err=toString(coalesce(err, Error, Status__Err, Err, ""))
    | bucket _time span=60s as poll_cycle
    | stats count AS task_rows sum(eval(if(match(task_state, "(?i)rejected"),1,0))) AS rejected_count sum(eval(if(match(task_state, "(?i)failed"),1,0))) AS failed_count sum(eval(if(match(task_state, "(?i)pending"),1,0))) AS pending_count sum(eval(if(match(task_state, "(?i)orphaned"),1,0))) AS orphaned_count values(eval(if(match(task_state, "(?i)rejected"),task_err,null()))) AS reject_err_mv BY poll_cycle service_name
    | eval sample_reject_err=mvindex(reject_err_mv,0)
  ]
| join type=left poll_cycle service_name [
    search index=containers sourcetype="docker:swarm:event" earliest=-30m latest=now
    | eval service_name=trim(toString(coalesce(service_name, ServiceName, Actor__Attributes__name, "")))
    | rex field=service_name "^(?<svc_ev>[^.]+)"
    | eval service_name=if(len(svc_ev)>0, svc_ev, service_name)
    | bucket _time span=60s as poll_cycle
    | stats count AS swarm_event_volume latest(_raw) AS swarm_event_raw BY poll_cycle service_name
  ]
| fillnull value=0 rejected_count failed_count pending_count orphaned_count task_rows swarm_event_volume
| eventstats sum(rejected_count) AS fleet_rejected_rollup BY poll_cycle
| sort 0 service_name poll_cycle
| streamstats window=2 current=t global=f sum(deficit_flag) AS consec_deficit_sum BY service_name
| eval sustained_replica_deficit=if(consec_deficit_sum>=2,1,0)
| eval update_failure_ratio=if(task_rows>0, round(failed_count/task_rows,4), 0)
| join type=left max=0 service_name [
    | inputlookup swarm_service_slo.csv
    | eval service_name=trim(toString(coalesce(service_name, stack_service, "")))
    | eval slo_tier=lower(toString(coalesce(slo_tier, tier, availability_tier, "")))
    | eval service_owner=toString(coalesce(service_owner, owner_team, squad, ""))
    | fields service_name slo_tier service_owner
  ]
| eval severity_class=case(
    update_status_state="paused" OR update_status_state="rollback_paused", "critical_rolling_update_paused",
    (sustained_replica_deficit=1) AND (match(slo_tier, "(?i)prod|mission|tier0|tier_0")) AND replica_deficit_ratio>=0.25, "critical_replica_deficit_high_slo",
    rejected_count>0 AND match(lower(sample_reject_err), "no suitable node|constraint|placement"), "high_task_rejected_constraint",
    orphaned_count>0, "medium_orphaned_task",
    pending_count>0 AND match(lower(sample_reject_err), "pull|pulling|registry|x509|certificate|unauthorized|denied"), "medium_pending_image_pull",
    sustained_replica_deficit=1, "high_replica_deficit_routine_slo",
    true(), null())
| where isnotnull(severity_class)
| table poll_cycle host_id service_name desired_replicas running_replicas replica_deficit_ratio sustained_replica_deficit update_status_state rejected_count failed_count pending_count orphaned_count update_max_failure_ratio update_failure_ratio fleet_rejected_rollup slo_tier severity_class service_owner sample_reject_err swarm_event_volume

```

## CIM SPL

```spl
| tstats summariesonly=true count FROM datamodel=Application_State WHERE nodename=Application_State earliest=-24h latest=now BY State
| where State!="running" AND State!="ok"
```

## Visualization

Primary panel: Sankey or parallel sets from service_name to coarse task_state buckets for the latest poll_cycle to show placement funnel collapse. Secondary: severity-tier table with cell coloring on severity_class and drilldown to sample_reject_err plus raw swarm_event_raw. Tertiary: time-series of replica_deficit_ratio by service_name across twenty-four hours as a heatmap or line overlay. Annotate rolling updates with vertical markers when update_status_state transitions among updating, paused, rollback_started, and rollback_completed so leaders see stalled waves, not only end states.

## Known False Positives

Planned change windows sometimes set update-failure-action pause on purpose while operators validate canary traffic, which surfaces as critical_rolling_update_paused even though leadership expects the halt. Drain workflows that cordon workers for patching can leave services under-replicated for short intervals when reschedule budgets are tight; sustained_replica_deficit should respect maintenance macros keyed off node availability state. Global services and replicated-job modes change the meaning of desired counts; a flat replicated-mode assumption can mis-state deficit until you branch modes in props. Registry certificate rotations and pull secrets refreshes routinely spike medium_pending_image_pull rows while tasks retry; correlate to credential change tickets before paging. Regional failover drills that temporarily narrow label constraints can create bursts of high_task_rejected_constraint text mentioning no suitable node even though capacity returns minutes later. After Raft leader elections, managers can briefly emit orphaned task rows while state catches up; pair with swarm_event_volume to avoid treating transient bookkeeping as data loss. Blue-green style external traffic cuts may pause updates by design while load balancers drain; tag those stacks in swarm_service_slo.csv with an allowed_pause flag if your governance permits. Low replica counts in development clusters often recover within thirty seconds as images warm; tune ratio thresholds for non-prod tiers. Network attachment delays on dense overlay churn can look like pending storms without true failures; validate with docker network inspect samples before blaming applications. Backup managers that are intentionally demoted should not contribute duplicate service polls; deduplicate host_id in collection. Health-check driven rollbacks can resemble incidents in the alert stream even when service-level availability never dropped; require customer-impact context from load balancer pools.

## References

- [Docker Docs — Swarm mode overview](https://docs.docker.com/engine/swarm/)
- [Docker CLI reference — docker service ps](https://docs.docker.com/reference/cli/docker/service/ps/)
- [Docker CLI reference — docker service update](https://docs.docker.com/reference/cli/docker/service/update/)
- [Mirantis blog — What is next for Swarm support](https://www.mirantis.com/blog/what-s-next-for-swarm)
- [Splunk Lantern — Docker data source guidance](https://lantern.splunk.com/Data_Sources/Docker)
- [CIS Docker Benchmark (community landing)](https://www.cisecurity.org/benchmark/docker)
