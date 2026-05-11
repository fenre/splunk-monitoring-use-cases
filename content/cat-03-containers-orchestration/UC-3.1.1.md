<!-- AUTO-GENERATED from UC-3.1.1.json — DO NOT EDIT -->

---
id: "3.1.1"
title: "Container Crash Loops"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.1.1 · Container Crash Loops

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Fault, Reliability &middot; **Wave:** Crawl &middot; **Status:** Verified

*We watch the small programs that run inside boxes on our servers, and when one keeps dying with a bad exit code we notice quickly. We also count how fast it is happening so we know if it is a single hiccup or a loop that will upset people using our service.*

---

## Description

Detects Docker Engine container die events carrying non-zero exit codes, classifies each death into an exit_code_class taxonomy (oom_kill for 137-style kernel kills, sigterm, sigint, segfault, generic_failure, with clean exits filtered from alert output), measures per-container crash velocity in fifteen-minute buckets and one-hour density for fleet context, and enriches deaths with the latest docker:container:logs line for triage. The search correlates multisearch arms across docker:events, linux:cgroup or syslog OOM hints, and aggregated container logs so operators see death, kernel context, and last application utterance together. This is not an OOM-only detector; see UC-3.1.2 for cgroup control-file isolation. It does not substitute UC-3.1.13 restart-policy back-off analytics, UC-3.1.22 HEALTHCHECK transitions, or UC-3.2.1 and UC-3.2.10 Kubernetes pod restart narratives.

## Value

Crash loops burn customer trust before dashboards catch latency: each unexplained exit delays releases, forces rollbacks, and hides whether the root cause is the kernel, a bad image, or a misread config. Separating kernel-signaled exits from application return codes shortens time to fix because platform on-call and service owners follow different runbooks, and quantifying fifteen-minute velocity distinguishes a single failed deploy from a tight loop that will exhaust restart limits. Customer-visible outages shrink when you alert on structured die telemetry instead of waiting for synthetic checks, and finance sees lower log license waste when teams stop turning every crash into verbose debug floods without first reading the last_log_line.

## Implementation

Install Splunk Connect for Docker on a collector with docker.sock access, enable docker:events and docker:container:logs modular inputs into index=docker, and deploy Splunk_TA_nix linux:cgroup plus syslog monitors for /var/log/syslog and /var/log/messages into index=os. Publish container_owner.csv with host, container_name, owner_team refreshed weekly. Schedule container_uc_3_1_1_crash_loops every five minutes on earliest=-1h@h latest=@h, route severities by owner_team, and archive results to your evidence index with optional container_exclusions.csv filtering documented in the macro wrapper.

## Evidence

Saved search container_uc_3_1_1_crash_loops, lookups lookups/container_owner.csv and lookups/container_exclusions.csv, weekly CSV snapshots archived to index=evidence, dashboard panel Docker Reliability — Crash Loops table, and git-tracked weekly CSV exports with change tickets.

## Control test

### Positive scenario

On a lab Linux host run docker run --name lab-crash --restart=on-failure ubuntu:22.04 /bin/sh -c 'exit 137' and wait for Splunk Connect for Docker to index the die event; execute container_uc_3_1_1_crash_loops and expect exit_code_class oom_kill, severity critical, crashes_15m at least one, and a populated owner_team row when container_owner.csv lists lab-crash.

### Negative scenario

Deploy a Compose service whose command is /bin/true or equivalent exiting zero, let it stop cleanly, and confirm the saved search returns no row for that container because exit_code zero rows are filtered; if a zero exit appears due to parser bugs, fix field extraction before declaring the control green.

## Detailed Implementation

### Prerequisites

