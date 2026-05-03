<!-- AUTO-GENERATED from UC-5.12.8.json — DO NOT EDIT -->

---
id: "5.12.8"
title: "Number Portability Request Tracking"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.12.8 · Number Portability Request Tracking

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Operations

*We help you track number-port requests so you can see delays or backlogs with carriers, which is important when a business is counting on a port date.*

---

## Description

LNP order status, NPAC responses, and port-out churn — operations and regulatory reporting for porting SLAs.

## Value

Porting operations teams track LNP order lifecycle, detect SLA breaches before regulatory penalties, and identify problematic carriers with high rejection rates for process improvement.

## Implementation

SLA alerts for orders >72h in PENDING; root-cause codes joined to carrier contact list.

## Detailed Implementation

### Prerequisites
- LNP (Local Number Portability) order data in `index=telco` with `sourcetype=lnp:order` from your porting system (BSS/OSS). This may be: (a) direct database export from your number management system, (b) SOA (Service Order Administration) API feeds from the NPAC (Number Portability Administration Center), (c) CSV/JSON batch files from your porting operations team.
- Key fields: `order_status` (PENDING, CONFIRMED, FOC_RECEIVED, ACTIVATED, REJECTED, TIMEOUT, CANCELLED), `tn_range` (telephone number or range being ported), `losing_carrier` (old carrier ID or name), `gaining_carrier` (new carrier — typically your network), `submitted_epoch` (order submission timestamp as epoch seconds), `foc_date` (Firm Order Commitment date), `activation_date`, `reject_reason` (if rejected).
- Optional: NPAC SOA responses in `sourcetype=npac:soa` providing real-time status updates from the central porting database.
- Regulatory context: FCC (US), CRTC (Canada), Ofcom (UK), and BEREC (EU) mandate specific porting timelines. US: simple ports must complete within 1 business day; complex ports within 4 business days. Non-compliance results in regulatory fines and customer complaints.
- Build a carrier lookup `carrier_contacts.csv` mapping `losing_carrier` codes to carrier names and NOC contact information for escalation.

### Step 1 — Configure data collection
Verify LNP order data is flowing:
```spl
index=telco sourcetype="lnp:order" earliest=-7d
| stats count by order_status
```
You should see a distribution across PENDING, CONFIRMED, ACTIVATED, REJECTED, etc. If all orders show as PENDING, the status update feed may be delayed.

Verify key fields:
```spl
index=telco sourcetype="lnp:order" earliest=-7d
| stats dc(tn_range) as unique_tns dc(losing_carrier) as carriers count by order_status
```

### Step 2 — Create the search and alert

**Primary search — Aging port orders (SLA tracking):**
```spl
index=telco sourcetype="lnp:order"
| where order_status IN ("PENDING", "REJECTED", "TIMEOUT")
| eval age_hours=round((now()-submitted_epoch)/3600, 1)
| eval age_days=round(age_hours/24, 1)
| eval sla_status=case(age_hours > 96, "SLA BREACH", age_hours > 72, "CRITICAL", age_hours > 48, "WARNING", 1==1, "On Track")
| lookup carrier_contacts.csv losing_carrier OUTPUT carrier_name noc_phone noc_email
| stats count avg(age_days) as avg_age max(age_days) as max_age values(sla_status) as statuses by tn_range, losing_carrier, carrier_name, order_status
| sort -max_age
```

#### Understanding this SPL: We calculate the age of each pending/rejected/timed-out port order in hours and days from submission. SLA thresholds are based on US FCC simple port timelines (1 business day = 24h, with escalation at 48h, 72h, and breach at 96h). The carrier lookup provides contact information for escalation. Orders aging beyond 72 hours are critical — they likely need manual intervention or escalation to the losing carrier's porting team.

**Rejection analysis — why ports are failing:**
```spl
index=telco sourcetype="lnp:order" order_status="REJECTED" earliest=-30d
| stats count by reject_reason, losing_carrier
| lookup carrier_contacts.csv losing_carrier OUTPUT carrier_name
| sort -count
| head 20
```

