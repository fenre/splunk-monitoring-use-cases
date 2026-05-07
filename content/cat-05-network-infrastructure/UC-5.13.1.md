<!-- AUTO-GENERATED from UC-5.13.1.json — DO NOT EDIT -->

---
id: "5.13.1"
title: "Device Health Score Overview"
status: "verified"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.1 · Device Health Score Overview

> **Criticality:** Critical &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability, Performance &middot; **Wave:** Crawl &middot; **Status:** Verified

*We watch the health of every network device managed by Catalyst Center and show you which ones are struggling, so problems get fixed before they cause outages. We rank them worst-first, so the team knows exactly where to look. Over months, the trend tells us which devices need replacing before they become a bigger problem.*

---

## Description

Surfaces the latest Catalyst Center Assurance health score for every managed network device, ranked worst-first, so operations can triage degraded switches, routers, and wireless controllers before users report connectivity problems.

## Value

A device health score below 50 almost always means active user impact — dropped packets, slow convergence, or failed client onboarding. Catching it in a Splunk overview first means you open the Device 360 in Catalyst Center, isolate the subscore (CPU, memory, link), and remediate before the NOC phone rings. Over 90 days the trend line also reveals chronic underperformers that need hardware refresh, IOS-XE upgrade, or workload redistribution — turning reactive firefighting into planned capacity work.

## Implementation

Install `TA_cisco_catalyst` (Splunkbase 7538) on the Search Head and the Heavy Forwarder. Configure a Catalyst Center account in the TA (Configuration → Account → Add: URL, service account with NETWORK-ADMIN-ROLE, verify SSL). Enable the `devicehealth` input (Inputs → Create → Device Health: account `catcenter-prod`, index `catalyst`, interval `900`). Schedule the search every 15 minutes over the last 1 hour, throttle by `deviceName` for 4 hours.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk (`TA_cisco_catalyst`, Splunkbase 7538) ≥1.0 installed on Search Heads (for knowledge objects and field extractions) AND on the Heavy Forwarder or single-instance Splunk that will run the modular input. Do NOT deploy to Universal Forwarders — they cannot run Python modular inputs.
- Catalyst Center **2.3.5+** so `overallHealth` and the Assurance subscore fields (`memoryScore`, `cpuScore`, `interDeviceLinkScore`) align with current Intent API output. Older releases may use different field names or scoring algorithms — validate with a sample event.
- Service account on Catalyst Center with **NETWORK-ADMIN-ROLE** (minimum for Assurance health data). **SUPER-ADMIN-ROLE** is needed only if you also plan to collect audit logs. Use a dedicated API account, not a personal login.
- Network: HTTPS (TCP 443) from the Splunk Heavy Forwarder to the Catalyst Center management IP or FQDN. If a web proxy sits between them, configure the TA's proxy settings in Configuration → Proxy.
- Splunk role: users running this search need `srchIndexesAllowed = catalyst`. Add to a custom role (`network_observer`) rather than granting `admin`.
- License headroom: the `cisco:dnac:devicehealth` sourcetype generates ~800 bytes/device/poll × 96 polls/day ≈ **75 KB/device/day** ≈ **2.3 GB/month per 1,000 devices** at the default 900s interval. Plan `fleet_size × 2.3 GB` of monthly license for this sourcetype alone. See `docs/guides/catalyst-center.md` § Sizing for the full multi-sourcetype estimate.
- Baseline knowledge: expected normal `overallHealth` per device role (core ≈ 85–95, distribution ≈ 80–90, access ≈ 70–85, WLC ≈ 80–90). Scores vary by network design; use your first week of data to establish site-specific baselines for Step 3 validation and Step 5 troubleshooting.

### Step 1 — Configure data collection
In the TA on the Heavy Forwarder (or single-instance), go to Configuration → Account → Add:

| Setting | Value |
|---------|-------|
| Account Name | `catcenter-prod` (descriptive, no spaces) |
| URL | `https://catcenter.example.com` (FQDN, no trailing slash) |
| Username | `splunk-svc@example.com` (dedicated service account) |
| Password | (service account password — stored encrypted in `passwords.conf`) |
| Verify SSL | Yes (use No only for lab/self-signed certs) |

Then go to Inputs → Create New Input → Device Health:

| Setting | Value |
|---------|-------|
| Account | `catcenter-prod` |
| Index | `catalyst` |
| Interval | `900` (15 minutes — shorter improves freshness but increases API load and may trigger throttling above 5,000 devices) |

