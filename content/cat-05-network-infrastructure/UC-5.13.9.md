<!-- AUTO-GENERATED from UC-5.13.9.json — DO NOT EDIT -->

---
id: "5.13.9"
title: "Client Health Score Overview (Wired vs Wireless)"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.9 · Client Health Score Overview (Wired vs Wireless)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Wave:** Crawl &middot; **Status:** Verified

*We show you how many people on your network are having a good experience versus a bad one, split between wired and wireless connections. When wireless drops but wired stays fine, we know it is a Wi-Fi problem, not a backbone problem — so the right team gets called immediately instead of everyone guessing.*

---

## Description

Breaks down Catalyst Center's client health score into wired and wireless segments, showing how many clients are connected and what percentage are healthy in each category, so operations can tell at a glance whether a user-experience problem is campus-wide, Wi-Fi-only, or wired-only.

## Value

Client experience is the metric that executives and help-desk managers actually feel. A wireless healthy percentage below 80% during business hours means dropped VoIP calls, failed Webex joins, and frustrated employees — and you need to know whether to investigate the RF layer, the DHCP/DNS infrastructure, or the wired backhaul. This overview separates wired from wireless in one view so you route the right engineer to the right problem within minutes, not hours. Over weeks the trend also reveals whether a campus renovation, AP firmware push, or SSID change made things better or worse.

## Implementation

Install `TA_cisco_catalyst` (Splunkbase 7538) on the Search Head and Heavy Forwarder. Configure a Catalyst Center account (Configuration → Account → Add). Enable the `clienthealth` input (Inputs → Create → Client Health: account `catcenter-prod`, index `catalyst`, interval `900`). The nested JSON requires `spath | mvexpand | spath` to flatten — validate field extraction with one raw event before building dashboards.

## Detailed Implementation

### Prerequisites
- `TA_cisco_catalyst` (Splunkbase 7538) ≥1.0 installed on Search Heads AND the Heavy Forwarder / single-instance running inputs.
- Catalyst Center **2.3.5+** with **DNA Advantage** or **DNA Premier** licensing — DNA Essentials provides inventory but NOT Assurance client health scores. Without Assurance licensing, the `clienthealth` API returns empty `scoreDetail` arrays.
- Service account with **NETWORK-ADMIN-ROLE** (minimum). Pure observer roles are often blocked from client health endpoints.
- Network: HTTPS (TCP 443) from Splunk HF to Catalyst Center management IP/FQDN.
- Splunk role: users need `srchIndexesAllowed = catalyst`.
- License headroom: the `cisco:dnac:clienthealth` sourcetype generates ~3 events/poll × 96 polls/day × 1.2 KB ≈ **350 KB/day** (aggregate summary). This is one of the lightest Catalyst Center sourcetypes — it does NOT scale with client count because it's a summary feed.
- Baseline knowledge: expected `healthyClientsPercentage` for your campus. Typical enterprise: wireless 75–90%, wired 90–98%. Guest SSIDs drag the wireless average down. Establish your own baselines during the first week.
- **Critical nested JSON note:** the `clienthealth` sourcetype uses double-nested JSON — `scoreDetail{}` is an array of objects, each containing a `scoreCategory` object with its own `scoreCategory` string and `value` integer. You MUST use `spath | mvexpand | spath input=` to extract fields. Direct field references like `scoreDetail{}.scoreCategory.value` are unreliable across TA versions.

### Step 1 — Configure data collection
In the TA on the Heavy Forwarder: Inputs → Create New Input → Client Health.

| Setting | Value |
|---------|-------|
| Account | `catcenter-prod` |
| Index | `catalyst` |
| Interval | `900` (15 minutes) |

The TA authenticates to `POST /dna/system/api/v1/auth/token`, then polls `GET /dna/intent/api/v1/client-health`. The response is an aggregate summary — NOT one event per connected client. Each poll produces approximately 3 JSON events:

```json
{
  "scoreDetail": [
    {
      "scoreCategory": { "scoreCategory": "ALL", "value": "72" },
      "clientCount": 450,
      "scoreList": [
        { "scoreCategory": { "scoreCategory": "WIRED", "value": "85" }, "clientCount": 120 },
        { "scoreCategory": { "scoreCategory": "WIRELESS", "value": "68" }, "clientCount": 330 }
      ]
    }
  ]
}
```

Verification: wait one poll interval, then run:
```spl
index=catalyst sourcetype="cisco:dnac:clienthealth" earliest=-30m | head 1 | spath
```
Confirm you see `scoreDetail{}` with nested `scoreCategory` and `clientCount` fields. If `scoreDetail` is empty (`[]`), Assurance is not licensed — see Prerequisites.

If no events arrive at all, check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for errors. Common failures: `401 Unauthorized` (wrong credentials), `Connection refused` (wrong URL or firewall), `SSL certificate verify failed` (self-signed cert).

### Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:clienthealth"
| spath output=categories path=scoreDetail{}
| mvexpand categories
| spath input=categories
| eval category=mvindex(split(spath(categories, "scoreCategory.scoreCategory"), ","), 0)
| stats latest(clientCount) as clients latest(healthyClientsPercentage) as healthy_pct by category
| eval client_type=case(category=="ALL","All Clients", category=="WIRED","Wired", category=="WIRELESS","Wireless", 1==1, category)
| table client_type, clients, healthy_pct
| sort client_type
```

Why `spath | mvexpand | spath input=`: the client health JSON is double-nested. Direct field references like `scoreDetail{}.scoreCategory.value` are fragile — they break when the TA changes JSON serialisation between versions or when pagination wraps the array differently. The three-stage `spath` pattern is the reliable way to extract nested arrays in Splunk and survives TA upgrades without SPL changes.

Why `latest()` not `avg()`: like device health, client health is already an Assurance-computed aggregate. Taking `latest()` shows the current state for triage. `avg()` across multiple polls would smooth out a sudden wireless health drop caused by an AP outage — you want to see that drop immediately.

Why `healthyClientsPercentage` not `value`: the `value` field in `scoreCategory` is the overall health band score (0–100). `healthyClientsPercentage` is the actual percentage of clients in the "Good" health band, which is a more actionable metric for operations. If your TA build doesn't emit `healthyClientsPercentage`, fall back to `value` and note this in your dashboard documentation.

Schedule as Alert: cron `*/15 * * * *`, time range `-1h to now`, trigger when WIRELESS `healthy_pct < 60`, throttle on `category` for `4h`.

### Step 3 — Validate
(a) In Catalyst Center, navigate to **Assurance > Health > Client Health**. Note the ALL / WIRED / WIRELESS scores and client counts. In Splunk, run the Step 2 search over the same 15-minute window. Scores should match within 2 percentage points (poll timing difference).

(b) Confirm the spath extraction produces exactly 3 rows (ALL, WIRED, WIRELESS). If you see fewer, the API may be returning fewer categories for wired-only campuses — this is normal. If you see more rows than expected, check for duplicate `scoreCategory` strings in the raw JSON.

(c) Verify `clientCount` is plausible: compare `clients` from the Splunk search to the number shown in **Catalyst Center > Assurance > Health > Client Health > Total Connected Clients**. If Splunk shows 0 clients but the Catalyst Center UI shows active clients, the API token may be scoped to an empty virtual domain.

(d) Ingest cadence: `index=catalyst sourcetype="cisco:dnac:clienthealth" | timechart span=15m count`. Expect a regular step function. Gaps indicate a stalled input, expired credentials, or API throttling.

(e) Cross-reference with UC-5.13.1 (Device Health): if `WIRELESS healthy_pct` drops sharply but device health for WLCs remains high, the problem is likely RF or DHCP, not a WLC hardware issue.

### Step 4 — Operationalize
Dashboard (recommended layout, placed as the "Client Experience" row on the Catalyst Center overview dashboard):
- Row 1 — Three single-value tiles: ALL (clients + healthy %), WIRED (clients + healthy %), WIRELESS (clients + healthy %). Colour thresholds: green ≥ 80%, yellow 60–80%, red < 60%. Click through to UC-5.13.10 (trending) or UC-5.13.12 (by SSID).
- Row 2 — Stacked bar: client count by health band (Good/Fair/Poor/Idle/New) split by WIRED vs WIRELESS. This shows the distribution shape — a long "Poor" tail on wireless during business hours is a coverage gap; a spike of "Idle" on wired is a power-save or VLAN isolation issue.
- Row 3 — Timechart: healthy_pct for WIRED and WIRELESS overlaid on one chart, last 24h with `span=1h`. Diverging lines (wireless drops while wired stays flat) isolate the problem to the RF/wireless layer.
- Time-picker presets: "Last 4 hours" (incident), "Last 24 hours" (daily review), "Last 7 days" (weekly ops review).

Alerting:
- PagerDuty/On-Call: trigger when WIRELESS `healthy_pct < 60` for 2+ consecutive polls during business hours (Mon–Fri 07:00–19:00 local). Annotate with client count and site ID if available.
- Slack/Teams: `#network-ops` for any category dropping below 70% — informational, no paging.

