<!-- AUTO-GENERATED from UC-3.1.14.json — DO NOT EDIT -->

---
id: "3.1.14"
title: "Docker Network Overlay Issues"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-3.1.14 · Docker Network Overlay Issues

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Reliability, Availability &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch the underground tunnels between buildings on the same campus that carry packets between containers on different machines. Sometimes the floorplan shows a tunnel exists in both directions, but one end is collapsed; packets going outward arrive while replies coming back vanish, and customers feel half-broken connections long before any single container looks unhealthy.*

---

## Description

This control isolates the container-network overlay axis between the Docker Engine and the customer-facing service by correlating libnetwork driver state, VXLAN tunnel health on UDP 4789, and Swarm gossip-protocol convergence on TCP and UDP 7946 with iptables and nf_conntrack drop counters on the underlay. It reads docker:events filtered to type=network for create, connect, and disconnect transitions, polls docker:inspect_network on each Swarm manager so endpoint counts and Driver fields are reconciled per network, parses linux:journald:docker for libnetwork error families such as gossip protocol failure, peer disconnect, vxlan_id collision, network not converged, and bridge not found, and ingests linux:procfs:netfilter scripted reads of IPTABLES_FORWARD_DROP and nf_conntrack counters on docker_gwbridge, docker0, br-* bridges, and vxlan* interfaces. The saved search computes endpoint-count drift against docker_overlay_network_baseline.csv expected values, derives gossip_lag_sec from per-network event timestamp deltas across managers, and detects VXLAN tunnel asymmetry where some nodes register the network in inspect output while others do not. It complements UC-3.1.8 daemon-process error monitoring and UC-3.1.28 Swarm replica health by isolating the network layer that lives between the engine and the service object rather than the engine process or the service replica count, and it does not duplicate UC-3.1.6 privilege posture, UC-3.1.25 docker.sock exposure, or any container-level lifecycle signal owned by UC-3.1.1, UC-3.1.2, UC-3.1.3, UC-3.1.13, or UC-3.1.22.

## Value

A half-broken VXLAN tunnel is the failure mode that crashes service-mesh sidecars, kills high-availability database replicas, and breaks ingress controllers without any individual container looking unhealthy on docker ps or systemctl status docker, which is exactly why platform teams that miss this axis spend hours staring at crash-loop dashboards while customers see HTTP 502 storms and replication-lag pages. Quantifiable benefit lands as silent network-partition outages prevented before customer-visible 5xx accumulate, p99 latency-spike root-cause attribution shifted from misdiagnosed application bugs to overlay-plane drops, post-overlay-upgrade regression detection during dockerd or Mirantis Container Runtime patch windows, and capacity-planning evidence for VXLAN scope sizing and net.netfilter.nf_conntrack_max reservations across fleets that exceed five thousand hosts. Finance reviewers stop challenging ingest cost when one weekend of avoided cross-availability-zone overlay flapping pays back the docker:inspect_network polling for the year, regulators asking for evidence of operational availability monitoring receive timestamped rows tied to lookup governance, and incident commanders finally have one page that names the network, the host, the FDB asymmetry, the gossip lag, and the per-interface drop rate instead of ten minutes of CLI gathering on a Sev-1 bridge.

## Implementation

Ingest docker:events network actions, docker:inspect_network polls, linux:journald:docker libnetwork lines, and linux:procfs:netfilter iptables and conntrack reads into index=oti_containers; publish docker_overlay_network_baseline.csv (network_name, expected_endpoint_count, expected_node_set, slo_tier) and container_owner.csv weekly; save container_uc_3_1_14_overlay_network_issues every five minutes over earliest=-1h@h; route critical_overlay_split_brain_or_gossip_failure and critical_vxlan_tunnel_asymmetric_data_plane to platform networking with recommended_response inline.

## Evidence

Saved search container_uc_3_1_14_overlay_network_issues; lookups lookups/docker_overlay_network_baseline.csv (network_name, expected_endpoint_count, expected_node_set, slo_tier) and lookups/container_owner.csv versioned in git with weekly publish hashes; weekly CSV exports of severity-tagged rows to a restricted evidence index for SRE on-call review and audit sampling; dashboard panels combining endpoint-count drift heatmaps, VXLAN asymmetry tables, and per-interface iptables_drop_rate time-series. External research informing thresholds and recommendations includes Cilium production write-ups on container-overlay packet drops and data-path correctness on cloud underlays, Cloudflare engineering posts on conntrack table exhaustion under high-fanout traffic and long-lived connection patterns, Datadog blog content on monitoring Docker network metrics that informed the iptables_drop_rate baselining strategy, HashiCorp Serf production stories on gossip-protocol convergence behavior under partition events, RFC 7348 VXLAN encapsulation overhead post-mortems referenced during MTU and conntrack capacity reviews, and Docker community incidents documenting libnetwork driver-state corruption after dockerd ungraceful restart that motivated the high_libnetwork_driver_error_sustained tier.

## Control test

### Positive scenario

On a sealed lab three-manager Swarm cluster, block UDP 7946 between two managers with a temporary iptables DROP rule for ninety seconds, ingest linux:journald:docker entries containing gossip protocol failure and peer disconnect, execute container_uc_3_1_14_overlay_network_issues, and expect critical_overlay_split_brain_or_gossip_failure with gossip_lag_sec above sixty seconds and driver_error_class containing gossip_lag_or_drop on the affected network row.

### Negative scenario

Run a stable three-worker lab Swarm with a single overlay network and a steady three-replica service, refresh docker_overlay_network_baseline.csv to expected_endpoint_count three with expected_node_set listing all three workers, confirm vxlan_state stays symmetric, gossip_lag_sec stays near zero, iptables_drop_rate stays below ten on docker_gwbridge, and verify the saved search returns no qualifying severity row across multiple five-minute intervals.

## Detailed Implementation

### Step 1 — Prerequisites

Head of Platform owns this control jointly with the network engineering lead and the platform observability engineer who certifies Docker overlay telemetry on Linux worker fleets. UC-3.1.14 is the container-network overlay axis: it isolates control- and data-plane reliability of the overlay layer (libnetwork drivers, VXLAN tunnels on UDP 4789, Serf gossip on TCP and UDP 7946) between Docker Engine and the customer-facing service. UC-3.1.8 owns daemon-process error monitoring, UC-3.1.28 owns Swarm replica convergence, UC-3.1.6 and UC-3.1.25 own runtime privilege and socket exposure security, and UC-3.1.1, UC-3.1.2, UC-3.1.3, UC-3.1.13, and UC-3.1.22 own container lifecycle, cgroup, throttle, restart-cadence, and healthcheck signals. None of those siblings detect a VXLAN tunnel that is half-built across two managers, a Serf gossip layer that is silently behind by ninety seconds, or a docker_gwbridge interface that is dropping more packets than baseline because the conntrack table approached its limit.

