<!-- AUTO-GENERATED from UC-3.1.11.json — DO NOT EDIT -->

---
id: "3.1.11"
title: "Docker Daemon Resource Limits Monitoring"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.1.11 · Docker Daemon Resource Limits Monitoring

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch whether the kitchen manager who coordinates every food tray is running out of hands, pantry labels, or delivery slots. When their personal limits fill up, new dishes wait with no error bell, and dinner looks late for no obvious reason until someone counts what the manager is already holding.*

---

## Description

Monitors dockerd-process resource ceilings that fail silently while clients only see timeouts: open file descriptors versus hard `nofile` limits from `/proc/$pid/limits`, thread counts from `/proc/$pid/status`, optional dockerd CPU percent from the same probe or from Prometheus `engine_daemon_engine_cpu_percent`, registry pull queue depth versus `max-concurrent-downloads` / `max-concurrent-uploads` semantics scraped from dockerd metrics, and inode utilization on the graph root from `linux:df_inodes` because overlay2 consumes inodes faster than bytes. The SPL joins `dockerd_resource_baseline.csv` so drift is measured against signed host-class expectations, uses `streamstats` for FD leak slope, and `eventstats` for fleet FD and inode percentiles. This is complementary to UC-3.1.8, which classifies dockerd journal errors and engine API 5xx narratives: a daemon can remain log-quiet while handle tables fill. It does not replace UC-3.1.14 overlay gossip diagnostics, UC-3.1.2 cgroup OOM kills, UC-3.1.3 container CPU throttling, UC-3.1.13 restart cadence, or UC-3.1.16 volume byte trending.

## Value

Quantified outcomes include shortened mean time to detect silent deploy queues caused by daemon admission limits rather than application bugs, documented evidence for raising systemd `LimitNOFILE` and tuning `daemon.json` concurrency with before-and-after Splunk rows attached to change records, prevention of graph-root inode outages that `df -h` alone misses, and FinOps-friendly pruning cadence when `inode_pct` trends align with stale image retention policies. Fleet-wide percentile context reduces noisy one-off pages while still catching hosts crossing ninety percent FD or inode pressure. Pull-queue saturation detection saves Patch Tuesday war rooms from chasing container healthchecks when the real bottleneck is registry fan-in capped by daemon concurrency defaults across ten thousand docker hosts.

## Implementation

Deploy Splunk_TA_nix-style scripted inputs for `linux:proc:dockerd_status` and `linux:df_inodes` into `index=oti_containers`, configure Splunk OpenTelemetry Collector to scrape dockerd `/metrics` into `docker:metrics`, publish `lookups/dockerd_resource_baseline.csv`, save `container_uc_3_1_11_daemon_resource_ceilings` every five minutes on `earliest=-4h@h latest=@h`, route critical FD and inode tiers to platform on-call, and archive weekly CSV snapshots with baseline commit hashes.

## Evidence

Saved search container_uc_3_1_11_daemon_resource_ceilings; lookup dockerd_resource_baseline.csv versioned in git; weekly CSV exports to a restricted evidence index; dashboard panels for fd_pct heatmap and inode_pct trend. External grounding includes Linux proc(5) limit semantics, Docker daemon.json concurrency and metrics documentation, Moby community threads on dockerd file-descriptor exhaustion, and kernel nf_conntrack discussions when pull storms interact with network path limits.

## Control test

### Positive scenario

On a lab Linux host lower LimitNOFILE, generate concurrent docker activity until open_fds exceeds ninety percent of hard_nofile_limit in linux:proc:dockerd_status, execute the saved search, and expect critical_fd_pct_above_90_imminent_exhaustion with non-null recommended_response.

### Negative scenario

On a healthy host with fd_pct below forty, inode_pct below forty on /var/lib/docker, and quiet docker:metrics pull queue, verify the saved search returns no severity row across multiple five-minute intervals.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control with the Linux observability engineer who certifies Splunk Add-on for Linux scripted inputs and the container runtime SRE who signs dockerd systemd units across the worker fleet. UC-3.1.11 is the dockerd-process and API-concurrency ceiling axis: it watches the supervisor itself running out of room to hold sockets, threads, and registry pull workers, plus inode starvation on the graph root that blocks new layer creation. UC-3.1.8 remains the journald and Prometheus error-stream narrative when dockerd prints panics, storage-driver faults, or engine API 5xx lines. UC-3.1.14 isolates overlay control-plane and VXLAN data-plane health. UC-3.1.2 and UC-3.1.4 read cgroup memory for workloads, not /proc entries for the daemon PID. UC-3.1.3 covers container CPU throttling, not dockerd single-process saturation. UC-3.1.13 measures restart cadence on supervised containers, which can look quiet while the daemon is merely too full of handles to accept new creates. Keep those boundaries explicit in runbooks so incident commanders route FD and inode rows to platform capacity engineering while routing overlay gossip rows to networking.

