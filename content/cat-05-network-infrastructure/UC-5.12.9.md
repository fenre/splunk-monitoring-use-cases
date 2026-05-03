<!-- AUTO-GENERATED from UC-5.12.9.json — DO NOT EDIT -->

---
id: "5.12.9"
title: "Roaming Usage Anomaly"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.12.9 · Roaming Usage Anomaly

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Fraud, Revenue Assurance

*We help you flag odd roaming or premium usage before an invoice or fraud team finds it first—especially when a SIM or plan should stay home.*

---

## Description

Sudden data/voice roaming volume from HLR/VLR or TAP records may indicate SIM box, cloned IMSI, or billing leakage.

## Value

Fraud and revenue assurance teams detect SIM box operations, SIM cloning, and anomalous roaming patterns using statistical analysis of TAP/usage data, protecting interconnect revenue and subscriber security.

## Implementation

Privacy: only hashed IMSI in Splunk; correlate with HLR IMEI change for SIM swap fraud.

## Detailed Implementation

### Prerequisites
- Roaming usage data in `index=telco` from: (a) TAP (Transferred Account Procedure) files in TD.35 format from roaming clearinghouses (BICS, Syniverse, etc.) parsed into `sourcetype=tap:cdr`; (b) aggregated roaming usage records from the HLR/HSS or billing mediation system into `sourcetype=roaming:usage`.
- Key fields: `imsi_hash` (HMAC of IMSI for privacy — never store raw IMSI in Splunk), `visited_country` (MCC or country name), `visited_plmn` (MCC-MNC of the visited network), `charge_units` (usage units — minutes, MB, SMS count), `charge_amount` (monetary value in settlement currency), `service_type` (voice/data/sms), `event_timestamp`.
- Privacy requirement: IMSI and MSISDN are personal identifiers under GDPR and most telecom regulations. Use HMAC (with a key stored in KMS) to create `imsi_hash` — this allows correlation across events without storing the raw identifier. Only the fraud team with access to the HMAC key can reverse-map to the actual subscriber.
- Build a `mcc_country.csv` lookup mapping MCC codes to country names and risk tiers (low/medium/high/premium). High-risk countries for telecom fraud: countries with premium-rate interconnect, SIM box hubs (parts of Africa, South Asia), and countries with weak fraud controls.
- Understand normal roaming patterns: your subscriber base has predictable roaming patterns based on geography, tourism seasons, and business travel. Scandinavian carriers see heavy roaming to Spain/Greece in summer and to alpine countries in winter. Establish these baselines by month.

### Step 1 — Configure data collection
Verify roaming data:
```spl
index=telco sourcetype="roaming:usage" earliest=-7d
| stats count dc(imsi_hash) as unique_subscribers dc(visited_country) as countries sum(charge_amount) as total_revenue by service_type
```
You should see voice, data, and SMS service types with subscriber counts across visited countries. If the count is zero, check TAP file delivery from your clearinghouse.

Establish roaming baselines by country:
```spl
index=telco sourcetype="roaming:usage" earliest=-90d
| bin _time span=1d
| stats sum(charge_units) as daily_units dc(imsi_hash) as daily_subs sum(charge_amount) as daily_rev by visited_country, _time
| stats avg(daily_units) as avg_units stdev(daily_units) as std_units avg(daily_subs) as avg_subs avg(daily_rev) as avg_rev by visited_country
| eval anomaly_threshold=avg_units + (5 * std_units)
```

### Step 2 — Create the search and alert

**Primary search — Subscriber-level roaming anomaly (daily):**
```spl
index=telco sourcetype="roaming:usage" earliest=-24h
| stats sum(charge_units) as units sum(charge_amount) as rev dc(visited_country) as countries values(visited_country) as visited_list values(service_type) as services by imsi_hash
| eventstats avg(units) as fleet_avg_units stdev(units) as fleet_std_units
| eval z_score=round((units - fleet_avg_units) / fleet_std_units, 1)
| where z_score > 5 OR units > 10 * fleet_avg_units OR countries > 3
| eval anomaly_type=case(countries > 3, "Multi-country (impossible travel?)", units > 10 * fleet_avg_units, "Extreme usage (SIM box?)", z_score > 5, "Statistical outlier")
| sort -units
```

#### Understanding this SPL: We detect three anomaly patterns: (1) A subscriber active in >3 countries in 24 hours suggests SIM cloning or impossible travel. (2) Usage exceeding 10x the fleet average suggests a SIM box operation (a device that routes international calls through local SIMs to avoid interconnect charges). (3) Statistical outliers (z-score > 5) catch unusual patterns that don't fit the first two categories. The `imsi_hash` preserves privacy while enabling correlation.

**Country-level anomaly — sudden roaming traffic spike:**
```spl
index=telco sourcetype="roaming:usage" earliest=-7d
| bin _time span=1d
| stats sum(charge_units) as units sum(charge_amount) as rev dc(imsi_hash) as subscribers by visited_country, _time
| eventstats avg(units) as avg_units by visited_country
| where _time >= relative_time(now(), "-1d@d")
| eval spike_ratio=round(units/avg_units, 1)
| where spike_ratio > 3 OR (subscribers > 100 AND spike_ratio > 2)
| lookup mcc_country.csv visited_country OUTPUT risk_tier
| sort -spike_ratio
```

