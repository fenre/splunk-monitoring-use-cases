<!-- AUTO-GENERATED from UC-2.6.79.json — DO NOT EDIT -->

---
id: "2.6.79"
title: "Citrix Secure Private Access (ZTNA) Session Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.79 · Citrix Secure Private Access (ZTNA) Session Monitoring

## Description

Zero-trust access to private web and TCP apps should enforce policy, give visibility into application categories, and still feel responsive. Monitoring successful versus blocked sessions, connector path health, and round-trip time highlights misconfiguration, over-broad or over-tight rules, and performance issues on browser-based and agent-based paths alike.

## Value

Zero-trust access to private web and TCP apps should enforce policy, give visibility into application categories, and still feel responsive. Monitoring successful versus blocked sessions, connector path health, and round-trip time highlights misconfiguration, over-broad or over-tight rules, and performance issues on browser-based and agent-based paths alike.

## Implementation

Ingest the cloud service feed in near real time. Map internal app names to a category lookup for business-friendly breakdowns. Alert on block spikes, connector-down patterns, and sustained high RTT by region. Pair with traditional gateway logs during migration. Document split between legacy full tunnel and this access path for the same app families.

## Detailed Implementation

Prerequisites: ZTNA logging subscribed to your sink with HEC or cloud connector into index=ztna; category taxonomy aligned with security. Step 1: Configure data collection — Confirm field names in a pilot; props.conf [citrix:ztna:session] and [citrix:ztna:connector] with FIELDALIAS for rtt_ms, app_category, and result. Step 2: Create the search and alert — Create separate saved searches: policy blocks, connector health, and RTT SLO; start with median rtt>250ms (tune from baseline) and add per-region thresholds. Step 3: Validate — After approved allow/deny tests in non-production, run `index=ztna (sourcetype="citrix:ztna:session" OR sourcetype="citrix:ztna:connector") earliest=-20m | stats count by result, app, app_category` to confirm tags. Step 4: Operationalize — Publish the dashboard to security and EUC; refresh when new app groups publish; if blocks or high RTT remain steady, escalate to the Citrix Secure Private Access and connector owner teams.

## SPL

```spl
index=ztna (sourcetype="citrix:ztna:session" OR sourcetype="citrix:ztna:access" OR sourcetype="citrix:ztna:connector") earliest=-4h
| eval ok=if(match(lower(result),"(?i)allow|success|established|up"),1,0), rtt=tonumber(rtt_ms), cat=coalesce(app_category, category, "uncategorized"), bfail=if(match(lower(result),"(?i)block|deny|fail|down|timeout"),1,0)
| bin _time span=5m
| stats count as n, sum(ok) as okc, sum(bfail) as blks, median(rtt) as medrtt, values(cat) as cats by _time, user, app
| where blks>0 OR (isnotnull(medrtt) AND medrtt>250)
| table _time, user, app, n, okc, blks, medrtt, cats
```

## Visualization

Sankey: user to app to outcome; timechart: block rate; map or bar: by region; table: high RTT with category.

## References

- [Citrix — Secure Private Access (ZTNA) overview](https://docs.citrix.com/en-us/citrix-secure-private-access/)
