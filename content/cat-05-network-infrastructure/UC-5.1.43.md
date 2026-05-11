<!-- AUTO-GENERATED from UC-5.1.43.json — DO NOT EDIT -->

---
id: "5.1.43"
title: "DHCP Snooping Violations (Meraki MS)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.1.43 · DHCP Snooping Violations (Meraki MS)

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We help you know early when something looks wrong with dhcp snooping violations so the team can act before it grows into a bigger outage.*

---

## Description

Detects unauthorized DHCP servers and spoofing attempts that disrupt network address allocation.

## Value

Security teams detect rogue DHCP servers and DHCP snooping violations on Meraki MS switches, preventing unauthorized DHCP responses that cause IP address conflicts and man-in-the-middle attacks.

## Implementation

1. Configure SC4S for MS syslog and enable DHCP server response blocking in Meraki Dashboard -> Switch -> DHCP servers & ARP. 2. Use rex to extract the rogue DHCP server's MAC and the VLAN id. 3. Trigger an alert on every blocked DHCP response — these are real incidents and should be investigated immediately.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA)..
- Ensure the following data sources are available: SC4S Meraki vendor pack (sourcetype=meraki) receiving Meraki MS switch syslog. Meraki MS DHCP guard emits messages of the form 'Blocked DHCP server response from <mac> on VLAN <id>' as type=events when an unauthorised DHCP server is detected on the access switch..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Configure SC4S for MS syslog and enable DHCP server response blocking in Meraki Dashboard -> Switch -> DHCP servers & ARP. 2. Use rex to extract the rogue DHCP server's MAC and the VLAN id. 3. Trigger an alert on every blocked DHCP response — these are real incidents and should be investigated immediately.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" type=events "Blocked DHCP server response"
    earliest=-24h
| rex "Blocked DHCP server response from (?<server_mac>[0-9A-Fa-f:]+) on VLAN (?<vlan_id>\d+)"
| stats count as block_count,
        values(server_mac) as blocked_servers,
        values(vlan_id) as vlans
         by host
| where block_count > 0
| sort - block_count
```

#### Understanding this SPL

**DHCP Snooping Violations (Meraki MS)** — Security teams detect rogue DHCP servers and DHCP snooping violations on Meraki MS switches, preventing unauthorized DHCP responses that cause IP address conflicts and man-in-the-middle attacks.

Documented **Data sources**: SC4S Meraki vendor pack (sourcetype=meraki) receiving Meraki MS switch syslog. Meraki MS DHCP guard emits messages of the form 'Blocked DHCP server response from <mac> on VLAN <id>' as type=events when an unauthorised DHCP server is detected on the access switch. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts fields with `rex` (regular expression).
- `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where block_count > 0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of violations; timeline of events; affected port details.

## SPL

```spl
index=meraki sourcetype="meraki" type=events "Blocked DHCP server response"
    earliest=-24h
| rex "Blocked DHCP server response from (?<server_mac>[0-9A-Fa-f:]+) on VLAN (?<vlan_id>\d+)"
| stats count as block_count,
        values(server_mac) as blocked_servers,
        values(vlan_id) as vlans
         by host
| where block_count > 0
| sort - block_count
```

## Visualization

Table of violations; timeline of events; affected port details.

## Known False Positives

New VoIP, cameras, and docked laptops may appear on the wrong access VLAN until you update trusted ports and DHCP helpers.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
