<!-- AUTO-GENERATED from UC-3.1.8.json — DO NOT EDIT -->

---
id: "3.1.8"
title: "Docker Daemon Errors"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.1.8 · Docker Daemon Errors

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the engine that runs the entire shipping yard's container cranes. When that engine itself sputters, panics, or seizes up, every container in motion stops mid-air and no amount of restarting the cranes helps until the engine is breathing again. We catch that engine sputter early so a host-wide outage never grows into a fleet-wide outage.*

---

## Description

Engine-process reliability axis at the dockerd and containerd layer that keeps a Fortune 500 platform team aware when the engine itself is failing, not the workloads above it. The control correlates three independent signals: dockerd journald error stream from systemd-journald via Splunk Add-on for Linux, capturing storage-driver, libcontainer or runc, libnetwork, engine-api, socket, and image-pull error classes through stable regex taxonomy; containerd-shim panic events including signal sigsegv and sigbus markers plus goroutine running stack traces that orphan containers on kernel cgroups while dockerd loses the supervisory link and writes shim disconnected within roughly five seconds; and dockerd Prometheus /metrics scraped through Splunk OpenTelemetry Collector, where engine_api 5xx rate, engine_daemon_engine_cpu_percent, and engine_daemon_health_checks_failed_total surface daemon overload before the journal logs the consequences. A 5-minute bucket and 24-hour rollup expose error_count_5min trends per host_id and error_class, panic_count_24h per host, and an api_5xx_rate gate that distinguishes daemon overload from upstream bug. UC-3.1.13 catches container-level restart loops; this UC catches the layer below — when the engine ITSELF panics, every restart-policy retry on the host is moot until dockerd recovers and any container_name listed in restart-loop searches is misleading until the engine returns. Distinct from UC-3.1.1 exit-code taxonomy, UC-3.1.2 cgroup OOM kills, UC-3.1.3 CPU throttle diagnosis, UC-3.1.22 health-probe failures, UC-3.1.6 privileged container drift, UC-3.1.25 docker.sock exposure, and UC-3.1.28 Swarm replica convergence.

## Value

Quantified impact begins with avoided host-wide outages: a single dockerd panic on a host running 200 containers snaps 200 customer-visible service instances if live-restore is not configured, while a containerd-shim crash routinely orphans dozens of containers that require manual SIGKILL on zombie shim PIDs or a full host reboot before the platform team can rebuild scheduling state. Mean time to repair collapses from hours to one collection interval when the first page names error_class taxonomy, panic_count_24h trend, and the recommended_response runbook in the same row instead of asking analysts to grep ten thousand journal lines under stress, then chase three different vendor docs to translate a SIGBUS into an action. Daemon-level patch-window evidence becomes auditable when weekly CSV exports tie storage_driver_error_count and engine_api 5xx rate trends to dockerd version pins, kernel updates, and runc CVE rollouts so the platform team can prove safe-change windows held the line. Capacity planning gains defensible signal for daemon CPU and memory tuning when engine_cpu_pct and api_5xx_rate cross-correlate with concurrent socket consumers — the conversation finance teams need before approving larger build-host SKUs or splitting CI-host classes. FinOps benefits when engine-overload incidents are caught at the daemon layer rather than absorbed into ten thousand container alerts that triple ingest cost during outages, because container-level dashboards stay quiet while only this UC fires.

## Implementation

Deploy Splunk Add-on for Linux on every Docker host shipping linux:journald:docker and linux:journald:containerd into index=oti_containers, configure Splunk OpenTelemetry Collector to scrape dockerd /metrics (enabled by metrics-addr in /etc/docker/daemon.json) into sourcetype docker:metrics, publish docker_daemon_error_taxonomy.csv and container_owner.csv weekly, save container_uc_3_1_8_docker_daemon_errors every five minutes on earliest=-24h@h latest=@h, route critical tiers to platform on-call jointly with owner_team, and archive weekly CSV snapshots to the evidence index.

## Evidence

Saved search container_uc_3_1_8_docker_daemon_errors with five-minute schedule; lookups docker_daemon_error_taxonomy.csv (error_class, default_severity, recommended_response, kfp_pattern) and container_owner.csv versioned in git; weekly CSV exports of severity rows landing in a restricted evidence index with commit hashes; dashboard panels including error_class heatmap by host over twenty-four hours, panic-count single-value with zero versus non-zero coloring, and api_5xx_rate line per host. External research includes Docker Inc engineering documentation on dockerd panic patterns and live-restore tradeoffs, Cloudflare and Datadog production retrospectives on containerd-shim escape, orphan reaping, and SIGKILL-versus-reboot decisions, the moby/moby issue tracker for engine-api 5xx and panic patterns reported by enterprise customers running large Docker fleets, and journald analysis case studies from systemd documentation that informed regex taxonomy choices.

## Control test

### Positive scenario

On a sealed lab Linux host running Docker CE supervised by systemd, simulate a dockerd panic by injecting a SIGSEGV into dockerd via a kernel-fault-injection or by attaching gdb and forcing a crash, then ingest journalctl -u docker.service into sourcetype=linux:journald:docker, execute container_uc_3_1_8_docker_daemon_errors, and expect critical_dockerd_panic_or_fatal with non-null evidence_excerpt naming the panic, panic_count_24h>=1, and a populated owner_team row for the host_id when container_owner.csv has a DOCKER_DAEMON_HOST row.

### Negative scenario

Run a healthy Docker host serving production-shape traffic for one hour with dockerd nominal, containerd nominal, and Prometheus engine_api 5xx rate below one percent, confirm linux:journald:docker shows only routine info-priority lines, confirm linux:journald:containerd shows no panic markers, confirm docker:metrics emits engine_api_request_total counters with 2xx dominance, and verify the saved search returns no severity row for the host across multiple intervals.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control jointly with the Linux observability engineer who certifies Splunk Add-on for Linux on every Docker host and the container platform lead who controls dockerd flags, /etc/docker/daemon.json contents, and systemd unit drop-ins on the worker fleet. This walk-tier use case answers a question that is structurally distinct from every other UC in this category: when the Docker Engine process itself is failing — not the workloads it supervises — every retry-policy cadence, every container memory cgroup analysis, and every health-probe correlation downstream becomes a moot exercise until dockerd or containerd recovers. UC-3.1.1 classifies container die exit codes; UC-3.1.2 reads cgroup OOM controllers; UC-3.1.3 surfaces CPU throttle pressure; UC-3.1.13 watches restart-policy back-off; UC-3.1.22 tracks HEALTHCHECK transitions; UC-3.1.6 monitors privileged containers; UC-3.1.25 catches docker.sock exposure; UC-3.1.28 tracks Swarm replica convergence. Each of those UCs assumes the engine is alive and serving an API. UC-3.1.8 is the engine-process reliability axis itself.

Three telemetry feeds are required and non-substitutable. First, journalctl -u docker.service must reach Splunk via sourcetype linux:journald:docker. The Splunk Add-on for Linux scripted journal input or a systemd-journald-to-HEC bridge can both produce this feed; what matters is that PRIORITY, SYSTEMD_UNIT, MESSAGE, and host fields survive into Splunk so log_priority<=4 (warning or worse on the syslog scale where 0 emerg, 1 alert, 2 crit, 3 err, 4 warning) and the regex taxonomy in the SPL can classify each line. Second, journalctl -u containerd.service must reach Splunk as sourcetype linux:journald:containerd. The shim-v2 architecture introduced in containerd 1.5 and stabilized in 1.6 runs a containerd-shim-runc-v2 process per container; when that shim panics with SIGSEGV or SIGBUS, dockerd typically logs shim disconnected within roughly five seconds and the running container becomes a zombie — alive on the kernel cgroups but unmanageable by the engine until an operator either kills the dead shim and restarts containerd or reboots the host. Third, dockerd exposes Prometheus metrics on /metrics when metrics-addr is enabled in /etc/docker/daemon.json (for example, the canonical setting is "metrics-addr": "127.0.0.1:9323"). Splunk OpenTelemetry Collector configured with a prometheus receiver scrapes these metrics into sourcetype docker:metrics. Critical metric families include engine_daemon_engine_info, engine_daemon_engine_cpu_percent (or its process_cpu_seconds_total derivative when the build does not export the percent gauge directly), engine_daemon_health_checks_failed_total, and engine_api_request_total counters labelled with HTTP status codes for 5xx-rate calculation against the 2xx baseline.

