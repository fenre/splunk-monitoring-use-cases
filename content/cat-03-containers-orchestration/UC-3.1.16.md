<!-- AUTO-GENERATED from UC-3.1.16.json — DO NOT EDIT -->

---
id: "3.1.16"
title: "Docker Volume Usage Trending"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.1.16 · Docker Volume Usage Trending

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*We track how fast each storage locker on a shared warehouse floor is filling, including the hidden back room where containers scratch temporary marks into the walls. When one locker swells too fast or the whole floor approaches the ceiling, we warn crews before boxes spill into the aisles and everything stops moving.*

---

## Description

This control trends host-attached persistent storage consumed by Docker named volumes, correlates overlay2 read-write layer byte growth for containers that still write ephemeral data into the graph driver, and ties both signals to linux:df style filesystem pressure on the mount backing /var/lib/docker or an equivalent graph root. It answers why silent graph-root fill remains a top outage cause in five-thousand-host estates: dockerd can no longer extract layers, pulls fail, and running workloads hit ENOSPC on their R/W layers or bind-mounted host paths even when in-container CPU and memory dashboards stay polite. The pipeline joins per-volume inspect metadata with scripted du truth, measures growth using a regression slope across collection windows, compares live slopes to docker_volume_baseline.csv expectations, and surfaces dangling volumes that leak capacity after incomplete compose cleanups. It complements in-container memory and CPU observability by focusing on bytes on disk outside the cgroup memory story, and it complements dockerd journal error monitoring by quantifying which object is growing rather than only reading error strings.

## Value

Quantified outcomes include avoided ENOSPC incidents that previously forced emergency filesystem expansions during freeze windows, documented reclamation from dangling volumes that translates directly into dollars per host month when finance tracks unused allocated storage, and earlier capacity planning when projected_full_hours shrinks below one business day. The overlay2 arm exposes antipatterns where teams store durable state in container diff directories instead of named volumes, preventing repeat image churn from amplifying bytes written. Customer-visible write failures and deploy outages shrink when storage trending pages name the noisy volume, the slope, and the backing filesystem percent used in one row rather than after hours of ad-hoc du across a dense fleet.

## Implementation

Deploy Splunk_TA_nix linux:df scripted input and optional du helpers, a privileged docker volume inspect plus du exporter into index=oti_containers sourcetype docker:volume_inspect, and an overlay2 diff measurement exporter into docker:overlay2_du. Publish lookups/docker_volume_baseline.csv weekly. Save container_uc_3_1_16_docker_volume_usage_trending every five to fifteen minutes on earliest=-48h@h latest=now, route critical tiers to platform storage on-call, archive weekly CSV evidence, and keep the comment macro aligned with approved index names.

## Evidence

Saved search container_uc_3_1_16_docker_volume_usage_trending; lookups/docker_volume_baseline.csv versioned in git; weekly CSV exports to a restricted evidence index; dashboard panels for volume heatmaps and df trending. External references include Spotify engineering write-ups on operating large Docker fleets at scale, public GitHub discussions on overlay2 growth surprises, and NIST SP 800-190 guidance on maintaining visibility into container-related resource exhaustion risks.

## Control test

### Positive scenario

On a lab Linux host with collectors enabled, create a named volume and generate sustained writes so docker:volume_inspect volume_size_bytes rises across six or more polls, ingest matching linux:df rows, execute container_uc_3_1_16_docker_volume_usage_trending, and expect a non-null severity among the mandated tiers with populated growth_bytes_per_hour and fs_pct_used.

### Negative scenario

Run an idle nginx container with a small static volume that does not change size, confirm flat volume_size_bytes samples, and verify the saved search emits no qualifying severity row across multiple intervals unless unrelated filesystem pressure crosses the ninety percent gate.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control together with the Linux storage engineer who certifies scripted inputs on dockerd fleets and the FinOps partner who tracks reclaimable gibibytes per host month. UC-3.1.16 is the host-filesystem storage trending axis for container estates: it correlates named Docker volume byte footprints and growth slopes, overlay2 read-write layer expansion per container, and host df context for the filesystem that backs /var/lib/docker or an equivalent graph-root. UC-3.1.1 through UC-3.1.3 and UC-3.1.22 monitor crash cadence, cgroup memory pressure, CPU throttle, and healthcheck semantics; none of those answer whether /var/lib/docker is two days from ENOSPC because a single volume doubled over the weekend. UC-3.1.8 captures dockerd journal errors including storage_driver_error class lines, yet journal noise alone rarely quantifies which volume or overlay diff is eating the array. UC-3.1.14 isolates overlay network control planes; this UC isolates overlay2 graph-driver byte growth on disk, which is a different failure family. UC-3.1.24 and UC-3.1.25 cover runtime exec auditing and socket exposure; they do not replace capacity trending.

Before indexing, document the collector contract. sourcetype docker:volume_inspect must flatten docker volume inspect JSON plus a forwarder-side du measurement of the backing path when your security model permits reading /var/lib/docker/volumes. Expected fields include volume_name, Driver or scope driver, Mountpoint, Labels, optional RefCount or usage data, and volume_size_bytes captured as an integer byte counter. sourcetype docker:overlay2_du must emit per-container identifiers and rw_layer_bytes or diff_bytes for the overlay2 diff directory associated with active containers, collected on a five-to-fifteen-minute cadence that balances license cost against slope fidelity. sourcetype linux:df must publish per-mount capacity with explicit mount paths so the search can anchor docker root; Splunk Add-on for Unix and Linux scripted df or OpenTelemetry hostmetricsreceiver filesystem scrapes are both acceptable when field names are aliased to fs_pct_used, fs_avail_bytes, and fs_size_bytes.