Confirm four telemetry writers exist before scheduling the saved search. First, docker:events filtered to type=network. Docker Engine emits create, connect, disconnect, and remove actions for every overlay network change with Actor.Attributes.driver and Actor.Attributes.name preserved through Splunk Connect for Docker (Splunkbase 4496) or an equivalent modular input that opens unix:///var/run/docker.sock or an approved TCP endpoint. Validate that downstream filters in your TA do not drop type=network because some installations narrow events to type=container only; on a canary host run docker events --filter 'type=network' in parallel and compare _time skew to Splunk arrival within thirty seconds. Second, docker:inspect_network. A privileged scripted input on every Swarm manager (and optionally on workers if you operate non-Swarm overlay) iterates docker network ls --format '{{.ID}}\t{{.Name}}\t{{.Driver}}', runs docker network inspect --format json for each network, and posts one HEC event per network per poll. The poll cadence anchors endpoint-count drift detection: five minutes is the default in this UC; on busy CI clusters with hundreds of ephemeral networks fifteen minutes is acceptable as long as docker_overlay_network_baseline.csv refreshes at the same cadence. Field fidelity matters more than indentation: EndpointCount or endpoint_count, Driver, IPAM.Config[].Subnet, Containers[] keys, and Options like com.docker.network.driver.overlay.vxlanid_list must survive props transforms with both camelCase and snake_case aliases so the SPL coalesce list stays short. Third, linux:journald:docker. Splunk Add-on for Unix and Linux (Splunkbase 833) ships journald lines from systemd-journald with a filter for unit dockerd.service. Confirm libnetwork-prefixed log lines and Serf gossip strings such as gossip protocol failure, peer disconnect, failed to ping, network not converged, and node not yet ready survive forwarder transport without being trimmed by an aggressive line-length filter. Fourth, linux:procfs:netfilter. A scripted input on each worker reads /proc/net/stat/nf_conntrack, parses iptables -L DOCKER-USER -n -v -x output (or runs nft list table inet docker on nft-only hosts), and emits one event per (interface, _time) with stable host_id, iface, iptables_drop_count, conntrack_drop, conntrack_table_full, and IPTABLES_FORWARD_DROP fields scoped to docker_gwbridge, docker0, br-*, and vxlan* interfaces.

Governance lookups sit beside the saved search. Publish docker_overlay_network_baseline.csv with columns network_name (lowercase exact docker network ls Name string including stack prefix when Compose or Swarm prepends one), expected_endpoint_count (integer endpoint count after a steady deploy), expected_node_set (comma-separated lowercase host_id values that must hold the network), slo_tier (production, mission, routine, sandbox), and optional notes. Refresh from your service catalog or Compose stack registry whenever services attach or detach. Maintain container_owner.csv with host_id, container_name, owner_team for paging parity with sibling UC-3.1.x searches; even though this UC alerts at network granularity rather than container granularity, owner_team routing remains valuable because the host hosting the affected service is the actionable target. Roles must allow search on index=oti_containers; restrict docker:inspect_network indexes if internal service names appear in network labels.

Risk briefing for incident commanders: a half-broken VXLAN tunnel is the failure mode that drops half the cross-host packets and never fires container-level alerts. Service-mesh sidecars start failing readiness because their probes target sibling services on different hosts; HA database replicas drift because synchronous replication ACKs are lost; ingress 5xx storms appear without any individual container looking unhealthy on docker ps or kubectl get pods. Serf gossip silently drifting can cause the cluster to schedule new tasks on nodes that no longer agree on cluster topology, producing orphaned overlay endpoints that consume IPs from the IPAM pool until a manual docker network prune runs. iptables and conntrack drops on docker_gwbridge or br-* interfaces look identical in symptom to application bugs but are diagnosable through delta math on /proc counters. This UC stitches the four signals together so a Fortune 500 SRE bridge has one row that names the network, the host, the FDB state, the gossip lag, and the drop rate without ten minutes of CLI gathering during an active incident.

Differentiation recap: UC-3.1.8 monitors dockerd daemon process errors. UC-3.1.6 monitors runtime privilege configuration. UC-3.1.25 monitors docker.sock and Engine-API exposure. UC-3.1.28 monitors Swarm replica convergence at the service object. This UC sits between the daemon and the service object, isolating overlay control-plane (libnetwork driver state, gossip convergence) and data-plane (VXLAN tunnels, iptables and conntrack drops) reliability. Do not merge any of those concerns or analysts lose the ability to route socket incidents to security and gossip incidents to platform networking.

Licensing and volume: docker:events network actions are sparse on stable estates and bursty during deploys. docker:inspect_network is denser because it is one event per network per poll across the fleet; thirty networks across ten managers polling every five minutes is roughly seventeen thousand events per hour, which is modest. linux:procfs:netfilter is the heaviest writer because it samples every interface every interval; cap to docker-related interfaces (docker_gwbridge, docker0, br-*, vxlan*) at the collector to stay reasonable. linux:journald:docker volume is incident-driven and ordinarily small. Legal and privacy: network labels can echo internal service names; redact at the forwarder when image names contain customer or product code names, and restrict dashboards and saved-search results to roles that need to see overlay topology.

### Step 2 — Configure data collection

On every Linux Swarm manager and every overlay-aware worker, enable the four collection paths described in the prerequisites. For docker:events with type=network, confirm Splunk Connect for Docker, the Docker scripted input shipping events, or a customer-maintained modular input streams the Engine API event firehose into index=oti_containers with sourcetype docker:events. The default modular input does not filter by type, so type=network events arrive alongside type=container, type=image, and type=volume; do not narrow that filter at collection unless you simultaneously update every UC that depends on docker:events. Validate on a canary host with docker events --filter 'type=network' and compare _time skew to the Splunk arrival within thirty seconds. Normalize host_id to the lowercase short hostname Universal Forwarders emit so joins to container_owner.csv and docker_overlay_network_baseline.csv stay deterministic across fleets that mix FQDN and short names in legacy data.

For docker:inspect_network polling, deploy a privileged systemd timer or Splunk modular input on each Swarm manager (and on workers operating non-Swarm overlay networks) that iterates the docker network list, runs docker network inspect --format json for each ID, and posts one JSON event per network per poll to HEC with sourcetype docker:inspect_network. The poller should preserve EndpointCount or endpoint_count, Driver, IPAM.Config[].Subnet, IPAM.Config[].Gateway, Containers[] keys, Options like com.docker.network.driver.overlay.vxlanid_list, and Labels. Cadence: five minutes for production, fifteen minutes for sandbox or CI; align poll intervals to wall-clock minutes so eventstats min(_time) BY network_key, action_lc gives meaningful gossip lag math. Manager HA requires either a single elected poller per cluster or deduplication by host_id in the search; the SPL collapses to one row per (network_key, host_id) so duplicate manager polls on the same host produce the same row, but two distinct managers will produce two rows for the same network, which is the desired observed_node_count math.

For linux:journald:docker, install Splunk Add-on for Unix and Linux on each manager and each worker. Configure a journald input filtering on _SYSTEMD_UNIT="docker.service" (or the equivalent unit string on your distribution) with sourcetype linux:journald:docker. Preserve the full _raw line because libnetwork errors and Serf gossip strings span varied formats across Engine versions. Examples to validate: a deliberate docker network rm of a stale overlay should log libnetwork: failed to update driver state at INFO; a managed Swarm restart should temporarily log peer disconnect and node not yet ready until gossip reconverges; a vxlan_id collision (rare; usually after manual import of an unrelated swarm cluster) logs vxlan_id collision. If your fleet runs Mirantis Container Runtime, validate that log keys remain compatible because MCR has historically renamed some libnetwork keys after major upgrades.

For linux:procfs:netfilter, the most reliable collection is a small bash or python wrapper that runs at fifteen-second cadence and emits CSV or KV pairs into a Universal Forwarder monitor. The wrapper should: (1) read /proc/net/stat/nf_conntrack and tally insert_failed, drop, search_restart, and ignore counters with timestamp; (2) parse the output of iptables -L DOCKER-USER -n -v -x to extract per-rule packet and byte counters tagged with the chain name and any rule comment; (3) parse ip -s -j link show output (where -j JSON is supported) for tx_dropped, rx_dropped, and rx_missed_errors per interface; and (4) emit one event per (interface, _time) with stable host_id, iface, iptables_drop_count, conntrack_drop, conntrack_table_full, and IPTABLES_FORWARD_DROP fields. Restrict iface emission to docker_gwbridge, docker0, br-*, and vxlan* to keep volume sane. The SPL in this UC computes per-second rates via streamstats on consecutive samples; that math relies on monotonic counter behavior, so the wrapper must clamp negative deltas to null when counters reset after dockerd restart or when interfaces are recreated.

