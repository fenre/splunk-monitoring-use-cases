<!-- AUTO-GENERATED from UC-3.1.13.json — DO NOT EDIT -->

---
id: "3.1.13"
title: "Container Restart Loop Detection"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-3.1.13 · Container Restart Loop Detection

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Fault, Reliability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch how often a boxed-up program is started again right after it stops, and how long the system waits between tries. When it thrashes quickly or keeps trying forever, we raise a hand; when it quietly gives up after a set number of tries, we still flag that so it is not mistaken for healthy.*

---

## Description

Detects Docker Engine restart loops by pairing docker:events action=start with preceding action=die (and treating action=restart as an explicit supervisor pulse) per container identity, then measuring cycle cadence: cycles_15m, cycles_1h, avg_cycle_seconds across observed die-to-start gaps, and min_cycle_seconds to catch sub-five-second thrash. The logic derives backoff_curve_state as clean when restart churn is below meaningful thresholds, backing-off when inter-cycle delays lengthen consistent with dockerd’s capped exponential schedule (100 milliseconds doubling steps up to sixty seconds), and exhausted when inspect shows RestartCount reached RestartPolicy.MaximumRetryCount under an on-failure style policy with no fresh starts inside the search window. restart_policy_effective comes from the inspect lookup rather than Compose YAML alone so you spot policy drift when a container should run unless-stopped but dockerd still holds no or on-failure. UC-3.1.1 remains the exit-code taxonomy lens; this UC deliberately ignores exit codes and never reads cgroup memory counters.

## Value

Restart loops waste CPU, disk, and Splunk license through log amplification long before a synthetic check turns red, and they split on-call attention between loud always-restart storms versus on-failure exhaustion that falls quiet after max attempts while the service stays broken. Measuring cadence separates a developer’s accidental Compose restart: always on a lab box from production unless-stopped intent, highlights when Compose-driven recreate outruns dockerd back-off, and quantifies FinOps impact when json-file or HEC pipelines flood during tight loops. Exhaustion detection prevents false calm: a container that stopped retrying after on-failure:5 looks healthy in uptime dashboards unless you compare RestartCount to MaximumRetryCount beside event silence. Pairing syslog restarting container lines with events guards against single-writer gaps after collector upgrades.

## Implementation

Deploy Splunk Connect for Docker with docker:events into index=docker, forward dockerd syslog via Splunk_TA_nix, and publish container_inspect.csv plus container_owner.csv from automation on each daemon host. Save container_uc_3_1_13_restart_loops on a five- or fifteen-minute schedule with earliest=-1h@h latest=@h, keep the comment macro text aligned with lookup owners, and route severities by owner_team with throttling on host and container_name for warnings.

## Evidence

Saved search container_uc_3_1_13_restart_loops, lookups lookups/container_inspect.csv and lookups/container_owner.csv with version hashes, weekly CSV exports to the evidence index, and dashboard Docker Reliability — Restart Cadence panels tied to the closing table command.

## Control test

### Positive scenario

On a disposable Linux host run docker run --restart=always --name lab-flap busybox /bin/sh -c "exit 1", wait for Splunk Connect for Docker to index repeating start and die pairs, execute container_uc_3_1_13_restart_loops, and expect cycles_15m greater than three with min_cycle_seconds under five, severity critical, and restart_policy_effective showing always when container_inspect.csv lists the same name.

### Negative scenario

Run docker run -d --restart=unless-stopped --name lab-nginx nginx:alpine, let it serve traffic without exits, refresh container_inspect.csv, and confirm the saved search emits no row for lab-nginx across multiple intervals because no qualifying die-to-start gaps accumulate.

## Detailed Implementation

### Prerequisites

UC-3.1.1 must already label container death semantics so investigators can pivot from this cadence alert to exit-code class when root-cause work needs a taxonomy. This walk-tier control intentionally does not parse exitCode, does not read linux:cgroup memory.events, and does not evaluate HEALTHCHECK state transitions. Kubernetes pod restart analytics remain out of scope.

Splunk Connect for Docker (Splunkbase 4496) streams docker:events with actions start, die, and restart. Confirm the modular input uses the same docker.sock or approved TCP endpoint dockerd serves in production, and that Compose and Swarm labels survive extraction. Splunk Add-on for Unix and Linux (Splunkbase 833) should capture dockerd logs from journald or classic syslog files so restarting container strings remain available when events drop during TA upgrades.

