<!-- AUTO-GENERATED from UC-5.13.40.json — DO NOT EDIT -->

---
id: "5.13.40"
title: "Client Inventory and Connection Summary"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.40 · Client Inventory and Connection Summary

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Inventory &middot; **Wave:** Crawl &middot; **Status:** Verified

*We count and categorise every device connected to your network — laptops, phones, tablets, IoT gadgets — and show you how many of each type are connected and whether they're on Wi-Fi or plugged in with a cable. This tells your team how big the network population is and whether unexpected devices are showing up.*

---

## Description

Provides a complete inventory of every client device visible to Catalyst Center, grouped by operating system / device type (Windows, Mac, iOS, Android, Linux, IoT) and connection method (wired vs wireless), giving operations and security teams a baseline understanding of who and what is on the network.

## Value

You can't protect or optimise what you don't know about. This inventory is the foundation for capacity planning (how many clients per AP?), security policy (are there unexpected IoT devices?), and support resource allocation (what's the Windows vs Mac ratio for desktop support?). It also reveals shadow IT — an unexpected spike in `Linux` or `Unknown` host types often indicates unmanaged devices, containers, or raspberry-pi-style gear plugged into the wired network. The connection type breakdown shows the wired-to-wireless ratio, which directly affects AP sizing and switch port planning.

## Implementation

Enable the `client` detail input: Inputs → Create → Client Detail, account `catcenter-prod`, index `catalyst`, interval `900`. This is a high-volume input — ensure Splunk license can absorb ~75 KB/client/day. Schedule the inventory report daily for security review and monthly for capacity planning.

## Detailed Implementation

### Prerequisites
- `TA_cisco_catalyst` (Splunkbase 7538) ≥1.0 installed on Search Heads AND the Heavy Forwarder.
- The `client` detail input is the **heaviest** Catalyst Center sourcetype. Budget your Splunk license accordingly:
  - 500 clients: ~37 MB/day ≈ 1.1 GB/month
  - 2,000 clients: ~150 MB/day ≈ 4.5 GB/month
  - 10,000 clients: ~750 MB/day ≈ 22.5 GB/month
- Consider whether you need the per-client detail at all. For basic client health monitoring, UC-5.13.9 through UC-5.13.15 use the lightweight `clienthealth` summary feed (~350 KB/day total). This UC and UC-5.13.12–14, 41–44 use the per-client feed for deeper analysis.
- Service account with **NETWORK-ADMIN-ROLE** for client detail data.
- Catalyst Center **2.3.5+** for consistent `hostType` classification and `connectionType` values.

### Step 1 — Configure data collection
Enable the `client` detail input:

| Setting | Value |
|---------|-------|
| Input type | Client Detail |
| Account | `catcenter-prod` |
| Index | `catalyst` |
| Interval | `900` (15 minutes — increase to `1800` or `3600` for campuses > 5,000 clients to manage API load and license) |

The TA polls `GET /dna/intent/api/v1/client-detail` with pagination. Each connected client produces one JSON event.

Verification:
```spl
index=catalyst sourcetype="cisco:dnac:client" earliest=-30m
| stats dc(macAddress) as unique_clients, count as total_events
| eval events_per_client=round(total_events/unique_clients,1)
```
`unique_clients` should match the total connected client count in **Catalyst Center > Assurance > Health > Client Health > Total**. `events_per_client` should be close to the number of polls in the window (e.g., 2 for a 30-minute window at 900s interval).

If no events arrive, check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for errors. The client detail endpoint is the most resource-intensive API call — HTTP 429 throttling is common with large client populations.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:client"
| stats dc(macAddress) as unique_clients latest(connectionType) as connection by hostType
| sort -unique_clients
```

Why `dc(macAddress)` not `count`: the search window covers multiple poll cycles, so each client produces multiple events. `dc(macAddress)` gives the true unique client count. `count` would show `clients × polls_in_window`.

Why `latest(connectionType)`: a client may switch between wired and wireless during the search window (e.g., a laptop docked in the morning and undocked in the afternoon). `latest()` shows the most recent connection type, which is the current state.

Why `by hostType`: groups by operating system / device type. Catalyst Center classifies clients based on DHCP fingerprinting, HTTP user-agent analysis, and ISE profiling data. The classification accuracy depends on the profiling data available — `Unknown` typically means the device didn't send identifiable DHCP options.

For a current-state snapshot (only actively connected clients), narrow to one poll cycle:
```spl
index=catalyst sourcetype="cisco:dnac:client" earliest=-20m
| stats dc(macAddress) as unique_clients by hostType, connectionType
| sort -unique_clients
```

For fleet growth tracking (monthly capacity planning):
```spl
index=catalyst sourcetype="cisco:dnac:client"
| timechart span=1d dc(macAddress) as daily_clients by hostType
```

This is a report, not an alert. Schedule daily for security review (cron `0 7 * * *`) and monthly for capacity planning (cron `0 7 1 * *`).

### Step 3 — Validate
(a) Compare `unique_clients` total with the client count in **Catalyst Center > Assurance > Health > Client Health > Total Connected Clients**. They should agree within 10% (poll timing and client churn).

(b) Check `hostType` distribution against expectations. A corporate campus typically shows: Windows 50-70%, Mac 10-20%, iOS 10-20%, Android 5-10%, Unknown/Other 5-15%. If Unknown is > 20%, profiling data may be insufficient — check ISE profiling configuration.

(c) Verify `connectionType` ratio: for a typical campus, wireless clients outnumber wired 2:1 to 4:1. If wired dominates, check whether wireless clients are being classified correctly.

(d) Check for MAC randomisation impact: `index=catalyst sourcetype="cisco:dnac:client" | eval is_random=if(tonumber(substr(macAddress,2,1),16) % 4 >= 2, "randomised", "real") | stats dc(macAddress) by is_random`. If `randomised` > 30% of total, consider using `hostName` or `userId` for client counting.

(e) Run the fleet growth timechart over 30 days and compare with HR/facilities headcount data. Significant divergence indicates either undercounting (profiling gaps) or overcounting (MAC randomisation, guest inflation).

### Step 4 — Operationalize
Dashboard placement (as the opening panel on a "Client Population" or "Network Inventory" dashboard):
- Single value tiles: total unique clients, wireless count, wired count.
- Table: hostType | unique_clients | connection — sorted by count.
- Pie chart: client share by hostType for the device mix.
- 30-day growth timechart as a sparkline or full panel.

Security review (weekly, owner: Network Security):
- Check for unexpected `hostType` values (e.g., `Linux` on a Windows-only campus, `Unknown` spikes).
- Cross-reference with asset management: are all counted clients authorised?
- If ISE integration is active (UC-5.13.68), correlate unauthorised clients with ISE posture failures.

Capacity planning (monthly, owner: Network Architecture):
- Track wireless client growth rate. If growing > 10%/quarter, plan AP capacity expansion.
- Track wired port utilisation: `unique_wired_clients / total_wired_ports`. If > 80%, plan switch expansion.
- Track hostType shifts: growing mobile workforce (more iOS/Android) may require additional wireless capacity.

### Step 5 — Troubleshooting

- **Client count much higher than expected** — MAC randomisation is inflating unique MAC counts. iOS and Android devices generate a new random MAC per SSID per day. Solution: use `hostName` or `userId` for accurate headcounts. Or filter to `| eval is_real_mac=if(tonumber(substr(macAddress,2,1),16) % 4 < 2, 1, 0) | where is_real_mac=1`.

- **`hostType` is "Unknown" for most clients** — DHCP fingerprinting or ISE profiling is not providing device classification data. Check ISE profiling policy and ensure DHCP probes are enabled on the WLC.

- **No client events at all** — the `client` detail input is not enabled, or the API is returning empty results. Check TA → Inputs for the Client Detail input. Also check for HTTP 429 throttling — the client detail endpoint is the most expensive API call.

- **Event count is astronomically high** — the `client` input generates one event per client per poll. A campus with 5,000 clients at 900s interval produces ~480,000 events/day. If this is too much for your license, increase the interval to `3600` (hourly) or `7200` (every 2 hours).

- **connectionType shows unexpected values** — some TA versions may report `Wired`/`Wireless` (capitalised) instead of `WIRED`/`WIRELESS` (uppercase). Normalise with `| eval connectionType=upper(connectionType)`.

- **Wired clients show ssid=null** — expected. Wired clients don't have an SSID. Filter to `connectionType="WIRELESS"` for SSID-specific analysis.

- **Guest clients dominate the inventory** — use a `corporate_ssids` lookup to filter: `| lookup corporate_ssids ssid OUTPUT is_corporate | where is_corporate="yes"`.

- **Fleet growth trend shows sudden drop** — possible causes: (a) holiday/break period (expected); (b) AP or WLC outage preventing clients from connecting (check UC-5.13.1); (c) `client` input stopped running (check `index=_internal` for errors).

## SPL

```spl
index=catalyst sourcetype="cisco:dnac:client"
| stats dc(macAddress) as unique_clients latest(connectionType) as connection by hostType
| sort -unique_clients
```

## Visualization

(1) Table: hostType | unique_clients | connection — sorted by client count descending. Drilldown to UC-5.13.12 for per-SSID detail. (2) Pie chart: client share by hostType for the device mix view. (3) Stacked bar: wired vs wireless client count by hostType. (4) Single value tiles: total unique clients, wireless client count, wired client count. (5) Timechart variant: `| timechart span=1d dc(macAddress) by hostType` for fleet growth tracking over 30-90 days.

## Known False Positives

**MAC address randomisation inflating unique client counts.** iOS 14+, Android 10+, and Windows 11 randomise MAC addresses per SSID, making the same physical device appear as multiple unique clients. Distinguish by checking for locally-administered MACs (second hex digit is 2, 6, A, or E). Suppress by using `hostName` or `userId` (if available from ISE integration) as the client identifier instead of `macAddress` for accurate headcounts.

**Printer/IoT devices classified as unknown hostType.** Printers, IP phones, and IoT devices may not report an identifiable OS fingerprint, appearing as `Unknown` or empty hostType. Distinguish by checking whether the MACs belong to known vendor OUIs (Zebra, HP, Polycom). Suppress by maintaining a `known_iot_devices` lookup that maps MAC prefix to device type.

**Guest clients inflating total counts.** A campus with open guest Wi-Fi may see hundreds of transient guest devices that aren't part of the managed fleet. Distinguish by filtering to corporate SSIDs using `| where ssid IN ("Corp","Corporate","Secure")` or a `corporate_ssids` lookup. Present guest and corporate inventories separately.

**Historical clients appearing in inventory.** The search window may include clients that connected once and haven't been seen since. For a current-state inventory, narrow to `earliest=-1h` to show only actively connected clients.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Client Detail endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-client-detail)
- [Catalyst Center Integration Guide (this repo)](docs/guides/catalyst-center.md)
- [Catalyst Center Integration Guide — Capacity Planning](docs/guides/catalyst-center.md#sizing)
