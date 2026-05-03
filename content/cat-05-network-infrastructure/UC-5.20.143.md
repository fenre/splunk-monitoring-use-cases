<!-- AUTO-GENERATED from UC-5.20.143.json — DO NOT EDIT -->

---
id: "5.20.143"
title: "IPv6 Operational Readiness Scorecard — Composite Health Assessment"
status: "verified"
criticality: "high"
splunkPillar: "Platform"
---

# UC-5.20.143 · IPv6 Operational Readiness Scorecard — Composite Health Assessment

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Platform &middot; **Type:** Compliance, Availability, Security &middot; **Wave:** Run &middot; **Status:** Verified

*This is like a report card for our entire IPv6 deployment. Instead of checking 142 individual things, the bosses see one simple grade from A to F, plus scores in six areas like 'Security' and 'Adoption.' If any area gets a low grade, we know exactly where to focus our improvement efforts. It's the summary page that tells you whether your IPv6 house is in order.*

---

## Description

Composite IPv6 operational readiness scorecard that aggregates signals from across the full IPv6 use case catalog into a single executive-level assessment. Scores six dimensions: (1) Adoption and Visibility, (2) Security Posture, (3) Routing Health, (4) Transition Mechanism Status, (5) Compliance Coverage, and (6) Operational Hygiene. Each dimension scores 0-100, producing an overall grade (A through F).

## Value

Provides C-level and architecture teams with a single, quantified view of IPv6 operational maturity. Instead of reviewing 142 individual monitoring use cases, leadership sees one scorecard with actionable dimensional scores. The scorecard tracks progress over time, identifies the weakest dimensions, and drives targeted improvement. Essential for organizations pursuing IPv6-ready certifications, government mandates (OMB M-21-07), or compliance frameworks requiring IPv6 readiness evidence.

## Implementation

Aggregate signals from existing IPv6 monitoring use cases into six dimension scores. Compute overall grade. Track trend over time.

## Detailed Implementation

### Prerequisites
- Multiple IPv6 monitoring use cases deployed from the 5.20 subcategory.
- Sufficient data ingestion across firewall, router, switch, and sensor sources.

### Step 1 — Deploy foundational IPv6 UCs: Start with UC-5.20.1 (adoption tracking), UC-5.20.28 (RA Guard), UC-5.20.44 (routing), UC-5.20.131 (ICMPv6 policy).

### Step 2 — Create the composite scorecard search. Customize dimension thresholds to your environment.

### Step 3 — Validate: Manually verify each dimension score against known state. Adjust thresholds.

### Step 4 — Operationalize
**Dashboard:** Executive IPv6 readiness scorecard with radar chart and trend.
**Report:** Weekly scorecard email to architecture and security teams.
**KPI:** Overall score in ITSI service tree.

### Step 5 — Troubleshooting
- Low Adoption score: Deploy dual-stack more broadly or enable IPv6 on additional segments.
- Low Security score: Prioritize FHS deployment (UC-5.20.142).
- Low Transition score: Sunset deprecated mechanisms (UC-5.20.138).
- Low Compliance score: Fix ICMPv6 filtering policies (UC-5.20.131).

## SPL

```spl
| makeresults
| eval dimension="Adoption", score=0
| append [search index=network sourcetype=netflow earliest=-24h | eval is_ipv6=if(match(src, ":") OR match(dest, ":"), 1, 0) | stats count(eval(is_ipv6=1)) as ipv6_flows count as total_flows | eval adoption_pct=round(ipv6_flows/total_flows*100, 1) | eval dimension="1_Adoption", score=case(adoption_pct >= 50, 100, adoption_pct >= 25, 75, adoption_pct >= 10, 50, adoption_pct >= 1, 25, 1=1, 0), detail=adoption_pct . "% of flows are IPv6" | fields dimension, score, detail]
| append [search index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-24h ("RA Guard" OR "ND Inspection" OR "SISF" OR "DHCPv6 Guard") ("enabled" OR "active" OR "violation" OR "denied") | stats dc(host) as fhs_hosts | eval dimension="2_Security", score=case(fhs_hosts >= 50, 100, fhs_hosts >= 20, 75, fhs_hosts >= 5, 50, fhs_hosts >= 1, 25, 1=1, 0), detail=fhs_hosts . " switches with FHS active" | fields dimension, score, detail]
| append [search index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-24h ("OSPFv3" OR "BGP.*IPv6" OR "IS-IS.*IPv6") ("neighbor.*up" OR "adjacency.*up" OR "ESTABLISHED") | stats dc(host) as routing_hosts | eval dimension="3_Routing", score=case(routing_hosts >= 20, 100, routing_hosts >= 10, 75, routing_hosts >= 5, 50, routing_hosts >= 1, 25, 1=1, 0), detail=routing_hosts . " routers with healthy IPv6 routing" | fields dimension, score, detail]
| append [search index=network earliest=-24h ("6to4" OR "teredo" OR "isatap" OR "2002:") NOT ("disabled" OR "removed") | stats count as deprecated_flows | eval dimension="4_Transition", score=case(deprecated_flows=0, 100, deprecated_flows < 10, 75, deprecated_flows < 100, 50, deprecated_flows < 1000, 25, 1=1, 0), detail=deprecated_flows . " deprecated transition mechanism flows" | fields dimension, score, detail]
| append [search index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-7d ("ICMPv6" AND ("deny" OR "drop") AND ("type 2" OR "PTB" OR "too big")) | stats count as blocked_ptb | eval dimension="5_Compliance", score=case(blocked_ptb=0, 100, blocked_ptb < 5, 75, blocked_ptb < 50, 50, 1=1, 25), detail=blocked_ptb . " blocked ICMPv6 PTB messages" | fields dimension, score, detail]
| append [search index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe") earliest=-24h ("neighbor.*table.*full" OR "ND.*table.*overflow" OR "rogue.*RA" OR "unauthorized.*RA") | stats count as security_events | eval dimension="6_Hygiene", score=case(security_events=0, 100, security_events < 5, 75, security_events < 20, 50, 1=1, 25), detail=security_events . " NDP security events" | fields dimension, score, detail]
| where dimension!="Adoption"
| sort dimension
| eventstats avg(score) as overall_score
| eval overall_grade=case(overall_score >= 90, "A — Excellent", overall_score >= 75, "B — Good", overall_score >= 60, "C — Fair", overall_score >= 40, "D — Needs Improvement", 1=1, "F — Critical")
| table dimension, score, detail, overall_score, overall_grade
```

## Visualization

(1) Gauge: overall readiness score. (2) Radar chart: six dimensions. (3) Table: dimension scores with details. (4) Trend: weekly score history. (5) Grade letter (A-F) with color.

## Known False Positives

**Dimension weighting.** All dimensions are weighted equally. Organizations may need to adjust weights based on their specific priorities (e.g., government agencies may weight compliance higher).

**Data availability.** Dimensions score low if the underlying data sources are not ingested yet. Low scores may indicate missing data rather than actual operational deficiency.

## References

- [NIST SP 800-119 — Guidelines for the Secure Deployment of IPv6](https://csrc.nist.gov/pubs/sp/800/119/final)
- [OMB M-21-07 — Completing the Transition to IPv6](https://www.whitehouse.gov/wp-content/uploads/2020/11/M-21-07.pdf)
