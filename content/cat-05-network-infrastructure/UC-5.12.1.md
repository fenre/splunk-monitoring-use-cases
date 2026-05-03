<!-- AUTO-GENERATED from UC-5.12.1.json — DO NOT EDIT -->

---
id: "5.12.1"
title: "CDR Call Failure Statistics"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.12.1 · CDR Call Failure Statistics

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We help you see when too many calls are failing so you can fix trunks, dial plans, or carrier issues before customers keep redialing.*

---

## Description

Aggregates release causes, SIP response codes, and ISUP cause values from CDRs to spot trunk, routing, or peer outages early.

## Value

Voice operations teams detect trunk and routing failures within minutes via cause code analysis, enabling rapid traffic rerouting before call completion rates drop below SLA thresholds.

## Implementation

Normalize vendor-specific cause codes to Q.850 / SIP mapping table; baseline by destination prefix (emergency, international).

## Detailed Implementation

### Prerequisites
- CDR data ingestion configured: your SBC (Session Border Controller) — Cisco CUBE, AudioCodes, Ribbon, Oracle/Acme Packet — must export CDRs to Splunk. Common methods: (a) CSV/JSON CDR files via syslog or file monitor (`inputs.conf` with `[monitor:///var/log/sbc/cdr/]`), (b) RADIUS accounting from the SBC to Splunk via Stream, (c) direct CDR export via API or SFTP batch. The sourcetype `cdr:voip` is a generic label — your environment may use `cisco:ucm:cdr` (Cisco UCM), `broadworks:cdr` (Broadworks), `asterisk:cdr` (Asterisk), or a vendor-specific type.
- Create a dedicated `index=voip` for all CDR data. Configure `props.conf` to extract key fields: `call_status` (answered/failed/busy/no_answer), `release_cause` (Q.850 cause code or SIP response code), `calling_party`, `called_number`, `dest` (trunk group or gateway), `duration_sec`, `setup_time`, `disconnect_time`.
- Build a Q.850-to-SIP mapping lookup `q850_sip_causes.csv` with columns: `cause_code`, `sip_code`, `description`, `severity` (normal/warning/critical). Example: cause_code=16 → "Normal call clearing" (normal), cause_code=34 → "No circuit/channel available" (critical), cause_code=41 → "Temporary failure" (warning). This lookup transforms cryptic numeric codes into actionable descriptions.
- License estimate: CDR volume = calls/day × ~0.5–1 KB per CDR. A carrier handling 1M calls/day ≈ 500 MB–1 GB/day of CDR data.
- Baseline knowledge: understand your normal failure rate. A healthy voice network has 1–3% call failure rate (mostly 486 Busy, which is normal). Failure rates above 5% indicate trunk or routing issues.

### Step 1 — Configure data collection
Configure CDR export from each SBC/gateway to Splunk. For Cisco CUBE, enable CDR generation via `gw-accounting file` and configure a file monitor input. For AudioCodes, enable syslog CDR format and point to your Heavy Forwarder or SC4S. For UCM, use the CDR Analysis and Reporting (CAR) database export or the CDR Repository Manager to push CDR files.

Verify data arrival and field extraction:
```spl
index=voip sourcetype="cdr:voip" earliest=-1h
| stats count by call_status, host
```
You should see events from each gateway/SBC with `call_status` values like "answered", "failed", "busy", "no_answer". If `call_status` is null, check `props.conf` field extractions.

Verify cause code extraction:
```spl
index=voip sourcetype="cdr:voip" call_status!="answered" earliest=-1h
| stats count by release_cause
| lookup q850_sip_causes.csv cause_code as release_cause OUTPUT description severity
| sort -count
```

### Step 2 — Create the search and alert

**Primary search — Failure rate with cause code breakdown (15-min alert):**
```spl
index=voip sourcetype="cdr:voip" earliest=-15m
| eval is_fail=if(call_status!="answered" AND call_status!="busy", 1, 0)
| eval is_abnormal=if(match(release_cause, "^(34|38|41|42|47|50[0-9]|503)$"), 1, 0)
| stats count as total sum(is_fail) as fails sum(is_abnormal) as abnormal_fails by dest
| eval fail_pct=round(100*fails/total, 2)
| eval abnormal_pct=round(100*abnormal_fails/total, 2)
| where fail_pct > 5 OR abnormal_fails > 20
| sort -abnormal_pct
```

#### Understanding this SPL: We distinguish between "normal" failures (486 Busy, caller abandon) and "abnormal" failures (cause 34=No Circuit, 38=Network Out of Order, 41=Temporary Failure, 42=Switching Congestion, 503=Service Unavailable). Normal failures are expected in healthy networks; abnormal failures indicate infrastructure problems. Grouping by `dest` (trunk/gateway) isolates the problem to a specific carrier or route.

