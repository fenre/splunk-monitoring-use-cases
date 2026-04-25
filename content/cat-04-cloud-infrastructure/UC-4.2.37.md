<!-- AUTO-GENERATED from UC-4.2.37.json — DO NOT EDIT -->

---
id: "4.2.37"
title: "Front Door WAF Blocks"
criticality: "high"
splunkPillar: "Security"
---

# UC-4.2.37 · Front Door WAF Blocks

## Description

Managed rule blocks protect origins; tracking rule IDs separates scanning noise from targeted application abuse.

## Value

Managed rule blocks protect origins; tracking rule IDs separates scanning noise from targeted application abuse.

## Implementation

Enable WAF logs on Front Door profile. Ingest to Splunk. Dashboard OWASP rule groups. Create exceptions carefully with SecOps. Correlate with origin 5xx to avoid blocking good clients.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_microsoft-cloudservices`.
• Ensure the following data sources are available: Front Door diagnostic logs (WebApplicationFirewallLog).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable WAF logs on Front Door profile. Ingest to Splunk. Dashboard OWASP rule groups. Create exceptions carefully with SecOps. Correlate with origin 5xx to avoid blocking good clients.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=azure sourcetype="mscs:azure:diagnostics" log_s="WebApplicationFirewallLog" action_s="Block"
| stats count by ruleName_s, clientIP_s, hostName_s
| sort -count
```

Understanding this SPL

**Front Door WAF Blocks** — Managed rule blocks protect origins; tracking rule IDs separates scanning noise from targeted application abuse.

Documented **Data sources**: Front Door diagnostic logs (WebApplicationFirewallLog). **App/TA** (typical add-on context): `Splunk_TA_microsoft-cloudservices`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: azure; **sourcetype**: mscs:azure:diagnostics. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=azure, sourcetype="mscs:azure:diagnostics". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by ruleName_s, clientIP_s, hostName_s** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (ruleName), Table (client IP, URI), Timeline (block rate).

## SPL

```spl
index=azure sourcetype="mscs:azure:diagnostics" log_s="WebApplicationFirewallLog" action_s="Block"
| stats count by ruleName_s, clientIP_s, hostName_s
| sort -count
```

## Visualization

Bar chart (ruleName), Table (client IP, URI), Timeline (block rate).

## References

- [Splunk_TA_microsoft-cloudservices](https://splunkbase.splunk.com/app/3110)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
