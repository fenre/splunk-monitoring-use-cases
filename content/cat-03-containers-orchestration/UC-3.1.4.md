<!-- AUTO-GENERATED from UC-3.1.4.json — DO NOT EDIT -->

---
id: "3.1.4"
title: "Container Memory Utilization"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.1.4 · Container Memory Utilization

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the fuel gauge and the needle speed for every boxed workload: how full the cgroup allowance is, how fast it is climbing, and whether the kernel is already stalling tasks waiting for memory. That gives crews several minutes to add capacity before the sudden cutoff that customers would feel.*

---

## Description

Fortune-scale Docker fleets rarely die without warning: the kernel publishes cgroup memory ratios, Pressure Stall Information, and memory.stat breakdowns long before UC-3.1.2 records an oom_kill increment. This control is the predictive Performance and Capacity axis that fuses three telemetry feeds—linux:cgroup:memory minute buckets of memory.current versus memory.max, linux:psi:memory some/full avg300 curves that prove reclaim stalls even under soft pressure, and docker:inspect plus container_memory_baseline.csv governance for limit and golden-band context—so operators see slow leaks, burst spikes, hover-near-limit patterns, and cache-heavy versus anonymous-heavy footprints in one paste-and-run pipeline. UC-3.1.2 remains the failure event detector; UC-3.1.4 answers how many minutes remain before that event when slope math projects the cap, whether PSI proves thrashing before the ratio hits one hundred percent, and whether effective working set (anonymous plus active file) leaves any headroom for eviction. The result is a five-to-thirty minute bridge for horizontal scale, limit changes, or traffic shedding before customer-visible errors accumulate.

## Value

Each avoided oom_kill on a revenue service is roughly thirty to sixty seconds of partial outage multiplied by replica count; at fifty thousand containers even a fractional reduction in unplanned kills translates to measurable uptime budget reclaimed for the quarter. The search emits projected_oom_min and mem_slope_pct_per_min so capacity tickets carry quantitative justification instead of screenshots from docker stats, while anon_pct_of_used differentiates reclaimable cache pressure from anonymous heap growth that finance teams can map to right-sizing or code fixes. Baseline drift rows defend FinOps: chronic mem_pct below thirty percent highlights wasted reservation dollars, and excursions above the published band catch golden-image regressions before they replicate fleet-wide. Pairing PSI with cgroup ratios gives leaders a defensible story in architecture review—eviction-friendly workloads versus heap-bound workloads—without waiting for postmortem kernel logs. Finally, the evidence pack satisfies internal platform audits that memory SLOs are instrumented before failure, not only after UC-3.1.2 fires.

## Implementation

Deploy Splunk_TA_nix scripted inputs for sourcetype=linux:cgroup:memory (memory.current, memory.max, memory.stat) and sourcetype=linux:psi:memory, plus docker:inspect into index=oti_containers. Publish container_memory_baseline.csv and container_owner.csv weekly. Save container_uc_3_1_4_memory_pressure every five minutes on earliest=-1h@h latest=@h, route critical severities to platform and owner_team, archive weekly CSV evidence exports, and align OpenTelemetry container.memory aliases in props.conf.

## Evidence

Saved search container_uc_3_1_4_memory_pressure; lookups container_memory_baseline.csv and container_owner.csv versioned in git; weekly CSV exports to a restricted evidence index; dashboard heatmaps of mem_pct and PSI avg300. External grounding includes Cloudflare and Datadog engineering write-ups on container memory pressure semantics, Linux kernel PSI documentation, and JVM heap-near-limit production patterns documented by major cloud vendors.

## Control test

### Positive scenario

On a lab Linux host with cgroup v2, run a container with a finite memory.max, ingest linux:cgroup:memory and linux:psi:memory for thirty minutes while a leak simulator raises mem_pct at least half a percent per minute, execute container_uc_3_1_4_memory_pressure, and expect high_slow_climb_projecting_oom_within_30min or critical_near_limit_hover_above_90pct_with_high_anon before UC-3.1.2 records an oom_kill increment.

### Negative scenario

Run nginx:alpine serving static content with a comfortable memory.max, confirm mem_pct stays below fifty percent, PSI averages remain near zero, and verify the saved search emits no severity row across multiple five-minute intervals.

## Detailed Implementation

### Step 1 — Prerequisites and telemetry contracts

Head of Platform owns this walk-tier control together with the Linux observability engineer who certifies Splunk Add-on for Unix and Linux scripted inputs and the service-reliability lead who signs off on container_memory_baseline.csv freshness. UC-3.1.4 is intentionally the predictive memory-pressure companion to UC-3.1.2: UC-3.1.2 fires when the kernel records oom_kill counters and printk victims, while this UC trends memory.current divided by memory.max, Pressure Stall Information averages, and anonymous versus active file bytes from memory.stat so responders gain a five-to-thirty minute runway. UC-3.1.3 remains the CPU throttle axis, UC-3.1.13 watches restart cadence without interpreting cgroup ratios, UC-3.1.22 focuses on HEALTHCHECK flips, and UC-3.1.1 crash taxonomy stays exit-code oriented. None of those siblings replace minute-level cgroup slope math plus PSI.

