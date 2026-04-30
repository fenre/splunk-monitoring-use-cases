<!-- AUTO-GENERATED from UC-3.1.17.json — DO NOT EDIT -->

---
id: "3.1.17"
title: "Container Resource Limit Enforcement"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.1.17 · Container Resource Limit Enforcement

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Configuration, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*We check that every boxed workload has a painted size on the parking lot, so one vehicle cannot spread across four spaces and block everyone else. We also compare the dashboard sticker to the actual stripes on the pavement, because if those disagree the rules you thought you posted never really applied.*

---

## Description

This Configuration and Compliance control audits cgroup-limit governance for Fortune-scale Docker fleets: it proves whether each running container declares finite HostConfig.Memory and a hard CPU cap via NanoCpus or positive CpuQuota, compares those declarations to memory.max and cpu.max as read from cgroup v2 files to catch enforcement drift, and joins container_limit_policy.csv so production workloads cannot silently run unlimited memory, exceed tier ceilings such as sixteen gibibytes RAM or four fractional cores, or sit below documented floors that signal under-provisioning waste. It surfaces MemorySwap posture and CpuShares-only configurations that lack a true quota, because soft shares still permit hogging under contention while operators believe they imposed caps. UC-3.1.3 interprets CPU throttling once a cap exists; UC-3.1.4 interprets memory pressure ratios against an existing finite limit; UC-3.1.2 records oom_kill after pressure breaches. This UC answers the prior question of whether limits exist at all and whether policy and kernel reality agree, which is the isolation story auditors and platform governance teams require before trusting performance analytics built on assumed caps.

## Value

Quantified benefits include avoided host-wide OOM storms where a single unlimited workload crowds out dozens of revenue services, measurable reduction in noisy-neighbor latency incidents caused by quota-free CPU contention, and audit-ready evidence for PCI DSS 6.5.10 change and configuration controls, SOC 2 CC6.6 logical access and system operations monitoring, and ISO 27001 A.12.1.3 capacity management when limits are treated as mandatory controls. Policy-violation counts by image and environment feed executive scorecards and FinOps right-sizing programs: ceiling breaches highlight entitlement sprawl, floor breaches highlight wasted reservation dollars that finance can reclaim, and drift rows shorten investigations when compliance attests to one limit while the kernel enforces another. Pairing this detector with public guidance from NIST SP 800-190 on container resource control and CIS Docker Benchmark memory-and-CPU recommendations gives regulators a traceable narrative. Capacity planning teams gain a longitudinal CSV trail of under-provisioned containers aligned with Vertical Pod Autoscaler style studies without waiting for outages.

## Implementation

Deploy Splunk Add-on for Linux with sourcetype=linux:cgroup:limits reading memory.max and cpu.max per container scope, and a docker inspect exporter into index=oti_containers sourcetype=docker:inspect. Publish lookups/container_limit_policy.csv and container_owner.csv weekly. Save container_uc_3_1_17_limit_enforcement every five minutes on earliest=-4h@h latest=@h, route critical tiers to platform and owner_team, archive weekly CSV evidence with policy commit hashes, and keep the comment macro aligned with approved index names.

## Evidence

Saved search container_uc_3_1_17_limit_enforcement; lookups container_limit_policy.csv and container_owner.csv versioned in git; weekly CSV exports to a restricted evidence index with commit hashes; dashboard panels for unlimited counts by environment and declared-versus-enforced drift tables. External references include Docker default unlimited memory case studies in production postmortems, Kubernetes Vertical Pod Autoscaler guidance on under- and over-provisioned containers, NIST SP 800-190 container resource expectations, and CIS Docker Benchmark publications on memory and CPU limits.

## Control test

### Positive scenario

On a lab Linux host, run a container without memory limits while labeling environment as production in the inspect exporter, ingest docker:inspect and linux:cgroup:limits, execute container_uc_3_1_17_limit_enforcement, and expect critical_unlimited_memory_in_production with policy_compliance unlimited_memory_prod.

### Negative scenario

Run nginx:alpine with docker run --memory=512m --cpus=0.5, confirm cgroup files match inspect within three percent, ensure container_limit_policy.csv contains a compliant row for the image and environment, and verify the saved search returns no violation row across multiple intervals.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this Configuration and Compliance control jointly with the Linux observability engineer who certifies Splunk Add-on for Linux scripted inputs and the container platform architect who publishes container_limit_policy.csv from the governance repository. UC-3.1.17 is deliberately the policy-and-enforcement axis: it asks whether each running workload has explicit CPU and memory limits at all, whether those limits satisfy tiered ceilings and floors in a lookup table keyed by image and environment, and whether the kernel cgroup files agree with what docker inspect claims. UC-3.1.3 measures CPU throttling after a hard cap exists; UC-3.1.4 trends memory pressure against an existing finite memory.max; UC-3.1.2 fires when the kernel records oom_kill. None of those siblings replace a governance detector for missing limits, policy ceilings, CpuShares-only soft scheduling without a quota, MemorySwap posture, or silent drift between HostConfig and cgroup v2 files. UC-3.1.6 remains the privilege posture story; UC-3.1.25 remains control-socket exposure; do not merge those narratives here.

