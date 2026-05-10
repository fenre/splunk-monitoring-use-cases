<!-- AUTO-GENERATED from UC-3.1.23.json — DO NOT EDIT -->

---
id: "3.1.23"
title: "Container Network I/O Anomalies"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-3.1.23 · Container Network I/O Anomalies

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Security &middot; **Wave:** Walk &middot; **Status:** Verified

*We weigh every package leaving each loading dock on a shared warehouse floor. When one dock suddenly ships a hundred times its usual weight while the others go quiet, we notice before the highway backs up and other stores miss deliveries.*

---

## Description

This control watches per-container cumulative network counters at the cgroup and network-namespace boundary, turns them into five-minute egress and ingress byte rates plus transmit and receive drop accelerations, and compares those rates to a six-hour rolling mean and standard deviation for each container identifier. It consumes docker stats style JSON that exposes tx_bytes, rx_bytes, tx_dropped, and rx_dropped for every supervised container, and linux procfs exports that read /proc/<pid>/net/dev inside each netns so Compose, Swarm, and static Docker hosts share one analytics path even when the Engine API summary aggregates interfaces differently than the namespace view. The saved search computes host_egress_share_pct so operators see when one tenant captures more than sixty percent of a host transmit budget for consecutive intervals while peers starve, which is the customer-visible noisy-neighbor failure mode behind cross-application timeouts. It also elevates containers whose egress_zscore crosses three sigma above their recent history, surfacing low-CPU exfiltration and runaway publishers that never trip memory or throttle alerts. Packet-drop tiers highlight queue pressure and qdisc backpressure distinct from UC-3.1.14 overlay gossip or VXLAN asymmetry, and distinct from UC-3.1.21 Falco syscall narratives that do not reconstruct byte totals. UC-3.1.26 registry transport spikes should be correlated before calling a sigma breach malicious.

## Value

Mean time to isolate noisy-neighbor saturation drops when platform teams can name the dominant container, its share of host egress, and the slope of drop counters in one Splunk row instead of correlating packet captures with orchestration metadata by hand. Threat hunting gains a quantitative exfiltration-shaped signal that does not depend on application logs or DNS query exports, which attackers often disable or encrypt after compromise while leaving wire-speed uploads intact. Application owners see fewer unexplained tail-latency tickets because queue drops are visible before HTTP clients exhaust retries. Regulators and assessors asking for evidence of network traffic review receive timestamped exports that tie container identity to byte rates and sustained share, supporting PCI DSS 10.6.1 style review of network traffic and security events alongside SOC 2 CC6.1 logical and physical access monitoring when paired with your broader control set. Economically, one weekend of avoided cross-tenant starvation or one shortened insider-style exfiltration investigation routinely pays back the ingest and engineering cost of dual docker stats and procfs writers for the year.

## Implementation

Ingest docker:stats and linux:proc:net:dev into index=oti_containers via Splunk Add-on for Unix and Linux scripted inputs plus a docker stats JSON poller or cAdvisor scrape. Version container_egress_baseline.csv in git; schedule container_uc_3_1_23_network_io_anomalies every five minutes over earliest=-6h@h; route critical tiers to platform and security jointly; archive weekly CSV snapshots to your evidence index with lookup commit hashes.

## Evidence

Saved search container_uc_3_1_23_network_io_anomalies, lookups lookups/container_egress_baseline.csv with weekly git versioning, dashboard panels for egress sparklines and host share heatmaps, weekly CSV snapshots archived to a restricted evidence index, and corroborating references to Linux cgroup v2 documentation, Docker stats CLI semantics, and cAdvisor Prometheus metric definitions.

## Control test

### Positive scenario

On a lab worker run a controlled low-CPU high-egress upload from a single container while peers stay idle; after three to six five-minute buckets expect critical_egress_anomaly_3sigma_above_baseline or critical_host_egress_share_above_60pct_sustained with host_egress_share_pct greater than sixty for consecutive intervals.

### Negative scenario

Run only steady-state web traffic within documented baselines for twenty-four hours and confirm no critical tiers fire except low_baseline_drift_no_history rows for brand-new containers lacking CSV baseline rows.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control together with the Linux networking observability lead and the fleet SRE who certifies cgroup-scoped byte counters on mixed Compose, Swarm, and bare Docker worker tiers topping fifty thousand containers. UC-3.1.23 is the per-container data-plane throughput and drop-rate axis: cumulative tx_bytes, rx_bytes, tx_dropped, and rx_dropped interpreted at the network namespace boundary, differenced into interval rates, compared against a rolling six-hour statistical envelope, and reconciled to governance baselines in container_egress_baseline.csv. UC-3.1.14 remains the Docker overlay control-plane narrative covering libnetwork gossip, VXLAN tunnel symmetry, and manager inspect drift; it does not replace byte accounting that proves one container suddenly owns the majority of host egress. UC-3.1.21 remains syscall-grade Falco and eBPF behavioral analytics; it does not observe monotonic interface counters the way docker stats or procfs exports do, and it should not be the only signal when exfiltration code keeps CPU and memory flat while saturating the wire. UC-3.1.26 isolates registry pull failures and manifest transport errors; treat spikes that coincide with image layer downloads as sibling context rather than automatic exfiltration. UC-3.1.22 covers HEALTHCHECK probe semantics, UC-3.1.13 covers restart cadence, and neither explains NIC queue drops that surface only as rising tx_dropped counters on a veth pair.

