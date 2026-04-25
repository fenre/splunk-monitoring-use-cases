<!-- AUTO-GENERATED from UC-2.5.4.json — DO NOT EDIT -->

---
id: "2.5.4"
title: "IGEL Device Heartbeat Loss Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.5.4 · IGEL Device Heartbeat Loss Detection

## Description

IGEL OS 12 devices send periodic heartbeat signals to the UMS server to report operational status. When heartbeats stop, the device may be powered off, network-disconnected, or experiencing a crash loop. Detecting heartbeat loss within a configurable window enables proactive remediation before users report issues at shift start.

## Value

IGEL OS 12 devices send periodic heartbeat signals to the UMS server to report operational status. When heartbeats stop, the device may be powered off, network-disconnected, or experiencing a crash loop. Detecting heartbeat loss within a configurable window enables proactive remediation before users report issues at shift start.

## Implementation

Poll the UMS API with `facets=details` to retrieve `lastContact` timestamps per device. Convert to epoch and compare against current time. Devices that have not contacted UMS within the configured threshold (default 4 hours, adjust for shift patterns) are flagged. Exclude devices in the UMS recycle bin (`movedToBin=true`). Correlate with site/directory to identify location-specific network outages. Trigger escalation if more than 5 devices at the same site lose heartbeat simultaneously.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom scripted input polling IGEL UMS REST API (`GET /v3/thinclients?facets=details`).
• Ensure the following data sources are available: `index=endpoint` `sourcetype="igel:ums:inventory"` fields `device_name`, `last_contact`, `directory_path`, `last_ip`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll the UMS API with `facets=details` to retrieve `lastContact` timestamps per device. Convert to epoch and compare against current time. Devices that have not contacted UMS within the configured threshold (default 4 hours, adjust for shift patterns) are flagged. Exclude devices in the UMS recycle bin (`movedToBin=true`). Correlate with site/directory to identify location-specific network outages. Trigger escalation if more than 5 devices at the same site lose heartbeat simultaneously.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=endpoint sourcetype="igel:ums:inventory"
| stats latest(last_contact) as last_contact, latest(last_ip) as last_ip, latest(directory_path) as site by device_name
| eval contact_epoch=strptime(last_contact, "%Y-%m-%dT%H:%M:%S")
| eval hours_since_contact=round((now()-contact_epoch)/3600, 1)
| where hours_since_contact > 4
| sort -hours_since_contact
| table device_name, site, last_ip, last_contact, hours_since_contact
```

Understanding this SPL

**IGEL Device Heartbeat Loss Detection** — IGEL OS 12 devices send periodic heartbeat signals to the UMS server to report operational status. When heartbeats stop, the device may be powered off, network-disconnected, or experiencing a crash loop. Detecting heartbeat loss within a configurable window enables proactive remediation before users report issues at shift start.

Documented **Data sources**: `index=endpoint` `sourcetype="igel:ums:inventory"` fields `device_name`, `last_contact`, `directory_path`, `last_ip`. **App/TA** (typical add-on context): Custom scripted input polling IGEL UMS REST API (`GET /v3/thinclients?facets=details`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: endpoint; **sourcetype**: igel:ums:inventory. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=endpoint, sourcetype="igel:ums:inventory". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by device_name** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **contact_epoch** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **hours_since_contact** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where hours_since_contact > 4` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **IGEL Device Heartbeat Loss Detection**): table device_name, site, last_ip, last_contact, hours_since_contact

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (stale devices sorted by hours since contact), Bar chart (devices per site with lost heartbeat), Single value (total devices with lost heartbeat).

## SPL

```spl
index=endpoint sourcetype="igel:ums:inventory"
| stats latest(last_contact) as last_contact, latest(last_ip) as last_ip, latest(directory_path) as site by device_name
| eval contact_epoch=strptime(last_contact, "%Y-%m-%dT%H:%M:%S")
| eval hours_since_contact=round((now()-contact_epoch)/3600, 1)
| where hours_since_contact > 4
| sort -hours_since_contact
| table device_name, site, last_ip, last_contact, hours_since_contact
```

## Visualization

Table (stale devices sorted by hours since contact), Bar chart (devices per site with lost heartbeat), Single value (total devices with lost heartbeat).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