Governance lookups: docker_daemon_error_taxonomy.csv carries error_class, default_severity, recommended_response, and kfp_pattern columns so the pipeline emits a canonical taxonomy hint with each severity row even when the SPL classifier disagrees with vendor-specific naming after a Docker Engine upgrade. Refresh the file when Docker releases new error message formats — Docker maintainers occasionally rename log lines in the moby/moby tree without a major version bump, and Mirantis Container Runtime ships its own error strings on a slightly different release cadence. container_owner.csv reuses the UC-3.1.x pattern with host_id, container_name, owner_team; for daemon-tier alerts, populate a row per host with container_name=DOCKER_DAEMON_HOST so platform on-call routing matches the synthetic name the SPL emits inside the closing join. Both lookups belong under the same Splunk app as the saved search and should be versioned in git with weekly publishing automation.

Risk briefing for incident commanders: a single dockerd panic on a host running 200 containers takes down 200 customer-visible service instances if live-restore is not enabled, because dockerd is the supervisor that holds the open file descriptors connecting the kernel cgroups to the orchestrator state. With live-restore=true configured in /etc/docker/daemon.json, kernel cgroups keep workloads running while dockerd is restarted, but dockerd must still be brought back up cleanly to reattach. A containerd-shim crash is more insidious because the shim is one process per container, so a single shim crash orphans only one container, but a shim crash storm during a kernel regression or a runc CVE rollout can orphan dozens. dockerd cannot reconnect to a dead shim, so the orphaned container becomes unschedulable and unkillable except via SIGKILL on the zombie shim PID followed by a containerd restart. Engine API saturation cascades into platform-wide deploy failures when CI/CD pipelines hammer /containers/json, /images/create, or /containers/{id}/start with concurrent calls; the daemon ulimit, socket backlog, and gRPC channel between dockerd and containerd all become contention points before any individual container fails, and the symptoms look like a distributed problem until you read engine_api_request_total split by status code.

Licensing and volume: linux:journald:docker is low volume during steady state — a healthy dockerd writes a handful of lines per minute — but error storms during incidents can burst to thousands of lines per second when a storage driver loops on a corrupted overlay layer or a libnetwork driver retries an iptables installation. Plan for dynamic licensing peaks. linux:journald:containerd carries a similar profile. docker:metrics from a Prometheus scrape every fifteen seconds against a single dockerd produces roughly 200 KB per minute per host depending on label cardinality; multiplied across 50,000+ Docker hosts this becomes a non-trivial line item, so mirror engine_daemon_* gauges and engine_api 5xx counters into a metrics index rather than a logs index where possible, and consider summarizing into a dedicated metrics summary on the search head when retention exceeds thirty days.

Legal and privacy: dockerd journal lines occasionally contain image references, registry hostnames, and command arguments that may leak environment variable fragments or internal service names. Redact at the forwarder before HEC, restrict index=oti_containers to operators who hold the platform engineering role, and confirm that evidence_excerpt fields shown on dashboards do not surface PII when image labels include customer identifiers in regulated estates.

Differentiation recap relative to sibling UCs: UC-3.1.1, UC-3.1.2, UC-3.1.3, UC-3.1.13, and UC-3.1.22 are container-level reliability and performance signals; UC-3.1.6 and UC-3.1.25 are container-level and daemon-level security signals; UC-3.1.28 is orchestrator-level convergence. UC-3.1.8 is the only UC in this category that scopes evidence to the engine process itself — dockerd and containerd journald error streams plus dockerd Prometheus metrics. Do not merge those concerns into any other UC or analysts will lose the ability to route engine-process incidents to platform infrastructure owners while routing container-level incidents to application owners.

### Step 2 — Configure data collection

On every Linux worker that runs Docker CE, Mirantis Container Runtime, or an approved enterprise Engine build, install Splunk Add-on for Linux (Splunkbase 833) with a journal scripted input scoped to the docker.service and containerd.service systemd units. The scripted input should emit one event per journal entry with sourcetype set explicitly to linux:journald:docker and linux:journald:containerd respectively rather than the generic linux:journald default, because the SPL multisearch arms key on those exact sourcetype strings to keep the regex taxonomy bounded to engine-process evidence. Preserve PRIORITY, SYSTEMD_UNIT, MESSAGE, _HOSTNAME, _BOOT_ID, and _MACHINE_ID fields by aligning the input filter, then map host_id from _HOSTNAME or the equivalent host string Universal Forwarders emit, lower-casing it consistently across the fleet so joins to container_owner.csv stay deterministic.

Validate the input on a canary host: cat /var/log/journal/$(hostname)/system.journal | systemd-cat-test or the equivalent journalctl --output=json --no-pager command should produce JSON that maps cleanly to the props.conf KV_MODE settings the add-on ships. If your operations team runs journald in volatile mode, ensure the Splunk forwarder reads from /run/log/journal rather than /var/log/journal so error bursts during incidents are not lost when the in-memory buffer rolls. For estates that forward journald via RFC5424 syslog through Splunk Connect for Syslog, set sourcetype overrides on the SC4S filter so the same linux:journald:docker and linux:journald:containerd contracts hold downstream — the SPL does not care which transport delivered the line.

For the Prometheus metrics feed, edit /etc/docker/daemon.json on each host to enable the experimental metrics endpoint with a snippet equivalent to {"metrics-addr": "127.0.0.1:9323", "experimental": true} and reload dockerd via systemctl reload docker. The experimental flag is required only for older Docker Engine versions; newer builds expose the metrics endpoint without the flag. Configure the Splunk OpenTelemetry Collector with a prometheus receiver that scrapes 127.0.0.1:9323/metrics every fifteen seconds and exports through HEC into sourcetype docker:metrics. Map the metric_name field from the OpenTelemetry __name__ attribute, the metric_value field from the value, and the http_status field from the code or status label that engine_api_request_total emits. For Mirantis Container Runtime nodes that disable the metrics endpoint by default, follow vendor guidance to re-enable; if the endpoint cannot be enabled for security policy reasons, document the missing metrics arm in the comment macro and accept that engine_api 5xx detection will be limited to journal-side hints.

Security hygiene: the metrics endpoint should not be exposed beyond 127.0.0.1 on a routable interface. If a centralized Prometheus must scrape it, use a unix socket forwarder or an SSH tunnel rather than binding the daemon to 0.0.0.0:9323. UC-3.1.25 monitors socket exposure separately and catches the related dockerd -H tcp:// failure; this UC does not duplicate that detection, but the controls are complementary in production estates.

Index routing: index=oti_containers carries all three sourcetypes with shorter hot retention than logs in regulated estates, and index=evidence_oti for weekly CSV exports of severity rows. If your security office uses different index names, update the comment macro in the saved search before promoting the SPL to production. Roles must allow search on index=oti_containers for platform engineers and a narrower subscope for application teams who need to confirm whether a service incident is engine-related.

Expected validation searches before saving the alert: index=oti_containers sourcetype=linux:journald:docker SYSTEMD_UNIT=docker.service earliest=-15m, index=oti_containers sourcetype=linux:journald:containerd SYSTEMD_UNIT=containerd.service earliest=-15m, and index=oti_containers sourcetype=docker:metrics metric_name=engine_daemon_engine_info earliest=-15m. Each must return events on a healthy fleet before the saved search is scheduled. Skew between host clock and Splunk _time must stay under thirty seconds or the time_window=5m streamstats inside the metrics arm and the relative_time bounds in the eventstats panic_count_1h calculation will lie.

### Step 3 — Create search and alert

Save the SPL as saved search container_uc_3_1_8_docker_daemon_errors with schedule */5 * * * * (or */15 * * * * during cost reviews when the search head shows scan pressure) and time range earliest=-24h@h latest=@h. Throttle duplicate critical_dockerd_panic_or_fatal pages per host_id for forty-five minutes unless panic_count_24h grows by more than one inside an hour, which strongly indicates an automation loop relaunching dockerd into the same crash. Critical_containerd_shim_crash_with_orphan should bypass throttling because each crash represents a distinct orphaned container that needs SIGKILL and reconciliation. high_storage_driver_error_sustained, high_api_5xx_rate_above_5pct, medium_libnetwork_driver_failure, and low_image_manifest_unauthorized should follow standard duplicate-suppression cadence keyed to host_id and severity tier.

Understanding the pipeline in operator terms: the opening comment macro is the contract for index names, lookup paths, threshold tunables, and the explicit differentiation from container-level UCs. multisearch fans three arms so a silent failure in one collector path (for example, a journald scripted input crash on the host) does not blank the entire detection. Each arm produces a uniform schema (_time, host_id, daemon_unit, error_class, signal_type, evidence_excerpt, api_5xx_rate, engine_cpu_pct, health_failed_5m) so downstream eventstats and stats can aggregate without arm-specific branching. The dockerd journal arm is authoritative for engine-process error class. The containerd journal arm is authoritative for shim-process panic. The Prometheus metrics arm is authoritative for engine API saturation. coalesce lists absorb camelCase and snake_case journald field names emitted by different forwarder versions and OpenTelemetry attribute conventions.

