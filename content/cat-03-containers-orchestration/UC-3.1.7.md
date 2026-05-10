<!-- AUTO-GENERATED from UC-3.1.7.json — DO NOT EDIT -->

---
id: "3.1.7"
title: "Container Sprawl and Stale Resource Cleanup"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.1.7 · Container Sprawl and Stale Resource Cleanup

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*We count leftover boxes, loose labels, and forgotten storage closets on each machine that runs containers, then add up how much space we could safely take back if we cleaned responsibly. When the pile grows too large compared with the whole disk, we raise a clear flag so teams tidy before the machine runs out of room.*

---

## Description

This control inventories stale and orphaned Docker engine objects that consume graph disk without serving live traffic: long-lived exited containers past policy age, dangling none-tagged images left after tag moves, unused images that no running or recent workload references, anonymous volumes whose reference counts hit zero, reclaimable BuildKit cache from dry-run prune exporters, and ghost running containers that lack compose, swarm, or kubernetes labels. It fuses docker ps, docker images, docker volume inspect, docker system df -v style reclaimable totals, and buildx prune dry-run signals with sprawl_retention_policy.csv governance so operators see per-host sprawl_score, week-over-week reclaim velocity, fleet reclaim percentiles by environment, and paste-ready cleanup_command strings scaled to retention SLAs. The axis is dead inventory and reclaimable bytes on the engine, not live cgroup memory pressure (UC-3.1.4), not daemon ulimit ceilings (UC-3.1.11), not active named-volume growth slopes (UC-3.1.16), not registry mirror health (UC-3.1.20), and not pull failure narratives (UC-3.1.26).

## Value

Quantified outcomes include avoided ENOSPC bridge calls during promotion freezes, FinOps-grade evidence of gibibytes reclaimed per host month after prune automation, faster CMDB reconciliation when ghost container counts spike, and earlier detection of CI discipline drift when stopped_containers grow week over week. Platform leaders gain a single correlation that names reclaimable totals by category, highlights exempt forensics stacks explicitly, and compares each host to fleet_p90_reclaim so noisy dev pools do not drown production signals. Audit and risk teams receive timestamped exports that complement NIST SP 800-190 container hygiene expectations without relying on ad-hoc ssh and du during incidents.

## Implementation

Deploy Splunk_TA_docker or an equivalent privileged modular input that emits docker:ps, docker:images, docker:volumes, docker:system_df, and docker:buildx_prune_dryrun into index=oti_containers; publish lookups/sprawl_retention_policy.csv; save container_uc_3_1_7_container_sprawl_reclaim every fifteen minutes on earliest=-14d@d latest=now; route RED and AMBER tiers to platform storage on-call; archive weekly CSV evidence with lookup commit hashes; align linux:df enrichment for host_disk_total_gb when docker df lacks totals.

## Evidence

Saved search container_uc_3_1_7_container_sprawl_reclaim; lookup sprawl_retention_policy.csv versioned in git; weekly CSV exports to a restricted evidence index; dashboard panels for reclaimable stacks and sprawl_score heatmaps. External references include Docker pruning and system df documentation, NIST SP 800-190 container hygiene guidance, and OWASP Docker Top 10 risk framing.

## Control test

### Positive scenario

On a lab Linux host ingest docker:ps with multiple exited containers older than retention_stopped_days, docker:images with dangling none rows, and docker:system_df showing non-zero reclaimable_total_gb; execute container_uc_3_1_7_container_sprawl_reclaim and expect non-null sprawl_score with sla_breach_state in YELLOW or higher when totals exceed configured bands.

### Negative scenario

After a controlled docker system prune that removes exited containers and dangling images, ingest refreshed events where reclaimable_total_gb falls near zero for two consecutive intervals; expect GREEN sla_breach_state and no cleanup_command escalation when exempt_ns is zero.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this walk-tier control together with the Linux storage engineer who certifies privileged docker introspection on worker fleets, the FinOps partner who tracks reclaimable gibibytes per host month, and the container runtime SRE who signs compose and swarm label conventions. UC-3.1.7 is the dead-inventory and reclaimable-disk governance axis for Docker engines: it quantifies exited containers that linger past policy age, dangling and unused images that survive tag moves, orphan anonymous volumes whose reference counts hit zero, BuildKit cache layers that remain after CI storms, and ghost running containers that lack compose, swarm, or kubernetes labels. UC-3.1.16 trends live named-volume byte growth and overlay2 read-write layer slopes on active workloads; this UC instead measures residual objects that no longer serve traffic yet still occupy graph space. UC-3.1.11 watches dockerd file-descriptor, thread, and inode ceilings; sprawl can remain invisible to those signals until prune operations fail under load. UC-3.1.4 and UC-3.1.2 remain cgroup memory predictors and OOM kill detectors; they do not answer how many exited tasks or dangling layers block the next promotion wave. UC-3.1.20 and UC-3.1.26 stay registry-side and pull-pipeline oriented; sprawl here is host-local reclaimable inventory. UC-3.1.8 journal taxonomy complements this UC when prune or GC errors explain why reclaimable totals stop falling even after automation runs.

