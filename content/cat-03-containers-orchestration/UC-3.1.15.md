<!-- AUTO-GENERATED from UC-3.1.15.json — DO NOT EDIT -->

---
id: "3.1.15"
title: "Image Layer Bloat and Pull-Time Analysis"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.1.15 · Image Layer Bloat and Pull-Time Analysis

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*We measure how thick the shipping crate is before it leaves the factory: how many stacked sheets went into the box, how heavy the sealed package really is, and how long it should take to arrive over the road. When the crate breaks the rules for a destination, we flag it early so teams slim the load before anyone waits hours at the loading dock.*

---

## Description

This control is the image-hygiene observability plane at the build and registry edge: it correlates docker history layer counts and cumulative byte contributions from RUN versus COPY, docker inspect compressed sizes and base-image lineage, BuildKit metadata where available, registry HEAD manifest footprints per platform, and measured docker pull durations from cold-cache edge nodes. It predicts pull time from image megabytes versus edge link megabits per second, ranks images against environment-specific ceilings in pull_time_sla.csv, surfaces compression and multi-arch variance when a tag rebuild explodes from tens to hundreds of megabytes, and exposes repeated-layer patterns that hint at non-deduplicated blobs or oversized intermediate stages. UC-3.1.7 remains host-engine sprawl and reclaimable disk on accumulated local stores. UC-3.1.20 stays mirror-server health. UC-3.1.26 stays registry connectivity and pull-failure taxonomies. UC-3.1.10 and UC-3.1.5 remain vulnerability scanner outputs and scanner coverage SLAs. None of those siblings replace normalized layer-count and transfer-cost governance for promoted tags.

## Value

Platform teams gain quantitative answers for FinOps and SRE reviews: which repository tags violate layer-count and megabyte SLAs per environment, how much cold-cache pull time should cost at the edge given realistic WAN throughput, and when a rebuild regresses week over week even before users complain about rollout duration. Golden-image programs receive evidence tying oversized ubuntu or full JDK bases to predictable pull latency, while ML and CUDA teams can document intentional heaviness rather than silent drift. Capacity planning for edge clusters improves when predicted bytes-to-seconds ratios align with measured pull_seconds_avg, highlighting compression regressions or registry geo issues. Audit narratives aligned with container supply-chain hygiene reference continuous telemetry instead of quarterly manual docker history screenshots.

## Implementation

Land docker:image:history, docker:image:inspect, docker:pull:timing, and docker:registry:manifest:head in index=oti_containers via Splunk_TA_docker or HEC from CI and edge collectors; publish lookups/pull_time_sla.csv; schedule container_uc_3_1_15_image_bloat_pull_cost hourly on earliest=-30d@d latest=now; route BLOAT-SEVERE rows to Head of Platform and image owners; archive weekly CSV exports with lookup commit hashes.

## Evidence

Saved search container_uc_3_1_15_image_bloat_pull_cost; lookups/pull_time_sla.csv with git history; weekly CSV exports to a restricted evidence index; cited Splunk Docker add-on documentation, Docker history and multi-stage build guidance, BuildKit reference, NIST SP 800-190, and OWASP Docker Top 10 for control narratives.

## Control test

### Positive scenario

In lab, ingest docker:image:history and docker:image:inspect for an image with layer_count above max_layer_count and total_image_mb above max_image_mb from pull_time_sla.csv for env=lab, add docker:pull:timing above max_pull_seconds, run container_uc_3_1_15_image_bloat_pull_cost, and expect BLOAT-SEVERE or BLOAT-MODERATE with non-null action_required and nineteen-column table output.

### Negative scenario

Ingest inspect and history for a minimal ten-megabyte final image whose layer_count falls below caps with pull timings under max_pull_seconds, ensure lookup caps are generous for the test env, and confirm BLOAT-OK with no escalation fields populated beyond baselines.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this walk-tier control with the container supply-chain architect who signs Dockerfile baselines, the CI platform engineer who enables BuildKit metadata export, and the edge networking lead who documents WAN throughput tables that feed pull_time_sla.csv. UC-3.1.15 is deliberately the build-time and registry-edge bloat axis: layer cardinality, cumulative compressed weight normalized against base lineage, predicted versus measured pull duration, and per-environment SLA breaches. UC-3.1.7 quantifies dangling images, exited containers, and reclaimable graph bytes on engines, not whether a promoted tag is objectively fat for its function. UC-3.1.20 covers mirror latency and cache hit ratios on registry infrastructure. UC-3.1.26 isolates pull failures, throttles, and DNS or TLS faults on the north-south path. UC-3.1.10 ingests vulnerability scanner JSON for CVE triage on content, while UC-3.1.5 governs whether scanners ran at all. This UC does not replace those signals; it answers whether the artifact you intend to ship is expensive to move before runtime policy or CVE severity enters the conversation.