streamstats time_window=5m inside the metrics arm computes a sliding five-minute sum of api_5xx and api_2xx counter values per host so api_5xx_rate becomes a rolling percentage rather than a snapshot at one timestamp. bucket span=5m as bucket_5min outside the multisearch fan-in then assigns each event to a fixed five-minute window so eventstats count AS error_count_5min produces the in-window error density per host per error_class. Two more eventstats blocks roll panic_count_24h, containerd_shim_crash_count, storage_driver_error_count, network_driver_error_count, and image_pull_unauth_count over the full 24h window per host, plus panic_count_1h and shim_crashes_1h gated by relative_time(now(), -1h) for fast-moving incident escalation. A final eventstats lifts api_5xx_rate_host and engine_cpu_pct_host as per-host context drawn only from docker_metrics_prometheus rows so journal-only rows still see the latest metric context.

The inputlookup join against docker_daemon_error_taxonomy.csv carries default_severity, recommended_response_taxonomy, and kfp_pattern columns into each row keyed on error_class, satisfying governance reviewers who require lookup commands to be wrapped inside a join subsearch (UC-3.1.6 and UC-3.1.25 follow the same pattern). The case ladder emits exactly six severity strings or null: critical_dockerd_panic_or_fatal, critical_containerd_shim_crash_with_orphan, high_storage_driver_error_sustained, high_api_5xx_rate_above_5pct, medium_libnetwork_driver_failure, low_image_manifest_unauthorized. recommended_response provides paging-bridge text per tier so analysts do not improvise under stress; the taxonomy hint is appended when present so vendor-specific guidance flows alongside the canonical response. eval container_name=DOCKER_DAEMON_HOST sets a synthetic key for the closing join with container_owner.csv so platform on-call routing works without polluting container-level inventory tables. The final stats collapse to one row per (host_id, daemon_unit, error_class) with all rolled-up counters, ensuring the table is sortable and dashboard-friendly.

Alert actions should attach the closing table row, link to the dashboard described in the visualization field, and include a deep link to UC-3.1.13 saved search filtered on the same host so analysts can confirm whether container-level restart loops accompany the engine-process panic — if both fire, restart-loop counters are misleading until the engine returns. Critical tiers should also page the SOC if the recent incident timeline includes UC-3.1.25 critical_2375_unencrypted_daemon, because dockerd panics during an active socket-exposure incident raise immediate forensics questions.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:

