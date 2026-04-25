<!-- AUTO-GENERATED from UC-5.2.29.json — DO NOT EDIT -->

---
id: "5.2.29"
title: "Threat Intelligence Correlation and IoC Matching (Meraki MX)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.29 · Threat Intelligence Correlation and IoC Matching (Meraki MX)

## Description

Correlates network traffic with threat intelligence databases to detect known malicious IPs and domains.

## Value

Correlates network traffic with threat intelligence databases to detect known malicious IPs and domains.

## Implementation

Create threat intelligence lookup table. Correlate with network events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=security_event OR type=urls OR type=flow`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create threat intelligence lookup table. Correlate with network events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" (type=security_event OR type=urls OR type=flow)
| lookup threat_intelligence_list src as src OUTPUTNEW threat_name, threat_severity
| where threat_severity="high" OR threat_severity="critical"
| stats count as hit_count by src, dest, threat_name
| sort - hit_count
```

Understanding this SPL

**Threat Intelligence Correlation and IoC Matching (Meraki MX)** — Correlates network traffic with threat intelligence databases to detect known malicious IPs and domains.

Documented **Data sources**: `sourcetype=meraki type=security_event OR type=urls OR type=flow`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where threat_severity="high" OR threat_severity="critical"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by src, dest, threat_name** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
In the Meraki cloud dashboard, use the same organization, network, and time range as the search. Confirm the same events, site or appliance names, and policy context you see in the dashboard line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: IoC match timeline; threat severity breakdown; affected hosts table.

## SPL

```spl
index=cisco_network sourcetype="meraki" (type=security_event OR type=urls OR type=flow)
| lookup threat_intelligence_list src as src OUTPUTNEW threat_name, threat_severity
| where threat_severity="high" OR threat_severity="critical"
| stats count as hit_count by src, dest, threat_name
| sort - hit_count
```

## Visualization

IoC match timeline; threat severity breakdown; affected hosts table.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