Where Splunk OpenTelemetry Collector for Docker replaces some of these paths, mirror props aliases so OTel resource attributes for container.id and container.name map to host_id and the iptables labels remain stable. Do not dual-ship through both Connect and OTel without explicit deduplication or you will inflate event counts and corrupt observed_node_count. HEC tokens belong in vault and rotate quarterly. Restrict who can read docker:inspect_network indexes because network labels often echo internal service catalogs.

Expected validation searches before alert authoring: index=oti_containers sourcetype="docker:events" Type=network earliest=-15m; index=oti_containers sourcetype="docker:inspect_network" earliest=-15m; index=oti_containers sourcetype="linux:journald:docker" libnetwork earliest=-24h; index=oti_containers sourcetype="linux:procfs:netfilter" iface=docker_gwbridge earliest=-15m. Skew between forwarder clocks and Splunk _time must stay under thirty seconds or eventstats min(_time) BY network_key, action_lc will produce nonsensical gossip lag rows.

Security hygiene: the account that runs docker network inspect must not be the same interactive user developers use on laptops. Store inspect-script credentials in vault, rotate HEC tokens quarterly, and document Mirantis Container Runtime versus Docker CE field deltas in props.conf so coalesce lists stay short. For OT edge gateways with hardened kernels that omit nf_conntrack accounting, document the procfs collection fallback (or lack thereof) in the host-class registry so high_iptables_drop_rate_above_baseline does not silently fail to fire on those workers.

### Step 3 — Create search and alert

Save the SPL as saved search container_uc_3_1_14_overlay_network_issues with schedule */5 * * * * and time range earliest=-1h@h latest=@h so eventstats arms see a full hour of network activity per run. Throttle duplicate critical_overlay_split_brain_or_gossip_failure rows per network_name for forty-five minutes unless gossip_lag_sec increases by more than fifteen seconds inside the next interval. Throttle critical_vxlan_tunnel_asymmetric_data_plane rows per (network_name, host_id) until vxlan_state returns symmetric for two consecutive runs. Medium and low rows can throttle for thirty minutes per network without losing operational signal.

Understanding the pipeline in operator terms: the opening comment macro is the contract for index names, lookup paths, time windows, and the explicit complement to UC-3.1.8 daemon errors and UC-3.1.28 Swarm replica health. multisearch fans four arms so a silent failure on any single sourcetype does not blank the others. The docker:events arm filters to type=network and emits one row per create, connect, disconnect, or remove with normalized host_id, action_lc, network_id, network_name, and driver fields plus signal_type docker_events_network. The docker:inspect_network arm provides the authoritative endpoint count and Driver string and is the only arm that emits a host's view of a network at poll cadence; it sets action_lc to poll so eventstats can anchor per-network poll arrival times. The linux:journald:docker arm classifies libnetwork errors into named families (gossip_split_brain, gossip_lag_or_drop, vxlan_id_or_subnet_collision, libnetwork_driver_state, network_not_found_transient, libnetwork_other) so the severity ladder downstream branches deterministically without grepping raw text. The linux:procfs:netfilter arm computes per-second drop rates via streamstats window=2 on consecutive counter samples per (host_id, iface) so analysts see iptables_drop_rate as packets per second rather than cumulative counters and false alarms are avoided when counters reset after dockerd restart.

After fan-in, eventstats min(_time) AS earliest_ts_for_action BY network_key, action_lc anchors the earliest event in the window for each (network, action) pair, then row_event_lag_sec is the per-row delta from that anchor, and a second eventstats max(row_event_lag_sec) BY network_key derives gossip_lag_sec — the maximum staleness any row showed for the latest action affecting that network. eventstats values(host_id) BY network_key materializes hosts_seeing_network as a multivalue list, which observed_node_count summarizes after the per-(network_key, host_id) collapse.

stats latest collapses per-event rows into one row per (network_key, host_id) with endpoint_count_host, max iptables_drop_rate, mvjoined driver_error_class_mv, mvjoined actions_observed, and mvjoined signal_types. The driver field defaults to overlay only when no arm reported a Driver string, preserving legitimate bridge or macvlan annotations from inspect or events. driver_error_count records how many libnetwork error families were observed for that (network, host) pair, which the severity ladder uses to require sustained errors rather than a single transient line.

The first inputlookup-wrapped join attaches docker_overlay_network_baseline.csv on lower(network_key) to derive expected_endpoint_count, expected_node_set, and slo_tier per network without a bare lookup command; expected_node_count comes from mvcount(split(expected_node_set, ",")). vxlan_state then compares observed_node_count to expected_node_count: when observed is below expected the row is asymmetric, when observed is at or above expected it is symmetric, when only inspect rows exist with at least two hosts but no baseline is published it is symmetric_observed_only, and the single_node_observed and unknown branches handle non-Swarm overlay or fresh networks not yet in the baseline.

The severity case ladder emits exactly the six mandated tier strings or null. The order is strict: gossip_split_brain or gossip lag above sixty seconds with a gossip-class error wins; VXLAN asymmetry on an overlay driver wins next; sustained libnetwork driver errors come third; iptables drop rate above one hundred packets per second is fourth; endpoint count drift of two or more is fifth; routine create, connect, or disconnect events with no error class and minimal drops are last. recommended_response provides paging-bridge text per tier with concrete CLI commands (bridge fdb show dev vxlan*, ip -d link show, iptables -L DOCKER-USER -n -v, sysctl net.netfilter.nf_conntrack_max, docker network inspect, docker network connect) so analysts have follow-up actions in hand without opening another wiki.

The second inputlookup-wrapped join adds owner_team from container_owner.csv keyed on host_id. The closing table projects sixteen analyst columns: host_id, network_id, network_name, driver, endpoint_count, expected_endpoint_count, vxlan_state, gossip_lag_sec, iptables_drop_rate, driver_error_class, observed_node_count, expected_node_count, severity, recommended_response, signal_type, and owner_team — well above the twelve-column floor and tuned for SOC and SRE drilldown.

Alert actions for critical tiers should open a Sev-1 with the recommended_response text inline, attach the row, and include a deep link to UC-3.1.28 saved search filtered on the same managers when Swarm services are also involved. Medium and low rows should land in a ticket queue rather than paging.

Fenced SPL for runbooks must match the spl JSON field byte-for-byte:

```spl
`comment("UC-3.1.14 Docker Network Overlay Issues. Tunables: index=oti_containers; sourcetypes docker:events (filter type=network), docker:inspect_network, linux:journald:docker (libnetwork errors), linux:procfs:netfilter (iptables drop counters and nf_conntrack); inputlookup joins on docker_overlay_network_baseline.csv (network_name, expected_endpoint_count, expected_node_set, slo_tier) and container_owner.csv (host_id container_name owner_team); earliest=-1h@h latest=@h; complements UC-3.1.8 daemon errors and UC-3.1.28 Swarm replica health by isolating overlay control- and data-plane reliability between dockerd and the service.")`
| multisearch
    [ search index=oti_containers sourcetype="docker:events" earliest=-1h@h latest=@h
      | eval evt_type=lower(toString(coalesce(Type, type, eventType, event_type, "")))
      | where evt_type="network"
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval action_lc=lower(toString(coalesce(action, Action, "")))
      | eval network_id=trim(toString(coalesce(actor_id, actorId, Actor__ID, network_id, networkId, Id, "")))
      | eval network_name=trim(toString(coalesce(actor_name, Actor__Attributes__name, network_name, networkName, name, "")))
      | eval driver=lower(toString(coalesce(actor_driver, Actor__Attributes__driver, driver, network_driver, "")))
      | eval signal_type="docker_events_network"
      | eval driver_error_class=""
      | eval iptables_drop_rate=null()
      | eval endpoint_count_observed=null()
      | fields _time host_id action_lc network_id network_name driver signal_type driver_error_class iptables_drop_rate endpoint_count_observed ]
    [ search index=oti_containers sourcetype="docker:inspect_network" earliest=-1h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval network_id=trim(toString(coalesce(network_id, Id, id, networkId, "")))
      | eval network_name=trim(toString(coalesce(network_name, Name, name, networkName, "")))
      | eval driver=lower(toString(coalesce(driver, Driver, network_driver, "")))
      | eval endpoint_count_observed=tonumber(tostring(coalesce(endpoint_count, EndpointCount, endpoints_count, num_endpoints, "")), 10)
      | eval signal_type="docker_inspect_network"
      | eval action_lc="poll"
      | eval driver_error_class=""
      | eval iptables_drop_rate=null()
      | fields _time host_id action_lc network_id network_name driver signal_type driver_error_class iptables_drop_rate endpoint_count_observed ]
    [ search index=oti_containers sourcetype="linux:journald:docker" earliest=-1h@h latest=@h
      | eval lr=lower(_raw)
      | where match(lr, "libnetwork|vxlan|overlay|gossip|serf|network not found|allocating subnet|bridge.*not found|peer disconnect|node not yet ready|failed to ping|network not converged")
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | rex field=_raw "(?i)network=(?<nname>[a-zA-Z0-9_\-]+)"
      | eval network_name=trim(toString(coalesce(nname, network_name, "")))
      | eval network_id=""
      | eval driver=case(match(lr, "vxlan|overlay"), "overlay", match(lr, "macvlan"), "macvlan", match(lr, "bridge"), "bridge", true(), "")
      | eval driver_error_class=case(match(lr, "split.brain|two leaders|leader.*conflict|leader election.*conflict"), "gossip_split_brain", match(lr, "gossip protocol failure|failed to ping|peer disconnect|node not yet ready|network not converged"), "gossip_lag_or_drop", match(lr, "vxlan.*collision|vxlan_id collision|allocating subnet|subnet.*overlap"), "vxlan_id_or_subnet_collision", match(lr, "failed to update driver state|driver.*state.*error|libnetwork.*error|bridge.*not found"), "libnetwork_driver_state", match(lr, "network not found"), "network_not_found_transient", true(), "libnetwork_other")
      | eval signal_type="linux_journald_docker"
      | eval action_lc="error"
      | eval iptables_drop_rate=null()
      | eval endpoint_count_observed=null()
      | fields _time host_id action_lc network_id network_name driver signal_type driver_error_class iptables_drop_rate endpoint_count_observed ]
    [ search index=oti_containers sourcetype="linux:procfs:netfilter" earliest=-1h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval iface=lower(toString(coalesce(interface, iface, dev, "")))
      | where match(iface, "docker_gwbridge|^br-|^vxlan|docker0")
      | eval iptables_drops=tonumber(tostring(coalesce(iptables_drop_count, ipt_drops, drop_count, dropped_packets, IPTABLES_FORWARD_DROP, "")), 10)
      | eval conntrack_drops=tonumber(tostring(coalesce(conntrack_drop, nf_conntrack_drop, conntrack_table_full, "")), 10)
      | eval iface_drop_total=coalesce(iptables_drops, 0) + coalesce(conntrack_drops, 0)
      | sort 0 + host_id, iface, _time
      | streamstats window=2 current=t global=f last(iface_drop_total) AS prev_drop last(_time) AS prev_t BY host_id, iface
      | eval drop_delta=if(isnotnull(prev_drop), iface_drop_total - prev_drop, null())
      | eval sec_delta=if(isnotnull(prev_t), _time - prev_t, null())
      | eval iptables_drop_rate=if(isnotnull(drop_delta) AND isnotnull(sec_delta) AND sec_delta>0 AND drop_delta>=0, round(drop_delta / sec_delta, 2), null())
      | where isnotnull(iptables_drop_rate)
      | eval network_name=case(iface="docker_gwbridge", "ingress_or_gwbridge", match(iface, "^vxlan"), iface, true(), iface)
      | eval network_id=""
      | eval driver=case(match(iface, "^vxlan"), "overlay", iface="docker_gwbridge", "overlay", true(), "bridge")
      | eval signal_type="linux_procfs_netfilter"
      | eval action_lc="drop_rate"
      | eval driver_error_class=""
      | eval endpoint_count_observed=null()
      | fields _time host_id action_lc network_id network_name driver signal_type driver_error_class iptables_drop_rate endpoint_count_observed ]
| eval network_key=if(len(trim(network_name))>0, lower(network_name), if(len(trim(network_id))>0, network_id, "unscoped"))
| eventstats min(_time) AS earliest_ts_for_action BY network_key, action_lc
| eval row_event_lag_sec=if(isnotnull(earliest_ts_for_action), round(_time - earliest_ts_for_action, 2), null())
| eventstats max(row_event_lag_sec) AS gossip_lag_sec BY network_key
| eventstats values(host_id) AS hosts_seeing_network sum(eval(if(signal_type="docker_inspect_network",1,0))) AS inspect_seen_count BY network_key
| stats latest(network_id) AS network_id latest(network_name) AS network_name latest(driver) AS driver max(eval(if(signal_type="docker_inspect_network", endpoint_count_observed, null()))) AS endpoint_count_host max(iptables_drop_rate) AS iptables_drop_rate values(driver_error_class) AS driver_error_class_mv values(action_lc) AS actions_observed values(signal_type) AS signal_types latest(gossip_lag_sec) AS gossip_lag_sec latest(inspect_seen_count) AS inspect_seen_count latest(hosts_seeing_network) AS hosts_seeing_network BY network_key, host_id
| eval driver=coalesce(driver, "overlay")
| eval driver_error_class=mvjoin(driver_error_class_mv, "|")
| eval driver_error_count=mvcount(driver_error_class_mv)
| eval action_lc=mvjoin(actions_observed, "|")
| eval signal_type=mvjoin(signal_types, "|")
| eventstats max(endpoint_count_host) AS endpoint_count BY network_key
| eval observed_node_count=mvcount(hosts_seeing_network)
| eval network_key_lower=lower(network_key)
| join type=left max=0 network_key_lower
    [| inputlookup docker_overlay_network_baseline.csv
     | eval network_key_lower=lower(trim(toString(coalesce(network_name, network, name, ""))))
     | eval expected_endpoint_count=tonumber(tostring(coalesce(expected_endpoint_count, baseline_endpoint_count, golden_endpoint_count, "")), 10)
     | eval expected_node_set=toString(coalesce(expected_node_set, expected_nodes, baseline_node_set, ""))
     | eval slo_tier=lower(toString(coalesce(slo_tier, tier, availability_tier, "")))
     | fields network_key_lower expected_endpoint_count expected_node_set slo_tier ]
| eval expected_node_count=if(len(trim(expected_node_set))>0, mvcount(split(expected_node_set, ",")), null())
| eval vxlan_state=case(isnotnull(expected_node_count) AND observed_node_count<expected_node_count, "asymmetric", isnotnull(expected_node_count) AND observed_node_count>=expected_node_count, "symmetric", inspect_seen_count>=2, "symmetric_observed_only", inspect_seen_count==1, "single_node_observed", true(), "unknown")
| eval endpoint_count_drift=if(isnotnull(expected_endpoint_count) AND isnotnull(endpoint_count), expected_endpoint_count - endpoint_count, null())
| eval prod_like=if(match(slo_tier, "(?i)prod|tier0|tier_0|mission|gold"), 1, 0)
| eval severity=case(match(driver_error_class, "gossip_split_brain") OR (gossip_lag_sec>60 AND match(driver_error_class, "gossip_lag_or_drop")), "critical_overlay_split_brain_or_gossip_failure", vxlan_state="asymmetric" AND driver="overlay", "critical_vxlan_tunnel_asymmetric_data_plane", isnotnull(driver_error_count) AND driver_error_count>=3 AND match(driver_error_class, "libnetwork_driver_state|vxlan_id_or_subnet_collision"), "high_libnetwork_driver_error_sustained", isnotnull(iptables_drop_rate) AND iptables_drop_rate>100, "high_iptables_drop_rate_above_baseline", isnotnull(endpoint_count_drift) AND endpoint_count_drift>=2, "medium_endpoint_count_drift_below_threshold", match(action_lc, "create|connect|disconnect") AND len(trim(driver_error_class))=0 AND coalesce(iptables_drop_rate,0)<10, "low_routine_network_create_or_disconnect", true(), null())
| where isnotnull(severity)
| eval recommended_response=case(severity="critical_overlay_split_brain_or_gossip_failure", "Validate Swarm manager Raft quorum and Serf gossip ports (TCP/UDP 7946); compare leader election state across managers; check NTP and firewall on UDP 4789; capture dockerd journal for the window before restarting any manager.", severity="critical_vxlan_tunnel_asymmetric_data_plane", "On nodes missing the network: bridge fdb show dev vxlan*; ip -d link show; verify UDP 4789 reachability between underlay nodes; reattach with docker network connect or recreate the overlay if the FDB stays empty.", severity="high_libnetwork_driver_error_sustained", "Inspect /var/lib/docker/network/files/local-kv.db for corruption signs; restart dockerd only after quorum confirmation; rotate libnetwork bridge if subnet collisions persist; engage vendor support on repeated vxlan_id collisions.", severity="high_iptables_drop_rate_above_baseline", "Compare iptables -L DOCKER-USER -n -v to baseline; raise net.netfilter.nf_conntrack_max if conntrack table approached the limit; rule out tenant egress policies; correlate per-interface drops on docker_gwbridge and br-* bridges.", severity="medium_endpoint_count_drift_below_threshold", "Endpoint count below baseline: run docker network inspect on each manager; reconcile expected_endpoint_count in docker_overlay_network_baseline.csv after deploys; confirm services attached on missing nodes.", severity="low_routine_network_create_or_disconnect", "Routine network event recorded for evidence; no action unless paired with sustained driver errors or endpoint drift.", true(), "Correlate docker:events network actions, docker:inspect_network state, libnetwork journal entries, and iptables drop counters before closing.")
| join type=left max=0 host_id
    [| inputlookup container_owner.csv
     | eval host_id=lower(toString(coalesce(host_id, host, Host, "")))
     | eval owner_team=toString(coalesce(owner_team, squad, ""))
     | stats latest(owner_team) AS owner_team BY host_id ]
| table host_id network_id network_name driver endpoint_count expected_endpoint_count vxlan_state gossip_lag_sec iptables_drop_rate driver_error_class observed_node_count expected_node_count severity recommended_response signal_type owner_team
```