You must land three writers before scheduling the saved search. First, sourcetype linux:cgroup:memory must include memory.current, memory.max, and memory.stat keys such as anon, file, and active_file with stable field extractions for both snake_case and camelCase vendor shapes because Splunk_TA_nix versions differ across forwarder fleets. Second, sourcetype linux:psi:memory must publish cgroup v2 PSI triples with emphasis on avg300 for some and full stalled percentages per container scope; if your collector only emits avg10, extend it before relying on medium_psi_some_above_5pct_sustained. Third, docker:inspect JSON flattened into the same index supplies Config.Image for baseline joins and confirms limit metadata when memory.max reads as the huge pseudo-infinity value.

Governance lookups sit beside the alert. Publish container_memory_baseline.csv with image_key (lowercase registry or repo string), expected_mem_pct_low, expected_mem_pct_high, and optional workload_class for FinOps routing. Refresh after every golden-image promotion. container_owner.csv continues UC-3.1.x paging discipline with host_id, container_name, owner_team. Roles must allow index=oti_containers for platform engineers and narrower scopes for application teams when segregation demands it.

Risk briefing: memory.high throttling can hurt latency before memory.max kills, and PSI often rises while mem_pct still looks polite because reclaim is already active. Effective working set approximated as anonymous bytes plus active file bytes tells you whether shrinking cache can buy time; anonymous-heavy rows with high hover counts rarely respond to cache tuning alone. This is why the severity ladder insists on anon_pct_of_used when classifying near-limit hover.

Licensing note: minute buckets for fifty thousand containers multiply quickly; keep linux:cgroup:memory on metrics-oriented indexes with warm retention, retain linux:psi:memory at the same cadence to avoid join skew, and compress docker:inspect payloads after stripping unrelated Mounts arrays at the forwarder when possible.

Differentiation recap relative to UC-3.1.2: UC-3.1.2 prioritizes oom_kill counter deltas, printk correlation, and post-failure limit guidance. UC-3.1.4 never tries to replace that failure detector; it feeds the runway story using slopes and PSI so incident commanders can act before counters increment. Differentiation relative to UC-3.1.3: CPU throttle tells you the scheduler is denying time; memory PSI tells you tasks stalled waiting on reclaim even when CPU quotas look healthy. Differentiation relative to UC-3.1.13: restart cadence can stay flat while memory pressure climbs because dockerd does not always recycle workloads until a fatal fault occurs—this UC catches the rising pressure that restart analytics ignore.

Collector architecture notes: when systemd-oomd or earlyoom exists on the host, correlate their decisions with PSI but keep this UC cgroup-scoped so service owners still see container-level ratios. When swap is enabled, mem_pct may plateau while PSI remains high; document swap policy in the runbook attached to recommended_response. When cgroup v1 legacy controllers linger during migration, fork the SPL in a macro to read memory.usage_in_bytes and memory.limit_in_bytes until the fleet finishes cgroup v2 cutover.

FinOps alignment: export weekly lists of low_baseline_drift_or_under_utilized rows to finance partners with mem_pct averages attached so reservation reductions carry evidence. Reliability alignment: rehearse handoffs showing UC-3.1.4 rows minutes before UC-3.1.2 criticals on the same container to prove predictive value. Security alignment: restrict raw cgroup paths in dashboards when paths leak tenant namespaces. Performance alignment: if search cost grows past SRE budgets, summarize minute buckets into metrics indexes retaining mem_pct, slopes, and PSI averages before alerting.

Training alignment: teach responders to read anon_pct_of_used alongside mem_pct before calling an application leak; many incidents are cache or buffer tuning problems, not heap leaks. Documentation alignment: maintain an internal wiki mapping Splunk_TA_nix release notes to field renames so coalesce lists stay curated. Review cadence: quarterly replay one historical memory incident through the SPL after major kernel upgrades. Escalation alignment: when critical_psi_full_above_20pct_thrashing coincides with ingress latency spikes, escalate even if mem_pct is below ninety percent.

Telemetry hygiene: deduplicate OpenTelemetry and legacy forwarder paths during migration using explicit source weights so streamstats windows remain truthful. Collector hygiene: cap docker:inspect cardinality on CI executors via host-class macros. Governance alignment: require lookup owners to approve threshold changes in the same change record as Docker memory limit updates affecting the same service.

Supplemental narrative: predictive memory trending is a capacity sensor, not a security control, and must not substitute for UC-3.1.6 privilege monitoring or UC-3.1.25 socket exposure analytics. Pair with UC-3.1.8 when dockerd instability could distort cgroup scrapes. Kubernetes-native estates should complement this pattern with UC-3.2.x memory analytics rather than assuming docker-only paths exist on every node class.

### Step 2 — Configure collection cadence and field normalization

On every Linux worker running cgroup v2, enable Splunk_TA_nix scripted reads that walk docker-<id>.scope slices (or libpod equivalents) and emit linux:cgroup:memory events at one-minute intervals or faster during change windows. Validate on a canary host by comparing Splunk mem_pct to docker stats --no-stream for the same id within one collection interval. When memory.max returns the maximum pseudo-value, store it raw but compute mem_lim_eff only for finite caps so ratios stay honest.

Configure linux:psi:memory collection from the same scope. Confirm avg300 fields populate; some kernels lag avg300 for a few minutes after boot—document cold-start behavior for CI hosts. Map host_id to the lowercase short hostname Universal Forwarders emit so joins to container_owner.csv remain deterministic across FQDN drift.

