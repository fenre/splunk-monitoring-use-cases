<!-- AUTO-GENERATED from UC-5.8.13.json — DO NOT EDIT -->

---
id: "5.8.13"
title: "Network Device Inventory and Change Audit (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.13 · Network Device Inventory and Change Audit (Meraki)

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Configuration

*We keep an inventory and change feel for Meraki hardware and settings so large moves do not get lost in the day-to-day noise.*

---

## Description

Maintains accurate inventory of network devices and tracks hardware/software changes.

## Value

Network operations teams maintain a real-time Meraki device inventory with change audit trail, tracking device additions, removals, moves, and configuration changes across all networks for operational awareness and compliance.

## Implementation

1. Enable the Devices and Audit inputs in Splunk_TA_cisco_meraki. 2. The Devices input gives current inventory grouped by productType (wireless/switch/appliance/camera/sensor/cellularGateway) and model. 3. The Audit input emits one event per configuration change with adminName, page, label, action (add/remove/update), networkName, ts. 4. To detect device additions/removals specifically, filter page='Inventory' or page='Devices'. 5. Schedule a daily report comparing current inventory against the previous snapshot stored in a summary index for delta tracking.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices input (sourcetype=meraki:devices) for inventory, and Audit input (sourcetype=meraki:audit, daily) for organization configuration changes..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Devices and Audit inputs in Splunk_TA_cisco_meraki. 2. The Devices input gives current inventory grouped by productType (wireless/switch/appliance/camera/sensor/cellularGateway) and model. 3. The Audit input emits one event per configuration change with adminName, page, label, action (add/remove/update), networkName, ts. 4. To detect device additions/removals specifically, filter page='Inventory' or page='Devices'. 5. Schedule a daily report comparing current inventory against the …

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:devices" earliest=-1d
| stats dc(serial) as inventory_count
         by productType, model, networkId
| append [
    search index=meraki sourcetype="meraki:audit" earliest=-7d
        (action="add" OR action="remove" OR action="update")
    | stats count as change_events,
            values(adminName) as changed_by,
            values(label) as targets
             by networkName, page
    | sort - change_events
  ]
| sort productType model
```

#### Understanding this SPL

**Network Device Inventory and Change Audit (Meraki)** — Network operations teams maintain a real-time Meraki device inventory with change audit trail, tracking device additions, removals, moves, and configuration changes across all networks for operational awareness and compliance.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Devices input (sourcetype=meraki:devices) for inventory, and Audit input (sourcetype=meraki:audit, daily) for organization configuration changes. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:devices. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:devices", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by productType, model, networkId** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Appends rows from a subsearch with `append`.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Inventory summary table; device count by type pie chart; change log timeline.

## SPL

```spl
index=meraki sourcetype="meraki:devices" earliest=-1d
| stats dc(serial) as inventory_count
         by productType, model, networkId
| append [
    search index=meraki sourcetype="meraki:audit" earliest=-7d
        (action="add" OR action="remove" OR action="update")
    | stats count as change_events,
            values(adminName) as changed_by,
            values(label) as targets
             by networkName, page
    | sort - change_events
  ]
| sort productType model
```

## Visualization

Inventory summary table; device count by type pie chart; change log timeline.

## Known False Positives

Inventory pulls during hardware refresh or RMAs may spike changes; use baselines and change records before treating as unknown gear.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