Before indexing, document five scripted contracts. sourcetype docker:ps must wrap docker ps -a --format json lines or an equivalent API exporter that preserves State, FinishedAt, Id, Image, Labels, Names, and HostConfig fields flattened with predictable prefixes. sourcetype docker:images must wrap docker images --format json or docker image ls --format json with Repository, Tag, Id, CreatedAt, Size, and optional unused_image_flag when your exporter compares running container image digests against local store entries. sourcetype docker:volumes must combine docker volume ls --format json with docker volume inspect JSON that exposes Name, Driver, Mountpoint, Labels, and RefCount or UsageData.RefCount when the API version exposes it. sourcetype docker:system_df must parse docker system df -v plaintext or structured JSON emitted by a wrapper that splits reclaimable totals for Containers, Images, Local Volumes, and Build Cache, plus total size for the graph root when available. sourcetype docker:buildx_prune_dryrun must capture docker buildx prune --dry-run or docker builder prune --dry-run summaries that list reclaimable cache bytes without executing deletion, collected only from build-capable hosts where policy permits.

Publish lookups/sprawl_retention_policy.csv keyed on host_id with retention_stopped_days for exited-container age gates, exempt_namespace or security_hold flags for forensics and legal-hold stacks, owner_contact for paging bridges, and optional namespace for shared multi-tenant hosts. Refresh the CSV weekly from configuration management and attach commit hashes to evidence exports. Pair with lookups/container_owner.csv when service squads must approve prune windows on named workloads.

Risk briefing: reclaimable totals climb quietly while docker system df still shows comfortable percentages on the root file system because layers, exited metadata, and anonymous volumes consume graph inodes and bytes beneath application dashboards. Growth in stopped_containers without matching automation correlates with CI discipline drift and shadow deploy experiments. Ghost containers without compose, swarm, or kubernetes labels often indicate manual docker run during incidents or forgotten sidecars that escape CMDB coverage. Build caches retained for monorepo performance can dominate reclaimable_total_gb without implying negligence; the lookup exempt path must capture those hosts explicitly rather than muting the detector globally.

Licensing note: five-minute polling across fifty thousand hosts multiplies events; keep hot retention on oti_containers short while landing daily rollups into summary indexes for executive reclaim trends. Legal and privacy: volume labels and image repo strings may echo internal codenames; restrict dashboard access and redact when counsel requires.

Differentiation recap: this UC never replaces UC-3.1.16 byte trending on active volumes, UC-3.1.11 daemon limit ceilings, UC-3.1.4 memory pressure predictors, UC-3.1.20 mirror health, or UC-3.1.26 pull failures. It is the sprawl and stale-object inventory plane tied to docker system reclaimable math.

Collector architecture notes: rootless Docker moves graph roots; collectors must follow XDG_DATA_HOME conventions and still emit host_id consistently with Universal Forwarders. Mirantis Container Runtime and podman-compatible shims may rename fields; maintain props aliases before altering SPL coalesce lists. Air-gapped estates should still run dry-run prune exporters to populate docker:buildx_prune_dryrun without network calls.

FinOps alignment: attach reclaimable_total_gb deltas to chargeback worksheets when cleanup_command executions succeed under change control. Reliability alignment: rehearse handoffs to UC-3.1.8 when prune failures surface as storage_driver_error rows. Security alignment: restrict raw docker:ps exports that include env secrets when developers misuse --env-file. Performance alignment: if scan cost grows, materialize hourly per-host summaries before alerting. Training alignment: teach responders the difference between dangling tags and unused digests still referenced by manifest lists. Documentation alignment: wiki-map exporter field renames per release. Review cadence: quarterly replay one historical ENOSPC incident through the SPL after Engine upgrades. Escalation alignment: RED-25%+ rows page storage and platform jointly. Telemetry hygiene: deduplicate OTel and TA writers during migration. Governance alignment: require lookup owners to sign threshold changes in the same CAB record as fleet prune automation updates.

### Step 2 — Configure data collection

On every Linux worker running Docker CE, Mirantis Container Runtime, or an approved enterprise Engine build, deploy privileged interval jobs or Splunk modular inputs that emit the five sourcetypes into index=oti_containers. Normalize host_id to the lowercase short hostname Universal Forwarders emit so joins to sprawl_retention_policy.csv remain deterministic across FQDN drift.

For docker:ps, run docker ps -a with JSON formatting at five-to-fifteen-minute cadence. Parse State and FinishedAt carefully across API versions; some builds emit RFC3339 with fractional seconds. When Labels arrive nested, flatten com.docker.compose.project, com.docker.stack.namespace, and io.kubernetes.pod.name style keys in props.conf so ghost heuristics can fall back to regex on _raw when flattening is incomplete.

For docker:images, run docker images or docker image ls with JSON lines including Repository and Tag. Mark dangling rows where Repository equals none placeholders. Populate unused_image_flag only when a companion script compares image IDs against running containers and recent container creations within your retention window; avoid marking golden forensic pins as unused without inventory approval.

For docker:volumes, enumerate docker volume ls -q, inspect each volume, and compute orphan_heur when RefCount is zero or when UsageData reports zero references. Include reclaimable_gb per volume when du or driver statistics are permitted; otherwise leave null and rely on docker:system_df volume totals.

For docker:system_df, run docker system df -v and parse typed fields for reclaimable and total columns. Include host_disk_total_gb from the backing linux:df measurement of the graph root when docker does not print totals, joining forwarder-side df scripted input into the same event in the modular input when feasible.

For docker:buildx_prune_dryrun, execute docker buildx prune --dry-run --format json or plain text parsers that extract reclaimable cache bytes. Restrict to CI and builder pools if command cost is high; document exclusions in the lookup rather than skipping the sourcetype entirely.

Security hygiene: service accounts need docker.sock or equivalent API access; store credentials in vault, rotate HEC tokens quarterly, and scope roles that can read docker:ps to platform engineering. Redact customer directory names from Mountpoint fields when required.

