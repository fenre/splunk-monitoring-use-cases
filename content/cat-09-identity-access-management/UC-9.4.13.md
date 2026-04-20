---
id: "9.4.13"
title: "Active Directory Domain Controller Response Time"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.4.13 · Active Directory Domain Controller Response Time

## Description

LDAP bind time, DNS query time per DC — slow DCs cause auth delays and user lockouts.

## Value

LDAP bind time, DNS query time per DC — slow DCs cause auth delays and user lockouts.

## Implementation

Run scripted input from monitoring host: perform LDAP bind (e.g., ldapsearch -x -H ldap://dc:389 -b "" -s base) and measure elapsed time; run nslookup or Resolve-DnsName for _ldap._tcp.dc._msdcs.domain. Ingest Windows perf counters (NTDS, LDAP Client Sessions) via Splunk_TA_windows. Alert on LDAP bind >1s or DNS >200ms. Identify overloaded DCs for load balancing.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, custom scripted input.
• Ensure the following data sources are available: LDAP bind latency probes, DNS query timing, Windows DC perf counters.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Run scripted input from monitoring host: perform LDAP bind (e.g., ldapsearch -x -H ldap://dc:389 -b "" -s base) and measure elapsed time; run nslookup or Resolve-DnsName for _ldap._tcp.dc._msdcs.domain. Ingest Windows perf counters (NTDS, LDAP Client Sessions) via Splunk_TA_windows. Alert on LDAP bind >1s or DNS >200ms. Identify overloaded DCs for load balancing.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=ad_perf sourcetype="ad:dc_probe"
| bin _time span=5m
| stats avg(ldap_bind_ms) as avg_ldap, avg(dns_query_ms) as avg_dns, count(eval(ldap_bind_ms>1000)) as slow_ldap by dc_host, _time
| where avg_ldap > 500 OR avg_dns > 200 OR slow_ldap > 0
| table _time, dc_host, avg_ldap, avg_dns, slow_ldap
```

Understanding this SPL

**Active Directory Domain Controller Response Time** — LDAP bind time, DNS query time per DC — slow DCs cause auth delays and user lockouts.

Documented **Data sources**: LDAP bind latency probes, DNS query timing, Windows DC perf counters. **App/TA** (typical add-on context): `Splunk_TA_windows`, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: ad_perf; **sourcetype**: ad:dc_probe. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=ad_perf, sourcetype="ad:dc_probe". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by dc_host, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_ldap > 500 OR avg_dns > 200 OR slow_ldap > 0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Active Directory Domain Controller Response Time**): table _time, dc_host, avg_ldap, avg_dns, slow_ldap


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (LDAP/DNS latency by DC), Table (slow DCs), Status grid (DC × response time tier), Single value (worst DC latency).

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=ad_perf sourcetype="ad:dc_probe"
| bin _time span=5m
| stats avg(ldap_bind_ms) as avg_ldap, avg(dns_query_ms) as avg_dns, count(eval(ldap_bind_ms>1000)) as slow_ldap by dc_host, _time
| where avg_ldap > 500 OR avg_dns > 200 OR slow_ldap > 0
| table _time, dc_host, avg_ldap, avg_dns, slow_ldap
```

## Visualization

Line chart (LDAP/DNS latency by DC), Table (slow DCs), Status grid (DC × response time tier), Single value (worst DC latency).

## Known False Positives

Planned maintenance, backups, or batch jobs can drive metrics outside normal bands — correlate with change management windows.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
