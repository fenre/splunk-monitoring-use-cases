<!-- AUTO-GENERATED from UC-5.13.12.json — DO NOT EDIT -->

---
id: "5.13.12"
title: "Client Health by SSID and VLAN"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.12 · Client Health by SSID and VLAN

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We break down the wireless experience by network name — your office Wi-Fi, your guest Wi-Fi, your IoT network — so when the Wi-Fi is bad, you know exactly which network is the problem and which group of people is affected. The corporate network for voice calls matters more than the guest network for visitor phones.*

---

## Description

Breaks down wireless client health by SSID and VLAN, isolating which wireless networks and network segments have the poorest user experience — so you can tell whether the problem is your corporate SSID, your guest SSID, your IoT SSID, or a specific VLAN that's serving a bad DHCP pool.

## Value

UC-5.13.9 tells you wireless health is low; this UC tells you *which SSID*. A corporate SSID at 85% healthy alongside a guest SSID at 50% is a very different problem from both at 60%. The corporate SSID carries VoIP and Webex — that's a P2 incident. The guest SSID carries personal devices — that's a facilities request. Without the SSID split, you'd investigate everything; with it, you focus on the SSID that matters most to the business. The VLAN dimension adds another layer: a VLAN with a nearly-full DHCP scope will show concentrated poor health while the SSID as a whole looks fine.

## Implementation

Requires the `client` detail input (heavier than `clienthealth`). Enable the `client` input: Inputs → Create → Client Detail, account `catcenter-prod`, index `catalyst`, interval `900`. Validate that `ssid` and `vlanId` are populated in the events. For wired-only environments, remove the `connectionType="WIRELESS"` filter.

## Detailed Implementation

### Prerequisites
- UC-5.13.9 (Client Health Overview) should be operational first for context.
- This UC uses the **`client` detail input**, not the `clienthealth` summary input. The `client` input is significantly heavier: **1 event per connected client per poll**. A campus with 2,000 clients at 900s interval generates ~150 MB/day. Ensure your Splunk license and index can accommodate this volume before enabling.
- Service account with **NETWORK-ADMIN-ROLE** for client detail data.
- Confirm `ssid` and `vlanId` are populated in the events. The `ssid` field is null for wired clients — filter to `connectionType="WIRELESS"` for SSID analysis. `vlanId` should be present for both wired and wireless.
- For environments with many SSIDs (> 10), consider maintaining an `ssid_classification` lookup with columns `ssid, category` (corporate, guest, IoT, voice) for grouping and threshold management.

### Step 1 — Configure data collection
Enable the `client` detail input if not already running:

| Setting | Value |
|---------|-------|
| Input type | Client Detail |
| Account | `catcenter-prod` |
| Index | `catalyst` |
| Interval | `900` (15 minutes — may need to increase to `1800` for campuses with > 5,000 clients due to API pagination and volume) |

The TA polls `GET /dna/intent/api/v1/client-detail` (or the client listing endpoint). Each connected client produces one JSON event with fields: `macAddress`, `ssid`, `vlanId`, `connectionType`, `healthScore{}`, `hostType`, `location`, `apName`, `rssi`, `snr`.

Verification:
```spl
index=catalyst sourcetype="cisco:dnac:client" earliest=-30m
| stats dc(macAddress) as unique_clients dc(ssid) as unique_ssids by connectionType
```
Compare `unique_clients` with the client count in **Catalyst Center > Assurance > Client Health**. They should be within 10% (poll timing and client churn cause small differences).