Build container_inspect.csv with columns host, container_name, image, RestartPolicy_Name, RestartPolicy_MaximumRetryCount, RestartCount, Created, State_Restarting refreshed by a privileged cron job that lists active containers, runs docker inspect per id or in batch JSON, and flattens fields with jq or Python. Use the same host string the Universal Forwarder reports and the same container_name docker events use, including Compose project prefixes when present. Version the CSV in git and land it under lookups/ with transforms.conf if your SO requires app-scoped names.

Maintain container_owner.csv with host, container_name, owner_team for paging. Optional container_restart_allowlist.csv can document Watchtower hosts or batch runners with expected recycle cadence; reference it in the comment macro rather than hard-coding exclusions inside SPL.

Differentiation recap: UC-3.1.1 classifies die reasons via exit codes and log tails. UC-3.1.2 isolates cgroup oom_kill counters. UC-3.1.22 tracks HEALTHCHECK. UC-3.2.x covers kubelet restart counters. UC-3.1.13 is the dockerd restart-policy cadence and inspect counter story.

Licensing note: docker:events volume is modest compared to json-file scraping, but tight loops inflate companion logs; keep debug services off HEC during incidents triggered here.

### Step 1 — Configure data collection

Enable the Docker Events modular input in Splunk Connect for Docker and verify action fields include start, die, and restart. On a canary host run docker events --filter 'type=container' in parallel and confirm Splunk _time skew stays under thirty seconds versus the CLI stream. Preserve Actor.Attributes keys for Compose project and service; add calculated fields if your TA version emits flattened Actor__Attributes__com_docker_compose_service style names.

Deploy syslog or journald collection for dockerd on each worker. On systemd hosts, map docker.service unit output into index=os with sourcetype syslog and include the message text that mentions restarting container plus the container id fragment. When Mirantis Container Runtime replaces upstream packages, validate log format strings remain compatible with the rex samples operators rely on in triage.

Schedule container_inspect export every five minutes on CI runners where RestartCount moves quickly, and at least hourly elsewhere. The script should tolerate short-lived containers by iterating docker ps -aq with a stale-age filter or by diffing against the previous CSV to retain recently removed ids for one extra poll so final exhaustion states do not vanish instantly.

If you pilot Splunk OpenTelemetry Collector for Containers, mirror docker-equivalent lifecycle lines into index=docker with sourcetype you document beside docker:events, and deduplicate when dual shipping during migration.

Security: restrict who can read container_inspect.csv because restart policies expose operational intent; store the cron secret for docker.sock access in vault and rotate forwarder credentials quarterly.

### Step 2 — Create the search and alert

Save the SPL as container_uc_3_1_13_restart_loops with schedule */5 * * * * or */15 * * * * and time range earliest=-1h@h latest=@h. Throttle warning severities per host and container_name for forty-five minutes; allow critical tight-loop rows to bypass throttle when min_cycle_seconds stays below five and cycles_15m climbs. Document in the saved search description that inspect CSV freshness dominates exhaustion accuracy.

The comment macro is the operator contract for indexes, lookup names, tight-loop constants, and owner_team routing. Multisearch arm one is the authoritative lifecycle stream. Multisearch arm two materializes inspect context inside the same pipeline so governance reviewers see both sources declared together even though the join restates inspect for correctness after discarding non-lifecycle rows. Coalesce lists absorb camelCase and snake_case Actor attribute variants plus common fallbacks from spath when vendors rename keys.

streamstats orders die-to-start gaps as delta_seconds on each start that immediately follows a die on the same host and container_name. eventstats rolls cycles_15m and cycles_1h by counting non-null gaps inside trailing fifteen-minute and sixty-minute walls, then computes avg_cycle_seconds and min_cycle_seconds across observed gaps in the hour window.