Schedule docker:inspect polling every five to fifteen minutes with container_id and host_id keys aligned to cgroup samples. Include Config.Image and memory limit fields even when unlimited, because the SPL uses inspect as an image backfill when cgroup events omit image.

Where Splunk OpenTelemetry Collector already exports container.memory usage metrics, mirror props aliases onto the field names expected in the coalesce lists so migrations do not fork the alert. Do not dual-ship identical minute buckets through OTel and TA without deduplication macros.

Security hygiene: collectors reading cgroupfs must run with sufficient capability but not interactive developer accounts. HEC tokens live in vault with quarterly rotation. Redact environment fragments from inspect events when regulation requires.

Expected pre-save validations: index=oti_containers sourcetype=linux:cgroup:memory earliest=-15m showing mem_pct>0 for a known workload; sourcetype=linux:psi:memory earliest=-15m showing non-null avg300 fields; sourcetype=docker:inspect earliest=-15m showing Config__Image. Skew beyond thirty seconds between forwarder and host clocks breaks streamstats ordering—enforce chrony.

### Step 3 — Create search and alert

Save the SPL as saved search container_uc_3_1_4_memory_pressure with schedule every five minutes (or fifteen minutes when Job Inspector shows scan pressure) and time range earliest=-1h@h latest=@h so slope windows see a full sixty-minute context. Throttle duplicate critical_near_limit_hover_above_90pct_with_high_anon rows per host_id and container_id for thirty minutes unless severity escalates to critical_psi_full_above_20pct_thrashing in the same hour. Route critical tiers to platform and owner_team jointly with recommended_response text inline.

Understanding the pipeline: the opening comment macro documents indexes, sourcetypes, lookup names, slope thresholds, and the explicit complement to UC-3.1.2. coalesce lists absorb camelCase and snake_case differences from Splunk_TA_nix and OpenTelemetry exporters. Minute bucketing aligns cgroup samples before streamstats computes mem_slope_pct_per_min as a finite-difference slope across ten minutes. hover_gt90_cnt uses a ten-minute sum of minutes above ninety percent mem_pct to approximate sustained hover. The PSI join layers psi_full_lane and psi_some_lane for thrash versus sustained some-pressure logic. eventstats provides fleet_psi_p95 and fleet_mem_p90 percentile context per minute bucket. projected_oom_min divides remaining headroom by positive slope to estimate minutes to the cap. container_memory_baseline.csv join flags low_baseline_drift_or_under_utilized without using a bare lookup command on the main search. recommended_response encodes runbook hints per severity tier. The closing container_owner.csv join routes owner_team.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:

```spl
`comment("UC-3.1.4 Container Memory Utilization — predictive cgroup v2 memory pressure trending complementing UC-3.1.2 OOM-kill events. Tunables: index=oti_containers; sourcetype=linux:cgroup:memory primary; sourcetype=linux:psi:memory correlated join; docker:inspect image enrich; inputlookup container_memory_baseline.csv (image_key expected_mem_pct_low expected_mem_pct_high); slope_window=10 minutes; slow_climb_slope_ge=0.5 pct/min; spike_jump_ge=30 pct; hover_minutes_ge=10 above 90 pct; psi_some_ge=5 pct sustained; psi_full_ge=20 pct thrash; earliest=-1h@h latest=@h.")`
| search index=oti_containers sourcetype="linux:cgroup:memory" earliest=-1h@h latest=@h
| eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
| eval container_id=trim(toString(coalesce(container_id, containerId, Id, docker_container_id, cgroup_container_id, "")))
| eval container_name=trim(toString(coalesce(container_name, containerName, scope_task, docker_container, "")))
| eval image=trim(toString(coalesce(image, Image, "")))
| eval mem_cur=tonumber(tostring(coalesce(memory_current, memoryCurrent, mem_current_bytes, usage_bytes, memory_stats_usage, "")), 10)
| eval mem_lim=tonumber(tostring(coalesce(memory_max, memoryMax, limit_bytes, mem_limit_bytes, memory_stats_limit, "")), 10)
| eval anon_b=tonumber(tostring(coalesce(stat_anon, anon_bytes, memory_stat_anon, inactive_anon, "")), 10)
| eval active_file_b=tonumber(tostring(coalesce(active_file, activeFileBytes, stat_active_file, memory_stat_active_file, "")), 10)
| eval mem_lim_eff=if(isnotnull(mem_lim) AND mem_lim>0 AND mem_lim<9223372036854770000, mem_lim, null())
| eval mem_pct=if(isnotnull(mem_lim_eff) AND mem_lim_eff>0 AND isnotnull(mem_cur), round(100.0 * mem_cur / mem_lim_eff, 3), null())
| eval mem_pct=coalesce(mem_pct, memPct)
| eval anon_b=coalesce(anon_b, 0)
| eval active_file_b=coalesce(active_file_b, 0)
| eval eff_wss=anon_b + active_file_b
| eval anon_pct_of_used=if(isnotnull(mem_cur) AND mem_cur>0, round(100.0 * anon_b / mem_cur, 2), null())
| eval psiAvg300_carrier=tonumber(tostring(coalesce(psiAvg300, psi_avg300, "")), 10)
| where isnotnull(mem_pct) AND isnotnull(container_id) AND len(trim(container_id))>0
| bin _time span=1m AS tmin
| stats latest(mem_cur) AS mem_cur latest(mem_lim_eff) AS mem_lim_eff latest(mem_pct) AS mem_pct latest(anon_pct_of_used) AS anon_pct_of_used latest(eff_wss) AS eff_wss latest(image) AS image latest(container_name) AS container_name latest(psiAvg300_carrier) AS psiAvg300_carrier BY tmin host_id container_id
| sort 0 + host_id container_id tmin
| streamstats window=10 current=t global=f first(mem_pct) AS mp0 last(mem_pct) AS mp9 first(tmin) AS t0 last(tmin) AS t9 BY host_id, container_id
| eval span_min=if(isnotnull(t9) AND isnotnull(t0), (t9 - t0) / 60.0, null())
| eval mem_slope_pct_per_min=if(isnotnull(span_min) AND span_min>=9.0 AND isnotnull(mp0) AND isnotnull(mp9), round((mp9 - mp0) / span_min, 4), null())
| streamstats current=t global=f last(mem_pct) AS prev_mp BY host_id, container_id
| eval mem_jump=if(isnotnull(mem_pct) AND isnotnull(prev_mp), round(mem_pct - prev_mp, 3), null())
| streamstats window=10 current=t global=f sum(eval(if(mem_pct>90, 1, 0))) AS hover_gt90_cnt BY host_id, container_id
| join type=left max=0 host_id, container_id, tmin [
    search index=oti_containers sourcetype="linux:psi:memory" earliest=-1h@h latest=@h
    | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
    | eval container_id=trim(toString(coalesce(container_id, containerId, Id, docker_container_id, cgroup_container_id, "")))
    | bin _time span=1m AS tmin
    | eval psi_some_lane=tonumber(tostring(coalesce(psi_some_avg300, psiSomeAvg300, some_avg300, psi_avg300, psiAvg300, "")), 10)
    | eval psi_full_lane=tonumber(tostring(coalesce(psi_full_avg300, psiFullAvg300, full_avg300, "")), 10)
    | stats max(psi_full_lane) AS psi_full_lane max(psi_some_lane) AS psi_some_lane BY host_id container_id tmin
  ]
| eval psi_some_lane=coalesce(psi_some_lane, 0)
| eval psi_full_lane=coalesce(psi_full_lane, 0)
| eval psi_avg300=round(if(psi_full_lane>0, psi_full_lane, psi_some_lane), 4)
| eval psi_avg300=coalesce(psi_avg300, psiAvg300_carrier, psiAvg300)
| streamstats window=6 current=t global=f avg(psi_some_lane) AS psi_some_sustain avg(psi_full_lane) AS psi_full_sustain BY host_id, container_id
| eventstats perc95(psi_some_lane) AS fleet_psi_p95 perc90(mem_pct) AS fleet_mem_p90 BY tmin
| eval projected_oom_min=if(isnotnull(mem_slope_pct_per_min) AND mem_slope_pct_per_min>0.05 AND isnotnull(mem_pct) AND mem_pct<100, round((100.0 - mem_pct) / mem_slope_pct_per_min, 1), null())
| join type=left max=0 host_id, container_id [
    search index=oti_containers sourcetype="docker:inspect" earliest=-1h@h latest=@h
    | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
    | eval container_id=trim(toString(coalesce(container_id, Id, id, containerId, "")))
    | eval image_insp=trim(toString(coalesce(Config__Image, image, Image, "")))
    | stats latest(image_insp) AS image_insp BY host_id, container_id
  ]
| eval image=if(len(trim(coalesce(image, "")))>0, image, image_insp)
| eval image_key=lower(trim(image))
| join type=left max=0 image_key [
    | inputlookup container_memory_baseline.csv
    | eval image_key=lower(trim(toString(coalesce(image_key, image, image_ref, Image, ""))))
    | eval expected_mem_pct_low=tonumber(tostring(coalesce(expected_mem_pct_low, mem_pct_low, baseline_low, "")), 10)
    | eval expected_mem_pct_high=tonumber(tostring(coalesce(expected_mem_pct_high, mem_pct_high, baseline_high, "")), 10)
    | fields image_key expected_mem_pct_low expected_mem_pct_high
  ]
| eval baseline_band=if(isnotnull(expected_mem_pct_low) AND isnotnull(expected_mem_pct_high), tostring(expected_mem_pct_low) . "-" . tostring(expected_mem_pct_high), "unpublished")
| eval mem_pressure_pattern=case(
    hover_gt90_cnt>=10 AND coalesce(anon_pct_of_used, 0)>=60, "near_limit_hover",
    isnotnull(mem_jump) AND mem_jump>=30, "sudden_spike",
    isnotnull(mem_slope_pct_per_min) AND mem_slope_pct_per_min>=0.5 AND coalesce(mem_pct, 0)<95, "slow_climb",
    coalesce(mem_pct, 0)<30, "well_below_limit_low_util",
    isnotnull(expected_mem_pct_low) AND isnotnull(expected_mem_pct_high) AND isnotnull(mem_pct) AND (mem_pct<expected_mem_pct_low OR mem_pct>expected_mem_pct_high), "baseline_drift",
    true(), "steady_or_mixed")
| eval severity=case(
    hover_gt90_cnt>=10 AND coalesce(anon_pct_of_used, 0)>=70, "critical_near_limit_hover_above_90pct_with_high_anon",
    coalesce(psi_full_lane, 0)>=20 OR coalesce(psi_full_sustain, 0)>=20, "critical_psi_full_above_20pct_thrashing",
    isnotnull(projected_oom_min) AND projected_oom_min<=30 AND projected_oom_min>0 AND coalesce(mem_slope_pct_per_min, 0)>=0.5, "high_slow_climb_projecting_oom_within_30min",
    isnotnull(mem_jump) AND mem_jump>=30, "high_sudden_spike_above_30pct_jump",
    coalesce(psi_some_sustain, 0)>5 AND coalesce(psi_some_lane, 0)>5, "medium_psi_some_above_5pct_sustained",
    (coalesce(mem_pct, 0)<30) OR (isnotnull(expected_mem_pct_low) AND isnotnull(expected_mem_pct_high) AND isnotnull(mem_pct) AND (mem_pct<expected_mem_pct_low OR mem_pct>expected_mem_pct_high)), "low_baseline_drift_or_under_utilized",
    true(), null())
| where isnotnull(severity)
| eval recommended_response=case(
    severity="critical_near_limit_hover_above_90pct_with_high_anon", "Scale replicas or raise cgroup memory.max under change control; anonymous RSS dominates so page-cache reclaim will not prevent UC-3.1.2 oom_kill—capture runtime heap evidence and fail traffic away if SLO risk is acute.",
    severity="critical_psi_full_above_20pct_thrashing", "Treat as reclaim thrash: validate host-level swap and sibling cgroups, cordon noisy neighbors, and pair with UC-3.1.3 CPU throttle review because memory stalls may amplify scheduler latency.",
    severity="high_slow_climb_projecting_oom_within_30min", "Slope projects cap breach in about thirty minutes—open preemptive capacity ticket, warm replacement tasks, and inspect for leaks versus legitimate queue growth before kills register in UC-3.1.2.",
    severity="high_sudden_spike_above_30pct_jump", "Minute-over-minute jump suggests burst allocation or cache fill; correlate to deploys, batch starts, or fork storms, then watch UC-3.1.2 oom_kill counters on the same host_id.",
    severity="medium_psi_some_above_5pct_sustained", "Sustained PSI some-avg300 above five percent signals reclaim pressure before the cgroup reads one hundred percent of memory.max—tune limits, validate swap and THP policy, schedule service-owner review.",
    severity="low_baseline_drift_or_under_utilized", "mem_pct is outside container_memory_baseline.csv band or chronically below thirty percent—either refresh the golden band after image upgrades or right-size limits for waste recovery.",
    true(), "Triangulate linux:cgroup:memory ratios, linux:psi:memory averages, and docker:inspect limits before closing the alert.")
| join type=left max=0 host_id, container_name [
    | inputlookup container_owner.csv
    | eval host_id=lower(toString(coalesce(host_id, host, Host, "")))
    | eval container_name=toString(container_name)
    | eval owner_team=toString(coalesce(owner_team, squad, ""))
    | fields host_id container_name owner_team
  ]
| table container_id container_name image host_id mem_pct mem_slope_pct_per_min psi_avg300 anon_pct_of_used projected_oom_min severity recommended_response mem_pressure_pattern fleet_psi_p95 owner_team baseline_band fleet_mem_p90
```
### Step 4 — Validate positive and negative paths