**Cause code trending — patterns over 24h:**
```spl
index=voip sourcetype="cdr:voip" call_status!="answered" earliest=-24h
| lookup q850_sip_causes.csv cause_code as release_cause OUTPUT description severity
| where severity IN ("warning", "critical")
| timechart span=15m count by description limit=10
```

#### Understanding this SPL: Trends the top 10 abnormal cause codes over 24 hours. A sudden spike in a specific cause (e.g. "No circuit available") points to trunk exhaustion, while a gradual increase in "Temporary failure" suggests growing instability.

**Gateway comparison — which gateway has the worst failure rate:**
```spl
index=voip sourcetype="cdr:voip" earliest=-1h
| eval is_fail=if(call_status!="answered" AND call_status!="busy", 1, 0)
| stats count as total sum(is_fail) as fails by host
| eval fail_pct=round(100*fails/total, 2)
| where total > 50
| sort -fail_pct
```

Schedule as Alert: primary search runs every 15 minutes. Trigger when `abnormal_pct > 5` for any trunk with `total > 100` calls. Throttle by `dest` for 1 hour.

### Step 3 — Validate
(a) Export CDRs from the SBC admin interface for the same 15-minute window and compare total call count, answered count, and failed count. Splunk should match within 5%.

(b) Pick a specific release cause code and verify it matches the SBC's reported reason. For example, Q.850 cause 34 should correspond to "No circuit/channel available" in both Splunk and the SBC.

(c) Validate the trunk/gateway mapping: ensure `dest` correctly identifies the carrier or trunk group. If `dest` shows an IP address, build a lookup `sbc_trunks.csv` mapping dest_ip → carrier_name.

(d) Cross-check with the carrier's trouble ticket system: if the carrier reported a maintenance window, verify that the failure spike aligns with that window.

(e) Test alert routing: temporarily lower the threshold and verify the alert fires correctly.

### Step 4 — Operationalize
Dashboard ("Voice — CDR Failure Analysis"):
- Row 1 — Single-value tiles: "Overall failure rate" (gauge: green <3%, yellow 3–5%, red >5%), "Abnormal failures (15m)", "Total calls (15m)", "Worst gateway failure rate".
- Row 2 — Timechart: failure rate per trunk/gateway over 24h with 15-min granularity. 5% threshold line.
- Row 3 — Cause code distribution: stacked area chart of cause codes over time. Pie chart of current cause mix.
- Row 4 — Gateway comparison table: host, total calls, fail_pct, top cause code.

Alerting:
- Critical (abnormal_pct > 10%): page NOC — trunk infrastructure failure.
- Warning (abnormal_pct > 5%): ticket with 1-hour SLA.

Runbook (owner: Voice Operations):
1. **Cause 34/42 (No Circuit/Congestion)**: Trunk capacity exhausted. Check concurrent call count vs. licensed capacity. Reroute overflow to alternate trunks.
2. **Cause 38/41 (Network Out of Order / Temporary Failure)**: Remote gateway or carrier issue. Contact carrier NOC. Verify SBC connectivity to the carrier.
3. **503 (Service Unavailable)**: Carrier SBC overloaded. Reduce traffic rate; reroute to backup carrier.

### Step 5 — Troubleshooting

- **CDR data arrives with delay** — Batch CDR file delivery (FTP/SFTP) may lag by 5–30 minutes depending on the SBC's CDR rotation interval. For real-time monitoring, prefer syslog-based CDR delivery or RADIUS accounting. Configure the SBC to rotate CDR files every 5 minutes instead of the default 30–60 minutes.

- **`call_status` field is missing** — The TA or props.conf may not extract this field from your CDR format. Check the raw event format and add a REPORT or EXTRACT rule. Common CDR formats: CSV (field position-based), ASN.1 (binary — needs a decoder), XML.

- **Cause codes are numeric but the lookup returns null** — Ensure the lookup key type matches: if the CDR field is a string "034" but the lookup key is integer "34", they won't match. Normalize with `| eval release_cause=tonumber(release_cause)`.

- **Duplicate CDR records** — Some SBCs generate both a "start" and "stop" CDR record. Only the "stop" record contains the release cause and duration. Filter to stop records only, or deduplicate by call-id.

- **Failure rate appears high but SBC shows normal** — Check whether "busy" (486) is counted as a failure. In most voice networks, busy is a normal call outcome, not a failure. Exclude busy from the failure calculation unless it indicates trunk-level blocking.

## SPL

```spl
index=voip sourcetype="cdr:voip"
| eval is_fail=if(call_status!="answered" OR match(lower(call_status),"fail"),1,0)
| timechart span=15m sum(is_fail) as fails count as total
| eval fail_pct=if(total>0, round(100*fails/total,2), 0)
```

## Visualization

Stacked area (causes over time), Pie chart (cause mix), Single value (fail %).

## Known False Positives

Brief drops during gateway failovers, codec renegotiation, or PSTN trunk maintenance can add release reasons that look bad in a chart; compare to the SBC active-alarm view for the same minute.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
