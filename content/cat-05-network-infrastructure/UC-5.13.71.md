<!-- AUTO-GENERATED from UC-5.13.71.json — DO NOT EDIT -->

---
id: "5.13.71"
title: "Catalyst Center + ThousandEyes Network Path Correlation"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.71 · Catalyst Center + ThousandEyes Network Path Correlation

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Wave:** Run &middot; **Status:** Verified

*We compare two views of your network simultaneously — the internal campus health from Catalyst Center and the external internet path quality from ThousandEyes. When your Wi-Fi is slow, this tells you whether the problem is inside your building or on the road between your building and the cloud — so your team contacts the right people immediately.*

---

## Description

Correlates Catalyst Center internal network health with ThousandEyes external path quality to isolate whether performance problems are inside the campus network or on the WAN/internet path.

## Value

The hardest troubleshooting question is 'is it us or them?' Correlating internal health (Catalyst Center) with external path quality (ThousandEyes) answers this question in seconds.

## Implementation

1. **Catalyst Center (TA 7538):** `cisco:dnac:networkhealth` on `index=catalyst` with `healthScore` (UC-5.13.16).
2. **ThousandEyes (app 7719):** Install and connect Te OTel/HTTP to Splunk per app docs; create or confirm the **`stream_index`** macro to point at the index containing Te agent-to-server test metrics (often a dedicated HEC/OTel index).
3. **Field model:** The SPL uses `thousandeyes.test.type` and `network.latency` / `network.loss` in OTel-style JSON — if your app normalizes to different field names, update the `stats` to match (e.g. `avg(latency_ms)`).
4. **Thresholds:** Tune `70`, `100` ms, and `5%` loss to your SLAs and baseline noise.

## Detailed Implementation

### Prerequisites
- UC-5.13.16 (Network Health Score Overview) must be operational for the Catalyst Center campus health dimension.
- **ThousandEyes integration** must be configured — either via the ThousandEyes App for Splunk (Splunkbase 7719) or the ThousandEyes TA with HEC/OpenTelemetry streaming. ThousandEyes data typically lands with sourcetypes like `thousandeyes:test`, `thousandeyes:agent`, or in an OpenTelemetry-compatible format.
- **Join field**: the correlation is time-based (`| bin _time span=5m`) because Catalyst Center and ThousandEyes have independent test scopes — there is no shared device ID. ThousandEyes measures external path quality (WAN/internet); Catalyst Center measures internal campus health. When both degrade simultaneously, the problem is shared infrastructure (ISP, DNS, firewall). When only one degrades, it isolates which domain is affected.
- This is a **run-tier** cross-product UC that provides the internal-vs-external isolation that neither platform can do alone. It answers: 'Is the problem our campus network or the path to the cloud?'

### Step 1 — Configure data collection
Catalyst Center: same `networkhealth` input as UC-5.13.16.

ThousandEyes: configure the ThousandEyes App (Splunkbase 7719) or custom HEC integration. Key metrics from ThousandEyes:
- `network.latency` — round-trip latency in seconds
- `network.loss` — packet loss percentage (0–1)
- `network.jitter` — jitter in seconds
- Test type: `agent-to-server` tests from enterprise agents to target services

Ensure both data sources are indexed:
```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" earliest=-1h | stats count as catalyst_events
| appendcols [search index=thousandeyes OR sourcetype="thousandeyes:*" earliest=-1h | stats count as te_events]
```

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:networkhealth"
| where healthScore > 0
| bin _time span=5m
| stats latest(healthScore) as internal_health by _time
| appendcols
    [search index=thousandeyes sourcetype="thousandeyes:*" test_type="agent-to-server"
     | bin _time span=5m
     | stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss by _time
     | eval avg_latency_ms=round(avg_latency_s*1000,1)
     | eval loss_pct=round(avg_loss*100,1)]
| where isnotnull(internal_health) AND isnotnull(avg_latency_ms)
| eval isolation=case(
    internal_health < 70 AND avg_latency_ms < 50, "Internal network issue — campus infrastructure",
    internal_health >= 80 AND avg_latency_ms > 100, "External path issue — WAN/internet/cloud",
    internal_health < 70 AND avg_latency_ms > 100, "Both internal AND external degradation",
    1==1, "Both healthy")
