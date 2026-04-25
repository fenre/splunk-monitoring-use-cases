<!-- AUTO-GENERATED from UC-5.4.4.json — DO NOT EDIT -->

---
id: "5.4.4"
title: "Rogue AP Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.4.4 · Rogue AP Detection

## Description

Rogue APs are unauthorized and can be used for man-in-the-middle attacks or network bridging.

## Value

Rogue APs are unauthorized and can be used for man-in-the-middle attacks or network bridging.

## Implementation

Forward WLC rogue detection events. Enable rogue detection policies. Alert on rogue APs, especially those broadcasting your corporate SSID.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: WLC syslog, Meraki TA.
• Ensure the following data sources are available: WLC/Meraki security events.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward WLC rogue detection events. Enable rogue detection policies. Alert on rogue APs, especially those broadcasting your corporate SSID.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:wlc" "rogue" ("detected" OR "alert" OR "contained")
| stats count by rogue_mac, detecting_ap, channel | sort -count
```

Understanding this SPL

**Rogue AP Detection** — Rogue APs are unauthorized and can be used for man-in-the-middle attacks or network bridging.

Documented **Data sources**: WLC/Meraki security events. **App/TA** (typical add-on context): WLC syslog, Meraki TA. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:wlc. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:wlc". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by rogue_mac, detecting_ap, channel** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
In the Cisco WLC or Catalyst 9800 wireless GUI (Monitor > Clients or Access Points), compare counts and statuses with the Splunk rows for the same period. Confirm a few client MACs or AP names.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (rogue MAC, detecting AP, channel), Map, Single value.

## SPL

```spl
index=network sourcetype="cisco:wlc" "rogue" ("detected" OR "alert" OR "contained")
| stats count by rogue_mac, detecting_ap, channel | sort -count
```

## Visualization

Table (rogue MAC, detecting AP, channel), Map, Single value.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
