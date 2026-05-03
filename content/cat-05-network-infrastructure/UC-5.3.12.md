<!-- AUTO-GENERATED from UC-5.3.12.json — DO NOT EDIT -->

---
id: "5.3.12"
title: "iRule/Policy Errors (F5 BIG-IP)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.12 · iRule/Policy Errors (F5 BIG-IP)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Fault

*We look for script errors from custom rules on the same box so a bad change to logic does not stay silent while clients see odd failures.*

---

## Description

iRule failures cause unexpected traffic handling — potentially bypassing security or routing traffic incorrectly.

## Value

Application delivery teams detect F5 BIG-IP iRule TCL runtime errors and LTM policy failures that cause connection resets or incorrect traffic routing, correlating error spikes with recent iRule deployments.

## Implementation

Enable iRule logging (sparingly — high volume). Monitor for TCL runtime errors. Alert on any iRule abort events. Review and test iRules in staging before production.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for F5 BIG-IP (`Splunk_TA_f5-bigip`, Splunkbase 2680). F5 iRule and LTM policy logs in `index=network` with `sourcetype=f5:bigip:syslog`. Key fields: iRule errors appear as TCL runtime errors in syslog, LTM policy errors as policy evaluation failures.
* iRules are custom TCL scripts that process traffic on F5. iRule errors cause: (1) connection resets (if the error occurs mid-transaction), (2) performance degradation (TCL exceptions are expensive), (3) unexpected behavior (wrong pool selection, header manipulation failures). Common errors: TCL runtime errors, divide by zero, nil variable references, max loop iterations exceeded.

### Step 1 — - Configure data collection
F5 iRule errors are automatically logged to syslog. Verify:
```spl
index=network sourcetype="f5:bigip:syslog" ("TCL error" OR "iRule error" OR "rule error" OR "01220001" OR "01070151" OR "policy error") earliest=-24h
| stats count by host
```
Note: F5 message ID `01220001` = iRule TCL runtime error, `01070151` = max loop iterations exceeded.

### Step 2 — - Create the search and alert

**Primary search -- iRule/policy error analysis:**
```spl
index=network sourcetype="f5:bigip:syslog" ("TCL error" OR "iRule error" OR "rule error" OR "01220001" OR "01070151" OR "policy error" OR "cannot server" OR "aborted") earliest=-4h
| rex "Rule (?<rule_name>\S+) <(?<event_context>\S+)>: (?<error_detail>.+)"
| eval error_type=case(match(_raw, "01220001"), "TCL_RUNTIME", match(_raw, "01070151"), "MAX_LOOP", match(_raw, "(?i)cannot server"), "POOL_SELECTION_FAIL", match(_raw, "(?i)policy error"), "LTM_POLICY_ERROR", match(_raw, "(?i)abort"), "ABORTED", 1==1, "OTHER")
| stats count as errors dc(rule_name) as affected_rules values(rule_name) as rules values(error_detail) as details latest(_time) as last_error by host, error_type
| eval impact=case(error_type="TCL_RUNTIME", "iRule crashed -- connection may have been reset", error_type="MAX_LOOP", "iRule infinite loop -- performance impact", error_type="POOL_SELECTION_FAIL", "Traffic not being routed correctly", error_type="LTM_POLICY_ERROR", "LTM policy evaluation failed -- fallback behavior", 1==1, "Investigate")
| sort -errors
```

**Error rate trending:**
```spl
index=network sourcetype="f5:bigip:syslog" ("TCL error" OR "iRule error" OR "01220001" OR "01070151" OR "policy error") earliest=-24h
| bin _time span=1h
| stats count as errors by _time, host
| timechart span=1h sum(errors) by host
```

### Step 3 — - Validate
(a) Review active iRules: `tmsh list ltm rule` and identify complex rules.
(b) Intentionally introduce a TCL error in a test iRule and verify it appears in Splunk.
(c) Check the error rate trend -- a spike often correlates with a recent iRule deployment.

### Step 4 — - Operationalize
Dashboard ("F5 -- iRule & Policy Errors"):
* Row 1 -- Single-value: "Total errors (4h)", "Affected rules", "Last error time".
* Row 2 -- Error classification table with rule name, type, and impact.
* Row 3 -- Error rate trending.

Alerting:
* High (> 100 iRule errors in 15 min): iRule causing widespread failures.
* Warning (new rule_name appearing in errors): recently deployed iRule has bugs.

### Step 5 — - Troubleshooting

* **TCL runtime error** -- Check the error_detail for the specific TCL error. Common: "can't read variable" (variable not initialized in all code paths), "invalid command name" (typo or missing package).

* **Max loop iterations** -- iRule has a `while` or `foreach` loop that exceeded the F5 safety limit (default 10000 iterations). Fix the loop logic or increase the limit (not recommended).

* **Errors after iRule deployment** -- Roll back to the previous version: `tmsh load sys config file <backup>`. Debug the iRule in a test environment using `log local0. "debug: $variable"` statements.

## SPL

```spl
index=network sourcetype="f5:bigip:ltm" "TCL error" OR "rule error" OR "aborted"
| rex "Rule (?<rule_name>/\S+)"
| stats count by rule_name, host | sort -count
```

## Visualization

Table (rule name, error count, host), Timechart (errors over time).

## Known False Positives

Bad inputs, new headers, and rare corner cases can fire rule errors; treat as code bugs when volume jumps.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