**Volume warning**: this is the heaviest Catalyst Center sourcetype. Monitor `index=catalyst sourcetype="cisco:dnac:client" | stats count` × avg event size to project monthly license impact. For 2,000 clients: ~150 MB/day × 30 = ~4.5 GB/month.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS"
| stats avg(healthScore{}.score) as avg_health dc(macAddress) as client_count by ssid, vlanId
| eval health_status=case(avg_health>=80,"Good", avg_health>=60,"Fair", 1==1,"Poor")
| sort avg_health
```

Why `connectionType="WIRELESS"` filter: `ssid` is null for wired clients. Including wired clients would create a null-SSID bucket that conflates all wired connections into one misleading row. For wired VLAN analysis (without SSID), use a variant: `| where connectionType="WIRED" | stats avg(healthScore{}.score) as avg_health dc(macAddress) as client_count by vlanId`.

Why `avg(healthScore{}.score)` instead of the category-level percentage: this UC uses per-client data, not the aggregate summary. Each client has its own health score, and averaging across clients in the same SSID/VLAN gives a true population-weighted health metric. The `healthScore{}.score` field is nested — validate the path with `| head 1 | spath`.

Why `dc(macAddress)` for client count: MAC addresses are unique per client. `count` would count events (inflated by multiple polls per client within the search window). `dc(macAddress)` gives the actual number of distinct clients.

Why health_status bands at 80/60: these align with the general Catalyst Center Assurance health interpretation. For SSID-specific thresholds (e.g., corporate at 85, guest at 65, IoT at 50), replace the `case()` with a lookup: `| lookup ssid_thresholds ssid OUTPUT good_threshold fair_threshold | eval health_status=case(avg_health>=good_threshold,"Good", avg_health>=fair_threshold,"Fair", 1==1,"Poor")`.

This is a report panel, not a real-time alert. For alerting on client health drops, use UC-5.13.11 which operates on the lighter aggregate feed.

### Step 3 — Validate
(a) Run the search and compare the SSID list with **Catalyst Center > Assurance > Health > Client Health** filtered by "SSID". All active SSIDs should appear in both views.

(b) Pick the SSID with the lowest `avg_health`. In Catalyst Center, filter the client health view to that SSID and compare the health score and client count. They should agree within 5 points and 10% of clients (poll timing differences).

(c) Verify VLAN population: `| stats dc(vlanId) as vlans by ssid`. Each SSID should map to 1–3 VLANs (typically one VLAN per SSID, but some designs use multiple VLANs for load balancing). If a single SSID maps to > 10 VLANs, something may be misconfigured.

(d) Check for null SSIDs: `| stats count(eval(isnull(ssid))) as null_ssid, count as total`. If `null_ssid > 0`, those are wired clients leaking through the `connectionType="WIRELESS"` filter — check the filter is working.

(e) Cross-reference a poor-health SSID with UC-5.13.42 (RSSI/SNR) to determine if the issue is signal quality or something else (DHCP, DNS, RADIUS).

### Step 4 — Operationalize
Dashboard placement (on the "Client Experience" dashboard or a dedicated "Wireless Analysis" dashboard):
- Table: ssid | vlanId | avg_health | client_count | health_status — sorted worst-first.
- Bar chart: client_count by ssid, coloured by health_status.
- Drilldown: click an SSID → filter UC-5.13.42 (RSSI/SNR) and UC-5.13.44 (Roaming) to that SSID.
- Token-driven filter: add an SSID dropdown populated by `| stats dc(macAddress) by ssid | sort -dc(macAddress)` so engineers can focus on one SSID at a time.

Runbook (owner: Wireless Engineering):
1. Identify the SSID with the worst `avg_health`.
2. If it's a **guest SSID**: check client count. Guest SSIDs with > 200 clients may be at capacity. Check DHCP scope utilisation for the guest VLAN. Consider adding more APs or implementing rate limiting.
3. If it's a **corporate SSID**: this is a high-priority finding. Check UC-5.13.42 (RSSI/SNR) — if signal is poor, it's an RF/coverage issue. If signal is fine but health is low, check RADIUS authentication (`index=ise`), DHCP, or DNS.
4. If a **specific VLAN** within an SSID is much worse than others: check the DHCP scope for that VLAN. Run `show ip dhcp pool` on the DHCP server to check for scope exhaustion.
5. Track per-SSID health monthly. SSIDs that consistently show "Poor" are candidates for design review (AP placement, channel width, band steering policy).

### Step 5 — Troubleshooting

- **`ssid` is null for all events** — the `connectionType="WIRELESS"` filter may not be working (check case sensitivity: `WIRELESS` vs `wireless`), or the TA doesn't extract `ssid` from the API response. Check `| fieldsummary | search field=ssid`.

- **Only one SSID appears** — your campus may genuinely have one SSID (single-SSID design), or the API is returning a subset. Compare with **Catalyst Center > Assurance > Client Health > SSID** dropdown.

- **`healthScore{}.score` is null** — the nested health score path may differ in your TA version. Run `| head 1 | spath` and search for any field containing "health" and "score" to find the correct path.

- **Client count much higher than expected** — the search window covers multiple polls, and each poll produces one event per client. `dc(macAddress)` should still give unique counts, but if it's too high, check for MAC spoofing or duplicate client entries in the API.

- **Search is very slow** — the `cisco:dnac:client` sourcetype is high-volume. Narrow the time range (`earliest=-20m` for a single-poll snapshot), add SSID-specific filters if you know which SSID to investigate, or use summary indexing for daily aggregates.

- **Guest SSID dominates the table** — expected in campus environments with open guest Wi-Fi. Consider splitting the dashboard into "Corporate SSIDs" and "Guest SSIDs" sections using a `ssid_classification` lookup.

- **VLAN field shows unexpected values (0, null, or very high numbers)** — some client types report VLAN 0 or null when the VLAN assignment is in progress. Filter with `| where isnum(vlanId) AND vlanId > 0`.

- **Health scores disagree with UC-5.13.9** — UC-5.13.9 uses the aggregate `clienthealth` summary feed, while this UC uses per-client data from `client`. The aggregation methods differ (Assurance-weighted vs simple average). Directional agreement is expected; exact parity is not.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS"
| stats avg(healthScore{}.score) as avg_health dc(macAddress) as client_count by ssid, vlanId
| eval health_status=case(avg_health>=80,"Good", avg_health>=60,"Fair", 1==1,"Poor")
| sort avg_health
```

