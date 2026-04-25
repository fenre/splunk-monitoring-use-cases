<!-- AUTO-GENERATED from UC-5.5.12.json — DO NOT EDIT -->

---
id: "5.5.12"
title: "BFD Session Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.5.12 · BFD Session Monitoring

## Description

BFD (Bidirectional Forwarding Detection) provides sub-second failure detection between SD-WAN endpoints. A BFD session going down means the tunnel is unusable, and traffic must reroute. Tracking BFD flaps reveals transport instability before it cascades.

## Value

BFD (Bidirectional Forwarding Detection) provides sub-second failure detection between SD-WAN endpoints. A BFD session going down means the tunnel is unusable, and traffic must reroute. Tracking BFD flaps reveals transport instability before it cascades.

## Implementation

Collect BFD session data from vManage. Alert immediately when a BFD session transitions from up to down. Track flap frequency per tunnel; more than 3 flaps in an hour signals an unstable transport that needs carrier engagement. Cross-reference with ISP maintenance schedules.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API.
• Ensure the following data sources are available: vManage BFD sessions, `sourcetype=cisco:sdwan:bfd`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect BFD session data from vManage. Alert immediately when a BFD session transitions from up to down. Track flap frequency per tunnel; more than 3 flaps in an hour signals an unstable transport that needs carrier engagement. Cross-reference with ISP maintenance schedules.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=sdwan sourcetype="cisco:sdwan:bfd"
| where state!="up"
| stats count as flap_count, latest(_time) as last_flap, values(state) as states by local_system_ip, remote_system_ip, local_color, remote_color
| where flap_count > 3
| sort -flap_count
| eval last_flap=strftime(last_flap,"%Y-%m-%d %H:%M:%S")
```

Understanding this SPL

**BFD Session Monitoring** — BFD (Bidirectional Forwarding Detection) provides sub-second failure detection between SD-WAN endpoints. A BFD session going down means the tunnel is unusable, and traffic must reroute. Tracking BFD flaps reveals transport instability before it cascades.

Documented **Data sources**: vManage BFD sessions, `sourcetype=cisco:sdwan:bfd`. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: sdwan; **sourcetype**: cisco:sdwan:bfd. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=sdwan, sourcetype="cisco:sdwan:bfd". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where state!="up"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by local_system_ip, remote_system_ip, local_color, remote_color** so each row reflects one combination of those dimensions.
• Filters the current rows with `where flap_count > 3` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• `eval` defines or adjusts **last_flap** — often to normalize units, derive a ratio, or prepare for thresholds.


Step 3 — Validate
In Cisco vManage, open the monitor or reporting screen that matches this signal (device, tunnel, interface, certificate, flow, or application route) and compare site names, device IPs, and KPIs to the Splunk results for the same range.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (BFD sessions by color/site), Timeline (session state changes), Table (flapping tunnels).

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:bfd"
| where state!="up"
| stats count as flap_count, latest(_time) as last_flap, values(state) as states by local_system_ip, remote_system_ip, local_color, remote_color
| where flap_count > 3
| sort -flap_count
| eval last_flap=strftime(last_flap,"%Y-%m-%d %H:%M:%S")
```

## Visualization

Status grid (BFD sessions by color/site), Timeline (session state changes), Table (flapping tunnels).

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
