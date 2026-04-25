<!-- AUTO-GENERATED from UC-5.1.26.json — DO NOT EDIT -->

---
id: "5.1.26"
title: "Network Device Firmware Version Compliance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.26 · Network Device Firmware Version Compliance

## Description

Devices running unapproved or EOL firmware versions.

## Value

Devices running unapproved or EOL firmware versions.

## Implementation

Poll SNMP sysDescr or ingest `show version` via scripted input. Create lookup table (ios_version, approved, eol_date) from vendor EOL/EOS bulletins. Alert on non-approved or past-EOL versions. Update lookup quarterly.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog, SNMP TA (sysDescr).
• Ensure the following data sources are available: SNMP sysDescr, show version output.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll SNMP sysDescr or ingest `show version` via scripted input. Create lookup table (ios_version, approved, eol_date) from vendor EOL/EOS bulletins. Alert on non-approved or past-EOL versions. Update lookup quarterly.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype=snmp:sysinfo OR sourcetype=cisco:ios:version
| rex field=_raw "Version (?<ios_version>\S+)" | rex field=sysDescr "Version (?<ios_version>\S+)"
| lookup firmware_compliance ios_version OUTPUT approved eol_date
| where approved!="yes" OR (eol_date!="" AND strptime(eol_date,"%Y-%m-%d")<now())
| table host ios_version approved eol_date
```

Understanding this SPL

**Network Device Firmware Version Compliance** — Devices running unapproved or EOL firmware versions.

Documented **Data sources**: SNMP sysDescr, show version output. **App/TA** (typical add-on context): `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog, SNMP TA (sysDescr). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:sysinfo, cisco:ios:version. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype=snmp:sysinfo. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Extracts fields with `rex` (regular expression).
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where approved!="yes" OR (eol_date!="" AND strptime(eol_date,"%Y-%m-%d")<now())` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Network Device Firmware Version Compliance**): table host ios_version approved eol_date


Step 3 — Validate
SSH to a sample device that appears in the result and run the `show` command that matches the signal in this use case. Confirm the timestamp, interface, or user string matches a row in Splunk, and that your index and sourcetype are the ones the team expects after the last change window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (device, version, status), Bar chart (version distribution), Single value (non-compliant count).

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
index=network sourcetype=snmp:sysinfo OR sourcetype=cisco:ios:version
| rex field=_raw "Version (?<ios_version>\S+)" | rex field=sysDescr "Version (?<ios_version>\S+)"
| lookup firmware_compliance ios_version OUTPUT approved eol_date
| where approved!="yes" OR (eol_date!="" AND strptime(eol_date,"%Y-%m-%d")<now())
| table host ios_version approved eol_date
```

## Visualization

Table (device, version, status), Bar chart (version distribution), Single value (non-compliant count).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