## Visualization

(1) Table: ssid, vlanId, avg_health, client_count, health_status — sorted by avg_health ascending (worst SSIDs first). (2) Stacked bar: client_count by health_status per SSID. (3) Optional heatmap: SSID (rows) × VLAN (columns) with avg_health as colour intensity. (4) Drilldown: click an SSID → filter to UC-5.13.42 (RSSI/SNR) for that SSID to see if the issue is signal quality or something else.

## Known False Positives

**Guest SSID inherently lower health due to diverse client devices.** Guest SSIDs serve personal devices (phones, tablets, laptops) with varied hardware capabilities and driver quality. Average health for guest SSIDs is typically 10–20 points lower than corporate SSIDs. Distinguish by comparing health scores against per-SSID baselines rather than a universal threshold. Suppress by setting separate thresholds per SSID using a `ssid_thresholds` lookup.

**IoT SSID with constrained devices reporting low health.** IoT devices (sensors, cameras, digital signage) often have limited wireless capabilities and report lower health scores. Distinguish by checking the `hostType` field — IoT devices may report as specific types. Suppress by excluding IoT SSIDs from the client health comparison or using IoT-specific health thresholds.

**VLAN with nearly-full DHCP scope causing concentrated poor health.** When a VLAN's DHCP scope is 95%+ full, new clients fail to get IP addresses and report poor health. The VLAN will show disproportionate poor health while other VLANs on the same SSID are fine. Distinguish by correlating with DHCP server statistics (`show ip dhcp pool` or DHCP server logs). Do not suppress — this is a real capacity issue that needs DHCP scope expansion.

**Hidden SSID or disabled SSID appearing in the data.** SSIDs that are disabled or hidden may still have a few clients associated (cached profiles). These show very low client counts with potentially poor health. Distinguish by checking whether `client_count < 5`. Suppress by filtering `| where client_count >= 10` for operational dashboards.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Client Detail endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-client-detail)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [Catalyst Center Integration Guide — Sample Events (client)](docs/guides/catalyst-center.md#sample-events)
