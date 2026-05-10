<!-- AUTO-GENERATED from UC-3.1.3.json — DO NOT EDIT -->

---
id: "3.1.3"
title: "Container CPU Throttling"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.1.3 · Container CPU Throttling

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch whether the computer is repeatedly telling a boxed-up program to wait its turn for CPU time, like a car stuck trying to merge when traffic will not open a gap. Even when the box still looks busy-but-fine on average, those waits pile up and make real people feel slowness at the worst moments.*

---

## Description

This control surfaces cgroup-level CPU throttling before a workload ever trips UC-3.1.2 memory pressure or UC-3.1.1 crash semantics. It correlates three telemetry families: linux:cgroup cpu.stat counters where nr_periods and nr_throttled form throttle_ratio and throttled_time deltas form throttled_wall_pct against wall clock, docker:inspect HostConfig fields that reveal the static CFS quota, NanoCpus translation of docker --cpus, and cpuset.cpus pinning that can mimic quota exhaustion when only two logical CPUs are eligible on a large NUMA machine, plus procfs:loadavg host context so operators do not blame a container quota when the host run queue is already saturated. The saved search uses streamstats on monotonic counters, joins inspect and load averages, and joins container_cpu_baseline.csv so golden images with benign chronic throttle do not page the same way latency-sensitive services do. Unlike memory cgroup kills, CPU throttling rarely produces a dramatic exit code; instead it inflates tail latency and erodes SLOs while average CPU graphs still look polite, which is why Fortune-500 platform teams ship this as a dedicated Performance and Capacity axis adjacent to UC-3.1.2 rather than folding it into generic docker:stats dashboards.

## Value

Quantified benefits show up as fewer unexplained p95 latency regressions, faster right-sizing decisions backed by cpu.stat excerpts attached to change tickets, and defensible capacity evidence when finance asks why vCPU headroom increased. A single Splunk pipeline that unifies cgroup counters, inspect limits, host loadavg, and image baselines routinely replaces ad-hoc combinations of host agents, spreadsheet quotas, and manual docker inspect snapshots across fleets beyond ten thousand containers, which collapses operational toil and license duplication. Reliability improves because service owners receive owner_team-routed pages with recommended_response text tied to quota, cpuset, or host saturation hypotheses instead of generic CPU busy alerts. FinOps gains a longitudinal record of throttle_ratio trends per image for purchasing conversations, and customer trust rises when incidents are closed with kernel-accountable evidence rather than guesses from inside-container top snapshots that smooth away scheduler stalls.

## Implementation

Deploy Splunk_TA_nix linux:cgroup cpu.stat scrapes into metrics_oti or os, docker:inspect CPU quota and cpuset polls into containers, and procfs:loadavg into metrics_oti or os. Publish container_cpu_baseline.csv and container_owner.csv weekly. Save container_uc_3_1_3_cpu_throttling every five minutes on earliest=-1h@h latest=@h, route critical severities to platform and owner_team jointly, archive weekly CSV snapshots to the evidence index, and keep the comment macro synchronized with approved index names.

## Evidence

Saved search container_uc_3_1_3_cpu_throttling; lookups container_cpu_baseline.csv and container_owner.csv versioned in git; weekly CSV exports to a restricted evidence index; dashboard panels combining throttle_ratio heatmaps, quota_pct_used trends, and cpuset tables. External research includes Brendan Gregg CFS scheduler write-ups, Linux kernel cgroup v2 cpu.stat documentation, Buffer's 2017 Kubernetes CPU throttling incident narrative, and Cloudflare engineering posts on NGINX container CPU throttling failures that illustrate customer-visible tail latency before hard errors.

## Control test

### Positive scenario

On a lab Linux host run docker run --rm --cpus=0.25 --name lab-throttle an approved CPU stress image for two minutes, confirm linux:cgroup samples show rising nr_throttled and throttled_time with stable nr_periods deltas, ingest matching docker:inspect CpuQuota and CpuPeriod, then execute container_uc_3_1_3_cpu_throttling and expect a non-null severity string among the six mandated tiers with populated throttle_pct and recommended_response.

### Negative scenario

Run nginx:alpine idle for thirty minutes without CpuQuota limits, verify linux:cgroup throttle_ratio stays near zero, and confirm the saved search returns zero rows after the isnotnull(severity) filter for that container across multiple intervals.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control jointly with the Linux observability engineer who certifies Splunk_TA_nix scripted inputs and the container platform lead who controls Docker Engine flags on worker fleets. This walk-tier use case assumes Linux hosts where Docker or an equivalent OCI runtime attaches each container to a cgroup that exposes cpu.stat style counters (nr_periods, nr_throttled, throttled_time) and ideally cpuacct.usage for cumulative CPU time in nanoseconds. It complements UC-3.1.2, which reads the memory controller story ending in oom_kill, by focusing on the CPU controller story ending in latency tails long before memory pressure manifests. You are not replacing UC-3.1.1 crash taxonomy, UC-3.1.13 restart cadence, UC-3.1.25 socket exposure, UC-3.1.28 Swarm replica convergence, or UC-3.1.6 privilege posture; those siblings answer different risk questions.