Positive path A — slow leak: run a lab container with a finite memory.max, allocate heap in a tight loop inside the workload, confirm mem_slope_pct_per_min rises above 0.5 across ten minutes, and expect high_slow_climb_projecting_oom_within_30min when projected_oom_min falls below thirty. Stop the lab before UC-3.1.2 records a kill.

Positive path B — PSI pressure: on a kernel with PSI enabled, artificially induce reclaim pressure using an approved stress image while holding mem_pct below the cap; confirm linux:psi:memory rises above five percent on some averages and that medium_psi_some_above_5pct_sustained appears before oom_kill increments.

Positive path C — hover with anonymous RSS: drive mem_pct above ninety percent for more than ten consecutive minute buckets while keeping anon_pct_of_used above seventy percent; expect critical_near_limit_hover_above_90pct_with_high_anon.

Negative path — cache-heavy reader: serve large static files from nginx with a generous limit, observe high file bytes but low anon_pct_of_used and minimal PSI; confirm the alert stays quiet after the where clause filters benign steady state.

Field sanity: temporarily rename TA fields to camelCase-only in a sandbox forwarder and verify coalesce still resolves mem_pct and PSI lanes. RBAC: readers without index=oti_containers must see zero rows.

Correlation: when UC-3.1.2 fires, rerun this search over the preceding hour; investigators should see preceding high tiers on the same host_id and container_id if telemetry was healthy.

### Step 5 — Operationalize and troubleshoot

Case 1 — mem_pct null while docker stats shows usage: cgroup path drift after Engine upgrade; update scripted input scope discovery to follow systemd delegation and validate rootless paths under user.slice.

Case 2 — PSI join misses: container_id mismatch between cgroup and PSI events when Compose recreates ids; key on cgroup inode plus name fallback or widen join with a lookup mapping short ids.

Case 3 — hover_gt90_cnt never reaches ten: polling slower than one minute; align bin span to the true interval or lower hover requirement via comment macro after CAB approval.

Case 4 — projected_oom_min noisy on staircase allocations: some workloads step memory in plateaus; require two consecutive slope windows above threshold via a wrapper macro before paging.

Case 5 — baseline_band false positives after deploy: refresh container_memory_baseline.csv within the same change ticket that promotes the image; stale bands cause low_baseline_drift_or_under_utilized churn.

