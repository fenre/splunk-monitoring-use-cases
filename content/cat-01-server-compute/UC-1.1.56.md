---
id: "1.1.56"
title: "Firewall Rule Hit Tracking (iptables/nftables)"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.1.56 · Firewall Rule Hit Tracking (iptables/nftables)

## Description

Firewall rule tracking identifies blocked traffic patterns, helping optimize rules and detect attack attempts.

## Value

Firewall rule tracking identifies blocked traffic patterns, helping optimize rules and detect attack attempts.

## Implementation

Enable firewall logging in iptables/nftables. Configure kernel logging for denied traffic. Create alerts for spike in dropped packets to specific ports, and trending reports on top blocked IPs.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=syslog, kernel ufw/firewall logs`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable firewall logging in iptables/nftables. Configure kernel logging for denied traffic. Create alerts for spike in dropped packets to specific ports, and trending reports on top blocked IPs.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog "ufw" ("DENY" OR "REJECT" OR "DROP")
| stats count by host, src, dst_port, protocol
| where count > 100
```

Understanding this SPL

**Firewall Rule Hit Tracking (iptables/nftables)** — Firewall rule tracking identifies blocked traffic patterns, helping optimize rules and detect attack attempts.

Documented **Data sources**: `sourcetype=syslog, kernel ufw/firewall logs`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: syslog. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, src, dst_port, protocol** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 100` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Bar Chart

## SPL

```spl
index=os sourcetype=syslog "ufw" ("DENY" OR "REJECT" OR "DROP")
| stats count by host, src, dst_port, protocol
| where count > 100
```

## Visualization

Table, Bar Chart

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