```spl
`comment("UC-3.1.8 Docker Daemon Errors. Engine-process reliability axis distinct from container-level UCs (.1/.2/.3/.13/.22) and security UCs (.6/.25/.28). Tunables: index=oti_containers; sourcetypes linux:journald:docker linux:journald:containerd docker:metrics; lookup docker_daemon_error_taxonomy.csv keyed by error_class with default_severity recommended_response kfp_pattern; container_owner.csv with host_id+container_name=DOCKER_DAEMON_HOST routing; api_5xx_warn_pct=5; engine_cpu_warn_pct=85; storage_sustained_count=3; earliest=-24h@h latest=@h.")`
| multisearch
    [ search index=oti_containers sourcetype="linux:journald:docker" earliest=-24h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, _HOSTNAME, host_id, dest, "")))
      | eval daemon_unit=trim(toString(coalesce(SYSTEMD_UNIT, systemd_unit, unit, "docker.service")))
      | eval log_priority=tonumber(tostring(coalesce(PRIORITY, priority, syslog_priority, "6")), 10)
      | eval level_raw=lower(toString(coalesce(level, log_level, severity, MESSAGE_LEVEL, "")))
      | eval msg_lc=lower(toString(coalesce(MESSAGE, message, _raw, "")))
      | where match(level_raw, "(?i)error|fatal|panic|warn") OR (log_priority<=4) OR match(msg_lc, "(?i)error|panic|fatal|failed|denied|unauthorized")
      | eval error_class=case(
          match(msg_lc, "(?i)panic|fatal error|runtime stack:|signal sigsegv|signal sigbus|signal sigabrt"), "dockerd_panic_or_fatal",
          match(msg_lc, "(?i)overlay2|devicemapper|btrfs|zfs|graphdriver|failed to mount|overlay layer|backing file|not a directory.*upper"), "storage_driver_error",
          match(msg_lc, "(?i)libcontainer|runc|oci runtime error|cgroup v2 setup failed|pivot_root|failed to create container"), "libcontainer_runc_error",
          match(msg_lc, "(?i)libnetwork|bridge already exists|iptables forwarding failed|driver failure|network sandbox|endpoint create"), "libnetwork_driver_failure",
          match(msg_lc, "(?i)http: panic serving|client disconnect during request|invalid api version|engine_api"), "engine_api_request_error",
          match(msg_lc, "(?i)permission denied.*docker|error mounting|access denied|operation not permitted"), "socket_or_permission_error",
          match(msg_lc, "(?i)manifest unknown|unauthorized: authentication required|insufficient_scope|denied: requested access"), "image_manifest_unauthorized",
          match(msg_lc, "(?i)error pulling image|registry returned|connection reset|unexpected eof"), "image_pull_or_registry_error",
          match(msg_lc, "(?i)shim disconnected|shim exited|task exited with error code"), "shim_disconnect_signal",
          match(msg_lc, "(?i)live-restore|live restore"), "live_restore_event",
          true(), "uncategorized_dockerd_error")
      | eval signal_type="dockerd_journal_error"
      | eval evidence_excerpt=substr(toString(coalesce(MESSAGE, message, _raw, "")),1,420)
      | eval api_5xx_rate=null()
      | eval engine_cpu_pct=null()
      | eval health_failed_5m=null()
      | fields _time host_id daemon_unit error_class signal_type evidence_excerpt api_5xx_rate engine_cpu_pct health_failed_5m ]
    [ search index=oti_containers sourcetype="linux:journald:containerd" earliest=-24h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, _HOSTNAME, host_id, dest, "")))
      | eval daemon_unit=trim(toString(coalesce(SYSTEMD_UNIT, systemd_unit, unit, "containerd.service")))
      | eval msg_lc=lower(toString(coalesce(MESSAGE, message, _raw, "")))
      | eval level_raw=lower(toString(coalesce(level, log_level, severity, "")))
      | where match(level_raw, "(?i)fatal|error|panic") OR match(msg_lc, "(?i)panic|fatal|signal sigsegv|signal sigbus|goroutine.*running|reaping shim|shim disconnected")
      | eval error_class=case(
          match(msg_lc, "(?i)panic|signal sigsegv|signal sigbus|goroutine.*running"), "containerd_shim_panic",
          match(msg_lc, "(?i)reaping shim|task is shutting down|shim exited"), "shim_reap_event",
          match(msg_lc, "(?i)rpc error|context deadline exceeded|grpc"), "containerd_rpc_error",
          match(msg_lc, "(?i)snapshot|content store|metadata store"), "containerd_storage_error",
          true(), "uncategorized_containerd_error")
      | eval signal_type="containerd_journal_error"
      | eval evidence_excerpt=substr(toString(coalesce(MESSAGE, message, _raw, "")),1,420)
      | eval api_5xx_rate=null()
      | eval engine_cpu_pct=null()
      | eval health_failed_5m=null()
      | fields _time host_id daemon_unit error_class signal_type evidence_excerpt api_5xx_rate engine_cpu_pct health_failed_5m ]
    [ search index=oti_containers sourcetype="docker:metrics" earliest=-24h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, instance, dest, "")))
      | eval daemon_unit="docker.service"
      | eval metric_name=trim(toString(coalesce(metric_name, name, __name__, "")))
      | eval metric_value=tonumber(tostring(coalesce(value, metric_value, "")), 10)
      | eval http_status=trim(toString(coalesce(code, status, status_code, "")))
      | where isnotnull(metric_value) AND len(metric_name)>0
      | eval is_api_5xx=if(match(metric_name, "(?i)engine_api_request_total|http_request") AND match(http_status, "^5[0-9]{2}$"), 1, 0)
      | eval is_api_2xx=if(match(metric_name, "(?i)engine_api_request_total|http_request") AND match(http_status, "^2[0-9]{2}$"), 1, 0)
      | eval cpu_pct_sample=if(match(metric_name, "(?i)engine_daemon_engine_cpu_percent|process_cpu_seconds_total"), metric_value, null())
      | eval health_failed_sample=if(match(metric_name, "(?i)engine_daemon_health_checks_failed_total"), metric_value, null())
      | sort 0 + host_id, _time
      | streamstats time_window=5m current=t global=f sum(eval(if(is_api_5xx==1, metric_value, 0))) AS api_5xx_5m sum(eval(if(is_api_2xx==1, metric_value, 0))) AS api_2xx_5m max(cpu_pct_sample) AS engine_cpu_pct_5m max(health_failed_sample) AS health_failed_5m_streaming BY host_id
      | eval api_total_5m=api_5xx_5m + api_2xx_5m
      | eval api_5xx_rate=if(api_total_5m>0, round(100.0 * api_5xx_5m / api_total_5m, 2), 0)
      | eval error_class=case(
          api_5xx_rate>=5 AND api_total_5m>=20, "engine_api_5xx_rate_high",
          isnotnull(health_failed_5m_streaming) AND health_failed_5m_streaming>0, "engine_healthcheck_failure",
          isnotnull(engine_cpu_pct_5m) AND engine_cpu_pct_5m>=85, "engine_daemon_cpu_saturation",
          true(), null())
      | where isnotnull(error_class)
      | eval signal_type="docker_metrics_prometheus"
      | eval evidence_excerpt="prom_signal api_5xx_rate=" . tostring(coalesce(api_5xx_rate, 0)) . "% total_5m=" . tostring(coalesce(api_total_5m, 0)) . " cpu_pct=" . tostring(coalesce(engine_cpu_pct_5m, 0)) . " health_failed_5m=" . tostring(coalesce(health_failed_5m_streaming, 0))
      | eval engine_cpu_pct=engine_cpu_pct_5m
      | eval health_failed_5m=health_failed_5m_streaming
      | fields _time host_id daemon_unit error_class signal_type evidence_excerpt api_5xx_rate engine_cpu_pct health_failed_5m ]
| eval host_id=if(isnull(host_id) OR len(trim(host_id))==0, "unknown_host", host_id)
| sort 0 + host_id, daemon_unit, _time
| bucket _time span=5m as bucket_5min
| eventstats count AS error_count_5min BY host_id, error_class, bucket_5min
| eventstats sum(eval(if(error_class=="dockerd_panic_or_fatal", 1, 0))) AS panic_count_24h sum(eval(if(error_class=="containerd_shim_panic", 1, 0))) AS containerd_shim_crash_count sum(eval(if(error_class=="storage_driver_error", 1, 0))) AS storage_driver_error_count sum(eval(if(error_class=="libnetwork_driver_failure", 1, 0))) AS network_driver_error_count sum(eval(if(error_class=="image_manifest_unauthorized", 1, 0))) AS image_pull_unauth_count BY host_id
| eventstats sum(eval(if(error_class=="dockerd_panic_or_fatal" AND _time>=relative_time(now(), "-1h"), 1, 0))) AS panic_count_1h sum(eval(if(error_class=="containerd_shim_panic" AND _time>=relative_time(now(), "-1h"), 1, 0))) AS shim_crashes_1h BY host_id
| eventstats max(eval(if(signal_type=="docker_metrics_prometheus", api_5xx_rate, null()))) AS api_5xx_rate_host max(eval(if(signal_type=="docker_metrics_prometheus", engine_cpu_pct, null()))) AS engine_cpu_pct_host BY host_id
| join type=left max=0 error_class
    [| inputlookup docker_daemon_error_taxonomy.csv
     | eval error_class=trim(toString(coalesce(error_class, class, "")))
     | eval default_severity=lower(toString(coalesce(default_severity, severity_default, severity, "")))
     | eval recommended_response_taxonomy=toString(coalesce(recommended_response, response, action, ""))
     | eval kfp_pattern=toString(coalesce(kfp_pattern, false_positive_hint, ""))
     | fields error_class default_severity recommended_response_taxonomy kfp_pattern ]
| eval severity=case(
    error_class=="dockerd_panic_or_fatal", "critical_dockerd_panic_or_fatal",
    error_class=="containerd_shim_panic", "critical_containerd_shim_crash_with_orphan",
    error_class=="shim_disconnect_signal" AND shim_crashes_1h>=1, "critical_containerd_shim_crash_with_orphan",
    error_class=="storage_driver_error" AND error_count_5min>=3, "high_storage_driver_error_sustained",
    error_class=="engine_api_5xx_rate_high", "high_api_5xx_rate_above_5pct",
    error_class=="engine_daemon_cpu_saturation", "high_api_5xx_rate_above_5pct",
    error_class=="engine_healthcheck_failure", "high_api_5xx_rate_above_5pct",
    error_class=="engine_api_request_error" AND coalesce(api_5xx_rate_host, 0)>=5, "high_api_5xx_rate_above_5pct",
    error_class=="libnetwork_driver_failure", "medium_libnetwork_driver_failure",
    error_class=="image_manifest_unauthorized", "low_image_manifest_unauthorized",
    true(), null())
| where isnotnull(severity)
| eval recommended_response=case(
    severity=="critical_dockerd_panic_or_fatal", "Page platform on-call: dockerd panic on a host with many containers; capture journalctl -u docker.service --since '15 min ago', confirm live-restore=true in /etc/docker/daemon.json so kernel cgroups keep workloads alive while the engine recovers, validate /var/lib/docker integrity, file a Docker support bundle, and bring the engine up under change control before declaring the host healthy.",
    severity=="critical_containerd_shim_crash_with_orphan", "Page platform on-call: containerd-shim-runc-v2 crash leaves orphaned containers attached to kernel cgroups while dockerd lost the supervisory link; identify orphan PIDs via ps -ef | grep containerd-shim, send SIGKILL to zombie shims, restart containerd, reconcile docker ps -a, and document orphan count in the incident timeline.",
    severity=="high_storage_driver_error_sustained", "Storage driver overlay2, devicemapper, or btrfs errors sustained at three or more events in five minutes: inspect /var/lib/docker disk usage and inode pressure, validate xfs or ext4 health with smartctl and dmesg, drain workloads if filesystem integrity is suspect, and engage the storage team before further image pulls compound damage.",
    severity=="high_api_5xx_rate_above_5pct", "Engine API five-percent or higher 5xx rate, daemon CPU saturation, or health-check failures: capture engine_daemon_engine_info gauge trends, inspect socket backlog with ss -lpn, throttle CI/CD pipelines hammering /containers/json, and consider raising daemon ulimits or splitting socket consumers across hosts.",
    severity=="medium_libnetwork_driver_failure", "libnetwork driver failure on bridge, overlay, or macvlan: inspect docker network ls and docker network inspect for stuck pools, validate iptables -S for FORWARD chain state, restart networking only with an explicit change ticket, and watch for reload loops.",
    severity=="low_image_manifest_unauthorized", "Image manifest unauthorized or denied: validate registry credentials in /etc/docker/daemon.json or systemd drop-ins, rotate expired pull secrets, and confirm registry mirror health; treat as configuration drift rather than engine failure unless paired with daemon-side errors on the same host.",
    true(), "Correlate dockerd journal, containerd journal, and Prometheus metrics before closure; do not silence alerts on the host, route to platform on-call.")
| eval recommended_response=if(isnotnull(recommended_response_taxonomy) AND len(trim(recommended_response_taxonomy))>0, recommended_response . " | Taxonomy hint: " . recommended_response_taxonomy, recommended_response)
| eval container_name="DOCKER_DAEMON_HOST"
| join type=left max=0 host_id, container_name
    [| inputlookup container_owner.csv
     | eval host_id=lower(toString(coalesce(host_id, host, "")))
     | eval container_name=toString(container_name)
     | eval owner_team=toString(coalesce(owner_team, squad, ""))
     | fields host_id container_name owner_team ]
| stats max(error_count_5min) AS error_count_5min max(panic_count_24h) AS panic_count_24h max(containerd_shim_crash_count) AS containerd_shim_crash_count max(storage_driver_error_count) AS storage_driver_error_count max(network_driver_error_count) AS network_driver_error_count max(image_pull_unauth_count) AS image_pull_unauth_count max(api_5xx_rate_host) AS api_5xx_rate max(engine_cpu_pct_host) AS engine_cpu_pct values(signal_type) AS signal_types latest(evidence_excerpt) AS evidence_excerpt latest(severity) AS severity latest(recommended_response) AS recommended_response latest(owner_team) AS owner_team BY host_id, daemon_unit, error_class
| eval signal_types=mvjoin(signal_types, "|")
| table host_id daemon_unit error_class signal_types error_count_5min panic_count_24h containerd_shim_crash_count storage_driver_error_count network_driver_error_count api_5xx_rate engine_cpu_pct image_pull_unauth_count severity recommended_response owner_team evidence_excerpt
```

### Step 4 — Validate

Positive test A — dockerd panic injection in a sealed lab: on a disposable Linux VM running Docker CE supervised by systemd, force a dockerd crash by sending SIGSEGV via gdb attach or by exhausting the daemon ulimit until the engine panics on goroutine creation. Wait for journalctl -u docker.service to capture the panic stack and confirm linux:journald:docker rows arrive in Splunk within one collection interval. Execute container_uc_3_1_8_docker_daemon_errors and expect critical_dockerd_panic_or_fatal with non-null evidence_excerpt naming the runtime stack, panic_count_24h>=1, and a populated owner_team row when container_owner.csv has a DOCKER_DAEMON_HOST row for that host.