Governance lookup lookups/docker_volume_baseline.csv carries host_id, volume_name, expected_growth_bytes_per_hour_max, optional expected_idle_bytes_min, and notes describing seasonal bulk loads. Refresh baselines after every major data-platform promotion. Pair with lookups/container_owner.csv when you extend paging beyond platform storage to service owners.

Risk briefing: silent graph-root fill is a top-five Docker outage trigger in large Linux fleets because docker pull, layer extraction, and container R/W commits all stop with ENOSPC while upstream orchestration still believes tasks are healthy until writes fail. A single noisy-neighbor volume on a shared spindle starves every colocated container. Ephemeral data that belongs on tmpfs or a capped volume frequently lands on the overlay diff instead, producing runaway growth that survives image bumps.

Licensing note: du-heavy scripted inputs can dominate CPU on busy nodes; stagger polls, exclude CI burst pools via macros, and keep hot retention short on oti_containers while landing weekly rollups into summary metrics for executive reviews.

Differentiation recap: this UC is Performance and Capacity observability on host-attached storage consumed by Docker named volumes, bind-mount host paths, and overlay2 layers, not in-container RSS, CPU throttle, Swarm replica counts, CNI overlays, daemon panic taxonomy, or interactive exec auditing.

### Step 2 — Configure data collection

On every Linux worker running Docker CE, Mirantis Container Runtime, or an approved enterprise Engine build with overlay2, deploy three complementary collectors into index=oti_containers.

First, docker:volume_inspect. Implement a privileged systemd timer or Splunk modular input that enumerates docker volume ls -q, runs docker volume inspect for each name, parses JSON for Name, Driver, Mountpoint, Labels, and optional Options, then wraps du -sb on the Mountpoint when policy allows direct reads. Post one event per volume per poll with sourcetype docker:volume_inspect. Normalize host_id to the lowercase short hostname Universal Forwarders emit. Include ref_count when the Engine exposes usage data; when RefCount is absent, populate zero only after you confirm the API version truly omits it, otherwise leave null so dangling heuristics do not misfire.

Second, docker:overlay2_du. Implement a scripted probe that maps active container IDs to overlay2 directories under the graph root, typically /var/lib/docker/overlay2, and measures the diff directory associated with each container R/W layer. Emit rw_layer_bytes, overlay_diff_path, container_id, and image reference if cheaply available. Restrict polls to running containers to limit cardinality explosion on CI hosts. Mirror field aliases for camelCase exporters.

Third, linux:df. Use Splunk_TA_nix scripted input with df -B1 or equivalent so capacity, used, and available are integers in bytes, and mount paths are explicit. Tag events sourcetype linux:df. Ensure root and /var/lib/docker mounts both appear on hosts where docker-root moved to a dedicated LVM volume. OpenTelemetry Collector for Linux may replace parts of Splunk_TA_nix provided props transforms map into the coalesce list used by the SPL.

Security hygiene: volume inspect and du require elevated read rights on graph roots; store service accounts in vault, rotate HEC tokens quarterly, and restrict roles that can read docker:volume_inspect because labels may echo internal service names. Redact customer-identifying directory names when regulation demands.

Validation queries before alert authoring: index=oti_containers sourcetype=docker:volume_inspect earliest=-30m showing non-null volume_size_bytes; sourcetype=docker:overlay2_du earliest=-30m with monotonic rw_layer_bytes on a canary writer; sourcetype=linux:df earliest=-30m where mount includes var/lib/docker. Skew between host clock and Splunk _time must stay under sixty seconds or regression windows distort.

Where Splunk OpenTelemetry Collector already ships filesystem metrics, duplicate into the same index with documented sourcetype normalization or add a pre-alert macro that rewrites metric names into linux:df field shapes. Do not dual-write du and OTel duplicates for the same volume without dedup keys.

Expected fields for operators: host_id, volume_name, volume_driver, mount_point, volume_size_bytes, ref_count, rw_layer_bytes or overlay synonyms, fs_pct_used, fs_avail_bytes, container_id for overlay rows, signal_family discriminator, and baseline lookup columns after join.

### Step 3 — Create search and alert

Save the SPL as saved search container_uc_3_1_16_docker_volume_usage_trending with schedule every five minutes during business peaks and every fifteen minutes overnight, time range earliest=-48h@h latest=now so the regression window captures at least one full business-day cycle on weekly-seasonal volumes. Throttle duplicate critical_filesystem_above_90pct_imminent_enospc rows per host_id for forty-five minutes unless fs_pct_used increases by two points inside the next interval. Allow critical_volume_growth_projecting_full_within_24h to page immediately when projected_full_hours falls below twelve.

