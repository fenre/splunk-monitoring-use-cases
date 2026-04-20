---
id: "5.1.32"
title: "Network Device End-of-Life Tracking"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.32 · Network Device End-of-Life Tracking

## Description

Devices approaching EOL/EOS dates.

## Value

Devices approaching EOL/EOS dates.

## Implementation

Maintain device_inventory lookup (host, model) and eol_lookup (model, eol_date) from Cisco EOL/EOS bulletins. Run scheduled search or dashboard. Alert when days_to_eol < 180. Update lookups annually.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Lookup table with vendor EOL dates, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: Device inventory + EOL lookup.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Maintain device_inventory lookup (host, model) and eol_lookup (model, eol_date) from Cisco EOL/EOS bulletins. Run scheduled search or dashboard. Alert when days_to_eol < 180. Update lookups annually.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| inputlookup device_inventory
| lookup eol_lookup model OUTPUT eol_date eos_date
| eval days_to_eol=round((strptime(eol_date,"%Y-%m-%d")-now())/86400,0)
| where days_to_eol < 365 OR days_to_eol < 0
| table host model eol_date days_to_eol
| sort days_to_eol
```

Understanding this SPL

**Network Device End-of-Life Tracking** — Devices approaching EOL/EOS dates.

Documented **Data sources**: Device inventory + EOL lookup. **App/TA** (typical add-on context): Lookup table with vendor EOL dates, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

**Pipeline walkthrough**

• Loads rows via `inputlookup` (KV store or CSV lookup) for enrichment or reporting.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• `eval` defines or adjusts **days_to_eol** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where days_to_eol < 365 OR days_to_eol < 0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Network Device End-of-Life Tracking**): table host model eol_date days_to_eol
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (device, model, days to EOL), Single value (devices within 6 months), Gauge.

## SPL

```spl
| inputlookup device_inventory
| lookup eol_lookup model OUTPUT eol_date eos_date
| eval days_to_eol=round((strptime(eol_date,"%Y-%m-%d")-now())/86400,0)
| where days_to_eol < 365 OR days_to_eol < 0
| table host model eol_date days_to_eol
| sort days_to_eol
```

## Visualization

Table (device, model, days to EOL), Single value (devices within 6 months), Gauge.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
