---
id: "5.13.6"
title: "Device Reachability Loss Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.6 · Device Reachability Loss Detection

## Description

Identifies devices that Catalyst Center can no longer reach, indicating potential hardware failure, network partition, or misconfiguration.

## Value

Unreachable devices represent the most severe health state — they may be completely down. Rapid detection reduces outage duration and blast radius.

## Implementation

Requires UC-5.13.3 alerting in place. Filter specifically on `reachabilityHealth="Unreachable"` and schedule frequently (for example every 5–15 minutes) with P1-style routing. Confirm Catalyst Center and Splunk time zones align so `duration_min` matches operator expectations.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538).
• Ensure the following data sources are available: index=catalyst, sourcetype cisco:dnac:devicehealth (Catalyst Center /dna/intent/api/v1/device-health).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Requires UC-5.13.3 alerting in place. Filter specifically on `reachabilityHealth="Unreachable"` and schedule frequently (for example every 5–15 minutes) with P1-style routing. Confirm Catalyst Center and Splunk time zones align so `duration_min` matches operator expectations.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" reachabilityHealth="Unreachable" | stats count as unreachable_count earliest(_time) as first_unreachable latest(_time) as last_seen by deviceName, managementIpAddress, deviceType, siteId | eval duration_min=round((last_seen-first_unreachable)/60,0) | sort -duration_min
```

Understanding this SPL

**Device Reachability Loss Detection** — Unreachable devices represent the most severe health state — they may be completely down. Rapid detection reduces outage duration and blast radius.

Documented **Data sources**: index=catalyst, sourcetype cisco:dnac:devicehealth (Catalyst Center /dna/intent/api/v1/device-health). **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: catalyst; **sourcetype**: cisco:dnac:devicehealth. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• The search filter at index time or SPL filter keeps only rows where `reachabilityHealth` is Unreachable, focusing the runbook on full loss of management.
• `stats` per device records how many such samples occurred plus `earliest` and `latest` timestamps to bracket the incident window.
• `eval` converts the span to minutes for handoff; `sort -duration_min` highlights persistently dark devices versus brief blips (with appropriate time window choice).


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of unreachable devices with duration, timeline panel of first to last event, link-out to IP management or CMDB.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" reachabilityHealth="Unreachable" | stats count as unreachable_count earliest(_time) as first_unreachable latest(_time) as last_seen by deviceName, managementIpAddress, deviceType, siteId | eval duration_min=round((last_seen-first_unreachable)/60,0) | sort -duration_min
```

## Visualization

Table of unreachable devices with duration, timeline panel of first to last event, link-out to IP management or CMDB.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
