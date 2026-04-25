<!-- AUTO-GENERATED from UC-9.4.22.json — DO NOT EDIT -->

---
id: "9.4.22"
title: "BeyondTrust Password Safe Credential Release Volume by Asset"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.4.22 · BeyondTrust Password Safe Credential Release Volume by Asset

## Description

Credential checkout and release activity grouped by user and managed system highlights overuse of shared break-glass accounts and unusual access to crown-jewel assets.

## Value

Gives IAM and server owners a quantitative view of vault usage beyond static session recordings, supporting access reviews and separation-of-duty reporting.

## Implementation

Align `index`, `sourcetype`, and `source` with BeyondTrust’s Splunk connector configuration. Replace the `_raw` keyword match with explicit `EventType` or `MessageType` fields once validated in your environment. Enrich `asset` with CMDB ownership. Suppress service automation accounts via lookup.

## Detailed Implementation

Prerequisites
• Install and configure: BeyondTrust Password Safe / Cloud Dashboard for Splunk (Splunkbase 5574) with Splunk HTTP Event Collector.
• Data sources: Password Safe Splunk Event Forwarder `sourcetype=beyondtrust` or `source=password_safe`.

Step 1 — Configure data collection
Align `index`, `sourcetype`, and `source` with BeyondTrust’s Splunk connector configuration. Replace the `_raw` keyword match with explicit `EventType` or `MessageType` fields once validated in your environment. Enrich `asset` with CMDB ownership. Suppress service automation accounts via lookup.

Step 2 — Create the search and alert

```spl
index=pam (sourcetype=beyondtrust OR source=password_safe) earliest=-24h
| eval user=coalesce(UserName, user, User, "")
| eval asset=coalesce(SystemName, TargetSystem, ManagedAccount, host, "")
| search user!="" asset!=""
| where match(lower(_raw), "(?i)password|credential|checkout|retrieve|release")
| stats count by user, asset
| sort -count
```

Step 3 — Validate
Compare with BeyondTrust Password Safe reports and safe lists for the same users, assets, and time range.

Step 4 — Operationalize
Add to a dashboard or alert; document the owner. Table (user × asset), heatmap, timechart of daily checkouts.

## SPL

```spl
index=pam (sourcetype=beyondtrust OR source=password_safe) earliest=-24h
| eval user=coalesce(UserName, user, User, "")
| eval asset=coalesce(SystemName, TargetSystem, ManagedAccount, host, "")
| search user!="" asset!=""
| where match(lower(_raw), "(?i)password|credential|checkout|retrieve|release")
| stats count by user, asset
| sort -count
```

## Visualization

Table (user × asset), heatmap, timechart of daily checkouts.

## References

- [BeyondTrust Password Safe / Cloud Dashboard for Splunk](https://splunkbase.splunk.com/app/5574)
- [BeyondTrust Splunk integration (Event Forwarder)](https://docs.beyondtrust.com/bips/docs/bi-splunk-integration)