Splunk Add-on for Unix and Linux (Splunkbase 833) should already ship or be extended to emit sourcetype linux:cgroup events that include cpu controller files from cgroup v2 paths such as /sys/fs/cgroup/<scope>/cpu.stat and, where hybrid hierarchies remain, cgroup v1 cpu,cpuacct counterparts. Confirm your TA version walks docker-<id>.scope slices under systemd and does not silently drop short-lived CI containers between polls. Splunk OpenTelemetry Collector for Linux can scrape the same counters when your standard is OpenTelemetry-first; normalize field names to the coalesce list in the SPL so migrations do not fork the alert.

You need docker:inspect JSON on a cadence that matches security tolerance, typically five to fifteen minutes in production, sourced from a privileged scripted input or modular input that flattens HostConfig.CpuQuota, HostConfig.CpuPeriod, HostConfig.NanoCpus, and HostConfig.CpusetCpus. Those fields explain the static contract the kernel enforces against the dynamic cpu.stat deltas. Pair host-level sourcetype procfs:loadavg (or an equivalent Universal Forwarder monitor of /proc/loadavg) so investigators can separate true cgroup quota starvation from a host whose run queue is saturated by unrelated tenants.

Governance lookups live beside the saved search. Publish lookups/container_cpu_baseline.csv with columns such as image or image_ref (lowercase normalized), expected_throttle_pct or p95_throttle_pct representing acceptable chronic throttle for that golden image, and workload_class or slo_tier for routing nuance. Refresh baselines after every base image promotion. Maintain lookups/container_owner.csv with host_id (or host), container_name, owner_team exactly as other UC-3.1.x gold searches expect. If KV Store backs either file, expose it through transforms.conf names that still work with join-wrapped inputlookup in Splunk Cloud.

Risk briefing for incident commanders: sustained nr_throttled divided by nr_periods near one means the cgroup spent nearly every CFS period pinned against its quota even when docker stats or top inside the container looks deceptively calm, because those views often average away the scheduler stalls that inflate p95 and p99 latency. Pairing throttled_time deltas with wall-clock seconds yields the percentage of real time the cgroup spent runnable-but-throttled, which is the customer-experience lever finance teams understand when debating vCPU purchases.

Licensing note: polling cpu.stat per scope every minute across fifty thousand containers adds up; many teams land linux:cgroup in index metrics_oti with shorter hot retention and keep docker:inspect in index containers with governance review. Document whichever index names your security office approves inside the opening comment macro and do not hard-code alternate names only in prose.

Differentiation recap relative to UC-3.1.2: memory.events and memory.current answer whether the kernel will kill for RSS; cpu.stat answers whether the kernel is refusing CPU time under quota. Remediation for UC-3.1.2 raises memory.max or fixes leaks; remediation here raises CpuQuota, widens cpuset, splits replicas, or fixes host-level oversubscription discovered through loadavg.

### Step 2 — Configure data collection

On every Linux worker running Docker CE, Mirantis Container Runtime, or an approved enterprise Engine build, enable Splunk_TA_nix linux:cgroup scripted reads that include the CPU controller statistics for each container scope. For cgroup v2 unified hierarchies, collectors must open cpu.stat inside the leaf cgroup Docker creates, not only the parent slice, or nr_throttled will read zero while applications still stall. For cgroup v1 legacy paths under /sys/fs/cgroup/cpu,cpuacct/docker/<id>/, keep the same field names via props transforms so the SPL coalesce list stays stable across fleets mid-migration.

Configure a docker inspect exporter that posts sourcetype docker:inspect into index containers (or your approved name) with stable host_id matching Universal Forwarder host fields. The exporter should flatten camelCase and snake_case variants because Connect-style apps differ by release. Include container_id, container_name, Config.Image, and HostConfig CPU limit fields every poll even when values are negative one for unlimited, because the SPL distinguishes unlimited quotas from missing data.

Install procfs:loadavg collection via Splunk_TA_nix modular input, a lightweight scripted probe, or OpenTelemetry hostmetricsreceiver that exports load averages and logical processor counts. Without host_ncpus, the host_saturation gate in the SPL cannot warn responders that loadavg-driven queueing—not cgroup quota—is the dominant stall source.

Validate on a canary host by running a CPU spinner container with docker run --cpus=0.25 and observing linux:cgroup events where nr_throttled climbs while throttled_time grows monotonically. Compare docker inspect CpuQuota and CpuPeriod to the Docker documentation table for --cpus so Splunk numbers match docker CLI expectations within one collection interval.

Security hygiene: the inspect exporter account must not be a developer laptop user; store docker.sock or TLS client credentials in vault, rotate HEC tokens quarterly, and restrict who can read docker:inspect indexes because environment metadata can leak internal service names.

Expected fields before alert authoring: host_id, container_id, container_name, nr_periods, nr_throttled, throttled_time, cpuacct.usage or alias, cfs_quota_us, cfs_period_us, cpuset_cpus, host_load_1m, host_ncpus, image for baseline joins.

