<!-- AUTO-GENERATED from UC-5.2.4.json — DO NOT EDIT -->

---
id: "5.2.4"
title: "VPN Tunnel Status"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.4 · VPN Tunnel Status

## Description

VPN failures isolate remote sites or users. Proactive monitoring prevents "the VPN is down" calls.

## Value

VPN failures isolate remote sites or users. Proactive monitoring prevents "the VPN is down" calls.

## Implementation

Forward VPN logs. Alert on tunnel down events. Track flapping. Dashboard showing all tunnels.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX).
• Ensure the following data sources are available: Firewall VPN/system logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward VPN logs. Alert on tunnel down events. Track flapping. Dashboard showing all tunnels.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall ("tunnel" OR "IPSec" OR "IKE") ("down" OR "failed" OR "established")
| rex "(?<tunnel_peer>\d+\.\d+\.\d+\.\d+)"
| eval status=if(match(_raw,"established|up"),"Up","Down")
| stats latest(status) as state by host, tunnel_peer | where state="Down"
```

Understanding this SPL

**VPN Tunnel Status** — VPN failures isolate remote sites or users. Proactive monitoring prevents "the VPN is down" calls.

Documented **Data sources**: Firewall VPN/system logs. **App/TA** (typical add-on context): `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall.

**Pipeline walkthrough**

• Scopes the data: index=firewall. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `eval` defines or adjusts **status** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, tunnel_peer** so each row reflects one combination of those dimensions.
• Filters the current rows with `where state="Down"` — typically the threshold or rule expression for this monitoring goal.



Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.user All_Sessions.src All_Sessions.dest All_Sessions.action span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Network_Sessions data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Network_Sessions model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
Sample the same time range in your firewall management console, Panorama, FortiManager, or Check Point SmartConsole and confirm that counts, usernames, and object names line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (green/red per tunnel), Table, Timeline.

## SPL

```spl
index=firewall ("tunnel" OR "IPSec" OR "IKE") ("down" OR "failed" OR "established")
| rex "(?<tunnel_peer>\d+\.\d+\.\d+\.\d+)"
| eval status=if(match(_raw,"established|up"),"Up","Down")
| stats latest(status) as state by host, tunnel_peer | where state="Down"
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.user All_Sessions.src All_Sessions.dest All_Sessions.action span=1h
| sort -count
```

## Visualization

Status grid (green/red per tunnel), Table, Timeline.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Network_Sessions](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Sessions)
