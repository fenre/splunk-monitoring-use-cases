<!-- AUTO-GENERATED from UC-4.4.11.json — DO NOT EDIT -->

---
id: "4.4.11"
title: "Cloud Encryption and Key Rotation Compliance"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.4.11 · Cloud Encryption and Key Rotation Compliance

## Description

Unencrypted resources or keys past rotation date violate compliance. Central view across clouds supports audit and remediation.

## Value

Unencrypted resources or keys past rotation date violate compliance. Central view across clouds supports audit and remediation.

## Implementation

Use native compliance (Config rules, Azure Policy, SCC) or CSPM to evaluate encryption and key rotation. Ingest findings. Dashboard non-compliant resources by rule and cloud. Alert on new non-compliant critical resources.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Config/Security Hub, Defender, SCC, or CSPM.
• Ensure the following data sources are available: AWS Config (encryption rules), Azure Policy (encryption compliance), GCP SCC (crypto key rotation).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use native compliance (Config rules, Azure Policy, SCC) or CSPM to evaluate encryption and key rotation. Ingest findings. Dashboard non-compliant resources by rule and cloud. Alert on new non-compliant critical resources.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:config:notification" configRuleList{}.configRuleName=*encryption*
| search complianceType="NON_COMPLIANT"
| table _time resourceType resourceId configRuleList{}.configRuleName
```

Understanding this SPL

**Cloud Encryption and Key Rotation Compliance** — Unencrypted resources or keys past rotation date violate compliance. Central view across clouds supports audit and remediation.

Documented **Data sources**: AWS Config (encryption rules), Azure Policy (encryption compliance), GCP SCC (crypto key rotation). **App/TA** (typical add-on context): Config/Security Hub, Defender, SCC, or CSPM. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:config:notification. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:config:notification". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Pipeline stage (see **Cloud Encryption and Key Rotation Compliance**): table _time resourceType resourceId configRuleList{}.configRuleName


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (resource, rule, cloud, status), Pie chart (compliant %), Bar chart (non-compliant by rule).

## SPL

```spl
index=aws sourcetype="aws:config:notification" configRuleList{}.configRuleName=*encryption*
| search complianceType="NON_COMPLIANT"
| table _time resourceType resourceId configRuleList{}.configRuleName
```

## Visualization

Table (resource, rule, cloud, status), Pie chart (compliant %), Bar chart (non-compliant by rule).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