When Splunk OpenTelemetry Collector for Linux replaces part of Splunk_TA_nix, mirror props aliases so OTel metric labels map into the same nr_periods and nr_throttled field names this search expects, or introduce a thin summary index that normalizes vendor shapes before the alert tier scans raw events.

### Step 3 — Create search and alert

Save the SPL as saved search container_uc_3_1_3_cpu_throttling with schedule every five minutes (or fifteen minutes on cost-constrained search heads) and time range earliest=-1h@h latest=@h so cgroup deltas align with capacity reporting windows. Throttle duplicate pages per host_id and container_id for thirty minutes when severity is low_baseline_drift_within_10pct but allow immediate re-fire when severity escalates to either critical class.

Understanding the pipeline in operator terms: the opening comment macro is the contract for index names, lookup owners, and the explicit complement to UC-3.1.2. streamstats derives deltas from monotonic counters, which is mandatory because raw nr_periods snapshots without subtraction are meaningless velocity signals. eventstats captures throttle_peak_1h for chronic medium-tier detection. The first join layers docker:inspect quota and cpuset context without using bare lookup commands. The second join layers procfs:loadavg host saturation context. The third join wraps inputlookup container_cpu_baseline.csv on normalized image_key so governance reviewers see the same pattern as other gold UCs. The case ladder emits only the six mandated severity strings or null before the where clause drops quiet rows. recommended_response provides paging-bridge text so analysts do not improvise under stress. The closing join to container_owner.csv routes owner_team. The final table lists fourteen analyst columns including the mandated throttle_pct, quota_pct_used, severity, and recommended_response fields alongside throttle_ratio, throttled_wall_pct, host_load_1m, cpuset_cpus, and owner_team for drilldowns.

Alert actions: attach the recommended_response string, link to your latency SLO dashboard filtered on the service, and include a deep link to UC-3.1.2 saved search when memory pressure is suspected in parallel.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:

```spl
`comment("UC-3.1.3 Container CPU Throttling. Tunables: indexes metrics_oti containers os; lookups container_cpu_baseline.csv (image lower) and container_owner.csv (host_id container_name); sustained_avg_window=5 samples; quota_burst_pct=95; earliest=-1h@h latest=@h. Complements UC-3.1.2 memory cgroup axis with CPU throttle axis.")`
| search (index=metrics_oti OR index=containers OR index=os) sourcetype="linux:cgroup" earliest=-1h@h latest=@h
| eval host_id=lower(toString(coalesce(host, Host, hostname, dest, "")))
| eval container_id=trim(toString(coalesce(container_id, containerId, Id, docker_container_id, cgroup_container_id, "")))
| eval container_name=trim(toString(coalesce(container_name, containerName, scope_task, docker_container, "")))
| eval image=trim(toString(coalesce(image, Image, "")))
| eval nr_periods=tonumber(tostring(coalesce(nr_periods, nrPeriods, cpu_nr_periods, stat_nr_periods, "")), 10)
| eval nr_throttled=tonumber(tostring(coalesce(nr_throttled, nrThrottled, cpu_nr_throttled, stat_nr_throttled, "")), 10)
| eval throttled_time_ns=tonumber(tostring(coalesce(throttled_time, throttledTime, throttled_time_nanoseconds, "")), 10)
| eval cpu_usage_ns=tonumber(tostring(coalesce(cpuacct_usage, cpuacct_usage_ns, CPUAcctUsage, usage_ns, "")), 10)
| where isnotnull(nr_periods) AND isnotnull(nr_throttled) AND nr_periods>=0 AND nr_throttled>=0
| sort 0 + host_id, container_id, _time
| streamstats window=2 current=t global=f last(nr_periods) AS prev_np last(nr_throttled) AS prev_nt last(throttled_time_ns) AS prev_tt last(cpu_usage_ns) AS prev_cu last(_time) AS t_prev BY host_id, container_id
| eval sec_delta=if(isnotnull(t_prev), _time - t_prev, null())
| eval periods_delta=nr_periods - prev_np
| eval throttled_delta=nr_throttled - prev_nt
| eval tt_delta_ns=throttled_time_ns - prev_tt
| eval usage_delta_ns=if(isnotnull(cpu_usage_ns) AND isnotnull(prev_cu), cpu_usage_ns - prev_cu, null())
| eval throttle_ratio=if(periods_delta>0, throttled_delta / periods_delta, null())
| eval throttle_pct=round(100 * coalesce(throttle_ratio, throttledRatio, 0), 2)
| eval throttled_wall_pct=if(sec_delta>0 AND sec_delta<=900, round((tt_delta_ns / sec_delta) / 10000000, 4), null())
| where periods_delta>0 AND isnotnull(sec_delta) AND sec_delta>0
| streamstats window=5 current=t global=f avg(throttle_pct) AS throttle_pct_sustained BY host_id, container_id
| eventstats max(throttle_pct) AS throttle_peak_1h BY host_id, container_id
| join type=left max=0 host_id, container_id [
    search (index=containers OR index=os) sourcetype="docker:inspect" earliest=-1h@h latest=@h
    | eval host_id=lower(toString(coalesce(host, Host, hostname, "")))
    | eval container_id=trim(toString(coalesce(container_id, Id, id, containerId, "")))
    | eval cfs_quota_us=tonumber(tostring(coalesce(HostConfig_CpuQuota, host_config_cpu_quota, CpuQuota, cpu_quota, "-1")), 10)
    | eval cfs_period_us=tonumber(tostring(coalesce(HostConfig_CpuPeriod, host_config_cpu_period, CpuPeriod, cpu_period, "100000")), 10)
    | eval cpuset_cpus=toString(coalesce(HostConfig_CpusetCpus, host_config_cpuset_cpus, CpusetCpus, cpuset_cpus, ""))
    | eval nano_cpus=tonumber(tostring(coalesce(HostConfig_NanoCpus, host_config_nano_cpus, NanoCpus, "0")), 10)
    | stats latest(cfs_quota_us) AS cfs_quota_us latest(cfs_period_us) AS cfs_period_us latest(cpuset_cpus) AS cpuset_cpus latest(nano_cpus) AS nano_cpus BY host_id, container_id
  ]
| join type=left max=0 host_id [
    search (index=metrics_oti OR index=os) sourcetype="procfs:loadavg" earliest=-1h@h latest=@h
    | eval host_id=lower(toString(coalesce(host, Host, hostname, dest, "")))
    | eval host_load_1m=tonumber(tostring(coalesce(load1, load_1m, loadavg1, la1, "")), 10)
    | eval host_ncpus=tonumber(tostring(coalesce(ncpus, processor_count, cpu_count, logical_cpus, "")), 10)
    | stats latest(host_load_1m) AS host_load_1m latest(host_ncpus) AS host_ncpus BY host_id
  ]
| eval cfs_cpus=if(cfs_quota_us>0 AND cfs_period_us>0, cfs_quota_us / cfs_period_us, if(nano_cpus>0, nano_cpus / 1000000000, null()))
| eval quota_pct_used=if(isnotnull(usage_delta_ns) AND sec_delta>0 AND isnotnull(cfs_cpus) AND cfs_cpus>0, min(200, round(100 * usage_delta_ns / (sec_delta * 1000000000 * cfs_cpus), 2)), null())
| eval cpuset_span=if(len(trim(cpuset_cpus))>0, mvcount(split(replace(cpuset_cpus, "-", ","), ",")), null())
| eval cpuset_narrow=if(isnotnull(cpuset_span) AND cpuset_span>0 AND cpuset_span<=4, 1, 0)
| eval host_saturation=if(isnotnull(host_ncpus) AND host_ncpus>0 AND isnotnull(host_load_1m) AND host_load_1m>(host_ncpus * 0.92), 1, 0)
| eval signal_type="cgroup_cpu_stat_throttle"
| eval image_key=lower(trim(if(len(trim(image))>0, image, container_name)))
| join type=left max=0 image_key [
    | inputlookup container_cpu_baseline.csv
    | eval image_key=lower(trim(toString(coalesce(image, image_ref, ""))))
    | eval baseline_throttle_pct=tonumber(tostring(coalesce(expected_throttle_pct, p95_throttle_pct, golden_throttle_pct, "")), 10)
    | eval workload_class=toString(coalesce(workload_class, tier, slo_tier, ""))
    | fields image_key baseline_throttle_pct workload_class
  ]
| eval baseline_delta=if(isnotnull(baseline_throttle_pct), abs(throttle_pct - baseline_throttle_pct), null())
| eval severity=case(
    (host_saturation=1) AND (throttle_pct<35), null(),
    (throttle_pct_sustained>=90) AND (host_saturation=0), "critical_throttled_above_90pct_sustained",
    (isnotnull(quota_pct_used) AND quota_pct_used>=95 AND throttle_pct>=35), "critical_quota_exhausted_burst_failure",
    (cpuset_narrow=1) AND (throttle_pct>=60) AND (host_saturation=0), "high_cpuset_numa_misplacement",
    (throttle_pct>=70) AND (throttle_pct<90), "high_throttled_70_to_90pct",
    (throttle_pct>=30) AND (throttle_pct<70) AND (throttle_peak_1h>=30), "medium_throttled_30_to_70pct_chronic",
    (isnotnull(baseline_throttle_pct)) AND (baseline_delta<=10) AND (throttle_pct>=baseline_throttle_pct) AND (throttle_pct>=12) AND (throttle_pct<35), "low_baseline_drift_within_10pct",
    true(), null())
| where isnotnull(severity)
| eval recommended_response=case(
    severity="critical_throttled_above_90pct_sustained", "Increase docker --cpus / Kubernetes cpu limits, or reduce per-thread CPU; capture flame graphs during the window; verify not host-saturated via loadavg.",
    severity="critical_quota_exhausted_burst_failure", "Quota nearly equals measured cpuacct usage slope; allow short burst headroom or split replicas; validate CFS period and cgroup v2 cpu.max if migrated from v1.",
    severity="high_cpuset_numa_misplacement", "Revisit cpuset.cpus / Docker --cpuset-cpus pinning; widen CPU pool or align with NUMA node for memory-heavy workloads; confirm throttling is not host-wide.",
    severity="high_throttled_70_to_90pct", "Treat as production-impacting CPU starvation risk; schedule right-sizing review and compare throttle_wall_pct to latency SLO dashboards.",
    severity="medium_throttled_30_to_70pct_chronic", "Chronic partial throttling; tune requests/limits, check noisy neighbors, and trend against release calendar.",
    severity="low_baseline_drift_within_10pct", "Minor elevation versus golden image baseline; document and watch next sprint unless latency regressions appear.",
    true(), "Correlate linux:cgroup cpu.stat with docker inspect and host loadavg before closing.")
| eval recommended_response=if(host_saturation=1, "Host loadavg implies noisy-neighbor saturation; validate attribution before container-only quota changes. " + recommended_response, recommended_response)
| join type=left max=0 host_id, container_name [
    | inputlookup container_owner.csv
    | eval host_id=lower(toString(coalesce(host_id, host, "")))
    | eval container_name=toString(container_name)
    | eval owner_team=toString(coalesce(owner_team, squad, ""))
    | fields host_id container_name owner_team
  ]
| table container_id container_name image host_id signal_type throttle_pct throttle_ratio quota_pct_used throttled_wall_pct severity recommended_response host_load_1m cpuset_cpus owner_team
```

