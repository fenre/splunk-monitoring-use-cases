---
id: "5.3.8"
title: "WAF Policy Violations (F5 BIG-IP ASM)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.3.8 · WAF Policy Violations (F5 BIG-IP ASM)

## Description

WAF violations indicate attacks — SQL injection, XSS, command injection. Trending reveals campaigns.

## Value

WAF violations indicate attacks — SQL injection, XSS, command injection. Trending reveals campaigns.

## Implementation

Enable F5 ASM logging. Dashboard showing top violations, attack sources, and targeted URIs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_f5-bigip` (ASM).
• Ensure the following data sources are available: `sourcetype=f5:bigip:asm:syslog`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable F5 ASM logging. Dashboard showing top violations, attack sources, and targeted URIs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="f5:bigip:asm:syslog"
| stats count by violation_name, src, request_uri, severity | sort -count
```

Understanding this SPL

**WAF Policy Violations (F5 BIG-IP ASM)** — WAF violations indicate attacks — SQL injection, XSS, command injection. Trending reveals campaigns.

Documented **Data sources**: `sourcetype=f5:bigip:asm:syslog`. **App/TA** (typical add-on context): `Splunk_TA_f5-bigip` (ASM). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: f5:bigip:asm:syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="f5:bigip:asm:syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by violation_name, src, request_uri, severity** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Bar chart by violation, Map (source IPs), Timeline.

## SPL

```spl
index=network sourcetype="f5:bigip:asm:syslog"
| stats count by violation_name, src, request_uri, severity | sort -count
```

## Visualization

Table, Bar chart by violation, Map (source IPs), Timeline.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
