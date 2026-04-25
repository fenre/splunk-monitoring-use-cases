<!-- AUTO-GENERATED from UC-4.2.22.json — DO NOT EDIT -->

---
id: "4.2.22"
title: "Azure Firewall Rule Hit and Threat Intel"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.2.22 · Azure Firewall Rule Hit and Threat Intel

## Description

Firewall logs show allowed/denied traffic and threat intelligence hits. Essential for network security and incident response.

## Value

Firewall logs show allowed/denied traffic and threat intelligence hits. Essential for network security and incident response.

## Implementation

Enable Azure Firewall diagnostic logs to Event Hub or storage. Ingest in Splunk. Alert on any threat intel hit. Dashboard rule hits, denied flows, and top sources/destinations.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Azure Firewall diagnostic logs (AzureFirewallApplicationRule, AzureFirewallNetworkRule, AzureFirewallThreatIntelLog).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Azure Firewall diagnostic logs to Event Hub or storage. Ingest in Splunk. Alert on any threat intel hit. Dashboard rule hits, denied flows, and top sources/destinations.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="AzureFirewallThreatIntelLog"
| rename msg_src_ip as src, msg_dest_ip as dest
| table _time src dest action threat_id
| sort -_time
```

Understanding this SPL

**Azure Firewall Rule Hit and Threat Intel** — Firewall logs show allowed/denied traffic and threat intelligence hits. Essential for network security and incident response.

Documented **Data sources**: Azure Firewall diagnostic logs (AzureFirewallApplicationRule, AzureFirewallNetworkRule, AzureFirewallThreatIntelLog). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:diagnostics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Renames fields with `rename` for clarity or joins.
• Pipeline stage (see **Azure Firewall Rule Hit and Threat Intel**): table _time src dest action threat_id
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Azure Firewall Rule Hit and Threat Intel** — Firewall logs show allowed/denied traffic and threat intelligence hits.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on accelerated data model the CPU-related Performance model — enable that model in Data Models and CIM add-ons, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Azure Firewall Rule Hit and Threat Intel** — Firewall logs show allowed/denied traffic and threat intelligence hits.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Azure Firewall Rule Hit and Threat Intel** — Firewall logs show allowed/denied traffic and threat intelligence hits.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Azure Firewall Rule Hit and Threat Intel** — Firewall logs show allowed/denied traffic and threat intelligence hits.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

Understanding this CIM / accelerated SPL

**Azure Firewall Rule Hit and Threat Intel** — Firewall logs show allowed/denied traffic and threat intelligence hits.

If you map cloud vendor fields into the CIM, this variant uses normalized names and `tstats` on accelerated models. The raw vendor search in Step 2 is still the first stop for troubleshooting.

**Pipeline walkthrough**

• Uses `tstats` on the `Performance` data model (CPU child datasets)—enable that model in Data Models and the CIM add-on, or the search may return no rows.

• Uses `sort` to rank results; add `head` to limit the table.

Enable Data Model Acceleration (and the right field aliases) for the models or datasets above; otherwise `tstats` may not find summaries.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (source, dest, action, rule), Map (threat IPs), Timeline (threat intel hits).

## SPL

```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="AzureFirewallThreatIntelLog"
| rename msg_src_ip as src, msg_dest_ip as dest
| table _time src dest action threat_id
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as agg_value
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=5m
| sort - agg_value
```

## Visualization

Table (source, dest, action, rule), Map (threat IPs), Timeline (threat intel hits).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
