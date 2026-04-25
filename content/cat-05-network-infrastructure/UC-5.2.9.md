<!-- AUTO-GENERATED from UC-5.2.9.json — DO NOT EDIT -->

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
• `stats` rolls up events into metrics; results are split **by url_category, src** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.



Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  by Web.status Web.url Web.http_method Web.dest span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Web data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Web model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
Sample the same time range in your firewall management console, Panorama, FortiManager, or Check Point SmartConsole and confirm that counts, usernames, and object names line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (by category), Table, Pie chart.

## SPL

```spl
index=firewall sourcetype="pan:url" action="block-url"
| stats count by url_category, src | sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  by Web.status Web.url Web.http_method Web.dest span=1h
| sort -count
```

## Visualization

Bar chart (by category), Table, Pie chart.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
