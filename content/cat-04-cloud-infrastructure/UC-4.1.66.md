---
id: "4.1.66"
title: "AWS Config Rule Compliance Drift"
criticality: "medium"
splunkPillar: "Security"
---

# UC-4.1.66 · AWS Config Rule Compliance Drift

## Description

Resources oscillating between COMPLIANT and NON_COMPLIANT indicate automation fights or manual changes—drift trends surface systemic issues.

## Value

Resources oscillating between COMPLIANT and NON_COMPLIANT indicate automation fights or manual changes—drift trends surface systemic issues.

## Implementation

Ingest configuration item change streams. Track flapping rules weekly. Alert when critical rules (encryption, public access) change state more than N times per day. Root-cause with CloudTrail correlation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_aws`.
• Ensure the following data sources are available: `sourcetype=aws:config:notification`, Config history snapshots.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest configuration item change streams. Track flapping rules weekly. Alert when critical rules (encryption, public access) change state more than N times per day. Root-cause with CloudTrail correlation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:config:notification" configRuleList{}.complianceType=*
| mvexpand configRuleList{} limit=500
| spath input=configRuleList{} path=complianceType
| spath input=configRuleList{} path=configRuleName
| stats dc(complianceType) as state_changes by resourceId, configRuleName
| where state_changes > 1
| sort -state_changes
```

Understanding this SPL

**AWS Config Rule Compliance Drift** — Resources oscillating between COMPLIANT and NON_COMPLIANT indicate automation fights or manual changes—drift trends surface systemic issues.

Documented **Data sources**: `sourcetype=aws:config:notification`, Config history snapshots. **App/TA** (typical add-on context): `Splunk_TA_aws`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:config:notification. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:config:notification". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Expands multivalue fields with `mvexpand` — use `limit=` to cap row explosion.
• Extracts structured paths (JSON/XML) with `spath`.
• Extracts structured paths (JSON/XML) with `spath`.
• `stats` rolls up events into metrics; results are split **by resourceId, configRuleName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where state_changes > 1` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (resource, rule, changes), Line chart (compliant % over time), Single value (flapping resources).

## SPL

```spl
index=aws sourcetype="aws:config:notification" configRuleList{}.complianceType=*
| mvexpand configRuleList{} limit=500
| spath input=configRuleList{} path=complianceType
| spath input=configRuleList{} path=configRuleName
| stats dc(complianceType) as state_changes by resourceId, configRuleName
| where state_changes > 1
| sort -state_changes
```

## Visualization

Table (resource, rule, changes), Line chart (compliant % over time), Single value (flapping resources).

## References

- [Splunk_TA_aws](https://splunkbase.splunk.com/app/1876)