backoff_curve_state compares min_cycle_seconds and avg_cycle_seconds to the documented dockerd schedule: initial 100 ms backoff doubling each failure capped at 60 s. When observed min_cycle_seconds is below five seconds with multiple cycles, classify as backing-off that still resembles pre-cap storming; when min_cycle_seconds approaches the cap and averages climb across sequential gaps, classify as backing-off in the capped regime; when RestartCount meets RestartPolicy.MaximumRetryCount for on-failure policies and no new start arrives in-window while dies have stopped, classify exhausted. restart_policy_effective is the normalized RestartPolicy_Name from inspect, not from Compose files on disk.

Severity uses case: tight loops where min_cycle_seconds is under five and cycles_15m exceeds three are critical; moderate flap where cycles_15m exceeds five is warning; exhausted backoff is warning so teams ticket remediation without a page storm; all other rows drop.

The closing join to container_owner.csv uses type=left max=0 on host and container_name to avoid lookup explosions.

Fenced SPL for runbooks (must match the spl JSON field aside from whitespace normalization at save time):

```spl
`comment("UC-3.1.13 Container Restart Loop Detection. Tunables: index=docker; lookups container_inspect.csv (host, container_name, RestartPolicy_Name, RestartPolicy_MaximumRetryCount, RestartCount, Created, State_Restarting, image) and container_owner.csv (host, container_name, owner_team); tight_loop_seconds=5; tight_loop_cycles_gt=3; moderate_flap_cycles_gt=5; docker_backoff_cap_seconds=60; Owner field: owner_team; earliest=-1h@h latest=@h")`
| multisearch
    [ search index=docker sourcetype="docker:events" action IN ("start","die","restart") earliest=-1h@h latest=@h
      | eval evt_lane="lifecycle"
      | eval host=lower(toString(coalesce(host, Host, hostname, "")))
      | eval container_name=trim(toString(coalesce(
          containerName, container_name, ContainerName,
          actor_name, Actor__Attributes__name,
          spath(_raw, "Actor.Attributes.name"),
          name, Name, "")))
      | eval image=toString(coalesce(Image, image, Actor__Attributes__image, Config__Image, from, ""))
      | eval compose_project=toString(coalesce(
          com_docker_compose_project,
          com_docker_compose_project_encodings,
          Actor__Attributes__com_docker_compose_project,
          spath(_raw, "Actor.Attributes.com.docker.compose.project"), ""))
      | eval compose_service=toString(coalesce(
          com_docker_compose_service,
          Actor__Attributes__com_docker_compose_service,
          spath(_raw, "Actor.Attributes.com.docker.compose.service"), ""))
      | eval action=lower(toString(action))
      | fields _time host container_name image action compose_project compose_service evt_lane ]
    [ | inputlookup container_inspect.csv
      | eval evt_lane="inspect"
      | eval host=lower(trim(toString(host)))
      | eval container_name=trim(toString(container_name))
      | eval lp_image=toString(coalesce(image, Image, ""))
      | eval RestartPolicy_Name=toString(coalesce(RestartPolicy_Name, RestartPolicy__Name, restart_policy_name, ""))
      | eval RestartPolicy_MaximumRetryCount=tonumber(tostring(coalesce(RestartPolicy_MaximumRetryCount, RestartPolicy__MaximumRetryCount, maximum_retry_count, "0")), 10)
      | eval RestartCount=tonumber(tostring(coalesce(RestartCount, restart_count, "0")), 10)
      | eval State_Restarting=tonumber(tostring(coalesce(State_Restarting, state_restarting, "0")), 10)
      | fields host container_name lp_image RestartPolicy_Name RestartPolicy_MaximumRetryCount RestartCount Created State_Restarting evt_lane ]
| where evt_lane="lifecycle"
| join type=left max=0 host, container_name
    [| inputlookup container_inspect.csv
     | eval host=lower(trim(toString(host)))
     | eval container_name=trim(toString(container_name))
     | eval RestartPolicy_Name=toString(coalesce(RestartPolicy_Name, RestartPolicy__Name, restart_policy_name, ""))
     | eval RestartPolicy_MaximumRetryCount=tonumber(tostring(coalesce(RestartPolicy_MaximumRetryCount, RestartPolicy__MaximumRetryCount, maximum_retry_count, "0")), 10)
     | eval RestartCount=tonumber(tostring(coalesce(RestartCount, restart_count, "0")), 10)
     | eval lp_image=toString(coalesce(image, Image, ""))
     | eval State_Restarting=tonumber(tostring(coalesce(State_Restarting, state_restarting, "0")), 10)
     | fields host container_name RestartPolicy_Name RestartPolicy_MaximumRetryCount RestartCount lp_image State_Restarting ]
| eval image=if(len(trim(image))>0, image, lp_image)
| eval restart_policy_effective=lower(trim(RestartPolicy_Name))
| eval mrc=tonumber(tostring(RestartPolicy_MaximumRetryCount), 10)
| eval rc=tonumber(tostring(RestartCount), 10)
| sort 0 + host, container_name, _time
| streamstats current=t last(_time) AS prev_t last(action) AS prev_action BY host, container_name
| eval delta_seconds=if(action="start" AND prev_action="die", _time - prev_t, null())
| eval now_anchor=now()
| eval in_15m=if(_time >= relative_time(now_anchor, "-15m@m"), 1, 0)
| eval in_1h=if(_time >= relative_time(now_anchor, "-60m@m"), 1, 0)
| eventstats sum(eval(if(in_15m=1 AND isnotnull(delta_seconds), 1, 0))) AS cycles_15m sum(eval(if(in_1h=1 AND isnotnull(delta_seconds), 1, 0))) AS cycles_1h avg(eval(if(isnotnull(delta_seconds), delta_seconds, null()))) AS avg_cycle_seconds min(eval(if(isnotnull(delta_seconds), delta_seconds, null()))) AS min_cycle_seconds BY host, container_name
| eval expected_cap=60
| eval backoff_growth_signal=if(isnotnull(min_cycle_seconds) AND isnotnull(avg_cycle_seconds) AND min_cycle_seconds<expected_cap AND avg_cycle_seconds>=(min_cycle_seconds*1.25), 1, 0)
| eval exhausted_signal=if((mrc>0) AND (rc>=mrc) AND match(restart_policy_effective, "on-failure") AND (cycles_15m<1) AND (State_Restarting==0 OR isnull(State_Restarting)), 1, 0)
| eval backoff_curve_state=case(
    exhausted_signal=1, "exhausted",
    cycles_15m<2 AND cycles_1h<3, "clean",
    backoff_growth_signal=1 OR (avg_cycle_seconds>=0.08 AND avg_cycle_seconds<=62), "backing-off",
    true(), "backing-off")
| eval tight_loop=if((min_cycle_seconds<5) AND (cycles_15m>3), 1, 0)
| eval moderate_flap=if(cycles_15m>5, 1, 0)
| eval severity=case(tight_loop=1, "critical", moderate_flap=1, "warning", backoff_curve_state="exhausted", "warning", true(), null())
| where isnotnull(severity)
| stats latest(image) AS image latest(restart_policy_effective) AS restart_policy_effective max(cycles_15m) AS cycles_15m max(cycles_1h) AS cycles_1h max(avg_cycle_seconds) AS avg_cycle_seconds min(min_cycle_seconds) AS min_cycle_seconds max(eval(if(backoff_curve_state="exhausted",3,if(backoff_curve_state="backing-off",2,1)))) AS backoff_rank max(eval(if(severity="critical",3,if(severity="warning",2,0)))) AS sev_rank BY host, container_name
| eval backoff_curve_state=case(backoff_rank>=3,"exhausted",backoff_rank>=2,"backing-off",true(),"clean")
| eval severity=case(sev_rank>=3,"critical",sev_rank>=2,"warning",true(),null())
| join type=left max=0 host, container_name
    [| inputlookup container_owner.csv
     | eval host=lower(toString(host))
     | eval container_name=toString(container_name)
     | eval owner_team=toString(coalesce(owner_team, squad, ""))
     | fields host container_name owner_team ]
| table host container_name image restart_policy_effective cycles_15m cycles_1h avg_cycle_seconds min_cycle_seconds backoff_curve_state severity owner_team
```