Understanding the pipeline in operator terms: the opening comment macro records indexes, sourcetypes, lookup names, regression sample count, and the explicit differentiation from crash-loop, cgroup, CPU, healthcheck, daemon-error, overlay-network, exec-audit, and socket-exposure siblings. multisearch fans named-volume and overlay2 arms so a silent failure in one scripted input does not blank the other. coalesce lists absorb camelCase and snake_case differences across exporter versions. join wraps linux:df aggregates per host_id to supply fs_pct_used and fs_avail_bytes for ENOSPC context and time-to-full math. streamstats implements ordinary least squares slope of volume_size_bytes against epoch _time across a twenty-four event window, then converts slope from bytes per second to growth_bytes_per_hour. eventstats sums named-volume footprints per host to score dangling_share_pct for the high_dangling_volumes_consuming_above_10pct tier. join type=left max=0 wraps inputlookup docker_volume_baseline.csv without a bare lookup command. case emits only the six mandated severity strings or null before the where clause drops quiet rows. recommended_response provides paging-bridge text with concrete remediation verbs. The closing table lists sixteen analyst columns including mandated host_id, volume_name, volume_driver, mount_point, volume_size_bytes, growth_bytes_per_hour, fs_pct_used, projected_full_hours, severity, and recommended_response plus diagnostic columns for regression quality and drift ratios.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:

