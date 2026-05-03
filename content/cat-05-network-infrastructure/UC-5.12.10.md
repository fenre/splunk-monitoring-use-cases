<!-- AUTO-GENERATED from UC-5.12.10.json — DO NOT EDIT -->

---
id: "5.12.10"
title: "Toll Fraud Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.12.10 · Toll Fraud Detection

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Fraud, Security

*We help you spot when someone is routing expensive or odd international calls, which can be fraud, a misdial, or a broken private branch setup—before the bill is paid.*

---

## Description

Premium-rate, international, or short-duration high-cost patterns from compromised PBX or SIP credentials — classic CDR analytics use case.

## Value

Fraud teams detect and stop toll fraud attacks — compromised PBX, stolen SIP credentials, Wangiri callbacks — within minutes, preventing financial losses that can reach tens of thousands of dollars per incident.

## Implementation

Hotline to NOC + auto-block high-risk destinations on SBC after threshold; require PIN for international on suspect trunks.

## Detailed Implementation

### Prerequisites
- CDR data in `index=voip` with `sourcetype=cdr:voip` from your SBC/PBX/UCM. Required fields: `called_number` (destination dialed), `calling_party` (originator), `src` (source trunk/gateway), `toll_charge` (call cost, if available from rating), `duration_sec`, `call_status`.
- A premium and high-risk number prefix lookup `premium_and_high_risk_prefixes.csv` with columns: `called_number` (prefix pattern), `risk_tier` (premium/satellite/high_cost_geo/normal), `country`, `rate_per_min` (estimated cost). Sources for this lookup: your carrier's rate deck (most accurate), international premium rate databases (e.g. IPRN databases), and fraud intelligence feeds.
- Understand toll fraud patterns: (a) PBX/UCM compromise: attacker gains access to a PBX and routes calls to premium international numbers, often overnight or on weekends when offices are empty. (b) SIP credential theft: stolen SIP registration credentials used to place premium calls. (c) Call transfer/forwarding abuse: legitimate accounts configured to forward to premium numbers. (d) Wangiri callbacks: subscribers tricked into calling back premium numbers. (e) Conference bridge abuse: dial-in conference numbers used to bridge premium calls.
- Financial exposure: toll fraud losses average $38 billion/year globally (CFCA). A single compromised PBX can generate $10,000-$100,000 in premium call charges in a single weekend.
- Rate data: if your CDR includes `toll_charge` (per-call cost), use it directly. If not, estimate from the prefix lookup's `rate_per_min` × `duration_sec / 60`.

### Step 1 — Configure data collection
Verify CDR data and the fraud-relevant fields:
```spl
index=voip sourcetype="cdr:voip" earliest=-1h
| stats count dc(called_number) as unique_destinations dc(calling_party) as unique_callers dc(src) as unique_sources
```

Upload the premium prefix lookup. At minimum, include:
- Premium rate service numbers (e.g. +900 in some countries, UK 09xx, US 1-900)
- Satellite phone prefixes (+870, +871, +872, +873, +881, +882)
- High-cost international destinations (Somalia +252, Cuba +53, Sierra Leone +232, certain Pacific islands)
- IPRN (International Premium Rate Numbers) known to be used in fraud

Test the lookup:
```spl
| makeresults | eval called_number="+8821234567890"
| lookup premium_and_high_risk_prefixes.csv called_number OUTPUT risk_tier country
```

### Step 2 — Create the search and alert

**Primary search — Real-time toll fraud detection (15-min alert):**
```spl
index=voip sourcetype="cdr:voip" earliest=-15m
| lookup premium_and_high_risk_prefixes.csv called_number OUTPUT risk_tier country rate_per_min
| where risk_tier IN ("premium", "satellite", "high_cost_geo")
| eval estimated_cost=if(isnotnull(toll_charge), toll_charge, round(rate_per_min * duration_sec / 60, 2))
| stats sum(estimated_cost) as total_cost count as calls dc(calling_party) as unique_callers sum(duration_sec) as total_sec by src, risk_tier, country
| eval total_min=round(total_sec/60, 0)
| where total_cost > 100 OR calls > 20
| sort -total_cost
```

#### Understanding this SPL: We enrich every CDR with the premium prefix lookup to identify high-risk calls. The estimated cost calculation uses actual toll charges when available, falling back to rate-deck estimates. Grouping by `src` (source trunk/gateway) identifies the entry point of the fraud traffic. Thresholds of $100 or 20 calls in 15 minutes are aggressive — toll fraud can accumulate thousands of dollars per hour if not caught quickly.

**After-hours premium call detection:**
```spl
index=voip sourcetype="cdr:voip" earliest=-24h
| lookup premium_and_high_risk_prefixes.csv called_number OUTPUT risk_tier country
| where risk_tier IN ("premium", "satellite", "high_cost_geo")
| eval hour=strftime(_time, "%H")
| eval is_after_hours=if(hour >= 20 OR hour < 6, 1, 0)
| where is_after_hours=1
| stats sum(toll_charge) as cost count as calls dc(called_number) as unique_destinations by calling_party, src
| where calls > 5
| sort -cost
```