You need two indexed sourcetypes on every Linux worker that runs Docker Engine or a Mirantis-compatible runtime. First, docker:inspect JSON flattened from a privileged scripted input that enumerates docker ps -q, runs docker inspect per id (or a batched JSON array), and posts one event per container per poll with stable field aliases for HostConfig.Memory, HostConfig.MemorySwap, HostConfig.NanoCpus, HostConfig.CpuQuota, HostConfig.CpuPeriod, HostConfig.CpuShares, plus Config.Image and normalized container identity fields. Zero in Memory means unlimited; negative MemorySwap values mean Docker defaults that can permit swap behavior your policy forbids; NanoCpus at 1e9 equals one core equivalent for quick mental math. Second, linux:cgroup:limits from a Splunk Add-on for Linux extension or companion script that walks the leaf cgroup Docker attaches (commonly systemd slices named docker-<64hex>.scope under cgroup v2) and reads memory.max and cpu.max as raw strings exactly as the kernel exposes them, including the max token when no cap exists. The collector must not parse away the word max before Splunk sees it, or drift detection collapses.

Publish lookups/container_limit_policy.csv with columns image (registry/repo:tag or pattern key), environment (prod, staging, dev, unknown), mem_min and mem_max in bytes, cpu_min and cpu_max in fractional cores, optional notes, and exception_ticket when finance or risk approves a ceiling breach. Refresh the CSV from the same pipeline that promotes golden images so policy travels with digest pins. Maintain container_owner.csv with host_id, container_name, owner_team for paging parity with sibling UC-3.1.x searches even though this UC keys primarily on container_id.

Risk briefing for executives: one unlimited memory container on a dense host can starve every other cgroup until the host-wide OOM killer chooses victims arbitrarily, which is how customer-visible outages happen without a single deploy touching the applications that die. CpuShares without CpuQuota or NanoCpus is not a cap; it is relative weight, so a noisy neighbor can still monopolize cores under contention while dashboards that only glance at docker stats suggest fairness. Declared versus enforced drift means your CMDB and audit trail say one limit while the kernel enforces another, which breaks isolation proofs for regulators and for internal blameless postmortems.

Licensing and volume: inspect snapshots are larger than single-metric scrapes; cgroup file reads are cheap per interval but multiply by container count. Land both sourcetypes in index=oti_containers with hot retention aligned to security office standards. Legal and privacy: strip environment variable blobs from inspect events at the forwarder when they contain secrets; restrict indexes to platform and compliance roles.

Differentiation recap relative to UC-3.1.3 and UC-3.1.4: those walk-tier Performance searches assume limits exist and interpret scheduler or memory-controller effects. This Compliance search must fire when limits are absent, mis-sized against policy, or lying relative to cgroupfs. Pair them in dashboards but never substitute one for the other.

### Step 2 — Configure data collection

On every Linux worker running cgroup v2 as Docker’s default, install or extend Splunk Add-on for Linux so a scripted input executes every five minutes (or faster during change windows) and, for each running container id, resolves the cgroup path with docker inspect --format '{{.Id}}' combined with systemd-cgls or a documented mapper, then cats memory.max and cpu.max from the leaf scope. Emit sourcetype linux:cgroup:limits with fields host_id, container_id, cgroup_memory_max, cgroup_cpu_max mirroring raw file text, plus cgroup_path for forensic drilldowns. On hybrid v1 estates during migration, either fork a macro that reads memory.limit_in_bytes and cpu.cfs_quota_us until cutover completes, or exclude those hosts in the comment macro until unified hierarchy is live.

Deploy the docker:inspect exporter on the same cadence with HEC or Universal Forwarder routing to index=oti_containers. Normalize host_id to lowercase short hostnames that match linux:cgroup:limits events. Include MemorySwap even when operators rarely tune it: MemorySwap equal to Memory often means swap is disabled for that container, which accelerates OOM under pressure; MemorySwap at -1 can mean unlimited swap allowance depending on daemon version, which is a policy conversation, not a silent default.

Validate on a canary host: docker run --memory=256m --cpus=1.5 --name lab-limited nginx:alpine sleep 3600 should produce positive Memory, NanoCpus near 1.5e9 or equivalent quota math, matching memory.max and cpu.max within one collection interval. docker run --name lab-unlimited nginx:alpine sleep 3600 should produce Memory zero in inspect and memory.max reading max in cgroup v2. Compare Splunk fields to docker inspect and cat /sys/fs/cgroup/.../memory.max manually before promoting the alert.

Security hygiene: the collector account must be non-interactive, vault-stored, and separate from developer laptops. Rotate HEC tokens quarterly. Document Mirantis Container Runtime field deltas after upgrades.

Expected pre-save validations: index=oti_containers sourcetype=docker:inspect earliest=-15m returns HostConfig fragments; sourcetype=linux:cgroup:limits earliest=-15m returns cgroup paths for the same container_id keys. Skew between forwarder clock and host must stay under thirty seconds or drift ratios wobble.

### Step 3 — Create search and alert

Save the SPL as saved search container_uc_3_1_17_limit_enforcement with schedule every five minutes (or fifteen minutes when Job Inspector shows scan pressure) and time range earliest=-4h@h latest=@h so latest stats capture short-lived CI tasks without scanning twenty-four hours of noise. Throttle duplicate critical_declared_vs_enforced_drift pages per host_id and container_id for forty-five minutes unless memory_bytes_enforced flips between max and a finite value inside the hour, which indicates active tampering or migration. Route critical_unlimited_memory_in_production to platform and application owner_team jointly with recommended_response text inline. Archive weekly CSV snapshots of the closing table to your evidence index with git commit hashes for container_limit_policy.csv.

