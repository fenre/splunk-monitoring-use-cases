<!-- AUTO-GENERATED from UC-2.1.39.json — DO NOT EDIT -->

---
id: "2.1.39"
title: "ESXi Host Firewall Rule Audit"
criticality: "medium"
splunkPillar: "Security"
---

# UC-2.1.39 · ESXi Host Firewall Rule Audit

## Description

ESXi has a built-in firewall that controls which services are accessible. Overly permissive rules (e.g., SSH from any IP, open NFC ports) expand the attack surface. CIS benchmarks and DISA STIGs require specific firewall configurations on ESXi hosts.

## Value

ESXi has a built-in firewall that controls which services are accessible. Overly permissive rules (e.g., SSH from any IP, open NFC ports) expand the attack surface. CIS benchmarks and DISA STIGs require specific firewall configurations on ESXi hosts.

## Implementation

Create a PowerCLI scripted input: `Get-VMHost | Get-VMHostFirewallException | Where Enabled | Select VMHost, Name, Enabled, IncomingPorts, OutgoingPorts, Protocols`. Run daily. Alert on rules with AllHosts=true for sensitive services (SSH, NFC, vSAN). Compare against a baseline lookup of approved rules.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`, custom scripted input.
• Ensure the following data sources are available: Custom scripted input (PowerCLI `Get-VMHostFirewallException`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a PowerCLI scripted input: `Get-VMHost | Get-VMHostFirewallException | Where Enabled | Select VMHost, Name, Enabled, IncomingPorts, OutgoingPorts, Protocols`. Run daily. Alert on rules with AllHosts=true for sensitive services (SSH, NFC, vSAN). Compare against a baseline lookup of approved rules.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="esxi_firewall"
| where enabled="true" AND allowedAll="true"
| table host, rule_name, protocol, port, direction, allowedAll
| sort host, rule_name
```

Understanding this SPL

**ESXi Host Firewall Rule Audit** — ESXi has a built-in firewall that controls which services are accessible. Overly permissive rules (e.g., SSH from any IP, open NFC ports) expand the attack surface. CIS benchmarks and DISA STIGs require specific firewall configurations on ESXi hosts.

Documented **Data sources**: Custom scripted input (PowerCLI `Get-VMHostFirewallException`). **App/TA** (typical add-on context): `Splunk_TA_vmware`, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: esxi_firewall. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="esxi_firewall". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where enabled="true" AND allowedAll="true"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **ESXi Host Firewall Rule Audit**): table host, rule_name, protocol, port, direction, allowedAll
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, rule, ports, scope), Bar chart (rules allowing all IPs), Compliance percentage.

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
index=vmware sourcetype="esxi_firewall"
| where enabled="true" AND allowedAll="true"
| table host, rule_name, protocol, port, direction, allowedAll
| sort host, rule_name
```

## Visualization

Table (host, rule, ports, scope), Bar chart (rules allowing all IPs), Compliance percentage.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