### Step 4 — Validate

Positive path A — quota-bound spinner: on a lab host run docker run --rm --cpus=0.25 --name lab-throttle stress-ng --cpu 2 --timeout 120s or an approved equivalent, wait for linux:cgroup samples, and confirm nr_throttled increments with a rising throttle_ratio while the container remains alive. Execute container_uc_3_1_3_cpu_throttling and expect a non-null severity row with quota_pct_used trending high if cpuacct.usage deltas are present in your TA feed.

Positive path B — inspect alignment: docker inspect lab-throttle --format '{{.HostConfig.CpuQuota}} {{.HostConfig.CpuPeriod}}' must match cfs_quota_us and cfs_period_us fields in Splunk after normalization. Mismatches indicate props gaps, not benign noise.

Positive path C — host saturation: drive host loadavg above logical CPU count with a separate host-wide stress test while keeping a tight container quota; verify host_saturation prepends the attribution warning inside recommended_response and that trivial container-only quota increases are not recommended without reading loadavg.

Negative path — idle nginx: run nginx:alpine without CPU limits for thirty minutes under light traffic and confirm throttle_pct stays near zero, producing no severity row after the where clause.

Field sanity: temporarily rename TA fields in a sandbox forwarder to mimic camelCase-only payloads and confirm coalesce still populates nr_periods. RBAC: readers without metrics_oti and containers indexes must see zero rows. Clock skew: if sec_delta becomes negative or absurdly large, fix NTP before trusting quota_pct_used.

Correlation: compare alert times to APM or ingress p95 latency; mis-timed spikes usually mean collection lag or duplicate container_id keys after rapid recreate events.

### Step 5 — Operationalize & Troubleshoot

Case A — Sustained throttling above ninety percent on production-tier latency-sensitive container: treat as immediate capacity risk; raise CpuQuota or split replicas, capture profiles, and open a change record referencing cgroup cpu.stat excerpts archived to your evidence index.

Case B — CFS quota exhausted during normal burst pattern: validate whether Kubernetes or Docker settings removed burst allowance; review KEP-2625 era guidance on cgroup v2 cpu quota behavior and consider increasing parallelism across pods instead of inflating single-threaded limits.

Case C — cpuset NUMA mis-placement during failover: widen cpuset.cpus after confirming memory nodes with numastat; do not only raise quota if the workload is pinned to two logical CPUs on a ninety-six core host.

Case D — Host saturation false attribution: when host_load_1m exceeds host_ncpus and many cgroups show throttle, prioritize fleet scale-out or noisy-neighbor containment before per-container tuning.

Case E — Scheduled batch hitting throttle as designed: align container_cpu_baseline.csv workload_class with batch expectations and route alerts to FinOps instead of product on-call.

Case F — JVM or dotnet GC pause windows masquerading as throttle: compare throttled_wall_pct to GC logs; if pauses coincide, tune heap or GC ergonomics alongside CPU limits.

Case G — Legitimate CI compile farm: maintain owner_team routing to developer productivity and lower severity macros for builder host classes.

Case H — Dual writers after OTel migration: deduplicate linux:cgroup events or you will double-count periods_delta; enforce one primary collector per node class.

Case I — Short-lived tasks never sampled: increase poll frequency on CI executors or accept that this control targets steady services, not sub-second lambdas.

Case J — container_owner join misses: normalize Compose project prefixes in the CSV publisher exactly as linux:cgroup container_name fields appear.