Splunk Enterprise or Splunk Cloud requires indexers sized for four complementary sourcetypes plus optional buildkit and manifest inspect streams. Roles must separate builders who see repository names from executives who may only see percentile dashboards. Service accounts that read registry HEAD endpoints need least-privilege tokens that cannot push. CI systems emitting docker history JSON must scrub secrets from CreatedBy strings when developers accidentally pass build-args containing tokens; prefer structured redaction in the collector before HEC.

Author four ingestion contracts before alert work. docker:image:history must preserve one event per layer or one batched array per image with stable image_key, repository, tag, CreatedBy or instruction, Size in bytes, and a digest or chain identifier so dc counts layers without double-counting missing IDs. docker:image:inspect must carry RepoTags, Architecture, Os, Size or VirtualSize, optional RootFS.Layers length, labels for fleet_env, and a parent base reference when your exporter resolves it. docker:pull:timing must record pull_duration_seconds, repository, tag, edge_node, env, cold_cache boolean, and image digest when available so averages are not polluted by warm-cache pulls unless you filter them. docker:registry:manifest:head must store Content-Length from HEAD responses, requested platform, registry hostname, and tag or digest key so multi-arch manifests can be compared without downloading full blobs.

Lookup pull_time_sla.csv requires columns env, max_layer_count, max_image_mb, max_pull_seconds, and edge_link_mbps. Refresh the CSV when WAN upgrades land or when Kubernetes edge tiers move regions. Version the file in git and attach hashes to evidence exports.

Risk briefing: docker history on multi-stage builds lists instructions from intermediate stages even when the final stage is small; interpreters of alerts must pair history with inspect Size and optional BuildKit metadata to avoid punishing efficient patterns. Multi-arch manifest lists can make a single logical tag appear as several heavyweight platform rows; always carry architecture in the grain. Compression changes, such as registry support for zstd, shift bytes without changing logical layers; track registry feature flags in documentation when severity flaps.

Licensing and volume: history streams are chatty during CI storms. Use summary indexing for daily per-tag rollups after thirty days of raw retention if license pressure appears.

Differentiation recap: host reclaim, mirror health, pull failures, CVE scanners, and this UC are orthogonal facets of one supply chain. This UC focuses on layer bloat and pull-time cost analysis for promoted artifacts.

### Step 2 — Configure data collection

On CI runners, after docker build completes and before promotion, run docker history with JSON formatting or an equivalent API exporter. Pipe results to a small forwarder or curl to HEC with sourcetype=docker:image:history. Include the immutable digest or image ID that ties history rows to inspect rows. For BuildKit, add --metadata-file on buildx builds and ship the JSON as sourcetype=docker:buildkit:metadata for stage-level attribution when you need to separate final stage bytes from intermediate compilers.

On the same runner or a trusted inspector host, run docker image inspect on the promoted digest. Flatten nested JSON so Splunk extracts repository, tag, architecture, size fields, and labels without spath cost explosions. Timestamp events with build completion time, not indexer arrival time, when clocks are trustworthy.

Deploy a read-only registry HEAD agent or sidecar allowed to issue HEAD /v2/{name}/manifests/{reference} with Accept headers for application/vnd.docker.distribution.manifest.v2+json and OCI equivalents, plus manifest list types when you track multi-arch divergence. Map responses to sourcetype=docker:registry:manifest:head with content_length, digest, platform, and latency_ms. Never log authorization headers.

On edge nodes participating in cold-cache drills, wrap docker pull with a timer script that writes JSON lines containing pull_duration_seconds, image reference, edge_node, env, and cache_mode. Ingest as sourcetype=docker:pull:timing. Schedule drills during maintenance windows so production pulls are not starved.

Optional promotion gates can run docker manifest inspect per platform and ingest sourcetype=docker:manifest:inspect for explicit arm64 versus amd64 size comparisons.

Splunk props and transforms should normalize field names, trim registry host prefixes from repository strings consistently, and route quarantined namespaces to non-production indexes when repository paths include customer codenames.

Validation before searches: index=oti_containers sourcetype=docker:image:history earliest=-1h must show non-zero layer rows for a known fat test image; sourcetype=docker:image:inspect must show Size; sourcetype=docker:pull:timing must correlate with a manual timed pull within ten percent on a lab edge; sourcetype=docker:registry:manifest:head must move when you push a new layer blob.

Clock skew beyond thirty seconds between builders, registry agents, and edge nodes distorts last_seen correlation; fix NTP before trusting predict_pull_seconds versus measured averages.

### Step 3 — Create the search and alert

Save the SPL as saved search container_uc_3_1_15_image_bloat_pull_cost with hourly schedule, time range earliest=-30d@d latest=now, and throttle duplicate BLOAT-SEVERE rows per repository tag pair for four hours unless total_image_mb increases by more than fifteen percent inside the same day. Route BLOAT-SEVERE to platform and owning service queues; route BLOAT-MODERATE to weekly hygiene backlog unless env is production edge, where you page during business hours.