#### Understanding this SPL: Detects daily roaming traffic spikes by country. A 3x spike could indicate a major event (sports championship, conference), a new roaming agreement driving increased usage, or a fraud ring operating in that country. The risk_tier from the country lookup adds context — a spike to a high-risk country warrants faster investigation.

**IMEI change detection (SIM swap/clone indicator):**
```spl
index=telco sourcetype="roaming:usage" earliest=-7d
| stats dc(imei_hash) as unique_devices values(visited_country) as countries values(imei_hash) as devices by imsi_hash
| where unique_devices > 2
| eval risk=case(unique_devices > 5, "HIGH - possible SIM cloning", unique_devices > 2, "MEDIUM - device change", 1==1, "LOW")
| sort -unique_devices
```

#### Understanding this SPL: A single IMSI appearing on multiple IMEIs (devices) is a strong indicator of SIM cloning. Legitimate reasons exist (subscriber changing phones), but >2 devices in a week, especially across different countries, warrants investigation.

Schedule as Alert: subscriber anomaly runs daily at 06:00. Country anomaly runs daily. IMEI change runs weekly.

### Step 3 — Validate
(a) Cross-reference a flagged subscriber's roaming usage with the billing system. Verify the charge amounts match.
(b) Check a known roaming subscriber (test SIM on a roaming trip) and verify their usage appears correctly.
(c) Validate the country baseline: compare Splunk roaming revenue by country to the monthly roaming settlement report from your clearinghouse.
(d) Verify HMAC consistency: confirm the same IMSI always produces the same hash across data sources.

### Step 4 — Operationalize
Dashboard ("Telecom - Roaming Analytics & Fraud"):
- Row 1 — Single-value tiles: "Roaming subscribers (24h)", "Roaming revenue (24h)", "Anomalous subscribers", "Countries with traffic spikes".
- Row 2 — Map: visited countries sized by subscriber count, colored by spike ratio.
- Row 3 — Anomalous subscriber table: imsi_hash, anomaly type, units, revenue, visited countries, risk level.
- Row 4 — Country-level trend: daily roaming revenue by top 10 countries over 30 days.

Alerting:
- Fraud (subscriber with impossible travel or >10x usage): immediate alert to fraud team with imsi_hash, visited countries, and usage details.
- Revenue (country spike > 5x): alert to roaming operations for investigation.
- IMEI change (>3 devices on one IMSI in 7 days): alert to fraud team for SIM clone investigation.

Runbook (owner: Fraud / Roaming Operations):
1. **SIM box detection**: Contact the visited network's fraud team via the roaming agreement contact. Provide the imsi_hash, visited country, and usage pattern. Request the subscriber's location data from the visited network to confirm the SIM box location.
2. **SIM clone/impossible travel**: Immediately suspend the affected IMSI at the HLR. Contact the subscriber to verify their SIM is in their possession. Issue a new SIM if cloning is confirmed.
3. **Country-level roaming spike**: Verify with the roaming clearinghouse that the TAP data is accurate. Check for a known event in that country. If fraud is suspected, implement temporary roaming barring for new activations to that country.

### Step 5 — Troubleshooting

- **TAP file data is delayed by days** — TAP files from roaming clearinghouses typically arrive 24-48 hours after the roaming event. For near-real-time detection, use NRTRDE (Near Real-Time Roaming Data Exchange) feeds if your clearinghouse supports them. Alternatively, use HLR/HSS location update events for real-time roaming detection (at the cost of less detailed usage data).

- **`imsi_hash` doesn't correlate across data sources** — Ensure the same HMAC key and algorithm is used across all systems that hash the IMSI. Different hashing methods will produce different hashes for the same IMSI.

- **False positives from border areas** — Subscribers near country borders may roam into neighboring countries unintentionally (e.g. Norway/Sweden border). This creates multi-country patterns that are legitimate. Use a `border_regions.csv` lookup to exclude known border areas from impossible travel detection.

- **Charge amounts don't match billing** — TAP data uses wholesale IOT (Inter-Operator Tariff) rates, while billing uses retail rates. These will never match exactly. Compare at the CDR count level rather than revenue level for validation.

## SPL

```spl
index=telco sourcetype="roaming:usage"
| bin _time span=1d
| stats sum(charge_units) as units, sum(charge_amount) as rev by imsi_hash, visited_country, _time
| eventstats avg(units) as baseline by visited_country
| where units > 10*baseline
| sort -units
```

## Visualization

Map (visited countries), Table (suspicious subscribers), Line chart (roaming $ trend).

## Known False Positives

Border handovers, ferry routes, and mis-tagged MCC in partner feeds can look like false roaming; brief drops during gateway failovers and trunk maintenance can also add noise.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