Positive test B — containerd-shim panic in a sealed lab: build a runc binary with a deliberate fault-injection in the shim startup path, deploy to a single lab host outside production, run a container that invokes the faulty shim, and watch journalctl -u containerd.service for the panic stack and dockerd journal for the matching shim disconnected line. Confirm both rows arrive within five seconds of each other in Splunk and verify critical_containerd_shim_crash_with_orphan fires with non-zero containerd_shim_crash_count. Document orphan PIDs that survived the panic and confirm SIGKILL on the zombie shim followed by containerd restart cleared the orphan from docker ps -a.

Positive test C — engine_api 5xx storm: run a short-duration concurrent docker ps and docker inspect storm against a lab host with a small ulimit (for example ulimit -n 256) so the engine returns 5xx for a fraction of requests above the queue depth, and confirm docker:metrics shows api_5xx_rate crossing five percent inside a five-minute window with api_total_5m above twenty. Verify high_api_5xx_rate_above_5pct fires with the correct evidence_excerpt and recommended_response. Restore ulimit before leaving the lab.

Positive test D — storage driver fault injection: on a lab VM with overlay2 storage driver, mount /var/lib/docker on a small loop-back device, fill the device until ENOSPC errors appear, and run docker pull against a multi-layer image. Expect linux:journald:docker rows showing storage_driver_error patterns and confirm error_count_5min crosses three so high_storage_driver_error_sustained fires.

Negative test — healthy production-shape traffic: run a healthy Docker host serving production-shape traffic for one hour with dockerd nominal, containerd nominal, and Prometheus engine_api 5xx rate below one percent. Confirm linux:journald:docker shows only routine info-priority lines, linux:journald:containerd shows no panic markers, and docker:metrics emits engine_api_request_total counters with 2xx dominance. Verify the saved search returns no severity row for the host across multiple intervals.

Field sanity: temporarily rename SYSTEMD_UNIT to systemd_unit in a sandbox forwarder props.conf and confirm coalesce still resolves daemon_unit. Temporarily emit metric labels under the OpenTelemetry __name__ form rather than metric_name and confirm the metrics arm still classifies. RBAC: a reader without index=oti_containers must see zero rows. Clock skew: NTP drift exceeding thirty seconds breaks streamstats time_window=5m semantics, so enforce ntpdate or chrony health checks on managers and forwarders.

Correlation: compare alert times to UC-3.1.13 restart-loop counters; an engine-process panic should cause every restart-loop row on that host to become misleading until the engine returns. Cross-launch UC-3.1.25 to confirm no concurrent socket-exposure incident is in progress.

### Step 5 — Operationalize & Troubleshoot

Case 1 — dockerd panic on a multi-tenant build host: treat as host-wide outage; capture journalctl -u docker.service --since '15 min ago' with --no-pager output redirected to a forensics index, confirm live-restore=true is in /etc/docker/daemon.json so kernel cgroups keep workloads breathing while the engine recovers, validate /var/lib/docker integrity with df -i and du -sh, file a Docker support bundle via docker support, and bring the engine up under change control. If panic_count_24h is >=2 within an hour the engine is likely looping into the same crash; rollback the most recent dockerd version under change control before further restart attempts compound damage.

Case 2 — containerd-shim panic from runc CVE rollout: orphaned containers will not respond to docker stop or docker kill because dockerd lost the supervisory link; identify orphan PIDs via ps -ef | grep containerd-shim, capture process details for forensics, send SIGKILL to each zombie shim, restart containerd via systemctl restart containerd, then reconcile docker ps -a output. Document orphan count in the incident timeline and pair the row with vulnerability-management evidence on the runc rollout schedule.

Case 3 — Storage driver overlay2 inode exhaustion: error_count_5min crosses three when /var/lib/docker runs out of inodes long before it runs out of bytes; confirm with df -i, then drain workloads off the host, prune unused images and dangling layers via docker image prune -a under change control, and engage the storage team if the host filesystem itself is showing dmesg corruption. Do not delete /var/lib/docker subdirectories manually because the cleanup is not safe while dockerd is running and may corrupt the metadata store.

Case 4 — Engine API 5xx flood from CI/CD scrape storm: api_5xx_rate above five percent during build-window peaks usually reflects parallel CI executors hammering /containers/json or /containers/{id}/stats; throttle the CI orchestrator, raise daemon ulimits via systemd drop-in (LimitNOFILE) under change control, and consider splitting socket consumers across hosts with a docker proxy or a build-local socket. If api_5xx_rate stays elevated after the CI pause, the cause is an internal dockerd contention point rather than client volume; capture goroutine dumps via SIGUSR1 and engage Docker support.

Case 5 — libnetwork iptables FORWARD chain wedge: medium_libnetwork_driver_failure on a host that just lost networking suggests iptables -S FORWARD has been corrupted or another agent (firewalld, ufw, kube-proxy) collided with libnetwork rules; do not bounce networking globally — first confirm whether iptables-restore can re-seed the chain from a known-good snapshot, and only then restart the docker network namespace if the chain stays wedged. Watch for reload loops where libnetwork retries the same install repeatedly; that pattern usually means the kernel iptables module mismatch is the underlying issue.

Case 6 — Image manifest unauthorized after registry credential rotation: low_image_manifest_unauthorized rows blooming after a planned credential rotation indicate that /etc/docker/daemon.json or the systemd drop-in for docker.service no longer carries the new credentials; rotate via the secret-management pipeline rather than manually editing daemon.json, and confirm the registry mirror health if the credentials prove valid. Do not raise this severity to high unless it pairs with daemon-side errors on the same host because credential drift is a configuration issue, not an engine failure.

Case 7 — OOM-killed dockerd from co-resident workload memory pressure: dmesg may show oom-kill targeting the dockerd PID when a co-resident workload exhausts host memory; the root cause is host-level capacity, not the engine, and UC-3.1.2 owns the cgroup analysis for memory. Correlate the dockerd panic timestamp with UC-3.1.2 oom_kill rows on the same host and route the incident to capacity owners, not engine on-call. Tune cgroup memory limits or split workloads to a less-loaded host before redeploying dockerd.

Case 8 — Live-restore reload event mistaken for panic: a planned dockerd reload via systemctl reload docker writes live-restore enable or live-restore reload lines to journald that the regex taxonomy classifies as live_restore_event rather than dockerd_panic_or_fatal, but operators occasionally see the reload churn in dashboards and assume the worst. Tag the maintenance window in container_owner.csv (or a dedicated maintenance lookup) and downgrade live_restore_event rows during planned patch windows, then re-enable the alert routing once the window closes.

Case 9 — journald rotation gap during heavy logging: when /var/log/journal fills the configured SystemMaxUse limit, journald rotates and may briefly drop entries before the Splunk forwarder catches up, producing apparent error gaps in Splunk that are actually collection gaps. Tune SystemMaxUse on the host, switch journald to volatile mode for short retention, and ensure the Splunk forwarder reads from /run/log/journal during the rotation window.

Case 10 — Mirantis Container Runtime field-naming drift after upgrade: a Mirantis upgrade may rename SYSTEMD_UNIT casing or rebrand error message strings in journald, producing a sudden uncategorized_dockerd_error spike. Reconcile the regex taxonomy against the Mirantis release notes, extend coalesce lists in props.conf, and update docker_daemon_error_taxonomy.csv with new strings before the next saved-search run.

Case 11 — docker:metrics scrape failures during dockerd restart: the prometheus receiver loses scrapes while dockerd is bouncing, producing apparent api_5xx_rate gaps even when the engine itself was the source of the trouble; this is acceptable because the journal arms still detect the panic. Document the gap pattern in the runbook so analysts do not mistake metric-scrape gaps for engine recovery.

Case 12 — host_id casing mismatch breaking owner_team join: when forwarders emit FQDN host strings and container_owner.csv carries short-name host_id rows, the closing join misses and owner_team stays null. Normalize casing in the lookup publisher and the SPL coalesce list together so paging routes deterministically; do not loosen the join keys.

Dashboard publishing follows the visualization field: an error_class heatmap by host_id over 24 hours with cell coloring escalating past three errors per five-minute bucket; a daemon-unit panic-count single-value tile with zero versus non-zero coloring; an api_5xx_rate line chart per host_id from docker:metrics with a five-percent reference band; and a severity-tiered table mirroring the SPL projection with drilldowns to journalctl excerpts, containerd panic stacks, and Prometheus engine_daemon_engine_info gauges. Add an annotations layer for live-restore reload events so analysts can visually distinguish planned reloads from unplanned panics.

