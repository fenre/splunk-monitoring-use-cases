<!-- AUTO-GENERATED from UC-5.20.35.json — DO NOT EDIT -->

---
id: "5.20.35"
title: "SAVI Event Logging and Binding Verification"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.35 · SAVI Event Logging and Binding Verification

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Compliance &middot; **Wave:** Run &middot; **Status:** Verified

*The switch keeps a registration book of every device on the network — when they arrived, when they left, and when they checked in again. We read this registration book to make sure everyone who should be registered actually is, and that no one's registration mysteriously disappeared.*

---

## Description

Monitors SAVI/SISF binding table lifecycle events — creation, deletion, and update of IPv6-to-MAC-to-port bindings — to verify the health and completeness of the first-hop security binding table. The binding table is the foundation of all SISF security features (RA Guard, DHCPv6 Guard, Source Guard, Destination Guard). If the binding table is incomplete (hosts missing), security features may block legitimate traffic. If it is stale (expired entries not cleaned up), the switch wastes memory. If it is churning excessively (rapid creation/deletion cycles), there may be a network instability issue. This use case provides lifecycle visibility to ensure the binding table accurately reflects the active network population.

## Value

The SISF binding table is the single source of truth for IPv6 identity at the access layer. Its accuracy directly impacts both security effectiveness and user experience. An incomplete binding table means Source Guard blocks legitimate hosts. An overly permissive table (stale entries) means deleted devices retain access. Monitoring the binding lifecycle ensures the table is current, complete, and correctly sized. This is especially important for troubleshooting SISF-related connectivity issues — the first question is always 'is the host in the binding table?'

## Implementation

Collect SISF ENTRY_CREATED, ENTRY_DELETED, and ENTRY_UPDATED syslog events. Track binding lifecycle: creation rate, deletion rate, and churn. Alert on anomalies: high churn (instability), excessive deletions (binding table draining), or zero creations on active VLANs (SISF learning disabled).

## Detailed Implementation

### Prerequisites
- SISF in `guard` or `inspect` mode on access switches.
- Syslog forwarding at severity 6 (informational) to capture `%SISF-6-ENTRY_*` events.
- Sufficient syslog pipeline capacity — busy switches may generate hundreds of ENTRY events per minute.

### Step 1 — Configure data collection

SISF binding events are generated automatically. Ensure syslog is forwarded at informational level:
```
logging host <splunk_syslog>
logging trap informational
```

Verify binding table:
```
show device-tracking database
  Network Layer Address     Link Layer Address  Interface  vlan  prlvl  age    state
  2001:db8:100::a           aabb.ccdd.eeff      Gi1/0/5    100   0005   30s    REACHABLE
  FE80::1                   aabb.ccdd.eeff      Gi1/0/5    100   0005   30s    REACHABLE
```

**Verification:**
```spl
index=network sourcetype="cisco:ios" "%SISF-6-ENTRY" earliest=-24h
| stats count by host
```

### Step 2 — Create the search and alert

**Binding lifecycle trending:**
```spl
index=network sourcetype="cisco:ios" "%SISF-6-ENTRY" earliest=-24h
| rex field=_raw "(?<action>CREATED|DELETED|UPDATED)"
| timechart span=1h count by action
```

**Binding completeness check (compare bindings vs known hosts):**
```spl
index=network sourcetype="cisco:ios" "%SISF-6-ENTRY_CREATED" earliest=-24h
| rex field=_raw "MAC=(?<mac_addr>[0-9a-fA-F.]+)"
| rex field=_raw "(?:vlan|VLAN)\s*(?<vlan>\d+)"
| stats dc(mac_addr) as bound_macs by host, vlan
| lookup expected_host_count.csv host, vlan OUTPUT expected_count
| eval coverage_pct=round(bound_macs / expected_count * 100, 1)
| where coverage_pct < 80
| eval alert="SISF binding coverage low: " . coverage_pct . "% on VLAN " . vlan
```