Runbook (owner: Network Operations on-call):
1. Open the client health dashboard. Identify which category is degraded: ALL, WIRED, or WIRELESS.
2. If WIRELESS only: check UC-5.13.42 (RSSI/SNR) for signal quality issues. Check UC-5.13.12 (by SSID) to isolate if the problem is on a specific SSID (often guest vs corporate). Check UC-5.13.44 (roaming) for excessive roaming events. If RSSI is fine but health is low, suspect DHCP/DNS — check `index=ise sourcetype=cisco:ise:*` for authentication failures.
3. If WIRED only: check UC-5.13.1 for switch health scores. Check `index=catalyst sourcetype="cisco:dnac:interfacehealth"` for down ports. Common cause: STP topology change or VLAN misconfiguration on an access switch.
4. If ALL degraded: this usually indicates a shared-infrastructure problem — DNS, DHCP, RADIUS/ISE, or an upstream routing issue. Correlate with UC-5.13.16 (Network Health) and UC-5.13.21 (Assurance Issues).
5. Check planned maintenance: `index=catalyst sourcetype="cisco:dnac:audit:logs" earliest=-4h` for recent configuration changes.
6. Cross-reference with help desk ticket volume: a spike in user complaints validates the health score drop.

### Step 5 — Troubleshooting

- **No events at all** — `clienthealth` input not enabled, or TA not installed on the Heavy Forwarder. Check: TA → Inputs → confirm Client Health is present and enabled. On the CLI: `$SPLUNK_HOME/bin/splunk btool inputs list --debug | grep -i clienthealth`. Check `splunkd.log` for `ExecProcessor` entries with error codes.

- **Events arrive but `scoreDetail` is empty (`[]`)** — Assurance is not licensed on this Catalyst Center cluster. DNA Essentials does NOT include client health scoring. Verify licensing in **Catalyst Center > System > Licensing**. Also check: Assurance may be licensed but disabled for the site — **Assurance > Settings > Enable/Disable**.

- **`spath` produces no rows after `mvexpand`** — the JSON nesting structure changed between TA versions. Dump one raw event: `| head 1 | spath` and examine the actual path to the score data. Common variants: `scoreDetail{}.scoreCategory.scoreCategory` vs `scoreDetail{}.scoreCategory.value` vs `response.scoreDetail{}`. Adjust the `spath path=` accordingly.

- **`healthyClientsPercentage` is null but `clientCount` is populated** — your Catalyst Center version or TA build doesn't emit this field. Fall back to `value` from the `scoreCategory` object, which is the overall health score (0–100) for that category. The two metrics are related but not identical.

