# Splunk UC Recommender — TA

App ID: `splunk-uc-recommender-ta`  
App version: **6.1.0**  
Generated: `2026-04-18T08:01:30Z`

Enterprise-only companion TA for the primary
[`splunk-uc-recommender`](../splunk-uc-recommender/README.md) app.

Ships a single modular input — `uc_recommender_deep_scan` — that
runs once per day and samples one event per
`(index, sourcetype)` pair. For each sample it extracts the set of
field names, then writes them back into the primary app's
`uc_recommender_inventory` KV store under the `fields_extracted`
column so the recommender can prefer UCs whose `requiredFields` are
actually present in your data.

The TA is **not vetted for Splunk Cloud** (modular inputs require
explicit Cloud vetting). Install it on Enterprise search heads only.
Without the TA the recommender still works; it just flags every match
with "field coverage unknown".

## Install

1. Install the primary app first.
2. `tar czf splunk-uc-recommender-ta.spl splunk-uc-recommender-ta/` and upload via the Splunk
   app manager.
3. Enable the input under **Settings → Data inputs → UC Recommender
   deep scan**.

---

_This app is generated. Edits in place will be overwritten._
