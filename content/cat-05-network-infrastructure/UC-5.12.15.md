<!-- AUTO-GENERATED from UC-5.12.15.json — DO NOT EDIT -->

---
id: "5.12.15"
title: "E911 / Emergency Calling Path Validation"
status: "verified"
criticality: "critical"
splunkPillar: "Platform"
---

# UC-5.12.15 · E911 / Emergency Calling Path Validation

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Platform &middot; **Type:** Compliance, Safety, Availability &middot; **Wave:** Run &middot; **Status:** Verified

*We double-check that if someone dials the emergency number from your building phone system, the call goes out tagged the way regulators expect, without us storing anything more personal than we need.*

---

## Description

Audits emergency call metadata—completion status, ELIN/ANI alignment against inventory, and egress trunk selection—to validate regulatory routing without retaining sensitive audio or precise citizen locations beyond policy.

## Value

Safety and compliance stakeholders prove ongoing correctness of emergency breakout after dial-plan edits, subnet moves, or SBC migrations—reducing liability when PSAP callbacks must reach on-site security desks.

## Implementation

Maintain authoritative ELIN/location_id CSV refreshed from LIS; synthetic 933 or carrier-approved test calls on schedule; alert on mismatch or non-answered emergency CDR tails; coordinate retention with legal (often shorter than general CDR).

## Detailed Implementation

### Prerequisites
- Written policy defining test-number allowances (e.g., 933 where carriers permit) and prohibition on storing unnecessary location payloads.
- `corp_elin_inventory.csv` with `subnet_or_switchport`, `location_id`, `expected_elin`, `psap_route_ok`, reviewer signature date.
- CDR fields proving emergency classification post-normalization across vendors.

### Step 1 — Scope ingestion
Tag emergency rows at index-time via transforms evaluating dialed digits and carrier emergency flags.

### Step 2 — Correlate inventory
Lookup ELIN vs switch-port-derived location_id; flag mismatches and missing inventory rows.

### Step 3 — Scheduled validation
Run synthetic routing checks weekly per site cluster; log PASS/FAIL without dialing live PSAP except approved drills.

### Step 4 — Reporting
Executive dashboard: mismatch count trend, sites lacking inventory coverage, mean time to remediate.

### Step 5 — Incident handling
Open SEV-1 if production emergency CDR shows failed completion rates above drill thresholds; engage carrier NOC with anonymized metadata.

Extended troubleshooting
Hybrid work VPN egress may strip correct ELIN—ensure SBC topology hides corporate NAT inconsistencies. Multi-line hunt groups can emit misleading calling_party—prefer tagged ELIN field when present.

## SPL

```spl
index=voip sourcetype="cdr:voip" earliest=-24h
| eval emrg=if(match(called_number,"^(911|933|112)$") OR like(lower(call_type),"%emergency%"),1,0)
| where emrg=1
| lookup corp_elin_inventory.csv location_id OUTPUT expected_elin psap_route_ok
| eval elin_mismatch=if(isnotnull(expected_elin) AND calling_party!=expected_elin,1,0)
| stats count values(call_status) as statuses sum(elin_mismatch) as mismatches by location_id, dest
| where mismatches>0 OR mvfind(statuses,"answered")==null
| sort -mismatches
```

## Visualization

Compliance-oriented summary tiles (mismatch count, inventory completeness %); timeline of emergency-test successes; site-level table with drilldown to last mismatched subnet.

## Known False Positives

Drills using alternate codes may parse inconsistently; transient SIP failures retried successfully can duplicate rows; carrier-normalized ANI may differ formatting (+1 vs ten-digit) causing cosmetic mismatches; maintenance windows that reroute to alternate PSAP appear as deviations until inventory CSV updates.

## References

- [NENA NG911 / i3 foundation references (context)](https://www.nena.org/page/NG911_Standards)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