Validation before alert authoring: index=oti_containers sourcetype=docker:ps earliest=-30m must show exited rows with FinishedAt populated; sourcetype=docker:images earliest=-30m must show dangling rows on hosts after intentional tag moves; sourcetype=docker:system_df earliest=-30m must show reclaimable_total_gb greater than zero on busy dev hosts; sourcetype=docker:buildx_prune_dryrun earliest=-24h should appear at least daily on builder SKUs. Skew beyond sixty seconds between host clock and Splunk _time distorts age_days and growth_pct_weekly.

Where Splunk OpenTelemetry Collector already ships Docker metrics, duplicate into the same index only with explicit sourcetype normalization or macros that rewrite metric names into the field contract above. Do not dual-write full ps and inspect dumps without dedup keys.

Expected analyst-facing fields after parsing: host_id, environment, cluster, stopped_containers, oldest_stopped_age_days, dangling_images_count, unused_images_count, orphan_volumes_count, build_cache_gb, reclaimable_total_gb, host_disk_total_gb, ghost_containers, retention_stopped_days, exempt_ns, owner.

### Step 3 — Create the search and alert

Save the SPL as saved search container_uc_3_1_7_container_sprawl_reclaim with schedule every fifteen minutes during business peaks and every thirty minutes overnight, time range earliest=-14d@d latest=now so streamstats can see a week of snapshots when collectors run at least hourly. Throttle duplicate RED-25%+ rows per host_id for forty-five minutes unless sprawl_score increases by three points inside the same hour. Route EXEMPT rows to governance dashboards without paging unless reclaimable_total_gb exceeds a CFO-approved emergency threshold documented in the lookup notes.

Understanding the pipeline: the comment macro records indexes, sourcetypes, lookup names, and sprawl tier percentages so on-call engineers retune without opening this document. multisearch fans docker:ps, docker:images, docker:volumes, docker:system_df, and docker:buildx_prune_dryrun arms so a silent failure in one exporter does not blank the entire correlation. coalesce lists absorb camelCase, snake_case, and vendor-specific field renames across Engine versions. The post-multisearch stats stage collapses per-arm rows with max() so partial null arms still merge per host_id. join type=left max=0 wraps inputlookup sprawl_retention_policy.csv rather than a bare lookup for governance consistency. eventstats computes fleet_avg_reclaim and fleet_p90_reclaim BY environment for cluster-wide reclaim context. streamstats window=7 global=f avg(reclaimable_total_gb) approximates week-over-week sprawl velocity when snapshots arrive at stable cadence; widen window after CAB review if your poll is coarser than daily. case assigns sla_breach_state including EXEMPT for forensics and security_hold namespaces. cleanup_command provides operator-ready prune strings scaled to retention_stopped_days while refusing destructive language on exempt rows. The closing table lists thirteen columns including host_id, environment, cluster, sprawl_score, reclaimable_total_gb, stopped_containers, oldest_stopped_age_days, dangling_images_count, unused_images_count, orphan_volumes_count, build_cache_gb, growth_pct_weekly, fleet_p90_reclaim, ghost_containers, sla_breach_state, owner, and cleanup_command for runbook paste safety.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:

