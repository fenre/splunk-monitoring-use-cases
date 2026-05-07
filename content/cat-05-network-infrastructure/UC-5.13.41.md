<!-- AUTO-GENERATED from UC-5.13.41.json — DO NOT EDIT -->

---
id: "5.13.41"
title: "Client Distribution by Type (Wired/Wireless/Guest)"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.41 · Client Distribution by Type (Wired/Wireless/Guest)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Inventory, Capacity &middot; **Wave:** Walk &middot; **Status:** Verified

*We sort everyone on the network into groups — office workers on cable, office workers on Wi-Fi, visitors on the guest network, and smart devices like cameras and sensors. This tells your team how many people and things are using each part of the network, so they can plan for growth and make sure each group gets the right amount of bandwidth.*

---

## Description

Segments the client population into operational categories — corporate wired, corporate wireless, guest wireless, IoT wireless — and shows client distribution per SSID, enabling capacity planning decisions about AP density, guest network sizing, and IoT segment isolation.

## Value

A campus with 60% wireless and growing needs more APs next year. A campus with 40% on the guest SSID needs better guest network isolation and rate limiting. A campus with 15% IoT devices on the corporate SSID has a security segmentation gap. This UC turns the raw client inventory from UC-5.13.40 into actionable capacity and security intelligence by classifying clients into segments that map to your network design decisions — different SSIDs, different VLANs, different QoS policies, different budget lines.

## Implementation

Same `client` detail input as UC-5.13.40. The SSID-to-segment classification uses regex pattern matching — customise the `match()` patterns to match your actual SSID naming conventions. For more precise classification, maintain a `ssid_classification` lookup.

## Detailed Implementation

### Prerequisites
- UC-5.13.40 (Client Inventory) should be operational — same `client` detail input.
- Know your SSID naming convention to build the classification regex. Common patterns:
  - Corporate: `Corp`, `Secure`, `802.1X`, `Enterprise`, company name
  - Guest: `Guest`, `Visitor`, `Open`, `Public`
  - IoT: `IoT`, `Sensor`, `BMS`, `HVAC`, `Camera`
  - Voice: `Voice`, `VoIP`, `Jabber`
- For a lookup-based approach (more maintainable than regex), create `lookups/ssid_classification.csv`:
  ```
  ssid,segment
  CorpSecure,Corporate Wireless
  GuestAccess,Guest Wireless
  IoT-Sensors,IoT Wireless
  ```
  Then replace the `eval case()` with `| lookup ssid_classification ssid OUTPUT segment | eval client_segment=coalesce(segment, if(connectionType="WIRED","Wired","Unknown Wireless"))`.

### Step 1 — Configure data collection
Same `client` detail input as UC-5.13.40. Confirm SSID field is populated for wireless clients:
```spl
index=catalyst sourcetype="cisco:dnac:client" connectionType="WIRELESS" earliest=-30m
| stats dc(ssid) as ssid_count, values(ssid) as ssid_list
```
The SSID list should match the SSIDs configured in your Catalyst Center / WLC deployment.

### Step 2 — Create the search and report
```spl
index=catalyst sourcetype="cisco:dnac:client"
| eval client_segment=case(
    connectionType="WIRED", "Wired",
    match(ssid, "(?i)guest|visitor"), "Guest Wireless",
    match(ssid, "(?i)iot|sensor|device"), "IoT Wireless",
    connectionType="WIRELESS", "Corporate Wireless",
    1==1, "Unknown")
| stats dc(macAddress) as client_count by client_segment, ssid
| sort -client_count
```

Why regex-based classification: the `case()` evaluates top-to-bottom and returns the first match. Wired clients are classified first (no SSID needed). Then guest and IoT SSIDs are matched by name pattern. Everything else wireless defaults to "Corporate Wireless." This is a reasonable starting point but should be replaced with a lookup for production use (see Prerequisites).

Why include `ssid` in the `by` clause: shows the per-SSID breakdown within each segment. A segment with 3 SSIDs reveals the intra-segment distribution (e.g., `CorpSecure` has 2,000 clients while `Corp5GHz` has 500 — the 5 GHz SSID may need promotion via band steering).

For a pure segment-level view (executive summary), remove `ssid` from the `by` clause:
```spl
| stats dc(macAddress) as client_count by client_segment
```

For time-of-day distribution (capacity planning):
```spl
index=catalyst sourcetype="cisco:dnac:client"
| eval client_segment=case(...same as above...)
| timechart span=1h dc(macAddress) as clients by client_segment
```
This shows the daily cycle: wireless peaks during business hours, wired drops after office hours, IoT stays flat 24/7.

### Step 3 — Validate
(a) Sum `client_count` across all segments. It should match UC-5.13.40's total unique clients for the same time window.

(b) Check classification accuracy: `| stats dc(macAddress) by client_segment | sort -dc(macAddress)`. If "Unknown" or "Corporate Wireless" is disproportionately large, SSIDs are not being classified — review the regex patterns against `| stats values(ssid)`.

(c) Cross-reference with **Catalyst Center > Assurance > Health > Client Health** which shows wired vs wireless client counts. The totals should approximately match.