Pipeline walkthrough: the comment macro lists indexes, sourcetypes, lookup keys, prediction formula, and streamstats window so operators retune without opening this document. multisearch fans docker:image:history, docker:image:inspect, docker:pull:timing, and docker:registry:manifest:head so one silent exporter does not blank the correlation. The history arm computes layer_count with dc of stable layer tokens, sum_layer_bytes, and run_layer_bytes using a case-insensitive match on instructions beginning with RUN to spotlight heavy command layers. The inspect arm supplies compressed byte totals, architecture, base_image, env labels, and optional rootfs layer hints when history is missing. The pull arm averages measured pull_seconds and counts edge_nodes_seen. The manifest head arm supplies registry-facing byte proxies per repository tag architecture.

The post-multisearch stats stage merges on image_key repository tag, carrying last_seen as the maximum of partial timestamps for freshness sorting. coalesce_mb converts inspect bytes, summed history bytes, or manifest head bytes into total_image_mb with explicit division by 1048576. layer_count falls back to rootfs hints when history dc undercounts because of legacy graph drivers.

join type=left max=0 env wraps inputlookup pull_time_sla.csv as a subsearch join, satisfying governance that SLA rows come from versioned lookups rather than hard-coded thresholds. fillnull guards prevent null comparisons on SLA numerics when a new environment appears; adjust defaults to conservative production caps only after CAB review.

predict_pull_seconds applies total_image_mb times eight divided by edge_link_mbps, a megabit-oriented transfer estimate that operators should calibrate against measured WAN efficiency. pull_seconds_avg coalesces real averages with predictions when edge drills have not run yet so dashboards stay populated.

eventstats perc90(total_image_mb) and perc95(layer_count) BY env place each row in context against its environment distribution before human review.

streamstats window=14 current=t global=f avg(pull_seconds_avg) BY repository tag yields repo_pull_roll_avg as a week-scale drift detector on pull latency when drills repeat.

severity uses case with BLOAT-SEVERE when both layer count and megabytes exceed caps, BLOAT-MODERATE when either dimension or measured pull seconds breach, and BLOAT-OK otherwise. sev_rank supports descending sort without lexical ambiguity.

action_required provides concise remediation hints tied to which clause failed. The closing table projects image_id, repository, tag, architecture, base_image, layer_count, total_image_mb, pull_seconds_avg, predict_pull_seconds, repo_pull_roll_avg, env, layer_sla, image_size_sla, pull_sla, env_p90_image_mb, env_p95_layers, severity, owner, action_required, edge_nodes_seen, and last_seen for nineteen columns, exceeding the ten-column operational minimum.

Fenced SPL for runbooks must match the spl JSON field exactly:

```spl
`comment("UC-3.1.15 Image Layer Bloat and Pull-Time Analysis. Tunables: index=oti_containers; sourcetypes docker:image:history docker:image:inspect docker:pull:timing docker:registry:manifest:head; optional docker:buildkit:metadata docker:manifest:inspect; subsearch join inputlookup pull_time_sla.csv on env for max_layer_count max_image_mb max_pull_seconds edge_link_mbps; predict_pull_seconds = round(total_image_mb*8/edge_link_mbps,2); earliest=-30d@d latest=now; streamstats window=14 BY repository tag for rolling pull average; eventstats perc90 total_image_mb BY env.")`
| multisearch
    [ search index=oti_containers sourcetype="docker:image:history" earliest=-30d@d latest=now
      | eval image_key=lower(trim(toString(coalesce(image_id, imageId, target_image, ImgId, ""))))
      | eval repository=trim(toString(coalesce(repository, repo, Repository, image_repo, "")))
      | eval tag=trim(toString(coalesce(tag, Tag, image_tag, ref_tag, "")))
      | eval instruction=trim(toString(coalesce(created_by, CreatedBy, instruction, layer_cmd, "")))
      | eval layer_token=trim(toString(coalesce(layer_digest, chain_id, layer_id, short_id, "")))
      | eval layer_bytes=tonumber(tostring(coalesce(size_bytes, layer_size_bytes, Size, layer_size, "0")), 10)
      | eval layer_bytes=if(isnull(layer_bytes) OR layer_bytes<0, 0, layer_bytes)
      | stats dc(layer_token) AS layer_count sum(layer_bytes) AS sum_layer_bytes sum(eval(if(match(lower(instruction), "^run"), layer_bytes, 0))) AS run_layer_bytes max(_time) AS hist_last BY image_key repository tag ]
    [ search index=oti_containers sourcetype="docker:image:inspect" earliest=-30d@d latest=now
      | eval image_key=lower(trim(toString(coalesce(image_id, imageId, Id, imageId_short, ""))))
      | eval repository=trim(toString(coalesce(repository, repo, Repository, "")))
      | eval tag=trim(toString(coalesce(tag, Tag, primary_tag, "")))
      | eval env=trim(toString(coalesce(env, fleet_env, deployment_env, environment, "production")))
      | eval architecture=trim(toString(coalesce(architecture, Architecture, image_arch, "")))
      | eval base_image=trim(toString(coalesce(base_image, BaseImage, Parent, rootfs_base, "")))
      | eval inspect_b=tonumber(tostring(coalesce(total_compressed_size, compressed_size, Size, VirtualSize, image_size_bytes, "0")), 10)
      | eval rootfs_layers=tonumber(tostring(coalesce(rootfs_layer_count, RootFS__Layers_mv_count, "")), 10)
      | stats latest(inspect_b) AS inspect_total_b latest(base_image) AS base_image latest(architecture) AS architecture latest(env) AS env latest(rootfs_layers) AS rootfs_layer_hint max(_time) AS insp_last BY image_key repository tag ]
    [ search index=oti_containers sourcetype="docker:pull:timing" earliest=-30d@d latest=now
      | eval image_key=lower(trim(toString(coalesce(image_id, imageId, local_image_id, ""))))
      | eval repository=trim(toString(coalesce(repository, repo, Repository, "")))
      | eval tag=trim(toString(coalesce(tag, Tag, image_tag, "")))
      | eval env=trim(toString(coalesce(env, fleet_env, edge_env, environment, "production")))
      | eval edge_node=lower(trim(toString(coalesce(edge_node, host, hostname, host_id, dest, ""))))
      | eval pull_seconds=tonumber(tostring(coalesce(pull_duration_seconds, pull_seconds, wall_seconds, duration_sec, "")), 10)
      | eval pull_seconds=if(isnull(pull_seconds) OR pull_seconds<0, null(), pull_seconds)
      | stats avg(pull_seconds) AS avg_pull_seconds max(pull_seconds) AS max_pull_seconds dc(edge_node) AS edge_nodes_seen max(_time) AS pull_last BY image_key repository tag env ]
    [ search index=oti_containers sourcetype="docker:registry:manifest:head" earliest=-30d@d latest=now
      | eval repository=trim(toString(coalesce(repository, repo, registry_repo, "")))
      | eval tag=trim(toString(coalesce(tag, Tag, reference, "")))
      | eval architecture=trim(toString(coalesce(architecture, platform, oci_platform, "linux/amd64")))
      | eval head_b=tonumber(tostring(coalesce(manifest_head_bytes, content_length, Content_Length, registry_head_bytes, "0")), 10)
      | stats latest(head_b) AS manifest_head_b max(_time) AS head_last BY repository tag architecture ]
| eval image_key=if(len(image_key)>0, image_key, lower(md5(strcat(repository, ":", tag))))
| stats
    max(layer_count) AS layer_count
    max(sum_layer_bytes) AS sum_layer_bytes
    max(run_layer_bytes) AS run_layer_bytes
    max(inspect_total_b) AS inspect_total_b
    max(rootfs_layer_hint) AS rootfs_layer_hint
    max(base_image) AS base_image
    max(architecture) AS architecture
    max(env) AS env
    avg(avg_pull_seconds) AS pull_seconds_avg
    max(max_pull_seconds) AS pull_seconds_max
    max(manifest_head_b) AS manifest_head_b
    max(hist_last) AS hist_last
    max(insp_last) AS insp_last
    max(pull_last) AS pull_last
    max(head_last) AS head_last
    max(edge_nodes_seen) AS edge_nodes_seen
  BY image_key repository tag
| eval architecture=if(len(architecture)>0, architecture, "linux/amd64")
| eval env=if(len(env)>0, env, "production")
| eval coalesce_mb=round(coalesce(inspect_total_b, sum_layer_bytes, manifest_head_b, 0)/1048576, 4)
| eval total_image_mb=if(coalesce_mb>0, coalesce_mb, round(sum_layer_bytes/1048576, 4))
| eval layer_count=if(isnull(layer_count) OR layer_count<1, coalesce(rootfs_layer_hint, 0), layer_count)
| eval layer_count=if(layer_count<1 AND isnotnull(rootfs_layer_hint), rootfs_layer_hint, layer_count)
| eval last_seen=max(max(hist_last,insp_last),max(pull_last,head_last))
| join type=left max=0 env
    [| inputlookup pull_time_sla.csv
     | eval env=trim(toString(coalesce(env, fleet_env, environment, "")))
     | eval max_layer_count=tonumber(tostring(coalesce(max_layer_count, layer_count_sla, "")), 10)
     | eval max_image_mb=tonumber(tostring(coalesce(max_image_mb, image_mb_cap, "")), 10)
     | eval max_pull_seconds=tonumber(tostring(coalesce(max_pull_seconds, pull_seconds_cap, "")), 10)
     | eval edge_link_mbps=tonumber(tostring(coalesce(edge_link_mbps, edge_mbps, wan_mbps, "")), 10)
     | fields env max_layer_count max_image_mb max_pull_seconds edge_link_mbps ]
| fillnull value=512 max_layer_count
| fillnull value=8192 max_image_mb
| fillnull value=3600 max_pull_seconds
| fillnull value=100 edge_link_mbps
| eval predict_pull_seconds=if(edge_link_mbps>0, round((total_image_mb*8.0)/edge_link_mbps, 2), null())
| eval pull_seconds_avg=coalesce(pull_seconds_avg, predict_pull_seconds)
| eventstats perc90(total_image_mb) AS env_p90_image_mb perc95(layer_count) AS env_p95_layers BY env
| sort 0 + repository + tag + last_seen
| streamstats window=14 current=t global=f avg(pull_seconds_avg) AS repo_pull_roll_avg BY repository tag
| eval layer_sla=max_layer_count
| eval image_size_sla=max_image_mb
| eval pull_sla=max_pull_seconds
| eval owner=trim(toString(coalesce(image_owner, squad, service_owner, platform_team, "platform")))
| eval action_required=case(
    layer_count>max_layer_count AND total_image_mb>max_image_mb, "Rebuild with fewer layers and smaller final stage; switch base; enable zstd where registry supports it.",
    layer_count>max_layer_count, "Collapse instructions, adopt multi-stage final slim stage, remove duplicate RUN assets.",
    total_image_mb>max_image_mb, "Audit COPY/ADD sources, strip build tools from final layer, prefer distroless or minimal base.",
    pull_seconds_avg>max_pull_seconds, "Investigate edge bandwidth, registry distance, and cache warmers; compare predict versus measured pull.",
    true(), "Record baseline; trend week over week.")
| eval severity=case(
    layer_count>max_layer_count AND total_image_mb>max_image_mb, "BLOAT-SEVERE",
    pull_seconds_avg>max_pull_seconds, "BLOAT-MODERATE",
    layer_count>max_layer_count OR total_image_mb>max_image_mb, "BLOAT-MODERATE",
    true(), "BLOAT-OK")
| eval sev_rank=case(severity="BLOAT-SEVERE", 30, severity="BLOAT-MODERATE", 20, true(), 5)
| eval image_id=image_key
| table image_id repository tag architecture base_image layer_count total_image_mb pull_seconds_avg predict_pull_seconds repo_pull_roll_avg env layer_sla image_size_sla pull_sla env_p90_image_mb env_p95_layers severity owner action_required edge_nodes_seen last_seen
| sort - sev_rank - total_image_mb
```

