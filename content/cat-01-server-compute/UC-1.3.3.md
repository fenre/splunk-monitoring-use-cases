<!-- AUTO-GENERATED from UC-1.3.3.json — DO NOT EDIT -->

---
id: "1.3.3"
title: "Gatekeeper and SIP Status"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.3.3 · Gatekeeper and SIP Status

## Description

Disabled Gatekeeper or System Integrity Protection weakens macOS security posture. May indicate developer override or tampering.

## Value

Catching when these protections are turned off helps you separate intentional developer or lab setups from a machine that may have been tampered with and needs a closer look.

## Implementation

Scripted inputs for `spctl --status` and `csrutil status`. Run daily. Dashboard showing fleet-wide compliance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Universal Forwarder, custom scripted input.
• Ensure the following data sources are available: Custom scripted inputs (`spctl --status`, `csrutil status`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Scripted inputs for `spctl --status` and `csrutil status` on a daily schedule. Normalize output into `gatekeeper` and `sip` fields (the example search expects a value of `enabled` for healthy).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=macos_security host=*
| stats latest(gatekeeper) as gk, latest(sip) as sip by host
| where gk!="enabled" OR sip!="enabled"
```

Understanding this SPL

**Gatekeeper and SIP Status** — Disabled Gatekeeper or System Integrity Protection weakens macOS security posture. May indicate developer override or tampering.

**Pipeline walkthrough**

• Scopes the data: `index=os`, `sourcetype=macos_security`.
• `stats` keeps the latest `gk` and `sip` per **host**.
• `where` flags any host where either value is not `enabled` per your normalizer.


Step 3 — Validate
On a test Mac, run the two commands and compare the parsed fields in Search. `csrutil` only reports meaningful SIP state from a normal boot, not from Recovery; document that in your runbook if you use this field.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions as required. Document visualizations: Pie chart (compliant vs. not), Table of non-compliant endpoints. See the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=os sourcetype=macos_security host=*
| stats latest(gatekeeper) as gk, latest(sip) as sip by host
| where gk!="enabled" OR sip!="enabled"
```

## CIM SPL

```spl
N/A — System Integrity Protection and Gatekeeper state are not standard CIM fields; use a custom macOS security posture sourcetype.
```

## Visualization

Pie chart (compliant vs. not), Table of non-compliant endpoints.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