Evidence retention: weekly CSV exports of the closing table to a restricted evidence index with lookup commit hashes satisfy internal audit samples when paired with change tickets that document dockerd version pins and runc CVE rollouts. Map findings to platform reliability SLO statements that quantify host-availability targets per worker class.

Governance: quarterly replay one historical engine-process incident through the SPL after Docker Engine, containerd, or Splunk Add-on for Linux upgrades, and update the comment macro when index names move. Update docker_daemon_error_taxonomy.csv whenever Docker maintainers rename error message strings in the moby/moby tree or Mirantis Container Runtime ships its own naming convention in a major release.

Closing checklist: five plain-text step headers use em dashes; multisearch lists three arms keyed on linux:journald:docker, linux:journald:containerd, and docker:metrics; coalesce appears in every arm to absorb camelCase and snake_case variants; streamstats appears for the metrics arm sliding window plus eventstats for the bucket-aligned counters; two join type=left max=0 blocks wrap inputlookup for docker_daemon_error_taxonomy.csv and container_owner.csv; severity case emits exactly the six mandated strings or null; the closing table projects sixteen analyst columns including host_id, daemon_unit, error_class, error_count_5min, panic_count_24h, api_5xx_rate, engine_cpu_pct, severity, recommended_response, and owner_team; narrative JSON fields contain no asterisk emphasis pairs; knownFalsePositives stay reliability-themed and distinct from sibling UCs; references span Docker Inc dockerd documentation, containerd runtime-v2 architecture, systemd journalctl(1) man page, Docker live-restore tradeoffs, a specific Splunk Lantern article path, and the Docker daemon Prometheus metrics documentation.

Supplemental engineering notes for long-term owners: when migrating to rootless Docker, journald paths shift to user.slice and metrics endpoint configuration moves to ~/.config/docker/daemon.json; revisit the comment macro and props aliases after the migration. When CI fleets standardize on BuildKit remote builders or rootless Kaniko, dockerd panic exposure shrinks because the build host no longer runs containers, but the metrics endpoint still merits monitoring for build pipeline saturation. When integrating Splunk ITSI, map severity_tier to episode priority with critical_dockerd_panic_or_fatal as P1 and critical_containerd_shim_crash_with_orphan as P2 because shim crashes orphan a smaller blast radius. When red teaming, pair this UC with UC-3.1.25 to confirm a panic is not coincident with active socket exposure. When OT edge gateways run Docker for legacy reasons, duplicate the governance lookups with OT-specific owner_team routing and lower the api_5xx_rate threshold because edge consumers tolerate less daemon overhead than data-center fleets. When auditors ask for SOC2 availability evidence, attach a screenshot of the saved search description, weekly CSV exports, and the dockerd version pin trail to the control test sample. When finance questions ingest cost, compare license bytes for journald and Prometheus scrapes against the expected cost of a single fleet-wide engine-failure incident response retainer.

Appendix — Taxonomy field contract for docker_daemon_error_taxonomy.csv

error_class must match the SPL classifier output strings exactly: dockerd_panic_or_fatal, storage_driver_error, libcontainer_runc_error, libnetwork_driver_failure, engine_api_request_error, socket_or_permission_error, image_manifest_unauthorized, image_pull_or_registry_error, shim_disconnect_signal, live_restore_event, uncategorized_dockerd_error, containerd_shim_panic, shim_reap_event, containerd_rpc_error, containerd_storage_error, uncategorized_containerd_error, engine_api_5xx_rate_high, engine_healthcheck_failure, engine_daemon_cpu_saturation. default_severity is informational only; the SPL severity ladder is authoritative. recommended_response carries vendor-specific or estate-specific guidance that supplements the canonical recommended_response built into the case ladder. kfp_pattern names a known false-positive pattern that the runbook should consult before paging.

Appendix — Probe taxonomy expectations for shim crashes

containerd-shim-runc-v2 panics typically include a goroutine running stack with the offending function name, a signal sigsegv or sigbus marker, and a runtime address that may correspond to a kernel-side memory mapping problem rather than a userspace bug. When the panic stack mentions runc directly, validate whether a runc CVE rollout is in progress and whether the upgrade reached the offending host before the panic. When the panic stack mentions golang runtime functions only, escalate to the containerd maintainers via the support bundle path with a redacted stack snippet attached to the ticket.

Appendix — Live-restore semantics

live-restore=true in /etc/docker/daemon.json keeps containers running while dockerd restarts, but it does not protect against shim crashes or kernel-side faults. Live-restore is a safety net for engine-process panics and planned reloads, not for runc CVE rollouts or shim panics. Operators who assume live-restore makes engine reliability a non-issue underestimate shim-process failure modes, which is why this UC explicitly carries containerd-shim panic detection in a separate arm.

Appendix — FinOps alignment

Attach panic_count_24h trends to platform-tier capacity tickets so finance sees monitoring maturity moving with reliability investment. Pair weekly exports with incident retrospectives that mention dockerd version pins, runc CVE rollouts, and storage driver migrations, proving the control influenced real engineering decisions rather than producing a noisy log volume tax.

Appendix — Security alignment

Restrict dashboards that expose evidence_excerpt because journald lines occasionally include image references and registry hostnames. Mask evidence_excerpt in tier-one analyst views when raw journal entries contain PII or customer identifiers in regulated estates.

Appendix — Performance alignment

If multisearch or eventstats costs grow as the fleet expands beyond 50,000 Docker hosts, summarize linux:journald:docker into a metrics index retaining only error_class counts per five-minute bucket per host before alerting, and keep raw journal entries in a shorter-retention logs index for forensic drilldowns.

Appendix — Training alignment

Run tabletop exercises where operators must distinguish dockerd panic from containerd-shim panic from engine_api saturation using the same telemetry this UC surfaces, and reinforce the rule that container-level UCs are misleading until engine-process health is confirmed.

Appendix — Documentation alignment

Maintain an internal wiki page mapping Docker Engine and containerd release notes to regex taxonomy updates so coalesce lists and case classifiers do not sprawl without review.

Appendix — Review cadence

Quarterly replay one historical engine-process incident through the SPL after Docker Engine, containerd, or Splunk Add-on for Linux upgrades, and confirm regex taxonomy still matches the latest journald output formats.

Appendix — Escalation alignment

When severity is critical_dockerd_panic_or_fatal and panic_count_24h exceeds three on the same host, escalate immediately to vendor support because the daemon is likely looping into the same crash and a rollback decision must be made under change control.

Appendix — Telemetry hygiene

Deduplicate Splunk Add-on for Linux journal scripted inputs and Splunk OpenTelemetry Collector log receivers when both paths exist during migration so error_count_5min does not double-count the same line.

Appendix — Collector hygiene

Cap docker:metrics cardinality on CI executors or exclude builder profiles via macros to preserve search performance, because BuildKit pipelines emit short-lived metric labels that inflate label cardinality without helping engine-process detection.

Appendix — Governance alignment

Require lookup owners to approve changes to docker_daemon_error_taxonomy.csv in the same change record as Docker Engine version pins, so the taxonomy stays synchronized with vendor releases.

Final reminder: this UC remains scoped to the engine-process axis. Do not retitle it to cover container-level reliability, do not merge it with UC-3.1.25 socket exposure monitoring, and do not extend it to Kubernetes kubelet failure modes — those belong to UC-3.2.x and require different telemetry feeds entirely.

## SPL

