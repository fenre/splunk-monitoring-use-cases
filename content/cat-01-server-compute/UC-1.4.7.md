<!-- AUTO-GENERATED from UC-1.4.7.json — DO NOT EDIT -->

---
id: "1.4.7"
title: "BMC Out-of-Band Connectivity Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.4.7 · BMC Out-of-Band Connectivity Health

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability

*We check that the server’s “remote control” path over the management network is still there, so you are not caught unable to turn a machine on or fix it from afar when something goes wrong in the data hall.*

---

## Description

BMC (IPMI/iDRAC/iLO) loss prevents remote power, console, and sensor access. Early detection ensures out-of-band management remains available for recovery.

## Value

If the out-of-band path is down, you may not be able to power-cycle or re-image a box during an outage, so you want to know before the next time you are counting on that remote “lights-out” access.

## Implementation

Create scripted input: `ipmitool lan print` or vendor-specific tools (racadm, hpasm) to verify BMC reachability and LAN channel. Run every 5 minutes. Alert when BMC becomes unreachable.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: Custom scripted input, IPMI.
- Ensure the following data sources are available: `ipmitool lan print`, BMC health sensors, SNMP (if BMC supports it).
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
From a host or bastion, run `ipmitool lan print` (or vendor CLI) to capture link state and channel information; schedule every 5 minutes. If you use SNMP to the BMC, map `link` and any voltage/health into the same or related sourcetype. Alert when the management path is not usable.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust thresholds to your field names):

```spl
index=hardware sourcetype=bmc_health host=*
| stats latest(channel_voltage) as voltage, latest(link_detected) as link by host
| where link="no" OR voltage < 3.0
| table host link voltage _time
```

#### Understanding this SPL

**BMC Out-of-Band Connectivity Health** — BMC (IPMI/iDRAC/iLO) loss prevents remote power, console, and sensor access. Early detection ensures out-of-band management remains available for recovery.

**Pipeline walkthrough**

- Scopes the data: `index=hardware`, `sourcetype=bmc_health`.
- `stats` takes the latest `link` and `voltage` per **host**.
- `where` and `table` list suspect hosts and recent samples.


### Step 3 — Validate
Compare one host’s `ipmitool lan print` output to your indexed `link` and `voltage`. For full details, see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=hardware sourcetype=bmc_health host=*
| stats latest(channel_voltage) as voltage, latest(link_detected) as link by host
| where link="no" OR voltage < 3.0
| table host link voltage _time
```

## CIM SPL

```spl
N/A — management-network link and BMC health fields are not a CIM data model; use a custom `bmc_health` sourcetype (from `ipmitool lan` or Redfish) or vendor SNMP OIDs.
```

## Visualization

Status grid (BMC up/down per host), Table of unreachable BMCs, Single value (count of healthy BMCs).

## Known False Positives

A brief poll failure during a BMC firmware update, switch maintenance, or VLAN change can look like a down link. A machine just powered off has no in-band poll—separate in-band vs. OOB health if you use both. SNMP traps can duplicate syslog events.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