Alert actions: include action_required text, last_seen, and both pull_seconds_avg with predict_pull_seconds so recipients see modeling drift. Attach drilldown links to raw docker:image:history for the same image_key.

Dashboard publishing: scatter of total_image_mb versus layer_count colored by severity, time chart of repo_pull_roll_avg, table of multi-arch pairs with divergent total_image_mb, and base_image treemap for lineage concentration.

Performance: if multisearch cost exceeds Job Inspector budgets, materialize hourly summaries into docker:image:bloat_daily with the same keys and point this search at summaries while retaining raw sourcetypes for investigations.

### Step 4 — Validate

Positive path A — synthetic fat image: build a lab image with thirty layers and a large COPY layer, ingest history and inspect, set pull_time_sla.csv production max_layer_count below the layer count and max_image_mb below the compressed size, run the search, expect BLOAT-SEVERE with both layer_count and total_image_mb beyond caps.

Positive path B — pull SLA only: ingest docker:pull:timing with average sixty seconds while max_pull_seconds in the lookup is thirty, expect BLOAT-MODERATE even when layer_count is within bounds.

Positive path C — prediction sanity: set edge_link_mbps to fifty on a five hundred megabyte image, confirm predict_pull_seconds approximates eighty seconds within rounding tolerance, then compare with a measured cold pull on a throttled lab link.

Positive path D — manifest head movement: push a new blob increasing Content-Length, confirm manifest_head_b drives total_image_mb when inspect events lag, demonstrating registry-side sensitivity.

Positive path E — streamstats drift: send fourteen sequential pull timing events with rising averages, confirm repo_pull_roll_avg increases monotonically in the last rows.

Negative path — slim final stage with verbose history: craft a multi-stage build whose final stage is ten megabytes but history lists many intermediate layers; rely on inspect_total_b dominating total_image_mb and document in the ticket that history layer_count may exceed policy while bytes remain compliant, adjusting SLA interpretation through governance notes rather than muting the detector.

RBAC: readers without oti_containers see zero rows.

Correlation: when severity fires alongside UC-3.1.26 errors, investigate registry path before blaming image weight alone.

### Step 5 — Operationalize & Troubleshoot

Case 1 — multisearch arm silent after CI change: validate sourcetype names in props, replay one HEC payload manually, and confirm ExecProcessor rc=0 lines for the modular input.

Case 2 — total_image_mb near zero while history shows layers: inspect_total_b missing and sum_layer_bytes zero because Size was not extracted; fix transforms to read docker history JSON Size field or switch to rootfs_layer_hint until inspect arrives.

Case 3 — layer_count explodes for distroless-style images: history lists many squashed metadata lines; dedupe using layer_digest tokens and compare with inspect RootFS layer count.

