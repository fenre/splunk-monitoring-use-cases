<!-- AUTO-GENERATED from UC-1.4.3.json — DO NOT EDIT -->

---
id: "1.4.3"
title: "Power Supply Failure"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-1.4.3 · Power Supply Failure

## Description

Lost power supply redundancy means a single PSU failure away from an unplanned outage. Replacement needs to happen before the remaining PSU fails.

## Value

When one of two power feeds drops out or a supply fails, the server may still be running on the remaining path — but you are one fault away from a hard stop until someone replaces the part.

## Implementation

Forward IPMI System Event Log data. Enable syslog forwarding from iLO/iDRAC to Splunk. Alert immediately on PSU failure events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input (`ipmitool`), SNMP, vendor management syslog (iLO/iDRAC).
• Ensure the following data sources are available: IPMI SEL (System Event Log) via scripted input, syslog from BMC.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect the SEL with `ipmitool sel elist` (or vendor equivalents) and forward `sourcetype=ipmi:sel` with `event_description` (or `message`) parsed. Alternatively forward BMC syslog. Alert on substrings you prove match PSU failure in your environment.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust as needed):

```spl
index=hardware sourcetype=ipmi:sel ("Power Supply" OR "PS" OR "power_supply") ("Failure" OR "Absent" OR "fault" OR "lost")
| table _time host sensor event_description
| sort -_time
```

Understanding this SPL

**Power Supply Failure** — Lost power supply redundancy means a single PSU failure away from an unplanned outage. Replacement needs to happen before the remaining PSU fails.

**Pipeline walkthrough**

• Scopes the data: `index=hardware`, `sourcetype=ipmi:sel`.
• The keyword search narrows to likely PSU events (tune to your vendor’s strings).
• `table` and `sort` list recent events for triage.


Step 3 — Validate
Induce a test SEL on a lab BMC if possible, or compare past vendor tickets to the exact text in your index. For full details, see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=hardware sourcetype=ipmi:sel ("Power Supply" OR "PS" OR "power_supply") ("Failure" OR "Absent" OR "fault" OR "lost")
| table _time host sensor event_description
| sort -_time
```

## CIM SPL

```spl
N/A — power-supply events in the IPMI or BMC SEL are not a CIM data model; use the sourcetype search or a vendor-parsed key/value feed.
```

## Visualization

Events timeline, Status indicator per host, Alert panel.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