#### Understanding this SPL: Identifies the most common rejection reasons by carrier. Typical reasons: "CSR mismatch" (Customer Service Record data doesn't match — usually name or address), "Unauthorized" (subscriber didn't authorize the port), "Complex port" (requires manual handling), "TN not found" (number not in the losing carrier's system). Persistent CSR mismatches with a specific carrier suggest a systemic data quality issue.

**Porting throughput — daily activation rate:**
```spl
index=telco sourcetype="lnp:order" order_status="ACTIVATED" earliest=-30d
| bin _time span=1d
| stats count as activations by _time
| eventstats avg(activations) as avg_daily
| eval above_avg=if(activations > avg_daily*1.5, "High", "Normal")
```

Schedule as Alert: aging orders search runs every 4 hours. Trigger when any order exceeds 72 hours in PENDING. Rejection analysis runs daily for weekly review.

### Step 3 — Validate
(a) Cross-reference a sample of aging orders with the porting system's UI. Verify the `submitted_epoch` and `order_status` match.
(b) Check with the porting operations team that the rejection reasons in Splunk match what they see in the BSS.
(c) Verify the `carrier_contacts.csv` lookup has current contact information — carrier NOC numbers change.
(d) Confirm the `foc_date` field is populated for orders that have received FOC (Firm Order Commitment).

### Step 4 — Operationalize
Dashboard ("Telecom — Number Portability Operations"):
- Row 1 — Single-value tiles: "Orders in PENDING", "Orders past SLA", "Rejections (30d)", "Avg completion time (days)".
- Row 2 — Funnel chart: order lifecycle (Submitted → FOC Received → Activated) with drop-off rates.
- Row 3 — Aging orders table: TN, losing carrier, carrier contact, age in days, SLA status (color-coded).
- Row 4 — Rejection analysis: top rejection reasons by carrier, with trend over 30 days.

Alerting:
- Critical (order > 96 hours in PENDING): page porting operations — SLA breach, potential regulatory violation. Include TN, losing carrier, and carrier NOC contact.
- Warning (order > 72 hours): ticket with 4-hour SLA.
- Informational (rejection rate > 20% from a specific carrier): weekly report to porting management for carrier engagement.

Runbook (owner: Number Portability Operations):
1. **Order stuck in PENDING > 72h**: Contact the losing carrier's porting team using the carrier lookup contact. Common causes: the losing carrier hasn't processed the port request, FOC date not issued, or the port request was lost in their system. Escalate to the NPAC if the carrier is unresponsive.
2. **High rejection rate from a carrier**: Review the rejection reasons. If "CSR mismatch" dominates, work with the carrier to align data formats. If "Unauthorized" dominates, verify that subscriber authorization is being captured correctly in your ordering system.
3. **Porting volume spike**: A large batch of ports (e.g. enterprise migration) can overwhelm porting operations. Pre-coordinate with the losing carrier and the NPAC for bulk port handling.

### Step 5 — Troubleshooting

- **`submitted_epoch` is null or 0** — The porting system may use a different timestamp format (ISO 8601, Unix milliseconds). Check the raw event and add a `EVAL-submitted_epoch` in `props.conf` to normalize.

- **Order status never updates** — The status update feed from the porting system or NPAC SOA may be delayed or broken. Check the data input for the SOA feed. Some porting systems only push status updates in batch files at specific intervals.

- **Duplicate orders for the same TN** — Porting retries and re-submissions can create multiple order records for the same number. Use `| dedup tn_range sortby -_time` to keep only the latest order.

- **SLA calculation doesn't account for business days** — The current calculation uses calendar hours. For accurate FCC SLA compliance, exclude weekends and holidays. Create a `business_days.csv` lookup or use `date_wday` filtering.

## SPL

```spl
index=telco sourcetype="lnp:order"
| where order_status IN ("PENDING","REJECTED","TIMEOUT")
| stats count, avg((now()-submitted_epoch)/86400) as age_days by tn_range, losing_carrier
| sort -age_days
```

## Visualization

Funnel (order states), Table (aging ports), Bar chart (reject reasons).

## Known False Positives

Batch jobs and re-drives in porting can create event bursts without customer impact; compare to the carrier’s actual FOC date, not the raw log count only.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