Case 4 — predict_pull_seconds wildly optimistic: edge_link_mbps in the lookup reflects theoretical ISP speed, not lossy VPN; update pull_time_sla.csv with measured iperf floors per env.

Case 5 — streamstats flat: only one timestamp per repository tag in the window; widen earliest or schedule more frequent edge drills.

Case 6 — join misses on env: builder labels use prod while lookup says production; normalize env with a secondary lookup mapping aliases.

Case 7 — manifest_head_b inflated by manifest list JSON: ensure HEAD requests target per-platform digest manifests when policy requires architecture-specific weights.

Case 8 — BLOAT-OK rows still slow at runtime: correlate with UC-3.1.4 and UC-3.1.11 for local extraction CPU or graph driver contention unrelated to registry bytes.

Case 9 — duplicate events double megabytes: CI retries resend history; dedup at ingest with build_id or collapse with stats in a summary.

Case 10 — base_image blank: inspect omit parent; enrich with a nightly registry crawler that writes base lineage into a KV store.

Case 11 — pull_seconds_avg equals prediction always: no real pull events arrived; flag data quality on docker:pull:timing collectors.

Case 12 — severity flaps daily: registry toggles compression; document compression policy and widen throttle windows for the same digest.

Governance: quarterly review pull_time_sla.csv with networking and FinOps; update comment macro when indexes move.

Evidence: weekly CSV of the closing table with lookup commit hash and exporter versions satisfies internal audits when paired with Docker and NIST references.

Training: teach owners that layer count proxies attack surface only loosely; pair with UC-3.1.10 for CVE truth.

FinOps: translate predict_pull_seconds into lost deploy minutes using your standard rollout parallelism.

Security: scrub customer names from repository paths in tickets.

Performance: shift schedule off peak if Job Inspector shows queueing.

Reliability: when registry HEAD agent fails closed, expect missing manifest_head_b without failing open on severity; show data-quality flags in dashboards.

Documentation: keep collector version pins beside pull_time_sla.csv in git.

Escalation: if BLOAT-SEVERE persists after rebuild, escalate to base-image selection review with architecture board.

Closing: Step 5 lists twelve numbered troubleshooting cases covering collector silence, byte extraction gaps, history distortion, throughput assumptions, streamstats sparsity, env normalization, manifest list confusion, runtime-only slowness, duplicate ingest, lineage enrichment, missing pull telemetry, and compression flaps so operators can sustain container_uc_3_1_15_image_bloat_pull_cost long term.


## SPL