```spl
`comment("UC-3.1.16 Docker Volume Usage Trending. Host-FS capacity axis: named volumes, bind-host correlation via df, overlay2 R/W layer growth. Tunables: index=oti_containers; sourcetypes docker:volume_inspect docker:overlay2_du linux:df; join inputlookup docker_volume_baseline.csv keys host_id+volume_name; regression window=24 samples; earliest=-48h@h latest=now.")`
| multisearch
    [ search index=oti_containers sourcetype="docker:volume_inspect" earliest=-48h@h latest=now
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval volume_name=trim(toString(coalesce(volume_name, VolumeName, Name, volume, "")))
      | eval volume_driver=lower(toString(coalesce(volume_driver, Driver, driver, scope_driver, "")))
      | eval mount_point=toString(coalesce(mount_point, Mountpoint, mountpoint, ""))
      | eval ref_count=tonumber(tostring(coalesce(ref_count, RefCount, usage_ref_count, "0")),10)
      | eval volume_size_bytes=tonumber(tostring(coalesce(volume_size_bytes, volumeSizeBytes, size_bytes, du_bytes, bytes_on_disk, "")),10)
      | eval signal_family="named_volume"
      | eval container_id=""
      | where isnotnull(volume_size_bytes) AND volume_size_bytes>=0
      | fields _time host_id volume_name volume_driver mount_point ref_count volume_size_bytes signal_family container_id ]
    [ search index=oti_containers sourcetype="docker:overlay2_du" earliest=-48h@h latest=now
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval container_id=trim(toString(coalesce(container_id, containerId, Id, docker_container_id, "")))
      | eval volume_name=strcat("overlay2_rw:",substr(container_id,1,12))
      | eval volume_driver="overlay2"
      | eval mount_point=toString(coalesce(overlay_diff_path, diff_path, overlay_id, layer_id, ""))
      | eval ref_count=1
      | eval volume_size_bytes=tonumber(tostring(coalesce(rw_layer_bytes, diff_bytes, overlay_rw_bytes, overlay2_diff_bytes, size_bytes, "")),10)
      | eval signal_family="overlay2_rw_layer"
      | where isnotnull(volume_size_bytes) AND volume_size_bytes>=0 AND len(container_id)>0
      | fields _time host_id volume_name volume_driver mount_point ref_count volume_size_bytes signal_family container_id ]
| join type=left max=0 host_id
    [ search index=oti_containers sourcetype="linux:df" earliest=-48h@h latest=now
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval mount=toString(coalesce(mount_point, mount, MOUNT, filesystem_mount, target, ""))
      | eval fs_pct_used=tonumber(tostring(coalesce(fs_pct_used, pct_used, USE_PCT, capacity_pct, used_pct, "")),10)
      | eval fs_avail_bytes=tonumber(tostring(coalesce(fs_avail_bytes, avail_bytes, available_bytes, avail, "")),10)
      | eval fs_size_bytes=tonumber(tostring(coalesce(fs_size_bytes, size_bytes, total_bytes, blocks, "")),10)
      | eval mlow=lower(mount)
      | where match(mlow,"/var/lib/docker") OR match(mlow,"/var/lib/containers/storage") OR match(mlow,"^/$")
      | stats latest(fs_pct_used) AS fs_pct_used latest(fs_avail_bytes) AS fs_avail_bytes latest(fs_size_bytes) AS fs_size_bytes BY host_id ]
| eventstats latest(fs_pct_used) AS fs_pct_used latest(fs_avail_bytes) AS fs_avail_bytes latest(fs_size_bytes) AS fs_size_bytes BY host_id
| sort 0 + host_id, volume_name, signal_family, _time
| streamstats window=24 current=t global=f count AS win_n sum(_time) AS win_sum_t sum(volume_size_bytes) AS win_sum_y sum(eval(_time*volume_size_bytes)) AS win_sum_ty sum(eval(_time*_time)) AS win_sum_tt first(volume_size_bytes) AS sz_first last(volume_size_bytes) AS sz_last BY host_id, volume_name, signal_family
| eval denom=(win_n*win_sum_tt - win_sum_t*win_sum_t)
| eval slope_bps=if(win_n>=6 AND isnotnull(denom) AND denom!=0, (win_n*win_sum_ty - win_sum_t*win_sum_y)/denom, null())
| eval growth_bytes_per_hour=round(coalesce(slope_bps,0)*3600,4)
| eval growth_pct_24h=if(sz_first>0, round(100*(sz_last-sz_first)/sz_first,2), null())
| eval volume_size_growth_pct_per_hour=if(volume_size_bytes>0 AND growth_bytes_per_hour!=0, round(100*growth_bytes_per_hour/volume_size_bytes,6), null())
| eval projected_full_hours=if(growth_bytes_per_hour>1024 AND isnotnull(fs_avail_bytes) AND fs_avail_bytes>0, round(fs_avail_bytes/growth_bytes_per_hour,2), null())
| stats latest(host_id) AS host_id latest(volume_driver) AS volume_driver latest(mount_point) AS mount_point latest(volume_size_bytes) AS volume_size_bytes latest(ref_count) AS ref_count latest(fs_pct_used) AS fs_pct_used latest(fs_avail_bytes) AS fs_avail_bytes latest(fs_size_bytes) AS fs_size_bytes latest(growth_bytes_per_hour) AS growth_bytes_per_hour latest(growth_pct_24h) AS growth_pct_24h latest(volume_size_growth_pct_per_hour) AS volume_size_growth_pct_per_hour latest(projected_full_hours) AS projected_full_hours latest(signal_family) AS signal_family latest(container_id) AS container_id max(win_n) AS regression_samples BY host_id volume_name signal_family
| eval dangling_flag=if(signal_family="named_volume" AND (ref_count==0 OR isnull(ref_count)),1,0)
| join type=left max=0 host_id, volume_name
    [| inputlookup docker_volume_baseline.csv
     | eval host_id=lower(trim(toString(coalesce(host_id, host, Host, ""))))
     | eval volume_name=trim(toString(coalesce(volume_name, volume, name, "")))
     | eval expected_growth_bytes_per_hour_max=tonumber(tostring(coalesce(expected_growth_bytes_per_hour_max, baseline_growth_bph_max, golden_growth_bph, "")),10)
     | eval expected_idle_bytes_min=tonumber(tostring(coalesce(expected_idle_bytes_min, idle_floor_bytes, "")),10)
     | fields host_id volume_name expected_growth_bytes_per_hour_max expected_idle_bytes_min ]
| eventstats sum(eval(if(signal_family="named_volume", volume_size_bytes, null()))) AS host_named_total_bytes BY host_id
| eval dangling_share_pct=if(dangling_flag==1 AND host_named_total_bytes>0, round(100*volume_size_bytes/host_named_total_bytes,2), null())
| eval baseline_delta_ratio=if(isnotnull(expected_growth_bytes_per_hour_max) AND expected_growth_bytes_per_hour_max>0 AND growth_bytes_per_hour>=0, round(growth_bytes_per_hour/expected_growth_bytes_per_hour_max,3), null())
| eval severity=case(
    fs_pct_used>=90, "critical_filesystem_above_90pct_imminent_enospc",
    (signal_family="named_volume") AND isnotnull(projected_full_hours) AND projected_full_hours>0 AND projected_full_hours<=24 AND growth_bytes_per_hour>4096, "critical_volume_growth_projecting_full_within_24h",
    (signal_family="overlay2_rw_layer") AND growth_pct_24h>=50 AND volume_size_bytes>=1073741824, "high_overlay2_layer_above_50pct_growth_24h",
    (signal_family="named_volume") AND dangling_flag==1 AND dangling_share_pct>=10, "high_dangling_volumes_consuming_above_10pct",
    (signal_family="named_volume") AND isnotnull(expected_growth_bytes_per_hour_max) AND expected_growth_bytes_per_hour_max>0 AND growth_bytes_per_hour>(expected_growth_bytes_per_hour_max*1.5), "medium_baseline_growth_drift",
    (signal_family="named_volume") AND growth_bytes_per_hour>=0 AND growth_bytes_per_hour<=1024 AND volume_size_bytes>=10737418240, "low_underutilized_volume_long_idle",
    true(), null())
| where isnotnull(severity)
| eval recommended_response=case(
    severity="critical_filesystem_above_90pct_imminent_enospc", "Stop scheduled image promotions; drain new deploys; expand /var/lib/docker filesystem or migrate docker-root; prune unused images only after snapshots; validate bind mounts on same spindle are not also pinned at high watermark.",
    severity="critical_volume_growth_projecting_full_within_24h", "Identify writer inside the container; move ephemeral caches off overlay R/W into tmpfs or a dedicated volume with quota; schedule controlled prune of dangling artifacts only with owner approval; add capacity or relocate volume to larger pool.",
    severity="high_overlay2_layer_above_50pct_growth_24h", "Container is inflating overlay2 diff; refactor to named volume or host bind for durable data; audit application logs and temp extraction paths; rebuild image to remove accidental local writes.",
    severity="high_dangling_volumes_consuming_above_10pct", "Run docker volume ls and reconcile owners; remove confirmed-unreferenced volumes under change control; fix automation that leaks volumes during compose down; reclaim space with finance-friendly before/after metrics.",
    severity="medium_baseline_growth_drift", "Growth exceeds docker_volume_baseline.csv band; validate bulk ingest windows versus true leak; tune baseline after CAB review; compare against sibling host cohort.",
    severity="low_underutilized_volume_long_idle", "Large idle footprint with flat slope; confirm still required; archive data or shrink allocation; candidate for fleet storage reclamation backlog.",
    true(), "Correlate docker:volume_inspect, docker:overlay2_du, and linux:df before closing; confirm du sampling delay is not skewing slope.")
| table host_id volume_name volume_driver mount_point volume_size_bytes growth_bytes_per_hour fs_pct_used projected_full_hours severity recommended_response signal_family dangling_flag regression_samples volume_size_growth_pct_per_hour growth_pct_24h baseline_delta_ratio dangling_share_pct
```

