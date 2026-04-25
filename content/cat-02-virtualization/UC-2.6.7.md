<!-- AUTO-GENERATED from UC-2.6.7.json — DO NOT EDIT -->

---
id: "2.6.7"
title: "ICA/HDX Virtual Channel Bandwidth Consumption"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.6.7 · ICA/HDX Virtual Channel Bandwidth Consumption

## Description

HDX sessions use multiple virtual channels — graphics, audio, video, printer redirection, drive mapping, clipboard, and USB. Excessive bandwidth consumption on specific channels (e.g., large print jobs, multimedia redirection, USB device streaming) degrades the session experience for all users on the same VDA or network segment. Identifying bandwidth-heavy channels enables targeted policy optimization.

## Value

HDX sessions use multiple virtual channels — graphics, audio, video, printer redirection, drive mapping, clipboard, and USB. Excessive bandwidth consumption on specific channels (e.g., large print jobs, multimedia redirection, USB device streaming) degrades the session experience for all users on the same VDA or network segment. Identifying bandwidth-heavy channels enables targeted policy optimization.

## Implementation

Collect HDX virtual channel performance counters from VDAs. The Citrix ICA Session performance object exposes per-channel bandwidth metrics (Graphics, Audio, Printing, Drive Mapping, Clipboard, etc.). Alert on abnormal channel bandwidth: graphics channel above 5 Mbps sustained (possible unoptimized video), printing channel spikes (large print jobs), or drive mapping spikes (file copy operations). Use to tune HDX policies: enable adaptive transport, configure video codec, set print quality limits.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Template for Citrix XenDesktop 7 (`TA-XD7-VDA`).
• Ensure the following data sources are available: `index=xd_perfmon` `sourcetype="citrix:vda:perfmon"` fields `counter_name`, `counter_value`, `instance_name`, `vda_host`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect HDX virtual channel performance counters from VDAs. The Citrix ICA Session performance object exposes per-channel bandwidth metrics (Graphics, Audio, Printing, Drive Mapping, Clipboard, etc.). Alert on abnormal channel bandwidth: graphics channel above 5 Mbps sustained (possible unoptimized video), printing channel spikes (large print jobs), or drive mapping spikes (file copy operations). Use to tune HDX policies: enable adaptive transport, configure video codec, set print quality limits…

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=xd_perfmon sourcetype="citrix:vda:perfmon"
  (counter_name="Output Bandwidth*" OR counter_name="Input Bandwidth*")
| bin _time span=15m
| stats avg(counter_value) as avg_bw_bps by instance_name, counter_name, vda_host, _time
| eval avg_bw_kbps=round(avg_bw_bps/1024, 1)
| where avg_bw_kbps > 500
| sort -avg_bw_kbps
| table _time, vda_host, instance_name, counter_name, avg_bw_kbps
```

Understanding this SPL

**ICA/HDX Virtual Channel Bandwidth Consumption** — HDX sessions use multiple virtual channels — graphics, audio, video, printer redirection, drive mapping, clipboard, and USB. Excessive bandwidth consumption on specific channels (e.g., large print jobs, multimedia redirection, USB device streaming) degrades the session experience for all users on the same VDA or network segment. Identifying bandwidth-heavy channels enables targeted policy optimization.

Documented **Data sources**: `index=xd_perfmon` `sourcetype="citrix:vda:perfmon"` fields `counter_name`, `counter_value`, `instance_name`, `vda_host`. **App/TA** (typical add-on context): Template for Citrix XenDesktop 7 (`TA-XD7-VDA`). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: xd_perfmon; **sourcetype**: citrix:vda:perfmon. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=xd_perfmon, sourcetype="citrix:vda:perfmon". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by instance_name, counter_name, vda_host, _time** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **avg_bw_kbps** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where avg_bw_kbps > 500` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **ICA/HDX Virtual Channel Bandwidth Consumption**): table _time, vda_host, instance_name, counter_name, avg_bw_kbps

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Stacked area chart (bandwidth by channel), Table (top bandwidth consumers), Bar chart (channel comparison by VDA).

## SPL

```spl
index=xd_perfmon sourcetype="citrix:vda:perfmon"
  (counter_name="Output Bandwidth*" OR counter_name="Input Bandwidth*")
| bin _time span=15m
| stats avg(counter_value) as avg_bw_bps by instance_name, counter_name, vda_host, _time
| eval avg_bw_kbps=round(avg_bw_bps/1024, 1)
| where avg_bw_kbps > 500
| sort -avg_bw_kbps
| table _time, vda_host, instance_name, counter_name, avg_bw_kbps
```

## Visualization

Stacked area chart (bandwidth by channel), Table (top bandwidth consumers), Bar chart (channel comparison by VDA).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
