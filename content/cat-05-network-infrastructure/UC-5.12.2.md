<!-- AUTO-GENERATED from UC-5.12.2.json — DO NOT EDIT -->

---
id: "5.12.2"
title: "Call Volume Trending by Destination"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.12.2 · Call Volume Trending by Destination

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Capacity

*We help you see which called areas or routes get busy over time so you can plan trunks and spot odd spikes that are not part of a normal day.*

---

## Description

Traffic engineering for trunk groups and geographic hot spots — detects flash crowds or fraud-driven spikes to premium destinations.

## Value

Traffic engineers and fraud analysts detect flash crowds, capacity constraints, and toll fraud spikes by destination prefix before they impact service or revenue.

## Implementation

Mask PANI for privacy dashboards; use HMAC of full number for drilldown in secured role.

## Detailed Implementation

### Prerequisites
- CDR data flowing into `index=voip` with `sourcetype=cdr:voip` (or your vendor-specific variant). Key fields required: `called_number` (destination number in E.164 format), `route_label` or `trunk_group` (identifies the trunk used), `duration_sec`, `call_status`.
- A destination prefix lookup `prefix_geo.csv` mapping number prefixes to countries/regions. For NANP numbers (North America), the first 6 digits identify the NPA-NXX (area code + exchange). For international E.164, the country code (1-3 digits) identifies the country. Sources: ITU-T E.164 assignment tables, your carrier's rate deck, or open datasets like libphonenumber.
- Privacy considerations: full called numbers are PII in many jurisdictions (GDPR, CPNI). For shared dashboards, use only the prefix (first 4-6 digits) and mask the subscriber portion. For authorized drilldowns, use HMAC of the full number tied to a Splunk role that only fraud/security analysts hold.
- Baseline knowledge: understand your normal call volume patterns by day-of-week and hour-of-day. Business hours show high domestic volume; evenings show more mobile/residential. Sudden spikes to international premium prefixes outside these patterns are strong fraud indicators.

### Step 1 — Configure data collection
Verify CDR data includes `called_number` and `route_label`:
```spl
index=voip sourcetype="cdr:voip" earliest=-1h
| stats count dc(called_number) as unique_destinations dc(route_label) as unique_routes
```
If `route_label` is null, check your SBC CDR format — some vendors call it `trunk_group`, `route_pattern`, or `peer_name`. Build and upload the `prefix_geo.csv` lookup from your carrier's rate deck or the ITU E.164 registry. For production, import a comprehensive prefix-to-geography mapping with columns: prefix, country, region, risk_tier (normal/premium/satellite).

### Step 2 — Create the search and alert

**Primary search — Call volume by destination prefix (hourly):**
```spl
index=voip sourcetype="cdr:voip" earliest=-24h
| eval dest_prefix=substr(called_number, 1, 6)
| eval dest_country_code=case(match(called_number, "^\+?1"), "NANP", match(called_number, "^\+?44"), "UK", match(called_number, "^\+?49"), "DE", match(called_number, "^\+?47"), "NO", 1==1, substr(called_number, 1, 3))
| timechart span=1h count as calls sum(duration_sec) as total_sec by dest_country_code limit=20
```

#### Understanding this SPL: We extract a 6-digit prefix for granular destination identification and a country code for high-level geographic grouping. The timechart shows hourly call volume and total minutes by destination country over 24 hours, revealing traffic patterns and anomalies.

**Anomaly detection — unexpected destination spike:**
```spl
index=voip sourcetype="cdr:voip" earliest=-7d
| eval dest_prefix=substr(called_number, 1, 6)
| bin _time span=1h
| stats count as calls by _time, dest_prefix
| eventstats avg(calls) as avg_calls stdev(calls) as std_calls by dest_prefix
| where calls > avg_calls + (4 * std_calls) AND calls > 20
| eval spike_ratio=round(calls/avg_calls, 1)
| lookup prefix_geo.csv prefix as dest_prefix OUTPUT country region risk_tier
| sort -spike_ratio
```