#### Understanding this SPL: Most toll fraud occurs outside business hours (8 PM to 6 AM) when offices are unattended and PBX compromises go unnoticed. Any premium calls during these hours from enterprise trunks are suspicious. Legitimate after-hours premium calls are rare — most businesses don't call satellite phones or premium numbers at midnight.

**Behavioral anomaly — sudden destination change:**
```spl
index=voip sourcetype="cdr:voip" earliest=-7d
| lookup premium_and_high_risk_prefixes.csv called_number OUTPUT risk_tier
| eval is_premium=if(risk_tier IN ("premium", "satellite", "high_cost_geo"), 1, 0)
| bin _time span=1d
| stats sum(is_premium) as premium_calls count as total_calls by calling_party, _time
| eventstats avg(premium_calls) as avg_premium by calling_party
| where _time >= relative_time(now(), "-1d@d")
| where premium_calls > 0 AND (avg_premium == 0 OR premium_calls > 5 * avg_premium)
| sort -premium_calls
```

#### Understanding this SPL: Detects callers who never or rarely called premium numbers but suddenly start. A calling_party with zero historical premium calls that suddenly places 10 premium calls is a strong indicator of credential compromise or forwarding abuse.

Schedule as Alert: primary search runs every 15 minutes. Trigger when total_cost > $500 or calls > 50 in any 15-min window. Route to fraud team AND auto-trigger SBC blocking rule if your platform supports it.

### Step 3 — Validate
(a) Manually verify that the premium prefix lookup correctly classifies known premium numbers (e.g. +881 = Iridium satellite, +900 = premium).
(b) Check a few flagged calls against the SBC CDR and carrier invoice. Verify the cost estimates are reasonable.
(c) Test the after-hours detection by placing a test call to a non-premium international number outside business hours and verifying it does NOT trigger the alert (should not match the premium lookup).
(d) Coordinate with your carrier for real-time fraud alerts — many carriers provide their own fraud detection and can block premium destinations at the interconnect level.

### Step 4 — Operationalize
Dashboard ("Voice - Toll Fraud Detection"):
- Row 1 — Single-value tiles: "Premium calls (24h)", "Estimated fraud cost (24h)" (red if >$0), "After-hours premium calls", "Unique high-risk destinations".
- Row 2 — Timeline: premium call rate over 7 days with cost overlay. After-hours periods shaded.
- Row 3 — Top fraud sources table: src/calling_party, cost, calls, destinations, risk_tier. Drilldown to individual CDRs.
- Row 4 — Geographic map: destination countries colored by risk tier and sized by call volume.

Alerting:
- Critical ($500+ in premium calls in 15 min): page fraud team AND trigger automatic SBC destination block. This is a "shoot first, ask questions later" threshold — the financial exposure grows by hundreds of dollars per minute.
- Warning (any premium calls after hours): notify security/fraud team for review next business day.
- Auto-remediation: configure the SBC to block premium/satellite prefixes by default and require explicit unblocking for legitimate use (defense in depth).

Runbook (owner: Fraud / Voice Security):
1. **Active toll fraud detected**: IMMEDIATELY block the source trunk or calling party on the SBC. Then investigate: was it a compromised PBX, stolen SIP credentials, or forwarding abuse? Preserve CDRs for evidence. Contact the carrier to dispute fraudulent charges (most carrier agreements have a fraud dispute window of 30-90 days).
2. **PBX compromise**: Reset all SIP credentials. Check for unauthorized call forwarding rules, voicemail-to-external forwarding, and DISA (Direct Inward System Access) configuration. Implement SIP registration authentication if not already active.
3. **After-hours premium calls from enterprise**: Check if the PBX has international calling restrictions enabled. Implement time-based call routing policies that block premium/international calls outside business hours.
4. **Wangiri callback fraud**: Alert subscribers who called back premium numbers. Implement inbound number screening for known IPRN prefixes.

### Step 5 — Troubleshooting

- **Premium prefix lookup doesn't match enough numbers** — Premium number allocation changes frequently. Subscribe to an IPRN database feed (CFCA, i3 Forum, or commercial providers) and refresh the lookup weekly.

- **`toll_charge` is null for all calls** — Your CDR may not include per-call rating. Estimate costs using the `rate_per_min` field from the prefix lookup. For accurate costing, integrate with your billing/rating engine.

- **False positives from legitimate international calls** — Some businesses legitimately call satellite phones (maritime, remote sites) or high-cost countries. Maintain a whitelist of approved calling parties and destinations. The whitelist should require periodic re-approval.

- **Fraud detection is too slow (15-min lag)** — For sub-minute detection, use real-time SIP signaling monitoring (UC-5.10.4) instead of CDR-based detection. CDRs are generated at call completion, so a long fraud call won't appear until it ends. SIP INVITE monitoring detects the call attempt immediately.

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

## Known False Positives

Time-zone and midnight-boundary rating can cluster calls; also brief drops during gateway failovers, codec renegotiation, or PSTN trunk maintenance can add retries that look like extra attempts.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
