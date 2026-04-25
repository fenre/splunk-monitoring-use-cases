<!-- AUTO-GENERATED from UC-5.13.36.json — DO NOT EDIT -->

---
id: "5.13.36"
title: "Advisory Trending and New Advisory Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.13.36 · Advisory Trending and New Advisory Detection

## Description

Identifies newly detected security advisories in the last 7 days, enabling rapid assessment of new vulnerabilities affecting the managed network.

## Value

New advisories require immediate triage. Detecting them as soon as Catalyst Center reports them ensures the vulnerability management process starts promptly.

## Implementation

Enable the `securityadvisory` input. The `where first_seen` window compares the earliest event per advisory to `now()`. Adjust the `-7d` lookback to match your patch SLAs.

## Detailed Implementation

Prerequisites
• Cisco Catalyst Add-on (7538); **securityadvisory** → `cisco:dnac:securityadvisory` in `index=catalyst`.
• **Retention** must cover the lookback you care about: if the index is **7d** max, *every* run looks “all-new.” Size **catalyst** for long PSIRT lookbacks (often year+ for audit).
• `first_seen` here is data-arrival in Splunk—rename the panel to **“new to our Splunk in 7d”** if you present to **exec** to avoid over-claiming.
• `docs/implementation-guide.md`.

Step 1 — Configure data collection
• Default **TA** poll ~**3600s**; the `-7d` window is a **query** window, not the poll **interval**.

Step 2 — New-advisory **report** (triage list)
```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" | stats earliest(_time) as first_seen latest(_time) as last_seen dc(deviceId) as affected_devices by advisoryId, advisoryTitle, severity | eval first_seen_date=strftime(first_seen, "%Y-%m-%d") | where first_seen > relative_time(now(), "-7d") | sort severity -affected_devices
```

Understanding this SPL
**New to Splunk** — Pair with a **Cisco** published date field if the TA ever extracts it, or with **Cisco.com** for true **“zero-day to us”**.

**Pipeline walkthrough**
• `earliest`/`latest` on `_time` for each `advisoryId` → `where first_seen>…-7d` → sort by **severity** and **affected** count.

Step 3 — Validate
• When a *real* new bulletin ships, confirm **`first_seen_date`** in Splunk is within **1–2** **polls** of the first **Catalyst** UI appearance.
• Re-run after **`| delete`** test in non-prod to see how **re-ingest** shifts `first_seen` (education for analysts).

Step 4 — Operationalize
• **Vuln bridge:** feed this to **JIRA** **PSIRT** queue with `advisoryId` as **epic** key; **throttle** duplicate tickets by **`advisoryId`**.
• **KPI** slide: new advisories / week, not just **count** of raw events (dedup in a **summary** index if the TA re-emits each hour).

Step 5 — Troubleshooting
• **Over-count new:** **backfill** or **S2S** migration copied old events to a new index with fresh `_time`—compare to **Cisco** **published** date on the **web** side.
• **Under-count new:** `where` is too strict; widen to **-14d** or remove **if** you only want **Catalyst-announced** net-new **in product** (requires **Cisco** field).
• **No rows:** no advisories in range or **sourcetype** quiet—`| tstats count` and **Catalyst** **API** health.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:securityadvisory" | stats earliest(_time) as first_seen latest(_time) as last_seen dc(deviceId) as affected_devices by advisoryId, advisoryTitle, severity | eval first_seen_date=strftime(first_seen, "%Y-%m-%d") | where first_seen > relative_time(now(), "-7d") | sort severity -affected_devices
```

## Visualization

Table of new advisories (first_seen_date, affected_devices), timechart of first_seen counts.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
