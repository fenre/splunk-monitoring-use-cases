<!-- AUTO-GENERATED from UC-5.3.21.json — DO NOT EDIT -->

---
id: "5.3.21"
title: "Citrix ADC Responder and Rewrite Policy Errors (NetScaler)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.3.21 · Citrix ADC Responder and Rewrite Policy Errors (NetScaler)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Fault

*We look for policy misses on responder and rewrite so odd headers and rare clients do not fail silently in a long tail of one-off cases.*

---

## Description

Responder and rewrite policies on Citrix ADC implement URL redirects, HTTP header manipulation, security rules, and custom error responses. Policy evaluation errors or undef (undefined) hits indicate misconfiguration — the policy expression failed to evaluate, causing the request to fall through to default behavior. This can result in bypassed security headers, missing redirects, or unexpected error pages being served to users.

## Value

Application delivery teams detect Citrix ADC responder and rewrite policy errors that cause incorrect redirects, broken header manipulation, or application-level failures.

## Implementation

Poll the NITRO API `responderpolicy` and `rewritepolicy` resources. Each policy exposes `hits` (successful evaluations) and `undefhits` (evaluation failures). Run every 15 minutes. Alert when any policy has `undefhits > 0` — this indicates the policy expression has a bug. Common causes: referencing a non-existent header, type mismatch in expression, or regex syntax errors. Policies with high `undefhits` relative to `hits` are effectively broken. Also monitor `responderglobal_responderpolicy_binding` and `rewriteglobal_rewritepolicy_binding` for globally bound policies that affect all traffic.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). Citrix ADC syslog with responder and rewrite policy error messages. Key fields: `policy_name`, `policy_type` (responder/rewrite), `action`, `error_reason`, `vserver`.
* Responder policies: return custom responses (redirects, error pages, rate limiting). Rewrite policies: modify HTTP headers, URLs, or body content. Errors in these policies cause: (1) incorrect redirects, (2) broken header manipulation, (3) application errors.

### Step 1 — - Configure data collection
Verify responder/rewrite events:
```spl
index=netscaler sourcetype="citrix:netscaler:syslog" ("responder" OR "rewrite" OR "RESP_" OR "RW_") earliest=-24h
| where match(_raw, "(?i)(error|fail|invalid|undefined)")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Responder/rewrite policy errors:**
```spl
index=netscaler sourcetype="citrix:netscaler:syslog" ("responder" OR "rewrite" OR "RESP_" OR "RW_") earliest=-4h
| where match(_raw, "(?i)(error|fail|invalid|undefined|exception|syntax)")
| eval policy_type=if(match(_raw, "(?i)responder"), "Responder", "Rewrite")
| rex "(?i)(?:policy|action)\s+(?<policy_name>\S+)"
| eval error=coalesce(error_reason, if(match(_raw, "(?i)undefined"), "Undefined variable", if(match(_raw, "(?i)syntax"), "Syntax error", if(match(_raw, "(?i)invalid"), "Invalid expression", "Unknown error"))))
| stats count as errors latest(_time) as last_error by host, policy_type, policy_name, error
| eval severity=case(errors > 100, "HIGH -- frequent policy errors", errors > 10, "WARNING", 1==1, "INFO")
| sort severity, -errors
```

### Step 3 — - Validate
(a) On ADC CLI: `show responder policy <policy>` and `show rewrite policy <policy>` -- check for errors.
(b) Create a test policy with an intentional error and verify it appears.
(c) Check policy hit counters: `stat responder policy <policy>`.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- Policy Errors"):
* Row 1 -- Single-value: "Total policy errors (4h)", "Responder errors", "Rewrite errors".
* Row 2 -- Policy error detail table.

Alerting:
* High (> 100 policy errors in 15 min): widespread policy failures impacting traffic.
* Warning (new policy name appearing in errors): recently deployed policy has issues.

### Step 5 — - Troubleshooting

* **"Undefined variable" error** -- The policy expression references a header or variable that doesn't exist in the request. Check: `show responder action <action>` -- verify the target expression.

* **Errors after policy deployment** -- Roll back: unbind the policy from the vserver and rebind the previous version.

* **High error rate on specific URL patterns** -- The policy expression may not handle all URL variations. Test with: `show policy expression <expr> -eval`.

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

## Known False Positives

Typos, new headers, and rare clients can make responder or rewrite actions miss; not every miss is an attack.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