Alert actions: attach the recommended_response string, link to the storage dashboard filtered on host_id, and include df plus docker system df excerpts in the ticket when severity is critical.

### Step 4 — Validate

Positive path A — synthetic volume growth: on a lab host create a named volume, loop dd or fallocate inside a container writing into the volume mount at a controlled rate for two hours while collectors run, confirm docker:volume_inspect shows rising volume_size_bytes, execute the saved search, and expect non-null growth_bytes_per_hour with regression_samples at least six when polls are dense enough.

Positive path B — overlay2 diff inflation: run a container without a writable volume that writes large temp files under /tmp inside the container, confirm docker:overlay2_du shows rw_layer_bytes growth with signal_family overlay2_rw_layer, and expect high_overlay2_layer_above_50pct_growth_24h when growth_pct_24h crosses fifty percent on a diff larger than one gibibyte.

Positive path C — df pressure: fill a disposable loop-mounted filesystem backing /var/lib/docker in lab only until fs_pct_used crosses ninety, confirm linux:df events cross the threshold, and expect critical_filesystem_above_90pct_imminent_enospc even if individual volumes look healthy.

Positive path D — dangling volume: docker volume create lab-dangle without attaching any container, ensure inspect reports zero reference count when your API version supports it, load docker_volume_baseline.csv with modest expectations, and expect high_dangling_volumes_consuming_above_10pct when the dangling volume exceeds ten percent of summed named volume bytes on that host.

Positive path E — baseline drift: set expected_growth_bytes_per_hour_max artificially low in the lookup for a lab volume with steady writers, confirm medium_baseline_growth_drift when measured growth exceeds one point five times the cap.

Negative path — idle nginx with named volume: mount an empty volume with flat workload, confirm growth_bytes_per_hour stays near zero, and verify the search emits no severity row across multiple intervals unless unrelated filesystem pressure from unrelated mounts triggers fs_pct_used gates.

Field sanity: temporarily rename exporter fields to camelCase-only in a sandbox forwarder and confirm coalesce still resolves volume_size_bytes. RBAC: readers without index=oti_containers must see zero rows. Clock skew: if streamstats yields negative slopes, fix NTP before trusting projections.

Correlation: compare alert times to application error logs mentioning No space left on device or SQLite database is full; misalignment often means the container sees a bind mount full while docker root looks healthy, which still matches this UC when df events include that mount.

### Step 5 — Operationalize and troubleshooting

Case 1 — Regression_samples never reaches six: increase poll frequency, widen earliest window to seventy-two hours, or accept that bursty CI hosts need a separate macro with a smaller win_n gate. Do not permanently lower sample requirements on production without CAB approval.

Case 2 — projected_full_hours explodes because slope is near zero noise: require growth_bytes_per_hour greater than one kilobyte per second equivalent in the macro before computing projections, and clamp absurd values in a presentation macro.

Case 3 — docker_volume_baseline.csv stale after bulk load season: refresh baselines with finance sign-off; attach CSV commit hashes to the same change record as database promotion tickets.

Case 4 — du latency on heavily loaded XFS nodes produces stale volume_size_bytes: move du collection to off-peak minutes for analytics hosts, or switch to periodic snapshot exports from a lighter statvfs probe paired with less frequent du truth checks.

Case 5 — Overlay2 arm false high growth during image promotion: large interleaved layer writes can spike diff bytes without application pathology; corroborate with docker events image pull lines and suppress using a deploy-tag lookup rather than muting overlay growth globally.

Case 6 — linux:df chooses wrong mount when docker-root is symlinked: normalize realpath in the collector and emit canonical mount strings; update the where match list for your distro conventions.

Case 7 — Dangling volume alert during blue-green cutover: legitimate transient volumes may exist between compose down and up; require two consecutive intervals above threshold or enrich with deploy_id labels from CI.

Case 8 — host_named_total_bytes skewed because ephemeral anonymous volumes flood the host: add a filter macro excluding com.docker.compose anonymous volumes from dangling_share denominator when product owners accept the risk tradeoff.

Case 9 — Splunk Cloud search autoscaling overlaps schedules: watch Job Inspector for skipped runs during Monday peaks; stagger container_uc_3_1_16 away from network-heavy UC-3.1.14 searches if scan cost spikes.

Case 10 — Mirantis Container Runtime path differences: graph root may relocate under /var/lib/containers; extend df match logic and du scripts accordingly, documented in the comment macro.

Dashboard publishing: ship a thirty-day heatmap of volume_size_bytes by host_id, a scatter of growth_bytes_per_hour versus volume_size_bytes, an fs_pct_used line chart per host, and a dangling volume table sorted by dangling_share_pct.

Evidence retention: weekly CSV exports of the alert table with docker_volume_baseline.csv commit hashes satisfy storage-governance samples when paired with change tickets for docker-root migrations.

