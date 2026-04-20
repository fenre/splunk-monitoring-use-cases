---
id: "1.1.16"
title: "Package Vulnerability Tracking"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.1.16 · Package Vulnerability Tracking

## Description

Maintains visibility into known vulnerable packages across the fleet, supporting vulnerability management and compliance programs.

## Value

Maintains visibility into known vulnerable packages across the fleet, supporting vulnerability management and compliance programs.

## Implementation

Enable `package` scripted input in Splunk_TA_nix (daily interval). Cross-reference with a CVE lookup table updated from vulnerability scan exports. Alternatively, ingest Qualys/Tenable scan results directly.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`, custom scripted input.
• Ensure the following data sources are available: `sourcetype=package` (Splunk_TA_nix), vulnerability scanner output.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable `package` scripted input in Splunk_TA_nix (daily interval). Cross-reference with a CVE lookup table updated from vulnerability scan exports. Alternatively, ingest Qualys/Tenable scan results directly.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=package host=*
| stats values(VERSION) as version by host, NAME
| join max=1 NAME [| inputlookup known_cves.csv]
| table host NAME version cve_id severity
| sort -severity
```

Understanding this SPL

**Package Vulnerability Tracking** — Maintains visibility into known vulnerable packages across the fleet, supporting vulnerability management and compliance programs.

Documented **Data sources**: `sourcetype=package` (Splunk_TA_nix), vulnerability scanner output. **App/TA** (typical add-on context): `Splunk_TA_nix`, custom scripted input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: package. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=package. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, NAME** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
• Pipeline stage (see **Package Vulnerability Tracking**): table host NAME version cve_id severity
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, package, CVE, severity), Stats panel of critical/high vuln counts, Bar chart by severity.

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
index=os sourcetype=package host=*
| stats values(VERSION) as version by host, NAME
| join max=1 NAME [| inputlookup known_cves.csv]
| table host NAME version cve_id severity
| sort -severity
```

## Visualization

Table (host, package, CVE, severity), Stats panel of critical/high vuln counts, Bar chart by severity.

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
