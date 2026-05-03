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

Aggregate metrics across multiple organizations. Create comparison views.

## Detailed Implementation

### Prerequisites
- Multiple Meraki organizations managed via separate API keys or a single API key with cross-org access. Data in `index=meraki` with `sourcetype=meraki:api:devices` (per-org device inventory/status). Key field to partition data: `organizationId` or `organizationName`.
- Build `meraki_organizations.csv` lookup: `organizationId,org_name,business_unit,region,device_count_baseline` for cross-org context.
- Multi-organization Meraki environments are common in: (1) MSPs managing multiple customers, (2) large enterprises with separate orgs per business unit or region, (3) post-M&A environments with inherited Meraki deployments.

### Step 1 — Configure data collection
Verify multi-org data:
```spl
index=meraki sourcetype="meraki:api:devices" earliest=-1h
| stats dc(serial) as devices dc(network) as networks by organizationId
| lookup meraki_organizations.csv organizationId OUTPUT org_name business_unit
```

### Step 2 — Create the search and alert

**Primary search — Cross-organization health benchmarking:**
```spl
index=meraki sourcetype="meraki:api:devices" earliest=-15m
| dedup serial sortby -_time
| stats count as total count(eval(status="online")) as online count(eval(status="offline")) as offline dc(network) as networks by organizationId
| eval health_pct=round(100*online/total, 1)
| lookup meraki_organizations.csv organizationId OUTPUT org_name business_unit region device_count_baseline
| eval growth_pct=if(isnotnull(device_count_baseline), round(100*(total - device_count_baseline)/device_count_baseline, 1), null())
| eval benchmark=case(health_pct > 98, "ABOVE_AVG", health_pct > 95, "AVERAGE", health_pct > 90, "BELOW_AVG", 1==1, "POOR")
| sort benchmark, health_pct
```

#### Understanding this SPL: Cross-org benchmarking answers the question: "which business units or regions have the healthiest networks?" For MSPs, this is the customer health scorecard. For enterprises, it identifies which regions need the most attention. The `growth_pct` metric tracks fleet expansion, which impacts licensing and support capacity.

**Organization comparison metrics:**
```spl
index=meraki sourcetype="meraki:api:devices" earliest=-15m
| dedup serial sortby -_time
| eval device_type=case(match(model, "^MX"), "Security", match(model, "^MR"), "Wireless", match(model, "^MS"), "Switching", 1==1, "Other")
| stats count as devices by organizationId, device_type
| lookup meraki_organizations.csv organizationId OUTPUT org_name
| chart sum(devices) by org_name device_type
```

### Step 3 — Validate
(a) Compare organization device counts with each Meraki Dashboard (log in to each org and check inventory).
(b) Verify the org lookup has all managed organizations.
(c) Check that the API key has access to all intended organizations.

### Step 4 — Operationalize
Dashboard ("Meraki Multi-Org Comparison"):
- Row 1 — Single-value: "Organizations monitored", "Total devices", "Best health %", "Worst health %".
- Row 2 — Org health benchmark table: org, total devices, health %, growth %, benchmark rating.
- Row 3 — Device type distribution by organization.

Alerting:
- Warning (any org health drops below 90%): attention needed for that business unit/customer.
- Info (monthly): cross-org health report for management review.

### Step 5 — Troubleshooting

- **Some organizations missing** — Verify the API key has admin access to all organizations. Each Meraki API key is associated with an admin account that may have access to multiple orgs.

- **Device counts don't match Meraki Dashboard** — API pagination may truncate results for large organizations. Verify the TA handles pagination correctly.

- **Organization names not resolving** — Update the `meraki_organizations.csv` lookup with current org IDs and names from the Meraki API.

## SPL

```spl
index=cisco_network sourcetype="meraki:api"
| stats avg(health_score) as avg_health, count as device_count by organization
| sort - avg_health
```

## Visualization

Organization comparison bar chart; health rank table; benchmark line chart.

## Known False Positives

Different site sizes and use cases make raw scores unfair; compare like-sized orgs and segment retail vs head office.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