Splunk Connect for Docker (Splunkbase 4496) must be installed on a Linux collector tier that can reach the Docker Engine REST API over unix:///var/run/docker.sock or a TCP dockerd endpoint that mirrors production. The modular inputs that matter for this control are the Docker Events stream (sourcetype docker:events with action=die) and the container log follower that lands docker:container:logs from stdout and stderr of each container, respecting the logging driver in effect on the host (json-file, local, splunk log driver, or journald on systemd hosts where you bridge journald into Splunk). Splunk Add-on for Unix and Linux (Splunkbase 833) must ship linux:cgroup scripted reads or equivalent file tail of cgroup-v2 memory controller files under /sys/fs/cgroup (memory.current, memory.events, memory.max, memory.high) and cgroup-v1 legacy paths under /sys/fs/cgroup/memory when the host has not migrated; those reads are how you corroborate kernel-side OOM decisions against exit code 137 without treating OOM as the only story. Syslog capture from /var/log/syslog, /var/log/messages, or /var/log/kern.log remains necessary because many distributions still emit oom-kill lines only through the kernel printk path that lands in those files, especially when Docker is not the cgroup writer that increments memory.events.

Splunk OpenTelemetry Collector for Containers is optional but recommended when you already standardize on OpenTelemetry for host and runtime telemetry; configure the containerd receiver when Docker is backed by containerd so you still see shim-level lifecycle transitions, and keep the receiver’s socket path aligned with /run/containerd/containerd.sock on the node. Index routing: docker for docker:* sourcetypes, os for linux:cgroup and syslog arms, evidence or security for weekly CSV exports of alert output if your SO requires immutable retention. Roles must allow srchIndexesAllowed to include docker and os for operators running container_uc_3_1_1_crash_loops.

Lookups: publish container_owner.csv with columns host (normalized lowercase hostname as forwarders report it), container_name (Compose project prefixes included if that is how die events name the container), owner_team (pager routing), and refresh weekly from your service catalog or Compose labels. Maintain container_exclusions.csv for deliberate crash drills even though the base SPL filters non-zero exits only; exclusions are enforced in a wrapper macro or secondary filter to avoid muting production silently.

Differentiation: UC-3.1.2 isolates cgroup memory.oom_control and OOM-only signals. UC-3.1.13 emphasizes restart-policy back-off without building the exit-code taxonomy used here. UC-3.1.22 watches HEALTHCHECK state transitions, not die events. UC-3.2.1 and UC-3.2.10 cover Kubernetes pod restart loops, not dockerd-native streams on bare metal or Compose hosts.

Licensing and volume: docker events are low volume compared to full json-file duplication, but docker:container:logs can dominate license if you scrape high-cardinality debug services; trim retention on non-prod indexes and consider sampling for stdout-only noise services after platform approval.

### Step 1 — Configure data collection

