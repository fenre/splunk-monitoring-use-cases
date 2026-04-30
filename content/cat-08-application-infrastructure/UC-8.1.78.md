<!-- AUTO-GENERATED from UC-8.1.78.json — DO NOT EDIT -->

---
id: "8.1.78"
title: "Apache Tomcat Valve Request Filtering and Access Pattern Audit"
status: "draft"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.78 · Apache Tomcat Valve Request Filtering and Access Pattern Audit

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Security, Audit &middot; **Status:** Draft

*We use this to support zero-trust and WAF-adjacent controls with evidence of enforcement.*

---

## Description

Valves such as `RemoteAddrValve` and security constraints emit 403/401 in access logs. Auditing stems and sources validates rules and spots probing.

## Value

Supports zero-trust and WAF-adjacent controls with evidence of enforcement.

## Implementation

Enable Access Log Valve in `server.xml`; sync field order with `props.conf`. Correlate 403 spikes with `RemoteAddrValve` deny rules.

## SPL

```spl
index=web sourcetype="tomcat:access"
| where status=403 OR status=401
| stats count by cs_uri_stem, remote_host, status
| sort - count
| head 50
```

## Visualization

Time charts for utilization, tables for top URIs and deploy events, single-value alerts.

## Known False Positives

Spikes or gaps can follow approved maintenance, load tests, or short collection outages. We add a second signal and a change window before escalating.

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
- [Apache Tomcat documentation](https://tomcat.apache.org/tomcat-10.0-doc/config/valve.html)