You need three telemetry writers before scheduling the saved search. First, sourcetype linux:proc:dockerd_status must materialize from a privileged interval job on each host that resolves the dockerd PID (pidof dockerd or cgroup-aware lookup), then reads /proc/$pid/status for Threads and FDSize hints, /proc/$pid/limits for Max open files soft and hard pairs, and counts open entries under /proc/$pid/fd (or uses the same count your forwarder already exposes as open_fds). Normalize host_id to the lowercase short hostname Universal Forwarders emit. Second, sourcetype linux:df_inodes should capture df -i output (or statfs equivalents) for the mount hosting /var/lib/docker, emitting inode_pct used or derivable IUsePercent style fields. Third, sourcetype docker:metrics lands Prometheus exposition scraped from the dockerd metrics listener enabled through daemon.json metrics-addr, typically bound to loopback. Splunk OpenTelemetry Collector prometheus receiver polls that endpoint and forwards counters or gauges you map into pull_queue_depth and max_concurrent_downloads when your build exports them; otherwise extend the receiver mapping with a textf processor that reads custom labels your team already emits from an out-of-tree exporter.

Governance lookup dockerd_resource_baseline.csv carries host_id, baseline_fd_pct_warn (danger band start, often near seventy percent of hard nofile), baseline_thread_max (Threads count above which you investigate leaks), and baseline_cpu_pct (rolling median dockerd_cpu_pct for that host class). Refresh after golden AMI promotions, kernel bumps, or deliberate daemon.json concurrency changes. Roles must search index=oti_containers for platform engineers; restrict docker:metrics if labels leak registry hostnames.

Risk briefing: when open_fds divided by hard_nofile_limit crosses ninety percent, new container creates and even local docker ps calls can stall without a single ERROR line in journald because the failure is resource admission, not application logic. When inode_pct on the graph mount crosses ninety percent while disk free space still looks comfortable, dockerd may refuse layer extraction and operators only see client-side context deadline exceeded during pulls. When max-concurrent-downloads stays at default three on ten thousand hosts and a patch Tuesday schedules wide docker pull, pull_hot rows explain deploy queues that no container-level alert will name. Slow leaks that move fd_leak_slope_per_hr upward for days often trace to plugins, stuck event streams, or client libraries that never close unix socket connections to docker.sock.

Licensing note: proc scrapes are tiny; Prometheus scrapes per host every fifteen seconds add up across fifty thousand nodes, so land docker:metrics in a metrics-friendly index with shorter hot retention and keep linux:proc:dockerd_status on a logs index with governance review. Legal and privacy: /proc snapshots must not include environment files from unrelated processes; scope the scripted input to dockerd PID only.

Differentiation recap: this UC never tries to replace UC-3.1.8 log taxonomy, UC-3.1.14 overlay convergence, or UC-3.1.2 OOM analysis. It is the silent ceiling detector for the daemon process and graph filesystem headroom.

### Step 2 — Configure data collection

On every Linux worker running Docker CE, Mirantis Container Runtime, or an approved enterprise Engine build, install a systemd timer or Splunk modular input that runs every sixty seconds (or faster during change windows) to resolve dockerd main PID and emit one linux:proc:dockerd_status event per poll. The script should parse /proc/$pid/limits lines for open files and max processes, /proc/$pid/status for Threads, and count directory entries under /proc/$pid/fd. When counting fds is too expensive on overloaded hosts, approximate with readlink bulk sampling only after CAB approval, but Fortune-500 estates usually accept the cost on dockerd alone because cardinality is one row per host per minute, not per container.

