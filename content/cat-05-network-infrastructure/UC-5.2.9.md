---
id: "5.2.9"
title: "URL Filtering Blocks"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.2.9 · URL Filtering Blocks

## Description

Shows what categories users are trying to access. Reveals policy effectiveness and shadow IT.

## Value

Shows what categories users are trying to access. Reveals policy effectiveness and shadow IT.

## Implementation

Forward URL filtering logs. Dashboard showing blocks by category and user.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX).
• Ensure the following data sources are available: `sourcetype=pan:url`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward URL filtering logs. Dashboard showing blocks by category and user.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall sourcetype="pan:url" action="block-url"
| stats count by url_category, src | sort -count
```

Understanding this SPL

**URL Filtering Blocks** — Shows what categories users are trying to access. Reveals policy effectiveness and shadow IT.

Documented **Data sources**: `sourcetype=pan:url`. **App/TA** (typical add-on context): `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall; **sourcetype**: pan:url. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=firewall, sourcetype="pan:url". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by url_category, src** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.action="blocked"
  by All_Traffic.src All_Traffic.dest All_Traffic.dest_port span=1h
| eval bytes=bytes_in+bytes_out
| sort -count
```

Understanding this CIM / accelerated SPL

**URL Filtering Blocks** — Shows what categories users are trying to access. Reveals policy effectiveness and shadow IT.

Documented **Data sources**: `sourcetype=pan:url`. **App/TA** (typical add-on context): `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.
• `eval` defines or adjusts **bytes** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (by category), Table, Pie chart.

## SPL

```spl
index=firewall sourcetype="pan:url" action="block-url"
| stats count by url_category, src | sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.action="blocked"
  by All_Traffic.src All_Traffic.dest All_Traffic.dest_port span=1h
| eval bytes=bytes_in+bytes_out
| sort -count
```

## Visualization

Bar chart (by category), Table, Pie chart.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