| where isolation != "Both healthy"
| table _time, internal_health, avg_latency_ms, loss_pct, isolation
| sort _time
```

Why time-based correlation (`bin _time span=5m`): Catalyst Center and ThousandEyes have no shared device identifiers. The correlation is temporal — when campus health drops at the same time as internet path quality degrades, the root cause is likely shared (ISP, DNS, gateway). When only one drops, it isolates the fault domain.

Why the four-quadrant isolation logic: this is the core value of the cross-product correlation. It maps every 5-minute window into one of four states:
- **Internal only**: campus degraded, internet fine → switch/AP/WLC issue (use UC-5.13.1 for triage)
- **External only**: campus fine, internet degraded → ISP/WAN/cloud issue (use ThousandEyes path visualisation for triage)
- **Both**: simultaneous degradation → shared infrastructure (gateway, DNS, firewall) or coincidental failures
- **Neither**: everything healthy — no action needed

Why `appendcols` not `join`: `appendcols` aligns results by row position after both subsearches are time-bucketed identically. It's simpler than `join` for time-aligned correlation when both sources are bucketed to the same span.

Schedule: as a real-time dashboard panel (auto-refresh every 5 minutes) for the NOC. Also as hourly alert for `isolation != "Both healthy"`.

### Step 3 — Validate
(a) During a known campus network issue (switch failure, AP outage), the search should show `isolation="Internal network issue"` with `internal_health < 70` and `avg_latency_ms < 50` (internet unaffected).

(b) During a known ISP outage, the search should show `isolation="External path issue"` with `internal_health >= 80` and `avg_latency_ms > 100`.

(c) Verify the 5-minute time alignment: both subsearches should produce the same number of rows per time window. If one has gaps, it disrupts the `appendcols` alignment.

(d) Check ThousandEyes latency baseline: `| stats avg(avg_latency_ms) p95(avg_latency_ms)`. Normal latency depends on your geography — 20ms for domestic, 100ms for transatlantic. Adjust the threshold accordingly.

(e) Vendor UI parity: compare the internal_health value with **Catalyst Center > Assurance > Health** and the latency/loss values with **ThousandEyes > Views > Network Overview**.

### Step 4 — Operationalize
- NOC dashboard: real-time 4-quadrant view. When `isolation` changes from "Both healthy" to any other state, the NOC immediately knows which domain to investigate.
- Alert: trigger when `isolation` is not "Both healthy" for 2+ consecutive 5-minute windows. Route to the appropriate team based on the isolation value.

Runbook:
1. "Internal network issue": investigate campus infrastructure — UC-5.13.1 (Device Health), UC-5.13.9 (Client Health), UC-5.13.21 (Issues).
2. "External path issue": investigate WAN/internet — ThousandEyes path visualisation shows where the degradation occurs (ISP hop, DNS resolver, cloud provider).
3. "Both degradation": check shared infrastructure — default gateway, DNS servers, firewall, NAT. These are the devices that bridge internal and external paths.

### Step 5 — Troubleshooting

- **No ThousandEyes data** — the ThousandEyes integration is not configured. Install the ThousandEyes App (Splunkbase 7719) or configure HEC streaming.

- **`appendcols` alignment issues** — if the two subsearches produce different row counts, `appendcols` may misalign. Ensure both use identical `bin _time span=5m` and cover the same time range.

- **Latency threshold too high/low** — 100ms is appropriate for domestic US/EU paths. For transatlantic or APAC paths, increase to 200ms. For local data centre paths, decrease to 30ms.

- **`isolation` always shows "Both healthy"** — either no degradation events occurred (good) or the thresholds are too loose. Check individual metrics to verify the ranges.

- **ThousandEyes field names differ** — the field names depend on the ThousandEyes integration method (App vs HEC vs OTel). Check `| head 1 | spath` on the ThousandEyes events for actual field names.

- **Want to add SD-WAN correlation** — extend with a third `appendcols` subsearch for SD-WAN BFD/AppRoute data (UC-5.13.69). The isolation logic expands to 8 quadrants (internal × external × WAN overlay).

- **Performance** — the dual-subsearch approach is lightweight. Each subsearch aggregates to one row per 5-minute bucket. The `appendcols` alignment is fast.

- **Time zone mismatch** — ensure Splunk, Catalyst Center, and ThousandEyes all use the same timezone or UTC. Misalignment shifts the correlation window.

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as internal_health by _time | appendcols [search `stream_index` thousandeyes.test.type="agent-to-server" | stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss by _time | eval avg_latency_ms=round(avg_latency_s*1000,1) | eval loss_pct=round(avg_loss*100,1)] | where internal_health < 70 AND (avg_latency_ms > 100 OR loss_pct > 5) | eval isolation=if(internal_health<70 AND avg_latency_ms<50, "Internal network issue", if(internal_health>=70 AND avg_latency_ms>100, "External path issue", "Both internal and external issues")) | table _time internal_health avg_latency_ms loss_pct isolation
```

## Visualization

Table of internal_health, avg_latency_ms, loss_pct, isolation; optional Sankey or treemap of isolation reason counts; timechart overlay: internal_health vs Te latency.

## Known False Positives

**ThousandEyes test agent offline or unreachable causing missing network path data.** If a ThousandEyes cloud or enterprise agent is unavailable, the network path correlation will show gaps. Distinguish by checking `index=thousandeyes` for agent-health events or missing test results. Do not suppress — an offline ThousandEyes agent is its own operational issue.

**ThousandEyes measuring internet/cloud path quality while Catalyst Center measures campus LAN health.** A degradation in ThousandEyes scores (internet latency, cloud service reachability) does not necessarily correlate with Catalyst Center campus health. The divergence may be correct: the campus is healthy but the internet path is degraded. Distinguish by checking whether the ThousandEyes tests target internet endpoints or internal campus targets. No suppression needed — the divergence is informative.

**Different time granularity between ThousandEyes and Catalyst Center data.** ThousandEyes tests may run at 1-5 minute intervals while Catalyst Center polls at 15 minutes. The `appendcols` join may produce misaligned time comparisons. Distinguish by comparing the latest event timestamps from both sources. Suppress by binning both data sources to a common time span (e.g., 15 minutes) before correlation.

**ThousandEyes alert-only data appearing without baseline context.** If the ThousandEyes integration sends only alert/degradation events (not continuous health data), the correlation will only trigger during problems, not during normal operation. Distinguish by checking whether ThousandEyes data is continuous or event-driven. Suppress by noting the asymmetric data model in the dashboard description.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Cisco ThousandEyes App (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [Catalyst Center Network Health API — Cisco DevNet](https://developer.cisco.com/docs/catalyst-center/#!get-overall-network-health)
