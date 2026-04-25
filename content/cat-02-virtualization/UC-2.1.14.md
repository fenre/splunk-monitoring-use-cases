<!-- AUTO-GENERATED from UC-2.1.14.json — DO NOT EDIT -->

---
id: "2.1.14"
title: "ESXi Patch Compliance"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.1.14 · ESXi Patch Compliance

## Description

Unpatched ESXi hosts have known vulnerabilities. Fleet-wide version tracking ensures consistent patching and audit compliance.

## Value

Unpatched ESXi hosts have known vulnerabilities. Fleet-wide version tracking ensures consistent patching and audit compliance.

## Implementation

Splunk_TA_vmware collects host inventory including ESXi version and build number. Maintain a lookup of current expected builds. Dashboard showing compliance percentage and hosts needing updates.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:inv:hostsystem`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Splunk_TA_vmware collects host inventory including ESXi version and build number. Maintain a lookup of current expected builds. Dashboard showing compliance percentage and hosts needing updates.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:inv:hostsystem"
| stats latest(version) as esxi_version, latest(build) as build by host
| eval is_current = if(build="24585291", "Yes", "No")
| sort esxi_version
| table host esxi_version build is_current
```

Understanding this SPL

**ESXi Patch Compliance** — Unpatched ESXi hosts have known vulnerabilities. Fleet-wide version tracking ensures consistent patching and audit compliance.

Documented **Data sources**: `sourcetype=vmware:inv:hostsystem`. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:inv:hostsystem. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:inv:hostsystem". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **is_current** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **ESXi Patch Compliance**): table host esxi_version build is_current

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, version, build, compliant), Pie chart (compliant %), Bar chart by version.

## SPL

```spl
index=vmware sourcetype="vmware:inv:hostsystem"
| stats latest(version) as esxi_version, latest(build) as build by host
| eval is_current = if(build="24585291", "Yes", "No")
| sort esxi_version
| table host esxi_version build is_current
```

## Visualization

Table (host, version, build, compliant), Pie chart (compliant %), Bar chart by version.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
