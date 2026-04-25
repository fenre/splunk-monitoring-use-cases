<!-- AUTO-GENERATED from UC-4.2.30.json — DO NOT EDIT -->

---
id: "4.2.30"
title: "NSG Flow Log Threat Hunting"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.2.30 · NSG Flow Log Threat Hunting

## Description

NSG flow logs reveal lateral movement, denied probes, and unexpected east-west volume; baselining flows speeds incident triage beyond simple allow/deny counts.

## Value

NSG flow logs reveal lateral movement, denied probes, and unexpected east-west volume; baselining flows speeds incident triage beyond simple allow/deny counts.

## Implementation

Ingest NSG Flow Logs to Event Hub and Splunk. Enrich IPs with threat intel and CMDB. Alert on denied burst to sensitive subnets or new rare port pairs. Retention per compliance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: `sourcetype=mscs:azure:nsgflow` or Event Hub JSON (flow records).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest NSG Flow Logs to Event Hub and Splunk. Enrich IPs with threat intel and CMDB. Alert on denied burst to sensitive subnets or new rare port pairs. Retention per compliance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:nsgflow" flowDirection="In" macAddress=*
| stats sum(bytes) as total_bytes, dc(src) as unique_sources by dest, dest_port_s, rule
| where unique_sources > 50 OR total_bytes > 1000000000
| sort -total_bytes
```

Understanding this SPL

**NSG Flow Log Threat Hunting** — NSG flow logs reveal lateral movement, denied probes, and unexpected east-west volume; baselining flows speeds incident triage beyond simple allow/deny counts.

Documented **Data sources**: `sourcetype=mscs:azure:nsgflow` or Event Hub JSON (flow records). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:nsgflow. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:nsgflow". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by dest, dest_port_s, rule** so each row reflects one combination of those dimensions.
• Filters the current rows with `where unique_sources > 50 OR total_bytes > 1000000000` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Sankey or chord (src→dest), Table (top talkers), Map (geo of external IPs).

## SPL

```spl
index=azure sourcetype="mscs:azure:nsgflow" flowDirection="In" macAddress=*
| stats sum(bytes) as total_bytes, dc(src) as unique_sources by dest, dest_port_s, rule
| where unique_sources > 50 OR total_bytes > 1000000000
| sort -total_bytes
```

## Visualization

Sankey or chord (src→dest), Table (top talkers), Map (geo of external IPs).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