Map hard_nofile_limit from the Max open files hard column and open_fds from the fd count. Include dockerd_cpu_pct if you already compute jiffies from /proc/$pid/stat in the same script; otherwise ingest engine_daemon_engine_cpu_percent from docker:metrics and coalesce in the SPL as implemented. Preserve camelCase aliases emitted by experimental collectors.

For linux:df_inodes, wrap df -Pi (POSIX inode columns) or parse statfs in Python, tagging mount_point /var/lib/docker when docker-root moves, publish inode_pct consistently with df human output. Restrict to docker-relevant mounts to control volume.

Enable dockerd Prometheus metrics per vendor documentation: metrics-addr on loopback, experimental flag only when required on older engines, reload dockerd under change control. Configure Splunk OpenTelemetry Collector with a prometheus receiver job scraping https or http localhost:9323/metrics depending on your tls settings. Normalize metric names into metric_name and value fields Splunk expects. If your distribution lacks pull queue gauges, add a sidecar exporter that watches dockerd debug pprof goroutine stacks during incidents only, not continuous high-cardinality scraping.

Security hygiene: metrics endpoints stay on loopback; never bind 0.0.0.0 for convenience. UC-3.1.25 already covers accidental exposure; this UC assumes localhost-only scraping tunneled or agent-local.

Validate on a canary host: compare Splunk open_fds to ls /proc/$(pidof dockerd)/fd | wc -l within one interval, compare fd_pct to manual calculation, and confirm df -i inode_pct matches Splunk linux:df_inodes. Skew beyond ninety seconds between host clock and Splunk _time breaks streamstats windows; enforce chrony.

### Step 3 — Create the search and alert

Save the SPL as saved search container_uc_3_1_11_daemon_resource_ceilings with schedule every five minutes and time range earliest=-4h@h latest=@h so streamstats sees enough history for fd leak slope while keeping scan cost bounded. Throttle duplicate critical_fd_pct_above_90_imminent_exhaustion pages per host_id for thirty minutes unless fd_pct climbs another five points in the same hour. Do not throttle critical_inode_above_90_dockerd_layer_creation_blocked because inode exhaustion accelerates nonlinearly once dentry caches churn.

Understanding the pipeline: the comment macro records indexes, sourcetypes, lookup names, pull_depth_mult, and default concurrency assumptions. streamstats window=18 on linux:proc:dockerd_status estimates fd_leak_slope_per_hr for leak triage even when severity is still low_baseline_drift. eventstats perc90(fd_pct) and perc95(inode_pct) add fleet context for bridge calls so a host at seventy-two percent fd_pct is read against fleet_fd_p90 rather than arbitrary gut feel. Joined docker:metrics supplies pull_queue_depth and max_concurrent_downloads with coalesce lists tolerating OTel label naming drift. streamstats time_window=30s max(pull_queue_depth) implements the thirty-second sustained queue heuristic before pull_hot asserts. inputlookup-wrapped dockerd_resource_baseline.csv join keeps governance reviewers satisfied that baselines are explicit. The case ladder emits only the six mandated severity strings or null. recommended_response encodes immediate operator actions per tier.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:


```spl
`comment("UC-3.1.11 Docker Daemon Resource Limits Monitoring. Daemon FD, thread, CPU ceilings; Prometheus pull-queue context; /var/lib/docker inode headroom. Tunables: index=oti_containers; sourcetypes linux:proc:dockerd_status docker:metrics linux:df_inodes; lookup dockerd_resource_baseline.csv; earliest=-4h@h latest=@h; fd_crit_pct=90 inode_crit_pct=90 dockerd_cpu_crit=90; pull_depth_mult=2; default_max_concurrent_downloads=3")`
| search index=oti_containers sourcetype="linux:proc:dockerd_status" earliest=-4h@h latest=@h
| eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
| eval dockerd_pid=tonumber(tostring(coalesce(dockerd_pid, dockerdPid, pid, "")), 10)
| eval open_fds=tonumber(tostring(coalesce(open_fds, openFds, open_fd_count, fds_open, "")), 10)
| eval hard_nofile_limit=tonumber(tostring(coalesce(hard_nofile_limit, hardNofileLimit, nofile_hard, limits_nofile_hard, "")), 10)
| eval threads=tonumber(tostring(coalesce(threads, thread_count, Threads, proc_threads, "")), 10)
| eval dockerd_cpu_pct=tonumber(tostring(coalesce(dockerd_cpu_pct, dockerdCpuPct, engine_daemon_engine_cpu_percent, "")), 10)
| eval fd_pct=if(isnotnull(open_fds) AND isnotnull(hard_nofile_limit) AND hard_nofile_limit>0, round(100.0 * open_fds / hard_nofile_limit, 2), null())
| sort 0 + host_id, _time
| streamstats window=18 current=t global=f first(open_fds) AS fds_first last(open_fds) AS fds_last first(_time) AS t_first last(_time) AS t_last BY host_id
| eval fd_leak_slope_per_hr=if(isnotnull(fds_last) AND isnotnull(fds_first) AND isnotnull(t_last) AND isnotnull(t_first) AND (t_last>t_first), round((fds_last - fds_first) / max(0.0001, ((t_last - t_first) / 3600.0)), 4), null())
| eventstats perc90(fd_pct) AS fleet_fd_p90
| join type=left max=0 host_id
    [| search index=oti_containers sourcetype="docker:metrics" earliest=-4h@h latest=@h
     | eval host_id=lower(toString(coalesce(host, Host, hostname, instance, dest, "")))
     | eval metric_name=lower(toString(coalesce(metric_name, name, __name__, "")))
     | eval mv=tonumber(tostring(coalesce(value, metric_value, "")), 10)
     | eval pull_queue_depth=if(match(metric_name, "(?i)pull|image|download|layer|registry") AND match(metric_name, "(?i)queue|pending|backlog|wait|depth|inflight"), mv, null())
     | eval max_concurrent_downloads=if(match(metric_name, "(?i)max_concurrent_downloads|concurrent_download"), mv, null())
     | eval pull_queue_depth=coalesce(pull_queue_depth, tonumber(tostring(coalesce(pullQueueDepth, engine_pull_queue_depth, pending_image_pulls, "")), 10))
     | eval max_concurrent_downloads=coalesce(max_concurrent_downloads, tonumber(tostring(coalesce(maxConcurrentDownloads, daemon_max_pulls, "")), 10))
     | stats latest(pull_queue_depth) AS pull_queue_depth latest(max_concurrent_downloads) AS max_concurrent_downloads BY host_id ]
| fillnull value=0 pull_queue_depth
| eval max_concurrent_downloads=coalesce(max_concurrent_downloads, 3)
| eval pull_depth_mult=2
| streamstats time_window=30s current=t global=f max(pull_queue_depth) AS pull_q_peak_30s BY host_id
| eval pull_hot=if(pull_q_peak_30s > (pull_depth_mult * max_concurrent_downloads), 1, 0)
| join type=left max=0 host_id
    [| search index=oti_containers sourcetype="linux:df_inodes" earliest=-4h@h latest=@h
     | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
     | eval inode_pct=tonumber(tostring(coalesce(inode_pct, inode_used_pct, IUsePercent, ipcent, "")), 10)
     | eval mp=lower(toString(coalesce(mount_point, mountPoint, MOUNT, path, "")))
     | where match(mp, "var/lib/docker|/docker|overlay") OR inode_pct>=75
     | stats max(inode_pct) AS inode_pct BY host_id ]
| join type=left max=0 host_id
    [| inputlookup dockerd_resource_baseline.csv
     | eval host_id=lower(trim(toString(coalesce(host_id, host, hostname, ""))))
     | eval baseline_fd_pct_warn=tonumber(tostring(coalesce(baseline_fd_pct_warn, fd_pct_warn, expected_fd_pct_high, "")), 10)
     | eval baseline_thread_max=tonumber(tostring(coalesce(baseline_thread_max, thread_baseline_max, expected_threads, "")), 10)
     | eval baseline_cpu_pct=tonumber(tostring(coalesce(baseline_cpu_pct, cpu_baseline_pct, expected_dockerd_cpu, "")), 10)
     | fields host_id baseline_fd_pct_warn baseline_thread_max baseline_cpu_pct ]
| fillnull value=0 inode_pct
| eventstats perc95(inode_pct) AS fleet_inode_p95
| eval severity=case(
    coalesce(fd_pct,0)>=90, "critical_fd_pct_above_90_imminent_exhaustion",
    inode_pct>=90, "critical_inode_above_90_dockerd_layer_creation_blocked",
    coalesce(dockerd_cpu_pct,0)>=90, "high_dockerd_cpu_above_90_single_thread_saturation",
    pull_hot=1, "high_pull_queue_depth_above_2x_max_concurrent",
    isnotnull(baseline_thread_max) AND threads>baseline_thread_max, "medium_thread_count_above_baseline",
    (coalesce(fd_pct,0)>coalesce(baseline_fd_pct_warn,70) AND coalesce(fd_pct,0)<90) OR (isnotnull(baseline_cpu_pct) AND coalesce(dockerd_cpu_pct,0)>(baseline_cpu_pct+12)), "low_baseline_drift",
    true(), null())
| where isnotnull(severity)
| eval recommended_response=case(
    severity="critical_fd_pct_above_90_imminent_exhaustion", "Raise LimitNOFILE for docker.service via systemd drop-in; restart dockerd under change control; inspect plugins and stuck attach sessions; capture lsof -p dockerd snapshot; compare to published moby FD-leak discussions.",
    severity="critical_inode_above_90_dockerd_layer_creation_blocked", "Emergency image and builder prune on /var/lib/docker after workload drain; verify df -i; schedule overlay2 maintenance; audit image retention; expand filesystem or migrate graph root.",
    severity="high_dockerd_cpu_above_90_single_thread_saturation", "Capture SIGUSR1 goroutine dump; reduce concurrent API clients; stagger pulls; validate storage driver latency inflating dockerd CPU.",
    severity="high_pull_queue_depth_above_2x_max_concurrent", "Raise max-concurrent-downloads in daemon.json under CAB; stagger registry hits; add pull mirrors; throttle CI image storms during patch windows.",
    severity="medium_thread_count_above_baseline", "Investigate thread leak or plugin churn; compare proc status Threads to baseline; plan Engine upgrade if known goroutine leak.",
    severity="low_baseline_drift", "Refresh dockerd_resource_baseline.csv after fleet change; trend fd_leak_slope_per_hr; compare host to fleet_fd_p90 before raising limits.",
    true(), "Triangulate linux:proc:dockerd_status, docker:metrics, and linux:df_inodes before closing.")
| table host_id dockerd_pid open_fds hard_nofile_limit fd_pct threads dockerd_cpu_pct inode_pct pull_queue_depth max_concurrent_downloads severity recommended_response
```


