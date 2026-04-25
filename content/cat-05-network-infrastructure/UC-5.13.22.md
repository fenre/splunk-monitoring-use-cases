<!-- AUTO-GENERATED from UC-5.13.22.json — DO NOT EDIT -->

---
id: "5.13.22"
title: "Assurance Issue Trending Over Time"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.22 · Assurance Issue Trending Over Time

## Description

Tracks the volume and priority distribution of assurance issues over time to identify trends, recurring patterns, and the impact of changes.

## Value

Issue trends reveal whether the network is improving or degrading. Spikes correlate with changes, and persistent volumes indicate unresolved systemic problems.

## Implementation

Enable the `issue` input in the Cisco Catalyst TA pointing to `index=catalyst`. The TA polls `/dna/intent/api/v1/issues`. Ensure time parsing is correct so `timechart` reflects ingestion and event time as intended for operations.

## Detailed Implementation

Prerequisites
• The **issue** feed is continuous; retain **30–90+ days** in `catalyst` for seasonal and change-correlated patterns.
• **Time semantics:** confirm whether `_time` reflects issue **updated** time, **created** time, or **ingest** time as set by the TA—mis-set time breaks trend trust. Sample one JSON event and compare timestamps to the Catalyst Center UI before publishing to leadership.
• API user has read access to the full issues set; **5m** or **15m** polls should match the dashboard’s expected freshness.
• Align **time zone** expectations between Splunk users and Catalyst operators (especially across **DST** transitions).
• **Policy for `span=4h`:** about **6** points per day—good for week/month storylines; clone the panel to **`span=1h`** for war-room or near-real-time incident review.

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/issues` (paginated Assurance issues list).
• **TA input name:** **issue**; sourcetype `cisco:dnac:issue`, index `catalyst`.
• **Interval:** **300 seconds** is a common NOC default; **900s** is acceptable when rate-limited—record the actual value from `inputs.conf` in the runbook.
• **Volume:** grows with chronic P3/P4 noise; still far smaller than flow or firewall indices.
• **Dedup caveat:** if each poll re-sends the **entire** open backlog as new events, `count` inflates—validate once; pre-dedup on `issueId` in a summary or intermediate saved search if needed.

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:issue" | timechart span=4h count by priority
```

Understanding this SPL (4h span, what `count` means, dedup)
• **`span=4h`** smooths short spikes that `span=1h` would exaggerate and hides sub-hour blasts—good for execs, less so for minute-level war rooms. Keep a **`span=1h`** clone for NOC during active incidents.
• **`count` without dedup** counts every raw event in the bucket. If the TA re-emits the same open issues on every poll, counts become huge—watch for suspicious P3 thousands; fix the input filter or add `| dedup _time issueId` in a v2.
• **`by priority`** creates separate series for P1–P4; if P1 is always zero, you may have clean health—or API RBAC is hiding P1.
• Overlay **change calendar** and **Cisco TAC** case dates to explain spikes in postmortems.

**Pipeline walkthrough**
• The base search limits to `index=catalyst` and `sourcetype=cisco:dnac:issue`.
• `timechart span=4h` buckets events and counts them, split by the `priority` field.

Step 3 — Validate
• During an incident, temporarily use **`span=1h`** to see finer granularity if issues are created in that window.
• Run `| timechart count` with no `by` clause—if zero, ingest failed; if non-zero but P1 never appears, run a one-off `| where priority="P1"` on raw data to confirm the string exists.
• Compare the overall shape to **Catalyst Center > Issues** history in the same UTC offset; allow poll skew at bucket boundaries.
• After an upgrade, optionally add `| eval` to normalize priority text if Cisco changes string format.

Step 4 — Operationalize
• **Placement:** row 2 of an **Assurance** dashboard; **7-day** default next to a **P1** table. Keep **`span=4h`** on the executive copy and **`span=1h`** on the NOC copy.
• **Colors:** P1 line red, P2 orange, P3/P4 muted so leadership is not trained to ignore “all red.”
• **Not for paging** by itself—use **UC-5.13.23** for P1/P2 paging; this chart is for **trend** and **storytelling**.
• **Postmortem:** export a **30-day** PNG for incident records and QBRs.

Step 5 — Troubleshooting
• **Jagged spikes** after a TA upgrade: new payload or dedup behavior—reread add-on release notes; test `dedup issueId`.
• **Only one priority series:** `priority` extraction may have broken—run `fieldsummary priority` the week of upgrade.
• **Ingest lag** hours behind reality: fix HEC/UF queues and indexer load before tuning SPL.
• **Catalyst maintenance mode** with few new issues does not always mean a clean network—cross-check Syslog, SNMP, and client health UCs.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:issue" | timechart span=4h count by priority
```

## Visualization

Line or area timechart (count by priority over time), overlay annotations for change windows if desired.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