The TA authenticates to `POST /dna/system/api/v1/auth/token`, then polls `GET /dna/intent/api/v1/device-health`. It follows Cisco pagination automatically. Each poll produces one JSON event per managed device with fields: `overallHealth`, `reachabilityHealth`, `deviceName`, `deviceType`, `siteId`, `platformId`, `managementIpAddress`, `softwareVersion`, `memoryScore`, `cpuScore`, `interDeviceLinkScore`, `deviceFamily`, `location`.

Verification: wait one poll interval (15 minutes), then run:
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=-30m | stats count by deviceType
```
You should see rows for each device family (switches, routers, WLC, APs). Compare `| stats dc(deviceName) as device_count` to the device count in **Catalyst Center > Provision > Inventory**.

If no events arrive, check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for error messages. Common failures: `401 Unauthorized` (wrong credentials), `Connection refused` (wrong URL or firewall), `SSL certificate verify failed` (self-signed cert — set Verify SSL to No for lab, or install the CA cert).

Expected event volume: 1 event × `device_count` per poll. A 500-device campus at interval=900 produces ~48,000 events/day ≈ 38 MB/day for this sourcetype.

### Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| stats latest(overallHealth) as health_score latest(reachabilityHealth) as reachability by deviceName, deviceType, siteId
| eval health_status=case(health_score>=75,"Healthy",health_score>=50,"Fair",health_score>=25,"Poor",1==1,"Critical")
| sort health_score
```

Why `latest()` not `avg()`: the Intent API returns a point-in-time composite score for each device. Unlike raw CPU metrics that fluctuate second-to-second, `overallHealth` is already an Assurance-computed average. Taking `latest()` gives you the current state for triage; `avg()` over multiple polls would mask a sudden drop (e.g. a link failure that dropped the score from 90 to 30 in one poll).

Why these health_score bands (75 / 50 / 25): these align with Catalyst Center's own Assurance presentation where **below 50 is "Poor"** in the GUI. The bands in this SPL are intentionally compatible — when an operator clicks through to Catalyst Center > Device 360, the colour coding matches. Tighten the bands for stricter SLOs: for example, `>=80` for core switches in a hospital, or `>=70` for all devices in a data centre.

Why no CIM variant: Catalyst Center health scores are a proprietary Assurance construct — they don't map to the CIM Performance model, which expects `cpu_load_percent` as a raw hardware metric. Forcing health scores into CIM would misrepresent them. If you need CIM-compliant device monitoring, combine this UC with syslog-based CPU/memory UCs (e.g. UC-5.1.x for Cisco IOS `sourcetype=cisco:ios`).

Schedule as Alert: cron `*/15 * * * *`, time range `-1h to now`, trigger on "Number of results where health_score < 50 > 0", throttle suppression on `deviceName` field for `4h` so the same degraded device doesn't re-page during the same incident. For reachability alerts specifically, see UC-5.13.4.

### Step 3 — Validate
(a) In Catalyst Center, navigate to **Assurance > Health > Device**. Note the `overallHealth` score for three specific devices — one healthy (score > 80), one borderline (50–70), and one known-problematic. In Splunk, run `index=catalyst sourcetype="cisco:dnac:devicehealth" deviceName="<that-device>" | head 1 | table _time overallHealth reachabilityHealth memoryScore cpuScore`. The scores should match within 1–2 points (poll timing difference).

(b) Confirm device count parity: `| stats dc(deviceName) as devices` in Splunk vs **Catalyst Center > Provision > Inventory > count**. If Splunk shows fewer devices, the service account's virtual domain scope is too narrow — see Prerequisites.

(c) Check field extraction: `index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=-5m | fieldsummary | where count > 0 | table field count distinct_count`. All key fields (`overallHealth`, `reachabilityHealth`, `deviceName`, `deviceType`, `siteId`) should appear with non-zero distinct counts. If `overallHealth` is entirely null, Assurance is not licensed or not running on the Catalyst Center cluster.

(d) Confirm ingest cadence: `index=catalyst sourcetype="cisco:dnac:devicehealth" | timechart span=15m count`. You should see a regular step function with one spike per poll. Flat-line gaps indicate a stalled input, expired credentials, or API throttling.

(e) Confirm role permissions: `| rest splunk_server=local /servicesNS/-/-/authorization/roles | search title=<your-role> | table title srchIndexesAllowed`. The list must include `catalyst`.

