<!-- AUTO-GENERATED from UC-5.8.12.json — DO NOT EDIT -->

---
id: "5.8.12"
title: "License Expiration Tracking and Renewal Alerts (Meraki)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.8.12 · License Expiration Tracking and Renewal Alerts (Meraki)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you know before Meraki licenses slip past their date, so renewals are planned instead of a surprise cut-off.*

---

## Description

Ensures licenses don't expire unexpectedly and features remain available.

## Value

Network operations teams track Meraki license expiration dates across all license types, projecting renewal costs and detecting expired or soon-to-expire licenses before devices lose cloud management capabilities.

## Implementation

Query organization API for license expiry. Alert on <90 days.

## Detailed Implementation

### Prerequisites
- Meraki licensing information available via the Meraki Dashboard API. The TA may poll organization licensing endpoints, or a custom script queries `GET /organizations/{organizationId}/licenses` and `GET /organizations/{organizationId}/licensing/coterm/licenses`. Data in `index=meraki` with `sourcetype=meraki:api:licenses` or custom sourcetype.
- Key fields: `licenseType` (Enterprise, Advanced Security, etc.), `expirationDate`, `seatCount`, `networkId`, `state` (active/expired/recentlyQueued).
- Meraki operates on per-device licensing (classic) or co-termination licensing. Co-termination means all licenses in an organization expire on the same date. Classic licensing is per-device with individual expiration dates.
- Build `meraki_license_costs.csv` lookup: `licenseType,annual_cost_per_device` for cost projection.

### Step 1 — Configure data collection
Verify license data:
```spl
index=meraki sourcetype="meraki:api:licenses" earliest=-24h
| stats count by licenseType, state
```

### Step 2 — Create the search and alert

**Primary search — License expiration tracking:**
```spl
index=meraki sourcetype="meraki:api:licenses" earliest=-24h
| eval expiry_epoch=strptime(expirationDate, "%Y-%m-%dT%H:%M:%S")
| eval days_until_expiry=round((expiry_epoch - now()) / 86400, 0)
| eval urgency=case(days_until_expiry < 0, "EXPIRED", days_until_expiry < 30, "CRITICAL", days_until_expiry < 90, "WARNING", days_until_expiry < 180, "PLAN", 1==1, "OK")
| where urgency!="OK"
| lookup meraki_license_costs.csv licenseType OUTPUT annual_cost_per_device
| eval renewal_cost=if(isnotnull(annual_cost_per_device) AND isnotnull(seatCount), annual_cost_per_device * seatCount, null())
| stats count as licenses sum(seatCount) as total_seats sum(renewal_cost) as total_cost by licenseType, urgency, expirationDate
| sort urgency, expirationDate
```

#### Understanding this SPL: Meraki devices without a valid license lose cloud management capabilities after a grace period — they continue forwarding traffic but can't be configured, monitored, or updated. For co-termination licensing, the entire organization expires at once, making this a business-critical tracking item. The renewal cost projection helps procurement teams budget for renewals.

**License utilization (seats used vs. available):**
```spl
index=meraki sourcetype="meraki:api:licenses" state="active" earliest=-24h
| stats sum(seatCount) as total_seats by licenseType
| join licenseType type=left [search index=meraki sourcetype="meraki:api:devices" earliest=-24h | dedup serial | stats count as devices_deployed by productType | rename productType as licenseType]
| eval utilization_pct=round(100*devices_deployed/total_seats, 1)
| eval spare_seats=total_seats - devices_deployed
```

### Step 3 — Validate
(a) In Meraki Dashboard: Organization > License Info. Compare expiration dates and seat counts with Splunk.
(b) Verify co-termination vs. classic licensing mode matches the Splunk data model.
(c) Check renewal cost calculation against actual Meraki pricing.

### Step 4 — Operationalize
Dashboard ("Meraki Licensing"):
- Row 1 — Single-value tiles: "Expired licenses", "Expiring < 90 days", "Total seats", "Renewal cost (next 90 days)".
- Row 2 — License expiration table: type, expiration date, days remaining, seats, cost.
- Row 3 — License utilization: seats used vs. available per type.

Alerting:
- Critical (license expired): devices will lose management in grace period.
- Critical (co-term license expiring < 30 days): entire organization at risk.
- Warning (license expiring < 90 days): initiate procurement process.

### Step 5 — Troubleshooting

- **License data not available** — The Meraki API licensing endpoints require Organization-level read access. Verify the API key has the correct permissions.

- **Co-term vs. per-device confusion** — Check `GET /organizations/{orgId}/licensing/coterm/licenses` for co-term licensing or `GET /organizations/{orgId}/licenses` for classic per-device licensing. The API structure differs.

- **Seat count doesn't match device count** — Licenses may include spare capacity for planned deployments. The utilization search helps identify over-provisioning or under-licensing.

## SPL

```spl
index=cisco_network sourcetype="meraki:api" license_expiry=*
| eval days_until_expire=round((strptime(license_expiry, "%Y-%m-%d")-now())/86400, 0)
| stats latest(days_until_expire) as days_left, latest(license_expiry) as expiry_date by license_type, organization
| where days_left < 90
| sort days_left
```

## Visualization

License expiration countdown; renewal timeline; license detail table.

## Known False Positives

Co-term vs per-device licensing and co-termination renewals can confuse expiring tiles; match Splunk to Organization > License in Dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