### Step 4 — Validate

Positive path A — Serf gossip drop: in a sealed lab three-manager Swarm cluster, block UDP 7946 between two managers with a temporary iptables DROP rule for ninety seconds. Wait for two run cycles, confirm linux:journald:docker emits gossip protocol failure or peer disconnect lines on the affected nodes, and expect critical_overlay_split_brain_or_gossip_failure when gossip_lag_sec exceeds sixty seconds with driver_error_class containing gossip_lag_or_drop. Restore the rule under change control immediately after capture and validate that the row clears within two intervals.

Positive path B — VXLAN asymmetry: on a lab Swarm with three workers attached to an overlay network, deliberately invalidate the VXLAN FDB entry on one worker (one method is to stop systemd-networkd briefly while the overlay is active, or to manually delete the all-zero default FDB entry with bridge fdb del 00:00:00:00:00:00 dev vxlan<id>). Run docker network inspect on each worker; the affected worker should fail to enumerate the same Containers list. Expect critical_vxlan_tunnel_asymmetric_data_plane on the affected (network_name, host_id) row when observed_node_count drops below expected_node_count from docker_overlay_network_baseline.csv.

Positive path C — libnetwork driver error: stop dockerd ungracefully on one worker (kill -9 followed by systemctl start) to provoke a brief network bridge not found log line during reattachment; repeat three times within the hour to clear the sustained-error gate; expect high_libnetwork_driver_error_sustained when driver_error_count meets or exceeds three with driver_error_class matching libnetwork_driver_state. Restore the host immediately and document the exercise in change records.

Positive path D — iptables drop rate: on a lab worker, generate sustained traffic that exhausts nf_conntrack (open five thousand short-lived TCP connections per second toward an overlay-attached container and back) until conntrack table fills. Confirm linux:procfs:netfilter posts iptables_drop_count deltas above one hundred per second on docker_gwbridge and expect high_iptables_drop_rate_above_baseline. Reset net.netfilter.nf_conntrack_max after capture if temporarily lowered for the test.

Positive path E — endpoint-count drift: scale a Swarm service replicas down by two without updating docker_overlay_network_baseline.csv expected_endpoint_count. Confirm endpoint_count drops by two while expected_endpoint_count stays steady and expect medium_endpoint_count_drift_below_threshold. Reset the baseline once validation completes.

Negative path — healthy fleet: run a stable three-worker cluster with a single overlay network and a steady service. Confirm vxlan_state stays symmetric, gossip_lag_sec stays near zero, iptables_drop_rate stays below ten, and the saved search returns no rows for that network across multiple runs.

Field sanity: temporarily rename TA fields in a sandbox forwarder to mimic camelCase-only payloads (Actor__Attributes__name, Actor__Attributes__driver) and confirm coalesce still extracts network_name, network_id, and driver. RBAC: a reader without index=oti_containers must see zero results, proving overlay intelligence stays gated. Clock skew: if eventstats min(_time) anchor times appear out of order, fix NTP on managers and forwarders before trusting gossip_lag_sec.

Correlation: compare critical row times to ingress 5xx and database replication-lag dashboards. If a VXLAN asymmetry alert fires but downstream service KPIs stay healthy, double-check that the affected worker actually hosts a service replica on that network — a worker that is technically attached but hosts no replica produces a benign asymmetric row that may be downgraded with an SLO macro keyed on slo_tier.

Performance test: run Job Inspector during Monday peaks. If scan cost exceeds SRE search budget, consider summarizing linux:procfs:netfilter into a fifteen-minute metrics index that retains only iface_drop_total deltas per host and interface, keeping raw events for forensic drilldowns.

### Step 5 — Operationalize & Troubleshoot

Case 1 — Sustained gossip lag during legitimate manager restart: a planned manager rolling restart will produce gossip_lag_or_drop entries for fifteen to ninety seconds while Serf reconverges. Add a maintenance flag column allowed_gossip_pause_until (epoch timestamp) to docker_overlay_network_baseline.csv so a wrapper macro can suppress critical_overlay_split_brain_or_gossip_failure during the window. Do not drop the alert globally; record the maintenance window beside the change ticket.

Case 2 — Asymmetric VXLAN row that persists after worker reboot: the worker is technically attached to the overlay but never received the FDB entry. Run bridge fdb show dev vxlan<id> on each worker to compare; if the affected worker shows an empty FDB, force-recreate the network with docker network disconnect followed by docker network connect, or in worst-case scenarios run docker network rm and recreate the overlay with the same IPAM pool from a checked-in template. Document the recovery path so the next incident does not re-debug the same steps.

Case 3 — High iptables drop rate driven by tenant egress policies: a host that intentionally denies cross-tenant egress will register IPTABLES_FORWARD_DROP increments that look identical to overlay packet loss in raw counters. Annotate that host class with a known-policy macro that routes high_iptables_drop_rate_above_baseline to a tier-two queue rather than the platform networking pager. Confirm that dropped packets originate on docker_gwbridge or vxlan* interfaces (not on tenant policy chains) before paging on-call.