### Step 4 — Operationalize
Dashboard (recommended layout, named "Catalyst Center — Device Health Overview"):
- Row 1 — Single value tiles: "Devices with health < 50" (red threshold ≥ 1, links to filtered table), "Unreachable devices" (red threshold ≥ 1), "Fleet health average" (gauge 0–100, yellow < 80).
- Row 2 — Sortable table: deviceName | health_score | health_status | reachability | deviceType | siteId | platformId. Sorted by health_score ascending. Drilldown: click a device → open Catalyst Center Device 360 URL (`https://<catcenter>/dna/assurance/device/<deviceId>/overview`) in a new tab.
- Row 3 — Stacked bar or trellis: `| stats count by health_status` showing fleet mix (green Healthy, yellow Fair, orange Poor, red Critical). Side-by-side comparison over 24h vs 7d to spot fleet-level degradation.
- Row 4 — Top-10 worst-trending devices from UC-5.13.2 (timechart overlay, last 24h).
- Time-picker presets: "Last 1 hour" (incident view), "Last 24 hours" (daily review), "Last 30 days" (capacity review).

Alerting:
- Splunk On-Call / PagerDuty: low-urgency on first violation per device, high-urgency if the same device re-fires within 4h or if > 5 devices simultaneously drop below 50. Annotate the alert with the device's Catalyst Center Device 360 URL.
- Slack/Teams notification to `#network-ops` for visibility, no paging.

Runbook (owner: Network Operations on-call):
1. Open the device's row in the Splunk dashboard. Note the health_score and which subscore is lowest (cpuScore, memoryScore, or interDeviceLinkScore).
2. If `reachabilityHealth = Unreachable`, this is a hard down — pivot to UC-5.13.4 and escalate immediately.
3. If `cpuScore` is the dominant contributor (< 50 while others are > 70), SSH/console to the device. `show processes cpu sorted | head 10` to identify the runaway process (common: OSPF SPF storm, DAI inspection, heavy ACL logging).
4. If `memoryScore` is lowest, check `show memory platform` for memory leak indicators. Correlate with `index=catalyst sourcetype="cisco:dnac:securityadvisory"` for known memory-leak PSIRTs affecting this platform.
5. If `interDeviceLinkScore` is lowest, check upstream/downstream interface status in **Catalyst Center > Device 360 > Interfaces** or via `index=catalyst sourcetype="cisco:dnac:interfacehealth" deviceId="<id>"`. A single down uplink on a distribution switch causes this.
6. Check planned maintenance: `index=catalyst sourcetype="cisco:dnac:audit:logs" earliest=-4h` and your `catalyst_maintenance_windows` lookup.
7. If unresolved: open a Catalyst Center Assurance issue (the platform may have already auto-detected the root cause — check **Assurance > Issues** for the same device).

Capacity review (cadence: monthly, owner: Network Capacity Planning):
- Query: `index=catalyst sourcetype="cisco:dnac:devicehealth" | bin _time span=1d | stats avg(overallHealth) as daily_health by deviceName, _time | where daily_health < 50 | stats count as days_below_50 by deviceName | where days_below_50 > 7`.
- Action thresholds: 7–14 days/month below 50 → flag for configuration tuning or IOS-XE upgrade; >14 days/month → flag for hardware replacement or workload redistribution.

### Step 5 — Troubleshooting

- **No events at all** — TA not installed on the Heavy Forwarder, or the `devicehealth` input is not enabled. Check: TA → Inputs list → confirm Device Health is present and enabled. On the CLI: `$SPLUNK_HOME/bin/splunk btool inputs list --debug | grep -i cisco_catalyst` should show your input stanza. Check `$SPLUNK_HOME/var/log/splunk/splunkd.log` for `ExecProcessor` entries naming the TA with `rc=0`.

- **Events arriving but `overallHealth` is null for all devices** — Assurance is not licensed or not running on this Catalyst Center cluster. DNA Essentials provides inventory but NOT Assurance health scores — you need DNA Advantage or Premier. Verify in Catalyst Center > System > Licensing. Also check: some platforms (older Catalyst 3850/3650) are not supported by Assurance and will show null scores.

- **Fewer devices than Catalyst Center Inventory shows** — the service account's virtual domain scope is too narrow. The TA sees only devices in the domains the service account can access. Compare `| stats dc(deviceName)` in Splunk to the count in Catalyst Center > Provision > Inventory at **Global** scope. Fix: expand the service account's domain access, or create one input per domain.

- **Scores frozen (same `_time` and `overallHealth` for hours)** — the TA is re-ingesting cached responses or the Catalyst Center API is returning stale data. Check `_indextime - _time` distribution: `index=catalyst sourcetype="cisco:dnac:devicehealth" | eval lag=_indextime-_time | stats avg(lag) max(lag)`. Lag > 1800s indicates a stuck input or proxy timeout. Restart the input (disable/re-enable in the TA UI).