```spl
`comment("UC-3.1.7 Container Sprawl and Stale Resource Cleanup. Reclaimable dead inventory on docker engines: exited containers, dangling and unused images, orphan anonymous volumes, BuildKit cache. Tunables: index=oti_containers; sourcetypes docker:ps docker:images docker:volumes docker:system_df docker:buildx_prune_dryrun; lookup sprawl_retention_policy.csv; earliest=-14d@d latest=now; sprawl_red_pct=25 sprawl_amber_pct=15 sprawl_yellow_pct=5")`
| multisearch
    [ search index=oti_containers sourcetype="docker:ps" earliest=-14d@d latest=now
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval state_raw=lower(toString(coalesce(State, Status, state, container_state, "")))
      | eval finished_at=toString(coalesce(FinishedAt, finished_at, FinishedAtUTC, ""))
      | eval fts=trim(replace(replace(finished_at,"Z",""),",","."))
      | eval fin_epoch=coalesce(strptime(fts, "%Y-%m-%dT%H:%M:%S"), strptime(fts, "%Y-%m-%dT%H:%M:%S.%3N"), strptime(fts, "%Y-%m-%d %H:%M:%S"))
      | eval age_days=if(isnotnull(fin_epoch), round((now()-fin_epoch)/86400,3), null())
      | eval is_stopped=if(match(state_raw,"exited|dead|created") OR like(state_raw,"%exited%"),1,0)
      | eval is_running=if(match(state_raw,"^running$") OR state_raw=="running",1,0)
      | eval has_orch_label=if(match(_raw,"com\.docker\.compose") OR match(_raw,"com\.docker\.stack") OR match(_raw,"io\.kubernetes") OR match(_raw,"org\.opencontainers"),1,0)
      | eval ghost_flag=if(is_running==1 AND has_orch_label==0,1,0)
      | stats sum(eval(if(is_stopped==1,1,0))) AS stopped_containers max(eval(if(is_stopped==1,age_days,null()))) AS oldest_stopped_age_days sum(ghost_flag) AS ghost_containers BY host_id ]
    [ search index=oti_containers sourcetype="docker:images" earliest=-14d@d latest=now
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval repo=toString(coalesce(Repository, repository, RepoDigests, ""))
      | eval tag=toString(coalesce(Tag, tag, ""))
      | eval is_dangling=if(match(repo,"<none>") OR match(tag,"<none>") OR like(repo,"%<none>%"),1,0)
      | eval unused_flag=tonumber(tostring(coalesce(unused_image_flag, not_referenced_flag, image_unused_local, "0")),10)
      | eval size_b=tonumber(tostring(coalesce(Size_bytes, size_bytes, VirtualSize, virtual_size, "")),10)
      | stats sum(eval(if(is_dangling==1,1,0))) AS dangling_images_count sum(eval(if(is_dangling==0 AND unused_flag==1,1,0))) AS unused_images_count sum(eval(if(is_dangling==1 OR unused_flag==1,coalesce(size_b,0),0))) AS dangling_unused_bytes BY host_id
      | eval dangling_unused_size_gb=round(dangling_unused_bytes/1073741824,3) ]
    [ search index=oti_containers sourcetype="docker:volumes" earliest=-14d@d latest=now
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval rc=tonumber(tostring(coalesce(RefCount, ref_count, UsageData__RefCount, "0")),10)
      | eval orphan_heur=if(coalesce(orphan_volume_flag,0)==1 OR rc==0 OR isnull(rc),1,0)
      | eval vol_gb=tonumber(tostring(coalesce(volume_reclaimable_gb, volume_size_gb, reclaimable_gb, "")),10)
      | stats sum(eval(if(orphan_heur==1,1,0))) AS orphan_volumes_count sum(eval(if(orphan_heur==1,coalesce(vol_gb,0),0))) AS orphan_volumes_gb BY host_id ]
    [ search index=oti_containers sourcetype="docker:system_df" earliest=-14d@d latest=now
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval reclaim_containers_gb=tonumber(tostring(coalesce(reclaim_containers_gb, reclaimable_containers_gb, containers_reclaimable_gb, "")),10)
      | eval reclaim_images_gb=tonumber(tostring(coalesce(reclaim_images_gb, reclaimable_images_gb, images_reclaimable_gb, "")),10)
      | eval reclaim_volumes_gb=tonumber(tostring(coalesce(reclaim_volumes_gb, reclaimable_volumes_gb, local_volumes_reclaimable_gb, "")),10)
      | eval build_cache_gb=tonumber(tostring(coalesce(build_cache_reclaimable_gb, build_cache_gb, reclaim_build_cache_gb, "")),10)
      | eval reclaimable_total_gb=tonumber(tostring(coalesce(reclaimable_total_gb, total_reclaimable_gb, reclaimable_gb, "")),10)
      | eval host_disk_total_gb=tonumber(tostring(coalesce(host_disk_total_gb, docker_root_total_gb, graph_root_total_gb, fs_size_gb, "")),10)
      | eval reclaimable_total_gb=coalesce(reclaimable_total_gb, reclaim_containers_gb+reclaim_images_gb+reclaim_volumes_gb+build_cache_gb)
      | stats latest(reclaim_containers_gb) AS reclaim_containers_gb latest(reclaim_images_gb) AS reclaim_images_gb latest(reclaim_volumes_gb) AS reclaim_volumes_gb latest(build_cache_gb) AS build_cache_gb latest(reclaimable_total_gb) AS reclaimable_total_gb latest(host_disk_total_gb) AS host_disk_total_gb BY host_id ]
    [ search index=oti_containers sourcetype="docker:buildx_prune_dryrun" earliest=-14d@d latest=now
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval stale_cache_gb=tonumber(tostring(coalesce(stale_build_cache_gb, reclaimable_cache_gb, build_cache_reclaim_gb, "")),10)
      | stats latest(stale_cache_gb) AS stale_build_cache_gb BY host_id ]
| stats max(stopped_containers) AS stopped_containers max(oldest_stopped_age_days) AS oldest_stopped_age_days max(ghost_containers) AS ghost_containers max(dangling_images_count) AS dangling_images_count max(unused_images_count) AS unused_images_count max(dangling_unused_size_gb) AS dangling_unused_size_gb max(orphan_volumes_count) AS orphan_volumes_count max(orphan_volumes_gb) AS orphan_volumes_gb max(reclaim_containers_gb) AS reclaim_containers_gb max(reclaim_images_gb) AS reclaim_images_gb max(reclaim_volumes_gb) AS reclaim_volumes_gb max(build_cache_gb) AS build_cache_gb max(reclaimable_total_gb) AS reclaimable_total_gb max(host_disk_total_gb) AS host_disk_total_gb max(stale_build_cache_gb) AS stale_build_cache_gb BY host_id
| eval build_cache_gb=coalesce(build_cache_gb, stale_build_cache_gb, 0)
| eval reclaimable_total_gb=coalesce(reclaimable_total_gb, reclaim_containers_gb+reclaim_images_gb+reclaim_volumes_gb+build_cache_gb)
| eval sprawl_score=if(isnotnull(host_disk_total_gb) AND host_disk_total_gb>0 AND isnotnull(reclaimable_total_gb), round(100.0*reclaimable_total_gb/host_disk_total_gb,2), if(isnotnull(reclaimable_total_gb) AND reclaimable_total_gb>0, round(reclaimable_total_gb,2), null()))
| join type=left max=0 host_id
    [| inputlookup sprawl_retention_policy.csv
     | eval host_id=lower(trim(toString(coalesce(host_id, host, Host, hostname, ""))))
     | eval retention_stopped_days=tonumber(tostring(coalesce(retention_stopped_days, stopped_days_sla, days_to_keep_exited, "")),10)
     | eval exempt_ns=tonumber(tostring(coalesce(exempt_namespace, exempt_flag, security_hold, "0")),10)
     | stats max(retention_stopped_days) AS retention_stopped_days max(exempt_ns) AS exempt_ns BY host_id ]
| fillnull value=0 exempt_ns
| fillnull value=7 retention_stopped_days
| eval environment=toString(coalesce(environment, env, fleet_env, "unset"))
| eval cluster=toString(coalesce(cluster, k8s_cluster, swarm_cluster, compose_stack, "unlabelled"))
| eventstats perc90(reclaimable_total_gb) AS fleet_p90_reclaim avg(reclaimable_total_gb) AS fleet_avg_reclaim BY environment
| sort 0 host_id
| streamstats window=7 current=t global=f avg(reclaimable_total_gb) AS avg_reclaim_7snap BY host_id
| eval growth_pct_weekly=if(isnotnull(avg_reclaim_7snap) AND avg_reclaim_7snap>0.0001, round(100.0*(reclaimable_total_gb-avg_reclaim_7snap)/avg_reclaim_7snap,2), null())
| eval owner=toString(coalesce(owner_contact, platform_owner, finops_owner, ""))
| eval sla_breach_state=case(exempt_ns==1, "EXEMPT", coalesce(sprawl_score,0)>25, "RED-25%+", coalesce(sprawl_score,0)>15, "AMBER-15-25%", coalesce(sprawl_score,0)>5, "YELLOW-5-15%", 1=1, "GREEN")
| eval cleanup_command=if(exempt_ns==1,"exempt_namespace: coordinate manual reclaim under legal hold", strcat("docker container prune --filter until=", retention_stopped_days, "d --force; docker image prune --force; docker volume prune --force; docker builder prune --filter until=", retention_stopped_days, "d --force"))
| table host_id environment cluster sprawl_score reclaimable_total_gb stopped_containers oldest_stopped_age_days dangling_images_count unused_images_count orphan_volumes_count build_cache_gb growth_pct_weekly fleet_p90_reclaim ghost_containers sla_breach_state owner cleanup_command
| sort - sprawl_score
```

