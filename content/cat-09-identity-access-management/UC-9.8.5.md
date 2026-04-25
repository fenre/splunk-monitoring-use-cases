<!-- AUTO-GENERATED from UC-9.8.5.json — DO NOT EDIT -->

---
id: "9.8.5"
title: "BeyondTrust Password Safe Credential Rotation Compliance"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.8.5 · BeyondTrust Password Safe Credential Rotation Compliance

## Description

Stale shared credentials violate SOX, PCI, and cyber-insurance expectations. Comparing last successful rotation timestamps from Password Safe to per-system SLAs surfaces accounts that bypass automated rotation jobs.

## Value

Prevents credential-sprawl incidents and gives GRC teams defensible metrics on vault hygiene across server tiers.

## Implementation

(1) Build `pam_rotation_sla.csv` mapping system groups to max age. (2) Ensure rotation success events are distinct from failed attempts. (3) Exclude break-glass accounts with manual evidence workflow. (4) Auto-ticket owners when overdue. (5) Review quarterly with IAM.

## SPL

```spl
index=pam sourcetype="beyondtrust:vault" earliest=-60d
| eval evt=lower(coalesce(event_type, EventType, action, Action, ""))
| eval acct=coalesce(account_name, AccountName, system_account, "")
| eval sys=coalesce(system_name, SystemName, asset, "")
| where match(evt, "(?i)rotate|change.password|reconcile|verification")
| stats latest(_time) as last_rotation by acct sys
| eval days_since=round((now()-last_rotation)/86400,1)
| lookup pam_rotation_sla.csv system_tier OUTPUT max_days
| eval max_days=coalesce(max_days,90)
| where days_since>max_days
| sort -days_since
```

## Visualization

Table (account, system, days since rotation, SLA), bar chart (overdue by tier), single-value (percent compliant).

## References

- [BeyondTrust — automated password management](https://www.beyondtrust.com/privileged-password-management)
- [NIST SP 800-63B — password lifecycle guidance (context)](https://pages.nist.gov/800-63-3/sp800-63b.html)