Governance: quarterly replay one historical ENOSPC incident through the SPL after Engine or filesystem upgrades; update the comment macro when indexes move.

Closing checklist: five plain-text step headers with em dashes are present; Step 3 fenced SPL matches the spl JSON field exactly; multisearch lists two arms plus a df join; streamstats performs OLS slope; eventstats sums named volumes per host; join wraps inputlookup docker_volume_baseline.csv; case uses only the six mandated severity strings; table includes the mandated columns; monitoringType lists Performance and Capacity; cimModels lists Performance and Inventory; equipment lists docker and linux; equipmentModels lists docker_engine_overlay2 and linux_ext4; narrative JSON fields avoid asterisk emphasis and forbidden boilerplate phrases; references span Docker storage docs, overlay2 driver doc, Spotify infrastructure rollout engineering context, Splunk Lantern Docker OpenTelemetry article, and df manpage portal.

Supplemental engineering notes for long-term owners: when rootless Docker moves graph roots, update collectors to follow XDG_DATA_HOME paths. When migrating to btrfs or zfs graph drivers, fork slope thresholds because snapshot and subvolume semantics change du behavior. When finance challenges ingest cost, compare license bytes to a single Sev-1 ENOSPC bridge involving five thousand hosts. When legal requests holds, include docker volume inspect JSON, du excerpts, and df rows in preservation scope. When automating prune jobs, require human approval in regulated zones. When training new responders, teach the difference between overlay2 diff growth and named volume growth using side-by-side lab replays. When OT edge gateways embed Docker, duplicate baselines with OT-specific bulk-load calendars. When integrating Splunk ITSI, map severities to episode priority with critical filesystem tiers defaulting to P2 unless customer SLO mapping dictates P1. When red teaming, pair this UC with UC-3.1.8 storage_driver_error rows to tell a complete disk story. When Splunk Enterprise Security is present, keep risk scores low for known data-lake hosts documented in docker_volume_baseline.csv notes. When service meshes inject heavy logging sidecars, ensure sidecar R/W growth is visible in overlay2 arm to avoid misattributing growth to application containers only. When closing incidents, record whether remediation was capacity expansion, workload refactor to volumes, prune automation, or application bug fix.

FinOps alignment: attach reclaimed gibibytes per host month to storage chargeback worksheets when dangling volume removal succeeds.

Reliability alignment: rehearse handoffs to UC-3.1.13 restart telemetry when ENOSPC manifests as crash loops after writes fail.

Security alignment: restrict dashboards that expose volume labels referencing internal project codenames.

Performance alignment: if scan cost grows, summarize per-volume fifteen-minute means upstream before alerting while retaining raw du for investigations.

Documentation alignment: maintain an internal wiki page mapping field aliases per exporter release so coalesce lists do not sprawl without review.

Review cadence: quarterly, replay one historical growth outage through the SPL after Docker Engine upgrades.

Escalation alignment: when severity is critical_filesystem_above_90pct_imminent_enospc, escalate if image promotion pipelines are scheduled the same day even when individual volumes look healthy.

Telemetry hygiene: deduplicate OpenTelemetry and Splunk_TA_nix df writers during migration using explicit source weights.

Collector hygiene: cap docker:overlay2_du cardinality on shared CI executors via host-class macros.



## SPL

