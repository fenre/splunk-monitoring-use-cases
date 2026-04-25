<!-- AUTO-GENERATED from UC-9.8.6.json — DO NOT EDIT -->

---
id: "9.8.6"
title: "BeyondTrust Emergency Access Break-Glass Account Usage Audit"
criticality: "critical"
splunkPillar: "Security"
---

# UC-9.8.6 · BeyondTrust Emergency Access Break-Glass Account Usage Audit

## Description

Break-glass paths are powerful and rarely used; each invocation should be deliberate, approved, and reconciled. Centralizing BeyondTrust emergency events supports insider-threat reviews and proves governance to auditors.

## Value

Reduces abuse of standing emergency accounts and speeds post-incident attestation when adrenaline-driven access was granted.

## Implementation

(1) Tag emergency policies in BeyondTrust and ensure distinct log signatures. (2) Require ticket or MFA approval IDs in the event payload. (3) Alert if emergency access fires outside IR windows. (4) Monthly IAM review with signed checklist. (5) Integrate with SOAR for automatic case creation.

## SPL

```spl
index=pam sourcetype="beyondtrust:pam" earliest=-90d
| eval raw=lower(_raw)
| where match(raw, "(?i)emergency|break.glass|firecall|egress|crisis")
| eval user=coalesce(user, UserName, operator, "")
| eval approver=coalesce(approver, Approver, ticket_id, TicketID, "")
| eval target=coalesce(target_host, TargetHost, system, "")
| stats count earliest(_time) as first_use latest(_time) as last_use values(approver) as approvals by user target
| sort -count
```

## Visualization

Table (user, target, uses, approvals), timeline, bar chart (monthly break-glass count).

## References

- [NIST SP 800-53 — AC-2 (account management) supplementary discussion](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [BeyondTrust — privileged access best practices](https://www.beyondtrust.com/resources/whitepapers)