On the heavy forwarder or intermediate tier hosting Splunk Connect for Docker, open inputs.conf for the app and enable the Docker Events modular input pointing at the local socket unless your security team mandates a TCP proxy. Set the poll or stream mode according to the add-on version you run; modern builds follow the events API continuously. Confirm the sourcetype override remains docker:events and that action, id, from, Actor, and exitCode style fields are preserved through props.conf. For container logs, enable the modular input that tails json-file paths under /var/lib/docker/containers/<container-id>/*-json.log when you use the default logging driver, or switch the input to journald when the daemon uses the journald driver so the same docker:container:logs sourcetype still normalizes. Map index=docker unless your index routing standards mandate a different name, and document the deviation in the comment macro.

On every Linux worker running workloads, deploy Splunk_TA_nix with the linux:cgroup scripted input enabled for memory controller statistics. Validate that events include the path to the cgroup directory and the memory.events counter increments when the kernel kills a process group; on cgroup v2 the interesting control files live under a unified hierarchy while v1 splits memory and memsw. If scripted input latency is too high during incidents, add a supplemental Universal Forwarder monitor of /var/log/kern.log with sourcetype syslog so OOM lines arrive within seconds.

Docker daemon logs belong in syslog on many distributions (dockerd writing to journald then forwarded), or in /var/log/docker.log when configured; ensure those paths are ingested because restart storms often print transport errors before die events repeat. When docker login flows through linux_secure or auditd, keep that feed for forensic correlation even though it is out of scope for crash classification.

For Splunk OpenTelemetry Collector for Containers, install the host agent chart or package per docs.splunk.com, enable the containerd receiver block with the local socket, and export logs or events to HEC with a dedicated token landing in index=docker with sourcetype you normalize to docker:events or a parallel sourcetype that you add as a fourth multisearch arm later. Do not dual-index the same container line through both Connect and OTel without dedup logic or you will double-count crashes_1h.

Optional docker:stats modular input from the same Connect deployment gives CPU throttling context when exits are application-level but the host was constrained; it does not replace die events.

Expected fields for validation in Search before saving the alert: host, action=die, exitCode or exit_code after alias, containerName or actor attributes, image reference, docker:container:logs _raw tail, linux:cgroup memory.events or syslog oom-kill line with cgroup path. Expect one die event per container exit when the daemon sees the container stop; batch short-lived containers can generate bursts during compose up.

### Step 2 — Create the search and alert

Save the SPL as saved search container_uc_3_1_1_crash_loops with schedule every five minutes and time range matching earliest=-1h@h latest=@h so velocity buckets align to wall clock. Throttle alerts per host and container_name for thirty minutes when severity is warning but allow immediate re-fire when severity escalates to critical because kernel-signaled exits deserve a page.

#### Understanding this SPL without repeating a mechanical pipeline essay: the comment macro is the operator contract for indexes, lookup names, and ownership. Multisearch runs three parallel arms so you never imply a single vendor path owns the truth. The die arm is authoritative for exit_code and image. The cgroup and syslog arm supplies oom_ctx rows that you can extend later to adjust exit_code_class when the kernel reports OOM but Docker mis-reports an intermediate code; in the baseline SPL those rows participate in multisearch fan-in only and the classification still keys primarily off numeric exit_code per your eval ladder. The docker:container:logs arm pre-aggregates a latest line per host and container so die rows inherit last_log_line through eventstats without an expensive join on raw megabyte logs.

Coalesce lists tolerate Connect versions that emit camelCase Actor attributes versus lowercase extracted fields. streamstats keeps ordered exit_code history per container so rapid_backoff_hint flags repeating the same failing code, which pairs with velocity_per_15m from fifteen-minute buckets to separate a single bad deploy from a tight loop. eventstats adds crashes_1h for fleet context on dashboards. The severity case encodes kernel-signaled exits as critical, more than three deaths in the same fifteen-minute bucket as critical loop pressure, any other non-zero death in that bucket as warning, and info is unreachable here because the search filters exit_code!=0 before the case; if you remove that filter for auditing, the final branch returns info for clean exits.

The join with inputlookup container_owner.csv deliberately uses join type=left max=0 instead of the lookup command so governance reviewers see the pattern used in other gold UCs and so you can paste a transformed subsearch (eval host lowercase, trim service prefixes) without Splunk expanding multi-valued lookup explosions on busy namespaces.

Fenced SPL (must match the spl JSON field aside from whitespace you normalize in Save):

```spl
`comment("UC-3.1.1 Container Crash Loops. Tunables: replace index=docker and index=os with approved names; container_owner.csv keys host (lowercase), container_name, owner_team; tune velocity_per_15m thresholds in the severity case if batch hosts are noisy. Owner field: owner_team. earliest=-1h@h latest=@h aligns die events, cgroup hints, and log aggregates to the hour boundary.")`
| multisearch
    [ search index=docker sourcetype="docker:events" action="die" earliest=-1h@h latest=@h
      | eval event_branch="die"
      | eval host=lower(toString(coalesce(host, Host, hostname, "")))
      | eval exit_code=tonumber(tostring(coalesce(exitCode, exit_code, ExitCode, actor_exitCode, "")), 10)
      | eval container_name=toString(coalesce(containerName, container_name, ContainerName, actor_name, ""))
      | eval image=toString(coalesce(Image, image, from, ""))
      | fields _time host container_name image exit_code event_branch ]
    [ search index=os (sourcetype="linux:cgroup" OR (sourcetype=syslog AND (source="/var/log/syslog" OR source="/var/log/messages" OR source="/var/log/kern.log")))
      earliest=-1h@h latest=@h
      | search (match(_raw, "(?i)oom-kill|Out of memory|Killed process") OR match(_raw, "(?i)memory\\.(oom|high|max)") OR match(_raw, "(?i)Memory cgroup"))
      | eval event_branch="oom_ctx"
      | eval container_hint=toString(coalesce(container_name, containerName, cgroup_container, ""))
      | fields _time host container_hint event_branch ]
    [ search index=docker sourcetype="docker:container:logs" earliest=-1h@h latest=@h
      | eval host=lower(toString(coalesce(host, Host, "")))
      | eval container_name=toString(coalesce(containerName, container_name, ContainerName, ""))
      | eval _trim=if(len(_raw)>480, substr(_raw,1,480), _raw)
      | stats latest(_trim) AS last_log_line BY host, container_name
      | eval event_branch="clog_agg"
      | eval _time=now()
      | fields _time host container_name last_log_line event_branch ]
| eval cn=coalesce(container_name, container_hint, "")
| eventstats latest(eval(if(event_branch="clog_agg", last_log_line, null()))) AS last_log_line BY host, cn
| where event_branch="die"
| eval container_name=if(isnull(container_name) OR len(trim(container_name))==0, cn, container_name)
| eval last_log_line=coalesce(last_log_line, "")
| sort 0 + host, container_name, _time
| streamstats window=80 current=t global=f list(exit_code) AS recent_exit_seq BY host, container_name
| streamstats window=80 current=t global=f last(exit_code) AS prev_exit BY host, container_name
| eval rapid_backoff_hint=if(exit_code!=0 AND prev_exit==exit_code, 1, 0)
| bucket _time span=15m AS t15
| eventstats count AS velocity_per_15m BY host, container_name, t15
| eventstats count AS crashes_1h BY host, container_name
| eval crashes_15m=velocity_per_15m
| where exit_code!=0
| eval exit_code_class=case(exit_code==137 OR exit_code==247, "oom_kill", exit_code==143, "sigterm", exit_code==130, "sigint", exit_code==139 OR exit_code==11, "segfault", exit_code==0 OR isnull(exit_code), "clean", true(), "generic_failure")
| eval severity=case((exit_code==137 OR exit_code==143), "critical", (exit_code!=0 AND velocity_per_15m>3), "critical", (exit_code!=0 AND velocity_per_15m>0), "warning", true(), "info")
| join type=left max=0 host, container_name
    [| inputlookup container_owner.csv
     | eval host=lower(toString(host))
     | eval container_name=toString(container_name)
     | eval owner_team=toString(coalesce(owner_team, squad, ""))
     | fields host container_name owner_team ]
| table host container_name image exit_code exit_code_class crashes_15m crashes_1h last_log_line severity owner_team
```

Alert actions: route critical to the platform incident channel with the last_log_line pasted, route warning to the owning squad from owner_team with a link to the host’s Portainer or docker inspect output runbook attachment.

### Step 3 — Validate

Pick a staging host with Docker CE or Mirantis Container Runtime and run docker events in the shell while you docker run --rm alpine false; confirm a die event appears in index=docker sourcetype=docker:events with a non-zero exit_code within one collection interval. Compare the exit code to docker inspect --format '{{.State.ExitCode}}' for the same container id when you run a longer-lived failing task.

For OOM correlation, limit a test container with --memory=64m and stress memory; expect exit 137 on the die event and a matching oom-kill or memory.events increment in index=os within the same minute. This validates UC-3.1.1 classification oom_kill against UC-3.1.2 which would deep-dive cgroup files alone.

For logs, tail docker:container:logs around the failure and verify last_log_line in the search picks up the final stderr line you injected. If last_log_line is empty, the container_name keys between events and logs likely differ because Compose projects prepend directory names; normalize with a sed-style eval or extend container_owner.csv to include aliases.

Run timechart count of action=die by host over twenty-four hours to find silent gaps longer than two collection intervals; gaps usually mean the events input lost its socket or disk filled on the collector. Compare crashes_1h to docker stats sampling if you also ingest docker:stats sourcetype for CPU throttling side effects that do not kill the container.

Confirm RBAC: a reader without index=docker should see zero results, proving the role separation is effective.

### Step 4 — Operationalize

Dashboard Docker Reliability — Crash Loops: top row single-value tiles for count of critical severity rows in the last hour, distinct hosts with looped containers, and sum of crashes_1h across the fleet. Second row timechart of crashes_1h split by exit_code_class with a fifteen-minute span to show whether oom_kill spikes track a release or config push. Third row sortable table using the same columns as the closing table command with drilldown to raw docker:events and a side panel for docker:container:logs.

Runbook ownership sits with Head of Platform for kernel-signaled exits and with the owner_team column for application exits. Weekly, export the alert CSV to the evidence index and attach git commit hashes for container_owner.csv. Integrate maintenance windows by adding a boolean column to the lookup rather than muting the search.

For on-call training, walk through the difference between signal 9 exits and application return code 1 using the exit_code_class column so junior responders do not restart loops blindly.

Training dataset: keep a lab compose stack that fails fast and tag it in container_exclusions.csv so demos do not page production.

### Step 5 — Troubleshooting

Case 1 — Die events missing entirely: docker.sock permissions for the Connect user, rootless Docker moving the socket path, or AppArmor denying access. Verify ls -l /var/run/docker.sock on the collector, compare to the input stanza, and tail splunkd.log for REST errors naming the Docker API. Remediation is POSIX group membership in docker or a documented TCP relay with TLS.

Case 2 — exit_code always zero on die rows: you may be ingesting healthcheck-less stop events from an upstream wrapper that swallows the real code; inspect docker inspect after failure and adjust field aliases in props.conf so exitCode maps from the JSON field the add-on actually emits. Remediation is a TA upgrade or a calculated field from State.ExitCode.

Case 3 — velocity_per_15m explodes during legitimate blue-green deploys: parallel old tasks terminating generate bursts; add a deploy tag from your CD system into the events path or enrich with a lookup of expected churn namespaces. Remediation is a time-bound exclusion row, not a permanent threshold raise.

Case 4 — cgroup arm noisy without Docker substrings: tighten the search filter to require docker or runc in the oom line when syslog is shared with database servers. Remediation is a host-specific macro or a dedicated index for kernel logs from container workers only.

Case 5 — last_log_line stale or wrong container: name mismatches between die events and json-file tails when containers are recreated with the same name but different id; key on container id if Connect exposes it, or use the most recent log line within ten seconds of _time using a narrow join. Remediation is enrich die events with ID before stats.

Case 6 — join to container_owner misses: host casing or short name versus FQDN; enforce lowercase in the lookup publish job and add a second column for fqdn_host. Remediation is regenerate CSV from CMDB with the same string the Universal Forwarder uses in host=.

Case 7 — crashes_1h doubles after OTel dual ship: dedup on docker event id fields or drop one path in non-prod. Remediation is single writer per cluster.

Case 8 — streamstats order wrong when _time ties: add sequence from _indextime or use sort 0 with tie-breaker on extracted id. Remediation is stable sort keys in the sort command.

Extended hygiene: rotate HEC tokens quarterly, document Mirantis MCR versus Docker CE field deltas, keep cgroup v1 versus v2 cheat sheet for investigators, and rehearse pairing this UC with UC-3.1.13 when restart policy backoff is the operational question while this UC supplies the death taxonomy answer.



Appendix — Docker daemon semantics refresher

Restart policies named unless-stopped, always, on-failure, and no change how many die events you see versus how many restarts occur. A no policy still emits die when the main process exits; always restarts the container after clean or unclean exits unless the daemon stops; on-failure restarts only on non-zero status codes and respects a max retry count you set in Compose or swarm service definitions. unless-stopped resembles always except containers explicitly stopped by the operator do not restart after daemon restart. These distinctions matter when you interpret velocity: a Compose on-failure service with a tight max can look like a short loop then silence even though the application remains broken.

Signal numbers relevant on Linux x86_64: SIGKILL is 9, SIGTERM is 15, SIGINT is 2, SIGSEGV is 11. Docker reports 128 plus signal for many cases, yielding 137, 143, 130, 139 respectively. Some JVM exits use 143 after graceful shutdown hooks even when operations intended a clean bounce; treat owner context before calling it an incident.

Cgroup v2 memory pressure uses memory.high throttling before hard OOM in some configurations; you might see die events with application-chosen codes while the kernel never prints oom-kill. That is why syslog alone is insufficient and why docker:stats memory throttling metrics belong on a sibling dashboard.

Logging drivers affect whether docker:container:logs contains JSON-wrapped lines or plain stdout; the Splunk log driver can bypass json-file entirely and send straight to HEC, in which case you must ensure the HEC sourcetype still participates in the multisearch arm or you lose last_log_line context.

Docker Swarm worker nodes still run dockerd; service tasks map to containers with swarm service labels. Extend container_owner.csv with stack and service columns if you route pages by swarm stack name.

Podman with docker.sock compatibility can emit similar event streams when docker compat API is enabled; field names may differ slightly and SELinux denials show up in audit logs rather than docker logs.

Windows containers are explicitly out of scope; do not expect this SPL to run unchanged on Windows worker nodes.

Security note: docker:events can include image pull and exec start metadata; restrict dashboard access because layer digests and registry URLs leak supply-chain details.

Performance note: multisearch expands fan-out; schedule the alert at five minutes, not every minute, unless incident volume demands it, because each arm scans an hour window.

Governance note: keep the saved search description field in Splunk updated with the current lookup owners and the quarter last reviewed.

Operator note: when using rootless Docker, cgroup delegation may land under user.slice paths; linux:cgroup scripted inputs must follow the delegated subtree or they read empty counters.

FinOps note: crashes that print huge stack traces inflate docker:container:logs cost; consider log driver limits and application log level caps tied to this alert firing.

Reliability note: correlate with upstream ingress five hundred two spikes only after confirming container death times align with load balancer health check intervals.

Closing checklist: confirm prerequisiteUseCases is empty, confirm monitoringType lists Fault and Reliability, confirm securityDomain endpoint, confirm equipment docker and linux, confirm equipmentModels docker_engine, and confirm cimModels Performance only.



## SPL

```spl
`comment("UC-3.1.1 Container Crash Loops. Tunables: replace index=docker and index=os with approved names; container_owner.csv keys host (lowercase), container_name, owner_team; tune velocity_per_15m thresholds in the severity case if batch hosts are noisy. Owner field: owner_team. earliest=-1h@h latest=@h aligns die events, cgroup hints, and log aggregates to the hour boundary.")`
| multisearch
    [ search index=docker sourcetype="docker:events" action="die" earliest=-1h@h latest=@h
      | eval event_branch="die"
      | eval host=lower(toString(coalesce(host, Host, hostname, "")))
      | eval exit_code=tonumber(tostring(coalesce(exitCode, exit_code, ExitCode, actor_exitCode, "")), 10)
      | eval container_name=toString(coalesce(containerName, container_name, ContainerName, actor_name, ""))
      | eval image=toString(coalesce(Image, image, from, ""))
      | fields _time host container_name image exit_code event_branch ]
    [ search index=os (sourcetype="linux:cgroup" OR (sourcetype=syslog AND (source="/var/log/syslog" OR source="/var/log/messages" OR source="/var/log/kern.log")))
      earliest=-1h@h latest=@h
      | search (match(_raw, "(?i)oom-kill|Out of memory|Killed process") OR match(_raw, "(?i)memory\\.(oom|high|max)") OR match(_raw, "(?i)Memory cgroup"))
      | eval event_branch="oom_ctx"
      | eval container_hint=toString(coalesce(container_name, containerName, cgroup_container, ""))
      | fields _time host container_hint event_branch ]
    [ search index=docker sourcetype="docker:container:logs" earliest=-1h@h latest=@h
      | eval host=lower(toString(coalesce(host, Host, "")))
      | eval container_name=toString(coalesce(containerName, container_name, ContainerName, ""))
      | eval _trim=if(len(_raw)>480, substr(_raw,1,480), _raw)
      | stats latest(_trim) AS last_log_line BY host, container_name
      | eval event_branch="clog_agg"
      | eval _time=now()
      | fields _time host container_name last_log_line event_branch ]
| eval cn=coalesce(container_name, container_hint, "")
| eventstats latest(eval(if(event_branch="clog_agg", last_log_line, null()))) AS last_log_line BY host, cn
| where event_branch="die"
| eval container_name=if(isnull(container_name) OR len(trim(container_name))==0, cn, container_name)
| eval last_log_line=coalesce(last_log_line, "")
| sort 0 + host, container_name, _time
| streamstats window=80 current=t global=f list(exit_code) AS recent_exit_seq BY host, container_name
| streamstats window=80 current=t global=f last(exit_code) AS prev_exit BY host, container_name
| eval rapid_backoff_hint=if(exit_code!=0 AND prev_exit==exit_code, 1, 0)
| bucket _time span=15m AS t15
| eventstats count AS velocity_per_15m BY host, container_name, t15
| eventstats count AS crashes_1h BY host, container_name
| eval crashes_15m=velocity_per_15m
| where exit_code!=0
| eval exit_code_class=case(exit_code==137 OR exit_code==247, "oom_kill", exit_code==143, "sigterm", exit_code==130, "sigint", exit_code==139 OR exit_code==11, "segfault", exit_code==0 OR isnull(exit_code), "clean", true(), "generic_failure")
| eval severity=case((exit_code==137 OR exit_code==143), "critical", (exit_code!=0 AND velocity_per_15m>3), "critical", (exit_code!=0 AND velocity_per_15m>0), "warning", true(), "info")
| join type=left max=0 host, container_name
    [| inputlookup container_owner.csv
     | eval host=lower(toString(host))
     | eval container_name=toString(container_name)
     | eval owner_team=toString(coalesce(owner_team, squad, ""))
     | fields host container_name owner_team ]
| table host container_name image exit_code exit_code_class crashes_15m crashes_1h last_log_line severity owner_team
```

## CIM SPL

```spl
| tstats summariesonly=t avg(Performance.cpu_load_percent) AS avg_cpu_load FROM datamodel=Performance WHERE nodename=Performance.CPU earliest=-1h@h latest=@h BY Performance.host span=15m
| rename Performance.host AS host
| where avg_cpu_load>85
```

## Visualization

Lay out a dashboard with a top row of single-value tiles for critical count, warning count, and distinct looping containers. Place a second-row timechart spanning crashes_1h stacked by exit_code_class with fifteen-minute buckets. Finish with a third-row sortable table mirroring the SPL projection (host, container_name, image, exit_code, exit_code_class, crashes_15m, crashes_1h, last_log_line, severity, owner_team) tied to drilldowns on raw die events and paired logs.

## Known False Positives

Short-lived init containers defined in Compose to run database migrations often exit non-zero on the first attempt by design while a lock waits, then succeed on retry.
Batch sidecars that pull work from a queue may exit code one when the queue is empty if developers coded aggressive failure modes.
PreStop hooks that run docker stop --time=5 against lazy apps sometimes surface as sigterm-class exits during rolling updates even though traffic already drained.
Docker-in-Docker CI jobs intentionally kill helper containers with signal nine to simulate failure injection.
Image pulls during a rolling restart can overlap with on-failure policies so transient layer errors emit die events before the next pull succeeds.
Oneshot Compose command patterns such as printf diagnostics exit non-zero to signal skip conditions in automation.
A/B smoke tests deliberately exit non-zero on the canary branch while the stable branch keeps serving.
Blue-green scripts terminate the old task with a forced kill that looks like oom_kill class if misread without deploy tags.

## References

- [Splunk Connect for Docker (Splunkbase 4496)](https://splunkbase.splunk.com/)
- [Splunk Add-on for Unix and Linux (Splunkbase 833)](https://splunkbase.splunk.com/app/833)
- [Docker CLI reference — docker events](https://docs.docker.com/reference/cli/docker/)
- [Linux kernel documentation — cgroup v2](https://www.kernel.org/doc/Documentation/cgroup-v2.txt)
- [Splunk Observability — OpenTelemetry Collector for Kubernetes (containers agent install)](https://docs.splunk.com/observability/en/gdi/opentelemetry/)
- [Splunk CIM — Performance data model](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