Understanding the pipeline: the opening comment macro records index names, sourcetypes, lookup owners, drift fraction default 0.03, and the explicit complement to Performance siblings UC-3.1.3 and UC-3.1.4. coalesce lists absorb camelCase and snake_case inspect flattening differences across exporter versions. stats latest collapses docker:inspect to one row per host_id and container_id before the join so duplicate poll lines do not multiply severity. The subsearch-wrapped join to linux:cgroup:limits uses type=left max=0 to avoid lookup explosions and preserves raw cpu.max strings in cpu_max_enforced for investigator readability. rex parses quota and period from cgroup v2 cpu.max when both tokens are numeric, deriving enforced_cpu_cores for drift math against declared_cpu_cores from NanoCpus or CpuQuota divided by CpuPeriod. mem_drift_frac and cpu_drift_frac feed mem_drift_hit and cpu_drift_hit gates at three percent relative error; tune via macro if your TA rounds bytes. The join-wrapped inputlookup on container_limit_policy.csv applies mem_min, mem_max, cpu_min, and cpu_max without using a bare lookup command on the main search. prod_like normalizes environment tokens so production-tier policy cannot be bypassed with cosmetic casing. streamstats window=10 sums fleet_unlimited_mem along recent ordered samples per host_id as a coarse unlimited-container trend context column. eventstats perc90(memory_bytes_declared) BY environment supplies fleet percentile context for executive overlays. policy_compliance narrates the violation family; severity maps to the six mandated tier strings; recommended_response encodes runbook hints. The closing table lists fourteen analyst columns including the twelve mandated fields plus fleet_mem_p90 and unlimited_window_sum for trend and fleet context.

Alert actions: attach the row, link to the dashboard described in the visualization field, and include deep links to UC-3.1.2 only when investigators need kernel kill evidence after limits were missing.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:

```spl
`comment("UC-3.1.17 Container Resource Limit Enforcement. Governance axis: docker inspect HostConfig limits vs cgroup v2 files vs container_limit_policy.csv. Tunables: index=oti_containers; sourcetype=docker:inspect and linux:cgroup:limits; join-wrapped inputlookup container_limit_policy.csv on image_key+environment with mem_min mem_max cpu_min cpu_max; mem_drift_frac=0.03; earliest=-4h@h latest=@h.")`
| search index=oti_containers sourcetype="docker:inspect" earliest=-4h@h latest=@h
| eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
| eval container_id=trim(toString(coalesce(container_id, Id, id, containerId, "")))
| eval container_name=trim(toString(coalesce(Name, name, container_name, containerName, "")))
| eval image=trim(toString(coalesce(Config__Image, image, Image, "")))
| eval environment=lower(trim(toString(coalesce(environment, env, tier, deployment_env, labels_env, ""))))
| eval memory_bytes_declared=tonumber(tostring(coalesce(HostConfig_Memory, host_config_memory, memoryBytes, memory_bytes, Memory, "0")), 10)
| eval memory_bytes_declared=coalesce(memory_bytes_declared, memoryBytes)
| eval nano_cpus_declared=tonumber(tostring(coalesce(HostConfig_NanoCpus, host_config_nano_cpus, NanoCpus, nanoCpus, "0")), 10)
| eval nano_cpus_declared=coalesce(nano_cpus_declared, nanoCpus)
| eval cpu_quota=tonumber(tostring(coalesce(HostConfig_CpuQuota, host_config_cpu_quota, CpuQuota, "0")), 10)
| eval cpu_period=tonumber(tostring(coalesce(HostConfig_CpuPeriod, host_config_cpu_period, CpuPeriod, "100000")), 10)
| eval cpu_shares=tonumber(tostring(coalesce(HostConfig_CpuShares, host_config_cpu_shares, CpuShares, "1024")), 10)
| eval memory_swap=tonumber(tostring(coalesce(HostConfig_MemorySwap, host_config_memory_swap, MemorySwap, "-1")), 10)
| eval mem_limit_flag=if(isnotnull(memory_bytes_declared) AND memory_bytes_declared>0, 1, 0)
| eval cpu_hard_cap_flag=if((nano_cpus_declared>0) OR (cpu_quota>0), 1, 0)
| eval declared_cpu_cores=if(nano_cpus_declared>0, nano_cpus_declared/1000000000.0, if(cpu_quota>0 AND cpu_period>0, cpu_quota/cpu_period, null()))
| stats latest(_time) AS last_seen latest(container_name) AS container_name latest(image) AS image latest(environment) AS environment latest(memory_bytes_declared) AS memory_bytes_declared latest(nano_cpus_declared) AS nano_cpus_declared latest(cpu_quota) AS cpu_quota latest(cpu_period) AS cpu_period latest(cpu_shares) AS cpu_shares latest(memory_swap) AS memory_swap latest(mem_limit_flag) AS mem_limit_flag latest(cpu_hard_cap_flag) AS cpu_hard_cap_flag latest(declared_cpu_cores) AS declared_cpu_cores BY host_id, container_id
| join type=left max=0 host_id, container_id [
    search index=oti_containers sourcetype="linux:cgroup:limits" earliest=-4h@h latest=@h
    | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
    | eval container_id=trim(toString(coalesce(container_id, containerId, Id, "")))
    | eval cgroup_memory_max_raw=trim(toString(coalesce(cgroup_memory_max, memory_max_raw, mem_max_file, memoryMaxFile, "")))
    | eval cgroup_cpu_max_raw=trim(toString(coalesce(cgroup_cpu_max, cpu_max_raw, cpuMaxFile, "")))
    | stats latest(cgroup_memory_max_raw) AS cgroup_memory_max_raw latest(cgroup_cpu_max_raw) AS cgroup_cpu_max_raw BY host_id, container_id
  ]
| eval mem_raw_lc=lower(cgroup_memory_max_raw)
| eval memory_bytes_enforced=if(match(mem_raw_lc,"^max$") OR len(mem_raw_lc)==0, null(), tonumber(cgroup_memory_max_raw, 10))
| eval memory_bytes_enforced=coalesce(memory_bytes_enforced, enforced_memory_bytes)
| eval cpu_max_enforced=if(len(trim(cgroup_cpu_max_raw))==0, "unavailable", cgroup_cpu_max_raw)
| rex field=cgroup_cpu_max_raw "^(?<cpu_q_enf>[^\s]+)\s+(?<cpu_p_enf>\d+)$"
| eval enforced_cpu_cores=if(lower(cpu_q_enf)=="max", null(), if(isnotnull(cpu_q_enf) AND isnotnull(cpu_p_enf) AND tonumber(cpu_p_enf,10)>0 AND match(cpu_q_enf,"^[0-9]+$"), tonumber(cpu_q_enf,10)/tonumber(cpu_p_enf,10), null()))
| eval mem_drift_frac=if(isnotnull(memory_bytes_declared) AND memory_bytes_declared>0 AND isnotnull(memory_bytes_enforced) AND memory_bytes_enforced>0, abs(memory_bytes_declared - memory_bytes_enforced) / memory_bytes_declared, null())
| eval cpu_drift_frac=if(isnotnull(declared_cpu_cores) AND declared_cpu_cores>0 AND isnotnull(enforced_cpu_cores) AND enforced_cpu_cores>0, abs(declared_cpu_cores - enforced_cpu_cores) / declared_cpu_cores, null())
| eval mem_drift_hit=if(isnotnull(mem_drift_frac) AND mem_drift_frac>0.03, 1, 0)
| eval cpu_drift_hit=if(isnotnull(cpu_drift_frac) AND cpu_drift_frac>0.03, 1, 0)
| eval image_key=lower(trim(image))
| eval environment=if(isnull(environment) OR len(environment)==0, "unknown", environment)
| join type=left max=0 image_key, environment [
    | inputlookup container_limit_policy.csv
    | eval image_key=lower(trim(toString(coalesce(image, image_ref, Image, ""))))
    | eval environment=lower(trim(toString(coalesce(environment, env, tier, ""))))
    | eval mem_min=tonumber(tostring(coalesce(mem_min, mem_min_bytes, "0")), 10)
    | eval mem_max=tonumber(tostring(coalesce(mem_max, mem_max_bytes, "0")), 10)
    | eval cpu_min=tonumber(tostring(coalesce(cpu_min, cpu_min_cores, "0")), 10)
    | eval cpu_max=tonumber(tostring(coalesce(cpu_max, cpu_max_cores, "0")), 10)
    | fields image_key environment mem_min mem_max cpu_min cpu_max
  ]
| eval prod_like=if(match(environment, "(?i)^prod$|^production$|^tier0$|^tier_0$|^mission$"), 1, 0)
| eval fleet_unlimited_mem=if(mem_limit_flag=0, 1, 0)
| sort 0 + host_id, container_id, last_seen
| streamstats window=10 current=t global=f sum(fleet_unlimited_mem) AS unlimited_window_sum BY host_id
| eventstats perc90(memory_bytes_declared) AS fleet_mem_p90 perc50(declared_cpu_cores) AS fleet_cpu_p50 BY environment
| eval policy_compliance=case(
    mem_drift_hit=1 OR cpu_drift_hit=1, "declared_vs_enforced_mismatch",
    mem_limit_flag=0 AND prod_like=1, "unlimited_memory_prod",
    cpu_hard_cap_flag=0 AND prod_like=1, "no_hard_cpu_cap_prod",
    isnotnull(mem_max) AND mem_max>0 AND memory_bytes_declared>mem_max, "above_memory_ceiling",
    isnotnull(cpu_max) AND cpu_max>0 AND isnotnull(declared_cpu_cores) AND declared_cpu_cores>cpu_max, "above_cpu_ceiling",
    isnotnull(mem_min) AND mem_min>0 AND memory_bytes_declared>0 AND memory_bytes_declared<mem_min, "below_memory_floor",
    isnotnull(cpu_min) AND cpu_min>0 AND isnotnull(declared_cpu_cores) AND declared_cpu_cores<cpu_min, "below_cpu_floor",
    mem_limit_flag=0 AND prod_like=0, "unlimited_memory_nonprod",
    true(), "compliant_or_review")
| eval severity=case(
    mem_drift_hit=1 OR cpu_drift_hit=1, "critical_declared_vs_enforced_drift",
    mem_limit_flag=0 AND prod_like=1, "critical_unlimited_memory_in_production",
    (isnotnull(mem_max) AND mem_max>0 AND memory_bytes_declared>mem_max) OR (isnotnull(cpu_max) AND cpu_max>0 AND isnotnull(declared_cpu_cores) AND declared_cpu_cores>cpu_max), "high_above_policy_ceiling",
    cpu_hard_cap_flag=0 AND prod_like=1, "high_legacy_cpushares_only_no_hard_cap",
    (isnotnull(mem_min) AND mem_min>0 AND memory_bytes_declared>0 AND memory_bytes_declared<mem_min) OR (isnotnull(cpu_min) AND cpu_min>0 AND isnotnull(declared_cpu_cores) AND declared_cpu_cores<cpu_min), "medium_below_policy_floor_underprovisioned",
    (mem_limit_flag=0 AND prod_like=0) OR (cpu_hard_cap_flag=0 AND prod_like=0), "low_baseline_drift",
    true(), null())
| where isnotnull(severity) AND NOT match(policy_compliance, "compliant_or_review")
| eval recommended_response=case(
    severity="critical_unlimited_memory_in_production", "Set explicit memory limits (--memory) for this production container; open emergency change to cap RSS and validate cgroup memory.max matches inspect after recycle.",
    severity="critical_declared_vs_enforced_drift", "Investigate cgroup driver mismatch, rootless delegation, or privileged remount; reconcile forwarder paths for memory.max and cpu.max with docker-<id>.scope; open break-fix ticket for runtime isolation.",
    severity="high_above_policy_ceiling", "Reduce limits to policy maximums in container_limit_policy.csv or request CAB-approved policy exception with FinOps sign-off.",
    severity="high_legacy_cpushares_only_no_hard_cap", "Replace CpuShares-only posture with NanoCpus or CpuQuota/CpuPeriod hard cap; document burst allowance; pair with UC-3.1.3 only after caps exist.",
    severity="medium_below_policy_floor_underprovisioned", "Raise limits toward policy floor in container_limit_policy.csv or lower the floor after capacity review; attach load-test or autoscaler evidence.",
    severity="low_baseline_drift", "Schedule non-prod cleanup: add limits before promotion; tag sandbox workloads in policy lookup exemptions.",
    true(), "Re-run after policy CSV refresh; correlate with UC-3.1.4 memory pressure only if limits exist.")
| table container_id container_name image host_id environment memory_bytes_declared memory_bytes_enforced nano_cpus_declared cpu_max_enforced policy_compliance severity recommended_response fleet_mem_p90 unlimited_window_sum
```
### Step 4 — Validate

