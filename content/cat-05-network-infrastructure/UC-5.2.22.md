<!-- AUTO-GENERATED from UC-5.2.22.json — DO NOT EDIT -->

---
id: "5.2.22"
title: "Malware Detection and AMP File Reputation Events (Meraki MX)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.22 · Malware Detection and AMP File Reputation Events (Meraki MX)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We follow malware and reputation flags from the same edge so the team can quarantine a bad file before it moves deeper inside.*

---

## Description

Detects and tracks file-based threats to respond quickly to potential malware infections.

## Value

Security teams monitor Meraki MX AMP file reputation events, prioritizing retrospective malware alerts where previously allowed files are reclassified as malicious.

## Implementation

1. On the MX, Dashboard > Security & SD-WAN > Threat protection > Advanced Malware Protection: enabled. 2. Dashboard > Network-wide > General > Reporting > Syslog: ensure 'Security events' role is checked for the SC4S/Splunk receiver. 3. Confirm SC4S Meraki vendor pack writes to `index=meraki sourcetype=meraki`. 4. Use the SPL above which scans `_raw` for AMP markers and coalesces field-name variants — Meraki AMP events are not discrete `type=` records.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA)..
- Ensure the following data sources are available: Meraki MX AMP file-reputation events surfaced through Splunk_TA_cisco_meraki (Splunkbase 5580) or SC4S Meraki vendor pack. Default sourcetype `meraki`; AMP events do NOT carry a discrete `type=` value — they are plain text in `_raw` mentioning `malware`, `amp`, or `file reputation`. Field names vary between firmware (`disposition` vs `file_disposition`, `file_hash` vs `sha256`, `src` vs `src_ip`) so coalesce in SPL..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. On the MX, Dashboard > Security & SD-WAN > Threat protection > Advanced Malware Protection: enabled. 2. Dashboard > Network-wide > General > Reporting > Syslog: ensure 'Security events' role is checked for the SC4S/Splunk receiver. 3. Confirm SC4S Meraki vendor pack writes to `index=meraki sourcetype=meraki`. 4. Use the SPL above which scans `_raw` for AMP markers and coalesces field-name variants — Meraki AMP events are not discrete `type=` records.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" earliest=-24h
| where match(_raw, "(?i)malware|amp|file.*reputation|file.*block|malicious")
| eval disposition = lower(coalesce(disposition, file_disposition))
| eval file = coalesce(file_name, filename)
| eval hash = coalesce(file_hash, sha256)
| eval src = coalesce(src, src_ip)
| eval dst = coalesce(dest, dest_ip)
| eval event_type = case(
    match(_raw, "(?i)retrospective|reclassif"),                                  "RETROSPECTIVE",
    disposition="malicious" AND match(action, "(?i)block"),                       "BLOCKED_MALWARE",
    disposition="malicious" AND NOT match(action, "(?i)block"),                   "DETECTED_NOT_BLOCKED",
    1==1,                                                                          "AMP_EVENT")
| stats count as events dc(hash) as unique_hashes values(file) as filenames by event_type, src
| sort -events
```

#### Understanding this SPL

**Malware Detection and AMP File Reputation Events (Meraki MX)** — Security teams monitor Meraki MX AMP file reputation events, prioritizing retrospective malware alerts where previously allowed files are reclassified as malicious.

Documented **Data sources**: Meraki MX AMP file-reputation events surfaced through Splunk_TA_cisco_meraki (Splunkbase 5580) or SC4S Meraki vendor pack. Default sourcetype `meraki`; AMP events do NOT carry a discrete `type=` value — they are plain text in `_raw` mentioning `malware`, `amp`, or `file reputation`. Field names vary between firmware (`disposition` vs `file_disposition`, `file_hash` vs `sha256`, `src` vs `src_ip`) so coalesce in SPL. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Filters the current rows with `where match(_raw, "(?i)malware|amp|file.*reputation|file.*block|malicious")` — typically the threshold or rule expression for this monitoring goal.
- `eval` defines or adjusts **disposition** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **file** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **hash** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **src** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **dst** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **event_type** — often to normalize units, derive a ratio, or prepare for thresholds.
- `stats` rolls up events into metrics; results are split **by event_type, src** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection.IDS_Attacks
  by IDS_Attacks.signature IDS_Attacks.severity IDS_Attacks.src IDS_Attacks.dest span=1h
| where count>0
| sort -count
```

Understanding this CIM / accelerated SPL

**Malware Detection and AMP File Reputation Events (Meraki MX)** — Security teams monitor Meraki MX AMP file reputation events, prioritizing retrospective malware alerts where previously allowed files are reclassified as malicious.

Documented **Data sources**: Meraki MX AMP file-reputation events surfaced through Splunk_TA_cisco_meraki (Splunkbase 5580) or SC4S Meraki vendor pack. Default sourcetype `meraki`; AMP events do NOT carry a discrete `type=` value — they are plain text in `_raw` mentioning `malware`, `amp`, or `file reputation`. Field names vary between firmware (`disposition` vs `file_disposition`, `file_hash` vs `sha256`, `src` vs `src_ip`) so coalesce in SPL. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

- Uses `tstats` against accelerated summaries for data model `Intrusion_Detection.IDS_Attacks` — enable acceleration for that model.
- Filters the current rows with `where count>0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Threat timeline; infected hosts table; file reputation detail; incident dashboard.

## SPL

```spl
index=meraki sourcetype="meraki" earliest=-24h
| where match(_raw, "(?i)malware|amp|file.*reputation|file.*block|malicious")
| eval disposition = lower(coalesce(disposition, file_disposition))
| eval file = coalesce(file_name, filename)
| eval hash = coalesce(file_hash, sha256)
| eval src = coalesce(src, src_ip)
| eval dst = coalesce(dest, dest_ip)
| eval event_type = case(
    match(_raw, "(?i)retrospective|reclassif"),                                  "RETROSPECTIVE",
    disposition="malicious" AND match(action, "(?i)block"),                       "BLOCKED_MALWARE",
    disposition="malicious" AND NOT match(action, "(?i)block"),                   "DETECTED_NOT_BLOCKED",
    1==1,                                                                          "AMP_EVENT")
| stats count as events dc(hash) as unique_hashes values(file) as filenames by event_type, src
| sort -events
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

Threat timeline; infected hosts table; file reputation detail; incident dashboard.

## Known False Positives

Quarantine, cleanup tools, and rescanning the same file can repeat malware events without a new infection.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Intrusion_Detection](https://docs.splunk.com/Documentation/CIM/latest/User/Intrusion_Detection)