Splunk Add-on for Unix and Linux (Splunkbase 833) must be deployed on every worker that runs Docker Engine or an API-compatible runtime so scripted inputs can emit sourcetype linux:proc:net:dev samples from each monitored network namespace, typically by resolving the container PID namespace root and reading /proc/<pid>/net/dev on the same schedule as docker stats polling. Pair that path with a docker stats JSON stream or a cAdvisor Prometheus scrape reduced to Splunk events tagged sourcetype docker:stats so operators have redundant writers when one path loses field fidelity after an Engine upgrade. Index routing standard for this family is index=oti_containers; do not silently land these metrics beside full-fidelity application logs without retention planning because high-cardinality container_id fields can dominate license if sampling discipline slips.

Publish container_egress_baseline.csv under lookups with columns container_id_pattern (store the full sixty-four character ID when your CMDB exports it, or a stable Compose service key if IDs churn weekly), expected_egress_bytes_per_min_p95, and expected_rx_bytes_per_min_p95 derived from thirty rolling days of the same search without the closing where clause. Refresh the CSV weekly and attach git metadata for auditors. Maintain container_owner.csv with host_id, container_name, owner_team if you route pages through the same macro family as other UC-3.1.x searches even though the closing table in this UC focuses on throughput evidence.

RBAC must allow platform operations to search oti_containers while denying dashboard-only roles raw access to internal image names when regulations require redaction. HEC tokens for supplemental cAdvisor ship pipelines belong in vault with quarterly rotation. Document Mirantis Container Runtime versus Docker CE field naming deltas in props.conf so coalesce lists stay short and upgrades do not silently zero-out counters.

Risk briefing for executives: compromised workloads increasingly exfiltrate through simple HTTPS posts that barely register in CPU dashboards, while legitimate bulk jobs can look like attacks when baselines are stale. Noisy-neighbor saturation is a finance problem as much as a reliability problem because one unrestrained publisher can starve an entire host of egress budget, forcing unrelated services into tail latency. This control gives a single analyst row tying container identity, share of host egress, z-score distance from normal, and drop-rate acceleration so bridge calls start with evidence instead of anecdotes.

Differentiation recap: overlay health, runtime syscall alerts, registry pulls, health flaps, and restart storms are all siblings with distinct runbooks. Merging them collapses signal. Keep this search focused on byte counters and drops so SOC and platform networking can agree on what the data plane did, not only what the orchestrator intended.

Licensing and volume: five-minute aggregates per container per host are modest compared to packet captures, yet fifty thousand containers still produce millions of metricized events per day if you ingest every iface separately. Collapse interfaces only after validating double-counting rules on your stats provider. Legal and privacy: image names may include customer project codes; redact in forwarder transforms when required.

### Step 2 — Configure data collection

On each Linux worker, enable a docker stats poller that executes docker stats --no-trunc --no-stream at sixty to one hundred twenty second cadence and prints JSON Lines to a Universal Forwarder monitor or HEC receiver. Normalize the parser so each container row includes container_id, container_name, image, and network summary fields mapping to tx_bytes, rx_bytes, tx_dropped, rx_dropped with camelCase aliases preserved through props.conf. When you standardize on cAdvisor, configure the container scrape to include per-container network metrics and map container_label_com_docker_* tags into Splunk fields; keep the sourcetype docker:stats for continuity with this SPL or extend the multisearch arm with an OR sourcetype match documented in your local macro.

For linux:proc:net:dev, deploy a privileged scripted input that enumerates running containers, resolves the init PID per container, and reads /proc/<pid>/net/dev for each non-loopback interface you care about. Emit one event per (host_id, container_id, iface, _time) with cumulative counters so streamstats can difference them exactly as it does for docker stats. Validate that short-lived containers still produce at least two samples inside the six-hour window or expect egress_zscore to stay null for burst jobs that are intentionally out of scope.

Clock skew between forwarders and Docker must stay under thirty seconds or sec_w math invents impossible gigabit slopes. Use chrony on every worker and monitor offset. When rootless Docker shifts cgroup paths, confirm the PID you read still matches the container namespace you intend; mistaken PID attachment attributes throughput to the wrong tenant and poisons host_egress_share_pct.

