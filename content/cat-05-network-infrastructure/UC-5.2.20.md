<!-- AUTO-GENERATED from UC-5.2.20.json — DO NOT EDIT -->

---
id: "5.2.20"
title: "Content Filtering and URL Category Blocks (Meraki MX)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.20 · Content Filtering and URL Category Blocks (Meraki MX)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Compliance

*We show which web categories and pages get stopped at the network edge so policy stays in step with what people really need to do their jobs.*

---

## Description

Tracks blocked URLs and categories to monitor policy compliance and identify misclassified content.

## Value

Security teams analyze Meraki MX content filtering blocks by risk category, prioritizing malware/phishing blocks and proxy evasion attempts over routine policy enforcement.

## Implementation

Ingest URL filtering events from MX syslog. Categorize by policy.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA)..
- Ensure the following data sources are available: `sourcetype=meraki type=urls action="blocked"` | Alternate ingest: Splunk Connect for Syslog (SC4S) Meraki vendor pack — points the Meraki dashboard at an SC4S receiver and produces sourcetype="meraki" syslog events (free-form text extracted with rex). Use when you don't want to deploy the polling API TA..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Ingest URL filtering events from MX syslog. Categorize by policy.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" type=urls action="blocked"
| stats count as block_count by url_category, src
| sort - block_count
| head 20
```

#### Understanding this SPL

**Content Filtering and URL Category Blocks (Meraki MX)** — Security teams analyze Meraki MX content filtering blocks by risk category, prioritizing malware/phishing blocks and proxy evasion attempts over routine policy enforcement.

Documented **Data sources**: `sourcetype=meraki type=urls action="blocked"` | Alternate ingest: Splunk Connect for Syslog (SC4S) Meraki vendor pack — points the Meraki dashboard at an SC4S receiver and produces sourcetype="meraki" syslog events (free-form text extracted with rex). Use when you don't want to deploy the polling API TA. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by url_category, src** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
- Limits the number of rows with `head`.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  by Web.status Web.url Web.http_method Web.dest span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Content Filtering and URL Category Blocks (Meraki MX)** — Security teams analyze Meraki MX content filtering blocks by risk category, prioritizing malware/phishing blocks and proxy evasion attempts over routine policy enforcement.

Documented **Data sources**: `sourcetype=meraki type=urls action="blocked"` | Alternate ingest: Splunk Connect for Syslog (SC4S) Meraki vendor pack — points the Meraki dashboard at an SC4S receiver and produces sourcetype="meraki" syslog events (free-form text extracted with rex). Use when you don't want to deploy the polling API TA. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

- Uses `tstats` against accelerated summaries for data model `Web.Web` — enable acceleration for that model.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of top blocked categories; bar chart by category; user detail table.

## SPL

```spl
index=meraki sourcetype="meraki" type=urls action="blocked"
| stats count as block_count by url_category, src
| sort - block_count
| head 20
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  by Web.status Web.url Web.http_method Web.dest span=1h
| sort -count
```

## Visualization

Table of top blocked categories; bar chart by category; user detail table.

## Known False Positives

Overly strict categories, new SaaS, and one-off page visits can make URL blocks look worse than a policy problem.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