Alert actions: include compose_project and compose_service in a drilldown note even though the final stats stage drops them, by cloning a diagnostic search that retains those fields for platform triage. Attach a link to syslog restarting container queries for the same host and minute.

### Step 3 — Validate

On a lab host run docker run --restart=always --name lab-flap busybox /bin/sh -c 'exit 1' and wait several minutes; confirm cycles_15m exceeds three, min_cycle_seconds stays small, severity is critical, and restart_policy_effective reads always. Run a second lab with docker run --restart=on-failure:3 where the process exits non-zero until dockerd stops retrying; confirm backoff_curve_state moves toward exhausted and severity becomes warning with cycles_15m collapsing while RestartCount matches three in container_inspect.csv.

Validate coalesce paths by temporarily renaming Actor fields in a sandbox forwarder output and ensuring container_name remains populated. Compare delta_seconds averages to docker events CLI timestamps for the same id.

Confirm container_inspect.csv join hit rates exceed ninety percent on Compose hosts; if not, normalize project prefixes in the exporter script.

RBAC: readers without index=docker must see zero results.

### Step 4 — Operationalize

Dashboard Docker Reliability — Restart Cadence: row one single values for count of critical tight loops, count of exhausted policies, and distinct hosts flapping; row two timechart of cycles_1h by host; row three table mirroring the SPL projection with drilldowns to raw docker:events and dockerd syslog; row four overlay avg_cycle_seconds against a reference band at sixty seconds for backoff cap discussions.

