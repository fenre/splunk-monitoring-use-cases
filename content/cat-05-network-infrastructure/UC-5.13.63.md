<!-- AUTO-GENERATED from UC-5.13.63.json — DO NOT EDIT -->

---
id: "5.13.63"
title: "Wireless Client Experience Score by SSID"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.13.63 · Wireless Client Experience Score by SSID

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We calculate a single quality score for each wireless network by combining signal strength, signal quality, and overall health into one number. This makes it easy to see which Wi-Fi network gives the best experience and which one needs improvement — without needing to understand all the technical details.*

---

## Description

Computes a comprehensive wireless client experience score per SSID by combining Assurance health scores, signal strength (RSSI), and signal quality (SNR) into a single weighted metric — providing a more nuanced view than UC-5.13.12's basic health percentage, and directly answering 'which SSID has the worst user experience?'

## Value

UC-5.13.12 shows health percentage per SSID but doesn't weight signal quality. An SSID can show 80% healthy clients while every connected client has RSSI -78 dBm — technically functional but practically miserable for voice and video. This composite experience score weights three factors: (1) Assurance health score (40%) — the platform's AI-computed assessment; (2) RSSI (30%) — raw signal strength; (3) SNR (30%) — signal quality relative to noise. The result is a single number per SSID that correlates more closely with actual user experience than any individual metric alone.

## Implementation

Same `client` detail input as UC-5.13.40. Requires `healthScore{}.score`, `rssi`, and `snr` fields populated for wireless clients. The experience formula weights health, RSSI, and SNR; adjust weights based on your network's priorities (voice-heavy → increase SNR weight).

## Detailed Implementation

### Prerequisites
- UC-5.13.40 (Client Inventory) and UC-5.13.42 (RSSI/SNR) must be operational — same `client` detail input.
- The `healthScore{}.score`, `rssi`, and `snr` fields must all be populated for wireless clients. Verify: `| fieldsummary | search field IN ("rssi","snr") | where count > 0`.
- The experience formula is a weighted composite: `health*0.4 + (100+rssi)*0.3 + snr*4*0.3`. The RSSI transformation `(100+rssi)` converts negative dBm (-30 to -90) to a 0–70 scale. The SNR multiplication `snr*4` normalises 0–25 dB to a 0–100 scale. Adjust weights based on your priorities.

