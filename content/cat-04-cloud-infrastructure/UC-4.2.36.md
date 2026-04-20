---
id: "4.2.36"
title: "Azure Firewall Threat Intelligence Hits"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.2.36 · Azure Firewall Threat Intelligence Hits

## Description

Threat intel–based denies block known-bad IPs and domains at the edge; volume and target trends indicate active campaigns or misclassified traffic.

## Value

Threat intel–based denies block known-bad IPs and domains at the edge; volume and target trends indicate active campaigns or misclassified traffic.

## Implementation

Enable Threat Intel mode on Firewall and full diagnostic logging. Parse rule collection and threat category. Alert on new destination countries or sudden hit rate increase. Tune false positives with application owners.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Azure Firewall diagnostic logs (`AzureFirewallApplicationRule`, `AzureFirewallNetworkRule`), threat intel action.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Threat Intel mode on Firewall and full diagnostic logging. Parse rule collection and threat category. Alert on new destination countries or sudden hit rate increase. Tune false positives with application owners.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="AzureFirewallApplicationRule" msg_s="*ThreatIntel*"
| stats count by msg_s, FQDN, SourceAddress
| sort -count
```

Understanding this SPL

**Azure Firewall Threat Intelligence Hits** — Threat intel–based denies block known-bad IPs and domains at the edge; volume and target trends indicate active campaigns or misclassified traffic.

Documented **Data sources**: Azure Firewall diagnostic logs (`AzureFirewallApplicationRule`, `AzureFirewallNetworkRule`), threat intel action. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:diagnostics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by msg_s, FQDN, SourceAddress** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Intrusion_Detection.IDS_Attacks by IDS_Attacks.src | sort - count
```

Understanding this CIM / accelerated SPL

**Azure Firewall Threat Intelligence Hits** — Threat intel–based denies block known-bad IPs and domains at the edge; volume and target trends indicate active campaigns or misclassified traffic.

Documented **Data sources**: Azure Firewall diagnostic logs (`AzureFirewallApplicationRule`, `AzureFirewallNetworkRule`), threat intel action. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Intrusion_Detection.IDS_Attacks` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Map (source IP), Table (FQDN, count), Timeline (hits).

## SPL

```spl
index=azure sourcetype="mscs:azure:diagnostics" Category="AzureFirewallApplicationRule" msg_s="*ThreatIntel*"
| stats count by msg_s, FQDN, SourceAddress
| sort -count
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Intrusion_Detection.IDS_Attacks by IDS_Attacks.src | sort - count
```

## Visualization

Map (source IP), Table (FQDN, count), Timeline (hits).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