**Alert — binding table draining:**
```spl
index=network sourcetype="cisco:ios" "%SISF-6-ENTRY" earliest=-1h
| rex field=_raw "(?<action>CREATED|DELETED)"
| stats count(eval(action="CREATED")) as creates count(eval(action="DELETED")) as deletes by host
| where deletes > creates * 3 AND deletes > 50
```
Trigger: binding deletions outpace creations 3:1 — the binding table is draining, which may disable Source Guard protection.

### Step 3 — Validate
(a) **Connect a new host.** Verify ENTRY_CREATED appears in Splunk within 30 seconds.
(b) **Disconnect a host.** Verify ENTRY_DELETED appears after the reachable-lifetime expires.
(c) **Privacy extension rotation.** On a host with privacy extensions, observe the create/delete cycle for temporary addresses over 24 hours.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — SISF Binding Table Health"):
- Row 1 — Single-value: total active bindings, binding churn rate (creates+deletes per hour).
- Row 2 — Timechart: CREATED vs DELETED vs UPDATED over 24 hours — should be roughly balanced.
- Row 3 — Per-VLAN binding coverage: bound MACs vs expected host count.

**Scheduling:** Binding lifecycle trending hourly. Binding coverage check daily.

**Runbook:**
1. Binding table draining: check if reachable-lifetime is too short (`show device-tracking policy`). Increase if needed.
2. Low coverage on a VLAN: check if SISF learning is enabled. Some ports may be in `glean` mode (learns but doesn't enforce) or SISF may not be attached.

### Step 5 — Troubleshooting

- **No ENTRY events** — SISF is not in a mode that generates events. Check `show device-tracking policy` — `Logging: ENABLED` must be set.

- **Excessive ENTRY_UPDATED events** — Each NDP NS/NA exchange refreshes the binding, generating an UPDATE event. On busy VLANs, this can produce very high event volumes. Consider filtering UPDATED events from the alert search and focusing on CREATED/DELETED for lifecycle analysis.

## SPL

```spl
index=network sourcetype="cisco:ios" "%SISF-6-ENTRY" earliest=-24h
| rex field=_raw "(?<action>CREATED|DELETED|UPDATED)"
| rex field=_raw "IP=(?<ipv6_addr>[0-9a-fA-F:.]+)"
| rex field=_raw "MAC=(?<mac_addr>[0-9a-fA-F.]+)"
| rex field=_raw "(?:port|Port)\s*=?\s*(?<port>\S+)"
| rex field=_raw "(?:vlan|VLAN)\s*(?<vlan>\d+)"
| stats count as events count(eval(action="CREATED")) as created count(eval(action="DELETED")) as deleted count(eval(action="UPDATED")) as updated by host, vlan
| eval churn_rate=round((created + deleted) / 2, 0)
| eval health=case(
    deleted > created * 2, "WARNING — more deletions than creations, binding table shrinking",
    churn_rate > 1000, "WARNING — high binding churn",
    1=1, "OK")
| sort -churn_rate
```

## Visualization

(1) Timechart: binding creates vs deletes over time — should be roughly balanced during steady state. (2) Table: per-VLAN binding health with churn rate. (3) Single-value: total active bindings network-wide. (4) Drilldown: binding history for a specific MAC or IPv6 address.

## Known False Positives

**Daily privacy extension churn.** Hosts with RFC 8981 privacy extensions generate new temporary addresses daily. Each new address creates a binding, and the old address's binding eventually expires and is deleted. This produces a steady create/delete rate proportional to the number of hosts with privacy extensions.

**Morning onboarding spike.** When employees arrive in the morning and boot their devices, there is a spike in ENTRY_CREATED events. This is normal and expected.

**VLAN pruning or STP topology change.** When a VLAN is pruned from a trunk or STP reconverges, all bindings on the affected ports may be deleted simultaneously. This produces a spike in ENTRY_DELETED events.

## References

- [RFC 7039 — Source Address Validation Improvement (SAVI) Framework](https://www.rfc-editor.org/rfc/rfc7039)
- [RFC 6620 — FCFS SAVI: First-Come, First-Served Source Address Validation for Locally Assigned Addresses](https://www.rfc-editor.org/rfc/rfc6620)
- [RFC 7513 — SAVI Solution for DHCP](https://www.rfc-editor.org/rfc/rfc7513)
