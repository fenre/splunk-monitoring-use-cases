<!-- AUTO-GENERATED from UC-9.8.4.json — DO NOT EDIT -->

---
id: "9.8.4"
title: "BeyondTrust Privilege Elevation Request Denial Rate Monitoring"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.8.4 · BeyondTrust Privilege Elevation Request Denial Rate Monitoring

## Description

A sustained high denial rate can mean over-tight policies (hurting IT productivity) or attackers probing elevation paths. Tracking denials per user and day balances usability with detection of abusive requests.

## Value

Guides policy tuning for BeyondTrust elevation workflows and highlights accounts that may be compromised or insider testing boundaries.

## Implementation

(1) Standardize result field values across Windows and Mac agents. (2) Exclude known service accounts. (3) Baseline denial rates by team. (4) Cross-check with IdP risky sign-ins. (5) Offer self-service training when denial spikes follow application upgrades.

## SPL

```spl
index=pam sourcetype="beyondtrust:pam" earliest=-30d@d
| eval res=coalesce(result, Result, outcome, Outcome, status, "")
| eval user=coalesce(user, UserName, requester, "")
| eval app=coalesce(application, Application, target_app, "")
| bin _time span=1d
| stats count(eval(match(lower(res),"(?i)denied|reject|fail"))) as denied count as total by _time user
| eval deny_pct=round(100*denied/total,2)
| where total>=10 AND deny_pct>50
| sort -deny_pct
```

## Visualization

Line chart (denial % over time), bar chart (top users), heatmap (user × day).

## References

- [BeyondTrust — Endpoint Privilege Management](https://www.beyondtrust.com/endpoint-privilege-management)
- [Splunk Docs — eval](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Eval)