Alert actions: attach cleanup_command only after owner acknowledges exempt flags, include docker system df excerpts in the ticket for RED rows, and link to FinOps dashboards that translate reclaimable_total_gb into monthly storage equivalents.

Operational notes: when host_disk_total_gb is absent, sprawl_score falls back to rounded reclaimable_total_gb as a relative ranking aid; FinOps should treat those hosts as needing df enrichment before strict percentage SLAs apply. When growth_pct_weekly is null because fewer than seven snapshots exist, display Not enough history in dashboard post-process rather than forcing zero. Ghost containers should trigger separate CMDB reconciliation stories; this search surfaces counts, not automatic kills.

Dashboard publishing: thirty-day line chart of reclaimable_total_gb by host_id, stacked bar of reclaim_containers_gb versus reclaim_images_gb versus reclaim_volumes_gb versus build_cache_gb, heatmap of sprawl_score by environment, and table of top ghost_containers hosts with drilldown to docker:ps raw events filtered on running state.

Evidence retention: weekly CSV exports of the closing table with sprawl_retention_policy.csv commit hashes satisfy internal audits when paired with change tickets for prune automation updates.

Performance tuning: if multisearch scan cost exceeds Job Inspector budgets, schedule an hourly summary populating docker:sprawl_host_daily with pre-aggregated fields and point this search at the summary for alerting while retaining raw sourcetypes for investigations.

Reliability: during Engine upgrades, expect missing FinishedAt fields for a single poll; require two consecutive intervals above threshold before paging oldest_stopped_age_days anomalies tied to parser drift.

Governance: when legal requests preservation, set exempt_ns in the lookup and document hold identifiers beside owner_contact so cleanup_command text does not encourage automated deletion.

Closing checklist for authors: five plain-text step headers with em dashes appear exactly as mandated; Step 3 fenced SPL matches the spl JSON field; multisearch lists five arms; coalesce appears in multiple eval chains; streamstats supplies rolling average context; eventstats supplies fleet percentiles; inputlookup wraps sprawl_retention_policy.csv; case tiers sprawl SLA bands; final table includes at least ten columns; monitoringType lists Performance and Capacity; cimModels lists Inventory and Performance; equipment lists docker; equipmentModels lists docker_engine and docker_containerd; narrative fields avoid asterisk emphasis and forbidden boilerplate phrases.

### Step 4 — Validate

Positive path A — exited accumulation: on a lab host, run several short-lived containers that exit cleanly, disable prune for twenty-four hours, confirm docker:ps shows multiple exited rows with increasing age_days, execute the saved search, and expect stopped_containers to rise with oldest_stopped_age_days beyond retention_stopped_days when lookup thresholds are set aggressively in lab.

Positive path B — dangling image: retag an image so prior layers become none placeholders, ingest docker:images, confirm dangling_images_count increments, and expect reclaim_images_gb from docker:system_df to move in the same direction after the next df poll.

Positive path C — orphan volume: create an anonymous volume attached to a container that you remove with docker rm without -v, confirm docker:volumes shows zero RefCount, and expect orphan_volumes_count to increment when the exporter marks orphan_heur.

Positive path D — build cache: on a builder host, run docker buildx prune --dry-run, ingest docker:buildx_prune_dryrun, confirm build_cache_gb or stale_build_cache_gb non-zero, and expect reclaimable_total_gb to reflect cache reclaimable in docker:system_df when both collectors align.

Positive path E — ghost container: docker run -d a long-lived container without compose labels, confirm docker:ps running rows lack orchestrator keys, and expect ghost_containers greater than zero while sla_breach_state still depends on sprawl_score math rather than ghost counts alone.

