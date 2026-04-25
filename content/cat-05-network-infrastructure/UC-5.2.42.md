<!-- AUTO-GENERATED from UC-5.2.42.json — DO NOT EDIT -->

---
id: "5.2.42"
title: "Juniper SRX Screen Counter Monitoring (Juniper SRX)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.2.42 · Juniper SRX Screen Counter Monitoring (Juniper SRX)

## Description

Junos “Screen” features apply stateless, early-drop protections against floods, sweeps, malformed packets, and classic DoS patterns before sessions are fully created. Those drops often never appear in session or traffic logs, so screen telemetry is the only way to see perimeter volumetric or reconnaissance attacks. Sustained spikes in specific screen categories usually mean an active attack, a misconfigured peer, or a need to tune thresholds—not “normal” firewall noise.

## Value

Junos “Screen” features apply stateless, early-drop protections against floods, sweeps, malformed packets, and classic DoS patterns before sessions are fully created. Those drops often never appear in session or traffic logs, so screen telemetry is the only way to see perimeter volumetric or reconnaissance attacks. Sustained spikes in specific screen categories usually mean an active attack, a misconfigured peer, or a need to tune thresholds—not “normal” firewall noise.

## Implementation

Confirm screen options are enabled on untrust-facing interfaces and that `RT_SCREEN` syslog messages (or structured equivalents) reach Splunk. For SNMP, poll platform-specific screen/attack counters if your SRX model exposes them, and chart deltas alongside syslog. Baseline each `screen_type` per site; alert on order-of-magnitude jumps or sustained elevation. Investigate source `src` clusters and coordinate with upstream ISP scrubbing if attacks are large. Map to CIM `Intrusion_Detection` where fields align.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_juniper` (Splunkbase 2847), SNMP Modular Input.
• Ensure the following data sources are available: `sourcetype=juniper:junos:firewall:structured` (syslog `RT_SCREEN_*`), SNMP screen or attack-related counters where published for your platform.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Confirm screen options are enabled on untrust-facing interfaces and that `RT_SCREEN` syslog messages (or structured equivalents) reach Splunk. For SNMP, poll platform-specific screen/attack counters if your SRX model exposes them, and chart deltas alongside syslog. Baseline each `screen_type` per site; alert on order-of-magnitude jumps or sustained elevation. Investigate source `src` clusters and coordinate with upstream ISP scrubbing if attacks are large. Map to CIM `Intrusion_Detection` where …

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network (sourcetype="juniper:junos:firewall:structured" OR sourcetype="juniper:junos:firewall")
  "RT_SCREEN"
| rex field=_raw "RT_SCREEN_(?<screen_type>[A-Z0-9_]+)"
| rex field=_raw "source:\s*(?<src>\S+)"
| rex field=_raw "destination:\s*(?<dest>\S+)"
| bin _time span=5m
| stats count as screen_hits by _time host screen_type src dest
| eventstats median(screen_hits) as med by screen_type, host
| eval threshold=max(100, 5 * med)
| where screen_hits > threshold
| sort -screen_hits
```

Understanding this SPL

**Juniper SRX Screen Counter Monitoring (Juniper SRX)** — Junos “Screen” features apply stateless, early-drop protections against floods, sweeps, malformed packets, and classic DoS patterns before sessions are fully created. Those drops often never appear in session or traffic logs, so screen telemetry is the only way to see perimeter volumetric or reconnaissance attacks. Sustained spikes in specific screen categories usually mean an active attack, a misconfigured peer, or a need to tune thresholds—not “normal” firewall noise.

Documented **Data sources**: `sourcetype=juniper:junos:firewall:structured` (syslog `RT_SCREEN_*`), SNMP screen or attack-related counters where published for your platform. **App/TA** (typical add-on context): `Splunk_TA_juniper` (Splunkbase 2847), SNMP Modular Input. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: juniper:junos:firewall:structured, juniper:junos:firewall. Those sourcetypes align with what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="juniper:junos:firewall:structured". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Extracts fields with `rex` (regular expression).
• Extracts fields with `rex` (regular expression).
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time host screen_type src dest** so each row reflects one combination of those dimensions.
• `eventstats` rolls up events into metrics; results are split **by screen_type, host** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **threshold** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where screen_hits > threshold` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.




Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.signature IDS_Attacks.severity IDS_Attacks.src IDS_Attacks.dest span=1h
| where count>0
| sort -count
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Intrusion_Detection data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Intrusion_Detection model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
Compare a sample of events in J-Web or the SRX command line for the same time and rule context so on-box messages and Splunk stay aligned.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart (hits by screen type), Table (top sources), Single value (total screen drops vs prior day).

## SPL

```spl
index=network (sourcetype="juniper:junos:firewall:structured" OR sourcetype="juniper:junos:firewall")
  "RT_SCREEN"
| rex field=_raw "RT_SCREEN_(?<screen_type>[A-Z0-9_]+)"
| rex field=_raw "source:\s*(?<src>\S+)"
| rex field=_raw "destination:\s*(?<dest>\S+)"
| bin _time span=5m
| stats count as screen_hits by _time host screen_type src dest
| eventstats median(screen_hits) as med by screen_type, host
| eval threshold=max(100, 5 * med)
| where screen_hits > threshold
| sort -screen_hits
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.signature IDS_Attacks.severity IDS_Attacks.src IDS_Attacks.dest span=1h
| where count>0
| sort -count
```

## Visualization

Timechart (hits by screen type), Table (top sources), Single value (total screen drops vs prior day).

## References

- [Splunkbase app 2847](https://splunkbase.splunk.com/app/2847)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
