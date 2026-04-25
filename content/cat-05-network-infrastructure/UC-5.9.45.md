<!-- AUTO-GENERATED from UC-5.9.45.json — DO NOT EDIT -->

---
id: "5.9.45"
title: "FTP Server Availability and Throughput (ThousandEyes)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.45 · FTP Server Availability and Throughput (ThousandEyes)

## Description

Monitors FTP/SFTP server availability and file transfer throughput from ThousandEyes agents, ensuring file transfer services are accessible and performing adequately for automated data exchange workflows.

## Value

Monitors FTP/SFTP server availability and file transfer throughput from ThousandEyes agents, ensuring file transfer services are accessible and performing adequately for automated data exchange workflows.

## Implementation

Create FTP Server tests in ThousandEyes for critical file transfer endpoints. The OTel metric `ftp.server.request.availability` reports availability, `ftp.client.request.duration` reports TTFB, and `ftp.server.throughput` reports bytes per second. The `ftp.request.command` attribute indicates the FTP command tested (GET, PUT, LS). The Splunk App Voice dashboard includes FTP panels.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco ThousandEyes App for Splunk` (Splunkbase 7719).
• Ensure the following data sources are available: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (FTP Server tests).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create FTP Server tests in ThousandEyes for critical file transfer endpoints. The OTel metric `ftp.server.request.availability` reports availability, `ftp.client.request.duration` reports TTFB, and `ftp.server.throughput` reports bytes per second. The `ftp.request.command` attribute indicates the FTP command tested (GET, PUT, LS). The Splunk App Voice dashboard includes FTP panels.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
`stream_index` thousandeyes.test.type="ftp-server"
| stats avg(ftp.server.request.availability) as avg_availability avg(ftp.client.request.duration) as avg_response_s avg(ftp.server.throughput) as avg_throughput by thousandeyes.test.name, server.address
| eval avg_response_ms=round(avg_response_s*1000,1), throughput_mbps=round(avg_throughput/1048576,2)
| sort avg_availability, -throughput_mbps
```

Understanding this SPL

**FTP Server Availability and Throughput (ThousandEyes)** — Monitors FTP/SFTP server availability and file transfer throughput from ThousandEyes agents, ensuring file transfer services are accessible and performing adequately for automated data exchange workflows.

Documented **Data sources**: `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (FTP Server tests). **App/TA** (typical add-on context): `Cisco ThousandEyes App for Splunk` (Splunkbase 7719). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Invokes macro `stream_index` — in Search, use the UI or expand to inspect the underlying SPL.
• `stats` rolls up events into metrics; results are split **by thousandeyes.test.name, server.address** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **avg_response_ms** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare the same tests and time window in the Cisco ThousandEyes App for Splunk dashboard or the test view at app.thousandeyes.com so Splunk’s metrics and states match the vendor. If they disagree, check streaming or HEC inputs, macros, and API or token health before retuning.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (availability and throughput over time), Table (server, availability, throughput, response time), Single value.

## SPL

```spl
`stream_index` thousandeyes.test.type="ftp-server"
| stats avg(ftp.server.request.availability) as avg_availability avg(ftp.client.request.duration) as avg_response_s avg(ftp.server.throughput) as avg_throughput by thousandeyes.test.name, server.address
| eval avg_response_ms=round(avg_response_s*1000,1), throughput_mbps=round(avg_throughput/1048576,2)
| sort avg_availability, -throughput_mbps
```

## Visualization

Line chart (availability and throughput over time), Table (server, availability, throughput, response time), Single value.

## References

- [Splunkbase app 7719](https://splunkbase.splunk.com/app/7719)