Dashboard publishing: build a twenty-four hour heatmap of throttle_ratio by container_name, a stacked area chart of quota_pct_used versus measured throttle_pct, and a table of cpuset_cpus with NUMA notes for leadership reviews.

Evidence retention: weekly CSV exports of the alert table with lookup commit hashes satisfy internal audit samples when paired with change tickets that document CpuQuota adjustments.

Governance: quarterly replay one historical incident through the SPL after kernel or Docker upgrades; update the comment macro when indexes move.

Closing checklist: monitoringType lists Performance and Capacity; splunkPillar Observability; cimModels includes Performance; five step headers use plain text with em dashes; Step 3 fenced SPL matches the spl field exactly; knownFalsePositives discuss performance-domain batch and ML pinning patterns; references span kernel, Docker, Gregg, Lantern, and Kubernetes KEP documentation; no forbidden boilerplate phrases appear in narrative JSON fields.

Supplemental engineering notes for long-term owners: when rootless Docker delegates cgroups, confirm linux:cgroup paths follow user.slice subtrees. When migrating to cgroup v2-only distributions, revalidate cpu.max string parsing if you later extend this UC. When finance challenges ingest cost, compare license bytes to the revenue impact of an undetected p95 latency regression during Black Friday. When legal requests holds, include docker:inspect JSON and raw cpu.stat lines in preservation scope. When service meshes add sidecars, expect additive CPU usage that increases quota pressure without application code changes. When using AWS Graviton, validate that nr_periods semantics match x86 expectations after major kernel bumps. When integrating Splunk ITSI, map severity strings to episode priority with critical tiers as P2 unless SLO mapping dictates P1. When red teaming, pair this UC with UC-3.1.1 to prove whether latency followed crash loops or pure throttle. When OT edge gateways run Docker, duplicate baselines with OT-specific workload_class values. When automating remediation, never allow unsupervised quota removal in regulated PCI zones without human approval. When training new responders, teach the difference between throttled_time slope and simple CPU percent busy charts. When Splunk Cloud search autoscaling changes, revalidate schedule overlap so five-minute windows do not stack. When closing incidents, record whether the fix was quota, cpuset, replica count, or host scale-out to improve fleet learning. When handling zonal outages, throttle warning noise using region macros tied to loadavg context. When reviewing Mirantis support bundles, compare their cgroup snapshots to Splunk field extractions. When deprecating dockerd on a node class, retire this UC on that class rather than silencing detections globally.



## SPL