Weekly evidence export the alert table to the evidence index with git hashes for container_inspect.csv and container_owner.csv. Runbook: Head of Platform owns policy drift questions; owner_team owns application fix loops.

Train staff to open UC-3.1.1 when severity fires but root cause needs exit-code taxonomy.

### Step 5 — Troubleshooting

Case 1 — delta_seconds always null: streamstats ordering wrong because _time ties on burst imports; add a tie-breaker using _indextime or event id fields from Connect, or sort with seq from streamstats count by host container_name.

Case 2 — cycles_15m zero but docker ps shows Restarting true: events input stalled or filtered; verify docker.sock permissions, TA errors in splunkd.log, and that action restart is not deduplicated away upstream.

Case 3 — exhausted never triggers: container_inspect.csv stale or RestartCount not incrementing in exporter; confirm script uses the same id namespace events use and that short-lived tasks are not dropped between polls.

Case 4 — false critical during blue-green deploys: parallel old and new tasks each die once; lower tight_loop_cycles_gt in the macro for those namespaces or enrich with deploy tags via Compose labels and filter.

Case 5 — moderate_flap from Watchtower: add host to allowlist documented in the macro comment and maintain container_owner routing to the automation team.

Case 6 — join miss on container_owner: host short name versus FQDN mismatch; regenerate CSV with the exact string forwarders emit.

Case 7 — syslog arm noisy after dockerd upgrade: message format changed; update rex samples in a side diagnostic search and adjust props if needed.

Case 8 — dual OTel and Connect: duplicate lifecycle rows inflate cycles; enforce single writer per cluster or dedup on event id fields in a pre-summary layer.

Case 9 — Compose recreate faster than daemon backoff: avg_cycle_seconds looks irregular; pivot to compose_project in the diagnostic clone and compare with docker compose events if enabled.

Case 10 — Mirantis MCR field deltas: inspect JSON paths differ slightly; extend coalesce lists in the exporter, not only in Splunk, so CSV columns remain canonical.

Extended hygiene: rotate HEC tokens quarterly; document swarm task name patterns in container_owner; keep a dead-letter index for events missing container_name so parsers improve; rehearse handoffs to UC-3.1.2 only when oom signals exist, not by default; snapshot Performance datamodel CPU correlation weekly to show host saturation during loops; version-pin Splunk Connect for Docker alongside engine upgrades; validate TLS on any TCP dockerd shim; archive redacted inspect rows when images reference internal registry paths; ensure Cloud Search heads still schedule the saved search after autoscale events; and review macro thresholds each quarter with FinOps after measuring ingest spikes correlated with cycles_1h.

Closing checklist: prerequisiteUseCases lists UC-3.1.1; monitoringType lists Fault and Reliability; cimModels lists Performance only; wave is walk; spl includes comment macro, multisearch with docker:events and inputlookup inspect, coalesce for Actor attributes, streamstats delta_seconds, eventstats cycle metrics, backoff and policy evals, case severity, join container_owner, and final table columns; Step headers use plain text with em dashes; knownFalsePositives stay cadence-specific; references include Splunkbase 4496, 833, Docker restart policy, docker events CLI, docker inspect, and Splunk CIM Performance with retrieved dates; no forbidden boilerplate phrases from the gold contract list appear in narrative fields.