Alert actions: attach fd_leak_slope_per_hr and fleet_fd_p90 in the notable description, link to UC-3.1.8 filtered on the same host when investigators suspect concurrent daemon errors, and link to UC-3.1.16 volume trending when inode pressure follows image churn.

### Step 4 — Validate

Positive path A — FD pressure lab: lower LimitNOFILE temporarily on a disposable VM, drive concurrent docker run loops plus attach streams until open_fds approaches hard_nofile_limit, confirm linux:proc:dockerd_status reflects rising fd_pct, and expect critical_fd_pct_above_90_imminent_exhaustion before CLI commands fail. Restore limits immediately.

Positive path B — Inode pressure lab: create many tiny files under /var/lib/docker test mount namespace or use a loopback filesystem with tiny inode count, fill until inode_pct crosses ninety, confirm critical_inode_above_90_dockerd_layer_creation_blocked fires, then reclaim under change control.

Positive path C — Pull queue lab: set max-concurrent-downloads to one in daemon.json on a lab host, launch parallel docker pull against large layers from five terminals, observe pull_queue_depth rise in docker:metrics or your exporter, and expect high_pull_queue_depth_above_2x_max_concurrent when thirty-second peak exceeds twice the configured concurrency.

Negative path — healthy host: confirm fd_pct stays below fifty, inode_pct stays below fifty on docker mount, dockerd_cpu_pct stays modest, pull_queue_depth near zero, and the saved search emits no severity across multiple intervals.

Field sanity: rename a forwarder field to camelCase only in sandbox and verify coalesce lists still populate. RBAC: readers without oti_containers must see zero rows.

### Step 5 — Operationalize and troubleshoot

Case 1 — FD critical but journal quiet: classic silent admission failure; escalate to systemd LimitNOFILE increase and dockerd restart plan, capture lsof -p dockerd, and audit monitoring agents holding docker.sock open.

Case 2 — fd_leak_slope_per_hr positive for days without hitting ninety percent: treat as leak hunt; rotate suspicious plugins, upgrade Engine per moby advisories, schedule controlled dockerd restart during maintenance.

