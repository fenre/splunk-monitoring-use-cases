<!-- AUTO-GENERATED from UC-5.13.15.json — DO NOT EDIT -->

---
id: "5.13.15"
title: "Client Health Category Breakdown (Good/Fair/Poor/Idle/New)"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.15 · Client Health Category Breakdown (Good/Fair/Poor/Idle/New)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We show the full picture of how every connected person is doing — not just 'healthy or not,' but whether they're doing great, doing OK, struggling, or completely stuck. We also count the devices that are asleep and the ones we've lost track of, because both of those tell us something important about how the network is being used.*

---

## Description

Breaks down client health beyond the binary healthy/unhealthy split into Catalyst Center's full category taxonomy — Good, Fair, Poor, Idle, New, NoData — revealing not just how many clients are struggling but what *kind* of problem they have: idle clients wasting AP capacity, new clients stuck in onboarding, or NoData clients that Assurance has lost track of entirely.

## Value

UC-5.13.9 gives you a headline percentage; this UC gives you the distribution shape. A campus with 80% Good and 20% Poor is a very different problem from 60% Good, 20% Fair, 10% Idle, 10% New. The first means 20% of clients have serious issues. The second means many clients are in marginal states that could tip either way — the network is fragile, not broken. The Idle band is operationally interesting: high Idle counts mean APs are dedicating resources to clients that aren't actively transmitting (sleeping laptops, powered-off devices with cached associations), which affects airtime for active users. NoData clients represent monitoring blind spots where Assurance can't assess the health.

## Implementation

Same data feed as UC-5.13.9. The nested JSON must be flattened with `spath | mvexpand | spath` to extract the per-band breakdown. Place as a companion panel next to UC-5.13.9's headline tiles — together they provide the executive number (healthy %) and the engineering detail (category distribution).

## Detailed Implementation

### Prerequisites
- UC-5.13.9 (Client Health Overview) must be operational — confirms the `clienthealth` feed and nested JSON extraction work correctly.
- Understand the Catalyst Center health band taxonomy. The bands are determined by Assurance's scoring algorithm and vary slightly between Catalyst Center versions:
  - **GOOD** (health score ≥ 7 on a 1-10 scale, or ≥ 70%): client is connected, authenticated, and performing well.
  - **FAIR** (4-6 or 40-69%): client is connected but experiencing marginal performance (moderate latency, some retransmissions).
  - **POOR** (1-3 or < 40%): client is connected but experiencing significant issues (high latency, frequent retransmissions, packet loss).
  - **IDLE**: client is associated but not actively transmitting data. Common for sleeping laptops, powered-off devices with cached associations.
  - **NEW**: client recently connected and Assurance hasn't yet computed a health score. Typically transitions to another band within 5-15 minutes.
  - **NODATA**: Assurance cannot determine the client's health, usually because telemetry is unavailable from the AP.

### Step 1 — Configure data collection
No additional configuration. Same `clienthealth` input as UC-5.13.9. Confirm the health band breakdown is present in the nested JSON:
```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" earliest=-30m
| spath output=categories path=scoreDetail{}
| mvexpand categories
| spath input=categories output=band path=scoreCategory.scoreCategory
| stats dc(band) as band_count, values(band) as band_names
```
You should see 4-6 distinct bands. If only `ALL`/`WIRED`/`WIRELESS` appear, you're at the wrong nesting level — drill deeper into `scoreList{}` within `scoreDetail{}`.

The exact JSON path depends on your Catalyst Center version and TA. Common structures:
- `scoreDetail{}.scoreList{}.scoreCategory.scoreCategory` → GOOD, FAIR, POOR, etc.
- `scoreDetail{}.healthDistribution{}.category` → alternative path in some versions

