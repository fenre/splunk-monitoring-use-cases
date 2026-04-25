<!-- AUTO-GENERATED from UC-6.1.30.json — DO NOT EDIT -->

---
id: "6.1.30"
title: "MDS FLOGI Database Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-6.1.30 · MDS FLOGI Database Monitoring

## Description

The FLOGI (Fabric Login) database records every device that has logged into the SAN fabric. Monitoring FLOGI events detects rogue devices, unexpected host logins, and fabric login storms that indicate HBA or driver issues.

## Value

The FLOGI (Fabric Login) database records every device that has logged into the SAN fabric. Monitoring FLOGI events detects rogue devices, unexpected host logins, and fabric login storms that indicate HBA or driver issues.

## Implementation

Forward MDS syslog and periodically poll FLOGI database via NX-API. Maintain a lookup of known/authorized WWNs. Alert on unknown WWN logins. Track FLOGI count trends to detect login storms.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `cisco:mds` syslog, scripted input (NX-API).
• Ensure the following data sources are available: MDS syslog (FLOGI/FDISC events), NX-API (`show flogi database`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward MDS syslog and periodically poll FLOGI database via NX-API. Maintain a lookup of known/authorized WWNs. Alert on unknown WWN logins. Track FLOGI count trends to detect login storms.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:mds" "FLOGI" OR "FDISC"
| stats count as login_count by switch, port, pwwn, nwwn
| lookup mds_known_hosts pwwn OUTPUT host_name, authorized
| where isnull(authorized) OR authorized!="yes"
| table switch, port, pwwn, nwwn, host_name, authorized, login_count
```

Understanding this SPL

**MDS FLOGI Database Monitoring** — The FLOGI (Fabric Login) database records every device that has logged into the SAN fabric. Monitoring FLOGI events detects rogue devices, unexpected host logins, and fabric login storms that indicate HBA or driver issues.

Documented **Data sources**: MDS syslog (FLOGI/FDISC events), NX-API (`show flogi database`). **App/TA** (typical add-on context): `cisco:mds` syslog, scripted input (NX-API). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:mds. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:mds". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by switch, port, pwwn, nwwn** so each row reflects one combination of those dimensions.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where isnull(authorized) OR authorized!="yes"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **MDS FLOGI Database Monitoring**): table switch, port, pwwn, nwwn, host_name, authorized, login_count

Step 3 — Validate
Compare port and error counters with the switch CLI (`show interface`, `porterrshow`) or DCNM for the same switch, port, and interval.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Point on-call to the ONTAP or array runbook, Cisco SAN references, and SNMP/REST credentials already used in production—not generic platform steps only. Consider visualizations: Table (FLOGI entries with authorization status), Bar chart (logins per switch), Timeline (login events).

## SPL

```spl
index=network sourcetype="cisco:mds" "FLOGI" OR "FDISC"
| stats count as login_count by switch, port, pwwn, nwwn
| lookup mds_known_hosts pwwn OUTPUT host_name, authorized
| where isnull(authorized) OR authorized!="yes"
| table switch, port, pwwn, nwwn, host_name, authorized, login_count
```

## Visualization

Table (FLOGI entries with authorization status), Bar chart (logins per switch), Timeline (login events).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