Case 3 — inode critical with plenty of disk space: run image prune and builder prune, verify overlay2 age, consider filesystem migration; do not only watch df -h.

Case 4 — pull_hot during expected patch Tuesday: annotate maintenance lookup or lower page priority using fleet change calendar; do not delete the detection.

Case 5 — dockerd_cpu_pct high without pull_hot: correlate with storage latency, antivirus scans on /var/lib/docker, or excessive container list polling from CMDB agents; throttle clients before blaming hardware.

Case 6 — baseline join misses: normalize host_id in CSV publisher to match forwarder short name; add FQDN alias rows if dual naming persists.

Case 7 — metrics arm empty after OTel upgrade: validate prometheus receiver target, confirm metrics-addr still listening, check tls settings.

Case 8 — streamstats slope noisy on polling gaps: tighten scripted input cadence or increase window=18 only after Job Inspector review.

Case 9 — false medium_thread_count_above_baseline after deliberate concurrency experiment: refresh baseline_thread_max in the same change ticket that modified daemon workload.

Case 10 — Mirantis field renames: reconcile props aliases after MCR upgrades before muting.

Dashboard publishing: fd_pct heatmap by host_id, pull_queue_depth time series stacked by host, inode_pct versus disk_pct scatter, dockerd_cpu_pct single-value trends.

Evidence retention: weekly CSV exports with dockerd_resource_baseline.csv commit hashes in restricted index.

Governance: quarterly replay one historical silent deploy stall through the SPL after Engine or kernel upgrades; update comment macro when indexes move.

Closing checklist: monitoringType lists Performance and Capacity; splunkPillar Observability; equipment docker and linux; equipmentModels docker_engine and linux_proc; cimModels Performance and Application_State; five step headers with em dashes; Step 3 fenced SPL matches spl field exactly; Step 5 lists ten cases; narrative JSON fields contain no asterisk emphasis; exclusions and knownFalsePositives stay capacity-themed; references include dockerd, daemon.json anchor, proc.5, Spotify engineering daemon article, Splunk Lantern OpenTelemetry Docker article, Prometheus metrics anchor.

## SPL