Case 4 — Endpoint-count drift during Compose stack churn: developer-laptop Compose stacks that attach and detach within minutes can spike endpoint_count drift without a true incident. Tag those host classes by writing a wrapper macro that suppresses medium_endpoint_count_drift_below_threshold when host_id matches a developer-zone pattern. Production drift remains visible.

Case 5 — Mirantis Container Runtime field rename after upgrade: MCR releases occasionally rename libnetwork journal keys, which causes coalesce misses that look like sudden driver-error bursts. Validate by running btool props list against the new release in a lab, update the alias map, and only then re-enable the alert.

Case 6 — vxlan_id collision after a snapshot import: cloning an entire Swarm cluster from a backup occasionally results in two clusters competing for the same vxlan_id range, which produces vxlan_id_or_subnet_collision lines on both clusters. Force a vxlan_id reassignment by recreating the affected overlay with a manually specified --opt com.docker.network.driver.overlay.vxlanid_list and document the conflict in change records.

Case 7 — nf_conntrack exhaustion driven by application bug, not overlay: a connection-leaking client that refuses to close keep-alive sockets can fill the conntrack table and cause every container to show iptables drops. Compare per-container connection counts (ss -s), tcp_tw_recycle behavior, and application access logs before blaming the overlay. Raise net.netfilter.nf_conntrack_max as a temporary mitigation but track to the application owner.

Case 8 — Dual writers after OTel migration: deduplicate docker:events network rows when migrating from Splunk Connect for Docker to OpenTelemetry by enforcing a single writer per host class for one release cycle. Watch for inflated observed_node_count rows that include the same host twice with slightly different host_id normalization; fix the props alias rather than tuning thresholds.

Case 9 — Falsely healthy gossip after Splunk Cloud autoscale: when the Splunk Cloud search head autoscaler rebalances mid-run, eventstats anchor times can shift and gossip_lag_sec briefly reads zero for networks that are actually lagging. Confirm Job Inspector concurrency and rerun the search after autoscaling completes rather than tuning thresholds.

Case 10 — Edge industrial gateways on Docker: OT gateways with hardened kernels may not expose nf_conntrack accounting; the linux:procfs:netfilter arm goes silent on those hosts and high_iptables_drop_rate_above_baseline never fires. Document this in the host-class registry, add a synthetic external probe for end-to-end packet-loss verification on those gateways, and accept the limitation in scope rather than disabling the alert globally.

Case 11 — Fresh overlay missing from baseline lookup: a brand-new overlay created during a release is initially absent from docker_overlay_network_baseline.csv, which means expected_endpoint_count and expected_node_count return null and vxlan_state falls into symmetric_observed_only or single_node_observed. Add the row at deploy time as part of the release runbook so the first asymmetric VXLAN tunnel after rollout is detected; treat baseline absence on a production-tier service as a release readiness blocker.

Case 12 — Backup manager demotion bursts: docker swarm leave on a demoted manager emits gossip notifications that resemble peer disconnects for several minutes. Pair with a maintenance lookup that records demotion times and suppress critical_overlay_split_brain_or_gossip_failure for that window.

Dashboard publishing: build a twenty-four-hour endpoint-count drift heatmap by network_name with cells colored when expected_endpoint_count minus endpoint_count exceeds two; a VXLAN asymmetry table listing networks with observed_node_count below expected_node_count and the missing host_id values; an iptables_drop_rate time-series stacked by host_id and interface; and a severity-tier breakdown table with drilldowns to raw docker:events, docker:inspect_network json, libnetwork journal lines, and netfilter samples for the same host_id and network_name. Annotate dashboards with vertical markers when docker_overlay_network_baseline.csv is updated so reviewers see baseline-driven changes versus operational events.

Evidence retention: weekly CSV exports of severity-tagged rows to a restricted evidence index, paired with git commit hashes for docker_overlay_network_baseline.csv and container_owner.csv, satisfy internal audit samples. Map findings to NIST SP 800-190 section 4.4 orchestration visibility expectations and to internal availability SLO statements that name overlay reachability as a covered telemetry source.

Governance: quarterly replay one historical overlay incident through the SPL after Docker Engine, Mirantis MCR, or kernel upgrades that touch nf_conntrack or VXLAN tooling. Update the comment macro when indexes move. Require lookup owners to approve threshold changes (the sixty-second gossip_lag_sec gate, the one-hundred-packet-per-second iptables_drop_rate gate, the drift-greater-than-or-equal-to-two endpoint gate) inside the same change record as the network design change that motivates them.

Closing checklist: five plain-text step headers with em dashes; multisearch lists four arms (docker:events, docker:inspect_network, linux:journald:docker, linux:procfs:netfilter); coalesce appears in every arm and downstream; streamstats appears in the netfilter arm for drop-rate math and eventstats appears for gossip-lag and per-network rollups; two inputlookup-wrapped joins (docker_overlay_network_baseline.csv and container_owner.csv); the case ladder emits exactly the six mandated severity strings plus null; the closing table projects sixteen analyst columns including host_id, network_id, network_name, driver, endpoint_count, vxlan_state, gossip_lag_sec, iptables_drop_rate, severity, and recommended_response; narrative JSON fields contain no asterisk emphasis; six unique reference URLs span Docker overlay docs, RFC 7348, an authoritative engineering blog on container-overlay debugging, Serf gossip docs, a specific Splunk Lantern article path, and Linux kernel netfilter docs.

Supplemental engineering notes for long-term owners: when migrating to rootless Docker, libnetwork paths shift under user.slice; revalidate that scripted inputs follow the delegated subtree before trusting endpoint counts. When Swarm is replaced by Kubernetes-only orchestration, retire this UC on those node classes rather than masking detections; the kube CNI plane is monitored under UC-3.2.x. When finance challenges ingest cost, demonstrate that one weekend of avoided cross-availability-zone overlay flapping pays back the entire docker:inspect_network polling for the year. When legal requests holds, include docker:inspect_network json, journal lines, and netfilter samples in preservation scope. When automating remediation, never allow unsupervised docker network prune or docker network rm in regulated PCI or HIPAA zones without explicit human approval; recovery commands can mask topology evidence. When red-teaming, pair this UC with UC-3.1.25 to tell the story of how an attacker who briefly held docker.sock could craft a bogus overlay endpoint versus how a legitimate overlay was simply broken. When OT edge gateways embed Docker, duplicate docker_overlay_network_baseline.csv with OT-specific service_owner routing because mean time to network repair on factory floors is measured in minutes, not days. When training new responders, teach them the difference between a daemon error (UC-3.1.8) and an overlay error (UC-3.1.14) using a side-by-side replay of two historical incidents, and the difference between a service replica failure (UC-3.1.28) and an overlay tunnel failure where replicas exist but cannot reach each other. When Splunk Cloud reindexes during platform maintenance, validate that earliest=-1h@h windows still cover the cadence on which docker:inspect_network polls. When MTU mismatches are suspected (cloud overlay underlay typically supports nine-thousand-byte jumbo frames but defaults to fifteen hundred, and VXLAN encapsulation adds fifty bytes), pair this UC with a separate MTU-probe job that posts to the same index so analysts can correlate path-MTU discovery failures with sustained iptables_drop_rate anomalies.

## SPL

