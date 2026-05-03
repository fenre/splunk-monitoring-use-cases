<!-- AUTO-GENERATED from UC-5.6.6.json — DO NOT EDIT -->

---
id: "5.6.6"
title: "DHCP Rogue Server Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.6.6 · DHCP Rogue Server Detection

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Security &middot; **Type:** Security

*We help you know when a strange device might be handing out addresses on the network, which can break connectivity or steer people the wrong way until we fix it.*

---

## Description

Rogue DHCP servers assign wrong IPs/gateways, causing network disruption and potential MitM attacks.

## Value

Network security teams detect rogue DHCP servers that could enable man-in-the-middle attacks, identify the physical port via switch correlation, and quantify the number of affected clients.

## Implementation

Enable DHCP snooping on switches. Forward syslog. Alert on any rogue DHCP server detection events.

## Detailed Implementation

### Prerequisites
- DHCP event logs in `index=dhcp` with server IP extraction. A rogue DHCP server is an unauthorized device responding to DHCP DISCOVER/REQUEST messages, potentially handing out incorrect IP addresses, gateways, or DNS servers — a classic man-in-the-middle or denial-of-service attack vector.
- Build an `authorized_dhcp_servers.csv` lookup: `server_ip,server_name,location` listing all legitimate DHCP servers in your network.
- Detection method: DHCP OFFER and DHCP ACK messages come from a server IP. If the server IP is not in the authorized list, it's a rogue. Network-level detection (DHCP snooping on switches) is the primary defense; Splunk provides a secondary detection and forensic layer.
- Sources: Infoblox rogue DHCP detection logs, Windows DHCP Server events, or network-level DHCP snooping violation logs from switches.

### Step 1 — Configure data collection
Verify DHCP server identification in logs:
```spl
index=dhcp ("DHCPOFFER" OR "DHCPACK") earliest=-1h
| rex field=_raw "(?:from|server[\s:=]+)(?<dhcp_server>\d+\.\d+\.\d+\.\d+)"
| stats count by dhcp_server, host
```

### Step 2 — Create the search and alert

**Primary search — Rogue DHCP server detection:**
```spl
index=dhcp ("DHCPOFFER" OR "DHCPACK" OR "offer" OR "ack") earliest=-1h
| rex field=_raw "(?:from|server[\s:=]+)(?<dhcp_server>\d+\.\d+\.\d+\.\d+)"
| where isnotnull(dhcp_server)
| lookup authorized_dhcp_servers.csv server_ip as dhcp_server OUTPUT server_name
| where isnull(server_name)
| stats count dc(src) as affected_clients values(src) as client_list first(_time) as first_seen latest(_time) as last_seen by dhcp_server, host
| eval duration_min=round((last_seen-first_seen)/60, 1)
| sort -count
```

#### Understanding this SPL: Extracts the server IP from DHCP OFFER/ACK events and checks against the authorized server list. Any server not in the list is rogue. The `affected_clients` count shows the blast radius — how many clients received responses from the rogue server.

**DHCP snooping violation correlation:**
```spl
index=network sourcetype="syslog" ("dhcp snooping" OR "DHCP_SNOOPING" OR "rogue") earliest=-24h
| rex field=_raw "(?:interface|port)[\s:=]+(?<port>[\w/]+)"
| rex field=_raw "(?:vlan)[\s:=]+(?<vlan>\d+)"
| rex field=_raw "(?:from|mac)[\s:=]+(?<rogue_mac>[0-9a-fA-F]{2}(?:[:\-\.][0-9a-fA-F]{2,4}){2,5})"
| stats count first(_time) as first_seen by host, port, vlan, rogue_mac
| sort -first_seen
```

**Multi-server response detection (conflicting offers):**
```spl
index=dhcp "DHCPOFFER" earliest=-1h
| rex field=_raw "(?:from|server)\s+(?<dhcp_server>\d+\.\d+\.\d+\.\d+)"
| rex field=_raw "(?:for|to|client)\s+(?<client_mac>[0-9a-fA-F:.-]+)"
| where isnotnull(dhcp_server) AND isnotnull(client_mac)
| stats dc(dhcp_server) as server_count values(dhcp_server) as servers by client_mac
| where server_count > 1
| sort -server_count
```

#### Understanding this SPL: If a single client receives DHCP OFFERs from multiple servers, one of them may be rogue. Legitimate environments typically have only one DHCP server responding per subnet.

### Step 3 — Validate
(a) Verify the `authorized_dhcp_servers.csv` is complete — include all legitimate DHCP servers, DHCP relay agents, and any DHCP failover partners.
(b) Test: set up a rogue DHCP server in a lab VLAN and verify it's detected.
(c) Cross-reference with switch DHCP snooping logs for physical port identification.

### Step 4 — Operationalize
Dashboard ("Security — Rogue DHCP Detection"):
- Row 1 — Single-value tiles: "Rogue servers detected", "Affected clients", "DHCP snooping violations (24h)".
- Row 2 — Rogue server table: IP, first_seen, last_seen, affected_clients.
- Row 3 — Multi-server conflict table: client_mac, servers involved.
- Row 4 — Snooping violation log: switch, port, VLAN, MAC.

Alerting:
- Critical (any unauthorized DHCP server detected): page security and network operations immediately — this is a potential MITM attack.
- High (DHCP snooping violations > 5 on a single port): physical port investigation required.

Runbook:
1. **Rogue DHCP server found**: Identify the physical location via switch MAC table and DHCP snooping logs. Disable the switch port. Investigate the device. All clients that received leases from the rogue server need to renew from the legitimate server (`ipconfig /release && ipconfig /renew` on Windows).
2. **DHCP snooping violation**: Someone plugged in a device that's trying to serve DHCP. Check if it's a misconfigured network device, a personal router, or an intentional attack.

### Step 5 — Troubleshooting

- **Cannot extract DHCP server IP from logs** — Different log formats place the server IP differently. Test regex against sample events. For Infoblox, the server IP is the logging member's IP. For Windows DHCP events, it's the server sending the ACK.

- **Authorized server list incomplete** — DHCP failover partners, secondary DHCP servers, and DHCP relay agents may all appear as "servers". Include all legitimate sources.

- **False positives from DHCP relay agents** — DHCP relay agents forward requests but don't generate OFFERs. If your logs include relay agent IPs, filter them separately.

**DHCPv6 Considerations:** Extend rogue detection to unexpected DHCPv6 replies on UDP 547 and correlate with RA anomalies where dual-stack clients obtain gateways. DHCPv6 (RFC 8415) is a fundamentally different protocol from DHCPv4, using UDP ports 546/547. Key differences: (1) DHCPv6 does NOT provide default gateway — that comes from Router Advertisements. (2) Message types differ: Solicit/Advertise/Request/Reply instead of Discover/Offer/Request/Ack. (3) DHCPv6 Prefix Delegation (DHCPv6-PD) enables subnet allocation to downstream routers. (4) Syslog patterns differ: look for 'DHCPv6' in messages, not just 'DHCP'. For comprehensive DHCPv6 monitoring, see the IPv6 subcategory (UC-5.20.10, UC-5.20.141).

## SPL

```spl
index=network "DHCP" AND ("rogue" OR "conflict" OR "unauthorized" OR "snooping violation")
| table _time host src _raw | sort -_time
```

## Visualization

Events list (critical), Table, Map.

## Known False Positives

Port-security or MAB churn, lab switches, and miswired uplinks can resemble rogue offers until you confirm the MAC and port in your switch and DHCP admin views.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
