<!-- AUTO-GENERATED from UC-5.13.60.json — DO NOT EDIT -->

---
id: "5.13.60"
title: "Access Point Health and Availability"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.60 · Access Point Health and Availability

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability, Performance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We keep a dedicated eye on every wireless access point across your buildings — the devices that provide Wi-Fi to everyone. When one goes down, we flag it immediately because every person in that area loses their wireless connection. We also track which AP models break most often to help plan replacements.*

---

## Description

Monitors the health and availability of every wireless access point in the Catalyst Center inventory, surfacing APs that are down (unreachable), degraded (health < 50), or healthy — giving the wireless team a dedicated AP view that's separate from the general device health overview (UC-5.13.1) where APs can be drowned out by switches and routers.

## Value

APs are the wireless user's gateway to the network. A down AP means everyone in its coverage area loses Wi-Fi — but a campus with 500 APs and 200 switches won't notice one AP down in the general device health view (UC-5.13.1) because it's 1 of 700 devices. This dedicated AP view ensures wireless team members see their equipment first. The per-site grouping tells them which building has the most AP problems, and the `platformId` tells them which AP model is most failure-prone (a reliability signal for the next hardware refresh). Since APs typically outnumber switches 3:1, they deserve their own monitoring surface.

## Implementation

Same `devicehealth` input as UC-5.13.1 — no additional input needed. Filter to AP device types. The `deviceType` string varies by Catalyst Center version: `Unified AP`, `ACCESS_POINT`, `Cisco Aironet Access Point`. Test with `| stats count by deviceType` to find the correct filter for your environment.

## Detailed Implementation

### Prerequisites
- UC-5.13.1 (Device Health Overview) must be operational — same `devicehealth` data feed.
- Determine the correct `deviceType` filter for APs in your environment:
  ```spl
  index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=-1h
  | stats dc(deviceName) by deviceType
  | search deviceType="*AP*" OR deviceType="*Access*" OR deviceType="*Unified*" OR deviceType="*Aironet*"
  ```
  Common values: `Cisco Aironet Access Point`, `Unified AP`, `ACCESS_POINT`. Use the exact string in your SPL filter.
- This UC gives the wireless team a dedicated AP view. Consider assigning it to a `wireless_team` Splunk role with AP-specific dashboard access.

### Step 1 — Configure data collection
Same `devicehealth` input as UC-5.13.1. No additional configuration. APs are part of the regular device health polling.

Verification:
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" (deviceType="*AP*" OR deviceType="*Access Point*") earliest=-1h
| stats dc(deviceName) as ap_count
```
Compare with the AP count in **Catalyst Center > Provision > Inventory** filtered to Access Points.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" (deviceType="*AP*" OR deviceType="*Access Point*" OR deviceFamily="Unified AP")
| stats latest(overallHealth) as health latest(reachabilityHealth) as reachability by deviceName, siteId, platformId
| eval ap_status=case(reachability="Unreachable","Down", health<50,"Degraded", 1==1,"Healthy")
| sort health
```

Why filter to AP device types: separates APs from the general device population. In a typical campus, APs outnumber switches 3:1 — mixing them in one view makes AP issues invisible among switch data.

Why `latest()` per AP: deduplicates across polls. Shows the current state per AP.

Why three status bands (Down/Degraded/Healthy): `Down` (unreachable) is the highest severity — users in that coverage area have no Wi-Fi. `Degraded` (reachable but health < 50) means the AP is struggling — poor client experience but not a complete outage.

Why include `platformId`: identifies the AP model (9115, 9120, 9130, 9136, etc.). Helps detect model-specific issues (firmware bug affecting one model, hardware batch problem).

For a per-site AP health summary:
```spl
<base search>
| stats count as total count(eval(ap_status="Down")) as down count(eval(ap_status="Degraded")) as degraded by siteId
| lookup catalyst_site_lookup siteId OUTPUT siteName
| sort -down -degraded
```