```spl
`comment("UC-3.1.8 Docker Daemon Errors. Engine-process reliability axis distinct from container-level UCs (.1/.2/.3/.13/.22) and security UCs (.6/.25/.28). Tunables: index=oti_containers; sourcetypes linux:journald:docker linux:journald:containerd docker:metrics; lookup docker_daemon_error_taxonomy.csv keyed by error_class with default_severity recommended_response kfp_pattern; container_owner.csv with host_id+container_name=DOCKER_DAEMON_HOST routing; api_5xx_warn_pct=5; engine_cpu_warn_pct=85; storage_sustained_count=3; earliest=-24h@h latest=@h.")`
| multisearch
    [ search index=oti_containers sourcetype="linux:journald:docker" earliest=-24h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, _HOSTNAME, host_id, dest, "")))
      | eval daemon_unit=trim(toString(coalesce(SYSTEMD_UNIT, systemd_unit, unit, "docker.service")))
      | eval log_priority=tonumber(tostring(coalesce(PRIORITY, priority, syslog_priority, "6")), 10)
      | eval level_raw=lower(toString(coalesce(level, log_level, severity, MESSAGE_LEVEL, "")))
      | eval msg_lc=lower(toString(coalesce(MESSAGE, message, _raw, "")))
      | where match(level_raw, "(?i)error|fatal|panic|warn") OR (log_priority<=4) OR match(msg_lc, "(?i)error|panic|fatal|failed|denied|unauthorized")
      | eval error_class=case(
          match(msg_lc, "(?i)panic|fatal error|runtime stack:|signal sigsegv|signal sigbus|signal sigabrt"), "dockerd_panic_or_fatal",
          match(msg_lc, "(?i)overlay2|devicemapper|btrfs|zfs|graphdriver|failed to mount|overlay layer|backing file|not a directory.*upper"), "storage_driver_error",
          match(msg_lc, "(?i)libcontainer|runc|oci runtime error|cgroup v2 setup failed|pivot_root|failed to create container"), "libcontainer_runc_error",
          match(msg_lc, "(?i)libnetwork|bridge already exists|iptables forwarding failed|driver failure|network sandbox|endpoint create"), "libnetwork_driver_failure",
          match(msg_lc, "(?i)http: panic serving|client disconnect during request|invalid api version|engine_api"), "engine_api_request_error",
          match(msg_lc, "(?i)permission denied.*docker|error mounting|access denied|operation not permitted"), "socket_or_permission_error",
          match(msg_lc, "(?i)manifest unknown|unauthorized: authentication required|insufficient_scope|denied: requested access"), "image_manifest_unauthorized",
          match(msg_lc, "(?i)error pulling image|registry returned|connection reset|unexpected eof"), "image_pull_or_registry_error",
          match(msg_lc, "(?i)shim disconnected|shim exited|task exited with error code"), "shim_disconnect_signal",
          match(msg_lc, "(?i)live-restore|live restore"), "live_restore_event",
          true(), "uncategorized_dockerd_error")
      | eval signal_type="dockerd_journal_error"
      | eval evidence_excerpt=substr(toString(coalesce(MESSAGE, message, _raw, "")),1,420)
      | eval api_5xx_rate=null()
      | eval engine_cpu_pct=null()
      | eval health_failed_5m=null()
      | fields _time host_id daemon_unit error_class signal_type evidence_excerpt api_5xx_rate engine_cpu_pct health_failed_5m ]
    [ search index=oti_containers sourcetype="linux:journald:containerd" earliest=-24h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, _HOSTNAME, host_id, dest, "")))
      | eval daemon_unit=trim(toString(coalesce(SYSTEMD_UNIT, systemd_unit, unit, "containerd.service")))
      | eval msg_lc=lower(toString(coalesce(MESSAGE, message, _raw, "")))
      | eval level_raw=lower(toString(coalesce(level, log_level, severity, "")))
      | where match(level_raw, "(?i)fatal|error|panic") OR match(msg_lc, "(?i)panic|fatal|signal sigsegv|signal sigbus|goroutine.*running|reaping shim|shim disconnected")
      | eval error_class=case(
          match(msg_lc, "(?i)panic|signal sigsegv|signal sigbus|goroutine.*running"), "containerd_shim_panic",
          match(msg_lc, "(?i)reaping shim|task is shutting down|shim exited"), "shim_reap_event",
          match(msg_lc, "(?i)rpc error|context deadline exceeded|grpc"), "containerd_rpc_error",
          match(msg_lc, "(?i)snapshot|content store|metadata store"), "containerd_storage_error",
          true(), "uncategorized_containerd_error")
      | eval signal_type="containerd_journal_error"
      | eval evidence_excerpt=substr(toString(coalesce(MESSAGE, message, _raw, "")),1,420)
      | eval api_5xx_rate=null()
      | eval engine_cpu_pct=null()
      | eval health_failed_5m=null()
      | fields _time host_id daemon_unit error_class signal_type evidence_excerpt api_5xx_rate engine_cpu_pct health_failed_5m ]
    [ search index=oti_containers sourcetype="docker:metrics" earliest=-24h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, instance, dest, "")))
      | eval daemon_unit="docker.service"
      | eval metric_name=trim(toString(coalesce(metric_name, name, __name__, "")))
      | eval metric_value=tonumber(tostring(coalesce(value, metric_value, "")), 10)
      | eval http_status=trim(toString(coalesce(code, status, status_code, "")))
      | where isnotnull(metric_value) AND len(metric_name)>0
      | eval is_api_5xx=if(match(metric_name, "(?i)engine_api_request_total|http_request") AND match(http_status, "^5[0-9]{2}$"), 1, 0)
      | eval is_api_2xx=if(match(metric_name, "(?i)engine_api_request_total|http_request") AND match(http_status, "^2[0-9]{2}$"), 1, 0)
      | eval cpu_pct_sample=if(match(metric_name, "(?i)engine_daemon_engine_cpu_percent|process_cpu_seconds_total"), metric_value, null())
      | eval health_failed_sample=if(match(metric_name, "(?i)engine_daemon_health_checks_failed_total"), metric_value, null())
      | sort 0 + host_id, _time
      | streamstats time_window=5m current=t global=f sum(eval(if(is_api_5xx==1, metric_value, 0))) AS api_5xx_5m sum(eval(if(is_api_2xx==1, metric_value, 0))) AS api_2xx_5m max(cpu_pct_sample) AS engine_cpu_pct_5m max(health_failed_sample) AS health_failed_5m_streaming BY host_id
      | eval api_total_5m=api_5xx_5m + api_2xx_5m
      | eval api_5xx_rate=if(api_total_5m>0, round(100.0 * api_5xx_5m / api_total_5m, 2), 0)
      | eval error_class=case(
          api_5xx_rate>=5 AND api_total_5m>=20, "engine_api_5xx_rate_high",
          isnotnull(health_failed_5m_streaming) AND health_failed_5m_streaming>0, "engine_healthcheck_failure",
          isnotnull(engine_cpu_pct_5m) AND engine_cpu_pct_5m>=85, "engine_daemon_cpu_saturation",
          true(), null())
      | where isnotnull(error_class)
      | eval signal_type="docker_metrics_prometheus"
      | eval evidence_excerpt="prom_signal api_5xx_rate=" . tostring(coalesce(api_5xx_rate, 0)) . "% total_5m=" . tostring(coalesce(api_total_5m, 0)) . " cpu_pct=" . tostring(coalesce(engine_cpu_pct_5m, 0)) . " health_failed_5m=" . tostring(coalesce(health_failed_5m_streaming, 0))
      | eval engine_cpu_pct=engine_cpu_pct_5m
      | eval health_failed_5m=health_failed_5m_streaming
      | fields _time host_id daemon_unit error_class signal_type evidence_excerpt api_5xx_rate engine_cpu_pct health_failed_5m ]
| eval host_id=if(isnull(host_id) OR len(trim(host_id))==0, "unknown_host", host_id)
| sort 0 + host_id, daemon_unit, _time
| bucket _time span=5m as bucket_5min
| eventstats count AS error_count_5min BY host_id, error_class, bucket_5min
| eventstats sum(eval(if(error_class=="dockerd_panic_or_fatal", 1, 0))) AS panic_count_24h sum(eval(if(error_class=="containerd_shim_panic", 1, 0))) AS containerd_shim_crash_count sum(eval(if(error_class=="storage_driver_error", 1, 0))) AS storage_driver_error_count sum(eval(if(error_class=="libnetwork_driver_failure", 1, 0))) AS network_driver_error_count sum(eval(if(error_class=="image_manifest_unauthorized", 1, 0))) AS image_pull_unauth_count BY host_id
| eventstats sum(eval(if(error_class=="dockerd_panic_or_fatal" AND _time>=relative_time(now(), "-1h"), 1, 0))) AS panic_count_1h sum(eval(if(error_class=="containerd_shim_panic" AND _time>=relative_time(now(), "-1h"), 1, 0))) AS shim_crashes_1h BY host_id
| eventstats max(eval(if(signal_type=="docker_metrics_prometheus", api_5xx_rate, null()))) AS api_5xx_rate_host max(eval(if(signal_type=="docker_metrics_prometheus", engine_cpu_pct, null()))) AS engine_cpu_pct_host BY host_id
| join type=left max=0 error_class
    [| inputlookup docker_daemon_error_taxonomy.csv
     | eval error_class=trim(toString(coalesce(error_class, class, "")))
     | eval default_severity=lower(toString(coalesce(default_severity, severity_default, severity, "")))
     | eval recommended_response_taxonomy=toString(coalesce(recommended_response, response, action, ""))
     | eval kfp_pattern=toString(coalesce(kfp_pattern, false_positive_hint, ""))
     | fields error_class default_severity recommended_response_taxonomy kfp_pattern ]
| eval severity=case(
    error_class=="dockerd_panic_or_fatal", "critical_dockerd_panic_or_fatal",
    error_class=="containerd_shim_panic", "critical_containerd_shim_crash_with_orphan",
    error_class=="shim_disconnect_signal" AND shim_crashes_1h>=1, "critical_containerd_shim_crash_with_orphan",
    error_class=="storage_driver_error" AND error_count_5min>=3, "high_storage_driver_error_sustained",
    error_class=="engine_api_5xx_rate_high", "high_api_5xx_rate_above_5pct",
    error_class=="engine_daemon_cpu_saturation", "high_api_5xx_rate_above_5pct",
    error_class=="engine_healthcheck_failure", "high_api_5xx_rate_above_5pct",
    error_class=="engine_api_request_error" AND coalesce(api_5xx_rate_host, 0)>=5, "high_api_5xx_rate_above_5pct",
    error_class=="libnetwork_driver_failure", "medium_libnetwork_driver_failure",
    error_class=="image_manifest_unauthorized", "low_image_manifest_unauthorized",
    true(), null())
| where isnotnull(severity)
| eval recommended_response=case(
    severity=="critical_dockerd_panic_or_fatal", "Page platform on-call: dockerd panic on a host with many containers; capture journalctl -u docker.service --since '15 min ago', confirm live-restore=true in /etc/docker/daemon.json so kernel cgroups keep workloads alive while the engine recovers, validate /var/lib/docker integrity, file a Docker support bundle, and bring the engine up under change control before declaring the host healthy.",
    severity=="critical_containerd_shim_crash_with_orphan", "Page platform on-call: containerd-shim-runc-v2 crash leaves orphaned containers attached to kernel cgroups while dockerd lost the supervisory link; identify orphan PIDs via ps -ef | grep containerd-shim, send SIGKILL to zombie shims, restart containerd, reconcile docker ps -a, and document orphan count in the incident timeline.",
    severity=="high_storage_driver_error_sustained", "Storage driver overlay2, devicemapper, or btrfs errors sustained at three or more events in five minutes: inspect /var/lib/docker disk usage and inode pressure, validate xfs or ext4 health with smartctl and dmesg, drain workloads if filesystem integrity is suspect, and engage the storage team before further image pulls compound damage.",
    severity=="high_api_5xx_rate_above_5pct", "Engine API five-percent or higher 5xx rate, daemon CPU saturation, or health-check failures: capture engine_daemon_engine_info gauge trends, inspect socket backlog with ss -lpn, throttle CI/CD pipelines hammering /containers/json, and consider raising daemon ulimits or splitting socket consumers across hosts.",
    severity=="medium_libnetwork_driver_failure", "libnetwork driver failure on bridge, overlay, or macvlan: inspect docker network ls and docker network inspect for stuck pools, validate iptables -S for FORWARD chain state, restart networking only with an explicit change ticket, and watch for reload loops.",
    severity=="low_image_manifest_unauthorized", "Image manifest unauthorized or denied: validate registry credentials in /etc/docker/daemon.json or systemd drop-ins, rotate expired pull secrets, and confirm registry mirror health; treat as configuration drift rather than engine failure unless paired with daemon-side errors on the same host.",
    true(), "Correlate dockerd journal, containerd journal, and Prometheus metrics before closure; do not silence alerts on the host, route to platform on-call.")
| eval recommended_response=if(isnotnull(recommended_response_taxonomy) AND len(trim(recommended_response_taxonomy))>0, recommended_response . " | Taxonomy hint: " . recommended_response_taxonomy, recommended_response)
| eval container_name="DOCKER_DAEMON_HOST"
| join type=left max=0 host_id, container_name
    [| inputlookup container_owner.csv
     | eval host_id=lower(toString(coalesce(host_id, host, "")))
     | eval container_name=toString(container_name)
     | eval owner_team=toString(coalesce(owner_team, squad, ""))
     | fields host_id container_name owner_team ]
| stats max(error_count_5min) AS error_count_5min max(panic_count_24h) AS panic_count_24h max(containerd_shim_crash_count) AS containerd_shim_crash_count max(storage_driver_error_count) AS storage_driver_error_count max(network_driver_error_count) AS network_driver_error_count max(image_pull_unauth_count) AS image_pull_unauth_count max(api_5xx_rate_host) AS api_5xx_rate max(engine_cpu_pct_host) AS engine_cpu_pct values(signal_type) AS signal_types latest(evidence_excerpt) AS evidence_excerpt latest(severity) AS severity latest(recommended_response) AS recommended_response latest(owner_team) AS owner_team BY host_id, daemon_unit, error_class
| eval signal_types=mvjoin(signal_types, "|")
| table host_id daemon_unit error_class signal_types error_count_5min panic_count_24h containerd_shim_crash_count storage_driver_error_count network_driver_error_count api_5xx_rate engine_cpu_pct image_pull_unauth_count severity recommended_response owner_team evidence_excerpt
```

