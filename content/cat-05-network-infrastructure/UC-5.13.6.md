<!-- AUTO-GENERATED from UC-5.13.6.json — DO NOT EDIT -->

---
id: "5.13.6"
title: "Device Reachability Loss Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.13.6 · Device Reachability Loss Detection

## Description

Identifies devices that Catalyst Center can no longer reach, indicating potential hardware failure, network partition, or misconfiguration.

## Value

Unreachable devices represent the most severe health state — they may be completely down. Rapid detection reduces outage duration and blast radius.

## Implementation

Requires UC-5.13.3 alerting in place. Filter specifically on `reachabilityHealth="Unreachable"` and schedule frequently (for example every 5–15 minutes) with P1-style routing. Confirm Catalyst Center and Splunk time zones align so `duration_min` matches operator expectations.

## Detailed Implementation

Prerequisites
• **UC-5.13.3** baselines in place; this UC **narrows** to **`reachabilityHealth="Unreachable"`** only (management-plane loss from Catalyst Center’s view).
• Cisco Catalyst Add-on (7538), **devicehealth** → `cisco:dnac:devicehealth` on `index=catalyst`.
• **Time alignment:** use **same timezone** in Splunk and Catalyst Center operators’ consoles; **`duration_min`** is based on event **`_time`** in the search window.
• See `docs/implementation-guide.md`.

Step 1 — Configure data collection
• **Intent API:** `GET /dna/intent/api/v1/device-health`; **`reachabilityHealth`** is typically **`Reachable`** or **`Unreachable`** (exact strings—**verify in raw** JSON).
• **TA input:** **devicehealth**; poll **every 5–15 minutes** for this use case if you can sustain API load—unreachability is **P1**-class for many teams.
• **Prerequisite:** if **`reachabilityHealth`** is often blank for some platforms, document product-specific behavior and do not **page** on those until fields are reliable.

Step 2 — Create the search and alert
```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" reachabilityHealth="Unreachable" | stats count as unreachable_count earliest(_time) as first_unreachable latest(_time) as last_seen by deviceName, managementIpAddress, deviceType, siteId | eval duration_min=round((last_seen-first_unreachable)/60,0) | sort -duration_min
```

Understanding this SPL
• **Implicit filter** on **`reachabilityHealth="Unreachable"`**—if your build uses a different token, **adjust** the literal.
• **`earliest`/`latest`** in the `stats` bracket **unreachable** samples in the chosen window; **`duration_min`** is a **rough** session length, not a full ICMP history.
• **Sort** by **`-duration_min`** emphasizes **sustained** unreachability; pair with a **“first seen”** window filter to suppress **one-poll** blips if needed.

**Pipeline walkthrough**
• **Search-time** filter (or `where`) for **unreachable** rows.
• **Per-device** `stats` for **count** and time span; **`eval`** for minutes.

Step 3 — Validate
• Put a test device in **isolated** management failure (lab) and confirm **Unreachable** in **Catalyst** **Assurance** and the same in Splunk within **two** polls.
• Compare **duration** to **tickets**—if **duration_min** is always **0**, your window may be too **narrow** or only one event exists per device.
• **Join** to **UC-5.13.1** **overallHealth** in a **subsearch** to see if **unreachable** correlates with **null** or **0** health.

Step 4 — Operationalize (alerting)
• **Schedule:** **5–15 min**; **time range** **Last 15–30 min** with overlap to **miss** no polls.
• **Route:** **P1**-style for **production** `siteId`; **throttle** per **device**; **suppression** during **change** **windows** (lookup of **expected** work).
• **Ticket body:** `deviceName`, `managementIpAddress`, `siteId`, **`duration_min`**, **link** to **Device 360** in **Catalyst Center**.

Step 5 — Troubleshooting
• **False unreachability:** **routing** to the **management** **VLAN**; **co-boxed** **firewall** rule; path asymmetry to the controller.
• **Flapping between Reachable/Unreachable:** check **Catalyst** **issues** and **infrastructure** changes before assuming hardware—may be **vPC/HSRP** work or **transient** path loss.
• **User impact unclear:** this UC is **management** **reachability** from **Catalyst Center**—validate **data** plane with **separate** tests if users report outages while the device still “works” in **Assurance** for **data** only.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:devicehealth" reachabilityHealth="Unreachable" | stats count as unreachable_count earliest(_time) as first_unreachable latest(_time) as last_seen by deviceName, managementIpAddress, deviceType, siteId | eval duration_min=round((last_seen-first_unreachable)/60,0) | sort -duration_min
```

## Visualization

Table of unreachable devices with duration, timeline panel of first to last event, link-out to IP management or CMDB.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Integration Guide](docs/guides/catalyst-center.md)
