---
id: "5.1.1"
title: "Interface Up/Down Events"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.1 · Interface Up/Down Events

## Description

A hard-down uplink or WAN port can isolate an entire site or VLAN; flapping often manifests as application timeouts and VoIP drops before a ticket names 'the network.' Treat each DOWN on a trunk or uplink as a potential SEV-1 for that site; treat more than 3 transitions in 10 minutes as a stability risk requiring immediate investigation of optics, cabling, or port configuration.

## Value

A hard-down uplink or WAN port can isolate an entire site or VLAN; flapping often manifests as application timeouts and VoIP drops before a ticket names 'the network.' Treat each DOWN on a trunk or uplink as a potential SEV-1 for that site; treat more than 3 transitions in 10 minutes as a stability risk requiring immediate investigation of optics, cabling, or port configuration.

## Implementation

Configure syslog forwarding on all network devices (UDP/TCP 514). Install TA for field extraction. Alert on down events for uplinks/trunks. Track flapping (>3 transitions in 10 min).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: `sourcetype=cisco:ios`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure syslog forwarding on all network devices (UDP/TCP 514). Install TA for field extraction. Alert on down events for uplinks/trunks. Track flapping (>3 transitions in 10 min).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:ios" "%LINEPROTO-5-UPDOWN" OR "%LINK-3-UPDOWN"
| rex "Interface (?<interface>\S+), changed state to (?<state>\w+)"
| stats count by host, interface, state | where count > 3 | sort -count
```

Understanding this SPL

**Interface Up/Down Events** — A hard-down uplink or WAN port can isolate an entire site or VLAN; flapping often manifests as application timeouts and VoIP drops before a ticket names 'the network.' Treat each DOWN on a trunk or uplink as a potential SEV-1 for that site; treat more than 3 transitions in 10 minutes as a stability risk requiring immediate investigation of optics, cabling, or port configuration.

Documented **Data sources**: `sourcetype=cisco:ios`. **App/TA** (typical add-on context): `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:ios. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:ios". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by host, interface, state** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 3` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (green/red per interface), Table, Timeline.

## SPL

```spl
index=network sourcetype="cisco:ios" "%LINEPROTO-5-UPDOWN" OR "%LINK-3-UPDOWN"
| rex "Interface (?<interface>\S+), changed state to (?<state>\w+)"
| stats count by host, interface, state | where count > 3 | sort -count
```

## Visualization

Status grid (green/red per interface), Table, Timeline.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