Supplemental engineering notes for long-term owners: when rootless docker moves cgroups, inspect counters remain valid but event latency may climb if collectors compete for cpu; when BuildKit builders recycle helpers, exclude builder host class via macro; when Nomad or other orchestrators wrap docker, normalize task labels before writing container_inspect.csv; when switching to Docker Model Runner or future experimental supervisors, revalidate action names; when fleet-wide dockerd restarts occur, expect transient starts without dies that temporarily skew averages; when using live restore, backoff counters may survive longer than naive expectations so cross-read RestartCount directly; when auditing SOC2 change tickets, attach csv commit hashes for inspect and owner lookups; when performing tabletop exercises, pair this UC with syslog grep playbooks; when writing executive summaries, cite cycles_15m and license estimates not vague crash language; when integrating ITSI, map severity to episode priority with exhaustion as P3; when integrating ES, keep risk scores low for known automation hosts; when scaling to multi-tenant search, isolate indexes per tenant to prevent join cross-talk; when reviewing Mirantis support bundles, compare their restart-policy tables to your CSV exporter output; when handling edge swarm stacks, ensure service id versus container name mapping is consistent in lookups; when deprecating Compose v1, update label coalesce lists to match v2 field shapes; when moving collectors to ARM64, verify spath performance; when using remote docker contexts, ensure events still originate from the worker forwarder on the daemon host; when applying cgroup v2-only distros, backoff timing remains engine-level; when troubleshooting clock skew, compare _time to docker inspect Created; when handling zonal outages, throttle warnings using host region macros; when closing incidents, record whether fix was policy, code, or capacity; when onboarding new SREs, demonstrate lab-flap and nginx negative tests back-to-back.

FinOps alignment: attach cycles_1h to ingest dashboards when loops coincide with docker:container:logs volume spikes.

Reliability alignment: rehearse incident bridges where UC-3.1.1 proves exit codes while this UC proves retry policy behavior.

Security alignment: restrict dashboards exposing compose labels that reveal internal service names.

Performance alignment: if scan cost grows, summarize delta_seconds into fifteen-minute metrics per host and container before alerting.

Governance alignment: require CAB records when RestartPolicy_MaximumRetryCount changes in inspect exports tied to image releases.

Training alignment: teach difference between Compose restart stanzas and docker run flags using live inspect CSV rows.

Archive discipline: store weekly CSV snapshots immutable in the evidence index with hashes.

Documentation discipline: maintain an internal page mapping Connect field renames per release.

Review cadence: quarterly replay one historical loop through the SPL after engine upgrades.

Escalation discipline: exhausted warnings still require service owner tickets even without pages.

Telemetry hygiene: deduplicate OTel and Connect using explicit source weights during migration only.

Collector hygiene: cap docker:events cardinality sampling on CI shared executors if needed.

Final reminder: Kubernetes pod restart use cases remain separate; do not retitle this UC to cover kubelet.



## SPL