```spl
`comment("UC-3.1.11 Docker Daemon Resource Limits Monitoring. Daemon FD, thread, CPU ceilings; Prometheus pull-queue context; /var/lib/docker inode headroom. Tunables: index=oti_containers; sourcetypes linux:proc:dockerd_status docker:metrics linux:df_inodes; lookup dockerd_resource_baseline.csv; earliest=-4h@h latest=@h; fd_crit_pct=90 inode_crit_pct=90 dockerd_cpu_crit=90; pull_depth_mult=2; default_max_concurrent_downloads=3")`
| search index=oti_containers sourcetype="linux:proc:dockerd_status" earliest=-4h@h latest=@h
| eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
| eval dockerd_pid=tonumber(tostring(coalesce(dockerd_pid, dockerdPid, pid, "")), 10)
| eval open_fds=tonumber(tostring(coalesce(open_fds, openFds, open_fd_count, fds_open, "")), 10)
| eval hard_nofile_limit=tonumber(tostring(coalesce(hard_nofile_limit, hardNofileLimit, nofile_hard, limits_nofile_hard, "")), 10)
| eval threads=tonumber(tostring(coalesce(threads, thread_count, Threads, proc_threads, "")), 10)
| eval dockerd_cpu_pct=tonumber(tostring(coalesce(dockerd_cpu_pct, dockerdCpuPct, engine_daemon_engine_cpu_percent, "")), 10)
| eval fd_pct=if(isnotnull(open_fds) AND isnotnull(hard_nofile_limit) AND hard_nofile_limit>0, round(100.0 * open_fds / hard_nofile_limit, 2), null())
| sort 0 + host_id, _time
| streamstats window=18 current=t global=f first(open_fds) AS fds_first last(open_fds) AS fds_last first(_time) AS t_first last(_time) AS t_last BY host_id
| eval fd_leak_slope_per_hr=if(isnotnull(fds_last) AND isnotnull(fds_first) AND isnotnull(t_last) AND isnotnull(t_first) AND (t_last>t_first), round((fds_last - fds_first) / max(0.0001, ((t_last - t_first) / 3600.0)), 4), null())
| eventstats perc90(fd_pct) AS fleet_fd_p90
| join type=left max=0 host_id
    [| search index=oti_containers sourcetype="docker:metrics" earliest=-4h@h latest=@h
     | eval host_id=lower(toString(coalesce(host, Host, hostname, instance, dest, "")))
     | eval metric_name=lower(toString(coalesce(metric_name, name, __name__, "")))
     | eval mv=tonumber(tostring(coalesce(value, metric_value, "")), 10)
     | eval pull_queue_depth=if(match(metric_name, "(?i)pull|image|download|layer|registry") AND match(metric_name, "(?i)queue|pending|backlog|wait|depth|inflight"), mv, null())
     | eval max_concurrent_downloads=if(match(metric_name, "(?i)max_concurrent_downloads|concurrent_download"), mv, null())
     | eval pull_queue_depth=coalesce(pull_queue_depth, tonumber(tostring(coalesce(pullQueueDepth, engine_pull_queue_depth, pending_image_pulls, "")), 10))
     | eval max_concurrent_downloads=coalesce(max_concurrent_downloads, tonumber(tostring(coalesce(maxConcurrentDownloads, daemon_max_pulls, "")), 10))
     | stats latest(pull_queue_depth) AS pull_queue_depth latest(max_concurrent_downloads) AS max_concurrent_downloads BY host_id ]
| fillnull value=0 pull_queue_depth
| eval max_concurrent_downloads=coalesce(max_concurrent_downloads, 3)
| eval pull_depth_mult=2
| streamstats time_window=30s current=t global=f max(pull_queue_depth) AS pull_q_peak_30s BY host_id
| eval pull_hot=if(pull_q_peak_30s > (pull_depth_mult * max_concurrent_downloads), 1, 0)
| join type=left max=0 host_id
    [| search index=oti_containers sourcetype="linux:df_inodes" earliest=-4h@h latest=@h
     | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
     | eval inode_pct=tonumber(tostring(coalesce(inode_pct, inode_used_pct, IUsePercent, ipcent, "")), 10)
     | eval mp=lower(toString(coalesce(mount_point, mountPoint, MOUNT, path, "")))
     | where match(mp, "var/lib/docker|/docker|overlay") OR inode_pct>=75
     | stats max(inode_pct) AS inode_pct BY host_id ]
| join type=left max=0 host_id
    [| inputlookup dockerd_resource_baseline.csv
     | eval host_id=lower(trim(toString(coalesce(host_id, host, hostname, ""))))
     | eval baseline_fd_pct_warn=tonumber(tostring(coalesce(baseline_fd_pct_warn, fd_pct_warn, expected_fd_pct_high, "")), 10)
     | eval baseline_thread_max=tonumber(tostring(coalesce(baseline_thread_max, thread_baseline_max, expected_threads, "")), 10)
     | eval baseline_cpu_pct=tonumber(tostring(coalesce(baseline_cpu_pct, cpu_baseline_pct, expected_dockerd_cpu, "")), 10)
     | fields host_id baseline_fd_pct_warn baseline_thread_max baseline_cpu_pct ]
| fillnull value=0 inode_pct
| eventstats perc95(inode_pct) AS fleet_inode_p95
| eval severity=case(
    coalesce(fd_pct,0)>=90, "critical_fd_pct_above_90_imminent_exhaustion",
    inode_pct>=90, "critical_inode_above_90_dockerd_layer_creation_blocked",
    coalesce(dockerd_cpu_pct,0)>=90, "high_dockerd_cpu_above_90_single_thread_saturation",
    pull_hot=1, "high_pull_queue_depth_above_2x_max_concurrent",
    isnotnull(baseline_thread_max) AND threads>baseline_thread_max, "medium_thread_count_above_baseline",
    (coalesce(fd_pct,0)>coalesce(baseline_fd_pct_warn,70) AND coalesce(fd_pct,0)<90) OR (isnotnull(baseline_cpu_pct) AND coalesce(dockerd_cpu_pct,0)>(baseline_cpu_pct+12)), "low_baseline_drift",
    true(), null())
| where isnotnull(severity)
| eval recommended_response=case(
    severity="critical_fd_pct_above_90_imminent_exhaustion", "Raise LimitNOFILE for docker.service via systemd drop-in; restart dockerd under change control; inspect plugins and stuck attach sessions; capture lsof -p dockerd snapshot; compare to published moby FD-leak discussions.",
    severity="critical_inode_above_90_dockerd_layer_creation_blocked", "Emergency image and builder prune on /var/lib/docker after workload drain; verify df -i; schedule overlay2 maintenance; audit image retention; expand filesystem or migrate graph root.",
    severity="high_dockerd_cpu_above_90_single_thread_saturation", "Capture SIGUSR1 goroutine dump; reduce concurrent API clients; stagger pulls; validate storage driver latency inflating dockerd CPU.",
    severity="high_pull_queue_depth_above_2x_max_concurrent", "Raise max-concurrent-downloads in daemon.json under CAB; stagger registry hits; add pull mirrors; throttle CI image storms during patch windows.",
    severity="medium_thread_count_above_baseline", "Investigate thread leak or plugin churn; compare proc status Threads to baseline; plan Engine upgrade if known goroutine leak.",
    severity="low_baseline_drift", "Refresh dockerd_resource_baseline.csv after fleet change; trend fd_leak_slope_per_hr; compare host to fleet_fd_p90 before raising limits.",
    true(), "Triangulate linux:proc:dockerd_status, docker:metrics, and linux:df_inodes before closing.")
| table host_id dockerd_pid open_fds hard_nofile_limit fd_pct threads dockerd_cpu_pct inode_pct pull_queue_depth max_concurrent_downloads severity recommended_response
```

