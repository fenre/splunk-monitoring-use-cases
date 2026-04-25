<!-- AUTO-GENERATED from UC-7.1.81.json — DO NOT EDIT -->

---
id: "7.1.81"
title: "Snowflake Row Access Policy and Dynamic Masking Evidence"
criticality: "high"
splunkPillar: "Security"
---

# UC-7.1.81 · Snowflake Row Access Policy and Dynamic Masking Evidence

## Description

Regulators and internal risk teams need proof that sensitive tables were accessed only under active row access or masking policies. Mining ACCESS_HISTORY for applied policy payloads demonstrates controls were in force for each query.

## Value

Supports SOX, GDPR, and healthcare governance reviews without manual Snowflake UI sampling.

## Implementation

Ensure ACCESS_HISTORY export includes `POLICIES_APPLIED` JSON; use `spath` or indexed extraction in `props.conf` for policy names. Join to data dictionary for table classification. Restrict index to GRC roles. Document lag versus real time (ACCOUNT_USAGE latency).

## SPL

```spl
index=datawarehouse sourcetype="snowflake:access_history"
| search POLICIES_APPLIED=* OR match(_raw,"(?i)row access policy") OR match(_raw,"(?i)masking policy")
| eval pol=coalesce(POLICIES_APPLIED, policies_applied)
| stats dc(QUERY_ID) as queries dc(USER_NAME) as actors by OBJECT_NAME, pol
| where queries > 0
| sort -queries
```

## Visualization

Table (object, policy, queries, actors), Timeline.

## References

- [Snowflake — Row access policies](https://docs.snowflake.com/en/user-guide/security-row-intro)
- [Snowflake — Dynamic data masking](https://docs.snowflake.com/en/user-guide/security-column-intro)
