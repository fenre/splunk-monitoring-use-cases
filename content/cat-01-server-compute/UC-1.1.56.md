<!-- AUTO-GENERATED from UC-1.1.56.json — DO NOT EDIT -->

---
id: "1.1.56"
title: "Firewall Rule Hit Tracking (iptables/nftables)"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.1.56 · Firewall Rule Hit Tracking (iptables/nftables)

## Description

Builds a top-list of kernel-style firewall block lines that mention UFW or explicit DENY/REJECT/DROP actions, to spot surges in blocked flows by source, port, and protocol.

## Value

A sudden climb in denials for a single port or address range is often a scan, a mis-pointed client, or a policy bug—metrics here shorten triage for both security and app teams.

## Implementation

Make sure your logging rules prefix messages so the search can see them. Lower `>100` in quiet segments or add time bucketing in a follow-on alert. Extract `src`, `dst_port`, and `protocol` with your props; if missing, add `REX` temporarily in the base search.

## Detailed Implementation

Prerequisites
• On each host, enable **iptables** or **nftables** `LOG` for deny actions you care about, and forward **kern**-priority syslog to the Splunk input already managed by the TA.

Step 1 — Configure data collection
Map vendor-specific strings; UFW labels lines with `[UFW` while raw iptables might only show `IN=... OUT=...`. Use **props** to normalize to `action`, `src`, and `dst_port`.

Step 2 — Create the search and alert
The SPL groups high-volume denials. Start with a **report**; promote to an **alert** only after the volume threshold matches your noise floor.

**Understanding this SPL** — A straight count by tuple; adjust OR clauses if you standardize on `action=deny` instead of raw substrings.


Step 3 — Validate
On host, `iptables -L -n` / `nft list ruleset` to confirm the rule you think is logging; use `tcpdump` or `conntrack` if you also need to prove the packet really reached the policer.

Step 4 — Operationalize
Feed top sources into a threat or CMDB workflow; for benign partners, add CIDRs to an allow list rather than silencing the whole use case.



## SPL

```spl
index=os sourcetype=syslog "ufw" ("DENY" OR "REJECT" OR "DROP")
| stats count by host, src, dst_port, protocol
| where count > 100
```

## Visualization

Table, Bar Chart

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