Positive path A — unlimited production: on a disposable lab host tagged environment=production in inspect labels or your exporter’s environment field, run a container without --memory, ingest both sourcetypes, execute the saved search, and expect critical_unlimited_memory_in_production with policy_compliance unlimited_memory_prod. Remove the container immediately after capture.

Positive path B — declared versus enforced drift: run a container with --memory=128m, then manually echo a different finite value into memory.max inside a permitted lab cgroup namespace or simulate with a faulty collector that posts stale bytes while inspect updates, and confirm critical_declared_vs_enforced_drift when drift exceeds three percent. Do not perform manual cgroup writes in production without change control.

Positive path C — policy ceiling breach: add a container_limit_policy.csv row with mem_max below the declared limit for a lab image, refresh the lookup, and expect high_above_policy_ceiling.

Positive path D — CpuShares only: start a production-class workload without --cpus or quota while CpuShares remains default, confirm cpu_hard_cap_flag evaluates zero, and expect high_legacy_cpushares_only_no_hard_cap.

Negative path — compliant limited workload: run nginx:alpine with --memory=512m and --cpus=0.5, ensure cgroup files match, ensure policy row allows the band, and verify the saved search emits no row after the compliant_or_review filter.

Field sanity: rename HostConfig_Memory to memory-only camelCase in a sandbox forwarder and confirm coalesce still resolves memory_bytes_declared. RBAC: readers without index=oti_containers must see zero results.

Correlation: when UC-3.1.2 fires, pivot backward with this search over the prior hour; investigators often find unlimited_memory_prod rows that explain why the kernel faced an unbounded RSS spike.

### Step 5 — Operationalize and troubleshoot

Case 1 — linux:cgroup:limits arm empty while inspect flows: scripted input lost cgroup path after Docker upgrade; verify systemd slice names with systemd-cgls, confirm rootless delegation under user.slice, and update path discovery. Remediation is collector fix, not alert suppression.

Case 2 — Join to container_limit_policy.csv misses: image_key mismatch because registry includes digest while CSV uses floating tag; normalize to repo:tag or pin digest columns with parallel rows. Remediation is CSV publisher alignment.

Case 3 — False critical drift during cgroup v1 to v2 migration: both hierarchies briefly scraped; gate with host_class macro selecting active hierarchy only. Remediation is single-hierarchy collection per partition.

Case 4 — MemorySwap policy debates: unlimited swap allowance flags appear as informational columns in dashboards; route MemorySwap=-1 rows to the security and capacity council rather than paging application on-call unless prod_like triggers a ceiling violation.

Case 5 — Batch ETL temporary unlimited grants: add exception_ticket and environment=prod rows with mem_max override columns or a parallel policy_exception.csv join referenced in a wrapper macro so FinOps retains visibility.

Case 6 — Vendor images with internal caps operators cannot raise: document in knownFalsePositives and add image_allow rows that still require inspect limits even when policy floor exceeds vendor defaults.

Case 7 — streamstats unlimited_window_sum noisy on bursty CI hosts: increase window or exclude builder host classes via macro commenting in the saved search description.

Case 8 — cpu.max parsing fails on custom cgroupfs builds: extend rex in a development app first; keep cpu_max_enforced raw string for manual reads during incidents.

Case 9 — Dual OTel and TA writers duplicate inspect: deduplicate on container_id and _time within two seconds before stats latest. Remediation is single writer per node class.