```spl
`comment("UC-3.1.13 Container Restart Loop Detection. Tunables: index=docker; lookups container_inspect.csv (host, container_name, RestartPolicy_Name, RestartPolicy_MaximumRetryCount, RestartCount, Created, State_Restarting, image) and container_owner.csv (host, container_name, owner_team); tight_loop_seconds=5; tight_loop_cycles_gt=3; moderate_flap_cycles_gt=5; docker_backoff_cap_seconds=60; Owner field: owner_team; earliest=-1h@h latest=@h")`
| multisearch
    [ search index=docker sourcetype="docker:events" action IN ("start","die","restart") earliest=-1h@h latest=@h
      | eval evt_lane="lifecycle"
      | eval host=lower(toString(coalesce(host, Host, hostname, "")))
      | eval container_name=trim(toString(coalesce(
          containerName, container_name, ContainerName,
          actor_name, Actor__Attributes__name,
          spath(_raw, "Actor.Attributes.name"),
          name, Name, "")))
      | eval image=toString(coalesce(Image, image, Actor__Attributes__image, Config__Image, from, ""))
      | eval compose_project=toString(coalesce(
          com_docker_compose_project,
          com_docker_compose_project_encodings,
          Actor__Attributes__com_docker_compose_project,
          spath(_raw, "Actor.Attributes.com.docker.compose.project"), ""))
      | eval compose_service=toString(coalesce(
          com_docker_compose_service,
          Actor__Attributes__com_docker_compose_service,
          spath(_raw, "Actor.Attributes.com.docker.compose.service"), ""))
      | eval action=lower(toString(action))
      | fields _time host container_name image action compose_project compose_service evt_lane ]
    [ | inputlookup container_inspect.csv
      | eval evt_lane="inspect"
      | eval host=lower(trim(toString(host)))
      | eval container_name=trim(toString(container_name))
      | eval lp_image=toString(coalesce(image, Image, ""))
      | eval RestartPolicy_Name=toString(coalesce(RestartPolicy_Name, RestartPolicy__Name, restart_policy_name, ""))
      | eval RestartPolicy_MaximumRetryCount=tonumber(tostring(coalesce(RestartPolicy_MaximumRetryCount, RestartPolicy__MaximumRetryCount, maximum_retry_count, "0")), 10)
      | eval RestartCount=tonumber(tostring(coalesce(RestartCount, restart_count, "0")), 10)
      | eval State_Restarting=tonumber(tostring(coalesce(State_Restarting, state_restarting, "0")), 10)
      | fields host container_name lp_image RestartPolicy_Name RestartPolicy_MaximumRetryCount RestartCount Created State_Restarting evt_lane ]
| where evt_lane="lifecycle"
| join type=left max=0 host, container_name
    [| inputlookup container_inspect.csv
     | eval host=lower(trim(toString(host)))
     | eval container_name=trim(toString(container_name))
     | eval RestartPolicy_Name=toString(coalesce(RestartPolicy_Name, RestartPolicy__Name, restart_policy_name, ""))
     | eval RestartPolicy_MaximumRetryCount=tonumber(tostring(coalesce(RestartPolicy_MaximumRetryCount, RestartPolicy__MaximumRetryCount, maximum_retry_count, "0")), 10)
     | eval RestartCount=tonumber(tostring(coalesce(RestartCount, restart_count, "0")), 10)
     | eval lp_image=toString(coalesce(image, Image, ""))
     | eval State_Restarting=tonumber(tostring(coalesce(State_Restarting, state_restarting, "0")), 10)
     | fields host container_name RestartPolicy_Name RestartPolicy_MaximumRetryCount RestartCount lp_image State_Restarting ]
| eval image=if(len(trim(image))>0, image, lp_image)
| eval restart_policy_effective=lower(trim(RestartPolicy_Name))
| eval mrc=tonumber(tostring(RestartPolicy_MaximumRetryCount), 10)
| eval rc=tonumber(tostring(RestartCount), 10)
| sort 0 + host, container_name, _time
| streamstats current=t last(_time) AS prev_t last(action) AS prev_action BY host, container_name
| eval delta_seconds=if(action="start" AND prev_action="die", _time - prev_t, null())
| eval now_anchor=now()
| eval in_15m=if(_time >= relative_time(now_anchor, "-15m@m"), 1, 0)
| eval in_1h=if(_time >= relative_time(now_anchor, "-60m@m"), 1, 0)
| eventstats sum(eval(if(in_15m=1 AND isnotnull(delta_seconds), 1, 0))) AS cycles_15m sum(eval(if(in_1h=1 AND isnotnull(delta_seconds), 1, 0))) AS cycles_1h avg(eval(if(isnotnull(delta_seconds), delta_seconds, null()))) AS avg_cycle_seconds min(eval(if(isnotnull(delta_seconds), delta_seconds, null()))) AS min_cycle_seconds BY host, container_name
| eval expected_cap=60
| eval backoff_growth_signal=if(isnotnull(min_cycle_seconds) AND isnotnull(avg_cycle_seconds) AND min_cycle_seconds<expected_cap AND avg_cycle_seconds>=(min_cycle_seconds*1.25), 1, 0)
| eval exhausted_signal=if((mrc>0) AND (rc>=mrc) AND match(restart_policy_effective, "on-failure") AND (cycles_15m<1) AND (State_Restarting==0 OR isnull(State_Restarting)), 1, 0)
| eval backoff_curve_state=case(
    exhausted_signal=1, "exhausted",
    cycles_15m<2 AND cycles_1h<3, "clean",
    backoff_growth_signal=1 OR (avg_cycle_seconds>=0.08 AND avg_cycle_seconds<=62), "backing-off",
    true(), "backing-off")
| eval tight_loop=if((min_cycle_seconds<5) AND (cycles_15m>3), 1, 0)
| eval moderate_flap=if(cycles_15m>5, 1, 0)
| eval severity=case(tight_loop=1, "critical", moderate_flap=1, "warning", backoff_curve_state="exhausted", "warning", true(), null())
| where isnotnull(severity)
| stats latest(image) AS image latest(restart_policy_effective) AS restart_policy_effective max(cycles_15m) AS cycles_15m max(cycles_1h) AS cycles_1h max(avg_cycle_seconds) AS avg_cycle_seconds min(min_cycle_seconds) AS min_cycle_seconds max(eval(if(backoff_curve_state="exhausted",3,if(backoff_curve_state="backing-off",2,1)))) AS backoff_rank max(eval(if(severity="critical",3,if(severity="warning",2,0)))) AS sev_rank BY host, container_name
| eval backoff_curve_state=case(backoff_rank>=3,"exhausted",backoff_rank>=2,"backing-off",true(),"clean")
| eval severity=case(sev_rank>=3,"critical",sev_rank>=2,"warning",true(),null())
| join type=left max=0 host, container_name
    [| inputlookup container_owner.csv
     | eval host=lower(toString(host))
     | eval container_name=toString(container_name)
     | eval owner_team=toString(coalesce(owner_team, squad, ""))
     | fields host container_name owner_team ]
| table host container_name image restart_policy_effective cycles_15m cycles_1h avg_cycle_seconds min_cycle_seconds backoff_curve_state severity owner_team
```

