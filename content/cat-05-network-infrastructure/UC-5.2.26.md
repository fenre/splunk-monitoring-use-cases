<!-- AUTO-GENERATED from UC-5.2.26.json — DO NOT EDIT -->

---
id: "5.2.26"
title: "Client VPN Connections and Remote Access Patterns (Meraki MX)"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.2.26 · Client VPN Connections and Remote Access Patterns (Meraki MX)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We count remote access use over time so you can plan capacity, spot odd login surges, and help people who are stuck at home or on the road.*

---

## Description

Tracks client VPN usage patterns for remote workers and identifies problematic connections.

## Value

Security teams monitor Meraki MX Client VPN connections and authentication failures, detecting brute force attempts and tracking remote access patterns.

## Implementation

Filter VPN logs for client connections. Track by user and source IP.

## Detailed Implementation

### Prerequisites
* Meraki MX Client VPN (AnyConnect or native L2TP) logs. Data in `index=meraki` with `sourcetype=meraki:events`. Key fields: `user`, `client_ip`, `assigned_ip`, `event_type` (connect/disconnect), `duration`.
* Client VPN: remote access for individual users. Meraki supports AnyConnect (requires licensing) and native L2TP/IPSec. Authentication via Meraki cloud, RADIUS, or Active Directory.

### Step 1 — - Configure data collection
```
# Dashboard > Security & SD-WAN > Client VPN
# Enable Client VPN, configure authentication (RADIUS/AD/Meraki cloud)
# Syslog > Roles: VPN
```
Verify:
```spl
index=meraki sourcetype="meraki:events" earliest=-24h
| where match(_raw, "(?i)client.*vpn|anyconnect|l2tp|remote.*access.*vpn|vpn.*connect|vpn.*disconnect")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Client VPN connection analysis:**
```spl
index=meraki sourcetype="meraki:events" earliest=-24h
| where match(_raw, "(?i)client.*vpn|anyconnect|l2tp|vpn.*(connect|disconnect|auth)")
| eval vpn_event=case(match(_raw, "(?i)connect(?!.*dis)|established|logged.in|auth.*success"), "CONNECT", match(_raw, "(?i)disconnect|terminated|logged.out|session.*end"), "DISCONNECT", match(_raw, "(?i)auth.*fail|denied|reject"), "AUTH_FAILURE", 1==1, "OTHER")
| eval usr=coalesce(user, username, src_user)
| eval client_ip=coalesce(src, src_ip, client_ip)
| stats count as events count(eval(vpn_event="CONNECT")) as connects count(eval(vpn_event="DISCONNECT")) as disconnects count(eval(vpn_event="AUTH_FAILURE")) as auth_failures by usr, client_ip
| eval severity=case(auth_failures > 10, "HIGH -- multiple VPN auth failures for ".usr, auth_failures > 3 AND connects > 0, "WARNING -- auth failures followed by success", 1==1, "INFO")
| where severity != "INFO"
| sort severity, -auth_failures
```

### Step 3 — - Validate
(a) Dashboard: Security & SD-WAN > Client VPN -- active connections and users.
(b) Attempt a failed VPN login and verify auth_failure appears.
(c) Compare active VPN sessions with Dashboard.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- Client VPN"):
* Row 1 -- Single-value: "Active VPN users", "Connections (24h)", "Auth failures".
* Row 2 -- Client VPN session table.

Alerting:
* High (> 10 auth failures for single user): brute force attempt.
* Warning (auth failures then success): possible credential compromise.

### Step 5 — - Troubleshooting

* **Auth failures** -- Check: (1) RADIUS/AD server reachability from MX, (2) user credentials, (3) RADIUS shared secret matches, (4) user is in the correct AD group for VPN access.

* **VPN connects but no traffic** -- Check: (1) split-tunnel vs full-tunnel configuration, (2) VPN subnet routing, (3) firewall rules allowing VPN subnet.

* **Connection drops after short time** -- Check: (1) idle timeout settings, (2) RADIUS session timeout, (3) WAN uplink instability.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=vpn client_vpn=true
| stats count as connection_count, avg(duration) as avg_session_length by user_id, src
| where connection_count > 10
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.All_Sessions
  by All_Sessions.user All_Sessions.src All_Sessions.dest All_Sessions.action span=1h
| sort -count
```

## Visualization

Connected users timeline; session duration histogram; geography map of remote users.

## Known False Positives

Travel peaks, on-call surges, and class schedules can make remote access login counts swing widely.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Network_Sessions](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Sessions)
