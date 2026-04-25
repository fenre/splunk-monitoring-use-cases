<!-- AUTO-GENERATED from UC-9.8.2.json — DO NOT EDIT -->

---
id: "9.8.2"
title: "BeyondTrust Password Safe Credential Checkout and Check-In Cycle Time"
criticality: "medium"
splunkPillar: "Security"
---

# UC-9.8.2 · BeyondTrust Password Safe Credential Checkout and Check-In Cycle Time

## Description

Credentials checked out for many hours increase lateral movement risk if an endpoint is compromised. Measuring checkout-to-check-in duration enforces least-privilege time bounds and detects abandoned sessions.

## Value

Reduces standing privilege exposure and gives IAM leaders quantitative insight into Password Safe hygiene versus policy targets.

## Implementation

(1) Align `event_type` strings to checkout and check-in pairs. (2) If `transaction` is heavy, pre-build session IDs in the TA. (3) Set max checkout SLA (for example four hours) by asset tier via lookup. (4) Auto-expire in Password Safe where supported. (5) Feed outliers to line managers monthly.

## SPL

```spl
index=pam sourcetype="beyondtrust:vault" earliest=-7d
| eval evt=lower(coalesce(event_type, EventType, action, Action, ""))
| eval acct=coalesce(account_name, AccountName, credential, "")
| eval user=coalesce(user, UserName, requester, "")
| eval sess=coalesce(session_id, SessionID, checkout_id, CheckoutID, "")
| eval t_checkout=if(match(evt,"checkout"),_time,null())
| eval t_checkin=if(match(evt,"checkin|check.in|return"),_time,null())
| stats min(t_checkout) as checkout_ts max(t_checkin) as checkin_ts by user acct sess
| eval hours_open=round((checkin_ts-checkout_ts)/3600,2)
| where hours_open>4 OR isnull(checkin_ts)
| table checkout_ts checkin_ts user acct hours_open
```

## Visualization

Histogram (duration distribution), table (longest checkouts), timeline.

## References

- [BeyondTrust — Password Safe](https://www.beyondtrust.com/privileged-password-management)
- [Splunk Docs — transaction](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Transaction)