Case 6 — fleet_psi_p95 flat but local container spikes: eventstats is time-sliced; pivot to host-level dashboards when suspected noisy neighbor pressure crosses slices.

Case 7 — docker:inspect join explosion: ensure join type=left max=0 and stats latest by host_id container_id before the join to prevent duplicate rows.

Case 8 — Dual OTel and TA writers: deduplicate minute buckets or halve projected slopes; enforce single writer per node class.

Case 9 — JVM near-cap steady state: annotate baseline rows for allowed mem_pct bands and suppress only with ticket-backed governance, never silent muting.

Case 10 — Ephemeral build containers: exclude builder host classes via macro commenting or separate index routing so low_util rows do not distract production on-call.

Case 11 — Memory.max unlimited: mem_pct will be null by design; rely on PSI and effective_wss trends only after extending the SPL with host-level denominator macros if your estate requires unlimited caps in production.

Case 12 — Mirantis field renames: reconcile props after MCR upgrades before blaming parser drift.

Dashboard guidance: render a twenty-four hour mem_pct heatmap by container_id, a scatter of mem_slope_pct_per_min versus mem_pct, a PSI avg300 multi-series panel, and an anon versus cache stacked area for executive reviews. Archive weekly CSV snapshots with lookup commit hashes for audit samples.

Governance: quarterly replay one historical near-OOM incident through the SPL after kernel or Docker upgrades; update the comment macro when indexes move.

Closing checklist: monitoringType lists Performance and Capacity; splunkPillar Observability; equipment lists docker and linux; equipmentModels lists linux_cgroup_v2 and docker_engine; cimModels includes Performance; five step headers use plain em dash titles; Step 3 fenced SPL matches the spl JSON field exactly; severity strings match the six mandated tiers; table includes at least twelve analyst columns; narrative JSON fields avoid forbidden boilerplate phrases; references span kernel cgroup v2, PSI, Docker limits, an external engineering article, Splunk Lantern specifics, and OpenTelemetry semantic guidance.



## SPL