Expected pre-flight searches: index=oti_containers sourcetype=docker:stats earliest=-15m for field presence; index=oti_containers sourcetype=linux:proc:net:dev earliest=-15m for iface cardinality; a timechart of dc(container_id) by host_id to catch collection gaps after deploys.

Governance: record the collector version, poll interval, and forwarder tier in the same configuration management database entry that stores container_egress_baseline.csv ownership so auditors can trace metric lineage end to end.

### Step 3 — Create search and alert

Save the SPL as saved search container_uc_3_1_23_network_io_anomalies with schedule */5 * * * * and the same earliest=-6h@h latest=@h window used in development so six-hour baselines remain comparable week over week. Throttle duplicate critical_host_egress_share_above_60pct_sustained rows per host_id and container_id for thirty minutes when a maintenance flag lookup says a planned bulk transfer is underway, but never throttle critical_egress_anomaly_3sigma_above_baseline without human approval because that tier is the exfiltration-shaped signal.

Understanding the pipeline in operator terms: multisearch fans docker stats and procfs lanes so a silent failure on one writer still leaves the other for triage until you restore parity. sort and streamstats rebuild byte deltas from cumulative counters, clamping negative deltas that appear after counter resets or container recreation. bin span=5m rolls raw per-second slopes into five-minute buckets that align host share denominators across containers on the same host. eventstats sum establishes host_tx_sum for host_egress_share_pct, while streamstats window=2 on the sorted per-container series detects sustained domination above sixty percent for two consecutive buckets. eventstats avg and stdev by container_id provide the six-hour egress_mu and egress_sigma that feed egress_zscore; tune a macro if you need a shorter memory for bursty CI hosts. The join-wrapped inputlookup attaches expected_egress_p95_from_baseline for governance comparisons even though the primary statistical gate uses sigma from live data. severity applies the mandated tier strings in priority order so noisy drop events do not mask sustained share anomalies when both fire. recommended_response gives paging-bridge instructions without opening a wiki.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:

