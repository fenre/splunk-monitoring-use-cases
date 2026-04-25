<!-- AUTO-GENERATED from UC-2.10.9.json — DO NOT EDIT -->

---
id: "2.10.9"
title: "VxRail Secure Remote Services (SRS) / Call Home Connectivity Health"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.10.9 · VxRail Secure Remote Services (SRS) / Call Home Connectivity Health

## Description

Broken call-home paths delay proactive case creation and parts dispatch. Operators may not notice until a fault occurs.

## Value

Restores predictive support value and shortens hardware RMA cycles.

## Implementation

Test endpoints from automation weekly. Alert on failed reachability. Document firewall allow lists in the runbook link.

## SPL

```spl
index=vxrail sourcetype="vxrail:support_gateway" earliest=-24h
| eval ok=lower(dell_services_reachable)
| eval gs=lower(gateway_state)
| where ok="false" OR match(gs, "(?i)down|error") OR match(lower(coalesce(proxy_error, _raw)), "(?i)proxy|tls|timeout")
| stats latest(last_successful_upload) as last_up, values(proxy_error) as errs
```

## Visualization

Single value connectivity; timeline tests; error codes table.

## References

- [Secure Connect Gateway (Dell)](https://www.dell.com/support/kbdoc/en-us/000178280/dell-emc-secure-connect-gateway)