Use `| head 1 | spath` on a raw event to map the actual structure before building the dashboard.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:clienthealth"
| spath output=categories path=scoreDetail{}
| mvexpand categories
| spath input=categories output=band path=scoreCategory.scoreCategory
| spath input=categories output=client_count path=clientCount
| where isnum(client_count) AND band IN ("GOOD","FAIR","POOR","IDLE","NEW","NODATA")
| stats latest(client_count) as count by band
| eventstats sum(count) as total
| eval pct=round(count*100/total,1)
| table band, count, pct
| sort -count
```

Why `latest(client_count)` per band: if the search window covers multiple polls, `latest()` gives the most recent snapshot. Using `avg()` would smooth across polls, which is fine for trending but misleading for a point-in-time breakdown.

Why `eventstats sum(count) as total`: computes the grand total across all bands in a single pass, so `pct` sums to 100%. Without `eventstats`, you'd need a subsearch or `appendpipe` for the denominator.

Why filter to specific band names: Catalyst Center may include additional internal categories (e.g., `ALL`, `WIRED`, `WIRELESS` from the parent level) that would corrupt the breakdown. The explicit `IN ()` filter ensures only health bands are included.

Why show all bands including IDLE and NODATA: these are operationally significant. A high IDLE percentage (> 30%) means many devices are reserving AP resources without using them — a capacity planning signal. A high NODATA percentage (> 5%) means Assurance has blind spots — a monitoring coverage gap.

This is a dashboard panel, not an alert. Use it alongside UC-5.13.9 and UC-5.13.10 for the complete client health picture.

### Step 3 — Validate
(a) Run the search and verify the band names match what you see in **Catalyst Center > Assurance > Health > Client Health > Health Distribution**.

(b) Sum `count` across all bands. It should approximately match the total client count from UC-5.13.9. If significantly different, the nested path is extracting a subset.

(c) Verify percentages sum to 100% (±0.1% due to rounding).

(d) Check the distribution shape against expectations: during business hours, GOOD should dominate (60-90%), IDLE should be low (5-15%). During off-hours, IDLE should increase significantly (30-60%) as devices sleep.

(e) Cross-reference: if UC-5.13.11 is alerting on poor client health, the POOR band here should show a meaningful percentage (> 10%). If POOR is at 2% but the alert is firing, the threshold in UC-5.13.11 may need tuning.

### Step 4 — Operationalize
Dashboard placement (on the "Client Experience" dashboard, next to UC-5.13.9's headline tiles):
- **Pie or donut chart**: band distribution with colour coding (GOOD green, FAIR yellow, POOR red, IDLE grey, NEW blue, NODATA black).
- **Table**: band | count | pct — for exact numbers.
- Time-picker: default "Last 1 hour" for current state.

Interpretation guide:
- **High GOOD (> 80%)**: healthy campus, no action needed.
- **High FAIR (> 20%)**: many clients in marginal state. This is a fragility signal — a small change (AP reboot, interference event) could push FAIR clients to POOR. Investigate RF quality (UC-5.13.42) and DHCP/DNS health.
- **High POOR (> 10%)**: active user impact. Trigger investigation per UC-5.13.11's runbook.
- **High IDLE (> 40%)**: capacity waste. Consider implementing idle-timeout policies on the WLC to free up AP resources.
- **High NEW (> 5% sustained)**: onboarding is slow or stuck. Investigate per UC-5.13.14.
- **High NODATA (> 5%)**: monitoring gap. Some APs may not be sending telemetry to Catalyst Center. Check AP health (UC-5.13.60) and WLC connectivity.

### Step 5 — Troubleshooting

- **Only 3 bands appear (ALL, WIRED, WIRELESS) instead of health bands** — you're extracting from the wrong nesting level. The health bands (GOOD/FAIR/POOR/IDLE/NEW) are typically one level deeper: `scoreDetail{}.scoreList{}.scoreCategory.scoreCategory`. Adjust the `spath path=` accordingly.

- **Band names are different from expected** — Catalyst Center may use localised or version-specific names. Run `| stats values(band)` to see the actual strings. Common variants: `Good`/`GOOD`, `Fair`/`FAIR`, `idle`/`IDLE`. Use `| eval band=upper(band)` to normalise.

- **Percentages don't sum to 100%** — a band is being excluded by the `IN ()` filter. Remove the filter temporarily and check `| stats values(band)` for any unexpected category names.

- **NODATA is very high (> 20%)** — significant monitoring gap. Common causes: old APs that don't support Assurance telemetry, APs with firmware that predates the current Assurance protocol, or APs in a virtual domain the service account can't see.

- **IDLE is always 0** — your Catalyst Center version may not report IDLE clients, or the band name differs. Check with `| head 1 | spath` for idle-related fields.

- **Client counts in the breakdown don't match the total from UC-5.13.9** — the breakdown may exclude some client categories (e.g., clients on non-managed SSIDs). The discrepancy is the number of clients outside the health band classification.

- **Distribution changes dramatically between polls** — clients transition between bands as network conditions change. This is expected behaviour. For a stable view, use `avg()` across 4+ polls (`earliest=-1h`) instead of `latest()`.

- **FAIR band growing over time** — this is the most important trend signal in this UC. A growing FAIR band means your network is losing headroom. Investigate before FAIR transitions to POOR.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:clienthealth"
| spath output=categories path=scoreDetail{}
| mvexpand categories
| spath input=categories output=band path=scoreCategory.scoreCategory
| spath input=categories output=client_count path=clientCount
| where isnum(client_count) AND band IN ("GOOD","FAIR","POOR","IDLE","NEW","NODATA")
| stats latest(client_count) as count by band
| eventstats sum(count) as total
| eval pct=round(count*100/total,1)
| table band, count, pct
| sort -count
```

## Visualization

(1) 100% stacked bar: client count by band, with GOOD green, FAIR yellow, POOR red, IDLE grey, NEW blue, NODATA black. (2) Pie chart of pct by band for proportional view. (3) Table: band | count | pct — sorted by count for operational focus. (4) Timechart variant (from UC-5.13.10 style): `| timechart span=1h sum(client_count) by band` stacked to show how the distribution shifts during business hours vs off-hours.

## Known False Positives

**High IDLE count during off-hours is expected.** Laptops and phones that go to sleep maintain their Wi-Fi association but stop transmitting, moving from GOOD to IDLE. This is normal behaviour, not a problem. Distinguish by checking whether IDLE count correlates with time of day (increases after business hours). Do not suppress — but interpret IDLE as "capacity reserved for sleeping devices" rather than "unhealthy."

**NEW count spikes after AP reboot or VLAN change.** When an AP reboots, all its clients reconnect and briefly appear as NEW before Assurance reclassifies them. Distinguish by correlating with UC-5.13.8 (Uptime/Reboot) for recent AP reboots. Suppress by requiring the NEW spike to persist for 2+ polls.

**NODATA for clients on non-managed APs.** Clients connected to APs not managed by Catalyst Center (rogue APs, personal hotspots, non-Cisco APs) may appear as NODATA if they're partially visible to the Assurance engine. Distinguish by checking whether the NODATA clients are on known SSIDs. Investigate NODATA as a potential monitoring gap.

**FAIR clients are not necessarily a problem.** The FAIR band represents clients with marginal health that are still functional. A high FAIR percentage is normal in dense environments with many 2.4GHz-only IoT devices. Distinguish by checking the device types in the FAIR band. Suppress by treating FAIR as informational, not actionable, unless it's trending upward.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Client Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-client-health)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [Catalyst Center Assurance — Client Health Bands](https://www.cisco.com/c/en/us/td/docs/cloud-systems-management/network-automation-and-management/catalyst-center-assurance/assurance-overview.html)
