<!-- AUTO-GENERATED from UC-5.9.12.json — DO NOT EDIT -->

---
id: "5.9.12"
title: "Prefix Reachability by Region"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.12 · Prefix Reachability by Region

## Description

Comparing BGP prefix reachability across geographic regions identifies regional outages or ISP-specific routing issues that affect only certain user populations.

## Value

Comparing BGP prefix reachability across geographic regions identifies regional outages or ISP-specific routing issues that affect only certain user populations.

## Implementation

BGP monitors are distributed globally. Group reachability results by `thousandeyes.monitor.location` and aggregate into regions. A prefix that is 100% reachable in Americas but <80% in APAC indicates a regional routing problem.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (BGP tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
BGP monitors are distributed globally. Group reachability results by `thousandeyes.monitor.location` and aggregate into regions. A prefix that is 100% reachable in Americas but <80% in APAC indicates a regional routing problem.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="bgp"
| stats avg(bgp.reachability) as avg_reachability by thousandeyes.monitor.location, network.prefix
| eval region=case(
    match(thousandeyes.monitor.location,"US\|CA\|MX\|BR"),"Americas",
    match(thousandeyes.monitor.location,"GB\|DE\|FR\|NL"),"EMEA",
    match(thousandeyes.monitor.location,"JP\|SG\|AU\|IN"),"APAC",
    1=1,"Other")
| stats avg(avg_reachability) as regional_reachability by region, network.prefix
| sort region, network.prefix
```

Understanding this SPL

**Prefix Reachability by Region** — Comparing BGP prefix reachability across geographic regions identifies regional outages or ISP-specific routing issues that affect only certain user populations.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (BGP tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.monitor.location, network.prefix** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **region** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by region, network.prefix** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Map (reachability by monitor location), Table (region, prefix, reachability), Column chart comparing regions.

## SPL

```spl
`stream_index` thousandeyes.test.type="bgp"
| stats avg(bgp.reachability) as avg_reachability by thousandeyes.monitor.location, network.prefix
| eval region=case(
    match(thousandeyes.monitor.location,"US\|CA\|MX\|BR"),"Americas",
    match(thousandeyes.monitor.location,"GB\|DE\|FR\|NL"),"EMEA",
    match(thousandeyes.monitor.location,"JP\|SG\|AU\|IN"),"APAC",
    1=1,"Other")
| stats avg(avg_reachability) as regional_reachability by region, network.prefix
| sort region, network.prefix
```

## Visualization

Map (reachability by monitor location), Table (region, prefix, reachability), Column chart comparing regions.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