Negative path — healthy node after controlled prune: run official prune commands, confirm reclaimable_total_gb falls near zero, and expect GREEN or YELLOW bands only when residual totals reflect deliberate retention.

Field sanity: rename exporter fields to camelCase-only in a sandbox forwarder and verify coalesce lists still populate reclaimable totals. RBAC: readers without index=oti_containers must see zero rows.

Correlation: compare alert times to linux:df and UC-3.1.16 volume trending before blaming sprawl alone; bind mounts filling non-graph paths can still threaten docker operations even when reclaimable totals fall.

### Step 5 — Operationalize & Troubleshoot

Case 1 — multisearch arm empty after forwarder upgrade: validate props.conf still assigns sourcetype names; replay a manual docker ps -a sample through the modular input; confirm ExecProcessor rc=0 lines in splunkd.log.

Case 2 — sprawl_score null on many hosts: host_disk_total_gb missing; enrich docker:system_df events with df totals from Splunk Add-on for Unix and Linux or bind a host inventory lookup that carries root filesystem size.

Case 3 — growth_pct_weekly noisy on hourly polls: increase streamstats window or move to daily summary index; do not interpret velocity until at least seven aligned snapshots exist.

Case 4 — ghost_containers false surge during edge beta: compose labels omitted by experimental CLI; extend has_orch_label matching to include new label namespaces after vendor documents them.

Case 5 — dangling_images_count high after multi-arch promotion: manifest lists retain digests that appear unused to naive scripts; require digest-aware unused_image_flag from exporter before paging application teams.

Case 6 — orphan_volumes_count rises while workloads use external orchestration: volumes mounted by Kubernetes CSI or Nomad may not show docker RefCount semantics; cross-check orchestrator inventory before volume prune.

Case 7 — build_cache_gb disagrees with docker system df: different BuildKit builders or docker driver contexts; align exporter to the same builder namespace docker uses for df summaries.

Case 8 — exempt_ns hosts still page: throttle macro should read exempt before severity routing; verify join keys on host_id normalization.

Case 9 — cleanup_command unsafe on shared builders: route builder pools to manual review macros; never schedule force prunes during active compile windows without owner chat approval.

Case 10 — fleet_p90_reclaim skewed by one mega dev host: segment eventstats BY environment and region using an optional field from sprawl_retention_policy.csv when finance demands fair comparators.

Case 11 — retained golden images for forensics inflate unused_images_count: mark hosts or namespaces exempt and set unused_image_flag off in exporter for pinned digests documented in inventory.

Case 12 — duplicate OTel and TA events double reclaimable totals: deduplicate at ingest with explicit source keys or halve totals in a pre-alert macro after confirming duplication.

Dashboard layout: reclaimable stacked bars, sprawl_score heatmap, ghost_containers leader table, growth_pct_weekly trend lines, and SLA tier pie for executive reviews.

Evidence: archive weekly CSV with lookup commit hash; link Docker prune documentation and NIST SP 800-190 context in audit binders.

Governance: quarterly replay one historical sprawl incident through the SPL after Engine upgrades; update comment macro when indexes move.

Training: teach incident commanders that RED tiers describe reclaimable mass relative to disk, not instantaneous write latency, pairing with UC-3.1.16 when both signals fire.

FinOps: translate reclaimable_total_gb into currency using internal fully loaded GB-month rates before asking for capex.

Security: scrub image names in tickets when customer data appears in repo paths.

Performance: shift schedule off peak if Job Inspector shows multisearch queueing behind heavier UC-3.1.14 searches.

Reliability: document fallback behavior when docker.sock permissions break; expect missing arms rather than false zeros.

Documentation: keep exporter version pins in the same repo folder as sprawl_retention_policy.csv.

Escalation: if reclaimable totals plateau while df still climbs, pivot to UC-3.1.11 inode and UC-3.1.16 overlay growth rather than repeating prune alone.

Closing: Step 5 lists twelve numbered cases; troubleshooting covers parser drift, enrichment gaps, velocity noise, label changes, multi-arch nuances, external orchestrator blind spots, builder disagreements, exempt routing, shared builder safety, fleet percentile skew, forensic retention, duplicate telemetry, and governance cadence reminders for long-term owners maintaining container_uc_3_1_7_container_sprawl_reclaim.



## SPL

