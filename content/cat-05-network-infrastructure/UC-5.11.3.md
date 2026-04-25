<!-- AUTO-GENERATED from UC-5.11.3.json — DO NOT EDIT -->

---
id: "5.11.3"
title: "BGP Peer State Change Detection via ON_CHANGE"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.11.3 · BGP Peer State Change Detection via ON_CHANGE

## Description

Syslog-based BGP monitoring depends on log forwarding latency and parsing reliability. gNMI ON_CHANGE subscriptions to BGP neighbor state deliver sub-second notification when a peer leaves Established — faster than syslog and with structured data. For VXLAN EVPN fabrics where BGP is both underlay and overlay, a single peer drop can black-hole tenant traffic within seconds.

## Value

Syslog-based BGP monitoring depends on log forwarding latency and parsing reliability. gNMI ON_CHANGE subscriptions to BGP neighbor state deliver sub-second notification when a peer leaves Established — faster than syslog and with structured data. For VXLAN EVPN fabrics where BGP is both underlay and overlay, a single peer drop can black-hole tenant traffic within seconds.

## Implementation

Subscribe to `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state` using `subscription_mode = "on_change"`. BGP session state is represented as integer (1=Idle through 6=Established). Alert on any state != 6 (Established). For Cisco IOS XR, use native YANG path `Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance`. Correlate with interface flaps (UC-5.11.1) and optical health (UC-5.11.5) for root cause.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Telegraf (`inputs.gnmi` plugin) → Splunk HEC.
• Ensure the following data sources are available: gNMI path: `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state` (ON_CHANGE), Telegraf metric: `openconfig_bgp`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Subscribe to `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state` using `subscription_mode = "on_change"`. BGP session state is represented as integer (1=Idle through 6=Established). Alert on any state != 6 (Established). For Cisco IOS XR, use native YANG path `Cisco-IOS-XR-ipv4-bgp-oper:bgp/instances/instance`. Correlate with interface flaps (UC-5.11.1) and optical health (UC-5.11.5) for root cause.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| mstats latest("openconfig_bgp.session_state") AS state WHERE index=gnmi_metrics BY host, neighbor_address span=1m
| where state != 6
| eval state_label=case(state=1, "Idle", state=2, "Connect", state=3, "Active", state=4, "OpenSent", state=5, "OpenConfirm", state=6, "Established", 1=1, "Unknown")
| table _time, host, neighbor_address, state_label
| sort -_time
```

Understanding this SPL

**BGP Peer State Change Detection via ON_CHANGE** — Syslog-based BGP monitoring depends on log forwarding latency and parsing reliability. gNMI ON_CHANGE subscriptions to BGP neighbor state deliver sub-second notification when a peer leaves Established — faster than syslog and with structured data. For VXLAN EVPN fabrics where BGP is both underlay and overlay, a single peer drop can black-hole tenant traffic within seconds.

Documented **Data sources**: gNMI path: `/network-instances/network-instance/protocols/protocol/bgp/neighbors/neighbor/state` (ON_CHANGE), Telegraf metric: `openconfig_bgp`. **App/TA** (typical add-on context): Telegraf (`inputs.gnmi` plugin) → Splunk HEC. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gnmi_metrics.

**Pipeline walkthrough**

• Uses `mstats` to query metrics indexes (pre-aggregated metric data).
• Filters the current rows with `where state != 6` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **state_label** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **BGP Peer State Change Detection via ON_CHANGE**): table _time, host, neighbor_address, state_label
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

CIM and metrics: BGP state here is gNMI ON_CHANGE in a **metrics** index. Route-protocol state is not a standard CIM dataset; do not expect `tstats` on built-in CIM for this.


Step 3 — Validate
On the router, `show bgp` / equivalent for the neighbor and confirm state is down when the metric leaves Established; capture one maintenance window to avoid paging planned work.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (BGP peer matrix — green=Established, red=down), Timeline (state change events), Table (non-established peers).

## SPL

```spl
| mstats latest("openconfig_bgp.session_state") AS state WHERE index=gnmi_metrics BY host, neighbor_address span=1m
| where state != 6
| eval state_label=case(state=1, "Idle", state=2, "Connect", state=3, "Active", state=4, "OpenSent", state=5, "OpenConfirm", state=6, "Established", 1=1, "Unknown")
| table _time, host, neighbor_address, state_label
| sort -_time
```

## Visualization

Status grid (BGP peer matrix — green=Established, red=down), Timeline (state change events), Table (non-established peers).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
