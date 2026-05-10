<!-- AUTO-GENERATED from UC-5.8.19.json — DO NOT EDIT -->

---
id: "5.8.19"
title: "Multi-Organization Comparison and Benchmarking (Meraki)"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.8.19 · Multi-Organization Comparison and Benchmarking (Meraki)

> **Criticality:** Low &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you compare sites and organizations on Meraki, so the slow or noisy places stand out next to the good ones.*

---

## Description

Compares metrics across organizations to identify best practices and outliers.

## Value

Network operations teams benchmark Meraki network health across multiple organizations for MSP customer reporting, enterprise business unit comparison, and fleet growth tracking.

## Implementation

1. In Splunk_TA_cisco_meraki -> Configuration -> Organization, add one entry per Meraki tenancy you want to benchmark. 2. Enable the same set of inputs (Devices Availabilities + Assurance Alerts) in each. 3. Group by organizationName for side-by-side comparison. 4. For per-product-type drill-down, add productType to the stats by clause.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities and Assurance Alerts inputs configured for each organization tenancy you want to compare. NOTE: configure one TA Organization entry per tenancy; events are stamped with organizationId and organizationName..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. In Splunk_TA_cisco_meraki -> Configuration -> Organization, add one entry per Meraki tenancy you want to benchmark. 2. Enable the same set of inputs (Devices Availabilities + Assurance Alerts) in each. 3. Group by organizationName for side-by-side comparison. 4. For per-product-type drill-down, add productType to the stats by clause.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:devicesavailabilities" earliest=-1h
| stats count as device_count,
        sum(eval(if(status="online",1,0))) as online_count,
        sum(eval(if(status="alerting",1,0))) as alerting_count
         by organizationId, organizationName
| eval availability_pct = round(online_count*100/device_count, 2)
| join type=left organizationId [
    search index=meraki sourcetype="meraki:assurancealerts" earliest=-24h
    | stats count as open_alerts by organizationId
  ]
| fillnull value=0 open_alerts
| eval alerts_per_device = round(open_alerts/device_count, 2)
| sort - availability_pct
```

#### Understanding this SPL

**Multi-Organization Comparison and Benchmarking (Meraki)** — Network operations teams benchmark Meraki network health across multiple organizations for MSP customer reporting, enterprise business unit comparison, and fleet growth tracking.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities and Assurance Alerts inputs configured for each organization tenancy you want to compare. NOTE: configure one TA Organization entry per tenancy; events are stamped with organizationId and organizationName. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:devicesavailabilities. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:devicesavailabilities", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by organizationId, organizationName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **availability_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
- Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
- Fills null values with `fillnull`.
- `eval` defines or adjusts **alerts_per_device** — often to normalize units, derive a ratio, or prepare for thresholds.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Organization comparison bar chart; health rank table; benchmark line chart.

## SPL

```spl
index=meraki sourcetype="meraki:devicesavailabilities" earliest=-1h
| stats count as device_count,
        sum(eval(if(status="online",1,0))) as online_count,
        sum(eval(if(status="alerting",1,0))) as alerting_count
         by organizationId, organizationName
| eval availability_pct = round(online_count*100/device_count, 2)
| join type=left organizationId [
    search index=meraki sourcetype="meraki:assurancealerts" earliest=-24h
    | stats count as open_alerts by organizationId
  ]
| fillnull value=0 open_alerts
| eval alerts_per_device = round(open_alerts/device_count, 2)
| sort - availability_pct
```

## Visualization

Organization comparison bar chart; health rank table; benchmark line chart.

## Known False Positives

Different site sizes and use cases make raw scores unfair; compare like-sized orgs and segment retail vs head office.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
