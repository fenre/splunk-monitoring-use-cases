<!-- AUTO-GENERATED from UC-1.1.55.json — DO NOT EDIT -->

---
id: "1.1.55"
title: "DNS Resolution Failure Rate"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.55 · DNS Resolution Failure Rate

## Description

Aggregates resolver log lines that show hard failures (SERVFAIL, TIMEOUT) or explicit NXDOMAIN responses for monitored strings, grouped by host and query name so you can see who is failing and for what name.

## Value

Rising DNS failure counts are an early signal for broken upstreams, wedged local resolvers, or application misconfiguration before large user-visible outages stack up.

## Implementation

Forward resolver logs into the OS index. Tune the keyword set to your resolver (not every stack logs `systemd-resolved`). Treat `NXDOMAIN` carefully: include it only when it is unexpected for your app, or split it to a separate alert with a lookup of known-pruned names.

## Detailed Implementation

Prerequisites
• Enable forwarding of resolver logs. **systemd-resolved** often lives under the journal: export via **journald** or **rsyslog** to the same `syslog` sourcetype the TA already parses.

Step 1 — Configure data collection
Add **host**-level filters in inputs.conf to avoid double-ingesting unrelated facilities; tag `query_name` with **SEDCMD** or transforms if the resolver only prints inside `_raw`.

Step 2 — Create the search and alert

```spl
index=os sourcetype=syslog ("systemd-resolved" OR "unbound" OR "named")
| search "SERVFAIL" OR "TIMEOUT" OR (query_level="error" AND "NXDOMAIN")
| stats count as failures by host, query_name
| where failures > 10
```

Simplify the middle line to the sample in the `spl` field if you only have **systemd-resolved** today.

**Understanding this SPL** — Counts problem strings per **host** and **query_name**; raise threshold on busy resolvers or require `>10` per hour with `earliest` bounds.


Step 3 — Validate
From the host, run `resolvectl status` or your resolver’s test CLI; compare to `_raw` lines in Splunk at the same time. For cross-checks, use `dig` or `getent` from an admin shell during a controlled test, not in place of long-term collection.

Step 4 — Operationalize
Send to both platform DNS and the application team when `query_name` shows an app-specific suffix pattern.



## SPL

```spl
index=os sourcetype=syslog "systemd-resolved" ("SERVFAIL" OR "NXDOMAIN" OR "TIMEOUT")
| stats count as failures by host, query_name
| where failures > 10
```

## Visualization

Table, Timechart

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