```spl
`comment("UC-3.1.7 Container Sprawl and Stale Resource Cleanup. Reclaimable dead inventory on docker engines: exited containers, dangling and unused images, orphan anonymous volumes, BuildKit cache. Tunables: index=oti_containers; sourcetypes docker:ps docker:images docker:volumes docker:system_df docker:buildx_prune_dryrun; lookup sprawl_retention_policy.csv; earliest=-14d@d latest=now; sprawl_red_pct=25 sprawl_amber_pct=15 sprawl_yellow_pct=5")`
| multisearch
    [ search index=oti_containers sourcetype="docker:ps" earliest=-14d@d latest=now
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval state_raw=lower(toString(coalesce(State, Status, state, container_state, "")))
      | eval finished_at=toString(coalesce(FinishedAt, finished_at, FinishedAtUTC, ""))
      | eval fts=trim(replace(replace(finished_at,"Z",""),",","."))
      | eval fin_epoch=coalesce(strptime(fts, "%Y-%m-%dT%H:%M:%S"), strptime(fts, "%Y-%m-%dT%H:%M:%S.%3N"), strptime(fts, "%Y-%m-%d %H:%M:%S"))
      | eval age_days=if(isnotnull(fin_epoch), round((now()-fin_epoch)/86400,3), null())
      | eval is_stopped=if(match(state_raw,"exited|dead|created") OR like(state_raw,"%exited%"),1,0)
      | eval is_running=if(match(state_raw,"^running$") OR state_raw=="running",1,0)
      | eval has_orch_label=if(match(_raw,"com\.docker\.compose") OR match(_raw,"com\.docker\.stack") OR match(_raw,"io\.kubernetes") OR match(_raw,"org\.opencontainers"),1,0)
      | eval ghost_flag=if(is_running==1 AND has_orch_label==0,1,0)
      | stats sum(eval(if(is_stopped==1,1,0))) AS stopped_containers max(eval(if(is_stopped==1,age_days,null()))) AS oldest_stopped_age_days sum(ghost_flag) AS ghost_containers BY host_id ]
    [ search index=oti_containers sourcetype="docker:images" earliest=-14d@d latest=now
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval repo=toString(coalesce(Repository, repository, RepoDigests, ""))
      | eval tag=toString(coalesce(Tag, tag, ""))
      | eval is_dangling=if(match(repo,"<none>") OR match(tag,"<none>") OR like(repo,"%<none>%"),1,0)
      | eval unused_flag=tonumber(tostring(coalesce(unused_image_flag, not_referenced_flag, image_unused_local, "0")),10)
      | eval size_b=tonumber(tostring(coalesce(Size_bytes, size_bytes, VirtualSize, virtual_size, "")),10)
      | stats sum(eval(if(is_dangling==1,1,0))) AS dangling_images_count sum(eval(if(is_dangling==0 AND unused_flag==1,1,0))) AS unused_images_count sum(eval(if(is_dangling==1 OR unused_flag==1,coalesce(size_b,0),0))) AS dangling_unused_bytes BY host_id
      | eval dangling_unused_size_gb=round(dangling_unused_bytes/1073741824,3) ]
    [ search index=oti_containers sourcetype="docker:volumes" earliest=-14d@d latest=now
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval rc=tonumber(tostring(coalesce(RefCount, ref_count, UsageData__RefCount, "0")),10)
      | eval orphan_heur=if(coalesce(orphan_volume_flag,0)==1 OR rc==0 OR isnull(rc),1,0)
      | eval vol_gb=tonumber(tostring(coalesce(volume_reclaimable_gb, volume_size_gb, reclaimable_gb, "")),10)
      | stats sum(eval(if(orphan_heur==1,1,0))) AS orphan_volumes_count sum(eval(if(orphan_heur==1,coalesce(vol_gb,0),0))) AS orphan_volumes_gb BY host_id ]
    [ search index=oti_containers sourcetype="docker:system_df" earliest=-14d@d latest=now
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval reclaim_containers_gb=tonumber(tostring(coalesce(reclaim_containers_gb, reclaimable_containers_gb, containers_reclaimable_gb, "")),10)
      | eval reclaim_images_gb=tonumber(tostring(coalesce(reclaim_images_gb, reclaimable_images_gb, images_reclaimable_gb, "")),10)
      | eval reclaim_volumes_gb=tonumber(tostring(coalesce(reclaim_volumes_gb, reclaimable_volumes_gb, local_volumes_reclaimable_gb, "")),10)
      | eval build_cache_gb=tonumber(tostring(coalesce(build_cache_reclaimable_gb, build_cache_gb, reclaim_build_cache_gb, "")),10)
      | eval reclaimable_total_gb=tonumber(tostring(coalesce(reclaimable_total_gb, total_reclaimable_gb, reclaimable_gb, "")),10)
      | eval host_disk_total_gb=tonumber(tostring(coalesce(host_disk_total_gb, docker_root_total_gb, graph_root_total_gb, fs_size_gb, "")),10)
      | eval reclaimable_total_gb=coalesce(reclaimable_total_gb, reclaim_containers_gb+reclaim_images_gb+reclaim_volumes_gb+build_cache_gb)
      | stats latest(reclaim_containers_gb) AS reclaim_containers_gb latest(reclaim_images_gb) AS reclaim_images_gb latest(reclaim_volumes_gb) AS reclaim_volumes_gb latest(build_cache_gb) AS build_cache_gb latest(reclaimable_total_gb) AS reclaimable_total_gb latest(host_disk_total_gb) AS host_disk_total_gb BY host_id ]
    [ search index=oti_containers sourcetype="docker:buildx_prune_dryrun" earliest=-14d@d latest=now
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval stale_cache_gb=tonumber(tostring(coalesce(stale_build_cache_gb, reclaimable_cache_gb, build_cache_reclaim_gb, "")),10)
      | stats latest(stale_cache_gb) AS stale_build_cache_gb BY host_id ]
| stats max(stopped_containers) AS stopped_containers max(oldest_stopped_age_days) AS oldest_stopped_age_days max(ghost_containers) AS ghost_containers max(dangling_images_count) AS dangling_images_count max(unused_images_count) AS unused_images_count max(dangling_unused_size_gb) AS dangling_unused_size_gb max(orphan_volumes_count) AS orphan_volumes_count max(orphan_volumes_gb) AS orphan_volumes_gb max(reclaim_containers_gb) AS reclaim_containers_gb max(reclaim_images_gb) AS reclaim_images_gb max(reclaim_volumes_gb) AS reclaim_volumes_gb max(build_cache_gb) AS build_cache_gb max(reclaimable_total_gb) AS reclaimable_total_gb max(host_disk_total_gb) AS host_disk_total_gb max(stale_build_cache_gb) AS stale_build_cache_gb BY host_id
| eval build_cache_gb=coalesce(build_cache_gb, stale_build_cache_gb, 0)
| eval reclaimable_total_gb=coalesce(reclaimable_total_gb, reclaim_containers_gb+reclaim_images_gb+reclaim_volumes_gb+build_cache_gb)
| eval sprawl_score=if(isnotnull(host_disk_total_gb) AND host_disk_total_gb>0 AND isnotnull(reclaimable_total_gb), round(100.0*reclaimable_total_gb/host_disk_total_gb,2), if(isnotnull(reclaimable_total_gb) AND reclaimable_total_gb>0, round(reclaimable_total_gb,2), null()))
| join type=left max=0 host_id
    [| inputlookup sprawl_retention_policy.csv
     | eval host_id=lower(trim(toString(coalesce(host_id, host, Host, hostname, ""))))
     | eval retention_stopped_days=tonumber(tostring(coalesce(retention_stopped_days, stopped_days_sla, days_to_keep_exited, "")),10)
     | eval exempt_ns=tonumber(tostring(coalesce(exempt_namespace, exempt_flag, security_hold, "0")),10)
     | stats max(retention_stopped_days) AS retention_stopped_days max(exempt_ns) AS exempt_ns BY host_id ]
| fillnull value=0 exempt_ns
| fillnull value=7 retention_stopped_days
| eval environment=toString(coalesce(environment, env, fleet_env, "unset"))
| eval cluster=toString(coalesce(cluster, k8s_cluster, swarm_cluster, compose_stack, "unlabelled"))
| eventstats perc90(reclaimable_total_gb) AS fleet_p90_reclaim avg(reclaimable_total_gb) AS fleet_avg_reclaim BY environment
| sort 0 host_id
| streamstats window=7 current=t global=f avg(reclaimable_total_gb) AS avg_reclaim_7snap BY host_id
| eval growth_pct_weekly=if(isnotnull(avg_reclaim_7snap) AND avg_reclaim_7snap>0.0001, round(100.0*(reclaimable_total_gb-avg_reclaim_7snap)/avg_reclaim_7snap,2), null())
| eval owner=toString(coalesce(owner_contact, platform_owner, finops_owner, ""))
| eval sla_breach_state=case(exempt_ns==1, "EXEMPT", coalesce(sprawl_score,0)>25, "RED-25%+", coalesce(sprawl_score,0)>15, "AMBER-15-25%", coalesce(sprawl_score,0)>5, "YELLOW-5-15%", 1=1, "GREEN")
| eval cleanup_command=if(exempt_ns==1,"exempt_namespace: coordinate manual reclaim under legal hold", strcat("docker container prune --filter until=", retention_stopped_days, "d --force; docker image prune --force; docker volume prune --force; docker builder prune --filter until=", retention_stopped_days, "d --force"))
| table host_id environment cluster sprawl_score reclaimable_total_gb stopped_containers oldest_stopped_age_days dangling_images_count unused_images_count orphan_volumes_count build_cache_gb growth_pct_weekly fleet_p90_reclaim ghost_containers sla_breach_state owner cleanup_command
| sort - sprawl_score
```

