<!-- AUTO-GENERATED from UC-7.1.77.json — DO NOT EDIT -->

---
id: "7.1.77"
title: "Snowflake Data Sharing and Secure View Access Audit"
criticality: "high"
splunkPillar: "Security"
---

# UC-7.1.77 · Snowflake Data Sharing and Secure View Access Audit

## Description

Consumer queries against secure views and shared objects are high-risk exfiltration paths because they bypass some traditional table ACL models. Retaining ACCESS_HISTORY in Splunk supports investigations when a share’s scope was wider than intended.

## Value

Strengthens data-governance programs for regulated datasets shared across business units or external partners.

## Implementation

Schedule ACCESS_HISTORY with columns `OBJECT_DOMAIN`, `DIRECT_OBJECTS_ACCESSED`, `BASE_OBJECTS_ACCESSED`, `USER_NAME`, `ROLE_NAME`. Enrich with a lookup of approved share consumers. Retain according to legal hold policy; restrict index ACLs. Validate JSON/array fields are flattened for search.

## SPL

```spl
index=datawarehouse sourcetype="snowflake:access_history"
| eval dom=upper(coalesce(OBJECT_DOMAIN, object_domain))
| where dom="VIEW" OR match(_raw,"(?i)share")
| stats dc(QUERY_ID) as queries dc(USER_NAME) as actors dc(ROLE_NAME) as roles values(OBJECT_NAME) as objects by DIRECT_OBJECTS_ACCESSED, _time
| where queries > 0
```

## Visualization

Table (objects, actors, roles), Timeline (queries), Sankey optional with enrichment.

## References

- [Snowflake — Data sharing overview](https://docs.snowflake.com/en/user-guide/data-sharing-intro)
- [Snowflake ACCESS_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/access_history)
