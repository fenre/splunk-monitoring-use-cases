<!-- AUTO-GENERATED from UC-4.2.34.json — DO NOT EDIT -->

---
id: "4.2.34"
title: "AKS Diagnostics and Errors"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.2.34 · AKS Diagnostics and Errors

## Description

Control plane and node problems surface as API errors, failed mounts, and ImagePullBackOff; centralized errors shorten MTTR.

## Value

Control plane and node problems surface as API errors, failed mounts, and ImagePullBackOff; centralized errors shorten MTTR.

## Implementation

Enable AKS diagnostic categories for audit and container logs. Ingest to Splunk. Alert on elevated 5xx from API server or repeated ImagePullBackOff patterns. Dashboard by namespace and deployment.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: `sourcetype=mscs:azure:diagnostics` (kube-audit, container logs), Azure Monitor for containers.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable AKS diagnostic categories for audit and container logs. Ingest to Splunk. Alert on elevated 5xx from API server or repeated ImagePullBackOff patterns. Dashboard by namespace and deployment.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:diagnostics" category="kube-audit" "responseStatus.code">=400
| stats count by objectRef.resource, verb, responseStatus.code
| sort -count
```

Understanding this SPL

**AKS Diagnostics and Errors** — Control plane and node problems surface as API errors, failed mounts, and ImagePullBackOff; centralized errors shorten MTTR.

Documented **Data sources**: `sourcetype=mscs:azure:diagnostics` (kube-audit, container logs), Azure Monitor for containers. **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:diagnostics. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by objectRef.resource, verb, responseStatus.code** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (resource, code, count), Timeline (audit errors), Bar chart (namespace).

## SPL

```spl
index=azure sourcetype="mscs:azure:diagnostics" category="kube-audit" "responseStatus.code">=400
| stats count by objectRef.resource, verb, responseStatus.code
| sort -count
```

## Visualization

Table (resource, code, count), Timeline (audit errors), Bar chart (namespace).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