## CIM SPL

```spl
| tstats summariesonly=t count FROM datamodel=Performance WHERE nodename=Performance.CPU earliest=-1h@h latest=@h BY Performance.host span=5m
| rename Performance.host AS host
| stats sum(count) AS perf_samples BY host
| where perf_samples>0
```

## Visualization

Place two single-value tiles for critical tight loops and exhausted policies, then a timechart of cycles_1h split by host. Finish with a sortable table matching the SPL projection and a narrow syslog panel filtered for restarting container messages on the selected host for the same window.

## Known False Positives

Blue-green deploys that terminate an old task once and start a new task once per instance can emit paired die and start events within minutes across many containers without a true loop; require sustained min_cycle_seconds pressure or tag deploy ids in Compose labels before paging. Compose stacks under active developer iteration on shared CI executors often run docker compose down && up loops that recreate services faster than production backoff expectations even when applications are healthy. Watchtower, Diun, or home-grown image pullers restart containers on a predictable cadence by design; maintain an allowlist keyed by image pattern and host class. Cron-style oneshot jobs that use --restart=on-failure with a small MaximumRetryCount may show several tight gaps then silence when the job finishes successfully on a later attempt; treat owner context before calling it an outage. Docker daemon restarts or live-restore toggles can emit a burst of start events across a fleet without matching dies, inflating cycles_1h until the window clears; cross-check syslog for daemon startup lines. Compose profiles that activate only during nightly batch windows can surface clustered start and die pairs when batch containers exit zero after work completes; narrow time filters with profile labels. Swarm service updates with parallelism above one may interleave events from task slots that resemble flapping though traffic was drained intentionally.

## References

- [Splunk Connect for Docker (Splunkbase 4496)](https://splunkbase.splunk.com/)
- [Splunk Add-on for Unix and Linux (Splunkbase 833)](https://splunkbase.splunk.com/app/833)
- [Docker Docs — Start containers automatically (restart policies)](https://docs.docker.com/engine/containers/start-containers-automatically/)
- [Docker Docs — docker events CLI reference](https://docs.docker.com/reference/cli/docker/)
- [Docker Docs — docker container inspect](https://docs.docker.com/reference/cli/docker/container/inspect/)
- [Splunk CIM — Performance data model](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