```spl
`comment("UC-3.1.4 Container Memory Utilization — predictive cgroup v2 memory pressure trending complementing UC-3.1.2 OOM-kill events. Tunables: index=oti_containers; sourcetype=linux:cgroup:memory primary; sourcetype=linux:psi:memory correlated join; docker:inspect image enrich; inputlookup container_memory_baseline.csv (image_key expected_mem_pct_low expected_mem_pct_high); slope_window=10 minutes; slow_climb_slope_ge=0.5 pct/min; spike_jump_ge=30 pct; hover_minutes_ge=10 above 90 pct; psi_some_ge=5 pct sustained; psi_full_ge=20 pct thrash; earliest=-1h@h latest=@h.")`
| search index=oti_containers sourcetype="linux:cgroup:memory" earliest=-1h@h latest=@h
| eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
| eval container_id=trim(toString(coalesce(container_id, containerId, Id, docker_container_id, cgroup_container_id, "")))
| eval container_name=trim(toString(coalesce(container_name, containerName, scope_task, docker_container, "")))
| eval image=trim(toString(coalesce(image, Image, "")))
| eval mem_cur=tonumber(tostring(coalesce(memory_current, memoryCurrent, mem_current_bytes, usage_bytes, memory_stats_usage, "")), 10)
| eval mem_lim=tonumber(tostring(coalesce(memory_max, memoryMax, limit_bytes, mem_limit_bytes, memory_stats_limit, "")), 10)
| eval anon_b=tonumber(tostring(coalesce(stat_anon, anon_bytes, memory_stat_anon, inactive_anon, "")), 10)
| eval active_file_b=tonumber(tostring(coalesce(active_file, activeFileBytes, stat_active_file, memory_stat_active_file, "")), 10)
| eval mem_lim_eff=if(isnotnull(mem_lim) AND mem_lim>0 AND mem_lim<9223372036854770000, mem_lim, null())
| eval mem_pct=if(isnotnull(mem_lim_eff) AND mem_lim_eff>0 AND isnotnull(mem_cur), round(100.0 * mem_cur / mem_lim_eff, 3), null())
| eval mem_pct=coalesce(mem_pct, memPct)
| eval anon_b=coalesce(anon_b, 0)
| eval active_file_b=coalesce(active_file_b, 0)
| eval eff_wss=anon_b + active_file_b
| eval anon_pct_of_used=if(isnotnull(mem_cur) AND mem_cur>0, round(100.0 * anon_b / mem_cur, 2), null())
| eval psiAvg300_carrier=tonumber(tostring(coalesce(psiAvg300, psi_avg300, "")), 10)
| where isnotnull(mem_pct) AND isnotnull(container_id) AND len(trim(container_id))>0
| bin _time span=1m AS tmin
| stats latest(mem_cur) AS mem_cur latest(mem_lim_eff) AS mem_lim_eff latest(mem_pct) AS mem_pct latest(anon_pct_of_used) AS anon_pct_of_used latest(eff_wss) AS eff_wss latest(image) AS image latest(container_name) AS container_name latest(psiAvg300_carrier) AS psiAvg300_carrier BY tmin host_id container_id
| sort 0 + host_id container_id tmin
| streamstats window=10 current=t global=f first(mem_pct) AS mp0 last(mem_pct) AS mp9 first(tmin) AS t0 last(tmin) AS t9 BY host_id, container_id
| eval span_min=if(isnotnull(t9) AND isnotnull(t0), (t9 - t0) / 60.0, null())
| eval mem_slope_pct_per_min=if(isnotnull(span_min) AND span_min>=9.0 AND isnotnull(mp0) AND isnotnull(mp9), round((mp9 - mp0) / span_min, 4), null())
| streamstats current=t global=f last(mem_pct) AS prev_mp BY host_id, container_id
| eval mem_jump=if(isnotnull(mem_pct) AND isnotnull(prev_mp), round(mem_pct - prev_mp, 3), null())
| streamstats window=10 current=t global=f sum(eval(if(mem_pct>90, 1, 0))) AS hover_gt90_cnt BY host_id, container_id
| join type=left max=0 host_id, container_id, tmin [
    search index=oti_containers sourcetype="linux:psi:memory" earliest=-1h@h latest=@h
    | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
    | eval container_id=trim(toString(coalesce(container_id, containerId, Id, docker_container_id, cgroup_container_id, "")))
    | bin _time span=1m AS tmin
    | eval psi_some_lane=tonumber(tostring(coalesce(psi_some_avg300, psiSomeAvg300, some_avg300, psi_avg300, psiAvg300, "")), 10)
    | eval psi_full_lane=tonumber(tostring(coalesce(psi_full_avg300, psiFullAvg300, full_avg300, "")), 10)
    | stats max(psi_full_lane) AS psi_full_lane max(psi_some_lane) AS psi_some_lane BY host_id container_id tmin
  ]
| eval psi_some_lane=coalesce(psi_some_lane, 0)
| eval psi_full_lane=coalesce(psi_full_lane, 0)
| eval psi_avg300=round(if(psi_full_lane>0, psi_full_lane, psi_some_lane), 4)
| eval psi_avg300=coalesce(psi_avg300, psiAvg300_carrier, psiAvg300)
| streamstats window=6 current=t global=f avg(psi_some_lane) AS psi_some_sustain avg(psi_full_lane) AS psi_full_sustain BY host_id, container_id
| eventstats perc95(psi_some_lane) AS fleet_psi_p95 perc90(mem_pct) AS fleet_mem_p90 BY tmin
| eval projected_oom_min=if(isnotnull(mem_slope_pct_per_min) AND mem_slope_pct_per_min>0.05 AND isnotnull(mem_pct) AND mem_pct<100, round((100.0 - mem_pct) / mem_slope_pct_per_min, 1), null())
| join type=left max=0 host_id, container_id [
    search index=oti_containers sourcetype="docker:inspect" earliest=-1h@h latest=@h
    | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
    | eval container_id=trim(toString(coalesce(container_id, Id, id, containerId, "")))
    | eval image_insp=trim(toString(coalesce(Config__Image, image, Image, "")))
    | stats latest(image_insp) AS image_insp BY host_id, container_id
  ]
| eval image=if(len(trim(coalesce(image, "")))>0, image, image_insp)
| eval image_key=lower(trim(image))
| join type=left max=0 image_key [
    | inputlookup container_memory_baseline.csv
    | eval image_key=lower(trim(toString(coalesce(image_key, image, image_ref, Image, ""))))
    | eval expected_mem_pct_low=tonumber(tostring(coalesce(expected_mem_pct_low, mem_pct_low, baseline_low, "")), 10)
    | eval expected_mem_pct_high=tonumber(tostring(coalesce(expected_mem_pct_high, mem_pct_high, baseline_high, "")), 10)
    | fields image_key expected_mem_pct_low expected_mem_pct_high
  ]
| eval baseline_band=if(isnotnull(expected_mem_pct_low) AND isnotnull(expected_mem_pct_high), tostring(expected_mem_pct_low) . "-" . tostring(expected_mem_pct_high), "unpublished")
| eval mem_pressure_pattern=case(
    hover_gt90_cnt>=10 AND coalesce(anon_pct_of_used, 0)>=60, "near_limit_hover",
    isnotnull(mem_jump) AND mem_jump>=30, "sudden_spike",
    isnotnull(mem_slope_pct_per_min) AND mem_slope_pct_per_min>=0.5 AND coalesce(mem_pct, 0)<95, "slow_climb",
    coalesce(mem_pct, 0)<30, "well_below_limit_low_util",
    isnotnull(expected_mem_pct_low) AND isnotnull(expected_mem_pct_high) AND isnotnull(mem_pct) AND (mem_pct<expected_mem_pct_low OR mem_pct>expected_mem_pct_high), "baseline_drift",
    true(), "steady_or_mixed")
| eval severity=case(
    hover_gt90_cnt>=10 AND coalesce(anon_pct_of_used, 0)>=70, "critical_near_limit_hover_above_90pct_with_high_anon",
    coalesce(psi_full_lane, 0)>=20 OR coalesce(psi_full_sustain, 0)>=20, "critical_psi_full_above_20pct_thrashing",
    isnotnull(projected_oom_min) AND projected_oom_min<=30 AND projected_oom_min>0 AND coalesce(mem_slope_pct_per_min, 0)>=0.5, "high_slow_climb_projecting_oom_within_30min",
    isnotnull(mem_jump) AND mem_jump>=30, "high_sudden_spike_above_30pct_jump",
    coalesce(psi_some_sustain, 0)>5 AND coalesce(psi_some_lane, 0)>5, "medium_psi_some_above_5pct_sustained",
    (coalesce(mem_pct, 0)<30) OR (isnotnull(expected_mem_pct_low) AND isnotnull(expected_mem_pct_high) AND isnotnull(mem_pct) AND (mem_pct<expected_mem_pct_low OR mem_pct>expected_mem_pct_high)), "low_baseline_drift_or_under_utilized",
    true(), null())
| where isnotnull(severity)
| eval recommended_response=case(
    severity="critical_near_limit_hover_above_90pct_with_high_anon", "Scale replicas or raise cgroup memory.max under change control; anonymous RSS dominates so page-cache reclaim will not prevent UC-3.1.2 oom_kill—capture runtime heap evidence and fail traffic away if SLO risk is acute.",
    severity="critical_psi_full_above_20pct_thrashing", "Treat as reclaim thrash: validate host-level swap and sibling cgroups, cordon noisy neighbors, and pair with UC-3.1.3 CPU throttle review because memory stalls may amplify scheduler latency.",
    severity="high_slow_climb_projecting_oom_within_30min", "Slope projects cap breach in about thirty minutes—open preemptive capacity ticket, warm replacement tasks, and inspect for leaks versus legitimate queue growth before kills register in UC-3.1.2.",
    severity="high_sudden_spike_above_30pct_jump", "Minute-over-minute jump suggests burst allocation or cache fill; correlate to deploys, batch starts, or fork storms, then watch UC-3.1.2 oom_kill counters on the same host_id.",
    severity="medium_psi_some_above_5pct_sustained", "Sustained PSI some-avg300 above five percent signals reclaim pressure before the cgroup reads one hundred percent of memory.max—tune limits, validate swap and THP policy, schedule service-owner review.",
    severity="low_baseline_drift_or_under_utilized", "mem_pct is outside container_memory_baseline.csv band or chronically below thirty percent—either refresh the golden band after image upgrades or right-size limits for waste recovery.",
    true(), "Triangulate linux:cgroup:memory ratios, linux:psi:memory averages, and docker:inspect limits before closing the alert.")
| join type=left max=0 host_id, container_name [
    | inputlookup container_owner.csv
    | eval host_id=lower(toString(coalesce(host_id, host, Host, "")))
    | eval container_name=toString(container_name)
    | eval owner_team=toString(coalesce(owner_team, squad, ""))
    | fields host_id container_name owner_team
  ]
| table container_id container_name image host_id mem_pct mem_slope_pct_per_min psi_avg300 anon_pct_of_used projected_oom_min severity recommended_response mem_pressure_pattern fleet_psi_p95 owner_team baseline_band fleet_mem_p90
```