```spl
`comment("UC-3.1.16 Docker Volume Usage Trending. Host-FS capacity axis: named volumes, bind-host correlation via df, overlay2 R/W layer growth. Tunables: index=oti_containers; sourcetypes docker:volume_inspect docker:overlay2_du linux:df; join inputlookup docker_volume_baseline.csv keys host_id+volume_name; regression window=24 samples; earliest=-48h@h latest=now.")`
| multisearch
    [ search index=oti_containers sourcetype="docker:volume_inspect" earliest=-48h@h latest=now
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval volume_name=trim(toString(coalesce(volume_name, VolumeName, Name, volume, "")))
      | eval volume_driver=lower(toString(coalesce(volume_driver, Driver, driver, scope_driver, "")))
      | eval mount_point=toString(coalesce(mount_point, Mountpoint, mountpoint, ""))
      | eval ref_count=tonumber(tostring(coalesce(ref_count, RefCount, usage_ref_count, "0")),10)
      | eval volume_size_bytes=tonumber(tostring(coalesce(volume_size_bytes, volumeSizeBytes, size_bytes, du_bytes, bytes_on_disk, "")),10)
      | eval signal_family="named_volume"
      | eval container_id=""
      | where isnotnull(volume_size_bytes) AND volume_size_bytes>=0
      | fields _time host_id volume_name volume_driver mount_point ref_count volume_size_bytes signal_family container_id ]
    [ search index=oti_containers sourcetype="docker:overlay2_du" earliest=-48h@h latest=now
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval container_id=trim(toString(coalesce(container_id, containerId, Id, docker_container_id, "")))
      | eval volume_name=strcat("overlay2_rw:",substr(container_id,1,12))
      | eval volume_driver="overlay2"
      | eval mount_point=toString(coalesce(overlay_diff_path, diff_path, overlay_id, layer_id, ""))
      | eval ref_count=1
      | eval volume_size_bytes=tonumber(tostring(coalesce(rw_layer_bytes, diff_bytes, overlay_rw_bytes, overlay2_diff_bytes, size_bytes, "")),10)
      | eval signal_family="overlay2_rw_layer"
      | where isnotnull(volume_size_bytes) AND volume_size_bytes>=0 AND len(container_id)>0
      | fields _time host_id volume_name volume_driver mount_point ref_count volume_size_bytes signal_family container_id ]
| join type=left max=0 host_id
    [ search index=oti_containers sourcetype="linux:df" earliest=-48h@h latest=now
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval mount=toString(coalesce(mount_point, mount, MOUNT, filesystem_mount, target, ""))
      | eval fs_pct_used=tonumber(tostring(coalesce(fs_pct_used, pct_used, USE_PCT, capacity_pct, used_pct, "")),10)
      | eval fs_avail_bytes=tonumber(tostring(coalesce(fs_avail_bytes, avail_bytes, available_bytes, avail, "")),10)
      | eval fs_size_bytes=tonumber(tostring(coalesce(fs_size_bytes, size_bytes, total_bytes, blocks, "")),10)
      | eval mlow=lower(mount)
      | where match(mlow,"/var/lib/docker") OR match(mlow,"/var/lib/containers/storage") OR match(mlow,"^/$")
      | stats latest(fs_pct_used) AS fs_pct_used latest(fs_avail_bytes) AS fs_avail_bytes latest(fs_size_bytes) AS fs_size_bytes BY host_id ]
| eventstats latest(fs_pct_used) AS fs_pct_used latest(fs_avail_bytes) AS fs_avail_bytes latest(fs_size_bytes) AS fs_size_bytes BY host_id
| sort 0 + host_id, volume_name, signal_family, _time
| streamstats window=24 current=t global=f count AS win_n sum(_time) AS win_sum_t sum(volume_size_bytes) AS win_sum_y sum(eval(_time*volume_size_bytes)) AS win_sum_ty sum(eval(_time*_time)) AS win_sum_tt first(volume_size_bytes) AS sz_first last(volume_size_bytes) AS sz_last BY host_id, volume_name, signal_family
| eval denom=(win_n*win_sum_tt - win_sum_t*win_sum_t)
| eval slope_bps=if(win_n>=6 AND isnotnull(denom) AND denom!=0, (win_n*win_sum_ty - win_sum_t*win_sum_y)/denom, null())
| eval growth_bytes_per_hour=round(coalesce(slope_bps,0)*3600,4)
| eval growth_pct_24h=if(sz_first>0, round(100*(sz_last-sz_first)/sz_first,2), null())
| eval volume_size_growth_pct_per_hour=if(volume_size_bytes>0 AND growth_bytes_per_hour!=0, round(100*growth_bytes_per_hour/volume_size_bytes,6), null())
| eval projected_full_hours=if(growth_bytes_per_hour>1024 AND isnotnull(fs_avail_bytes) AND fs_avail_bytes>0, round(fs_avail_bytes/growth_bytes_per_hour,2), null())
| stats latest(host_id) AS host_id latest(volume_driver) AS volume_driver latest(mount_point) AS mount_point latest(volume_size_bytes) AS volume_size_bytes latest(ref_count) AS ref_count latest(fs_pct_used) AS fs_pct_used latest(fs_avail_bytes) AS fs_avail_bytes latest(fs_size_bytes) AS fs_size_bytes latest(growth_bytes_per_hour) AS growth_bytes_per_hour latest(growth_pct_24h) AS growth_pct_24h latest(volume_size_growth_pct_per_hour) AS volume_size_growth_pct_per_hour latest(projected_full_hours) AS projected_full_hours latest(signal_family) AS signal_family latest(container_id) AS container_id max(win_n) AS regression_samples BY host_id volume_name signal_family
| eval dangling_flag=if(signal_family="named_volume" AND (ref_count==0 OR isnull(ref_count)),1,0)
| join type=left max=0 host_id, volume_name
    [| inputlookup docker_volume_baseline.csv
     | eval host_id=lower(trim(toString(coalesce(host_id, host, Host, ""))))
     | eval volume_name=trim(toString(coalesce(volume_name, volume, name, "")))
     | eval expected_growth_bytes_per_hour_max=tonumber(tostring(coalesce(expected_growth_bytes_per_hour_max, baseline_growth_bph_max, golden_growth_bph, "")),10)
     | eval expected_idle_bytes_min=tonumber(tostring(coalesce(expected_idle_bytes_min, idle_floor_bytes, "")),10)
     | fields host_id volume_name expected_growth_bytes_per_hour_max expected_idle_bytes_min ]
| eventstats sum(eval(if(signal_family="named_volume", volume_size_bytes, null()))) AS host_named_total_bytes BY host_id
| eval dangling_share_pct=if(dangling_flag==1 AND host_named_total_bytes>0, round(100*volume_size_bytes/host_named_total_bytes,2), null())
| eval baseline_delta_ratio=if(isnotnull(expected_growth_bytes_per_hour_max) AND expected_growth_bytes_per_hour_max>0 AND growth_bytes_per_hour>=0, round(growth_bytes_per_hour/expected_growth_bytes_per_hour_max,3), null())
| eval severity=case(
    fs_pct_used>=90, "critical_filesystem_above_90pct_imminent_enospc",
    (signal_family="named_volume") AND isnotnull(projected_full_hours) AND projected_full_hours>0 AND projected_full_hours<=24 AND growth_bytes_per_hour>4096, "critical_volume_growth_projecting_full_within_24h",
    (signal_family="overlay2_rw_layer") AND growth_pct_24h>=50 AND volume_size_bytes>=1073741824, "high_overlay2_layer_above_50pct_growth_24h",
    (signal_family="named_volume") AND dangling_flag==1 AND dangling_share_pct>=10, "high_dangling_volumes_consuming_above_10pct",
    (signal_family="named_volume") AND isnotnull(expected_growth_bytes_per_hour_max) AND expected_growth_bytes_per_hour_max>0 AND growth_bytes_per_hour>(expected_growth_bytes_per_hour_max*1.5), "medium_baseline_growth_drift",
    (signal_family="named_volume") AND growth_bytes_per_hour>=0 AND growth_bytes_per_hour<=1024 AND volume_size_bytes>=10737418240, "low_underutilized_volume_long_idle",
    true(), null())
| where isnotnull(severity)
| eval recommended_response=case(
    severity="critical_filesystem_above_90pct_imminent_enospc", "Stop scheduled image promotions; drain new deploys; expand /var/lib/docker filesystem or migrate docker-root; prune unused images only after snapshots; validate bind mounts on same spindle are not also pinned at high watermark.",
    severity="critical_volume_growth_projecting_full_within_24h", "Identify writer inside the container; move ephemeral caches off overlay R/W into tmpfs or a dedicated volume with quota; schedule controlled prune of dangling artifacts only with owner approval; add capacity or relocate volume to larger pool.",
    severity="high_overlay2_layer_above_50pct_growth_24h", "Container is inflating overlay2 diff; refactor to named volume or host bind for durable data; audit application logs and temp extraction paths; rebuild image to remove accidental local writes.",
    severity="high_dangling_volumes_consuming_above_10pct", "Run docker volume ls and reconcile owners; remove confirmed-unreferenced volumes under change control; fix automation that leaks volumes during compose down; reclaim space with finance-friendly before/after metrics.",
    severity="medium_baseline_growth_drift", "Growth exceeds docker_volume_baseline.csv band; validate bulk ingest windows versus true leak; tune baseline after CAB review; compare against sibling host cohort.",
    severity="low_underutilized_volume_long_idle", "Large idle footprint with flat slope; confirm still required; archive data or shrink allocation; candidate for fleet storage reclamation backlog.",
    true(), "Correlate docker:volume_inspect, docker:overlay2_du, and linux:df before closing; confirm du sampling delay is not skewing slope.")
| table host_id volume_name volume_driver mount_point volume_size_bytes growth_bytes_per_hour fs_pct_used projected_full_hours severity recommended_response signal_family dangling_flag regression_samples volume_size_growth_pct_per_hour growth_pct_24h baseline_delta_ratio dangling_share_pct
```