```spl
`comment("UC-3.1.23 Container Network I/O Anomalies. Tunables: index=oti_containers; sourcetypes docker:stats and linux:proc:net:dev; join inputlookup container_egress_baseline.csv on container_id_pattern; statistical window earliest=-6h@h latest=@h; sustained host_egress_share_pct uses two consecutive 5m buckets above 60; drop-rate floors tune tx_dropped_per_min and rx_dropped_per_min thresholds.")`
| multisearch
    [ search index=oti_containers sourcetype="docker:stats" earliest=-6h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval container_id=trim(toString(coalesce(container_id, containerId, Id, id, "")))
      | eval container_name=toString(coalesce(container_name, containerName, name, ""))
      | eval image=toString(coalesce(image, Image, from, ""))
      | eval iface=toString(coalesce(iface, interface, net_iface, "all"))
      | eval tx_bytes=tonumber(tostring(coalesce(tx_bytes, txBytes, network_tx_bytes, net_tx_bytes, "")), 10)
      | eval rx_bytes=tonumber(tostring(coalesce(rx_bytes, rxBytes, network_rx_bytes, net_rx_bytes, "")), 10)
      | eval tx_dropped=tonumber(tostring(coalesce(tx_dropped, txDropped, "")), 10)
      | eval rx_dropped=tonumber(tostring(coalesce(rx_dropped, rxDropped, "")), 10)
      | eval lane="docker_stats"
      | fields _time host_id container_id container_name image iface tx_bytes rx_bytes tx_dropped rx_dropped lane ]
    [ search index=oti_containers sourcetype="linux:proc:net:dev" earliest=-6h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval container_id=trim(toString(coalesce(container_id, containerId, netns_container_id, "")))
      | eval container_name=toString(coalesce(container_name, containerName, task_name, ""))
      | eval image=toString(coalesce(image, Image, ""))
      | eval iface=toString(coalesce(iface, interface, IFACE, dev, ""))
      | where len(iface)>0 AND NOT match(iface, "^(lo|docker0|br-)")
      | eval tx_bytes=tonumber(tostring(coalesce(tx_bytes, tx_bytes_total, TX_bytes, "")), 10)
      | eval rx_bytes=tonumber(tostring(coalesce(rx_bytes, rx_bytes_total, RX_bytes, "")), 10)
      | eval tx_dropped=tonumber(tostring(coalesce(tx_dropped, tx_drop, "")), 10)
      | eval rx_dropped=tonumber(tostring(coalesce(rx_dropped, rx_drop, "")), 10)
      | eval lane="proc_net_dev"
      | fields _time host_id container_id container_name image iface tx_bytes rx_bytes tx_dropped rx_dropped lane ]
| sort 0 + host_id, container_id, iface, _time
| streamstats window=2 current=f global=f last(tx_bytes) AS prev_tx last(rx_bytes) AS prev_rx last(tx_dropped) AS prev_txd last(rx_dropped) AS prev_rxd last(_time) AS prev_ts BY host_id, container_id, iface
| eval tx_delta=if(isnotnull(prev_tx) AND isnotnull(tx_bytes) AND tx_bytes>=prev_tx, tx_bytes - prev_tx, null())
| eval rx_delta=if(isnotnull(prev_rx) AND isnotnull(rx_bytes) AND rx_bytes>=prev_rx, rx_bytes - prev_rx, null())
| eval txd_delta=if(isnotnull(prev_txd) AND isnotnull(tx_dropped) AND tx_dropped>=prev_txd, tx_dropped - prev_txd, null())
| eval rxd_delta=if(isnotnull(prev_rxd) AND isnotnull(rx_dropped) AND rx_dropped>=prev_rxd, rx_dropped - prev_rxd, null())
| eval sec_w=if(isnotnull(prev_ts), _time - prev_ts, null())
| eval tx_bps=if(isnotnull(tx_delta) AND isnotnull(sec_w) AND sec_w>0, tx_delta / sec_w, null())
| eval rx_bps=if(isnotnull(rx_delta) AND isnotnull(sec_w) AND sec_w>0, rx_delta / sec_w, null())
| eval tx_bytes_per_min_raw=if(isnotnull(tx_bps), tx_bps * 60, null())
| eval rx_bytes_per_min_raw=if(isnotnull(rx_bps), rx_bps * 60, null())
| eval tx_dropped_per_min_raw=if(isnotnull(txd_delta) AND isnotnull(sec_w) AND sec_w>0, (txd_delta / sec_w) * 60, null())
| eval rx_dropped_per_min_raw=if(isnotnull(rxd_delta) AND isnotnull(sec_w) AND sec_w>0, (rxd_delta / sec_w) * 60, null())
| where isnotnull(tx_bytes_per_min_raw) OR isnotnull(rx_bytes_per_min_raw)
| bin _time span=5m AS t5
| stats sum(tx_bytes_per_min_raw) AS tx_bytes_per_min sum(rx_bytes_per_min_raw) AS rx_bytes_per_min sum(tx_dropped_per_min_raw) AS tx_dropped_per_min sum(rx_dropped_per_min_raw) AS rx_dropped_per_min values(lane) AS lane_mv BY host_id, container_id, container_name, image, t5
| eval lane=mvindex(lane_mv, 0)
| sort 0 + host_id, container_id, t5
| eventstats sum(tx_bytes_per_min) AS host_tx_sum BY host_id, t5
| eval host_egress_share_pct=if(host_tx_sum>0, round(100 * tx_bytes_per_min / host_tx_sum, 2), null())
| streamstats window=2 current=t global=f last(host_egress_share_pct) AS prev_share BY host_id, container_id
| eval sustained_share_gt60=if(host_egress_share_pct>60 AND prev_share>60, 1, 0)
| eventstats avg(tx_bytes_per_min) AS egress_mu stdev(tx_bytes_per_min) AS egress_sigma BY container_id
| eval egress_zscore=if(isnotnull(egress_sigma) AND egress_sigma>0 AND isnotnull(tx_bytes_per_min), round((tx_bytes_per_min - egress_mu) / egress_sigma, 3), null())
| join type=left max=0 container_id
    [| inputlookup container_egress_baseline.csv
     | eval container_id=trim(toString(coalesce(container_id_pattern, workload_container_key, "")))
     | eval expected_egress_p95_from_baseline=tonumber(tostring(coalesce(expected_egress_bytes_per_min_p95, expected_egress_p95, "")), 10)
     | fields container_id expected_egress_p95_from_baseline ]
| eval severity=case(
    sustained_share_gt60=1 AND host_egress_share_pct>60, "critical_host_egress_share_above_60pct_sustained",
    isnotnull(egress_zscore) AND egress_zscore>=3, "critical_egress_anomaly_3sigma_above_baseline",
    isnotnull(tx_dropped_per_min) AND tx_dropped_per_min>500, "high_tx_dropped_rate_above_threshold",
    isnotnull(rx_dropped_per_min) AND rx_dropped_per_min>500, "high_rx_dropped_rate_above_threshold",
    isnotnull(egress_zscore) AND egress_zscore>=2 AND egress_zscore<3, "medium_egress_2sigma_above_baseline",
    isnull(expected_egress_p95_from_baseline) OR expected_egress_p95_from_baseline<=0, "low_baseline_drift_no_history",
    true(), null())
| eval recommended_response=case(
    severity="critical_host_egress_share_above_60pct_sustained", "Throttle or reschedule the dominant container on the host, enable fair-queueing or egress shaping at the bridge, split noisy tenants to dedicated workers, and compare per-link utilization with host NIC counters to confirm starvation of peer containers.",
    severity="critical_egress_anomaly_3sigma_above_baseline", "Treat as potential bulk exfiltration or runaway publisher: capture layer-4 flow metadata in parallel, isolate the container network namespace under change control, rotate credentials touched by that workload, and compare image digest to golden build.",
    severity="high_tx_dropped_rate_above_threshold", "Investigate qdisc backpressure, ring-buffer drops, and MTU consistency on the veth path; correlate with concurrent deploys and traffic-policy changes; capture ss -ti and tc qdisc show from the worker.",
    severity="high_rx_dropped_rate_above_threshold", "Inspect receive-side steering, RSS queues, and burst ingress from upstream load balancers; validate container receive buffers and whether an L7 proxy batches responses; rule out NIC driver regressions after kernel upgrades.",
    severity="medium_egress_2sigma_above_baseline", "Notify the owning squad, confirm scheduled batch jobs or cache warmers, tighten baseline row in container_egress_baseline.csv if legitimate, and escalate if the pattern repeats without a change ticket.",
    severity="low_baseline_drift_no_history", "Publish a baseline row for this container class, backfill expected_egress_bytes_per_min_p95 from thirty days of samples, and keep monitoring until statistical gates stabilize.",
    true(), "Correlate docker:stats and linux:proc:net:dev lanes, then close with platform and service owner sign-off.")
| where isnotnull(severity)
| table container_id container_name host_id image tx_bytes_per_min rx_bytes_per_min tx_dropped_per_min rx_dropped_per_min host_egress_share_pct egress_zscore severity recommended_response expected_egress_p95_from_baseline
```