```spl
`comment("UC-3.1.15 Image Layer Bloat and Pull-Time Analysis. Tunables: index=oti_containers; sourcetypes docker:image:history docker:image:inspect docker:pull:timing docker:registry:manifest:head; optional docker:buildkit:metadata docker:manifest:inspect; subsearch join inputlookup pull_time_sla.csv on env for max_layer_count max_image_mb max_pull_seconds edge_link_mbps; predict_pull_seconds = round(total_image_mb*8/edge_link_mbps,2); earliest=-30d@d latest=now; streamstats window=14 BY repository tag for rolling pull average; eventstats perc90 total_image_mb BY env.")`
| multisearch
    [ search index=oti_containers sourcetype="docker:image:history" earliest=-30d@d latest=now
      | eval image_key=lower(trim(toString(coalesce(image_id, imageId, target_image, ImgId, ""))))
      | eval repository=trim(toString(coalesce(repository, repo, Repository, image_repo, "")))
      | eval tag=trim(toString(coalesce(tag, Tag, image_tag, ref_tag, "")))
      | eval instruction=trim(toString(coalesce(created_by, CreatedBy, instruction, layer_cmd, "")))
      | eval layer_token=trim(toString(coalesce(layer_digest, chain_id, layer_id, short_id, "")))
      | eval layer_bytes=tonumber(tostring(coalesce(size_bytes, layer_size_bytes, Size, layer_size, "0")), 10)
      | eval layer_bytes=if(isnull(layer_bytes) OR layer_bytes<0, 0, layer_bytes)
      | stats dc(layer_token) AS layer_count sum(layer_bytes) AS sum_layer_bytes sum(eval(if(match(lower(instruction), "^run"), layer_bytes, 0))) AS run_layer_bytes max(_time) AS hist_last BY image_key repository tag ]
    [ search index=oti_containers sourcetype="docker:image:inspect" earliest=-30d@d latest=now
      | eval image_key=lower(trim(toString(coalesce(image_id, imageId, Id, imageId_short, ""))))
      | eval repository=trim(toString(coalesce(repository, repo, Repository, "")))
      | eval tag=trim(toString(coalesce(tag, Tag, primary_tag, "")))
      | eval env=trim(toString(coalesce(env, fleet_env, deployment_env, environment, "production")))
      | eval architecture=trim(toString(coalesce(architecture, Architecture, image_arch, "")))
      | eval base_image=trim(toString(coalesce(base_image, BaseImage, Parent, rootfs_base, "")))
      | eval inspect_b=tonumber(tostring(coalesce(total_compressed_size, compressed_size, Size, VirtualSize, image_size_bytes, "0")), 10)
      | eval rootfs_layers=tonumber(tostring(coalesce(rootfs_layer_count, RootFS__Layers_mv_count, "")), 10)
      | stats latest(inspect_b) AS inspect_total_b latest(base_image) AS base_image latest(architecture) AS architecture latest(env) AS env latest(rootfs_layers) AS rootfs_layer_hint max(_time) AS insp_last BY image_key repository tag ]
    [ search index=oti_containers sourcetype="docker:pull:timing" earliest=-30d@d latest=now
      | eval image_key=lower(trim(toString(coalesce(image_id, imageId, local_image_id, ""))))
      | eval repository=trim(toString(coalesce(repository, repo, Repository, "")))
      | eval tag=trim(toString(coalesce(tag, Tag, image_tag, "")))
      | eval env=trim(toString(coalesce(env, fleet_env, edge_env, environment, "production")))
      | eval edge_node=lower(trim(toString(coalesce(edge_node, host, hostname, host_id, dest, ""))))
      | eval pull_seconds=tonumber(tostring(coalesce(pull_duration_seconds, pull_seconds, wall_seconds, duration_sec, "")), 10)
      | eval pull_seconds=if(isnull(pull_seconds) OR pull_seconds<0, null(), pull_seconds)
      | stats avg(pull_seconds) AS avg_pull_seconds max(pull_seconds) AS max_pull_seconds dc(edge_node) AS edge_nodes_seen max(_time) AS pull_last BY image_key repository tag env ]
    [ search index=oti_containers sourcetype="docker:registry:manifest:head" earliest=-30d@d latest=now
      | eval repository=trim(toString(coalesce(repository, repo, registry_repo, "")))
      | eval tag=trim(toString(coalesce(tag, Tag, reference, "")))
      | eval architecture=trim(toString(coalesce(architecture, platform, oci_platform, "linux/amd64")))
      | eval head_b=tonumber(tostring(coalesce(manifest_head_bytes, content_length, Content_Length, registry_head_bytes, "0")), 10)
      | stats latest(head_b) AS manifest_head_b max(_time) AS head_last BY repository tag architecture ]
| eval image_key=if(len(image_key)>0, image_key, lower(md5(strcat(repository, ":", tag))))
| stats
    max(layer_count) AS layer_count
    max(sum_layer_bytes) AS sum_layer_bytes
    max(run_layer_bytes) AS run_layer_bytes
    max(inspect_total_b) AS inspect_total_b
    max(rootfs_layer_hint) AS rootfs_layer_hint
    max(base_image) AS base_image
    max(architecture) AS architecture
    max(env) AS env
    avg(avg_pull_seconds) AS pull_seconds_avg
    max(max_pull_seconds) AS pull_seconds_max
    max(manifest_head_b) AS manifest_head_b
    max(hist_last) AS hist_last
    max(insp_last) AS insp_last
    max(pull_last) AS pull_last
    max(head_last) AS head_last
    max(edge_nodes_seen) AS edge_nodes_seen
  BY image_key repository tag
| eval architecture=if(len(architecture)>0, architecture, "linux/amd64")
| eval env=if(len(env)>0, env, "production")
| eval coalesce_mb=round(coalesce(inspect_total_b, sum_layer_bytes, manifest_head_b, 0)/1048576, 4)
| eval total_image_mb=if(coalesce_mb>0, coalesce_mb, round(sum_layer_bytes/1048576, 4))
| eval layer_count=if(isnull(layer_count) OR layer_count<1, coalesce(rootfs_layer_hint, 0), layer_count)
| eval layer_count=if(layer_count<1 AND isnotnull(rootfs_layer_hint), rootfs_layer_hint, layer_count)
| eval last_seen=max(max(hist_last,insp_last),max(pull_last,head_last))
| join type=left max=0 env
    [| inputlookup pull_time_sla.csv
     | eval env=trim(toString(coalesce(env, fleet_env, environment, "")))
     | eval max_layer_count=tonumber(tostring(coalesce(max_layer_count, layer_count_sla, "")), 10)
     | eval max_image_mb=tonumber(tostring(coalesce(max_image_mb, image_mb_cap, "")), 10)
     | eval max_pull_seconds=tonumber(tostring(coalesce(max_pull_seconds, pull_seconds_cap, "")), 10)
     | eval edge_link_mbps=tonumber(tostring(coalesce(edge_link_mbps, edge_mbps, wan_mbps, "")), 10)
     | fields env max_layer_count max_image_mb max_pull_seconds edge_link_mbps ]
| fillnull value=512 max_layer_count
| fillnull value=8192 max_image_mb
| fillnull value=3600 max_pull_seconds
| fillnull value=100 edge_link_mbps
| eval predict_pull_seconds=if(edge_link_mbps>0, round((total_image_mb*8.0)/edge_link_mbps, 2), null())
| eval pull_seconds_avg=coalesce(pull_seconds_avg, predict_pull_seconds)
| eventstats perc90(total_image_mb) AS env_p90_image_mb perc95(layer_count) AS env_p95_layers BY env
| sort 0 + repository + tag + last_seen
| streamstats window=14 current=t global=f avg(pull_seconds_avg) AS repo_pull_roll_avg BY repository tag
| eval layer_sla=max_layer_count
| eval image_size_sla=max_image_mb
| eval pull_sla=max_pull_seconds
| eval owner=trim(toString(coalesce(image_owner, squad, service_owner, platform_team, "platform")))
| eval action_required=case(
    layer_count>max_layer_count AND total_image_mb>max_image_mb, "Rebuild with fewer layers and smaller final stage; switch base; enable zstd where registry supports it.",
    layer_count>max_layer_count, "Collapse instructions, adopt multi-stage final slim stage, remove duplicate RUN assets.",
    total_image_mb>max_image_mb, "Audit COPY/ADD sources, strip build tools from final layer, prefer distroless or minimal base.",
    pull_seconds_avg>max_pull_seconds, "Investigate edge bandwidth, registry distance, and cache warmers; compare predict versus measured pull.",
    true(), "Record baseline; trend week over week.")
| eval severity=case(
    layer_count>max_layer_count AND total_image_mb>max_image_mb, "BLOAT-SEVERE",
    pull_seconds_avg>max_pull_seconds, "BLOAT-MODERATE",
    layer_count>max_layer_count OR total_image_mb>max_image_mb, "BLOAT-MODERATE",
    true(), "BLOAT-OK")
| eval sev_rank=case(severity="BLOAT-SEVERE", 30, severity="BLOAT-MODERATE", 20, true(), 5)
| eval image_id=image_key
| table image_id repository tag architecture base_image layer_count total_image_mb pull_seconds_avg predict_pull_seconds repo_pull_roll_avg env layer_sla image_size_sla pull_sla env_p90_image_mb env_p95_layers severity owner action_required edge_nodes_seen last_seen
| sort - sev_rank - total_image_mb
```