Case 10 — environment field always unknown: enrich inspect exporter from Compose labels com.example.environment or Kubernetes namespace maps if your estate mixes orchestrators; unknown environment must not silently inherit production severities—treat prod_like false until enrichment lands.

Dashboard publishing: follow the visualization field with a timechart of count of mem_limit_flag=0 split by environment, a declared versus enforced drift table with cell coloring on mem_drift_frac, and a bar chart of policy_compliance categories by image. Annotate when container_limit_policy.csv commits land.

Evidence retention: weekly CSV exports with lookup hashes satisfy PCI DSS change-monitoring samples, SOC 2 CC6.6 operational reviews, and ISO 27001 A.12.1.3 capacity-and-change narratives when paired with tickets.

Governance: quarterly replay one historical host OOM incident through this SPL after Engine or kernel upgrades; update the comment macro when indexes move.

Closing checklist: monitoringType lists Configuration and Compliance; splunkPillar Observability; cimModels lists Change and Inventory; equipment lists docker and linux; equipmentModels lists docker_engine and linux_cgroup_v2; five step headers use plain em dashes; Step 3 fenced SPL matches the spl field exactly; Step 5 lists at least eight numbered cases; narrative JSON fields contain no asterisk emphasis pairs; references span Docker resource constraints, docker inspect CLI, kernel cgroup v2, CIS Docker Benchmark landing, Splunk Lantern OpenTelemetry Docker article, and NIST SP 800-190; implementation field stays at or below six hundred characters.

Supplemental notes for long-term owners: when finance challenges ingest cost, compare license bytes for inspect plus cgroup polls to the expected cost of one unlimited-container incident on a full host. When legal requests litigation holds, include inspect JSON, cgroup raw lines, and policy CSV versions in preservation scope. When automating remediation, never silently raise limits in regulated zones without human approval. When training new responders, teach that UC-3.1.3 throttle charts are meaningless until this UC proves a hard cap exists. When Splunk Cloud autoscaling changes, revalidate schedule overlap so five-minute windows do not stack. When rootless Docker becomes default, revalidate cgroup path discovery quarterly. When integrating Splunk Enterprise Security, map severity strings to risk scores with critical drift tiers weighted above routine non-prod drift. When OT edge gateways run Docker, duplicate policy rows with OT-specific floors that reflect constrained RAM SKUs. When service meshes add sidecars, expect additive container counts that amplify poll volume without changing isolation semantics. When closing incidents, record whether fix was policy CSV update, compose change, daemon flag, or kernel migration.



## SPL