Alert actions: route critical tiers to platform networking and the container security liaison jointly, attach the row, and include deep links to host NIC utilization dashboards. Medium and low tiers should open tickets with the owning squad from container_owner.csv when that lookup is wrapped in a follow-on join your deployment adds after the base table.

### Step 4 — Validate

Positive path A — exfiltration-shaped egress: in a lab container, start a controlled upload of a multi-gigabyte object to an approved test bucket while keeping CPU pegged low with a single-threaded client. Expect critical_egress_anomaly_3sigma_above_baseline within three to six five-minute buckets as egress_zscore crosses three while CPU dashboards remain calm, proving the value of byte counters versus process-only telemetry.

Positive path B — noisy neighbor: on a shared worker, run two containers, one with iperf or an equivalent UDP generator toward an internal sink and one idle web tier. Expect critical_host_egress_share_above_60pct_sustained on the generator while host_egress_share_pct stays above sixty for two consecutive buckets and peer containers show depressed tx_bytes_per_min. Document NIC saturation with sar -n DEV for the runbook screenshot.

Positive path C — drop storm: lower the MTU on a veth intentionally or apply a tight tc tbf limiter, then push bursty traffic through the interface. Expect high_tx_dropped_rate_above_threshold or high_rx_dropped_rate_above_threshold when tx_dropped_per_min or rx_dropped_per_min crosses the documented floor. Restore MTU and qdisc under change control immediately after capture.

Negative path — healthy steady state: run a representative service at baseline throughput for twenty-four hours and confirm the saved search emits only low_baseline_drift_no_history rows for brand-new containers lacking CSV rows, not for established services.

Field sanity: rename fields in a sandbox forwarder to camelCase-only payloads and confirm coalesce still extracts tx_bytes and rx_bytes. RBAC: readers without oti_containers must see zero rows. Correlation: when UC-3.1.26 registry errors spike, expect correlated tx_bytes from layer pulls; annotate incidents so SOC does not mislabel pulls as exfiltration.

Performance test: run Job Inspector during Monday peaks; if scan cost exceeds budget, summarize linux:proc:net:dev into a metrics index at five-minute cadence while retaining raw samples for twelve hours of drilldown.

### Step 5 — Operationalize and troubleshoot

Case 1 — streamstats emits null slopes after Engine restart: cumulative counters reset to zero and the first delta after restart is skipped by design. Wait two poll intervals or add a reset detector that nulls the first sample per container_id after a docker events restart hint.

Case 2 — host_egress_share_pct sums to more than one hundred across rows in the same bucket: double-counted interfaces or duplicated docker stats lines. Deduplicate on container_id and iface before the bin stage or collapse to a single aggregate iface per provider.

Case 3 — egress_zscore flatlines near zero despite visible spikes: stdev collapsed because the container is new inside the six-hour window. Extend earliest or seed baselines from container_egress_baseline.csv using a secondary eval gate.

Case 4 — linux:proc:net:dev missing for Swarm tasks: the PID enumerator may be racing task churn. Slow the enumeration loop slightly and align it to docker events start hooks so every task ID maps before procfs reads.

Case 5 — sustained_share_gt60 fires during approved backup windows: add backup_window_flag to the baseline CSV or a wrapper macro keyed on container_name patterns like restic or velero rather than raising thresholds globally.

Case 6 — join to container_egress_baseline misses after truncate: ensure container_id_pattern stores the full ID without sha256: prefix mismatch; normalize with replace(container_id,"sha256:","") in both arms.