### Step 1 — Configure data collection
Same `client` detail input as UC-5.13.40. No additional configuration.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS"
| stats avg(healthScore{}.score) as avg_health avg(rssi) as avg_rssi avg(snr) as avg_snr dc(macAddress) as client_count count(eval(healthScore{}.score<50)) as poor_clients by ssid
| eval experience=round((avg_health*0.4 + (100+avg_rssi)*0.3 + avg_snr*0.3*4),1)
| eval experience=if(experience>100,100,experience)
| sort experience
```

Why a composite score: no single metric captures the full wireless experience. Health score misses signal quality. RSSI misses interference. SNR misses client-side issues. The composite weighs all three and produces a score that correlates with actual user-perceived quality.

Why these weights (40/30/30): health score gets the highest weight because Assurance's AI considers many factors beyond RF. RSSI and SNR get equal weight because signal strength and quality are equally important for real-time applications. Adjust: for voice-heavy environments, increase SNR weight to 40% and reduce health to 30%.

Why `experience=if(experience>100,100,experience)`: caps the score at 100 to prevent APs with exceptionally strong signal from producing scores > 100.

For per-SSID experience trending:
```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS"
| eval exp_raw=healthScore{}.score*0.4 + (100+rssi)*0.3 + snr*0.3*4
| eval experience=if(exp_raw>100,100,exp_raw)
| timechart span=1h avg(experience) by ssid
```

Schedule: daily for the wireless performance review.

### Step 3 — Validate
(a) The SSID with the highest experience score should be the one with the best-perceived Wi-Fi quality (typically the corporate SSID in well-designed areas).
(b) Cross-reference: the SSID with the lowest experience score should correlate with the most help-desk complaints.
(c) Compare individual components: if `avg_health` is high but `avg_rssi` is very low, the experience score correctly pulls down an SSID that Assurance considers healthy but has poor signal coverage.
(d) Compare with UC-5.13.12 (Client Health by SSID): the ranking should be similar but not identical — the experience score adds RF dimensions.

### Step 4 — Operationalize
- Wireless team weekly review: which SSIDs have the worst experience?
- Before/after analysis: compute experience score before and after a wireless change (AP addition, channel optimisation, band-steering policy) to measure impact.
- SLA tracking: define a minimum experience score per SSID type (corporate ≥ 70, guest ≥ 50, IoT ≥ 30).

Runbook (owner: Wireless Engineering):
1. Review the per-SSID experience scores.
2. For the lowest-scoring corporate SSID: drill into the component scores:
   - Low health → check UC-5.13.11 for root cause.
   - Low RSSI → check UC-5.13.42 for coverage gaps.
   - Low SNR → check UC-5.13.62 for channel utilisation/interference.
3. For consistently low-scoring SSIDs: review the wireless design (AP placement, channel width, band-steering policy) for that SSID.
4. Track experience improvement after each change.

### Step 5 — Troubleshooting

- **Experience score is always null** — one or more component fields are not populated. Check `| fieldsummary | search field IN ("rssi","snr","healthScore{}.score")`.

- **All SSIDs show similar scores** — the campus may have uniform wireless quality (good). Or the formula weights may need adjustment for your environment.

- **Experience score doesn't match user complaints** — the formula may not capture the specific issue. Add `onboardingTime` or `dataRate` as additional factors if available.

- **IoT SSID scores much lower than corporate** — expected. Compare within SSID categories.

- **Score fluctuates widely between polls** — low client count. Filter `| where client_count >= 10`.

- **5 GHz SSID scores lower than 2.4 GHz** — the RSSI component penalises 5 GHz (lower RSSI at same distance). Consider per-band normalisation.

- **Search is slow** — the `client` sourcetype is high-volume. Narrow to `earliest=-20m` for a snapshot.

- **Want to weight by client count** — use `| eval weighted_exp=experience*client_count` for a volume-weighted metric that prioritises SSIDs serving more users.

Additional operational context for Wireless Client Experience Score by SSID:

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
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS"
| stats avg(healthScore{}.score) as avg_health avg(rssi) as avg_rssi avg(snr) as avg_snr dc(macAddress) as client_count count(eval(healthScore{}.score<50)) as poor_clients by ssid
| eval experience=round((avg_health*0.4 + (100+avg_rssi)*0.3 + avg_snr*0.3*4),1)
| eval experience=if(experience>100,100,experience)
| sort experience
```

## Visualization

(1) Table: ssid, experience, avg_health, avg_rssi, avg_snr, client_count, poor_clients — sorted by experience ascending (worst first). (2) Bar chart: experience score by SSID (colour-coded: green > 70, yellow 50–70, red < 50). (3) Radar chart: per-SSID comparison across health, RSSI, SNR dimensions. (4) Timechart: `| timechart span=1h avg(experience) by ssid` for experience trending.

## Known False Positives

**IoT SSIDs with inherently lower experience scores.** IoT devices have weaker radios and simpler wireless capabilities, producing lower RSSI and health scores. Distinguish by checking the SSID name against IoT naming conventions. Suppress by comparing within SSID categories (corporate vs guest vs IoT) rather than across all SSIDs.

**Guest SSIDs with diverse client device quality.** Guest networks serve a wide range of device ages and capabilities, pulling down average scores. Distinguish by checking `client_count` and `hostType` distribution. Present guest and corporate SSIDs in separate comparisons.

**Low client count producing volatile scores.** An SSID with 2 connected clients produces unreliable averages. Distinguish by checking `client_count`. Suppress by filtering `| where client_count >= 10` for meaningful comparison.

**RSSI component dominated by 5 GHz clients.** 5 GHz RSSI is naturally lower than 2.4 GHz. An SSID serving mostly 5 GHz clients will have a lower RSSI-component than one serving mostly 2.4 GHz clients, even with identical coverage. Consider computing the experience score per-band rather than per-SSID.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Client Detail endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-client-detail)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [Cisco Wireless Client Experience — Design Best Practices](https://www.cisco.com/c/en/us/solutions/design-zone/networking-design-guides/campus-wired-wireless.html)