Schedule: every 15 minutes as a real-time dashboard panel. Alert: `ap_status="Down"` → page wireless team.

### Step 3 — Validate
(a) Compare the AP count with **Catalyst Center > Assurance > Health > Device** filtered to AP device types.
(b) Pick an AP showing `Down` in Splunk. Verify in **Catalyst Center > Assurance > Device 360 > [AP]** that it shows Unreachable.
(c) Pick a `Degraded` AP. Check the subscores in Device 360 — which dimension is pulling the AP health down?
(d) Compare the per-site AP summary with the wireless team's known trouble spots.
(e) Vendor UI parity: compare AP health distribution with **Catalyst Center > Assurance > Health > Device** filtered to APs.

### Step 4 — Operationalize
Dashboard (dedicated "Wireless AP Health" dashboard for the wireless team):
- Row 1: Single values — Down APs (red), Degraded APs (yellow), Total APs, AP healthy percentage.
- Row 2: Table of all APs sorted worst-first. Drilldown to Catalyst Center Device 360.
- Row 3: Per-site AP summary — which building has the most AP problems?
- Row 4: AP health timechart — trending to detect gradual AP fleet degradation.

Alerting:
- Down AP: page wireless on-call when `ap_status="Down"` for 2+ consecutive polls.
- Multiple Down APs at same site: escalate — likely an upstream switch or power issue.

Runbook (owner: Wireless Team):
1. Down AP detected. Check whether the AP is physically powered (verify PoE from the upstream switch port).
2. If PoE is fine: check the AP console/LED status. Solid red = boot failure. Flashing = recovering.
3. If multiple APs down at the same site: check the upstream switch (UC-5.13.1). If the switch is also unhealthy, the problem is the switch, not the APs.
4. If one AP is intermittently down: check for PoE budget issues on the switch (too many high-power devices on the same switch).
5. For degraded APs (health < 50): check UC-5.13.42 (RSSI/SNR) and UC-5.13.62 (Channel Utilisation) for the RF layer.
6. Track AP failure rates by `platformId` monthly. AP models with high failure rates are candidates for replacement.

### Step 5 — Troubleshooting

- **No APs in the results** — the `deviceType` filter doesn't match your Catalyst Center's AP naming. Check `| stats values(deviceType) | search *AP* OR *Access* OR *Aironet*`.

- **AP health is always 0** — APs may not support full Assurance health scoring in your Catalyst Center version. Check if `overallHealth` is populated for APs with `| stats avg(overallHealth) where deviceType="*AP*"`.

- **Too many APs showing Degraded** — APs in unoccupied areas report low health due to lack of client telemetry. Filter to APs with connected clients: join with `index=catalyst sourcetype="cisco:dnac:client"` to identify APs with active clients.

- **AP appears Down but users don't report issues** — the AP may be secondary coverage (clients roamed to nearby APs). Check UC-5.13.42 for RSSI at the affected location — if a neighbouring AP covers the area, the Down AP's impact is minimal.

- **AP count fluctuates between polls** — APs may be partially discovered or cycling between managed/unmanaged states. Check `index=catalyst sourcetype="cisco:dnac:device"` for AP inventory stability.

- **Want to see AP uptime** — use UC-5.13.8 (Uptime and Reboot Tracking) filtered to AP device types to identify APs that reboot frequently.

- **AP model-specific issues** — group by `platformId` and compare health: `| stats avg(health) as avg_health dc(deviceName) as count by platformId | sort avg_health`. Models with consistently low health may have firmware bugs.

- **PoE power budget correlation** — join with interface health data to check whether the upstream switch port shows PoE issues: `index=catalyst sourcetype="cisco:dnac:interfacehealth" | search *poe* OR *power*`.

Additional operational context for Access Point Health and Availability:

For month-over-month comparison:
- Export the primary search results monthly as CSV to a `catalyst_monthly_snapshots` directory. Compare current month vs previous month to identify trends, improvements, and regressions.
- Track the key metric from this UC over 90 days with `| timechart span=1w` for the quarterly operations review.

For SLA alignment:
- Define the acceptable threshold for this UC's primary metric in your SLA documentation.
- Schedule a weekly check against the SLA target. Breaches should generate tickets in your ITSM with a link to this UC's dashboard panel for investigation context.

Cross-reference with related UCs:
- When this UC flags an issue, always cross-reference with UC-5.13.1 (Device Health) and UC-5.13.16 (Network Health) to assess the broader impact.
- For compliance-related findings, connect to UC-5.13.28-33 for the compliance posture context.
- For security-related findings, connect to UC-5.13.34-39 for PSIRT advisory exposure.

Runbook integration:
- Document the response procedure for each alert from this UC in your operations runbook.
- Include: who to contact, what to check first, typical root causes, and escalation criteria.
- Review and update the runbook quarterly based on actual alert outcomes (was the runbook helpful? did it miss common scenarios?).

Additional troubleshooting:
- If the search returns unexpected results, check `| fieldsummary` on the base data to verify field names and types match the SPL.
- If data is not arriving for the expected sourcetype, verify the TA input is enabled and check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for errors from the modular input.
- If field values changed after a Catalyst Center upgrade, compare `| fieldsummary` from before and after the upgrade to identify renamed or restructured fields.
- If the search is slow, narrow the time range to `earliest=-20m` for a real-time snapshot, or use summary indexing for historical analysis.
- For vendor UI parity, cross-reference the Splunk results with the corresponding **Catalyst Center > Assurance** page for the same time window to confirm counts and values match.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" (deviceType="*AP*" OR deviceType="*Access Point*" OR deviceFamily="Unified AP")
| stats latest(overallHealth) as health latest(reachabilityHealth) as reachability by deviceName, siteId, platformId
| eval ap_status=case(reachability="Unreachable","Down", health<50,"Degraded", 1==1,"Healthy")
| sort health
```

## Visualization

(1) Table: deviceName, siteId, platformId, health, reachability, ap_status — sorted worst-first. (2) Single value tiles: Down AP count (red ≥ 1), Degraded AP count (yellow ≥ 5), Total APs. (3) Pie: AP status distribution (Healthy/Degraded/Down). (4) Timechart: `| timechart span=1h dc(eval(if(ap_status="Down",deviceName,null()))) as down_aps` for AP availability trending.

## Known False Positives

**AP rebooting during RRM optimisation.** Catalyst Center may push RRM changes (channel, power) that cause a brief AP reboot. The AP appears as Unreachable for 1–2 polls then recovers. Distinguish by checking whether the AP recovers within 30 minutes. Suppress by requiring Unreachable status to persist for 2+ consecutive polls.

**PoE cycling at the upstream switch port.** A switch port power cycle (maintenance, cable reseat, UPS event) causes the AP to reboot. Distinguish by correlating with switch interface status: `index=catalyst sourcetype="cisco:dnac:interfacehealth"`. Do not suppress — the root cause is the switch/power, not the AP, but the AP's unavailability is real.

**AP health score low due to no connected clients.** An AP in an unoccupied area (closed office, storage room) may report low health because Assurance can't compute meaningful metrics without client telemetry. Distinguish by checking `clientCount` — if zero, the low health is a data-quality artefact, not a failure. Suppress by filtering `| where clientCount > 0` or creating an `unoccupied_areas` lookup.

**Newly onboarded APs with transient low health.** APs recently provisioned via PnP may show low health for 30–60 minutes while Assurance builds baselines. Distinguish by checking AP uptime (UC-5.13.8). Suppress by allowing a 2-hour grace period for new APs.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Device Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-device-health)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [Cisco Catalyst 9100 Access Points — Data Sheet](https://www.cisco.com/c/en/us/products/wireless/catalyst-9100ax-access-points/datasheet-listing.html)