Case 7 — false critical from image layer pulls: cross-reference UC-3.1.26 pull error timelines and exclude hosts where docker pull traffic dominates by tagging registry_pull_minutes in a maintenance lookup.

Case 8 — rx_dropped spikes only on hypervisor SR-IOV guests: the symptom may live outside the container namespace; pair with host-level NIC dashboards before blaming a workload.

Case 9 — OT edge gateways with frozen procfs: hardened appliances may block /proc/<pid>/net/dev for non-root collectors; fall back to docker stats only and document the gap in the host-class registry.

Case 10 — dual ship from OTel and TA duplicates counters: enforce a single writer per host class or deduplicate on source and container_id before streamstats.

Case 11 — Compose project name churn breaks baselines: key baselines on image digest plus Compose service label instead of ephemeral container_name when developers recreate containers hourly.

Case 12 — finance challenges ingest cost: demonstrate one prevented exfiltration investigation shortened by hours equals months of metric volume spend.

Dashboard layout: top row single values for count of critical tiers, distinct hosts with sustained share breaches, and mean egress_zscore across firing containers. Second row timechart of tx_bytes_per_min by container_name for top talkers. Third row heatmap of host_egress_share_pct by host_id and t5. Fourth row overlay tx_dropped_per_min and rx_dropped_per_min for containers exceeding thresholds. Provide drilldowns to raw docker:stats and linux:proc:net:dev for the same container_id and window.

Evidence retention: weekly CSV exports of alert rows to a restricted evidence index with git commit hashes for container_egress_baseline.csv satisfy internal audit samples referencing PCI DSS style network monitoring expectations and SOC 2 change monitoring narratives without claiming sole compliance sufficiency.

Governance: quarterly replay one historical incident through the SPL after Docker Engine or kernel upgrades affecting veth drivers. Update the comment macro when indexes move. Require lookup owners to approve threshold changes inside the same change record that adjusts physical NIC capacity or tenant egress policies.

Closing checklist: five Step headers with em dashes; multisearch lists docker:stats and linux:proc:net:dev; streamstats differences cumulative counters; eventstats supplies host totals and per-container mu and sigma; join wraps inputlookup container_egress_baseline.csv; severity uses only the mandated tier strings; closing table lists thirteen analyst columns including host_egress_share_pct, egress_zscore, and expected_egress_p95_from_baseline; JSON narratives contain no asterisk emphasis pairs.

## SPL