```spl
`comment("UC-3.1.17 Container Resource Limit Enforcement. Governance axis: docker inspect HostConfig limits vs cgroup v2 files vs container_limit_policy.csv. Tunables: index=oti_containers; sourcetype=docker:inspect and linux:cgroup:limits; join-wrapped inputlookup container_limit_policy.csv on image_key+environment with mem_min mem_max cpu_min cpu_max; mem_drift_frac=0.03; earliest=-4h@h latest=@h.")`
| search index=oti_containers sourcetype="docker:inspect" earliest=-4h@h latest=@h
| eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
| eval container_id=trim(toString(coalesce(container_id, Id, id, containerId, "")))
| eval container_name=trim(toString(coalesce(Name, name, container_name, containerName, "")))
| eval image=trim(toString(coalesce(Config__Image, image, Image, "")))
| eval environment=lower(trim(toString(coalesce(environment, env, tier, deployment_env, labels_env, ""))))
| eval memory_bytes_declared=tonumber(tostring(coalesce(HostConfig_Memory, host_config_memory, memoryBytes, memory_bytes, Memory, "0")), 10)
| eval memory_bytes_declared=coalesce(memory_bytes_declared, memoryBytes)
| eval nano_cpus_declared=tonumber(tostring(coalesce(HostConfig_NanoCpus, host_config_nano_cpus, NanoCpus, nanoCpus, "0")), 10)
| eval nano_cpus_declared=coalesce(nano_cpus_declared, nanoCpus)
| eval cpu_quota=tonumber(tostring(coalesce(HostConfig_CpuQuota, host_config_cpu_quota, CpuQuota, "0")), 10)
| eval cpu_period=tonumber(tostring(coalesce(HostConfig_CpuPeriod, host_config_cpu_period, CpuPeriod, "100000")), 10)
| eval cpu_shares=tonumber(tostring(coalesce(HostConfig_CpuShares, host_config_cpu_shares, CpuShares, "1024")), 10)
| eval memory_swap=tonumber(tostring(coalesce(HostConfig_MemorySwap, host_config_memory_swap, MemorySwap, "-1")), 10)
| eval mem_limit_flag=if(isnotnull(memory_bytes_declared) AND memory_bytes_declared>0, 1, 0)
| eval cpu_hard_cap_flag=if((nano_cpus_declared>0) OR (cpu_quota>0), 1, 0)
| eval declared_cpu_cores=if(nano_cpus_declared>0, nano_cpus_declared/1000000000.0, if(cpu_quota>0 AND cpu_period>0, cpu_quota/cpu_period, null()))
| stats latest(_time) AS last_seen latest(container_name) AS container_name latest(image) AS image latest(environment) AS environment latest(memory_bytes_declared) AS memory_bytes_declared latest(nano_cpus_declared) AS nano_cpus_declared latest(cpu_quota) AS cpu_quota latest(cpu_period) AS cpu_period latest(cpu_shares) AS cpu_shares latest(memory_swap) AS memory_swap latest(mem_limit_flag) AS mem_limit_flag latest(cpu_hard_cap_flag) AS cpu_hard_cap_flag latest(declared_cpu_cores) AS declared_cpu_cores BY host_id, container_id
| join type=left max=0 host_id, container_id [
    search index=oti_containers sourcetype="linux:cgroup:limits" earliest=-4h@h latest=@h
    | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
    | eval container_id=trim(toString(coalesce(container_id, containerId, Id, "")))
    | eval cgroup_memory_max_raw=trim(toString(coalesce(cgroup_memory_max, memory_max_raw, mem_max_file, memoryMaxFile, "")))
    | eval cgroup_cpu_max_raw=trim(toString(coalesce(cgroup_cpu_max, cpu_max_raw, cpuMaxFile, "")))
    | stats latest(cgroup_memory_max_raw) AS cgroup_memory_max_raw latest(cgroup_cpu_max_raw) AS cgroup_cpu_max_raw BY host_id, container_id
  ]
| eval mem_raw_lc=lower(cgroup_memory_max_raw)
| eval memory_bytes_enforced=if(match(mem_raw_lc,"^max$") OR len(mem_raw_lc)==0, null(), tonumber(cgroup_memory_max_raw, 10))
| eval memory_bytes_enforced=coalesce(memory_bytes_enforced, enforced_memory_bytes)
| eval cpu_max_enforced=if(len(trim(cgroup_cpu_max_raw))==0, "unavailable", cgroup_cpu_max_raw)
| rex field=cgroup_cpu_max_raw "^(?<cpu_q_enf>[^\s]+)\s+(?<cpu_p_enf>\d+)$"
| eval enforced_cpu_cores=if(lower(cpu_q_enf)=="max", null(), if(isnotnull(cpu_q_enf) AND isnotnull(cpu_p_enf) AND tonumber(cpu_p_enf,10)>0 AND match(cpu_q_enf,"^[0-9]+$"), tonumber(cpu_q_enf,10)/tonumber(cpu_p_enf,10), null()))
| eval mem_drift_frac=if(isnotnull(memory_bytes_declared) AND memory_bytes_declared>0 AND isnotnull(memory_bytes_enforced) AND memory_bytes_enforced>0, abs(memory_bytes_declared - memory_bytes_enforced) / memory_bytes_declared, null())
| eval cpu_drift_frac=if(isnotnull(declared_cpu_cores) AND declared_cpu_cores>0 AND isnotnull(enforced_cpu_cores) AND enforced_cpu_cores>0, abs(declared_cpu_cores - enforced_cpu_cores) / declared_cpu_cores, null())
| eval mem_drift_hit=if(isnotnull(mem_drift_frac) AND mem_drift_frac>0.03, 1, 0)
| eval cpu_drift_hit=if(isnotnull(cpu_drift_frac) AND cpu_drift_frac>0.03, 1, 0)
| eval image_key=lower(trim(image))
| eval environment=if(isnull(environment) OR len(environment)==0, "unknown", environment)
| join type=left max=0 image_key, environment [
    | inputlookup container_limit_policy.csv
    | eval image_key=lower(trim(toString(coalesce(image, image_ref, Image, ""))))
    | eval environment=lower(trim(toString(coalesce(environment, env, tier, ""))))
    | eval mem_min=tonumber(tostring(coalesce(mem_min, mem_min_bytes, "0")), 10)
    | eval mem_max=tonumber(tostring(coalesce(mem_max, mem_max_bytes, "0")), 10)
    | eval cpu_min=tonumber(tostring(coalesce(cpu_min, cpu_min_cores, "0")), 10)
    | eval cpu_max=tonumber(tostring(coalesce(cpu_max, cpu_max_cores, "0")), 10)
    | fields image_key environment mem_min mem_max cpu_min cpu_max
  ]
| eval prod_like=if(match(environment, "(?i)^prod$|^production$|^tier0$|^tier_0$|^mission$"), 1, 0)
| eval fleet_unlimited_mem=if(mem_limit_flag=0, 1, 0)
| sort 0 + host_id, container_id, last_seen
| streamstats window=10 current=t global=f sum(fleet_unlimited_mem) AS unlimited_window_sum BY host_id
| eventstats perc90(memory_bytes_declared) AS fleet_mem_p90 perc50(declared_cpu_cores) AS fleet_cpu_p50 BY environment
| eval policy_compliance=case(
    mem_drift_hit=1 OR cpu_drift_hit=1, "declared_vs_enforced_mismatch",
    mem_limit_flag=0 AND prod_like=1, "unlimited_memory_prod",
    cpu_hard_cap_flag=0 AND prod_like=1, "no_hard_cpu_cap_prod",
    isnotnull(mem_max) AND mem_max>0 AND memory_bytes_declared>mem_max, "above_memory_ceiling",
    isnotnull(cpu_max) AND cpu_max>0 AND isnotnull(declared_cpu_cores) AND declared_cpu_cores>cpu_max, "above_cpu_ceiling",
    isnotnull(mem_min) AND mem_min>0 AND memory_bytes_declared>0 AND memory_bytes_declared<mem_min, "below_memory_floor",
    isnotnull(cpu_min) AND cpu_min>0 AND isnotnull(declared_cpu_cores) AND declared_cpu_cores<cpu_min, "below_cpu_floor",
    mem_limit_flag=0 AND prod_like=0, "unlimited_memory_nonprod",
    true(), "compliant_or_review")
| eval severity=case(
    mem_drift_hit=1 OR cpu_drift_hit=1, "critical_declared_vs_enforced_drift",
    mem_limit_flag=0 AND prod_like=1, "critical_unlimited_memory_in_production",
    (isnotnull(mem_max) AND mem_max>0 AND memory_bytes_declared>mem_max) OR (isnotnull(cpu_max) AND cpu_max>0 AND isnotnull(declared_cpu_cores) AND declared_cpu_cores>cpu_max), "high_above_policy_ceiling",
    cpu_hard_cap_flag=0 AND prod_like=1, "high_legacy_cpushares_only_no_hard_cap",
    (isnotnull(mem_min) AND mem_min>0 AND memory_bytes_declared>0 AND memory_bytes_declared<mem_min) OR (isnotnull(cpu_min) AND cpu_min>0 AND isnotnull(declared_cpu_cores) AND declared_cpu_cores<cpu_min), "medium_below_policy_floor_underprovisioned",
    (mem_limit_flag=0 AND prod_like=0) OR (cpu_hard_cap_flag=0 AND prod_like=0), "low_baseline_drift",
    true(), null())
| where isnotnull(severity) AND NOT match(policy_compliance, "compliant_or_review")
| eval recommended_response=case(
    severity="critical_unlimited_memory_in_production", "Set explicit memory limits (--memory) for this production container; open emergency change to cap RSS and validate cgroup memory.max matches inspect after recycle.",
    severity="critical_declared_vs_enforced_drift", "Investigate cgroup driver mismatch, rootless delegation, or privileged remount; reconcile forwarder paths for memory.max and cpu.max with docker-<id>.scope; open break-fix ticket for runtime isolation.",
    severity="high_above_policy_ceiling", "Reduce limits to policy maximums in container_limit_policy.csv or request CAB-approved policy exception with FinOps sign-off.",
    severity="high_legacy_cpushares_only_no_hard_cap", "Replace CpuShares-only posture with NanoCpus or CpuQuota/CpuPeriod hard cap; document burst allowance; pair with UC-3.1.3 only after caps exist.",
    severity="medium_below_policy_floor_underprovisioned", "Raise limits toward policy floor in container_limit_policy.csv or lower the floor after capacity review; attach load-test or autoscaler evidence.",
    severity="low_baseline_drift", "Schedule non-prod cleanup: add limits before promotion; tag sandbox workloads in policy lookup exemptions.",
    true(), "Re-run after policy CSV refresh; correlate with UC-3.1.4 memory pressure only if limits exist.")
| table container_id container_name image host_id environment memory_bytes_declared memory_bytes_enforced nano_cpus_declared cpu_max_enforced policy_compliance severity recommended_response fleet_mem_p90 unlimited_window_sum
```