## CIM SPL

```spl
| tstats summariesonly=t count FROM datamodel=Inventory WHERE nodename=Inventory earliest=-24h@h latest=@h BY Inventory.dest
| rename Inventory.dest AS edge_node
| appendcols [| tstats summariesonly=t avg(Performance.cpu_load_percent) AS pull_host_cpu FROM datamodel=Performance WHERE nodename=Performance.CPU earliest=-24h@h latest=@h BY Performance.host
| rename Performance.host AS edge_node ]
```

## Visualization

Scatter plot of layer_count versus total_image_mb with severity coloring, time series of repo_pull_roll_avg per repository, bar chart of architecture-specific megabytes for a single tag, table of base_image lineage contributors, and single value tiles for count of BLOAT-SEVERE rows per env.

## Known False Positives

Legitimately large ML and AI training images ship multi-gigabyte model weights; they will breach naive megabyte SLAs until you annotate repository prefixes or owner labels in a governance lookup and align caps per workload class. CUDA and cuDNN stacks often add hundreds of megabytes unrelated to application layer hygiene; treat them as expected heaviness with documented exceptions rather than silent suppression. Full JDK base images exceed slim JRE runtimes by design; compare like with like when setting max_image_mb. Multi-stage builds frequently show high docker history layer counts reflecting intermediate compiler stages even when docker inspect Size remains small; triage with inspect bytes and optional BuildKit metadata before paging teams. Multi-architecture manifest lists can duplicate logical tags per platform; without architecture in the grain, totals appear inflated relative to a single-node pull. Golden-image tags pinned under compliance hold may remain large intentionally; route them through exempt env rows or parallel policy tables instead of disabling the UC. Registry compression upgrades can shrink Content-Length proxies without any Dockerfile change, creating apparent improvement that is not a team accomplishment; note infrastructure changes in tickets. Distroless and minimal bases sometimes under-report intermediate history while still being secure; pair signals. Repeated COPY of the same source without cache mount optimization can look like layer bloat that is actually build-cache miss noise; corroborate with CI cache hit metrics. Security scanning layers added as sidecars may count as extra layers without materially increasing attack surface when they are empty metadata; validate with scanner documentation.

## References

- [Splunk Documentation — Splunk Add-on for Docker overview](https://docs.splunk.com/Documentation/AddOns/released/Docker/About)
- [Docker Docs — docker history](https://docs.docker.com/engine/reference/commandline/history/)
- [Docker Docs — Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker Docs — BuildKit](https://docs.docker.com/build/buildkit/)
- [NIST SP 800-190 — Application Container Security Guide](https://csrc.nist.gov/publications/detail/sp/800-190/final)
- [OWASP Docker Top 10](https://owasp.org/www-project-docker-top-10/)