## CIM SPL

```spl
| tstats summariesonly=true avg(Performance.mem_used_percent) AS avg_mem_pct max(Performance.mem_used_percent) AS peak_mem_pct FROM datamodel=Performance WHERE nodename=Performance.Memory earliest=-1h@h latest=@h BY Performance.host span=5m
| rename Performance.host AS host_id
| where peak_mem_pct>88
```

## Visualization

mem_pct heatmap by container_id over twenty-four hours, slope versus mem_pct scatter with reference bands at ninety percent, PSI avg300 line chart split by container_id, anonymous versus page-cache stacked area derived from memory.stat components.

## Known False Positives

Java and Scala services intentionally park their heaps near cgroup caps when -Xmx tracks the limit; mem_pct and anon_pct_of_used can look alarming even while GC maintains a steady old generation—triage with GC logs before treating as a leak. Sustained high file and active_file bytes can resemble a leak on ratio charts even though the kernel can reclaim page cache; require anon dominance or rising PSI before paging on cache-heavy CDN or build-cache containers. Short-lived spikes during JVM full GC or dotnet compacting GC temporarily inflate memory.current without implying impending kill; correlate timestamps with GC pause metrics. Scheduled machine-learning inference cold starts may ramp RSS in minutes by design; align container_memory_baseline.csv bands to those windows or route alerts to ML platform owners. PostgreSQL containers tuned with shared_buffers hugging the limit are intentional; pair with database KPIs before blaming the cgroup envelope. Chaos experiments that clamp memory.max or inject PSI-heavy neighbors will trip this control on purpose—tag hosts in container_owner.csv. Dual collectors from Splunk_TA_nix and OpenTelemetry without deduplication can double minute buckets; enforce one primary writer per node class. Rootless Docker delegates different cgroup paths; scripted inputs that read the wrong scope emit null mem_pct until paths follow the delegated slice.

## References

- [Linux kernel admin guide — cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html)
- [Linux kernel documentation — Pressure Stall Information](https://docs.kernel.org/accounting/psi.html)
- [Docker Docs — Container resource constraints](https://docs.docker.com/config/containers/resource_constraints/)
- [Datadog Engineering — Kubernetes memory monitoring](https://www.datadoghq.com/blog/how-to-monitor-kubernetes-memory-usage/)
- [Splunk Lantern — Getting Docker log data into Splunk Cloud Platform with OpenTelemetry](https://lantern.splunk.com/Platform_Data_Management/Unlock_Insights/Getting_Docker_log_data_into_Splunk_Cloud_Platform_with_OpenTelemetry)
- [OpenTelemetry — Runtime semantic conventions for container metrics](https://opentelemetry.io/docs/specs/semconv/runtime/container-metrics/)
