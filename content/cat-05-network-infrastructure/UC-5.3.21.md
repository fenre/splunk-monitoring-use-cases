---
id: "5.3.21"
title: "Citrix ADC Responder and Rewrite Policy Errors (NetScaler)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.3.21 · Citrix ADC Responder and Rewrite Policy Errors (NetScaler)

## Description

Responder and rewrite policies on Citrix ADC implement URL redirects, HTTP header manipulation, security rules, and custom error responses. Policy evaluation errors or undef (undefined) hits indicate misconfiguration — the policy expression failed to evaluate, causing the request to fall through to default behavior. This can result in bypassed security headers, missing redirects, or unexpected error pages being served to users.

## Value

Responder and rewrite policies on Citrix ADC implement URL redirects, HTTP header manipulation, security rules, and custom error responses. Policy evaluation errors or undef (undefined) hits indicate misconfiguration — the policy expression failed to evaluate, causing the request to fall through to default behavior. This can result in bypassed security headers, missing redirects, or unexpected error pages being served to users.

## Implementation

Poll the NITRO API `responderpolicy` and `rewritepolicy` resources. Each policy exposes `hits` (successful evaluations) and `undefhits` (evaluation failures). Run every 15 minutes. Alert when any policy has `undefhits > 0` — this indicates the policy expression has a bug. Common causes: referencing a non-existent header, type mismatch in expression, or regex syntax errors. Policies with high `undefhits` relative to `hits` are effectively broken. Also monitor `responderglobal_responderpolicy_binding` and `rewriteglobal_rewritepolicy_binding` for globally bound policies that affect all traffic.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input polling Citrix ADC NITRO API.
• Ensure the following data sources are available: `index=network` `sourcetype="citrix:netscaler:policy"` fields `policy_name`, `policy_type`, `hits`, `undef_hits`, `bound_to`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll the NITRO API `responderpolicy` and `rewritepolicy` resources. Each policy exposes `hits` (successful evaluations) and `undefhits` (evaluation failures). Run every 15 minutes. Alert when any policy has `undefhits > 0` — this indicates the policy expression has a bug. Common causes: referencing a non-existent header, type mismatch in expression, or regex syntax errors. Policies with high `undefhits` relative to `hits` are effectively broken. Also monitor `responderglobal_responderpolicy_bind…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="citrix:netscaler:policy"
| where undef_hits > 0
| eval error_ratio=if(hits>0, round(undef_hits/hits*100,2), 100)
| sort -undef_hits
| table policy_name, policy_type, bound_to, hits, undef_hits, error_ratio, host
```

Understanding this SPL

**Citrix ADC Responder and Rewrite Policy Errors (NetScaler)** — Responder and rewrite policies on Citrix ADC implement URL redirects, HTTP header manipulation, security rules, and custom error responses. Policy evaluation errors or undef (undefined) hits indicate misconfiguration — the policy expression failed to evaluate, causing the request to fall through to default behavior. This can result in bypassed security headers, missing redirects, or unexpected error pages being served to users.

Documented **Data sources**: `index=network` `sourcetype="citrix:netscaler:policy"` fields `policy_name`, `policy_type`, `hits`, `undef_hits`, `bound_to`. **App/TA** (typical add-on context): Custom scripted input polling Citrix ADC NITRO API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: citrix:netscaler:policy. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="citrix:netscaler:policy". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where undef_hits > 0` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **error_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Citrix ADC Responder and Rewrite Policy Errors (NetScaler)**): table policy_name, policy_type, bound_to, hits, undef_hits, error_ratio, host


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (policies with undef hits), Bar chart (error ratio by policy type), Timeline (undef hits trending).

## SPL

```spl
index=network sourcetype="citrix:netscaler:policy"
| where undef_hits > 0
| eval error_ratio=if(hits>0, round(undef_hits/hits*100,2), 100)
| sort -undef_hits
| table policy_name, policy_type, bound_to, hits, undef_hits, error_ratio, host
```

## Visualization

Table (policies with undef hits), Bar chart (error ratio by policy type), Timeline (undef hits trending).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
