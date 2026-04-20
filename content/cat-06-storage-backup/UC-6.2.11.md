---
id: "6.2.11"
title: "Object Versioning Compliance"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.2.11 · Object Versioning Compliance

## Description

Buckets without versioning risk unrecoverable overwrites. Monitoring ensures critical buckets remain versioned per data policy.

## Value

Buckets without versioning risk unrecoverable overwrites. Monitoring ensures critical buckets remain versioned per data policy.

## Implementation

Map critical buckets via lookup. Alert when versioning is suspended or never enabled on tagged buckets. Include MFA delete status in extended implementation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: AWS Config, Azure Policy compliance states.
• Ensure the following data sources are available: `GetBucketVersioning`, Config rule compliance.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Map critical buckets via lookup. Alert when versioning is suspended or never enabled on tagged buckets. Include MFA delete status in extended implementation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=aws sourcetype="aws:config:rule"
| search configRuleName="*s3-bucket-versioning*" OR resourceType="AWS::S3::Bucket"
| spath output=versioning resource.configuration.versioning.status
| where versioning!="Enabled" AND complianceType="NON_COMPLIANT"
| table resourceId, complianceType, versioning
```

Understanding this SPL

**Object Versioning Compliance** — Buckets without versioning risk unrecoverable overwrites. Monitoring ensures critical buckets remain versioned per data policy.

Documented **Data sources**: `GetBucketVersioning`, Config rule compliance. **App/TA** (typical add-on context): AWS Config, Azure Policy compliance states. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: aws; **sourcetype**: aws:config:rule. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=aws, sourcetype="aws:config:rule". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• Extracts structured paths (JSON/XML) with `spath`.
• Filters the current rows with `where versioning!="Enabled" AND complianceType="NON_COMPLIANT"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Object Versioning Compliance**): table resourceId, complianceType, versioning


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (non-compliant buckets), Single value (buckets without versioning), Status grid (bucket × region).

## SPL

```spl
index=aws sourcetype="aws:config:rule"
| search configRuleName="*s3-bucket-versioning*" OR resourceType="AWS::S3::Bucket"
| spath output=versioning resource.configuration.versioning.status
| where versioning!="Enabled" AND complianceType="NON_COMPLIANT"
| table resourceId, complianceType, versioning
```

## Visualization

Table (non-compliant buckets), Single value (buckets without versioning), Status grid (bucket × region).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