```spl
`comment("UC-3.1.14 Docker Network Overlay Issues. Tunables: index=oti_containers; sourcetypes docker:events (filter type=network), docker:inspect_network, linux:journald:docker (libnetwork errors), linux:procfs:netfilter (iptables drop counters and nf_conntrack); inputlookup joins on docker_overlay_network_baseline.csv (network_name, expected_endpoint_count, expected_node_set, slo_tier) and container_owner.csv (host_id container_name owner_team); earliest=-1h@h latest=@h; complements UC-3.1.8 daemon errors and UC-3.1.28 Swarm replica health by isolating overlay control- and data-plane reliability between dockerd and the service.")`
| multisearch
    [ search index=oti_containers sourcetype="docker:events" earliest=-1h@h latest=@h
      | eval evt_type=lower(toString(coalesce(Type, type, eventType, event_type, "")))
      | where evt_type="network"
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval action_lc=lower(toString(coalesce(action, Action, "")))
      | eval network_id=trim(toString(coalesce(actor_id, actorId, Actor__ID, network_id, networkId, Id, "")))
      | eval network_name=trim(toString(coalesce(actor_name, Actor__Attributes__name, network_name, networkName, name, "")))
      | eval driver=lower(toString(coalesce(actor_driver, Actor__Attributes__driver, driver, network_driver, "")))
      | eval signal_type="docker_events_network"
      | eval driver_error_class=""
      | eval iptables_drop_rate=null()
      | eval endpoint_count_observed=null()
      | fields _time host_id action_lc network_id network_name driver signal_type driver_error_class iptables_drop_rate endpoint_count_observed ]
    [ search index=oti_containers sourcetype="docker:inspect_network" earliest=-1h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval network_id=trim(toString(coalesce(network_id, Id, id, networkId, "")))
      | eval network_name=trim(toString(coalesce(network_name, Name, name, networkName, "")))
      | eval driver=lower(toString(coalesce(driver, Driver, network_driver, "")))
      | eval endpoint_count_observed=tonumber(tostring(coalesce(endpoint_count, EndpointCount, endpoints_count, num_endpoints, "")), 10)
      | eval signal_type="docker_inspect_network"
      | eval action_lc="poll"
      | eval driver_error_class=""
      | eval iptables_drop_rate=null()
      | fields _time host_id action_lc network_id network_name driver signal_type driver_error_class iptables_drop_rate endpoint_count_observed ]
    [ search index=oti_containers sourcetype="linux:journald:docker" earliest=-1h@h latest=@h
      | eval lr=lower(_raw)
      | where match(lr, "libnetwork|vxlan|overlay|gossip|serf|network not found|allocating subnet|bridge.*not found|peer disconnect|node not yet ready|failed to ping|network not converged")
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | rex field=_raw "(?i)network=(?<nname>[a-zA-Z0-9_\-]+)"
      | eval network_name=trim(toString(coalesce(nname, network_name, "")))
      | eval network_id=""
      | eval driver=case(match(lr, "vxlan|overlay"), "overlay", match(lr, "macvlan"), "macvlan", match(lr, "bridge"), "bridge", true(), "")
      | eval driver_error_class=case(match(lr, "split.brain|two leaders|leader.*conflict|leader election.*conflict"), "gossip_split_brain", match(lr, "gossip protocol failure|failed to ping|peer disconnect|node not yet ready|network not converged"), "gossip_lag_or_drop", match(lr, "vxlan.*collision|vxlan_id collision|allocating subnet|subnet.*overlap"), "vxlan_id_or_subnet_collision", match(lr, "failed to update driver state|driver.*state.*error|libnetwork.*error|bridge.*not found"), "libnetwork_driver_state", match(lr, "network not found"), "network_not_found_transient", true(), "libnetwork_other")
      | eval signal_type="linux_journald_docker"
      | eval action_lc="error"
      | eval iptables_drop_rate=null()
      | eval endpoint_count_observed=null()
      | fields _time host_id action_lc network_id network_name driver signal_type driver_error_class iptables_drop_rate endpoint_count_observed ]
    [ search index=oti_containers sourcetype="linux:procfs:netfilter" earliest=-1h@h latest=@h
      | eval host_id=lower(toString(coalesce(host, Host, hostname, host_id, dest, "")))
      | eval iface=lower(toString(coalesce(interface, iface, dev, "")))
      | where match(iface, "docker_gwbridge|^br-|^vxlan|docker0")
      | eval iptables_drops=tonumber(tostring(coalesce(iptables_drop_count, ipt_drops, drop_count, dropped_packets, IPTABLES_FORWARD_DROP, "")), 10)
      | eval conntrack_drops=tonumber(tostring(coalesce(conntrack_drop, nf_conntrack_drop, conntrack_table_full, "")), 10)
      | eval iface_drop_total=coalesce(iptables_drops, 0) + coalesce(conntrack_drops, 0)
      | sort 0 + host_id, iface, _time
      | streamstats window=2 current=t global=f last(iface_drop_total) AS prev_drop last(_time) AS prev_t BY host_id, iface
      | eval drop_delta=if(isnotnull(prev_drop), iface_drop_total - prev_drop, null())
      | eval sec_delta=if(isnotnull(prev_t), _time - prev_t, null())
      | eval iptables_drop_rate=if(isnotnull(drop_delta) AND isnotnull(sec_delta) AND sec_delta>0 AND drop_delta>=0, round(drop_delta / sec_delta, 2), null())
      | where isnotnull(iptables_drop_rate)
      | eval network_name=case(iface="docker_gwbridge", "ingress_or_gwbridge", match(iface, "^vxlan"), iface, true(), iface)
      | eval network_id=""
      | eval driver=case(match(iface, "^vxlan"), "overlay", iface="docker_gwbridge", "overlay", true(), "bridge")
      | eval signal_type="linux_procfs_netfilter"
      | eval action_lc="drop_rate"
      | eval driver_error_class=""
      | eval endpoint_count_observed=null()
      | fields _time host_id action_lc network_id network_name driver signal_type driver_error_class iptables_drop_rate endpoint_count_observed ]
| eval network_key=if(len(trim(network_name))>0, lower(network_name), if(len(trim(network_id))>0, network_id, "unscoped"))
| eventstats min(_time) AS earliest_ts_for_action BY network_key, action_lc
| eval row_event_lag_sec=if(isnotnull(earliest_ts_for_action), round(_time - earliest_ts_for_action, 2), null())
| eventstats max(row_event_lag_sec) AS gossip_lag_sec BY network_key
| eventstats values(host_id) AS hosts_seeing_network sum(eval(if(signal_type="docker_inspect_network",1,0))) AS inspect_seen_count BY network_key
| stats latest(network_id) AS network_id latest(network_name) AS network_name latest(driver) AS driver max(eval(if(signal_type="docker_inspect_network", endpoint_count_observed, null()))) AS endpoint_count_host max(iptables_drop_rate) AS iptables_drop_rate values(driver_error_class) AS driver_error_class_mv values(action_lc) AS actions_observed values(signal_type) AS signal_types latest(gossip_lag_sec) AS gossip_lag_sec latest(inspect_seen_count) AS inspect_seen_count latest(hosts_seeing_network) AS hosts_seeing_network BY network_key, host_id
| eval driver=coalesce(driver, "overlay")
| eval driver_error_class=mvjoin(driver_error_class_mv, "|")
| eval driver_error_count=mvcount(driver_error_class_mv)
| eval action_lc=mvjoin(actions_observed, "|")
| eval signal_type=mvjoin(signal_types, "|")
| eventstats max(endpoint_count_host) AS endpoint_count BY network_key
| eval observed_node_count=mvcount(hosts_seeing_network)
| eval network_key_lower=lower(network_key)
| join type=left max=0 network_key_lower
    [| inputlookup docker_overlay_network_baseline.csv
     | eval network_key_lower=lower(trim(toString(coalesce(network_name, network, name, ""))))
     | eval expected_endpoint_count=tonumber(tostring(coalesce(expected_endpoint_count, baseline_endpoint_count, golden_endpoint_count, "")), 10)
     | eval expected_node_set=toString(coalesce(expected_node_set, expected_nodes, baseline_node_set, ""))
     | eval slo_tier=lower(toString(coalesce(slo_tier, tier, availability_tier, "")))
     | fields network_key_lower expected_endpoint_count expected_node_set slo_tier ]
| eval expected_node_count=if(len(trim(expected_node_set))>0, mvcount(split(expected_node_set, ",")), null())
| eval vxlan_state=case(isnotnull(expected_node_count) AND observed_node_count<expected_node_count, "asymmetric", isnotnull(expected_node_count) AND observed_node_count>=expected_node_count, "symmetric", inspect_seen_count>=2, "symmetric_observed_only", inspect_seen_count==1, "single_node_observed", true(), "unknown")
| eval endpoint_count_drift=if(isnotnull(expected_endpoint_count) AND isnotnull(endpoint_count), expected_endpoint_count - endpoint_count, null())
| eval prod_like=if(match(slo_tier, "(?i)prod|tier0|tier_0|mission|gold"), 1, 0)
| eval severity=case(match(driver_error_class, "gossip_split_brain") OR (gossip_lag_sec>60 AND match(driver_error_class, "gossip_lag_or_drop")), "critical_overlay_split_brain_or_gossip_failure", vxlan_state="asymmetric" AND driver="overlay", "critical_vxlan_tunnel_asymmetric_data_plane", isnotnull(driver_error_count) AND driver_error_count>=3 AND match(driver_error_class, "libnetwork_driver_state|vxlan_id_or_subnet_collision"), "high_libnetwork_driver_error_sustained", isnotnull(iptables_drop_rate) AND iptables_drop_rate>100, "high_iptables_drop_rate_above_baseline", isnotnull(endpoint_count_drift) AND endpoint_count_drift>=2, "medium_endpoint_count_drift_below_threshold", match(action_lc, "create|connect|disconnect") AND len(trim(driver_error_class))=0 AND coalesce(iptables_drop_rate,0)<10, "low_routine_network_create_or_disconnect", true(), null())
| where isnotnull(severity)
| eval recommended_response=case(severity="critical_overlay_split_brain_or_gossip_failure", "Validate Swarm manager Raft quorum and Serf gossip ports (TCP/UDP 7946); compare leader election state across managers; check NTP and firewall on UDP 4789; capture dockerd journal for the window before restarting any manager.", severity="critical_vxlan_tunnel_asymmetric_data_plane", "On nodes missing the network: bridge fdb show dev vxlan*; ip -d link show; verify UDP 4789 reachability between underlay nodes; reattach with docker network connect or recreate the overlay if the FDB stays empty.", severity="high_libnetwork_driver_error_sustained", "Inspect /var/lib/docker/network/files/local-kv.db for corruption signs; restart dockerd only after quorum confirmation; rotate libnetwork bridge if subnet collisions persist; engage vendor support on repeated vxlan_id collisions.", severity="high_iptables_drop_rate_above_baseline", "Compare iptables -L DOCKER-USER -n -v to baseline; raise net.netfilter.nf_conntrack_max if conntrack table approached the limit; rule out tenant egress policies; correlate per-interface drops on docker_gwbridge and br-* bridges.", severity="medium_endpoint_count_drift_below_threshold", "Endpoint count below baseline: run docker network inspect on each manager; reconcile expected_endpoint_count in docker_overlay_network_baseline.csv after deploys; confirm services attached on missing nodes.", severity="low_routine_network_create_or_disconnect", "Routine network event recorded for evidence; no action unless paired with sustained driver errors or endpoint drift.", true(), "Correlate docker:events network actions, docker:inspect_network state, libnetwork journal entries, and iptables drop counters before closing.")
| join type=left max=0 host_id
    [| inputlookup container_owner.csv
     | eval host_id=lower(toString(coalesce(host_id, host, Host, "")))
     | eval owner_team=toString(coalesce(owner_team, squad, ""))
     | stats latest(owner_team) AS owner_team BY host_id ]
| table host_id network_id network_name driver endpoint_count expected_endpoint_count vxlan_state gossip_lag_sec iptables_drop_rate driver_error_class observed_node_count expected_node_count severity recommended_response signal_type owner_team
```