(d) Validate guest segment: check whether the count aligns with guest Wi-Fi usage reports from your WLC or guest management portal.

(e) Validate IoT segment: cross-reference with your asset management system for registered IoT devices.

### Step 4 — Operationalize
Dashboard placement:
- Stacked bar or donut showing the segment mix as the lead panel on a "Client Population" dashboard.
- Table below with per-SSID breakdown.
- 24-hour timechart showing how the mix shifts during the day.

Capacity planning (monthly):
- Track wireless-to-wired ratio trend. Growing wireless share → plan more APs.
- Track guest segment growth. If guest > 30% of wireless → review guest network sizing and rate-limiting policies.
- Track IoT segment growth. If IoT > 10% → review segmentation policies (are IoT devices on their own VLAN/VRF?).

Security review:
- Check for "Unknown" devices — these are potential shadow IT. Cross-reference MAC OUI with known vendor prefixes.
- Check for IoT devices on corporate SSIDs — they should be on the IoT SSID with appropriate ACLs.

### Step 5 — Troubleshooting

- **All wireless clients classified as "Corporate Wireless"** — the regex patterns don't match your SSID names. Run `| stats values(ssid)` and update the `match()` patterns or create a lookup.

- **"Unknown" segment is large** — `connectionType` field has unexpected values. Check `| stats count by connectionType` for variant strings (`wired`/`Wired`/`WIRED`).

- **Guest count seems too high** — MAC randomisation inflates guest counts because guest SSIDs often use open authentication, so devices rotate MACs more aggressively. Use the randomised-MAC filter from UC-5.13.40.

- **Wired and wireless totals don't match UC-5.13.9** — UC-5.13.9 uses the aggregate `clienthealth` feed, while this UC uses per-client data. Different aggregation methods produce different counts.

- **Time-of-day chart shows unexpected patterns** — check timezone alignment between Splunk and Catalyst Center. A 6-hour offset would make business-hour peaks appear at night.

- **Search is slow with large client populations** — narrow the time range to `earliest=-20m` for a snapshot, or use summary indexing for daily/weekly trend views.

- **SSID field is null for some wireless clients** — the client may be in the process of associating (pre-SSID). Filter with `| where isnotnull(ssid)` for clean results.

- **Dual-band SSIDs showing separate counts** — if you have `Corp2.4` and `Corp5` as separate SSIDs, they'll appear as separate rows. Group them using the regex classification to map both to "Corporate Wireless."

Additional operational context for Client Distribution by Type (Wired/Wireless/Guest):

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
index=catalyst sourcetype="cisco:dnac:client"
| eval client_segment=case(
    connectionType="WIRED", "Wired",
    match(ssid, "(?i)guest|visitor"), "Guest Wireless",
    match(ssid, "(?i)iot|sensor|device"), "IoT Wireless",
    connectionType="WIRELESS", "Corporate Wireless",
    1==1, "Unknown")
| stats dc(macAddress) as client_count by client_segment, ssid
| sort -client_count
```

## Visualization

(1) Stacked bar: client_count by client_segment showing the population mix. (2) Table: client_segment | ssid | client_count — top 20, sorted by count. (3) Timechart: `| timechart span=1h dc(macAddress) by client_segment` showing how the mix shifts throughout the day (wireless peaks during business hours, wired drops after 6 PM). (4) Pie chart: client share by segment for executive summaries.

## Known False Positives

**SSID naming convention not matching the classification regex.** If your guest SSID is named `OpenAccess` instead of `Guest`, the `match(ssid, "(?i)guest|visitor")` won't classify it as guest. Distinguish by checking `| stats dc(macAddress) by ssid` for SSIDs that defaulted to "Corporate Wireless" but shouldn't be. Suppress by updating the regex patterns or using a `ssid_classification` lookup.

**MAC randomisation inflating per-segment counts.** iOS and Android devices generate random MACs per SSID, making one physical device appear as multiple unique clients. This inflates wireless segment counts relative to wired. Distinguish by checking the randomised MAC ratio (UC-5.13.40 Step 3). Suppress by using `hostName` or `userId` instead of `macAddress` where available.

**Dual-connected clients counted in both wired and wireless.** A laptop that is both docked (Ethernet) and connected to Wi-Fi appears in both segments. Distinguish by checking `| stats values(connectionType) by hostName` for clients with both WIRED and WIRELESS entries. Suppress by deduplicating on `hostName` and keeping only the most recent `connectionType`.

**Transient guest clients inflating guest segment.** A 1-hour campus tour produces 50 guest connections that persist in the search window. For point-in-time capacity planning, narrow to `earliest=-20m` to see only currently connected guests.

## References

- [Cisco Catalyst Add-on for Splunk (Splunkbase 7538)](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center Intent API — Client Detail endpoint](https://developer.cisco.com/docs/catalyst-center/#!get-client-detail)
- [Catalyst Center Integration Guide (this repo)](../../docs/guides/catalyst-center.md)
- [Cisco Design Zone — Campus Wireless Design](https://www.cisco.com/c/en/us/solutions/design-zone/networking-design-guides/campus-wired-wireless.html)