- **401 Unauthorized in TA logs** — service account password expired or was changed. Check `index=_internal sourcetype=splunkd "TA_cisco_catalyst" "401"`. Rotate the credential in the TA: Configuration → Account → Edit → update password.

- **HTTP 429 (Too Many Requests) or 503 errors** — API throttling. Catalyst Center enforces ~5 requests/second for the Intent API. If you have many inputs firing simultaneously, stagger their intervals (e.g. devicehealth at 900, clienthealth at 930, networkhealth at 960). For fleets > 5,000 devices, increase the devicehealth interval to 1800s.

- **`overallHealth` suddenly drops to 0 for many devices simultaneously then recovers** — this is the Assurance recomputation cycle (see Known False Positives). Confirm by checking whether the dip affects > 30% of devices in a < 5 minute window. Filter with `| where overallHealth > 0` or require two consecutive bad polls.

- **Single device shows health=0 but is reachable and operational** — the device model may not be supported by Assurance's health scoring engine (e.g. some Meraki-managed devices that appear in Catalyst Center inventory but aren't scored by Assurance). Check in Catalyst Center > Assurance > Device 360 for that device — if Assurance shows "N/A" or no score, filter it from your overview with `| where isnum(overallHealth) AND overallHealth > 0`.

- **Dashboard shows stale data after a TA upgrade** — field names may have changed between TA versions. Run `index=catalyst sourcetype="cisco:dnac:devicehealth" earliest=-1h | fieldsummary` and compare with `earliest=-30d@d latest=-29d@d | fieldsummary` to spot renamed fields. Check the TA release notes for breaking changes.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth"
| stats latest(overallHealth) as health_score latest(reachabilityHealth) as reachability by deviceName, deviceType, siteId
| eval health_status=case(health_score>=75,"Healthy",health_score>=50,"Fair",health_score>=25,"Poor",1==1,"Critical")
| sort health_score
```

## Visualization

(1) Sortable table: deviceName, health_score, health_status, reachability, deviceType, siteId — sorted by health_score ascending so the sickest devices are at the top. (2) Single value tiles: count of devices with health_score < 50 (red threshold ≥ 1), count of devices with reachabilityHealth = Unreachable. (3) Trellis or stacked bar of `| stats count by health_status` for a fleet-mix gauge (green/yellow/orange/red). (4) Optional timechart overlay from UC-5.13.2 showing the 10 worst-trending devices over 24h to spot gradual degradation that a snapshot misses.

## Known False Positives

**Assurance recomputation cycle.** Catalyst Center's Assurance engine periodically recomputes health scores (typically near the top of each hour). During the 2–3 minute recomputation window, `overallHealth` may temporarily report as 0 or null for many devices simultaneously. Distinguish from a real outage by checking whether the dip affects a large fraction of devices in the same narrow window and recovers on the next poll. Suppress by adding `| where overallHealth>0` or by requiring two consecutive polls below threshold before alerting.

**New device onboarding via Plug and Play (PnP).** Devices provisioned through Catalyst Center PnP report low or zero health scores until Assurance builds a baseline, typically 30–60 minutes after onboarding. Distinguish by correlating with `index=catalyst sourcetype="cisco:dnac:device"` for devices with very short `upTime` or recent first-seen timestamps. Suppress by maintaining a `catalyst_new_devices` lookup populated from PnP events and excluding devices onboarded within the last 2 hours.

**Catalyst Center cluster upgrade or maintenance window.** During Catalyst Center platform upgrades (2–6 hours for major versions), the Intent API may return stale data or HTTP 503 errors, causing health scores to freeze or disappear. Distinguish by checking `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for HTTP 503 or timeout errors in the same window. Suppress by using a `catalyst_maintenance_windows` lookup with start and end times for scheduled Catalyst Center maintenance.

**Virtual domain scope mismatch — devices not visible to the TA service account.** If the Catalyst Center service account is scoped to a subset of virtual domains, some devices will be absent from the overview — appearing as missing rather than unhealthy. Distinguish by comparing `| stats dc(deviceName)` in Splunk to the device count in Catalyst Center > Provision > Inventory at Global scope. This is a configuration gap, not a false positive to suppress — expand the service account's virtual domain access or create separate inputs per domain.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Device Health endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-device-health)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [Catalyst Center API authentication — token lifecycle](https://developer.cisco.com/docs/catalyst-center/#!authentication)