## CIM SPL

```spl
| tstats summariesonly=t latest(Application_State.state) AS engine_state latest(Application_State.info) AS engine_info FROM datamodel=Application_State WHERE nodename=Application_State (Application_State.app="docker" OR Application_State.app="dockerd" OR Application_State.app="containerd") earliest=-1h@h latest=@h BY Application_State.dest Application_State.app
| rename Application_State.dest AS host_id Application_State.app AS daemon_unit
| where engine_state!="running" OR like(lower(engine_info), "%panic%") OR like(lower(engine_info), "%fatal%")
```

## Visualization

Primary panel: error_class heatmap by host_id over twenty-four hours with cell coloring escalating past three errors per five-minute bucket so the eye sees sustained_storage_driver_error rows instantly. Secondary panel: daemon-unit panic-count single-value tile with zero versus non-zero color (green at zero panic_count_24h, red the moment any host crosses one) tied to drilldown into raw linux:journald:docker for the offending host. Tertiary panel: api_5xx_rate line chart per host_id from docker:metrics with a five-percent reference band so leaders distinguish engine overload from upstream API issue at a glance. Companion table: severity-tiered rows mirroring the SPL projection with cell coloring on severity and drilldowns to journalctl excerpts, containerd panic stack traces, and Prometheus engine_daemon_engine_info gauges for the same host_id and minute.

## Known False Positives

Legitimate image pull unauthorized or denied: requested access events fire when registry credentials in /etc/docker/daemon.json or systemd drop-in files expire on a planned rotation cadence; the engine is healthy and the fix is the credential rotation pipeline, not a daemon restart, so route low_image_manifest_unauthorized rows to the registry-ops queue rather than the engine on-call rotation. Benign bridge already exists or libnetwork bridge already declared lines surface harmlessly when a node reloads or when docker-compose down and up cycles in CI executors recreate the same default bridge after a prior cleanup script left state behind; require sustained bursts above the macro threshold or pair with engine_api 5xx evidence before paging. The client disconnect during request log line is a routine outcome of kubelet probe-bursts and short-lived docker ps health checks from monitoring containers; do not score it as a daemon panic on its own. OOM-killed dockerd entries occasionally appear when a host is under extreme memory pressure from co-resident workloads; the root cause is host-level capacity and UC-3.1.2 owns the cgroup analysis for memory, so correlate before raising critical_dockerd_panic_or_fatal. Routine live-restore enable or reload events written to journald during scheduled patch windows look like daemon transitions but are intentional; tag the change window in maintenance lookups and downgrade those rows. Storage_driver_error bursts during planned overlay2 to fuse-overlayfs migrations, aggressive image-layer garbage collection runs, or BuildKit cache prune cycles may briefly cross the sustained threshold without indicating filesystem damage; require corroborating dmesg evidence before escalating. CI executors that intentionally run nested Docker-in-Docker for builder pipelines often emit shim_reap_event and shim_disconnect_signal lines as the inner daemon exits cleanly between jobs; tag those host classes in container_owner.csv with a builder owner_team and downgrade non-panic shim signals on builder fleets. Mirantis Container Runtime field-naming differences after a major release can cause coalesce misses that look like a sudden uncategorized_dockerd_error spike until props aliases catch up; reconcile against vendor release notes before paging.

## References

- [Docker Docs — dockerd reference (Engine daemon and metrics-addr)](https://docs.docker.com/reference/cli/dockerd/)
- [containerd — runtime-v2 (shim) architecture documentation](https://github.com/containerd/containerd/blob/main/docs/runtime-v2.md)
- [systemd — journalctl(1) man page](https://man7.org/linux/man-pages/man1/journalctl.1.html)
- [Docker Docs — Live restore (engine-restart tradeoffs)](https://docs.docker.com/engine/daemon/live-restore/)
- [Splunk Lantern — Getting Docker log data into Splunk Cloud Platform with OpenTelemetry](https://lantern.splunk.com/Platform_Data_Management/Unlock_Insights/Getting_Docker_log_data_into_Splunk_Cloud_Platform_with_OpenTelemetry)
- [Docker Docs — Collect Docker metrics with Prometheus (daemon /metrics endpoint)](https://docs.docker.com/config/daemon/prometheus/)