## CIM SPL

```spl
| tstats summariesonly=true count FROM datamodel=Change WHERE nodename=Change.All_Changes earliest=-24h latest=now BY All_Changes.object All_Changes.action | head 200
```

## Visualization

Timechart of unlimited-memory container count by environment; sortable declared-versus-enforced drift table with mem_drift_frac coloring; bar chart of policy_compliance distribution by image; optional MemorySwap and CpuShares companion panel for governance reviews.

## Known False Positives

Legitimate developer laptops and shared sandbox clusters often run unlimited memory by design; route those hosts through environment tags that never set prod_like unless mis-labeled. Infrastructure agents such as logging forwarders, service-mesh sidecars, and hardware telemetry exporters sometimes ship vendor Dockerfiles without limits until platform teams standardize helm-like wrappers; allowlist them with ticket-backed rows rather than muting the search globally. Containers mid-migration between staging and production tiers can briefly appear under the wrong environment key; reconcile labels before treating ceiling breaches as malicious. Planned load-test windows that temporarily lift limits should carry time-bounded policy_exception metadata referenced in a wrapper macro. Vendor-supplied images may embed runtime-enforced ceilings that differ from operator-supplied docker run flags; pair vendor documentation with inspect output before opening Sev-1 drift tickets. Rootless Docker and cgroup namespace views can make collectors read parent max while inspect shows child limits until path discovery follows delegated subtrees; expect one noisy interval after major upgrades. CI executors that spawn thousands of short-lived ids may miss cgroup polls between creation and teardown; tune host-class macros for builder fleets. Mirantis Container Runtime field renames after patches can cause coalesce misses that resemble policy drift until props aliases refresh. Dual ingestion from experimental eBPF exporters alongside Splunk_TA_nix without deduplication can double-count drift; enforce a single primary writer per node class.

## References

- [Docker Docs — container resource constraints](https://docs.docker.com/config/containers/resource_constraints/)
- [Docker Docs — docker inspect CLI reference](https://docs.docker.com/engine/reference/commandline/inspect/)
- [Linux kernel admin guide — cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html)
- [CIS Docker Benchmark — community program landing](https://www.cisecurity.org/benchmark/docker)
- [Splunk Lantern — Getting Docker log data into Splunk Cloud Platform with OpenTelemetry](https://lantern.splunk.com/Platform_Data_Management/Unlock_Insights/Getting_Docker_log_data_into_Splunk_Cloud_Platform_with_OpenTelemetry)
- [NIST SP 800-190 — Application Container Security Guide](https://csrc.nist.gov/publications/detail/sp/800-190/final)