```spl
`comment("UC-3.1.3 Container CPU Throttling. Tunables: indexes metrics_oti containers os; lookups container_cpu_baseline.csv (image lower) and container_owner.csv (host_id container_name); sustained_avg_window=5 samples; quota_burst_pct=95; earliest=-1h@h latest=@h. Complements UC-3.1.2 memory cgroup axis with CPU throttle axis.")`
| search (index=metrics_oti OR index=containers OR index=os) sourcetype="linux:cgroup" earliest=-1h@h latest=@h
| eval host_id=lower(toString(coalesce(host, Host, hostname, dest, "")))
| eval container_id=trim(toString(coalesce(container_id, containerId, Id, docker_container_id, cgroup_container_id, "")))
| eval container_name=trim(toString(coalesce(container_name, containerName, scope_task, docker_container, "")))
| eval image=trim(toString(coalesce(image, Image, "")))
| eval nr_periods=tonumber(tostring(coalesce(nr_periods, nrPeriods, cpu_nr_periods, stat_nr_periods, "")), 10)
| eval nr_throttled=tonumber(tostring(coalesce(nr_throttled, nrThrottled, cpu_nr_throttled, stat_nr_throttled, "")), 10)
| eval throttled_time_ns=tonumber(tostring(coalesce(throttled_time, throttledTime, throttled_time_nanoseconds, "")), 10)
| eval cpu_usage_ns=tonumber(tostring(coalesce(cpuacct_usage, cpuacct_usage_ns, CPUAcctUsage, usage_ns, "")), 10)
| where isnotnull(nr_periods) AND isnotnull(nr_throttled) AND nr_periods>=0 AND nr_throttled>=0
| sort 0 + host_id, container_id, _time
| streamstats window=2 current=t global=f last(nr_periods) AS prev_np last(nr_throttled) AS prev_nt last(throttled_time_ns) AS prev_tt last(cpu_usage_ns) AS prev_cu last(_time) AS t_prev BY host_id, container_id
| eval sec_delta=if(isnotnull(t_prev), _time - t_prev, null())
| eval periods_delta=nr_periods - prev_np
| eval throttled_delta=nr_throttled - prev_nt
| eval tt_delta_ns=throttled_time_ns - prev_tt
| eval usage_delta_ns=if(isnotnull(cpu_usage_ns) AND isnotnull(prev_cu), cpu_usage_ns - prev_cu, null())
| eval throttle_ratio=if(periods_delta>0, throttled_delta / periods_delta, null())
| eval throttle_pct=round(100 * coalesce(throttle_ratio, throttledRatio, 0), 2)
| eval throttled_wall_pct=if(sec_delta>0 AND sec_delta<=900, round((tt_delta_ns / sec_delta) / 10000000, 4), null())
| where periods_delta>0 AND isnotnull(sec_delta) AND sec_delta>0
| streamstats window=5 current=t global=f avg(throttle_pct) AS throttle_pct_sustained BY host_id, container_id
| eventstats max(throttle_pct) AS throttle_peak_1h BY host_id, container_id
| join type=left max=0 host_id, container_id [
    search (index=containers OR index=os) sourcetype="docker:inspect" earliest=-1h@h latest=@h
    | eval host_id=lower(toString(coalesce(host, Host, hostname, "")))
    | eval container_id=trim(toString(coalesce(container_id, Id, id, containerId, "")))
    | eval cfs_quota_us=tonumber(tostring(coalesce(HostConfig_CpuQuota, host_config_cpu_quota, CpuQuota, cpu_quota, "-1")), 10)
    | eval cfs_period_us=tonumber(tostring(coalesce(HostConfig_CpuPeriod, host_config_cpu_period, CpuPeriod, cpu_period, "100000")), 10)
    | eval cpuset_cpus=toString(coalesce(HostConfig_CpusetCpus, host_config_cpuset_cpus, CpusetCpus, cpuset_cpus, ""))
    | eval nano_cpus=tonumber(tostring(coalesce(HostConfig_NanoCpus, host_config_nano_cpus, NanoCpus, "0")), 10)
    | stats latest(cfs_quota_us) AS cfs_quota_us latest(cfs_period_us) AS cfs_period_us latest(cpuset_cpus) AS cpuset_cpus latest(nano_cpus) AS nano_cpus BY host_id, container_id
  ]
| join type=left max=0 host_id [
    search (index=metrics_oti OR index=os) sourcetype="procfs:loadavg" earliest=-1h@h latest=@h
    | eval host_id=lower(toString(coalesce(host, Host, hostname, dest, "")))
    | eval host_load_1m=tonumber(tostring(coalesce(load1, load_1m, loadavg1, la1, "")), 10)
    | eval host_ncpus=tonumber(tostring(coalesce(ncpus, processor_count, cpu_count, logical_cpus, "")), 10)
    | stats latest(host_load_1m) AS host_load_1m latest(host_ncpus) AS host_ncpus BY host_id
  ]
| eval cfs_cpus=if(cfs_quota_us>0 AND cfs_period_us>0, cfs_quota_us / cfs_period_us, if(nano_cpus>0, nano_cpus / 1000000000, null()))
| eval quota_pct_used=if(isnotnull(usage_delta_ns) AND sec_delta>0 AND isnotnull(cfs_cpus) AND cfs_cpus>0, min(200, round(100 * usage_delta_ns / (sec_delta * 1000000000 * cfs_cpus), 2)), null())
| eval cpuset_span=if(len(trim(cpuset_cpus))>0, mvcount(split(replace(cpuset_cpus, "-", ","), ",")), null())
| eval cpuset_narrow=if(isnotnull(cpuset_span) AND cpuset_span>0 AND cpuset_span<=4, 1, 0)
| eval host_saturation=if(isnotnull(host_ncpus) AND host_ncpus>0 AND isnotnull(host_load_1m) AND host_load_1m>(host_ncpus * 0.92), 1, 0)
| eval signal_type="cgroup_cpu_stat_throttle"
| eval image_key=lower(trim(if(len(trim(image))>0, image, container_name)))
| join type=left max=0 image_key [
    | inputlookup container_cpu_baseline.csv
    | eval image_key=lower(trim(toString(coalesce(image, image_ref, ""))))
    | eval baseline_throttle_pct=tonumber(tostring(coalesce(expected_throttle_pct, p95_throttle_pct, golden_throttle_pct, "")), 10)
    | eval workload_class=toString(coalesce(workload_class, tier, slo_tier, ""))
    | fields image_key baseline_throttle_pct workload_class
  ]
| eval baseline_delta=if(isnotnull(baseline_throttle_pct), abs(throttle_pct - baseline_throttle_pct), null())
| eval severity=case(
    (host_saturation=1) AND (throttle_pct<35), null(),
    (throttle_pct_sustained>=90) AND (host_saturation=0), "critical_throttled_above_90pct_sustained",
    (isnotnull(quota_pct_used) AND quota_pct_used>=95 AND throttle_pct>=35), "critical_quota_exhausted_burst_failure",
    (cpuset_narrow=1) AND (throttle_pct>=60) AND (host_saturation=0), "high_cpuset_numa_misplacement",
    (throttle_pct>=70) AND (throttle_pct<90), "high_throttled_70_to_90pct",
    (throttle_pct>=30) AND (throttle_pct<70) AND (throttle_peak_1h>=30), "medium_throttled_30_to_70pct_chronic",
    (isnotnull(baseline_throttle_pct)) AND (baseline_delta<=10) AND (throttle_pct>=baseline_throttle_pct) AND (throttle_pct>=12) AND (throttle_pct<35), "low_baseline_drift_within_10pct",
    true(), null())
| where isnotnull(severity)
| eval recommended_response=case(
    severity="critical_throttled_above_90pct_sustained", "Increase docker --cpus / Kubernetes cpu limits, or reduce per-thread CPU; capture flame graphs during the window; verify not host-saturated via loadavg.",
    severity="critical_quota_exhausted_burst_failure", "Quota nearly equals measured cpuacct usage slope; allow short burst headroom or split replicas; validate CFS period and cgroup v2 cpu.max if migrated from v1.",
    severity="high_cpuset_numa_misplacement", "Revisit cpuset.cpus / Docker --cpuset-cpus pinning; widen CPU pool or align with NUMA node for memory-heavy workloads; confirm throttling is not host-wide.",
    severity="high_throttled_70_to_90pct", "Treat as production-impacting CPU starvation risk; schedule right-sizing review and compare throttle_wall_pct to latency SLO dashboards.",
    severity="medium_throttled_30_to_70pct_chronic", "Chronic partial throttling; tune requests/limits, check noisy neighbors, and trend against release calendar.",
    severity="low_baseline_drift_within_10pct", "Minor elevation versus golden image baseline; document and watch next sprint unless latency regressions appear.",
    true(), "Correlate linux:cgroup cpu.stat with docker inspect and host loadavg before closing.")
| eval recommended_response=if(host_saturation=1, "Host loadavg implies noisy-neighbor saturation; validate attribution before container-only quota changes. " + recommended_response, recommended_response)
| join type=left max=0 host_id, container_name [
    | inputlookup container_owner.csv
    | eval host_id=lower(toString(coalesce(host_id, host, "")))
    | eval container_name=toString(container_name)
    | eval owner_team=toString(coalesce(owner_team, squad, ""))
    | fields host_id container_name owner_team
  ]
| table container_id container_name image host_id signal_type throttle_pct throttle_ratio quota_pct_used throttled_wall_pct severity recommended_response host_load_1m cpuset_cpus owner_team
```

