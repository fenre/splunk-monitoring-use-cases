<!-- AUTO-GENERATED from UC-5.8.20.json — DO NOT EDIT -->

---
id: "5.8.20"
title: "Configuration Change Window Compliance (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.8.20 · Configuration Change Window Compliance (Meraki)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Compliance

*We help you show when changes were made in approved windows versus odd hours, so maintenance stays under control.*

---

## Description

Ensures configuration changes only occur within approved maintenance windows.

## Value

Network operations teams enforce configuration change window compliance across Meraki networks, detecting out-of-window changes, flagging sensitive modifications, and generating governance compliance reports.

## Implementation

Monitor configuration change events. Check against maintenance windows.

## Detailed Implementation

### Prerequisites
- Meraki configuration change data from the organization change log API (`sourcetype=meraki:api:changelog`). Key fields: `ts` (timestamp), `adminName`, `page`, `label`, `networkName`, `oldValue`, `newValue`.
- Build `meraki_change_windows.csv` lookup: `networkName,window_start_utc,window_end_utc,day_of_week,description` (e.g., `Branch-Chicago,02:00,06:00,Saturday,Weekly maintenance`). This defines approved change windows per network.
- Change window compliance is a governance requirement: production changes should only happen during approved maintenance windows to minimize user impact. Changes outside windows need justification and approval.

### Step 1 — Configure data collection
Verify change log data:
```spl
index=meraki sourcetype="meraki:api:changelog" earliest=-7d
| stats count by networkName
| sort -count
```

### Step 2 — Create the search and alert

**Primary search — Change window compliance:**
```spl
index=meraki sourcetype="meraki:api:changelog" earliest=-7d
| eval change_hour=strftime(_time, "%H")
| eval change_day=strftime(_time, "%A")
| lookup meraki_change_windows.csv networkName OUTPUT window_start_utc window_end_utc day_of_week as approved_day
| eval in_window=if(isnotnull(window_start_utc) AND change_hour >= window_start_utc AND change_hour < window_end_utc AND change_day=approved_day, "IN_WINDOW", "OUTSIDE_WINDOW")
| eval in_window=if(isnull(window_start_utc), "NO_POLICY", in_window)
| where in_window!="IN_WINDOW"
| eval admin=coalesce(adminName, adminEmail)
| eval is_sensitive=if(match(page, "(?i)(firewall|security|vpn|admin|ssid)"), "YES", "NO")
| table _time, admin, networkName, page, label, in_window, is_sensitive
| sort is_sensitive, -_time
```

#### Understanding this SPL: Changes outside approved windows are the leading cause of unplanned outages in network operations. A firewall rule change at 3 PM on a Tuesday can impact hundreds of users; the same change at 3 AM Saturday affects no one. This search identifies non-compliant changes and flags sensitive ones (firewall, VPN, SSID) for immediate review.

**Change compliance summary:**
```spl
index=meraki sourcetype="meraki:api:changelog" earliest=-30d
| eval change_hour=strftime(_time, "%H")
| eval change_day=strftime(_time, "%A")
| lookup meraki_change_windows.csv networkName OUTPUT window_start_utc window_end_utc day_of_week as approved_day
| eval compliant=if(isnotnull(window_start_utc) AND change_hour >= window_start_utc AND change_hour < window_end_utc AND change_day=approved_day, 1, 0)
| stats count as total sum(compliant) as in_window by networkName
| eval compliance_pct=round(100*in_window/total, 1)
| sort compliance_pct
```

### Step 3 — Validate
(a) Make a change outside the approved window and verify it flags as "OUTSIDE_WINDOW".
(b) Make a change during the approved window and verify it shows as "IN_WINDOW".
(c) Verify change window lookup accurately reflects the organization's maintenance schedule.

### Step 4 — Operationalize
Dashboard ("Change Window Compliance"):
- Row 1 — Single-value tiles: "In-window changes", "Outside-window changes", "Compliance %", "Sensitive out-of-window changes".
- Row 2 — Non-compliant changes table: time, admin, network, change, sensitivity.
- Row 3 — Compliance % by network (30-day rolling).

Alerting:
- High (sensitive change outside window): immediate review — firewall/VPN/SSID change during production hours.
- Warning (any change outside window): track for compliance reporting.
- Monthly: compliance report per network.

### Step 5 — Troubleshooting

- **All changes show OUTSIDE_WINDOW** — The change window lookup may have incorrect time zone handling. Ensure timestamps are in the same timezone (convert to UTC).

- **Emergency changes flagged** — Emergency changes are expected to be outside the window. Add an `emergency_override` field to the lookup or a separate emergency change log to exclude approved emergency changes from compliance metrics.

- **NO_POLICY for some networks** — Networks without entries in the change window lookup don't have a defined policy. Add them to the lookup or establish a default policy.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*config*"
| eval hour=strftime(_time, "%H")
| stats count as config_change_count by hour
| eval window_compliant=if(hour>=22 OR hour<6, "Yes", "No")
| where window_compliant="No" AND config_change_count > 0
```

## Visualization

Change compliance timeline; out-of-window change alert table.

## Known False Positives

Emergency fixes outside the window are sometimes correct; require change ticket and approver for exceptions, do not only silence the alert.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