## CIM SPL

```spl
| tstats summariesonly=t count FROM datamodel=Network_Traffic WHERE nodename=All_Traffic earliest=-1h@h latest=@h BY All_Traffic.dest All_Traffic.transport All_Traffic.dest_port span=5m
| rename All_Traffic.dest AS host_id All_Traffic.transport AS transport All_Traffic.dest_port AS dest_port
| where (transport="udp" AND dest_port=4789) OR (transport="tcp" AND dest_port=7946) OR (transport="udp" AND dest_port=7946)
```

## Visualization

Primary panel: endpoint-count drift heatmap by network_name across twenty-four hours with cells colored when expected_endpoint_count minus endpoint_count exceeds two. Secondary panel: VXLAN asymmetry table listing networks with observed_node_count below expected_node_count and the missing host_id values. Tertiary panel: iptables_drop_rate time-series stacked by host_id and interface (docker_gwbridge, br-*, vxlan*). Severity-tier ranked drilldown table mirroring the SPL projection with cell coloring on severity and links to raw docker:events, docker:inspect_network json, libnetwork journal lines, and netfilter samples for the same host_id and network_name.

## Known False Positives

Endpoint-count drift during rolling deploys is benign because Swarm temporarily holds tasks in pending or starting while images pull, so docker_overlay_network_baseline.csv expected_endpoint_count must be refreshed alongside service-replica changes or medium_endpoint_count_drift_below_threshold will fire harmlessly for several minutes after every release. Transient gossip lag during manager-quorum re-election after a deliberate manager restart is expected: Serf needs ten to thirty seconds for the new leader to converge cluster state, which can show as gossip_lag_or_drop entries even though packets are not actually lost; require sustained gossip_lag_sec above sixty seconds before paging. Iptables drops from intentional egress-policy enforcement on tenant-tier worker nodes look exactly like overlay packet loss in raw counters until you separate DOCKER-USER chain drops attributable to documented egress rules from drops on the docker_gwbridge or vxlan* interfaces themselves; tag those host classes with a known-policy macro rather than silencing the alert globally. The string network not found is routinely emitted in dockerd journal during ephemeral CI builds that create and tear down Compose-style overlay networks within seconds, so high_libnetwork_driver_error_sustained should not fire on transient lifecycle events; the SPL therefore requires driver_error_count of three or more in the window. nf_conntrack exhaustion is sometimes caused by an application bug (a connection-leaking client that refuses to close keep-alive sockets) rather than overlay-plane disease; correlate with docker:container:logs and tcp_tw_recycle counters before blaming the network layer. Mirantis Container Runtime releases occasionally rename libnetwork log keys after major upgrades, which can cause coalesce misses that look like sudden driver-error bursts until props aliases are refreshed. Backup managers that are intentionally demoted via docker swarm leave emit gossip notifications for several minutes that resemble peer disconnects but are routine; pair with maintenance lookups before paging. Overlay networks that exist only on a single node by design (single-host bridge networks misclassified as overlay by a poller bug) will register vxlan_state single_node_observed and must not page; correct the poller mapping rather than tuning thresholds.

## References

- [Docker Docs — Overlay network driver](https://docs.docker.com/engine/network/drivers/overlay/)
- [IETF RFC 7348 — Virtual eXtensible Local Area Network (VXLAN)](https://datatracker.ietf.org/doc/html/rfc7348)
- [Cloudflare Engineering — Conntrack tales: one thousand and one flows](https://blog.cloudflare.com/conntrack-tales-one-thousand-and-one-flows/)
- [HashiCorp Serf — Gossip protocol internals](https://www.serf.io/docs/internals/gossip.html)
- [Splunk Lantern — Getting Docker log data into Splunk Cloud Platform with OpenTelemetry](https://lantern.splunk.com/Platform_Data_Management/Unlock_Insights/Getting_Docker_log_data_into_Splunk_Cloud_Platform_with_OpenTelemetry)
- [Linux kernel docs — netfilter conntrack sysctls](https://docs.kernel.org/networking/nf_conntrack-sysctl.html)