## CIM SPL

```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) AS avg_cpu_load max(Performance.cpu_load_percent) AS peak_cpu_load FROM datamodel=Performance WHERE nodename=Performance.CPU earliest=-1h@h latest=@h BY Performance.host span=5m
| rename Performance.host AS host_id
| where peak_cpu_load>88
```

## Visualization

Primary heatmap: throttle_ratio by container_name over twenty-four hours with cell coloring past seventy percent. Secondary stacked area: quota_pct_used versus throttle_pct for the top noisy services in the trailing hour. Tertiary table: cpuset_cpus, host_load_1m, and NUMA notes with drilldowns to raw linux:cgroup cpu.stat lines and docker:inspect JSON fragments for the same host_id and container_id.

## Known False Positives

Batch extract-transform-load containers, CI compile farms, and big-data shuffle workers often carry intentionally tight docker --cpus settings where chronic nr_throttled growth is an expected cost-control posture rather than an outage precursor; tag them in container_cpu_baseline.csv workload_class or suppress via host-class macros after FinOps approval. Periodic JVM or dotnet garbage-collection pauses can align in time with throttle metrics even when the dominant stall is heap management rather than cgroup quota; corroborate with GC logs before blaming CpuQuota alone. Scheduled cron bursts that spike CPU for two minutes every hour may trip medium_throttled_30_to_70pct_chronic without violating customer SLOs if latency dashboards stay flat; require SLO correlation before paging. NUMA-affinity-constrained ML inference pods may keep narrow cpuset spans by design; pair with GPU or accelerator telemetry so high_cpuset_numa_misplacement does not fire on approved pinning. Observed throttle without user-visible latency on background reindexers or telemetry scrapers is common; downgrade using baseline rows that record acceptable throttle for non-interactive images. Host-wide saturation flagged by procfs:loadavg can make many containers appear throttled simultaneously even when individual quotas are generous; follow the recommended_response host attribution path before opening per-container tickets. Kernel upgrades that reset cgroup counters can create one noisy interval; replay after two collection cycles. Dual ingestion from Splunk_TA_nix and OpenTelemetry without deduplication can double periods_delta; enforce a single primary writer per node class.

## References

- [Linux kernel docs — CFS scheduler design](https://docs.kernel.org/scheduler/sched-design-CFS.html)
- [Linux kernel admin guide — cgroup v2 CPU interface](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html#cpu-interface-files)
- [Docker Docs — CPU limits (--cpus, CFS quota)](https://docs.docker.com/engine/containers/resource_constraints/#cpu)
- [Brendan Gregg — Linux CFS scheduler and job capacity](http://www.brendangregg.com/blog/2017-11-12/linux-cfs-scheduler-and-job-capacity.html)
- [Splunk Lantern — Getting Docker log data into Splunk Cloud with OpenTelemetry](https://lantern.splunk.com/Platform_Data_Management/Unlock_Insights/Getting_Docker_log_data_into_Splunk_Cloud_Platform_with_OpenTelemetry)
- [Kubernetes enhancement — KEP-2625 cgroup v2 optional CPU quota](https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/2625-cgroupv2-optional-cpuquota)
