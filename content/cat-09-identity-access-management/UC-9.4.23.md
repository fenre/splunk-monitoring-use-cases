<!-- AUTO-GENERATED from UC-9.4.23.json — DO NOT EDIT -->

---
id: "9.4.23"
title: "BeyondTrust Password Safe Denied or Failed Access Attempts"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.4.23 · BeyondTrust Password Safe Denied or Failed Access Attempts

## Description

Failed or denied Password Safe operations often precede brute force, policy violations, or attackers probing shared credentials.

## Value

Adds vault-layer detection that complements IdP sign-in logs—especially when attackers already possess a password but lack approval workflow.

## Implementation

Map `src_ip` when the connector includes it; some deployments require `rex` from `_raw`. Normalize result strings per BeyondTrust documentation. Tune out expected lockouts from scanners. Correlate repeated failures with MFA and SOAR playbooks.

## Detailed Implementation

Prerequisites
• Install and configure: BeyondTrust Password Safe / Cloud Dashboard for Splunk (Splunkbase 5574).
• Data sources: Password Safe security events forwarded to Splunk (`sourcetype=beyondtrust` or `source=password_safe`).

Step 1 — Configure data collection
Map `src_ip` when the connector includes it; some deployments require `rex` from `_raw`. Normalize result strings per BeyondTrust documentation. Tune out expected lockouts from scanners. Correlate repeated failures with MFA and SOAR playbooks.

Step 2 — Create the search and alert

```spl
index=pam (sourcetype=beyondtrust OR source=password_safe) earliest=-24h
| eval user=coalesce(UserName, user, User, "")
| eval result=coalesce(Result, Status, Outcome, "")
| where match(lower(result), "(?i)deny|fail|block|invalid|unauthor")
 OR match(lower(_raw), "(?i)denied|failed|authentication failure")
| stats count values(result) as outcomes by user, src_ip
| sort -count
```

Step 3 — Validate
Compare with BeyondTrust Password Safe security and audit views for the same users, source IPs, and time window.

Step 4 — Operationalize
Add to a dashboard or alert; document the owner. Table (user × source IP), bar chart (outcomes), timeline.

## SPL

```spl
index=pam (sourcetype=beyondtrust OR source=password_safe) earliest=-24h
| eval user=coalesce(UserName, user, User, "")
| eval result=coalesce(Result, Status, Outcome, "")
| where match(lower(result), "(?i)deny|fail|block|invalid|unauthor")
 OR match(lower(_raw), "(?i)denied|failed|authentication failure")
| stats count values(result) as outcomes by user, src_ip
| sort -count
```

## Visualization

Table (user × source IP), bar chart (outcomes), timeline.

## References

- [BeyondTrust Password Safe / Cloud Dashboard for Splunk](https://splunkbase.splunk.com/app/5574)
- [BeyondTrust Splunk integration](https://docs.beyondtrust.com/bips/docs/bi-splunk-integration)