```spl
`comment("UC-3.1.23 Container Network I/O Anomalies. Tunables: index=oti_containers; sourcetypes docker:stats and linux:proc:net:dev; join inputlookup container_egress_baseline.csv on container_id_pattern; statistical window earliest=-6h@h latest=@h; sustained host_egress_share_pct uses two consecutive 5m buckets above 60; drop-rate floors tune tx_dropped_per_min and rx_dropped_per_min thresholds.")`
| multisearch
    [ search index=oti_containers sourcetype="docker:stats" earliest=-6h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval container_id=trim(toString(coalesce(container_id, containerId, Id, id, "")))
      | eval container_name=toString(coalesce(container_name, containerName, name, ""))
      | eval image=toString(coalesce(image, Image, from, ""))
      | eval iface=toString(coalesce(iface, interface, net_iface, "all"))
      | eval tx_bytes=tonumber(tostring(coalesce(tx_bytes, txBytes, network_tx_bytes, net_tx_bytes, "")), 10)
      | eval rx_bytes=tonumber(tostring(coalesce(rx_bytes, rxBytes, network_rx_bytes, net_rx_bytes, "")), 10)
      | eval tx_dropped=tonumber(tostring(coalesce(tx_dropped, txDropped, "")), 10)
      | eval rx_dropped=tonumber(tostring(coalesce(rx_dropped, rxDropped, "")), 10)
      | eval lane="docker_stats"
      | fields _time host_id container_id container_name image iface tx_bytes rx_bytes tx_dropped rx_dropped lane ]
    [ search index=oti_containers sourcetype="linux:proc:net:dev" earliest=-6h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval container_id=trim(toString(coalesce(container_id, containerId, netns_container_id, "")))
      | eval container_name=toString(coalesce(container_name, containerName, task_name, ""))
      | eval image=toString(coalesce(image, Image, ""))
      | eval iface=toString(coalesce(iface, interface, IFACE, dev, ""))
      | where len(iface)>0 AND NOT match(iface, "^(lo|docker0|br-)")
      | eval tx_bytes=tonumber(tostring(coalesce(tx_bytes, tx_bytes_total, TX_bytes, "")), 10)
      | eval rx_bytes=tonumber(tostring(coalesce(rx_bytes, rx_bytes_total, RX_bytes, "")), 10)
      | eval tx_dropped=tonumber(tostring(coalesce(tx_dropped, tx_drop, "")), 10)
      | eval rx_dropped=tonumber(tostring(coalesce(rx_dropped, rx_drop, "")), 10)
      | eval lane="proc_net_dev"
      | fields _time host_id container_id container_name image iface tx_bytes rx_bytes tx_dropped rx_dropped lane ]
| sort 0 + host_id, container_id, iface, _time
| streamstats window=2 current=f global=f last(tx_bytes) AS prev_tx last(rx_bytes) AS prev_rx last(tx_dropped) AS prev_txd last(rx_dropped) AS prev_rxd last(_time) AS prev_ts BY host_id, container_id, iface
| eval tx_delta=if(isnotnull(prev_tx) AND isnotnull(tx_bytes) AND tx_bytes>=prev_tx, tx_bytes - prev_tx, null())
| eval rx_delta=if(isnotnull(prev_rx) AND isnotnull(rx_bytes) AND rx_bytes>=prev_rx, rx_bytes - prev_rx, null())
| eval txd_delta=if(isnotnull(prev_txd) AND isnotnull(tx_dropped) AND tx_dropped>=prev_txd, tx_dropped - prev_txd, null())
| eval rxd_delta=if(isnotnull(prev_rxd) AND isnotnull(rx_dropped) AND rx_dropped>=prev_rxd, rx_dropped - prev_rxd, null())
| eval sec_w=if(isnotnull(prev_ts), _time - prev_ts, null())
| eval tx_bps=if(isnotnull(tx_delta) AND isnotnull(sec_w) AND sec_w>0, tx_delta / sec_w, null())
| eval rx_bps=if(isnotnull(rx_delta) AND isnotnull(sec_w) AND sec_w>0, rx_delta / sec_w, null())
| eval tx_bytes_per_min_raw=if(isnotnull(tx_bps), tx_bps * 60, null())
| eval rx_bytes_per_min_raw=if(isnotnull(rx_bps), rx_bps * 60, null())
| eval tx_dropped_per_min_raw=if(isnotnull(txd_delta) AND isnotnull(sec_w) AND sec_w>0, (txd_delta / sec_w) * 60, null())
| eval rx_dropped_per_min_raw=if(isnotnull(rxd_delta) AND isnotnull(sec_w) AND sec_w>0, (rxd_delta / sec_w) * 60, null())
| where isnotnull(tx_bytes_per_min_raw) OR isnotnull(rx_bytes_per_min_raw)
| bin _time span=5m AS t5
| stats sum(tx_bytes_per_min_raw) AS tx_bytes_per_min sum(rx_bytes_per_min_raw) AS rx_bytes_per_min sum(tx_dropped_per_min_raw) AS tx_dropped_per_min sum(rx_dropped_per_min_raw) AS rx_dropped_per_min values(lane) AS lane_mv BY host_id, container_id, container_name, image, t5
| eval lane=mvindex(lane_mv, 0)
| sort 0 + host_id, container_id, t5
| eventstats sum(tx_bytes_per_min) AS host_tx_sum BY host_id, t5
| eval host_egress_share_pct=if(host_tx_sum>0, round(100 * tx_bytes_per_min / host_tx_sum, 2), null())
| streamstats window=2 current=t global=f last(host_egress_share_pct) AS prev_share BY host_id, container_id
| eval sustained_share_gt60=if(host_egress_share_pct>60 AND prev_share>60, 1, 0)
| eventstats avg(tx_bytes_per_min) AS egress_mu stdev(tx_bytes_per_min) AS egress_sigma BY container_id
| eval egress_zscore=if(isnotnull(egress_sigma) AND egress_sigma>0 AND isnotnull(tx_bytes_per_min), round((tx_bytes_per_min - egress_mu) / egress_sigma, 3), null())
| join type=left max=0 container_id
    [| inputlookup container_egress_baseline.csv
     | eval container_id=trim(toString(coalesce(container_id_pattern, workload_container_key, "")))
     | eval expected_egress_p95_from_baseline=tonumber(tostring(coalesce(expected_egress_bytes_per_min_p95, expected_egress_p95, "")), 10)
     | fields container_id expected_egress_p95_from_baseline ]
| eval severity=case(
    sustained_share_gt60=1 AND host_egress_share_pct>60, "critical_host_egress_share_above_60pct_sustained",
    isnotnull(egress_zscore) AND egress_zscore>=3, "critical_egress_anomaly_3sigma_above_baseline",
    isnotnull(tx_dropped_per_min) AND tx_dropped_per_min>500, "high_tx_dropped_rate_above_threshold",
    isnotnull(rx_dropped_per_min) AND rx_dropped_per_min>500, "high_rx_dropped_rate_above_threshold",
    isnotnull(egress_zscore) AND egress_zscore>=2 AND egress_zscore<3, "medium_egress_2sigma_above_baseline",
    isnull(expected_egress_p95_from_baseline) OR expected_egress_p95_from_baseline<=0, "low_baseline_drift_no_history",
    true(), null())
| eval recommended_response=case(
    severity="critical_host_egress_share_above_60pct_sustained", "Throttle or reschedule the dominant container on the host, enable fair-queueing or egress shaping at the bridge, split noisy tenants to dedicated workers, and compare per-link utilization with host NIC counters to confirm starvation of peer containers.",
    severity="critical_egress_anomaly_3sigma_above_baseline", "Treat as potential bulk exfiltration or runaway publisher: capture layer-4 flow metadata in parallel, isolate the container network namespace under change control, rotate credentials touched by that workload, and compare image digest to golden build.",
    severity="high_tx_dropped_rate_above_threshold", "Investigate qdisc backpressure, ring-buffer drops, and MTU consistency on the veth path; correlate with concurrent deploys and traffic-policy changes; capture ss -ti and tc qdisc show from the worker.",
    severity="high_rx_dropped_rate_above_threshold", "Inspect receive-side steering, RSS queues, and burst ingress from upstream load balancers; validate container receive buffers and whether an L7 proxy batches responses; rule out NIC driver regressions after kernel upgrades.",
    severity="medium_egress_2sigma_above_baseline", "Notify the owning squad, confirm scheduled batch jobs or cache warmers, tighten baseline row in container_egress_baseline.csv if legitimate, and escalate if the pattern repeats without a change ticket.",
    severity="low_baseline_drift_no_history", "Publish a baseline row for this container class, backfill expected_egress_bytes_per_min_p95 from thirty days of samples, and keep monitoring until statistical gates stabilize.",
    true(), "Correlate docker:stats and linux:proc:net:dev lanes, then close with platform and service owner sign-off.")
| where isnotnull(severity)
| table container_id container_name host_id image tx_bytes_per_min rx_bytes_per_min tx_dropped_per_min rx_dropped_per_min host_egress_share_pct egress_zscore severity recommended_response expected_egress_p95_from_baseline
```

