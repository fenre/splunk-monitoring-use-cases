<!-- AUTO-GENERATED from UC-5.12.10.json — DO NOT EDIT -->

---
id: "5.12.10"
title: "Toll Fraud Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.12.10 · Toll Fraud Detection

## Description

Premium-rate, international, or short-duration high-cost patterns from compromised PBX or SIP credentials — classic CDR analytics use case.

## Value

Premium-rate, international, or short-duration high-cost patterns from compromised PBX or SIP credentials — classic CDR analytics use case.

## Implementation

Hotline to NOC + auto-block high-risk destinations on SBC after threshold; require PIN for international on suspect trunks.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SBC CDR, fraud scoring apps.
• Ensure the following data sources are available: `sourcetype="cdr:voip"` with `rate_class`, `destination`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Hotline to NOC + auto-block high-risk destinations on SBC after threshold; require PIN for international on suspect trunks.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=voip sourcetype="cdr:voip"
| lookup premium_and_high_risk_prefixes called_number OUTPUT risk_tier
| where risk_tier IN ("premium","satellite","high_cost_geo")
| stats sum(toll_charge) as cost, count, dc(calling_party) as sources by src, hour
| where cost>500 OR count>100
| sort -cost
```

Understanding this SPL

**Toll Fraud Detection** — Premium-rate, international, or short-duration high-cost patterns from compromised PBX or SIP credentials — classic CDR analytics use case.

Documented **Data sources**: `sourcetype="cdr:voip"` with `rate_class`, `destination`. **App/TA** (typical add-on context): SBC CDR, fraud scoring apps. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: voip; **sourcetype**: cdr:voip. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=voip, sourcetype="cdr:voip". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where risk_tier IN ("premium","satellite","high_cost_geo")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by src, hour** so each row reflects one combination of those dimensions.
• Filters the current rows with `where cost>500 OR count>100` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Tie a suspicious destination burst to the carrier CDR and call-detail from the SBC; confirm the account was not in a test mode or a known premium campaign.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (top fraud legs), Map (destination countries), Timeline (attack window).

## SPL

```spl
index=voip sourcetype="cdr:voip"
| lookup premium_and_high_risk_prefixes called_number OUTPUT risk_tier
| where risk_tier IN ("premium","satellite","high_cost_geo")
| stats sum(toll_charge) as cost, count, dc(calling_party) as sources by src, hour
| where cost>500 OR count>100
| sort -cost
```

## Visualization

Table (top fraud legs), Map (destination countries), Timeline (attack window).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