#### Understanding this SPL: Detects hourly call volume spikes to specific prefixes that exceed 4 standard deviations above the 7-day average. The minimum threshold of 20 calls prevents false positives on low-volume destinations. A sudden 10x spike to a premium international prefix outside business hours is a strong toll fraud indicator.

**Top routes by volume (daily capacity report):**
```spl
index=voip sourcetype="cdr:voip" earliest=-24h
| stats count as calls sum(duration_sec) as total_sec dc(called_number) as unique_destinations by route_label
| eval total_hours=round(total_sec/3600, 1)
| eval avg_duration_sec=round(total_sec/calls, 0)
| sort -calls
```

Schedule as Alert: anomaly detection runs hourly. Trigger on spike_ratio > 5 for any prefix. Route to fraud/security team.

### Step 3 — Validate
(a) Compare top 10 destination prefixes in Splunk to your carrier's traffic report for the same day. Volume per prefix should match within 10%.
(b) Test the anomaly detection: inject 50 test CDRs with an unusual prefix in a low-traffic hour and verify the search detects the spike.
(c) Validate the `prefix_geo.csv` lookup against a known number — call a known UK number and verify the CDR maps to country=UK.
(d) Check that `called_number` formatting is consistent across all SBCs/gateways — different vendors may use different E.164 formats.

### Step 4 — Operationalize
Dashboard ("Voice — Destination Volume Analytics"):
- Row 1 — Timechart: call volume by destination country over 7 days. Filter input for specific country codes.
- Row 2 — Top 20 destination prefixes table with calls, minutes, avg duration, and geo lookup.
- Row 3 — Anomaly detection results: flagged prefixes with spike ratio and geo context.
- Row 4 — Route utilization: calls and minutes per trunk group, for capacity planning.

Alerting:
- Fraud (spike_ratio > 10 to premium/high-cost prefix): page fraud team immediately. Include prefix, country, spike ratio.
- Capacity (route_label call volume > 80% of historical peak): notify capacity planning team.

Runbook (owner: Fraud / Voice Operations):
1. **Premium prefix spike**: Block the prefix on the SBC immediately. Investigate which calling parties are generating the traffic. Check for compromised SIP credentials or unauthorized trunk access.
2. **Flash crowd to a destination**: Verify if a known event explains the spike. If legitimate, ensure trunk capacity can handle the load.
3. **Gradual shift in destination mix**: Review for changes in customer behavior, marketing campaigns, or new route configurations.

### Step 5 — Troubleshooting

- **`called_number` is in inconsistent formats** — Different SBCs may report numbers with or without country code, with or without "+" prefix, or in national format. Normalize in `props.conf` using `SEDCMD` or `EVAL-called_number_e164` to convert all numbers to E.164 format before prefix extraction.

- **Prefix lookup returns null for many numbers** — The lookup may not be comprehensive enough. For a quick solution, extract just the country code (first 1-3 digits after "+" or "00") for geographic grouping.

- **Timechart shows empty periods** — CDR batch delivery may create gaps if files are not delivered on schedule. Verify the CDR file rotation and delivery mechanism. Switch to real-time syslog CDR delivery for continuous monitoring.

- **Anomaly detection fires on weekday/weekend transitions** — Day-of-week patterns are normal. Use `| where date_wday IN ("monday","tuesday","wednesday","thursday","friday")` to restrict the baseline to business days if your traffic is primarily B2B.

## SPL

```spl
index=voip sourcetype="cdr:voip"
| eval dest_prefix=substr(called_number,1,6)
| timechart span=1h sum(duration_sec) as minutes count as calls by dest_prefix
| sort -calls
```

## Visualization

Line chart (calls by prefix), Map (if geo-lookup on prefix), Table (top routes).

## Known False Positives

Holidays, marketing bursts, and short code campaigns can change destination mix without a fault; baseline by day-of-week before alerting.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