## CIM SPL

```spl
| tstats summariesonly=t sum(All_Traffic.bytes_out) AS bytes_out sum(All_Traffic.bytes_in) AS bytes_in FROM datamodel=Network_Traffic WHERE nodename=All_Traffic earliest=-6h@h latest=now BY All_Traffic.src span=5m
| rename All_Traffic.src AS host_id
| append [ | tstats summariesonly=t avg(Performance.cpu_load_percent) AS cpu_avg FROM datamodel=Performance WHERE nodename=Performance.HostPerformance earliest=-6h@h latest=now BY Performance.host span=5m
| rename Performance.host AS host_id ]
| stats latest(bytes_out) AS bytes_out latest(cpu_avg) AS cpu_avg BY host_id
```

## Visualization

Per-container egress sparklines with annotated sigma breaches; top-N egress byte-rate bar charts faceted by host_id; host saturation heatmap of host_egress_share_pct across five-minute buckets; paired panel correlating tx_dropped_per_min and rx_dropped_per_min with overlay markers for deploys and tc changes.

## Known False Positives

Machine-learning data loaders that stream multi-gigabyte training shards hourly will cross three sigma legitimately unless container_egress_baseline.csv encodes their workload class. Log forwarders such as Fluent Bit, Fluentd, Vector, or Promtail batching to remote indexes can spike egress without malicious intent; pair timestamps with known configuration pushes. Backup and DR containers running restic, kopia, or Velero toward object storage produce sustained high share that should be tagged in the baseline lookup. Image layer pulls during rolling upgrades can inflate tx_bytes; always correlate UC-3.1.26 registry telemetry before escalating. Scheduled tc traffic-policy enforcement or temporary rate limits may raise tx_dropped during the window even when applications are healthy. OS package refresh jobs inside privileged maintenance containers create predictable egress bursts after patch Tuesday style events. CI agents and synthetic stress harnesses intentionally saturate links for minutes at a time. Canary deployments that replay production traffic multipliers can look like exfiltration until labeled. Mis-mapped PIDs in procfs collectors occasionally attribute host traffic to the wrong container until the enumerator script is fixed; treat the first firing as a collection bug when host share sums look impossible.

## References

- [Linux kernel documentation — cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html)
- [Docker CLI reference — docker container stats](https://docs.docker.com/reference/cli/docker/container/stats/)
- [cAdvisor storage documentation — Prometheus metrics](https://github.com/google/cadvisor/blob/master/docs/storage/prometheus.md)
- [Splunk Lantern — Docker data sources](https://lantern.splunk.com/Data_Sources/Docker)
- [Sysdig — Detecting SCARLETEEL with Sysdig Secure](https://sysdig.com/blog/detect-scarleteel-sysdig-secure)
- [CIS Benchmarks program](https://www.cisecurity.org/cis-benchmarks)