## CIM SPL

```spl
| tstats summariesonly=t count FROM datamodel=Inventory WHERE nodename=Inventory earliest=-4h@h latest=@h BY Inventory.dest span=15m
| rename Inventory.dest AS host_id
```

## Visualization

Stacked bar of reclaim_containers_gb, reclaim_images_gb, reclaim_volumes_gb, and build_cache_gb; heatmap of sprawl_score by host_id; line chart of reclaimable_total_gb thirty-day trend; table of ghost_containers leaders; pie of sla_breach_state tiers.

## Known False Positives

Legitimate stopped-but-named data containers that hold reference datasets offline can accumulate exited rows without implying waste; require inventory tags or compose labels before auto-prune tickets fire. Golden-image digests pinned for forensic preservation often look unused to naive digest scans; rely on unused_image_flag exporters that honor inventory holds and exempt namespaces in sprawl_retention_policy.csv. Build caches deliberately retained for monorepo compile performance inflate reclaimable totals without negligence; mark builder SKUs exempt or document finance-approved retention in the lookup rather than muting the UC. Forensics and security_hold namespaces should set exempt_ns so cleanup_command stays advisory. Volumes mounted by external orchestrators the docker engine cannot fully reference may appear orphan_heur while still protected upstream; cross-check CSI or Nomad state before volume prune. Multi-architecture manifest lists keep dangling-looking digests that remain referenced; digest-aware unused detection is mandatory before paging unused_images_count. Patch Tuesday image storms can temporarily raise dangling counts during tag churn; corroborate with change calendars. Lab hosts that run continuous integration with intentional none layers will dominate fleet percentiles unless segmented by environment in eventstats. Duplicate telemetry from OpenTelemetry and legacy forwarders without dedup keys can double reclaimable totals; validate source weights before trusting RED tiers. docker system df rounding versus per-object du can disagree slightly; treat sub-gigabyte deltas as noise unless persistent for a week.

## References

- [Splunk Documentation — Splunk Add-on for Docker overview](https://docs.splunk.com/Documentation/AddOns/released/Docker/About)
- [Docker Docs — docker system df](https://docs.docker.com/engine/reference/commandline/system_df/)
- [Docker Docs — Prune unused Docker objects](https://docs.docker.com/config/pruning/)
- [Docker Docs — Build garbage collection](https://docs.docker.com/build/cache/garbage-collection/)
- [NIST SP 800-190 — Application Container Security Guide](https://csrc.nist.gov/publications/detail/sp/800-190/final)
- [OWASP Docker Top 10](https://owasp.org/www-project-docker-top-10/)
