<!-- AUTO-GENERATED from UC-5.4.5.json — DO NOT EDIT -->

---
id: "5.4.5"
title: "Client Count Trending"
criticality: "low"
splunkPillar: "Observability"
---

# UC-5.4.5 · Client Count Trending

> **Criticality:** Low &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We watch client count trending so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Client count trending informs capacity planning and AP density decisions.

## Value

Network operations teams track wireless client counts per AP against model-specific capacity limits, identifying overloaded access points and generating capacity planning data for building and floor-level wireless density management.

## Implementation

Poll client counts via API or SNMP. Track per AP, per SSID, and per building over time.

## Detailed Implementation

### Prerequisites
- Wireless controller or cloud platform reporting client count per AP. Sources: (1) Cisco WLC — client association data via SNMP or syslog, (2) Meraki API (`sourcetype=meraki:api:devices` or `meraki:api:wireless`) — client count per AP, (3) Aruba controller — client association table.
- Key fields: `ap_name`, `client_count`/`num_clients`, `ssid`, `radio_band`, `max_clients` (AP capacity limit).
- Build `wireless_ap_capacity.csv` lookup: `ap_model,max_clients_per_radio,recommended_max` (e.g., `MR46,128,80`, `AIR-AP3802I,200,120`). Recommended max is typically 60-70% of the hardware limit for good performance.

### Step 1 — Configure data collection
Verify client count data:
```spl
index=wireless earliest=-15m
| where isnotnull(client_count) OR isnotnull(num_clients)
| eval clients=coalesce(client_count, num_clients)
| stats sum(clients) as total_clients dc(ap_name) as active_aps
```

### Step 2 — Create the search and alert

**Primary search — Client count trending with capacity awareness:**
```spl
index=wireless earliest=-1h
| where isnotnull(client_count) OR isnotnull(num_clients)
| eval clients=coalesce(client_count, num_clients)
| stats latest(clients) as current_clients by ap_name, radio_band
| lookup wireless_ap_inventory.csv ap_name OUTPUT building floor zone ap_model
| lookup wireless_ap_capacity.csv ap_model OUTPUT max_clients_per_radio recommended_max
| eval utilization_pct=if(isnotnull(recommended_max), round(100*current_clients/recommended_max, 1), null())
| eval status=case(utilization_pct > 100, "OVERLOADED", utilization_pct > 80, "HIGH", utilization_pct > 60, "ELEVATED", 1==1, "OK")
| where status!="OK"
| eval location=building." / ".floor
| table ap_name, location, radio_band, current_clients, recommended_max, utilization_pct, status
| sort status, -current_clients
```

**Client count per building/floor:**
```spl
index=wireless earliest=-15m
| where isnotnull(client_count) OR isnotnull(num_clients)
| eval clients=coalesce(client_count, num_clients)
| lookup wireless_ap_inventory.csv ap_name OUTPUT building floor
| stats sum(clients) as total_clients dc(ap_name) as ap_count by building, floor
| eval clients_per_ap=round(total_clients/ap_count, 1)
| sort -total_clients
```

**Daily client count trending:**
```spl
index=wireless earliest=-7d
| where isnotnull(client_count) OR isnotnull(num_clients)
| eval clients=coalesce(client_count, num_clients)
| bin _time span=1h
| stats sum(clients) as total_clients by _time
| timechart span=1h avg(total_clients) as "Total Wireless Clients"
```

### Step 3 — Validate
(a) Compare client count on specific APs with the wireless controller dashboard.
(b) During a known event (all-hands meeting), verify the client count spikes on APs near the meeting room.
(c) Verify capacity lookup values against AP model datasheets.

### Step 4 — Operationalize
Dashboard ("Wireless — Client Count"):
- Row 1 — Single-value tiles: "Total wireless clients", "Overloaded APs", "Busiest AP", "Average clients/AP".
- Row 2 — AP capacity table: AP, location, clients, capacity, utilization %, status.
- Row 3 — Building/floor client density.
- Row 4 — 7-day client count trending.

Alerting:
- Critical (AP > 100% of recommended capacity): user experience degradation — add APs.
- Warning (AP > 80% capacity): approaching capacity limit.
- Info (weekly): capacity planning report — buildings approaching limits.

### Step 5 — Troubleshooting

- **Client count on one AP much higher than others** — Sticky clients (devices not roaming to less-loaded APs). Enable client load balancing on the controller. Also check if the AP is near a high-density area (conference room, cafeteria).

- **Total client count drops suddenly** — Controller issue, RADIUS failure, or DHCP pool exhaustion. Correlate with authentication events (UC-5.4.2) and DHCP events (UC-5.6.x).

- **Client count data not available per-AP** — Some platforms report only aggregate counts. Configure per-AP polling via SNMP or ensure the API returns device-level client counts.

## SPL

```spl
index=network sourcetype="meraki:api"
| timechart span=1h dc(client_mac) as client_count by ap_name
```

## Visualization

Line chart (clients over time), Table (AP, count), Heatmap.

## Known False Positives

Wireless client counts spike during shift changes, big events, or back-to-school style rushes; compare against the calendar before calling it an incident.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