## CIM SPL

```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) AS avg_cpu max(Performance.cpu_load_percent) AS peak_cpu FROM datamodel=Performance WHERE nodename=Performance.CPU earliest=-4h@h latest=@h BY Performance.host span=15m
| rename Performance.host AS host_id
| where peak_cpu>85
```

## Visualization

fd_pct host heatmap, pull_queue_depth line chart with max_concurrent_downloads band, inode_pct versus disk-use scatter for /var/lib/docker, dockerd_cpu_pct trend with reference line at ninety percent.

## Known False Positives

Transient FD spikes during legitimate burst image pulls or massive docker save and docker load operations can push fd_pct into the seventies without implying a leak; require sustained slope from streamstats or repeated polls above baseline_fd_pct_warn before paging application teams. Pull-queue depth may read nonzero during intentional concurrency experiments or when a registry mirror warms caches; cross-check change calendar before treating pull_hot as incident. dockerd restart resets host metrics counters and can briefly inflate inode_pct readings while dentry caches repopulate; suppress duplicate pages for one interval after controlled restarts documented in maintenance lookups. Background docker system prune or aggressive builder cache eviction causes inode churn that resembles exhaustion until the operation completes; validate prune jobs in automation logs. Some monitoring agents open docker.sock briefly each poll; cumulative mis-tuned agents can resemble dockerd leaks but are actually client-side handle pressure—correlate with agent release notes. Plugin drivers that maintain long-lived FUSE mounts may elevate open_fds within policy; verify against plugin vendor baselines in dockerd_resource_baseline.csv. Fleet-wide AMI refresh can shift default max_concurrent_downloads or LimitNOFILE; expect low_baseline_drift until CSV refresh. OTel double-scrape during migrations can duplicate docker:metrics rows; deduplicate before interpreting pull_queue_depth peaks.

## References

- [Docker Docs — dockerd reference](https://docs.docker.com/engine/reference/commandline/dockerd/)
- [Docker Docs — daemon configuration file](https://docs.docker.com/engine/reference/commandline/dockerd/#daemon-configuration-file)
- [Linux man-pages — proc(5)](https://man7.org/linux/man-pages/man5/proc.5.html)
- [Spotify Engineering — intelligent daemons and fault tolerance](https://engineering.atspotify.com/2013/03/achieving-fault-tolerance-with-intelligent-daemons/)
- [Splunk Lantern — Docker logs into Splunk Cloud via OpenTelemetry](https://lantern.splunk.com/Platform_Data_Management/Unlock_Insights/Getting_Docker_log_data_into_Splunk_Cloud_Platform_with_OpenTelemetry)
- [Docker Docs — Prometheus metrics (dockerd)](https://docs.docker.com/engine/reference/commandline/dockerd/#prometheus-metrics)