## CIM SPL

```spl
| tstats summariesonly=true avg(Performance.disk_usage) AS avg_disk_pct max(Performance.disk_usage) AS peak_disk_pct FROM datamodel=Performance WHERE nodename=Performance.Storage earliest=-4h@h latest=@h BY Performance.host span=15m
| rename Performance.host AS host_id
| where peak_disk_pct>85
```

## Visualization

Primary heatmap of volume_size_bytes by host_id across thirty days; secondary scatter of growth_bytes_per_hour against volume_size_bytes colored by severity; tertiary line chart of fs_pct_used per host; quaternary table of dangling_flag volumes ranked by dangling_share_pct with drilldowns to inspect JSON.

## Known False Positives

Planned database bulk-import windows intentionally raise named-volume slopes for hours; align those windows with docker_volume_baseline.csv notes or temporary macro suppressions instead of muting the control globally. Canary rollouts may leave dangling volumes between cutovers while the next task still mounts the successor volume; require two consecutive intervals above threshold or a missing deploy tag before paging storage on-call. Patch Tuesday image promotion waves can spike overlay2 diff measurements while layers extract even when applications are idle; corroborate with docker pull and events timelines before blaming application leaks. Heavy du execution on busy XFS arrays occasionally returns stale size snapshots that flatten regression slopes for a single poll; treat single-interval quiet as suspicious only if df and application logs agree. Legitimate developer clusters may keep large idle volumes by design; route those hosts through FinOps macros rather than production paging. Bind mounts that fill a separate array can trip fs_pct_used on non-docker mounts if your df collector includes them; confirm mount correlation before treating the issue as graph-root only.

## References

- [Docker Docs — storage drivers overview](https://docs.docker.com/storage/storagedriver/)
- [Docker Docs — volumes](https://docs.docker.com/storage/volumes/)
- [Docker Docs — OverlayFS storage driver](https://docs.docker.com/storage/storagedriver/overlayfs-driver/)
- [Spotify Engineering — improving critical infrastructure rollouts](https://engineering.atspotify.com/2017/6/improving-critical-infrastructure-rollouts)
- [Splunk Lantern — Getting Docker log data into Splunk Cloud Platform with OpenTelemetry](https://lantern.splunk.com/Platform_Data_Management/Unlock_Insights/Getting_Docker_log_data_into_Splunk_Cloud_Platform_with_OpenTelemetry)
- [manpages.org — df(1) manual](https://manpages.org/df)