- **Client count in Splunk ≠ Catalyst Center UI** — three common causes: (1) time window mismatch (Catalyst Center defaults to "last 1 hour", Splunk search may cover a different range); (2) virtual domain scoping (service account sees a subset); (3) wired clients without 802.1X are invisible to Assurance on some deployments.

- **WIRELESS healthy_pct drops every night at the same time** — this is the nightly AP maintenance window or RRM optimisation schedule. Validate by checking `index=catalyst sourcetype="cisco:dnac:wireless:rf"` for channel changes at that time. Suppress by excluding the maintenance window from alerting or by using time-of-day-aware baselines.

- **Alert fires during campus events (conferences, orientations)** — guest SSID onboarding surges drag down the wireless average. Track guest and corporate SSIDs separately in UC-5.13.12 (Client Health by SSID). Filter guest SSIDs from the overview alert using a `guest_ssid_list` lookup.

- **Data gap after TA upgrade** — field names in the nested JSON may have changed. Compare `| fieldsummary` on events from before and after the upgrade. Check the TA release notes for breaking changes to client health field extraction.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:clienthealth"
| spath output=categories path=scoreDetail{}
| mvexpand categories
| spath input=categories
| eval category=mvindex(split(spath(categories, "scoreCategory.scoreCategory"), ","), 0)
| stats latest(clientCount) as clients latest(healthyClientsPercentage) as healthy_pct by category
| eval client_type=case(category=="ALL","All Clients", category=="WIRED","Wired", category=="WIRELESS","Wireless", 1==1, category)
| table client_type, clients, healthy_pct
| sort client_type
```

## Visualization

(1) Three single-value tiles: ALL client count + healthy %, WIRED client count + healthy %, WIRELESS client count + healthy % — colour-coded green ≥ 80%, yellow 60–80%, red < 60%. (2) Stacked bar: client count by health band (Good/Fair/Poor/Idle/New) split by wired vs wireless. (3) Timechart overlay of healthy_pct for WIRED and WIRELESS over 24h from UC-5.13.10, to spot diverging trends. (4) Optional trellis by siteId if the API returns site-scoped categories.

## Known False Positives

**Mass DHCP renewal event causing temporary client disconnections.** A scheduled DHCP scope renewal can cause many clients to temporarily disconnect and reconnect, dropping the wired or wireless client count and health score for one poll cycle. Distinguish by correlating with DHCP server logs (`index=dhcp` or `index=ise sourcetype=cisco:ise:syslog DHCP`) for renewal events in the same 15-minute window. Suppress by requiring the health drop to persist across 2+ polls before alerting.

**Radio Resource Management (RRM) channel or power adjustment affecting wireless client health.** When Catalyst Center's RRM engine changes AP channels or power levels, wireless clients may temporarily reassociate, causing a dip in WIRELESS health while WIRED remains stable. Distinguish by correlating with `index=catalyst sourcetype="cisco:dnac:wireless:rf"` for channel or power changes in the same time window. Suppress by requiring the WIRELESS health dip to persist for 2+ consecutive polls.

**Guest SSID onboarding surge during large meetings or campus events.** A conference, orientation, or large gathering can spike guest wireless client count while depressing the average wireless health score (guest devices typically have lower health). Distinguish by checking whether `clientCount` increased significantly in the same window and whether the dip is concentrated on guest SSIDs. Suppress by filtering guest SSIDs from health alerting using a `guest_ssid_list` lookup, or by monitoring guest and corporate SSIDs separately.

**Catalyst Center client health data delayed during high-client-count environments.** In environments with thousands of connected clients, the client health API response may be delayed or paginated, causing apparent gaps in the health score trend. Distinguish by checking `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for timeout or pagination errors. Do not suppress — this indicates the poll interval may need to be increased for the clienthealth input.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Client Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-client-health)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [Catalyst Center Client Health nested JSON — sample event](docs/guides/catalyst-center.md#sample-events)
