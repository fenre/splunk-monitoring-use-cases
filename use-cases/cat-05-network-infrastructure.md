# 5. Network Infrastructure

**Monitoring type** (filter category): Each use case is tagged with one or more of the following so you can filter by kind of network monitoring:

| Type | Description |
|------|-------------|
| **Availability** | Link/device/service up-down, peer state, tunnel/HA status, health checks, uptime. |
| **Performance** | Utilization, throughput, latency, errors, response time, jitter, resource metrics. |
| **Security** | ACL/deny, authentication failures, threats, IDS/IPS, VPN, rogue detection, policy violations. |
| **Configuration** | Config or policy change detection, drift, change audit. |
| **Capacity** | Exhaustion (NAT, session, DHCP), trending, capacity planning, queue depth. |
| **Fault** | Environmental, power, fan, hardware failure, environmental monitoring. |
| **Anomaly** | Flapping, instability, anomalous patterns, MAC/route flapping. |
| **Compliance** | Audit trail, backup compliance, posture, change-window compliance. |

---

## 5.1 Routers & Switches

**Primary App/TA:** Splunk Add-on for Cisco IOS (`Splunk_TA_cisco-ios`), SNMP Modular Input — Free

---

### UC-5.1.1 · Interface Up/Down Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Link state changes directly impact connectivity. Flapping interfaces cause intermittent outages.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%LINEPROTO-5-UPDOWN" OR "%LINK-3-UPDOWN"
| rex "Interface (?<interface>\S+), changed state to (?<state>\w+)"
| stats count by host, interface, state | where count > 3 | sort -count
```
- **Implementation:** Configure syslog forwarding on all network devices (UDP/TCP 514). Install TA for field extraction. Alert on down events for uplinks/trunks. Track flapping (>3 transitions in 10 min).
- **Visualization:** Status grid (green/red per interface), Table, Timeline.
- **CIM Models:** N/A

---

### UC-5.1.2 · Interface Error Rates
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** CRC errors, drops indicate cabling, transceiver, or duplex issues.
- **App/TA:** SNMP Modular Input, IF-MIB
- **Data Sources:** `sourcetype=snmp:interface`
- **SPL:**
```spl
index=network sourcetype="snmp:interface"
| streamstats current=f last(ifInErrors) as prev by host, ifDescr
| eval delta = ifInErrors - prev | where delta > 0
| table _time host ifDescr delta
```
- **Implementation:** Poll IF-MIB (ifInErrors, ifOutErrors, ifInDiscards) at 300s. Use `streamstats` for delta. Alert on increasing counts.
- **Visualization:** Line chart (error rate), Table, Heatmap across devices.
- **CIM Models:** N/A

---

### UC-5.1.3 · Interface Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Capacity
- **Value:** Saturated links cause drops and congestion. Trending enables proactive upgrades.
- **App/TA:** SNMP Modular Input
- **Data Sources:** SNMP IF-MIB (ifHCInOctets, ifHCOutOctets, ifSpeed)
- **SPL:**
```spl
index=network sourcetype="snmp:interface"
| streamstats current=f last(ifHCInOctets) as prev_in, last(_time) as prev_time by host, ifDescr
| eval in_bps=((ifHCInOctets-prev_in)*8)/(_time-prev_time)
| eval util_pct=round(in_bps/ifSpeed*100,1) | where util_pct>80
```
- **Implementation:** Poll 64-bit counters every 300s. Alert at 80% sustained. Use `predict` for capacity planning.
- **Visualization:** Line chart, Gauge per critical link, Table sorted by utilization.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| sort -bytes
```

---

### UC-5.1.4 · BGP Peer State Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** BGP session drops cause routing convergence, potentially making networks unreachable.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%BGP-5-ADJCHANGE" OR "%BGP-3-NOTIFICATION"
| rex "neighbor (?<neighbor_ip>\S+)" | table _time host neighbor_ip _raw | sort -_time
```
- **Implementation:** Forward syslog from all BGP speakers. Critical alert on adjacency down. Include neighbor IP and AS number.
- **Visualization:** Events timeline (critical), Status panel per BGP session, Table.
- **CIM Models:** N/A

---

### UC-5.1.5 · OSPF Neighbor Adjacency
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** OSPF neighbor loss triggers SPF recalculation, disrupting traffic.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%OSPF-5-ADJCHG"
| rex "Nbr (?<neighbor_ip>\S+) on (?<interface>\S+) from (?<from_state>\S+) to (?<to_state>\S+)"
| table _time host neighbor_ip interface from_state to_state
```
- **Implementation:** Forward syslog from all OSPF routers. Alert on adjacency changes to/from FULL. Track frequency for instability.
- **Visualization:** Events timeline, Table (router, neighbor, states).
- **CIM Models:** N/A

---

### UC-5.1.6 · Spanning Tree Topology Change
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability, Anomaly
- **Value:** STP topology changes cause brief disruption and MAC flushing. Root bridge changes are critical.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%SPANTREE-5-TOPOTCHANGE" OR "%SPANTREE-2-ROOTCHANGE"
| stats count by host | where count > 5 | sort -count
```
- **Implementation:** Forward syslog. Alert on root bridge changes (critical). Track topology change frequency per VLAN.
- **Visualization:** Table, Timeline, Bar chart by VLAN.
- **CIM Models:** N/A

---

### UC-5.1.7 · Configuration Change Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration, Compliance
- **Value:** Unauthorized config changes are a top cause of outages. Essential for compliance.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%SYS-5-CONFIG_I"
| rex "Configured from (?<config_source>\S+) by (?<user>\S+)"
| table _time host user config_source
```
- **Implementation:** Forward syslog. Enable archive logging. Alert on any config change. Correlate with change tickets.
- **Visualization:** Table (device, user, time), Timeline, Single value (changes last 24h).
- **CIM Models:** N/A

---

### UC-5.1.8 · Device CPU/Memory Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Capacity
- **Value:** CPU exhaustion causes packet drops, routing failures, management unresponsiveness.
- **App/TA:** SNMP, CISCO-PROCESS-MIB
- **Data Sources:** `sourcetype=snmp:cpu`
- **SPL:**
```spl
index=network sourcetype="snmp:cpu"
| timechart span=5m avg(cpmCPUTotal5minRev) as cpu_pct by host | where cpu_pct > 80
```
- **Implementation:** Poll CISCO-PROCESS-MIB and CISCO-MEMORY-POOL-MIB every 300s. Alert CPU >80% or memory >85%.
- **Visualization:** Line chart, Gauge, Table of high-utilization devices.
- **CIM Models:** N/A

---

### UC-5.1.9 · Device Uptime / Reload Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability, Fault
- **Value:** Unexpected reboots indicate hardware failure or unauthorized reload.
- **App/TA:** SNMP, syslog
- **Data Sources:** SNMP sysUpTime, `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%SYS-5-RESTART" OR "%SYS-5-RELOAD"
| table _time host _raw | sort -_time
```
- **Implementation:** Poll SNMP sysUpTime. Forward syslog reload messages. Alert when uptime drops. Cross-reference with maintenance windows.
- **Visualization:** Table (device, uptime), Timeline, Single value (unexpected reboots).
- **CIM Models:** N/A

---

### UC-5.1.10 · VLAN Configuration Changes
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration, Compliance
- **Value:** VLAN changes affect segmentation. Unauthorized changes can bypass security controls.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%VLAN_MANAGER-6-VLAN_CREATE" OR "%VLAN_MANAGER-6-VLAN_DELETE"
| table _time host _raw | sort -_time
```
- **Implementation:** Forward syslog. Alert on VLAN creation/deletion. Correlate with change tickets.
- **Visualization:** Table, Timeline.
- **CIM Models:** N/A

---

### UC-5.1.11 · Power Supply / Fan Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Hardware failures reduce redundancy. A second failure causes outage.
- **App/TA:** `Splunk_TA_cisco-ios`, SNMP CISCO-ENVMON-MIB
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%FAN-3-FAN_FAILED" OR "%PLATFORM_ENV-1-PSU" OR "%ENVIRONMENTAL-1-ALERT"
| table _time host _raw | sort -_time
```
- **Implementation:** Forward syslog. Poll ENVMON-MIB. Alert immediately on hardware failure. Include device location for dispatch.
- **Visualization:** Status indicator per device, Events list (critical).
- **CIM Models:** N/A

---

### UC-5.1.12 · ARP/MAC Table Anomalies
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Anomaly, Security
- **Value:** MAC flapping indicates loops, misconfigurations, or layer-2 attacks.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%SW_MATM-4-MACFLAP_NOTIF"
| rex "(?<mac>[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})"
| stats count by host, mac | sort -count
```
- **Implementation:** Forward syslog. Alert on MACFLAP events. Investigate the MAC to find the device.
- **Visualization:** Table, Timeline, Bar chart.
- **CIM Models:** N/A

---

### UC-5.1.13 · ACL Deny Logging
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** ACL deny hits show blocked traffic. High volumes may indicate attacks or misconfigured apps.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%SEC-6-IPACCESSLOGP"
| rex "list (?<acl>\S+) denied (?<proto>\w+) (?<src_ip>\d+\.\d+\.\d+\.\d+)"
| stats count by host, acl, src_ip, proto | sort -count
```
- **Implementation:** Enable ACL logging (`log` keyword). Forward syslog. Dashboard showing top denied sources and trends.
- **Visualization:** Table, Bar chart by source IP, Timechart.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.action=blocked
  by All_Traffic.src All_Traffic.dest All_Traffic.dest_port span=1h
| sort -count
```

---

### UC-5.1.14 · SNMP Authentication Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Failed SNMP auth indicates unauthorized polling or reconnaissance.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%SNMP-3-AUTHFAIL"
| rex "from (?<src_ip>\S+)" | stats count by host, src_ip | sort -count
```
- **Implementation:** Forward syslog. Alert on repeated failures from unknown sources.
- **Visualization:** Table, Map, Timeline.
- **CIM Models:** N/A

---

### UC-5.1.15 · Environmental Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Temperature alerts catch cooling failures before they cause device outages.
- **App/TA:** SNMP, CISCO-ENVMON-MIB
- **Data Sources:** `sourcetype=snmp:environment`
- **SPL:**
```spl
index=network sourcetype="snmp:environment"
| stats latest(ciscoEnvMonTemperatureValue) as temp_c by host | where temp_c > 45
```
- **Implementation:** Poll ENVMON-MIB temperature sensors every 300s. Alert when >45°C.
- **Visualization:** Gauge per device, Line chart (trending), Table.
- **CIM Models:** N/A

---

### UC-5.1.16 · Route Table Flapping
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Anomaly
- **Value:** Unstable routes cause packet loss and reachability failures. Detecting flapping routes prevents cascading network outages across your infrastructure.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "ROUTING" OR "RT_ENTRY" OR "%DUAL-5-NBRCHANGE" OR "%BGP-5-ADJCHANGE" OR "%OSPF-5-ADJCHG"
| rex "(?<protocol>BGP|OSPF|EIGRP).*?(?<prefix>\d+\.\d+\.\d+\.\d+/?\d*)"
| bin _time span=10m | stats count as changes by _time, host, protocol, prefix
| where changes > 5 | sort -changes
```
- **Implementation:** Collect syslog from all routers. Alert on >5 route changes for the same prefix in 10 minutes. Correlate with interface flaps. Use `streamstats` to detect patterns.
- **Visualization:** Timeline (flapping events), Table (prefix, host, count), Line chart (change frequency).
- **CIM Models:** N/A

---

### UC-5.1.17 · Duplex Mismatch Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Fault
- **Value:** Duplex mismatches degrade link performance silently. They cause late collisions, CRC errors, and reduced throughput that are hard to diagnose.
- **App/TA:** SNMP Modular Input, IF-MIB, `Splunk_TA_cisco-ios`
- **Data Sources:** `sourcetype=cisco:ios`, `sourcetype=snmp:interface`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%CDP-4-DUPLEX_MISMATCH"
| rex "duplex mismatch discovered on (?<local_intf>\S+).*with (?<remote_device>\S+) (?<remote_intf>\S+)"
| stats count latest(_time) as last_seen by host, local_intf, remote_device, remote_intf
| sort -last_seen
```
- **Implementation:** Enable CDP/LLDP on all interfaces. Monitor syslog for duplex mismatch messages. Cross-reference with SNMP interface counters showing late collisions.
- **Visualization:** Table (local device/interface → remote device/interface), Alert list.
- **CIM Models:** N/A

---

### UC-5.1.18 · CDP/LLDP Neighbor Changes
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Configuration
- **Value:** Unexpected neighbor changes indicate cabling modifications, device replacements, or unauthorized devices connecting to the network.
- **App/TA:** SNMP Modular Input, CISCO-CDP-MIB, LLDP-MIB
- **Data Sources:** `sourcetype=snmp:cdp`, `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="snmp:cdp"
| stats latest(cdpCacheDeviceId) as neighbor, latest(cdpCachePlatform) as platform by host, cdpCacheIfIndex
| appendpipe [| inputlookup cdp_baseline.csv]
| eventstats latest(neighbor) as current, first(neighbor) as baseline by host, cdpCacheIfIndex
| where current!=baseline | table host, cdpCacheIfIndex, baseline, current, platform
```
- **Implementation:** Poll CDP-MIB/LLDP-MIB at 600s intervals. Create a baseline lookup via `outputlookup`. Compare current neighbors against baseline. Alert on new/removed neighbors.
- **Visualization:** Table (host, interface, old neighbor, new neighbor), Change log timeline.
- **CIM Models:** N/A

---

### UC-5.1.19 · PoE Power Budget Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Fault
- **Value:** PoE budget exhaustion causes powered devices (IP phones, APs, cameras) to lose power. Proactive monitoring prevents unplanned device outages.
- **App/TA:** SNMP Modular Input, POWER-ETHERNET-MIB
- **Data Sources:** `sourcetype=snmp:poe`
- **SPL:**
```spl
index=network sourcetype="snmp:poe"
| stats latest(pethMainPseOperStatus) as status, latest(pethMainPsePower) as total_watts, latest(pethMainPseConsumptionPower) as used_watts by host
| eval utilization_pct=round(used_watts/total_watts*100,1)
| where utilization_pct > 80 | sort -utilization_pct
```
- **Implementation:** Poll POWER-ETHERNET-MIB every 300s. Track per-switch PoE budget utilization. Alert at 80% utilization. Trend over time to plan for additional PoE capacity.
- **Visualization:** Gauge (per switch), Line chart (utilization trending), Table (switch, budget, used, remaining).
- **CIM Models:** N/A

---

### UC-5.1.20 · EIGRP Neighbor Flapping
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Anomaly, Availability
- **Value:** EIGRP neighbor instability causes route recalculation, increased CPU load, and traffic blackholing during convergence.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%DUAL-5-NBRCHANGE"
| rex "EIGRP-(?<protocol>IPv4|IPv6) (?<as_number>\d+).*Neighbor (?<neighbor_ip>\S+) \((?<interface>\S+)\) is (?<state>up|down)"
| bin _time span=15m | stats count(eval(state="down")) as downs, count(eval(state="up")) as ups by _time, host, neighbor_ip, interface
| where downs > 2
```
- **Implementation:** Collect syslog from Cisco routers. Alert on >2 EIGRP neighbor down events in 15 minutes. Correlate with interface flaps and CPU utilization.
- **Visualization:** Timeline (up/down events), Table (neighbor, interface, flap count), Status grid.
- **CIM Models:** N/A

---

### UC-5.1.21 · CRC Error Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Increasing CRC errors indicate failing cables, SFPs, or electromagnetic interference. Early detection prevents link failures.
- **App/TA:** SNMP Modular Input, IF-MIB
- **Data Sources:** `sourcetype=snmp:interface`
- **SPL:**
```spl
index=network sourcetype="snmp:interface"
| streamstats current=f last(ifInErrors) as prev_errors, last(_time) as prev_time by host, ifDescr
| eval error_rate=(ifInErrors-prev_errors)/(_time-prev_time)
| where error_rate > 0
| timechart span=1h avg(error_rate) by host limit=20
```
- **Implementation:** Poll IF-MIB counters every 300s. Use `streamstats` to compute deltas. Trend over days to detect worsening interfaces. Cross-reference with interface utilization.
- **Visualization:** Line chart (error rate over time per interface), Heatmap (device × interface), Table.
- **CIM Models:** N/A

---

### UC-5.1.22 · Syslog Source Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔴 Expert
- **Monitoring type:** Availability
- **Value:** Silence from a device means either it's healthy or its syslog forwarding broke. Detecting missing syslog sources ensures continuous visibility.
- **App/TA:** Splunk core (metadata search)
- **Data Sources:** `sourcetype=cisco:ios`, `sourcetype=syslog`
- **SPL:**
```spl
| tstats count where index=network sourcetype="cisco:ios" by host
| append [| inputlookup network_device_inventory.csv | rename device as host | fields host]
| stats sum(count) as event_count by host | where event_count=0 OR isnull(event_count)
| table host | rename host as "Silent Devices"
```
- **Implementation:** Maintain a device inventory lookup. Schedule a search comparing active syslog sources against inventory. Alert on devices missing for >1 hour.
- **Visualization:** Table (silent devices), Single value (count of silent devices), Status grid (all devices).
- **CIM Models:** N/A

---

### UC-5.1.23 · HSRP/VRRP State Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Gateway redundancy state changes impact all hosts on a subnet. Detecting unexpected failovers prevents prolonged outages.
- **App/TA:** `Splunk_TA_cisco-ios`, syslog
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%HSRP-5-STATECHANGE" OR "%VRRP-6-STATECHANGE"
| rex "Grp (?<group>\d+) state (?<old_state>\w+) -> (?<new_state>\w+)"
| where new_state="Active" OR new_state="Master"
| stats count by host, group, old_state, new_state | sort -_time
```
- **Implementation:** Enable HSRP/VRRP syslog notifications. Alert on Active/Master transitions. Correlate with interface or device failures to validate failover cause.
- **Visualization:** Timeline (state changes), Table (group, host, transition), Alert panel.
- **CIM Models:** N/A

---


## 5.2 Firewalls

**Primary App/TA:** Palo Alto Networks Add-on (`Splunk_TA_paloalto`), Cisco Firepower TA, Fortinet TA — Free

---

### UC-5.2.1 · Top Denied Traffic Sources
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Identifies top blocked traffic sources — useful for rule tuning, detecting scanning, and misconfigured apps.
- **App/TA:** Vendor-specific firewall TA
- **Data Sources:** `sourcetype=pan:traffic`, `sourcetype=fgt_traffic`, `sourcetype=cisco:firepower:syslog`
- **SPL:**
```spl
index=firewall action="denied" OR action="drop"
| stats count as denials, dc(dest_ip) as unique_dests by src_ip
| sort -denials | head 20 | lookup geoip ip as src_ip OUTPUT Country
```
- **Implementation:** Forward firewall traffic logs via syslog. Install vendor TA for CIM-compliant fields. Create top-N dashboard.
- **Visualization:** Table (source, denials, dests), Map (GeoIP), Bar chart.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.2.2 · Policy Change Audit
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration, Compliance
- **Value:** Firewall rule changes can expose the network. Compliance must-have (PCI, SOX, HIPAA).
- **App/TA:** Vendor-specific firewall TA
- **Data Sources:** `sourcetype=pan:config`, firewall system/config logs
- **SPL:**
```spl
index=firewall sourcetype="pan:config" cmd="set" OR cmd="edit" OR cmd="delete"
| table _time host admin cmd path | sort -_time
```
- **Implementation:** Forward configuration change logs. Alert on any rule modification. Require change ticket correlation. Keep 1-year retention.
- **Visualization:** Table (who, what, when), Timeline, Single value (changes last 24h).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.2.3 · Threat Detection Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** IPS/IDS events indicate active attacks. Correlation with traffic context enables rapid response.
- **App/TA:** Vendor-specific firewall TA
- **Data Sources:** `sourcetype=pan:threat`, `sourcetype=cisco:firepower:alert`
- **SPL:**
```spl
index=firewall sourcetype="pan:threat" severity="critical" OR severity="high"
| stats count by src_ip, dest_ip, threat_name, severity, action | sort -count
```
- **Implementation:** Forward threat logs. Alert immediately on critical severity. Correlate source IPs with auth logs.
- **Visualization:** Table (source, dest, threat, action), Bar chart by threat type, Map.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.2.4 · VPN Tunnel Status
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** VPN failures isolate remote sites or users. Proactive monitoring prevents "the VPN is down" calls.
- **App/TA:** Vendor-specific firewall TA
- **Data Sources:** Firewall VPN/system logs
- **SPL:**
```spl
index=firewall ("tunnel" OR "IPSec" OR "IKE") ("down" OR "failed" OR "established")
| rex "(?<tunnel_peer>\d+\.\d+\.\d+\.\d+)"
| eval status=if(match(_raw,"established|up"),"Up","Down")
| stats latest(status) as state by host, tunnel_peer | where state="Down"
```
- **Implementation:** Forward VPN logs. Alert on tunnel down events. Track flapping. Dashboard showing all tunnels.
- **Visualization:** Status grid (green/red per tunnel), Table, Timeline.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.2.5 · High-Risk Port Exposure
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Allowed traffic to RDP/SMB/Telnet from untrusted zones indicates policy gaps.
- **App/TA:** Vendor-specific firewall TA
- **Data Sources:** Firewall traffic logs
- **SPL:**
```spl
index=firewall action="allowed" (dest_port=3389 OR dest_port=445 OR dest_port=23)
| where NOT cidrmatch("10.0.0.0/8", src_ip)
| stats count by src_ip, dest_ip, dest_port | sort -count
```
- **Implementation:** Monitor allow rules for external traffic to high-risk ports. Alert on any matches. Review and tighten rules.
- **Visualization:** Table (source, dest, port), Bar chart by port, Map.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.2.6 · Geo-IP Anomaly Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Anomaly
- **Value:** Traffic to/from sanctioned or unexpected countries flags exfiltration, C2, or compromised hosts.
- **App/TA:** Vendor-specific TA + GeoIP lookup
- **Data Sources:** Firewall traffic logs
- **SPL:**
```spl
index=firewall action="allowed" direction="outbound"
| lookup geoip ip as dest_ip OUTPUT Country
| search Country IN ("Russia","China","North Korea","Iran")
| stats count, sum(bytes_out) as data_sent by src_ip, Country | sort -data_sent
```
- **Implementation:** Install GeoIP lookup (MaxMind). Enrich traffic logs. Alert on sanctioned country traffic and volume anomalies.
- **Visualization:** Choropleth map, Table, Bar chart by country.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.2.7 · Connection Rate Anomalies
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Anomaly, Performance
- **Value:** Sudden connection spikes indicate DDoS, scanning, or worm propagation.
- **App/TA:** Vendor-specific firewall TA
- **Data Sources:** Firewall traffic logs
- **SPL:**
```spl
index=firewall | timechart span=5m count as connections by src_ip
| eventstats avg(connections) as avg_c, stdev(connections) as std_c by src_ip
| where connections > (avg_c + 3*std_c) | sort -connections
```
- **Implementation:** Baseline connection rates over 7 days. Alert when rate exceeds 3 standard deviations.
- **Visualization:** Line chart with threshold overlay, Table, Timechart.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.2.8 · Certificate Inspection Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** SSL decryption failures mean traffic passes uninspected — could be legitimate cert pinning or SSL evasion.
- **App/TA:** Vendor-specific firewall TA
- **Data Sources:** Firewall decryption logs
- **SPL:**
```spl
index=firewall sourcetype="pan:decryption" action="ssl-error"
| stats count by dest_ip, dest_port, reason | sort -count
```
- **Implementation:** Enable decryption logging. Track failure rates by destination. Tune exclusion lists.
- **Visualization:** Table, Pie chart (reasons), Trend line.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.2.9 · URL Filtering Blocks
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Shows what categories users are trying to access. Reveals policy effectiveness and shadow IT.
- **App/TA:** Vendor-specific firewall TA
- **Data Sources:** `sourcetype=pan:url`
- **SPL:**
```spl
index=firewall sourcetype="pan:url" action="block-url"
| stats count by url_category, src_ip | sort -count
```
- **Implementation:** Forward URL filtering logs. Dashboard showing blocks by category and user.
- **Visualization:** Bar chart (by category), Table, Pie chart.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.action=blocked
  by All_Traffic.src All_Traffic.dest All_Traffic.dest_port span=1h
| sort -count
```

---

### UC-5.2.10 · Admin Access Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Firewall admin access is highly privileged. Audit trail is a compliance must-have.
- **App/TA:** Vendor-specific firewall TA
- **Data Sources:** Firewall system/auth logs
- **SPL:**
```spl
index=firewall sourcetype="pan:system" ("login" OR "logout" OR "auth")
| eval status=case(match(_raw,"success"),"Success", match(_raw,"fail"),"Failed", 1=1,"Other")
| stats count by admin_user, src_ip, status | sort -count
```
- **Implementation:** Forward system/auth logs. Alert on failed admin logins. Track all successful logins. Alert on unexpected source IPs.
- **Visualization:** Table (admin, source, status), Timeline, Bar chart.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.2.11 · Firewall Resource Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Capacity
- **Value:** Session table exhaustion blocks new connections. CPU saturation degrades throughput.
- **App/TA:** Vendor-specific TA, SNMP
- **Data Sources:** Firewall system resource logs
- **SPL:**
```spl
index=firewall ("session" AND "utilization") OR ("cpu" AND "dataplane")
| timechart span=5m avg(session_utilization) as session_pct by host | where session_pct > 80
```
- **Implementation:** Monitor via SNMP (vendor-specific MIB) or system logs. Alert on session table >80%, dataplane CPU >80%.
- **Visualization:** Gauge (session/CPU/memory), Line chart, Table.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| sort -bytes
```

---

### UC-5.2.12 · NAT Pool Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** NAT exhaustion prevents outbound connections. Users lose internet access.
- **App/TA:** Vendor-specific TA, syslog
- **Data Sources:** Firewall NAT/system logs
- **SPL:**
```spl
index=firewall ("NAT" OR "nat") ("exhausted" OR "allocation failed" OR "out of")
| stats count by host, nat_pool | sort -count
```
- **Implementation:** Forward firewall logs. Monitor NAT table usage. Alert on exhaustion messages or >80% utilization.
- **Visualization:** Gauge per pool, Table, Events timeline.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.2.13 · Session Table Exhaustion
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity
- **Value:** When session tables fill, new connections are dropped. This causes service outages that are difficult to diagnose without firewall telemetry.
- **App/TA:** `Splunk_TA_paloalto`, Splunk_TA_fortinet_fortigate, SNMP
- **Data Sources:** `sourcetype=pan:system`, `sourcetype=fgt_event`, SNMP
- **SPL:**
```spl
index=network sourcetype="pan:system" "session table"
| append [search index=network sourcetype="pan:traffic" | stats dc(session_id) as active_sessions by dvc | eval max_sessions=coalesce(max_sessions,500000)]
| stats latest(active_sessions) as sessions, latest(max_sessions) as max by dvc
| eval utilization=round(sessions/max*100,1) | where utilization > 80
```
- **Implementation:** Monitor session counts via SNMP or firewall system logs. Know your platform's session limit. Alert at 80% utilization. Investigate top session consumers by source/destination.
- **Visualization:** Gauge (per firewall), Line chart (session count trending), Table (top consumers).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.2.14 · Firewall HA Failover Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** HA failovers cause brief traffic disruption and can indicate underlying hardware or link failures. Tracking failover frequency detects instability.
- **App/TA:** `Splunk_TA_paloalto`, Splunk_TA_fortinet_fortigate
- **Data Sources:** `sourcetype=pan:system`, `sourcetype=fgt_event`
- **SPL:**
```spl
index=network (sourcetype="pan:system" "HA state change") OR (sourcetype="fgt_event" subtype="ha")
| rex "state change.*from (?<old_state>\w+) to (?<new_state>\w+)"
| table _time, dvc, old_state, new_state | sort -_time
```
- **Implementation:** Forward firewall system logs to Splunk. Alert on any active/passive transition. Correlate with link down events. Track failover frequency — more than 1 per week indicates instability.
- **Visualization:** Timeline (failover events), Single value (failovers this month), Table (history).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.2.15 · Botnet/C2 Traffic Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Detecting outbound connections to known C2 infrastructure identifies compromised internal hosts before data exfiltration occurs.
- **App/TA:** `Splunk_TA_paloalto`, Threat intelligence feeds
- **Data Sources:** `sourcetype=pan:threat`, `sourcetype=pan:traffic`
- **SPL:**
```spl
index=network sourcetype="pan:threat" category="command-and-control" OR category="spyware"
| stats count values(dest_ip) as c2_targets dc(dest_ip) as unique_c2 by src_ip
| sort -count
| lookup dnslookup clientip as src_ip OUTPUT clienthost as src_hostname
```
- **Implementation:** Enable threat prevention and URL filtering on the firewall. Ingest threat logs. Cross-reference with external threat intelligence (STIX/TAXII feeds). Alert immediately on any C2 match.
- **Visualization:** Table (compromised hosts, C2 targets), Sankey diagram (source → C2), Single value (count).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.2.16 · SSL/TLS Decryption Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Decryption failures create blind spots in security inspection. Tracking failures by destination reveals certificate pinning, protocol mismatches, or policy gaps.
- **App/TA:** `Splunk_TA_paloalto`
- **Data Sources:** `sourcetype=pan:decryption`
- **SPL:**
```spl
index=network sourcetype="pan:decryption" action="decrypt-error" OR action="no-decrypt"
| stats count by reason, dest_ip, dest_port
| sort -count
| head 50
```
- **Implementation:** Enable decryption logging. Group failures by reason (unsupported cipher, certificate pinning, policy exclude). Review and update decryption policy based on findings.
- **Visualization:** Bar chart (failure reasons), Table (top undecrypted destinations), Pie chart (by reason).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.2.17 · Firewall Rule Hit Count Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Unused firewall rules increase attack surface and complexity. Identifying zero-hit rules enables rule base cleanup and reduces risk.
- **App/TA:** `Splunk_TA_paloalto`, Splunk_TA_fortinet_fortigate
- **Data Sources:** `sourcetype=pan:traffic`, `sourcetype=fgt_traffic`
- **SPL:**
```spl
index=network sourcetype="pan:traffic"
| stats count as hit_count dc(src_ip) as unique_sources dc(dest_ip) as unique_dests by rule
| sort hit_count
| eval status=if(hit_count=0,"UNUSED",if(hit_count<10,"RARELY_USED","ACTIVE"))
```
- **Implementation:** Collect traffic logs with rule names. Run weekly reports to identify unused rules. Review rules with zero hits over 90 days for removal. Document cleanup actions.
- **Visualization:** Table (rule, hit count, status), Bar chart (hit count distribution), Single value (unused rule count).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.2.18 · Threat Prevention Signature Coverage
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Outdated threat signatures leave the firewall blind to new attacks. Monitoring signature versions ensures security posture is current.
- **App/TA:** `Splunk_TA_paloalto`, Splunk_TA_fortinet_fortigate
- **Data Sources:** `sourcetype=pan:system`, `sourcetype=fgt_event`
- **SPL:**
```spl
index=network sourcetype="pan:system" "threat version" OR "content update"
| rex "installed (?<content_type>threats|antivirus|wildfire) version (?<version>\S+)"
| stats latest(version) as current_version, latest(_time) as last_update by dvc, content_type
| eval days_since_update=round((now()-last_update)/86400,0)
| where days_since_update > 7
```
- **Implementation:** Forward system logs. Alert when signature updates are >7 days old. Compare across firewalls to detect update failures. Schedule weekly compliance reports.
- **Visualization:** Table (firewall, content type, version, days since update), Single value (outdated count).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---


## 5.3 Load Balancers & ADCs

**Primary App/TA:** Splunk Add-on for F5 BIG-IP (`Splunk_TA_f5-bigip`), Citrix ADC TA — Free

---

### UC-5.3.1 · Pool Member Health Status
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Offline pool members reduce capacity. All members down = complete service outage.
- **App/TA:** `Splunk_TA_f5-bigip`, syslog
- **Data Sources:** `sourcetype=f5:bigip:syslog`
- **SPL:**
```spl
index=network sourcetype="f5:bigip:syslog" ("pool member" AND ("down" OR "up" OR "offline"))
| rex "Pool (?<pool>\S+) member (?<member>\S+) monitor status (?<status>\w+)"
| table _time host pool member status | sort -_time
```
- **Implementation:** Forward F5 syslog (LTM log level). Install TA. Alert when pool members go down. Critical alert when all members in a pool offline.
- **Visualization:** Status grid (green/red per member), Table, Timeline.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.3.2 · Virtual Server Availability
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** VIP down = application unreachable. Direct service impact.
- **App/TA:** `Splunk_TA_f5-bigip`, SNMP
- **Data Sources:** `sourcetype=f5:bigip:syslog`, iControl REST
- **SPL:**
```spl
index=network sourcetype="f5:bigip:syslog" "virtual" ("disabled" OR "offline" OR "unavailable")
| table _time host virtual_server status | sort -_time
```
- **Implementation:** Forward syslog. Monitor VIP status via SNMP or iControl REST. Alert on any state change away from "available".
- **Visualization:** Status indicator per VIP, Events timeline (critical).
- **CIM Models:** Web
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(Web.bytes) as total_bytes
  from datamodel=Web.Web
  by Web.src Web.dest Web.uri_path Web.status span=1h
| sort -count
```

---

### UC-5.3.3 · Connection and Throughput Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Capacity
- **Value:** Reveals application demand patterns. Useful for capacity planning and DDoS detection.
- **App/TA:** `Splunk_TA_f5-bigip`, SNMP
- **Data Sources:** SNMP F5-BIGIP-LTM-MIB
- **SPL:**
```spl
index=network sourcetype="snmp:f5"
| timechart span=5m sum(clientside_curConns) as connections by virtual_server
```
- **Implementation:** Poll F5 via SNMP or iControl REST for VIP statistics. Baseline patterns and alert on anomalies.
- **Visualization:** Line chart per VIP, Area chart (throughput), Table.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| sort -bytes
```

---

### UC-5.3.4 · SSL Certificate Expiry
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Expired certificates on load balancers cause browser warnings or connection failures. Most preventable outage.
- **App/TA:** `Splunk_TA_f5-bigip`, custom scripted input
- **Data Sources:** iControl REST API (`/mgmt/tm/sys/crypto/cert`)
- **SPL:**
```spl
index=network sourcetype="f5:certificate_inventory"
| eval days_left=round((expiry_epoch-now())/86400,0) | where days_left<90
| sort days_left | table host cert_name days_left expiry_date
```
- **Implementation:** Scripted input querying iControl REST for certs. Run daily. Alert at 90/60/30/7 day thresholds.
- **Visualization:** Table sorted by days to expiry, Single value (expiring <30d), Status indicator.
- **CIM Models:** N/A

---

### UC-5.3.5 · HTTP Error Rate by VIP
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Backend 5xx errors indicate application issues. Per-VIP tracking isolates degraded services.
- **App/TA:** `Splunk_TA_f5-bigip`, request logging
- **Data Sources:** F5 request logging profile
- **SPL:**
```spl
index=network sourcetype="f5:bigip:ltm:http"
| eval is_error=if(response_code>=500,1,0)
| timechart span=5m sum(is_error) as errors, count as total by virtual_server
| eval error_rate=round(errors/total*100,2) | where error_rate>5
```
- **Implementation:** Enable F5 request logging profile on VIPs. Alert when 5xx rate >5% over 5 minutes.
- **Visualization:** Line chart (error rate), Table (VIP, error rate), Single value.
- **CIM Models:** Web
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  where Web.status>=400
  by Web.src Web.uri_path Web.status span=5m
| sort -count
```

---

### UC-5.3.6 · Response Time Degradation
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Increasing response times indicate backend bottlenecks before they become outages.
- **App/TA:** `Splunk_TA_f5-bigip`
- **Data Sources:** F5 request logging (server_latency)
- **SPL:**
```spl
index=network sourcetype="f5:bigip:ltm:http"
| timechart span=5m perc95(server_latency) as p95 by virtual_server | where p95>2000
```
- **Implementation:** Enable request logging with server-side timing. Track P95 latency per VIP. Alert when exceeding SLA threshold.
- **Visualization:** Line chart (P50/P95/P99), Table, Single value.
- **CIM Models:** Web
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Web.bytes) as avg_bytes count
  from datamodel=Web.Web
  by Web.uri_path Web.status span=5m
| sort -avg_bytes
```

---

### UC-5.3.7 · Session Persistence Issues
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Anomaly
- **Value:** Broken persistence causes lost sessions, shopping carts, or random logouts.
- **App/TA:** `Splunk_TA_f5-bigip`
- **Data Sources:** F5 LTM logs, request logs
- **SPL:**
```spl
index=network sourcetype="f5:bigip:syslog" "persistence" ("failed" OR "expired")
| stats count by virtual_server, persistence_type | sort -count
```
- **Implementation:** Monitor persistence failures. Track same client hitting different backends from request logs.
- **Visualization:** Table, Line chart, Bar chart.
- **CIM Models:** N/A

---

### UC-5.3.8 · WAF Policy Violations
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** WAF violations indicate attacks — SQL injection, XSS, command injection. Trending reveals campaigns.
- **App/TA:** `Splunk_TA_f5-bigip` (ASM)
- **Data Sources:** `sourcetype=f5:bigip:asm:syslog`
- **SPL:**
```spl
index=network sourcetype="f5:bigip:asm:syslog"
| stats count by violation_name, src_ip, request_uri, severity | sort -count
```
- **Implementation:** Enable F5 ASM logging. Dashboard showing top violations, attack sources, and targeted URIs.
- **Visualization:** Table, Bar chart by violation, Map (source IPs), Timeline.
- **CIM Models:** N/A

---

### UC-5.3.9 · Connection Queue Depth
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity, Performance
- **Value:** Growing connection queues indicate backend saturation. Users experience timeouts before the server actually fails.
- **App/TA:** F5 TA (`Splunk_TA_f5-bigip`), Splunk_TA_citrix-netscaler
- **Data Sources:** `sourcetype=f5:bigip:ltm`, SNMP
- **SPL:**
```spl
index=network sourcetype="f5:bigip:ltm"
| stats latest(curConns) as connections, latest(connqDepth) as queue_depth by virtual_server
| where queue_depth > 0 | sort -queue_depth
```
- **Implementation:** Monitor LTM connection queue statistics via iControl REST or SNMP. Alert when queue depth exceeds 0 persistently (>5 min). Correlate with backend pool member health.
- **Visualization:** Line chart (queue depth over time), Table (virtual server, connections, queue), Gauge.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.3.10 · Backend Server Error Code Distribution
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Understanding which backends return 5xx errors helps isolate faulty application instances vs. systemic issues.
- **App/TA:** F5 TA (`Splunk_TA_f5-bigip`), NGINX TA
- **Data Sources:** `sourcetype=f5:bigip:ltm:http`, `sourcetype=nginx:plus:api`
- **SPL:**
```spl
index=network sourcetype="f5:bigip:ltm:http"
| where response_code >= 500
| stats count by pool_member, response_code, virtual_server
| sort -count
```
- **Implementation:** Enable HTTP response logging on the LB. Track 5xx rates per backend member. Alert when a single member's error rate exceeds the pool average by 3x. Auto-disable unhealthy members.
- **Visualization:** Bar chart (errors by backend), Table (member, error code, count), Timechart.
- **CIM Models:** N/A

---

### UC-5.3.11 · Rate Limiting and DDoS Mitigation Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Anomaly
- **Value:** Tracking rate limiting events reveals ongoing attacks and validates that DDoS protections are actively working.
- **App/TA:** F5 TA (`Splunk_TA_f5-bigip`), Splunk_TA_citrix-netscaler
- **Data Sources:** `sourcetype=f5:bigip:asm`, `sourcetype=f5:bigip:ltm`
- **SPL:**
```spl
index=network sourcetype="f5:bigip:asm" attack_type="*dos*" OR violation="Rate Limiting"
| stats count values(src_ip) as source_ips dc(src_ip) as unique_sources by virtual_server, attack_type
| sort -count
```
- **Implementation:** Enable ASM/WAF logging. Configure rate limiting policies per virtual server. Alert on sustained rate limiting events. Track source IP patterns for blocklisting.
- **Visualization:** Timechart (events over time), Table (source IPs, attack types), Single value (blocked requests).
- **CIM Models:** N/A

---

### UC-5.3.12 · iRule/Policy Errors
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** iRule failures cause unexpected traffic handling — potentially bypassing security or routing traffic incorrectly.
- **App/TA:** F5 TA (`Splunk_TA_f5-bigip`)
- **Data Sources:** `sourcetype=f5:bigip:ltm`
- **SPL:**
```spl
index=network sourcetype="f5:bigip:ltm" "TCL error" OR "rule error" OR "aborted"
| rex "Rule (?<rule_name>/\S+)"
| stats count by rule_name, host | sort -count
```
- **Implementation:** Enable iRule logging (sparingly — high volume). Monitor for TCL runtime errors. Alert on any iRule abort events. Review and test iRules in staging before production.
- **Visualization:** Table (rule name, error count, host), Timechart (errors over time).
- **CIM Models:** N/A

---


## 5.4 Wireless Infrastructure

**Primary App/TA:** Splunk Add-on for Cisco Meraki, Cisco WLC syslog, Aruba syslog — Free

---

### UC-5.4.1 · AP Offline Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Offline APs create coverage dead zones. Users lose connectivity in affected areas.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog), WLC syslog
- **Data Sources:** `sourcetype=meraki, WLC events
- **SPL:**
```spl
index=network sourcetype="meraki" type="access point" ("went offline" OR "unreachable")
| table _time host ap_name network status | sort -_time
```
- **Implementation:** For Meraki: configure syslog in Dashboard, or use Meraki API TA. For WLC: forward syslog. Alert when APs go offline. Maintain AP inventory lookup for location context.
- **Visualization:** Map (AP locations with status), Table, Status grid, Single value (APs offline).
- **CIM Models:** N/A

---

### UC-5.4.2 · Client Association Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Failed associations frustrate users and indicate RADIUS/auth issues, RF problems, or AP overload.
- **App/TA:** WLC syslog, Meraki TA
- **Data Sources:** WLC/AP syslog, RADIUS logs
- **SPL:**
```spl
index=network sourcetype="cisco:wlc" ("association" OR "authentication") AND ("fail" OR "reject" OR "denied")
| stats count by ap_name, ssid, reason | sort -count
```
- **Implementation:** Forward WLC/AP syslog. Correlate with RADIUS logs (ISE). Alert on spike in failures per SSID or AP.
- **Visualization:** Table (AP, SSID, reason, count), Bar chart by reason, Timechart.
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

---

### UC-5.4.3 · Channel Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** High channel utilization degrades wireless performance. Identifies congested APs needing channel changes or additional coverage.
- **App/TA:** Meraki API, WLC SNMP
- **Data Sources:** Meraki API, SNMP (CISCO-DOT11-IF-MIB)
- **SPL:**
```spl
index=network sourcetype="meraki:api"
| stats avg(channel_utilization) as util_pct by ap_name, channel, band
| where util_pct > 60 | sort -util_pct
```
- **Implementation:** Poll Meraki RF statistics API or WLC SNMP. Track per-AP channel utilization. Alert when >60% (2.4GHz) or >50% (5GHz).
- **Visualization:** Heatmap (APs by utilization), Table, Line chart (trending).
- **CIM Models:** N/A

---

### UC-5.4.4 · Rogue AP Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Rogue APs are unauthorized and can be used for man-in-the-middle attacks or network bridging.
- **App/TA:** WLC syslog, Meraki TA
- **Data Sources:** WLC/Meraki security events
- **SPL:**
```spl
index=network sourcetype="cisco:wlc" "rogue" ("detected" OR "alert" OR "contained")
| stats count by rogue_mac, detecting_ap, channel | sort -count
```
- **Implementation:** Forward WLC rogue detection events. Enable rogue detection policies. Alert on rogue APs, especially those broadcasting your corporate SSID.
- **Visualization:** Table (rogue MAC, detecting AP, channel), Map, Single value.
- **CIM Models:** N/A

---

### UC-5.4.5 · Client Count Trending
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Client count trending informs capacity planning and AP density decisions.
- **App/TA:** Meraki API, WLC SNMP
- **Data Sources:** WLC/Meraki client data
- **SPL:**
```spl
index=network sourcetype="meraki:api"
| timechart span=1h dc(client_mac) as client_count by ap_name
```
- **Implementation:** Poll client counts via API or SNMP. Track per AP, per SSID, and per building over time.
- **Visualization:** Line chart (clients over time), Table (AP, count), Heatmap.
- **CIM Models:** N/A

---

### UC-5.4.6 · RF Interference Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault, Performance
- **Value:** Radar (DFS), non-WiFi interference, and channel changes degrade wireless quality.
- **App/TA:** WLC syslog, Meraki TA
- **Data Sources:** WLC/AP syslog
- **SPL:**
```spl
index=network sourcetype="cisco:wlc" ("radar" OR "DFS" OR "interference" OR "channel change")
| stats count by ap_name, channel | sort -count
```
- **Implementation:** Forward AP/WLC syslog. Alert on DFS radar events. Track channel change frequency per AP.
- **Visualization:** Table (AP, event type, count), Timeline, Bar chart.
- **CIM Models:** N/A

---

### UC-5.4.7 · Wireless Authentication Trends
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** 802.1X success/failure rates indicate RADIUS health, certificate issues, or expired credentials.
- **App/TA:** WLC syslog, RADIUS/ISE logs
- **Data Sources:** RADIUS logs, WLC auth events
- **SPL:**
```spl
index=network sourcetype="cisco:ise:syslog" ("Passed" OR "Failed") AND "Wireless"
| eval status=if(match(_raw,"Passed"),"Success","Failed")
| timechart span=1h count by status
```
- **Implementation:** Forward ISE/RADIUS authentication logs. Track success/failure ratio over time. Alert on sustained failure rate increase.
- **Visualization:** Stacked bar chart (success vs. failure), Line chart, Single value (failure rate %).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

---

### UC-5.4.8 · RADIUS Authentication Failures
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Mass RADIUS failures prevent wireless users from connecting. Distinguishing between user errors and server issues drives faster resolution.
- **App/TA:** Cisco WLC syslog, Splunk_TA_cisco-ise, `Splunk_TA_cisco-ise`
- **Data Sources:** `sourcetype=cisco:wlc`, `sourcetype=cisco:ise:syslog`
- **SPL:**
```spl
index=network sourcetype="cisco:ise:syslog" "Authentication failed"
| rex "UserName=(?<username>\S+).*?FailureReason=(?<reason>[^;]+)"
| stats count by reason, username | sort -count
| head 20
```
- **Implementation:** Forward ISE/RADIUS logs to Splunk. Alert when failure rate exceeds 20% of attempts. Distinguish between bad credentials, expired certificates, and server timeouts.
- **Visualization:** Bar chart (failure reasons), Table (username, reason, count), Timechart (failure rate).
- **CIM Models:** Authentication
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src span=1h
| where count > 10
```

---

### UC-5.4.9 · Client Roaming Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Anomaly
- **Value:** Poor roaming causes dropped calls, video freezes, and application timeouts. Analyzing roaming patterns identifies coverage gaps.
- **App/TA:** Cisco WLC syslog, Meraki API
- **Data Sources:** `sourcetype=cisco:wlc`, `sourcetype=meraki:api
- **SPL:**
```spl
index=network sourcetype="cisco:wlc" "roam" OR "reassociation"
| transaction client_mac maxspan=1h
| eval roam_count=eventcount-1
| stats avg(roam_count) as avg_roams, max(roam_count) as max_roams by client_mac, ssid
| where avg_roams > 10
```
- **Implementation:** Enable client roaming event logging on the WLC. Track roaming frequency per client. Investigate clients with >10 roams/hour — indicates poor RF design or sticky client behavior.
- **Visualization:** Table (client, SSID, roam count), Heatmap (AP-to-AP roaming), Choropleth (floor plan).
- **CIM Models:** N/A

---

### UC-5.4.10 · Wireless IDS/IPS Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Wireless attacks (deauth floods, evil twin, KRACK) compromise network security. Early detection prevents credential theft and MitM attacks.
- **App/TA:** Cisco WLC syslog, Meraki API
- **Data Sources:** `sourcetype=cisco:wlc`, `sourcetype=meraki:ids`
- **SPL:**
```spl
index=network sourcetype="cisco:wlc" "IDS Signature" OR "wIPS"
| rex "Signature (?<sig_id>\d+).*?(?<sig_name>[^,]+).*?MAC (?<attacker_mac>[0-9a-f:]+)"
| stats count by sig_name, attacker_mac | sort -count
```
- **Implementation:** Enable wireless IDS on the WLC/AP. Forward alerts to Splunk. Alert on deauth floods, rogue AP impersonation, and client spoofing events. Correlate with rogue AP detection.
- **Visualization:** Table (signature, attacker MAC, count), Timeline, Single value (alerts today).
- **CIM Models:** N/A

---

### UC-5.4.11 · Band Steering Effectiveness
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Band steering moves capable clients to 5 GHz, reducing congestion on 2.4 GHz. Measuring effectiveness validates RF policy.
- **App/TA:** Cisco WLC syslog, Meraki API
- **Data Sources:** `sourcetype=cisco:wlc`, `sourcetype=meraki:api
- **SPL:**
```spl
index=network sourcetype="cisco:wlc" "associated"
| eval band=if(match(channel,"^(1|6|11)$"),"2.4GHz","5GHz")
| stats count by band, ssid
| eventstats sum(count) as total by ssid
| eval pct=round(count/total*100,1)
```
- **Implementation:** Collect client association events with channel info. Calculate the ratio of 5 GHz vs 2.4 GHz clients per SSID. Target >70% on 5 GHz for dual-band capable clients.
- **Visualization:** Pie chart (band distribution), Bar chart (by SSID), Timechart (trending).
- **CIM Models:** N/A

---


## 5.5 SD-WAN

**Primary App/TA:** Cisco SD-WAN TA (vManage API), vendor-specific integrations

---

### UC-5.5.1 · Tunnel Health Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Tunnel loss/latency/jitter directly impacts application experience over WAN.
- **App/TA:** ta-cisco-sdwan, vManage API
- **Data Sources:** vManage BFD metrics
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd"
| stats avg(loss_percentage) as loss, avg(latency) as latency, avg(jitter) as jitter by site, tunnel_name
| where loss > 1 OR latency > 100 OR jitter > 30
```
- **Implementation:** Poll vManage API for BFD session statistics. Collect loss, latency, jitter per tunnel. Alert when SLA thresholds exceeded.
- **Visualization:** Line chart (loss/latency/jitter per tunnel), Table, Status grid per site.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.5.2 · Site Availability
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Edge device offline = remote site disconnected from the network.
- **App/TA:** ta-cisco-sdwan, vManage API
- **Data Sources:** vManage device status
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:device"
| where reachability!="reachable"
| table _time site_id hostname system_ip reachability | sort -_time
```
- **Implementation:** Poll vManage device inventory API. Alert when any edge device becomes unreachable. Include site name and location.
- **Visualization:** Map (site locations with status), Table, Status grid.
- **CIM Models:** N/A

---

### UC-5.5.3 · Application SLA Violations
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Detects when business-critical applications aren't meeting performance requirements over the WAN.
- **App/TA:** ta-cisco-sdwan
- **Data Sources:** vManage app-aware routing metrics
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:approute"
| where sla_violation="true"
| stats count by site, app_name, sla_class | sort -count
```
- **Implementation:** Collect app-aware routing statistics from vManage. Alert when critical applications violate their SLA class.
- **Visualization:** Table (site, app, violations), Bar chart by app, Timechart.
- **CIM Models:** N/A

---

### UC-5.5.4 · Path Failover Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Tracks when traffic switches between WAN transports. Frequent failovers indicate unstable links.
- **App/TA:** ta-cisco-sdwan
- **Data Sources:** vManage events
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:events" ("failover" OR "path-change" OR "transport-switch")
| stats count by site, from_transport, to_transport | sort -count
```
- **Implementation:** Collect vManage alarm/event data. Track path changes and failover frequency. Alert on frequent failovers.
- **Visualization:** Table, Sankey diagram (from/to transport), Timeline.
- **CIM Models:** N/A

---

### UC-5.5.5 · Control Plane Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** vSmart/vManage connectivity issues affect policy distribution and overlay routing.
- **App/TA:** ta-cisco-sdwan
- **Data Sources:** vManage control connection logs
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:control"
| where state!="up"
| table _time hostname peer_type peer_system_ip state | sort -_time
```
- **Implementation:** Monitor control connections to vSmart and vManage. Alert on any control connection down.
- **Visualization:** Status panel, Table, Timeline.
- **CIM Models:** N/A

---

### UC-5.5.6 · Certificate Expiration
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** SD-WAN device certificates must be valid for overlay connectivity.
- **App/TA:** ta-cisco-sdwan, vManage API
- **Data Sources:** vManage certificate inventory
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:certificate"
| eval days_left=round((expiry_epoch-now())/86400,0) | where days_left<60
| table hostname system_ip days_left | sort days_left
```
- **Implementation:** Poll vManage for certificate status. Alert at 60/30/7 day thresholds.
- **Visualization:** Table, Single value, Status indicator.
- **CIM Models:** N/A

---

### UC-5.5.7 · Bandwidth Utilization per Site
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Capacity
- **Value:** WAN bandwidth consumption per site enables capacity planning and cost optimization.
- **App/TA:** ta-cisco-sdwan
- **Data Sources:** vManage interface metrics
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:interface"
| timechart span=1h sum(tx_octets) as bytes_out, sum(rx_octets) as bytes_in by site
| eval out_mbps=round(bytes_out*8/3600/1000000,1)
```
- **Implementation:** Collect interface statistics from vManage. Track per-site, per-transport utilization. Use for upgrade decisions.
- **Visualization:** Line chart per site, Table, Stacked area.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| sort -bytes
```

---

### UC-5.5.8 · Jitter and Latency per Tunnel
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Real-time jitter and latency metrics reveal WAN quality degradation before users complain. Critical for voice/video SLAs.
- **App/TA:** ta-cisco-sdwan, Cisco vManage API
- **Data Sources:** `sourcetype=cisco:sdwan:bfd`, `sourcetype=cisco:sdwan:approute`
- **SPL:**
```spl
index=network sourcetype="cisco:sdwan:approute"
| stats avg(latency) as avg_latency, avg(jitter) as avg_jitter, avg(loss_percentage) as avg_loss by local_system_ip, remote_system_ip, local_color
| where avg_latency > 100 OR avg_jitter > 30 OR avg_loss > 1
| sort -avg_latency
```
- **Implementation:** Ingest BFD and app-route statistics from vManage API. Monitor per-tunnel quality metrics. Alert when latency >100ms, jitter >30ms, or loss >1% for business-critical SLAs.
- **Visualization:** Line chart (latency/jitter over time), Table (tunnel, metrics), Gauge (SLA compliance).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.5.9 · Application Routing Decisions
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Validates that SD-WAN policies are steering traffic correctly. Detects policy misconfigurations that route real-time traffic over suboptimal paths.
- **App/TA:** ta-cisco-sdwan, Cisco vManage API
- **Data Sources:** `sourcetype=cisco:sdwan:approute`, `sourcetype=cisco:sdwan:flow`
- **SPL:**
```spl
index=network sourcetype="cisco:sdwan:flow"
| stats sum(octets) as bytes by app_name, local_color, remote_system_ip
| eval MB=round(bytes/1048576,1)
| sort -MB
| head 50
```
- **Implementation:** Collect flow and app-route data from vManage. Verify voice/video uses MPLS, web traffic uses Internet. Alert when critical apps route over non-preferred transports.
- **Visualization:** Sankey diagram (app → transport), Table (app, path, volume), Pie chart.
- **CIM Models:** N/A

---

### UC-5.5.10 · WAN Link Utilization per Transport
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** Unbalanced link utilization wastes expensive MPLS bandwidth while underusing broadband circuits. Enables cost-effective traffic engineering.
- **App/TA:** ta-cisco-sdwan, SNMP
- **Data Sources:** `sourcetype=cisco:sdwan:interface`, SNMP IF-MIB
- **SPL:**
```spl
index=network sourcetype="cisco:sdwan:interface"
| eval util_pct=round(tx_octets*8/speed*100,1)
| stats avg(util_pct) as avg_util, max(util_pct) as peak_util by system_ip, color, interface_name
| where avg_util > 70 | sort -avg_util
```
- **Implementation:** Collect interface stats per WAN transport type (MPLS, Internet, LTE). Compare utilization across links. Alert on >70% sustained utilization. Use for capacity planning.
- **Visualization:** Line chart (utilization per transport), Stacked bar (site comparison), Table.
- **CIM Models:** N/A

---


## 5.6 DNS & DHCP

**Primary App/TA:** Splunk Add-on for Infoblox, Windows DNS/DHCP, BIND syslog — Free

---

### UC-5.6.1 · DNS Query Volume Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** DNS query volume trending supports capacity planning and reveals traffic pattern changes.
- **App/TA:** Splunk_TA_infoblox, Splunk_TA_windows (DNS logs), Pi-hole syslog
- **Data Sources:** `sourcetype=infoblox:dns`, `sourcetype=MSAD:NT6:DNS`
- **SPL:**
```spl
index=dns sourcetype="infoblox:dns" OR sourcetype="MSAD:NT6:DNS"
| timechart span=5m count as qps
```
- **Implementation:** Forward DNS query logs. For Windows DNS: enable analytical logging. For Infoblox: configure syslog output. Track queries per second over time.
- **Visualization:** Line chart (QPS over time), Single value (current QPS), Table.
- **CIM Models:** DNS
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution.DNS
  by DNS.src DNS.query DNS.record_type span=5m
| sort -count
```

---

### UC-5.6.2 · NXDOMAIN Spike Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Anomaly
- **Value:** NXDOMAIN spikes indicate DGA malware (generating random domain lookups), misconfiguration, or DNS infrastructure issues.
- **App/TA:** DNS TAs
- **Data Sources:** DNS query logs
- **SPL:**
```spl
index=dns reply_code="NXDOMAIN" OR rcode="3"
| timechart span=5m count as nxdomain_count
| eventstats avg(nxdomain_count) as avg_nx, stdev(nxdomain_count) as std_nx
| where nxdomain_count > (avg_nx + 3*std_nx)
```
- **Implementation:** Monitor DNS response codes. Baseline NXDOMAIN rates. Alert when exceeding 3 standard deviations. Investigate the querying clients and domain patterns.
- **Visualization:** Line chart with threshold, Table (top NXDOMAIN clients), Bar chart (top queried NX domains).
- **CIM Models:** DNS
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution.DNS
  where DNS.reply_code_id=3
  by DNS.src DNS.query span=1h
| sort -count
```

---

### UC-5.6.3 · SERVFAIL Rate Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** SERVFAIL increases indicate upstream DNS failures, DNSSEC validation issues, or resolver problems.
- **App/TA:** DNS TAs
- **Data Sources:** DNS query logs
- **SPL:**
```spl
index=dns reply_code="SERVFAIL" OR rcode="2"
| timechart span=5m count as servfail | where servfail > 10
```
- **Implementation:** Track SERVFAIL response codes. Alert on increases. Investigate which domains are failing and which resolvers are affected.
- **Visualization:** Line chart, Table (failing domains), Single value.
- **CIM Models:** N/A

---

### UC-5.6.4 · DNS Tunneling Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** DNS tunneling uses DNS queries to exfiltrate data or establish C2 channels, bypassing traditional security controls.
- **App/TA:** DNS TAs
- **Data Sources:** DNS query logs
- **SPL:**
```spl
index=dns
| eval query_len=len(query)
| stats avg(query_len) as avg_len, count as queries, dc(query) as unique_queries by src_ip, domain
| where avg_len > 50 OR queries > 1000
| sort -avg_len
```
- **Implementation:** Monitor for anomalously long DNS queries (>50 chars), high query volumes to single domains, and TXT record queries. Baseline normal DNS patterns.
- **Visualization:** Table (client, domain, query length, volume), Scatter plot, Bar chart.
- **CIM Models:** DNS
- **CIM SPL:**
```spl
| tstats `summariesonly` count dc(DNS.query) as unique_queries
  from datamodel=Network_Resolution.DNS
  by DNS.src span=1h
| where unique_queries > 500
```

---

### UC-5.6.5 · DHCP Scope Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity
- **Value:** Empty DHCP scopes prevent new devices from getting network access.
- **App/TA:** Splunk_TA_windows (DHCP logs), Splunk_TA_infoblox
- **Data Sources:** DHCP server logs, API metrics
- **SPL:**
```spl
index=dhcp sourcetype="DhcpSrvLog" OR sourcetype="infoblox:dhcp"
| stats dc(assigned_ip) as used by scope_name, scope_range
| eval total = scope_end - scope_start
| eval used_pct=round(used/total*100,1) | where used_pct > 90
```
- **Implementation:** For Windows: forward DHCP audit logs + scripted input for scope stats. For Infoblox: use API or syslog. Alert when >90% utilized.
- **Visualization:** Gauge per scope, Table, Bar chart.
- **CIM Models:** N/A

---

### UC-5.6.6 · DHCP Rogue Server Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Rogue DHCP servers assign wrong IPs/gateways, causing network disruption and potential MitM attacks.
- **App/TA:** Network syslog, DHCP snooping logs
- **Data Sources:** DHCP conflict events, switch DHCP snooping
- **SPL:**
```spl
index=network "DHCP" AND ("rogue" OR "conflict" OR "unauthorized" OR "snooping violation")
| table _time host src_ip _raw | sort -_time
```
- **Implementation:** Enable DHCP snooping on switches. Forward syslog. Alert on any rogue DHCP server detection events.
- **Visualization:** Events list (critical), Table, Map.
- **CIM Models:** N/A

---

### UC-5.6.7 · DNS Record Change Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration, Compliance
- **Value:** Unauthorized DNS changes can redirect traffic to attacker infrastructure (DNS hijacking).
- **App/TA:** Splunk_TA_infoblox, DNS update logs
- **Data Sources:** Infoblox audit log, DNS dynamic update logs
- **SPL:**
```spl
index=dns sourcetype="infoblox:audit" ("Added" OR "Deleted" OR "Modified") AND ("record" OR "zone")
| table _time admin record_type record_name record_data action | sort -_time
```
- **Implementation:** Forward DNS server audit logs. Alert on changes to critical domains. Correlate with change tickets.
- **Visualization:** Table (record, action, who, when), Timeline, Single value.
- **CIM Models:** DNS
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution.DNS
  by DNS.src DNS.query DNS.record_type span=5m
| sort -count
```

---

### UC-5.6.8 · DNS Latency Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** DNS latency directly adds to every network connection. Slow DNS = slow everything.
- **App/TA:** Custom scripted input, DNS diagnostic logs
- **Data Sources:** DNS recursive query timing
- **SPL:**
```spl
index=dns sourcetype="dns:latency"
| timechart span=5m avg(response_time_ms) as avg_latency by dns_server
| where avg_latency > 50
```
- **Implementation:** Use scripted input running `dig` queries against DNS servers measuring response time. Or enable DNS analytical logging with timing. Alert when average latency >50ms.
- **Visualization:** Line chart per server, Gauge, Table.
- **CIM Models:** DNS
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution.DNS
  by DNS.src DNS.query DNS.record_type span=5m
| sort -count
```

---

### UC-5.6.9 · DNS Cache Hit Ratio
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Low cache hit ratios indicate either a surge of new queries, cache poisoning attempts, or misconfigured TTLs — all increasing latency and upstream load.
- **App/TA:** Splunk_TA_infoblox, BIND/Unbound logs
- **Data Sources:** `sourcetype=infoblox:dns`, `sourcetype=named`
- **SPL:**
```spl
index=network sourcetype="infoblox:dns"
| eval cache_hit=if(match(message,"cache hit"),1,0), total=1
| timechart span=1h sum(cache_hit) as hits, sum(total) as total
| eval hit_ratio=round(hits/total*100,1) | where hit_ratio < 70
```
- **Implementation:** Enable query logging on DNS resolvers. Track cache hit vs. miss ratio. Alert when hit ratio drops below 70%. Investigate top domains causing misses.
- **Visualization:** Line chart (hit ratio over time), Single value (current ratio), Table (top miss domains).
- **CIM Models:** DNS
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution.DNS
  by DNS.src DNS.query DNS.record_type span=5m
| sort -count
```

---

### UC-5.6.10 · DNSSEC Validation Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** DNSSEC failures can indicate DNS spoofing attempts or misconfigured zones. Monitoring prevents users from being directed to malicious sites.
- **App/TA:** Splunk_TA_infoblox, BIND logs
- **Data Sources:** `sourcetype=infoblox:dns`, `sourcetype=named`
- **SPL:**
```spl
index=network sourcetype="named" "DNSSEC" ("validation failure" OR "SERVFAIL" OR "no valid signature")
| rex "(?<query_domain>[a-zA-Z0-9.-]+\.)/(?<query_type>\w+)"
| stats count by query_domain, query_type | sort -count
```
- **Implementation:** Enable DNSSEC validation logging. Monitor for validation failures by domain. Cross-reference with known domain registrations. Alert on spikes in DNSSEC failures.
- **Visualization:** Table (domain, failure count), Timechart (failure rate), Bar chart.
- **CIM Models:** DNS
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution.DNS
  where DNS.reply_code_id=3
  by DNS.src DNS.query span=1h
| sort -count
```

---

### UC-5.6.11 · DHCP Lease Duration Analysis
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Short lease durations increase DHCP traffic and scope churn. Long leases waste addresses. Optimizing lease times improves IP management.
- **App/TA:** Splunk_TA_infoblox, Windows DHCP logs
- **Data Sources:** `sourcetype=infoblox:dhcp`, `sourcetype=DhcpSrvLog`
- **SPL:**
```spl
index=network sourcetype="infoblox:dhcp" "DHCPACK"
| rex "lease (?<lease_ip>\d+\.\d+\.\d+\.\d+).*?(?<lease_duration>\d+)"
| stats avg(lease_duration) as avg_lease, count as renewals by subnet
| eval avg_hours=round(avg_lease/3600,1) | sort -renewals
```
- **Implementation:** Collect DHCP server logs. Analyze lease durations per scope. Identify scopes with unusually short leases (frequent renewals) or extremely long leases. Adjust based on network type (guest vs. corporate).
- **Visualization:** Table (scope, avg lease, renewal count), Bar chart (renewals by scope).
- **CIM Models:** N/A

---

### UC-5.6.12 · DNS Query Type Distribution
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** Unusual query type distribution (spikes in TXT, MX, or ANY) can indicate DNS tunneling, reconnaissance, or abuse.
- **App/TA:** Splunk_TA_infoblox, Splunk Stream
- **Data Sources:** `sourcetype=infoblox:dns`, `sourcetype=stream:dns`
- **SPL:**
```spl
index=network sourcetype="stream:dns"
| stats count by query_type
| eventstats sum(count) as total
| eval pct=round(count/total*100,2) | sort -count
| head 20
```
- **Implementation:** Capture DNS query types via Splunk Stream or DNS server logs. Baseline normal distribution (typically >80% A/AAAA). Alert on abnormal increases in TXT, NULL, or ANY queries.
- **Visualization:** Pie chart (query type distribution), Timechart (by type), Table.
- **CIM Models:** DNS
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution.DNS
  by DNS.src DNS.query DNS.record_type span=5m
| sort -count
```

---


## 5.7 Network Flow Data

**Primary App/TA:** Splunk App for Stream, Splunk Add-on for NetFlow — Free

---

### UC-5.7.1 · Top Talkers Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Capacity
- **Value:** Identifies top bandwidth consumers. Essential for troubleshooting congestion and capacity planning.
- **App/TA:** Splunk Add-on for NetFlow
- **Data Sources:** `sourcetype=netflow`, sFlow, IPFIX
- **SPL:**
```spl
index=netflow
| stats sum(bytes) as total_bytes by src_ip, dest_ip
| sort -total_bytes | head 20
| eval total_GB=round(total_bytes/1073741824,2)
```
- **Implementation:** Export NetFlow from routers/switches to a NetFlow collector that forwards to Splunk. Install NetFlow TA for field parsing.
- **Visualization:** Table (source, dest, bytes), Sankey diagram, Bar chart.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| sort -bytes
```

---

### UC-5.7.2 · Anomalous Traffic Patterns
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Anomaly
- **Value:** Unusual flows (new protocols, unexpected destinations) indicate compromise, misconfiguration, or shadow IT.
- **App/TA:** Splunk Add-on for NetFlow
- **Data Sources:** `sourcetype=netflow`
- **SPL:**
```spl
index=netflow
| stats dc(dest_port) as unique_ports, dc(dest_ip) as unique_dests by src_ip
| where unique_ports > 100 OR unique_dests > 500
| sort -unique_ports
```
- **Implementation:** Baseline normal flow patterns over 30 days. Alert on new protocol/port combinations, new external destinations, or unusual volume patterns.
- **Visualization:** Table, Scatter plot (ports vs. destinations), Timechart.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.7.3 · Bandwidth by Application
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Capacity
- **Value:** Application-level bandwidth breakdown helps prioritize QoS policies and justify network upgrades.
- **App/TA:** Splunk Add-on for NetFlow (with NBAR)
- **Data Sources:** NetFlow with application identification
- **SPL:**
```spl
index=netflow
| stats sum(bytes) as total_bytes by application
| sort -total_bytes | head 20 | eval GB=round(total_bytes/1073741824,2)
```
- **Implementation:** Enable NBAR (Network-Based Application Recognition) on Cisco routers to export application-tagged NetFlow. Ingest in Splunk.
- **Visualization:** Pie chart (bandwidth by app), Bar chart, Table.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| sort -bytes
```

---

### UC-5.7.4 · East-West Traffic Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Security
- **Value:** Lateral traffic between internal segments reveals application dependencies and detects lateral movement.
- **App/TA:** Splunk Add-on for NetFlow
- **Data Sources:** NetFlow from internal segments
- **SPL:**
```spl
index=netflow
| where cidrmatch("10.0.0.0/8",src_ip) AND cidrmatch("10.0.0.0/8",dest_ip)
| stats sum(bytes) as bytes, count as flows by src_ip, dest_ip, dest_port
| sort -bytes | head 50
```
- **Implementation:** Export NetFlow from internal router/switch interfaces. Analyze internal traffic patterns. Establish baseline for anomaly detection.
- **Visualization:** Chord diagram, Table, Sankey diagram.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.7.5 · Data Exfiltration Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Unusually large outbound transfers to uncommon destinations may be data theft.
- **App/TA:** Splunk Add-on for NetFlow
- **Data Sources:** NetFlow
- **SPL:**
```spl
index=netflow direction="outbound"
| stats sum(bytes) as total_bytes by src_ip, dest_ip
| where total_bytes > 1073741824
| lookup known_destinations dest_ip OUTPUT known
| where isnull(known)
| sort -total_bytes
```
- **Implementation:** Baseline normal outbound transfer volumes per host. Alert when transfers exceed threshold to unknown destinations. Correlate with DNS and firewall logs.
- **Visualization:** Table, Bar chart, Map (destination GeoIP).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.7.6 · Port Scan Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Hosts scanning many ports on targets indicate reconnaissance, worm propagation, or vulnerability scanning.
- **App/TA:** Splunk Add-on for NetFlow
- **Data Sources:** NetFlow
- **SPL:**
```spl
index=netflow
| stats dc(dest_port) as unique_ports by src_ip, dest_ip
| where unique_ports > 50
| sort -unique_ports
```
- **Implementation:** Detect hosts connecting to >50 unique ports on a single target in 5 minutes. Alert with source and target details.
- **Visualization:** Table, Scatter plot, Timeline.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.7.7 · Protocol Distribution Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Understanding protocol mix helps validate network policies and detect unauthorized protocols (e.g., unexpected SSH, RDP, or P2P traffic).
- **App/TA:** Splunk Stream, NetFlow integrator
- **Data Sources:** `sourcetype=netflow`, `sourcetype=stream:tcp`
- **SPL:**
```spl
index=network sourcetype="netflow"
| lookup service_lookup dest_port OUTPUT service_name
| stats sum(bytes) as total_bytes dc(src_ip) as unique_sources by protocol, service_name
| eval GB=round(total_bytes/1073741824,2) | sort -total_bytes
| head 20
```
- **Implementation:** Collect NetFlow/sFlow/IPFIX from routers and switches. Map port numbers to service names via lookup. Baseline protocol distribution. Alert on new protocols or significant shifts.
- **Visualization:** Pie chart (by protocol), Treemap (by service + volume), Timechart.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.7.8 · Multicast Traffic Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Uncontrolled multicast traffic floods switches and consumes bandwidth. Monitoring ensures multicast storms are detected before impacting unicast traffic.
- **App/TA:** Splunk Stream, NetFlow integrator
- **Data Sources:** `sourcetype=netflow`, `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="netflow" dest_ip="224.0.0.0/4"
| stats sum(bytes) as total_bytes, dc(src_ip) as sources by dest_ip
| eval MB=round(total_bytes/1048576,1) | sort -total_bytes
| head 20
```
- **Implementation:** Enable NetFlow on core/distribution switches. Filter for multicast destination range (224.0.0.0/4). Baseline expected multicast groups. Alert on new or high-volume groups.
- **Visualization:** Table (multicast group, volume, sources), Timechart (multicast volume), Bar chart.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.7.9 · Unauthorized VLAN Traffic Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Security
- **Value:** Traffic originating from or destined to unauthorized VLANs indicates misconfigured switch ports, VLAN hopping attacks, or rogue devices.
- **App/TA:** Splunk Stream, NetFlow integrator
- **Data Sources:** `sourcetype=netflow`, `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="netflow"
| lookup vlan_authorization_lookup src_vlan OUTPUT authorized
| where authorized!="yes" OR isnull(authorized)
| stats sum(bytes) as bytes, dc(src_ip) as unique_hosts by src_vlan, input_interface
| sort -bytes
```
- **Implementation:** Map flow data to VLANs via input interface. Maintain a lookup of authorized VLANs per port. Alert on traffic from unauthorized VLANs. Correlate with 802.1X status.
- **Visualization:** Table (VLAN, interface, hosts, volume), Alert panel, Status grid.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.7.10 · Long-Duration Flow Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Anomaly, Security
- **Value:** Extremely long-lived flows may indicate data exfiltration, persistent backdoors, or stuck sessions consuming resources.
- **App/TA:** Splunk Stream, NetFlow integrator
- **Data Sources:** `sourcetype=netflow`
- **SPL:**
```spl
index=network sourcetype="netflow"
| eval duration_min=duration/60
| where duration_min > 60
| stats sum(bytes) as total_bytes, max(duration_min) as max_duration by src_ip, dest_ip, dest_port
| eval GB=round(total_bytes/1073741824,2) | sort -max_duration
| head 20
```
- **Implementation:** Analyze flow records for duration >60 minutes. Cross-reference with known long-lived services (VPN, database replication). Flag unknown long flows for investigation.
- **Visualization:** Table (source, destination, port, duration, bytes), Scatter plot (duration vs. bytes).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---


## 5.8 Network Management Platforms

**Primary App/TA:** Cisco DNA Center TA, Meraki TA, syslog/SNMP trap receivers

---

### UC-5.8.1 · DNA Center Assurance Alerts
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** DNA Center provides AI/ML-driven network issue detection. Centralizing in Splunk enables cross-domain correlation.
- **App/TA:** Splunk-TA-cisco-dnacenter (API)
- **Data Sources:** DNA Center API (issues, events)
- **SPL:**
```spl
index=network sourcetype="cisco:dnac:issues"
| stats count by priority, category, name | sort -priority -count
```
- **Implementation:** Configure DNA Center API integration in Splunk TA. Poll for issues and client health. Alert on P1/P2 issues.
- **Visualization:** Table (issue, priority, category), Bar chart, Single value.
- **CIM Models:** N/A

---

### UC-5.8.2 · Meraki Organization Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Tracks Meraki device status across all networks and organizations from a single pane.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog) (API + syslog)
- **Data Sources:** Meraki Dashboard API, syslog
- **SPL:**
```spl
index=network sourcetype="meraki:api"
| stats count by network, status | eval is_offline=if(status="offline",1,0)
| where is_offline > 0
```
- **Implementation:** Configure Meraki API integration (API key + org ID). Poll device statuses. Forward syslog for events. Dashboard showing organization-wide health.
- **Visualization:** Map (device locations), Table, Status grid, Single value (offline count).
- **CIM Models:** N/A

---

### UC-5.8.3 · SNMP Trap Consolidation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Centralizing SNMP traps from all sources enables cross-tool correlation and reduces monitoring tool sprawl.
- **App/TA:** Splunk Add-on for SNMP (trap receiver)
- **Data Sources:** SNMP traps
- **SPL:**
```spl
index=network sourcetype="snmp:trap"
| stats count by trap_oid, host, severity | sort -count
```
- **Implementation:** Configure Splunk SNMP trap receiver (UDP 162). Map trap OIDs to human-readable names via lookup. Correlate with syslog events from the same device.
- **Visualization:** Table (device, trap, severity), Bar chart, Timeline.
- **CIM Models:** N/A

---

### UC-5.8.4 · Network Device Inventory
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** Up-to-date inventory supports change management, vulnerability tracking, and compliance auditing.
- **App/TA:** Combined sources (NMS APIs, SNMP sysDescr)
- **Data Sources:** NMS discovery, SNMP polling
- **SPL:**
```spl
index=network sourcetype="snmp:system"
| stats latest(sysDescr) as description, latest(sysLocation) as location by host
| table host description location
```
- **Implementation:** Poll SNMP sysDescr, sysName, sysLocation from all devices. Cross-reference with NMS discovery exports. Maintain inventory lookup for enrichment.
- **Visualization:** Table (device, model, location, version), Pie chart (by model/vendor).
- **CIM Models:** N/A

---

### UC-5.8.5 · Network Device Backup Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Missing backups mean a failed device requires manual rebuilding. Tracking backup success ensures rapid disaster recovery.
- **App/TA:** RANCID/Oxidized logs, SolarWinds NCM, custom scripts
- **Data Sources:** `sourcetype=rancid`, `sourcetype=oxidized`
- **SPL:**
```spl
index=network sourcetype="oxidized"
| stats latest(status) as backup_status, latest(_time) as last_backup by device
| eval days_since=round((now()-last_backup)/86400,0)
| where backup_status!="success" OR days_since > 7
| sort -days_since
```
- **Implementation:** Integrate config backup tool (Oxidized/RANCID) logs into Splunk. Track success/failure per device. Alert when a device hasn't been backed up in >7 days.
- **Visualization:** Table (device, status, days since backup), Single value (compliance %), Status grid.
- **CIM Models:** N/A

---

### UC-5.8.6 · ISE Endpoint Posture Compliance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Non-compliant endpoints (missing patches, disabled AV) on the network increase attack surface. ISE posture data enables enforcement visibility.
- **App/TA:** `Splunk_TA_cisco-ise`
- **Data Sources:** `sourcetype=cisco:ise:syslog`
- **SPL:**
```spl
index=network sourcetype="cisco:ise:syslog" "Posture"
| rex "PostureStatus=(?<posture_status>\w+).*?EndpointMacAddress=(?<mac>\S+)"
| stats count by posture_status, mac
| where posture_status="NonCompliant"
| sort -count
```
- **Implementation:** Forward ISE posture assessment logs to Splunk. Track compliant vs. non-compliant endpoints. Alert when non-compliance rate exceeds 10%. Drill down by failure reason.
- **Visualization:** Pie chart (compliant vs non-compliant), Table (non-compliant endpoints), Timechart (compliance trend).
- **CIM Models:** N/A

---

### UC-5.8.7 · Network Configuration Drift Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** Configuration drift from golden standards introduces vulnerabilities and operational inconsistencies. Detecting drift maintains compliance.
- **App/TA:** RANCID/Oxidized, custom diff scripts, DNA Center
- **Data Sources:** `sourcetype=config:diff`, `sourcetype=cisco:dnac`
- **SPL:**
```spl
index=network sourcetype="config:diff"
| rex "device=(?<device>\S+).*?lines_changed=(?<changes>\d+)"
| where changes > 0
| stats sum(changes) as total_changes, count as change_events by device
| sort -total_changes
```
- **Implementation:** Schedule config pulls via Oxidized/RANCID. Diff against golden templates. Ingest diff results into Splunk. Alert on unauthorized changes (outside change windows).
- **Visualization:** Table (device, changes, last modified), Timeline (change events), Single value (devices with drift).
- **CIM Models:** N/A

---

### UC-5.8.8 · SNMP Polling Gap Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Missing SNMP polls create gaps in monitoring data. Detecting polling failures ensures metrics dashboards remain accurate.
- **App/TA:** Splunk core (metadata search)
- **Data Sources:** Any SNMP sourcetype
- **SPL:**
```spl
| tstats count where index=network sourcetype="snmp:*" by host, sourcetype, _time span=10m
| stats range(_time) as time_range, count as poll_count by host, sourcetype
| eval expected_polls=round(time_range/300,0)
| eval gap_pct=round((1-poll_count/expected_polls)*100,1)
| where gap_pct > 20 | sort -gap_pct
```
- **Implementation:** Track SNMP data arrival per device using `tstats`. Compare expected vs. actual poll count. Alert when gap exceeds 20%. Investigate SNMP community/credential issues.
- **Visualization:** Table (device, expected, actual, gap %), Single value (devices with gaps), Heatmap.
- **CIM Models:** N/A

---


## 5.9 Cisco Meraki

**Primary App/TA:** Splunk Add-on for Cisco Meraki (`Splunk_TA_cisco_meraki`) — Free on Splunkbase; `TA-meraki` for syslog

---

### UC-5.9.1 · Wireless Client Association Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Identifies recurring authentication failures and SSID configuration issues that prevent users from connecting to wireless networks.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*Association*" OR signature="*authentication*" status="failure"
| stats count by ap_name, client_mac, reason, signature
| sort - count
```
- **Implementation:** Monitor syslog events from Meraki MR access points for failed association attempts. Correlate with SSID configuration and 802.1X radius responses.
- **Visualization:** Table with top APs/clients by failure count; time-series chart of failures over time by AP.
- **CIM Models:** N/A

---

### UC-5.9.2 · RSSI/Signal Strength Degradation Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Proactively identifies weak WiFi coverage areas and client placement issues before users experience connectivity problems.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| eval rssi_level=case(rssi>=-50, "Excellent", rssi>=-60, "Good", rssi>=-70, "Fair", rssi<-70, "Poor")
| stats avg(rssi) as avg_rssi, min(rssi) as min_rssi, count by ap_name, ssid, rssi_level
| where min_rssi < -70 or avg_rssi < -65
```
- **Implementation:** Ingest Meraki API client data periodically; analyze RSSI distribution by AP and SSID. Set thresholds for "poor" signal (< -70 dBm).
- **Visualization:** Heatmap of RSSI by AP location; histogram of signal strength distribution; gauge charts for coverage quality by SSID.
- **CIM Models:** N/A

---

### UC-5.9.3 · Excessive Client Roaming Activity
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Detects unstable roaming patterns and AP handoff issues that cause latency spikes and dropped connections.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*Roaming*" OR signature="*handoff*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*Roaming*" OR signature="*handoff*")
| stats count as roam_count by client_mac, ap_name
| eventstats sum(roam_count) as total_roams by client_mac
| where total_roams > 20
| sort - total_roams
```
- **Implementation:** Track client handoff events between APs. Alert when a single client roams more than threshold in a 15-minute window.
- **Visualization:** Table of heavy roamers; line chart of roaming frequency by client; network diagram showing roam paths.
- **CIM Models:** N/A

---

### UC-5.9.4 · SSID Performance Ranking and Trend Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Compares performance across multiple SSIDs to identify underperforming networks and optimize deployment strategy.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats avg(connection_duration) as avg_duration, count as client_count, avg(rssi) as avg_rssi by ssid
| eval performance_score=round((avg_rssi+100)*client_count/100, 2)
| sort - performance_score
```
- **Implementation:** Aggregate client connection metrics by SSID. Compare average connection duration, client count, and signal strength.
- **Visualization:** Bar chart comparing SSID performance; sparklines for trend; scorecard showing top/bottom performers.
- **CIM Models:** N/A

---

### UC-5.9.5 · WiFi Channel Utilization and Interference Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Identifies channel congestion and interference sources to optimize channel assignments and reduce co-channel interference.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api sourcetype=meraki
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MR
| stats count by channel, band
| eval utilization_pct=round(count*100/sum(count), 2)
| where utilization_pct > 40
| sort - utilization_pct
```
- **Implementation:** Query API device data for MR access points; track channel assignments. Correlate with interference signature logs.
- **Visualization:** Stacked bar chart of channel utilization by band; channel heatmap over time; interference event timeline.
- **CIM Models:** N/A

---

### UC-5.9.6 · Rogue and Unauthorized AP Detection (Air Marshal)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Identifies unauthorized wireless networks and malicious APs that may represent security threats or network intrusion attempts.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=air_marshal
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=air_marshal signature="*Rogue*" OR signature="*Unauthorized*"
| stats count by ssid, bssid, first_detected, last_seen, threat_level
| where threat_level="high" OR threat_level="critical"
| sort - first_detected
```
- **Implementation:** Enable Air Marshal on MR APs and ingest syslog events. Create alert for new rogue AP detections with risk scoring.
- **Visualization:** Table of detected rogues with threat indicators; map showing rogue AP locations; timeline of detections.
- **CIM Models:** N/A

---

### UC-5.9.7 · Client Device Type Distribution and Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Tracks device types connecting to network for capacity planning, security policy enforcement, and support optimization.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats count as device_count by os_type, device_family
| eval pct=round(device_count*100/sum(device_count), 2)
| sort - device_count
```
- **Implementation:** Use API clients endpoint to retrieve device OS and type information. Aggregate across network.
- **Visualization:** Pie chart of device types; bar chart by OS; treemap of device distribution; trend sparklines.
- **CIM Models:** N/A

---

### UC-5.9.8 · Band Steering Effectiveness Assessment
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Measures effectiveness of steering clients from 2.4GHz to 5GHz bands to reduce congestion and improve performance.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats count as client_count by band
| eval band_ratio=round(client_count*100/sum(client_count), 2)
| fields band, client_count, band_ratio
```
- **Implementation:** Query clients API to get current band distribution. Compare against expected ratio for band steering policy.
- **Visualization:** Gauge showing 5GHz percentage; pie chart of band distribution; trend line showing steering progress.
- **CIM Models:** N/A

---

### UC-5.9.9 · Failed DHCP Assignments and IP Pool Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Detects DHCP server failures and IP pool exhaustion that prevent new clients from obtaining addresses.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*DHCP*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*DHCP*" (signature="*failure*" OR signature="*NACK*")
| stats count as failure_count by ap_name, signature
| where failure_count > 5
| sort - failure_count
```
- **Implementation:** Monitor syslog for DHCP NACK and failure events. Alert on sustained failure rate.
- **Visualization:** Table of DHCP failures by AP; time-series showing failure spike; alert dashboard.
- **CIM Models:** N/A

---

### UC-5.9.10 · 802.1X Authentication Failures and Radius Issues
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Identifies authentication server problems, credential issues, and 802.1X configuration mismatches.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*802.1X*" OR signature="*Radius*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*802.1X*" OR signature="*Radius*" OR signature="*authentication*")
| stats count as auth_failures by client_mac, ap_name, signature
| eventstats sum(auth_failures) as total_failures by client_mac
| where total_failures > 10
| sort - total_failures
```
- **Implementation:** Ingest 802.1X and RADIUS-related syslog events. Correlate with RADIUS server logs.
- **Visualization:** Table of failing clients; time-series of auth failures; client-level detail dashboard.
- **CIM Models:** N/A

---

### UC-5.9.11 · DNS Resolution Performance and Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Monitors DNS query resolution times and failures to identify misconfiguration or server issues affecting user experience.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*DNS*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*DNS*" resolution_time=*
| stats avg(resolution_time) as avg_dns_time, max(resolution_time) as max_dns_time, count by ap_name
| where avg_dns_time > 100
```
- **Implementation:** Extract DNS query timing from syslog events. Set SLA thresholds (e.g., <100ms average).
- **Visualization:** Gauge showing average DNS time; histogram of query times; slow query detail table.
- **CIM Models:** N/A

---

### UC-5.9.12 · Wireless Latency Analysis by SSID and Location
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Identifies latency patterns across network to optimize AP placement, channel allocation, and client routing.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" latency=*
| stats avg(latency) as avg_latency, max(latency) as max_latency, count by ssid, ap_name
| eval latency_sla="OK"
| eval latency_sla=if(avg_latency > 50, "Warning", latency_sla)
| eval latency_sla=if(avg_latency > 100, "Critical", latency_sla)
```
- **Implementation:** Use API clients endpoint with latency metric. Aggregate by SSID and AP location.
- **Visualization:** Heatmap of latency by AP; line chart of latency trends; SLA compliance dashboard.
- **CIM Models:** N/A

---

### UC-5.9.13 · Splash Page Engagement and Redirection Analytics
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks guest network splash page performance and user acceptance rates for marketing and network access purposes.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*Splash*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*Splash*"
| stats count as redirect_count by result, ap_name
| eval acceptance_rate=round(count*100/sum(count), 2)
```
- **Implementation:** Capture splash page interaction events from syslog. Track accepts vs. denies.
- **Visualization:** Pie chart of acceptance rates; funnel chart of splash interactions; time-series trending.
- **CIM Models:** N/A

---

### UC-5.9.14 · Multicast and Broadcast Storm Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Anomaly
- **Value:** Identifies multicast/broadcast flooding that degrades wireless performance across multiple client devices.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=flow
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=flow dest_ip="255.255.255.255" OR dest_mac="ff:ff:ff:ff:ff:ff"
| stats sum(sent_bytes) as total_bytes, count as pkt_count by ap_name, src_mac
| where pkt_count > 1000
| sort - pkt_count
```
- **Implementation:** Monitor broadcast/multicast flows in syslog. Set thresholds for abnormal packet rates.
- **Visualization:** Table of broadcast sources; time-series of broadcast packets; alert threshold dashboard.
- **CIM Models:** N/A

---

### UC-5.9.15 · Wireless Health Score Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Provides a composite health metric across all APs to facilitate executive reporting and trend analysis.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MR
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MR
| stats avg(health_score) as network_health, min(health_score) as worst_ap, count(eval(health_score<80)) as unhealthy_aps by network_id
| eval health_status=if(network_health >= 85, "Healthy", if(network_health >= 70, "Degraded", "Critical"))
```
- **Implementation:** Pull health_score metric from MR devices API. Aggregate across network.
- **Visualization:** Gauge of overall health; bar chart of individual AP health; trend sparkline; KPI dashboard.
- **CIM Models:** N/A

---

### UC-5.9.16 · Connected Client Count Trending and Capacity Planning
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Tracks client density by AP and SSID for capacity planning and performance optimization.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats count as client_count by ap_name, ssid
| eval capacity_pct=round(client_count*100/30, 2)
| where capacity_pct > 70
| sort - client_count
```
- **Implementation:** Query clients API to count connected devices. Track over time.
- **Visualization:** Bubble chart of capacity by AP; stacked bar of clients by SSID; capacity gauge.
- **CIM Models:** N/A

---

### UC-5.9.17 · Top Talker Analysis and Bandwidth Hogs
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Identifies bandwidth-intensive clients and applications to enforce QoS policies and prevent network congestion.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=flow
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=flow
| stats sum(sent_bytes) as upload_bytes, sum(received_bytes) as download_bytes by client_mac, application
| eval total_bytes=upload_bytes+download_bytes
| sort - total_bytes
| head 20
```
- **Implementation:** Analyze flow records from syslog; track data usage by client and application.
- **Visualization:** Table of top talkers; horizontal bar chart of data usage; Sankey diagram of flows.
- **CIM Models:** N/A

---

### UC-5.9.18 · Connection Duration and Session Quality
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Analyzes typical session lengths and stability to identify problematic SSIDs or time-based issues.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" connection_duration=*
| stats avg(connection_duration) as avg_session_time, min(connection_duration) as min_session, max(connection_duration) as max_session by ssid
| eval session_quality=if(avg_session_time > 3600, "Stable", "Short")
```
- **Implementation:** Extract connection_duration from clients API. Aggregate by SSID and time of day.
- **Visualization:** Histogram of session durations; time-of-day heatmap; SSID comparison chart.
- **CIM Models:** N/A

---

### UC-5.9.19 · AP Uptime and Availability Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Ensures all access points are online and operational; alerts on unexpected AP outages.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MR
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MR
| stats latest(status) as ap_status, latest(last_status_change) as last_change by ap_name, ap_mac
| where ap_status="offline"
```
- **Implementation:** Monitor device status API for all MR devices. Alert on status="offline".
- **Visualization:** Status table with last seen time; uptime percentage gauge; event alert dashboard.
- **CIM Models:** N/A

---

### UC-5.9.20 · Mesh Network Link Quality and Backhaul Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Monitors wireless mesh backhaul links to ensure reliability of remote AP connections.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MR sourcetype=meraki type=security_event
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MR mesh_link_quality=*
| stats avg(mesh_link_quality) as avg_link_quality by ap_name, upstream_ap
| where avg_link_quality < 70
| sort avg_link_quality
```
- **Implementation:** Query MR device API for mesh_link_quality metric. Alert on degraded quality (<70%).
- **Visualization:** Network topology showing link quality; color-coded links; detail table with metrics.
- **CIM Models:** N/A

---

### UC-5.9.21 · Guest Network Access Patterns and Usage
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Tracks guest network adoption, usage patterns, and peak times for network provisioning.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api ssid="guest*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" ssid="guest"
| stats count as guest_users by _time
| timechart avg(guest_users) as avg_concurrent_guests
```
- **Implementation:** Filter clients API results for guest SSIDs. Track concurrent count over time.
- **Visualization:** Time-series of guest users; daily/weekly heatmap; trend dashboard.
- **CIM Models:** N/A

---

### UC-5.9.22 · WiFi Geolocation and Location Analytics
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Uses Cisco Meraki location services to track foot traffic patterns and heat maps in physical spaces.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api location_data=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" ap_name=*
| stats count as foot_traffic by ap_name, floor
| geom geo_from_metric lat, lon
```
- **Implementation:** Use Meraki location API to get AP-based location estimates. Map to floor/zone.
- **Visualization:** Heat map by physical location; AP heat map overlay; zone traffic comparison.
- **CIM Models:** N/A

---

### UC-5.9.23 · Port Utilization and Congestion Alerts
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Identifies port saturation and congestion events that require capacity upgrades or load balancing adjustments.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MS
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MS
| stats avg(port_utilization) as avg_util, max(port_utilization) as max_util by switch_name, port_id
| where max_util > 80
| sort - max_util
```
- **Implementation:** Query MS switch device API for port utilization metrics. Alert on sustained >80% utilization.
- **Visualization:** Table of congested ports; timeline showing peak congestion; port utilization heatmap.
- **CIM Models:** N/A

---

### UC-5.9.24 · Power over Ethernet (PoE) Consumption Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Monitors PoE power allocation to prevent over-subscription and ensure sufficient power for all devices.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MS
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MS poe_consumption=*
| stats sum(poe_consumption) as total_power_watts, avg(poe_consumption) as avg_power by switch_name
| eval power_capacity_pct=round(total_power_watts*100/1000, 2)
| where power_capacity_pct > 80
```
- **Implementation:** Pull poe_consumption metrics from MS device API. Aggregate by switch.
- **Visualization:** Gauge showing power utilization percentage; stacked bar of PoE by port; capacity dashboard.
- **CIM Models:** N/A

---

### UC-5.9.25 · Spanning Tree Protocol (STP) Topology Changes
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Alerts on unexpected STP topology changes that indicate link failures or network configuration issues.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*STP*" OR signature="*topology*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*STP*" OR signature="*topology*")
| stats count as change_count by switch_name, change_type
| where change_count > 3
```
- **Implementation:** Monitor STP-related syslog events. Alert on excessive topology changes.
- **Visualization:** Timeline of topology changes; table of affected switches; alert dashboard.
- **CIM Models:** N/A

---

### UC-5.9.26 · Port Security Violations and Rogue Device Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Detects unauthorized MAC addresses and port security breaches that indicate potential network intrusion.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*Port Security*" OR signature="*Unauthorized MAC*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*Port Security*" OR signature="*Unauthorized*")
| stats count as violation_count by switch_name, port_id, mac_address
| where violation_count > 0
| sort - violation_count
```
- **Implementation:** Monitor port security violation events from syslog. Create alert for each unique violation.
- **Visualization:** Table of violations; timeline of events; network detail with affected ports.
- **CIM Models:** N/A

---

### UC-5.9.27 · Switch Interface Up/Down Events and Link Flapping
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Identifies port flapping, cable issues, and unstable link states that cause intermittent connectivity.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*link*" OR signature="*Interface*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*link*" OR signature="*Interface*" OR signature="*up*" OR signature="*down*")
| stats count as event_count by switch_name, port_id
| eval flap_rate=round(event_count/24, 2)
| where flap_rate > 2
```
- **Implementation:** Track interface up/down state changes over 24 hours. Alert on flapping (>2 changes/hour).
- **Visualization:** Time-series showing flap events; table of affected ports; link state history.
- **CIM Models:** N/A

---

### UC-5.9.28 · VLAN Configuration Mismatches and Tagging Violations
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Detects VLAN configuration errors and tagging violations that disrupt network segmentation.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MS sourcetype=meraki
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*VLAN*"
| stats count as vlan_error_count by switch_name, vlan_id
| where vlan_error_count > 5
```
- **Implementation:** Monitor VLAN-related error events. Cross-reference with API device VLAN config.
- **Visualization:** Table of VLAN issues; timeline of configuration changes; network diagram with VLAN details.
- **CIM Models:** N/A

---

### UC-5.9.29 · MAC Flooding and Bridge Table Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Detects MAC address table exhaustion and flooding attacks that could overwhelm switch resources.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*MAC*" OR signature="*bridge*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*MAC*" OR signature="*flood*")
| stats count as flood_count by switch_name, port_id
| where flood_count > 50
```
- **Implementation:** Monitor MAC-related syslog events. Alert on suspicious patterns.
- **Visualization:** Table of affected switches/ports; time-series of flood events; alert dashboard.
- **CIM Models:** N/A

---

### UC-5.9.30 · DHCP Snooping Violations
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Detects unauthorized DHCP servers and spoofing attempts that disrupt network address allocation.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*DHCP Snooping*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*DHCP*Snooping*"
| stats count as violation_count by switch_name, port_id, server_ip
| where violation_count > 0
```
- **Implementation:** Enable DHCP snooping on MS switches. Monitor syslog for violations.
- **Visualization:** Table of violations; timeline of events; affected port details.
- **CIM Models:** N/A

---

### UC-5.9.31 · Broadcast Storm Detection and Mitigation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Anomaly
- **Value:** Identifies and alerts on broadcast storms that can freeze network performance across all switches.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*broadcast*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*broadcast*"
| stats sum(packet_count) as broadcast_packets by switch_name, port_id
| where broadcast_packets > 10000
```
- **Implementation:** Monitor broadcast traffic thresholds. Alert on sustained high broadcast rates.
- **Visualization:** Real-time alert dashboard; time-series of broadcast packets; affected port list.
- **CIM Models:** N/A

---

### UC-5.9.32 · Switch CPU and Memory Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Monitors switch hardware resources to prevent performance degradation or device failure.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MS
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MS
| stats avg(cpu_usage) as avg_cpu, max(cpu_usage) as peak_cpu, avg(memory_usage) as avg_mem by switch_name
| where avg_cpu > 75 OR avg_mem > 80
```
- **Implementation:** Query MS device API for CPU and memory metrics. Alert on threshold breaches.
- **Visualization:** Gauge charts for CPU/memory; time-series trends; capacity planning dashboard.
- **CIM Models:** N/A

---

### UC-5.9.33 · Stack Unit and Redundancy Health
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Ensures switch stacking configuration remains healthy and redundancy is not compromised.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MS stack_id=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MS stack_id=*
| stats count as stack_members, count(eval(status="offline")) as offline_members by stack_id
| where offline_members > 0
```
- **Implementation:** Monitor stack member status via device API. Alert on member removal or failure.
- **Visualization:** Table of stack members and status; redundancy gauge; alert dashboard.
- **CIM Models:** N/A

---

### UC-5.9.34 · Trunk Link Utilization and Performance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Monitors inter-switch and uplink trunk utilization to identify bandwidth constraints.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MS
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MS port_type="trunk"
| stats avg(port_utilization) as avg_trunk_util, max(port_utilization) as peak_util by switch_name, port_id
| where peak_util > 70
| sort - peak_util
```
- **Implementation:** Query MS API for trunk port utilization. Alert on sustained high utilization.
- **Visualization:** Trunk link utilization heatmap; timeline showing peak demand; capacity planning chart.
- **CIM Models:** N/A

---

### UC-5.9.35 · QoS Queue Drops and Priority Violations
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Detects QoS queue overflow and drops that indicate traffic priority issues.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*QoS*" OR signature="*queue*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*QoS*" OR signature="*queue*" OR signature="*drop*")
| stats sum(packets_dropped) as total_drops by switch_name, queue_id
| where total_drops > 1000
```
- **Implementation:** Monitor QoS-related syslog events and drops. Alert on significant drop rates.
- **Visualization:** Table of drops by queue; time-series of drop events; traffic distribution pie chart.
- **CIM Models:** N/A

---

### UC-5.9.36 · Port Access Control List (ACL) Hits and Block Events
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Tracks ACL rule hits to monitor policy enforcement and identify anomalous traffic.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*ACL*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*ACL*" action="block"
| stats count as block_count by switch_name, src_mac, dest_mac
| sort - block_count
```
- **Implementation:** Monitor ACL deny/block events from syslog. Track frequently blocked source/destinations.
- **Visualization:** Table of blocked traffic; timeline of ACL hits; top blocked addresses chart.
- **CIM Models:** N/A

---

### UC-5.9.37 · Cable Test Results and Port Diagnostics
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Analyzes cable integrity test results to identify wiring faults before they cause outages.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*cable*" OR signature="*diagnostic*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*cable*" OR signature="*diagnostic*")
| stats count as test_count by switch_name, port_id, test_result
| where test_result="FAIL"
```
- **Implementation:** Periodically run cable tests on switch ports. Ingest results into syslog.
- **Visualization:** Table of failed cable tests; port detail with diagnostic results; failure timeline.
- **CIM Models:** N/A

---

### UC-5.9.38 · Uplink Health and Failover Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Monitors primary/secondary uplink status to detect failover events and connection issues.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*Uplink*" OR signature="*failover*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*Uplink*" OR signature="*failover*")
| stats count as failover_count by uplink_name, event_type
| where failover_count > 0
```
- **Implementation:** Monitor uplink status change events in syslog. Alert on failover.
- **Visualization:** Uplink status dashboard; failover event timeline; connection health gauge.
- **CIM Models:** N/A

---

### UC-5.9.39 · VPN Tunnel Status and Path Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Ensures all site-to-site and client VPN tunnels remain active and operative.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=vpn sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=vpn
| stats latest(status) as tunnel_status, latest(last_changed) as status_change_time by tunnel_id, remote_site
| where tunnel_status="down" OR tunnel_status="unstable"
```
- **Implementation:** Monitor VPN tunnel state from syslog and API. Alert on status != "up".
- **Visualization:** VPN tunnel status matrix; site connectivity map; tunnel health sparklines.
- **CIM Models:** N/A

---

### UC-5.9.40 · Content Filtering and URL Category Blocks
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Tracks blocked URLs and categories to monitor policy compliance and identify misclassified content.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=urls action="blocked"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=urls action="blocked"
| stats count as block_count by url_category, src_ip
| sort - block_count
| head 20
```
- **Implementation:** Ingest URL filtering events from MX syslog. Categorize by policy.
- **Visualization:** Table of top blocked categories; bar chart by category; user detail table.
- **CIM Models:** N/A

---

### UC-5.9.41 · IDS/IPS Alert Analysis and Threat Scoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Identifies and prioritizes intrusion detection alerts for investigation and threat response.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=ids_alert
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=ids_alert
| stats count as alert_count by signature, priority, src_ip, dest_ip
| eval severity=case(priority=1, "Critical", priority=2, "High", priority=3, "Medium", 1=1, "Low")
| where priority <= 2
| sort - alert_count
```
- **Implementation:** Ingest IDS/IPS alert events from MX appliance. Enrich with threat intelligence.
- **Visualization:** Alert timeline; severity breakdown pie chart; alert detail table; threat map.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.9.42 · Malware Detection and AMP File Reputation Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Detects and tracks file-based threats to respond quickly to potential malware infections.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*malware*" OR signature="*AMP*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*malware*" OR signature="*AMP*")
| stats count as malware_count by src_ip, threat_name, file_name
| where malware_count > 0
| sort - malware_count
```
- **Implementation:** Enable AMP on MX appliance. Ingest malware detection events.
- **Visualization:** Threat timeline; infected hosts table; file reputation detail; incident dashboard.
- **CIM Models:** N/A

---

### UC-5.9.43 · Firewall Rule Hit Analysis and Top Denied Flows
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Identifies top denied flows to optimize firewall rules and detect policy violations.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=flow action="deny"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=flow action="deny"
| stats count as deny_count by firewall_rule, src_ip, dest_ip, dest_port
| sort - deny_count
| head 20
```
- **Implementation:** Analyze firewall deny events from flow logs. Correlate with rules.
- **Visualization:** Top denied flows table; denial timeline; source/dest distribution heatmap.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.9.44 · Traffic Shaping Effectiveness and QoS Policy Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Measures the impact of traffic shaping policies on bandwidth distribution and priority.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=flow sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=flow priority_queue=*
| stats sum(bytes) as total_bytes, avg(latency) as avg_latency by priority_queue
| eval efficiency=round(total_bytes/sum(total_bytes)*100, 2)
```
- **Implementation:** Extract priority_queue field from flow logs. Measure bandwidth by priority.
- **Visualization:** Stacked bar chart of bandwidth by priority; latency by QoS class; efficiency gauge.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| sort -bytes
```

---

### UC-5.9.45 · Site-to-Site VPN Latency and Performance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Monitors latency and jitter on VPN tunnels to ensure quality of critical business traffic.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=vpn sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=vpn latency=*
| stats avg(latency) as avg_vpn_latency, max(jitter) as max_jitter by tunnel_id, remote_site
| where avg_vpn_latency > 50
```
- **Implementation:** Extract VPN latency and jitter metrics. Monitor tunnel performance.
- **Visualization:** Gauge of VPN latency; latency trend line; jitter comparison chart.
- **CIM Models:** N/A

---

### UC-5.9.46 · Client VPN Connections and Remote Access Patterns
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Tracks client VPN usage patterns for remote workers and identifies problematic connections.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=vpn client_vpn=true
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=vpn client_vpn=true
| stats count as connection_count, avg(duration) as avg_session_length by user_id, src_ip
| where connection_count > 10
```
- **Implementation:** Filter VPN logs for client connections. Track by user and source IP.
- **Visualization:** Connected users timeline; session duration histogram; geography map of remote users.
- **CIM Models:** N/A

---

### UC-5.9.47 · NAT Pool Usage and Exhaustion Alerts
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Monitors NAT pool utilization to prevent address exhaustion that could block outbound traffic.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" nat_pool_usage=*
| stats max(nat_pool_usage) as peak_nat_usage, count by nat_pool_id
| eval nat_capacity_pct=round(peak_nat_usage*100/254, 2)
| where nat_capacity_pct > 80
```
- **Implementation:** Query appliance API for NAT pool metrics. Alert on >80% utilization.
- **Visualization:** Gauge of NAT pool usage; capacity timeline; pool exhaustion alert dashboard.
- **CIM Models:** N/A

---

### UC-5.9.48 · BGP Peering Status and Route Stability
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Ensures BGP peers remain established and routing remains stable for multi-ISP designs.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*BGP*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*BGP*" (signature="*neighbor*" OR signature="*route*")
| stats count as bgp_event_count by bgp_neighbor, event_type
| where bgp_event_count > 5
```
- **Implementation:** Monitor BGP event syslog. Alert on neighbor state changes.
- **Visualization:** BGP peer status table; route change timeline; peering stability gauge.
- **CIM Models:** N/A

---

### UC-5.9.49 · DHCP Pool Exhaustion and Address Allocation Issues
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Alerts when DHCP pools approach depletion to prevent clients from obtaining IP addresses.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" dhcp_pool=*
| stats latest(addresses_available) as available_ips, latest(pool_size) as total_pool by vlan_id
| eval allocation_pct=round((total_pool-available_ips)*100/total_pool, 2)
| where allocation_pct > 85
```
- **Implementation:** Query appliance API for DHCP metrics by VLAN. Alert on >85% allocation.
- **Visualization:** DHCP pool gauge per VLAN; timeline of pool usage; alert dashboard.
- **CIM Models:** N/A

---

### UC-5.9.50 · Threat Intelligence Correlation and IoC Matching
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Correlates network traffic with threat intelligence databases to detect known malicious IPs and domains.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event OR type=urls OR type=flow
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" (type=security_event OR type=urls OR type=flow)
| lookup threat_intelligence_list src_ip as src_ip OUTPUTNEW threat_name, threat_severity
| where threat_severity="high" OR threat_severity="critical"
| stats count as hit_count by src_ip, dest_ip, threat_name
| sort - hit_count
```
- **Implementation:** Create threat intelligence lookup table. Correlate with network events.
- **Visualization:** IoC match timeline; threat severity breakdown; affected hosts table.
- **CIM Models:** N/A

---

### UC-5.9.51 · Geo-Blocking Event Tracking and Geographic Policy Enforcement
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Tracks geo-blocking policy enforcement to verify compliance with data residency and export controls.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=urls action="blocked" country=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=urls action="blocked"
| lookup geo_ip.csv dest_ip OUTPUTNEW country, city
| stats count as block_count by country
| sort - block_count
```
- **Implementation:** Ingest URL logs with GeoIP enrichment. Track blocks by geography.
- **Visualization:** Geo-block map; country block count chart; policy compliance dashboard.
- **CIM Models:** N/A

---

### UC-5.9.52 · Application Visibility and Network Application Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Identifies top applications and protocols on network to understand usage patterns and detect anomalies.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=flow application=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=flow application=*
| stats sum(bytes) as app_bytes, count as flow_count by application, application_category
| eval app_bandwidth_pct=round(app_bytes*100/sum(app_bytes), 2)
| sort - app_bytes
| head 20
```
- **Implementation:** Extract application field from flow logs. Aggregate by app and category.
- **Visualization:** App bandwidth pie chart; top apps bar chart; bandwidth timeline by app.
- **CIM Models:** N/A

---

### UC-5.9.53 · Bandwidth by Application and Department
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Tracks bandwidth consumption by application and business unit for chargeback and optimization.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=flow
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=flow
| lookup department_by_ip.csv src_ip OUTPUTNEW department
| stats sum(sent_bytes) as upload_mb, sum(received_bytes) as download_mb by application, department
| eval total_mb=upload_mb+download_mb
| sort - total_mb
```
- **Implementation:** Correlate flows with IP-to-department mapping. Aggregate by app and dept.
- **Visualization:** Stacked bar of bandwidth by dept/app; heatmap of app usage per dept.
- **CIM Models:** N/A

---

### UC-5.9.54 · WAN Link Quality Monitoring (Jitter, Latency, Packet Loss)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Continuously monitors WAN quality metrics to detect link degradation before impacting users.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api wan_metrics=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" uplink=*
| stats avg(latency) as avg_latency, avg(jitter) as avg_jitter, avg(packet_loss) as avg_loss by uplink_id
| eval link_quality=case(avg_loss > 5, "Critical", avg_latency > 100, "Poor", avg_jitter > 50, "Fair", 1=1, "Good")
```
- **Implementation:** Query appliance API for uplink WAN metrics. Monitor quality KPIs.
- **Visualization:** Uplink quality scorecard; latency/jitter/loss timeline; quality gauge per uplink.
- **CIM Models:** N/A

---

### UC-5.9.55 · Internet Uplink Failover Events and Recovery Time
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Tracks failover events, recovery time, and uplink behavior to ensure high availability.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*failover*" OR signature="*recovery*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*failover*" OR signature="*recovery*")
| stats count as failover_count, latest(recovery_time) as recovery_duration by uplink_id, failure_reason
| where failover_count > 0
```
- **Implementation:** Monitor failover and recovery events from syslog. Calculate recovery MTTR.
- **Visualization:** Failover timeline; recovery time gauge; uplink failure cause pie chart.
- **CIM Models:** N/A

---

### UC-5.9.56 · Cellular Modem Failover Activation and Usage
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Tracks cellular backup activation to monitor failover effectiveness and cellular data usage.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*cellular*" OR signature="*4G*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*cellular*" OR signature="*4G*" OR signature="*LTE*")
| stats count as cellular_events, sum(data_usage_mb) as total_cellular_data by event_type
| where total_cellular_data > 0
```
- **Implementation:** Ingest cellular failover events. Track data consumption.
- **Visualization:** Cellular usage timeline; failover event table; data usage gauge.
- **CIM Models:** N/A

---

### UC-5.9.57 · Warm Spare Failover and Appliance Redundancy
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Ensures warm spare failover mechanism is operational and redundancy is maintained.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*warm spare*" OR signature="*HA*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*warm spare*" OR signature="*HA*" OR signature="*redundancy*")
| stats latest(ha_status) as redundancy_status, count as status_change_count by appliance_pair
| where ha_status!="active/standby"
```
- **Implementation:** Monitor HA/warm spare events. Alert on status != "active/standby".
- **Visualization:** HA status dashboard; failover timeline; redundancy health gauge.
- **CIM Models:** N/A

---

### UC-5.9.58 · Auto VPN Path Changes and Tunnel Switching
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Tracks automatic VPN path optimization to understand tunnel usage and convergence behavior.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=vpn signature="*Auto VPN*" OR signature="*path change*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=vpn (signature="*Auto VPN*" OR signature="*path change*")
| stats count as path_change_count by tunnel_id, new_path, old_path
| where path_change_count > 3
```
- **Implementation:** Monitor Auto VPN path optimization events. Alert on excessive changes.
- **Visualization:** Path change timeline; tunnel path change distribution; convergence analysis.
- **CIM Models:** N/A

---

### UC-5.9.59 · Connection Rate Analysis and DOS Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Detects denial of service attacks by analyzing abnormal connection establishment rates.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=flow protocol="tcp" tcp_flags="SYN"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=flow protocol="tcp" tcp_flags="SYN"
| timechart count as new_connections by src_ip
| where new_connections > 1000
```
- **Implementation:** Monitor TCP SYN rate by source IP. Alert on anomalous connection rates.
- **Visualization:** Connection rate timeline; source IP detail table; DOS alert dashboard.
- **CIM Models:** N/A

---

### UC-5.9.60 · Data Loss Prevention (DLP) Event Analysis
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Detects and alerts on sensitive data transmission to prevent data exfiltration.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*DLP*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*DLP*"
| stats count as dlp_match_count by src_ip, dest_ip, dlp_policy, data_type
| where dlp_match_count > 0
| sort - dlp_match_count
```
- **Implementation:** Enable DLP on MX appliance. Ingest DLP match events.
- **Visualization:** DLP incident timeline; data type breakdown; source/destination detail.
- **CIM Models:** N/A

---

### UC-5.9.61 · SSL/TLS Certificate Expiration Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Monitors SSL certificate expiration dates on all network devices to prevent outages.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" certificate_expiry=*
| eval days_until_expiry=round((strptime(certificate_expiry, "%Y-%m-%d")-now())/86400, 0)
| where days_until_expiry < 30
| stats latest(days_until_expiry) as days_left by device_name, device_type
| sort days_left
```
- **Implementation:** Query device API for certificate expiry dates. Alert on <30 days.
- **Visualization:** Expiration countdown gauge; timeline of expiring certs; alert table.
- **CIM Models:** N/A

---

### UC-5.9.62 · Firmware Update Compliance and Version Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Ensures all network devices run supported firmware versions and patches.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats latest(firmware_version) as current_fw, count as device_count by device_type
| lookup recommended_firmware.csv device_type OUTPUTNEW recommended_fw
| where current_fw != recommended_fw
```
- **Implementation:** Query device API for firmware versions. Compare to recommended baseline.
- **Visualization:** Firmware version table by device type; compliance percentage gauge; outdated device list.
- **CIM Models:** N/A

---

### UC-5.9.63 · API Call Rate Monitoring and Rate Limit Alerts
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Monitors API usage to prevent rate limit hits and optimize automation efficiency.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api:*"
| timechart count as api_calls by source, endpoint
| eval call_rate=api_calls/60
| where call_rate > 9
```
- **Implementation:** Log all API calls with timestamps. Monitor call rate by endpoint.
- **Visualization:** API call timeline; rate limit gauge; endpoint usage breakdown.
- **CIM Models:** N/A

---

### UC-5.9.64 · License Expiration Tracking and Renewal Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Ensures licenses don't expire unexpectedly and features remain available.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" license_expiry=*
| eval days_until_expire=round((strptime(license_expiry, "%Y-%m-%d")-now())/86400, 0)
| stats latest(days_until_expire) as days_left, latest(license_expiry) as expiry_date by license_type, organization
| where days_left < 90
| sort days_left
```
- **Implementation:** Query organization API for license expiry. Alert on <90 days.
- **Visualization:** License expiration countdown; renewal timeline; license detail table.
- **CIM Models:** N/A

---

### UC-5.9.65 · Network Device Inventory and Change Audit
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Configuration
- **Value:** Maintains accurate inventory of network devices and tracks hardware/software changes.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats count as device_count by device_type, network_id
| append [search index=cisco_network sourcetype="meraki:api" | stats count as org_count]
| fillnull device_count value=0
```
- **Implementation:** Query devices API to build current inventory. Track additions/removals.
- **Visualization:** Inventory summary table; device count by type pie chart; change log timeline.
- **CIM Models:** N/A

---

### UC-5.9.66 · Admin Activity Logging and Access Control Audit
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Tracks administrator actions and logins for compliance and security auditing.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*admin*" OR signature="*login*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*admin*" OR signature="*login*")
| stats count as admin_action_count by admin_user, action_type, timestamp
| where admin_action_count > 0
```
- **Implementation:** Enable admin audit logging. Ingest login and action events.
- **Visualization:** Admin activity timeline; action type breakdown; user activity detail table.
- **CIM Models:** N/A

---

### UC-5.9.67 · Admin Privilege Changes and Permission Escalation
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Detects unauthorized privilege changes and permission escalation attempts.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*privilege*" OR signature="*permission*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*privilege*" OR signature="*permission*")
| stats count as priv_change_count by admin_user, old_role, new_role
| where priv_change_count > 0
```
- **Implementation:** Monitor privilege and role change events. Alert on escalations.
- **Visualization:** Privilege change timeline; role change audit table; escalation alert dashboard.
- **CIM Models:** N/A

---

### UC-5.9.68 · Alert Volume Trending and Alert Fatigue Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Analyzes alert volume trends to optimize alerting rules and reduce false positives.
- **App/TA:** `Splunk_TA_cisco_meraki` (webhooks)
- **Data Sources:** `sourcetype=meraki:webhook
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:webhook"
| timechart count as alert_count by alert_type
| eval alert_ratio=alert_count/sum(alert_count)
```
- **Implementation:** Ingest webhook alerts. Track volume and types over time.
- **Visualization:** Alert volume timeline; alert type pie chart; trend sparklines.
- **CIM Models:** N/A

---

### UC-5.9.69 · Network Health Score Aggregation and Executive Reporting
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Provides high-level network health metric for executive dashboards and trend reporting.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats avg(health_score) as device_health, count(eval(status="offline")) as offline_count by network_id
| eval network_health=round(device_health - (offline_count*5), 2)
| eval health_status=case(network_health >= 85, "Healthy", network_health >= 70, "Degraded", 1=1, "Critical")
```
- **Implementation:** Aggregate device health scores. Calculate composite network score.
- **Visualization:** Network health gauge; health trend sparkline; status KPI dashboard.
- **CIM Models:** N/A

---

### UC-5.9.70 · Device Online/Offline Status Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Tracks device connectivity status to quickly identify and respond to device failures.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats latest(status) as device_status, latest(last_status_change) as status_change_time, count(eval(status="offline")) as offline_count by network_id
| eval offline_pct=round(offline_count*100/count, 2)
| where offline_count > 0
```
- **Implementation:** Poll devices API for status. Alert on offline devices.
- **Visualization:** Device status table; offline count gauge; status change timeline.
- **CIM Models:** N/A

---

### UC-5.9.71 · Multi-Organization Comparison and Benchmarking
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Compares metrics across organizations to identify best practices and outliers.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats avg(health_score) as avg_health, count as device_count by organization
| sort - avg_health
```
- **Implementation:** Aggregate metrics across multiple organizations. Create comparison views.
- **Visualization:** Organization comparison bar chart; health rank table; benchmark line chart.
- **CIM Models:** N/A

---

### UC-5.9.72 · Configuration Change Window Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Ensures configuration changes only occur within approved maintenance windows.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*config*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*config*"
| eval hour=strftime(_time, "%H")
| stats count as config_change_count by hour
| eval window_compliant=if(hour>=22 OR hour<6, "Yes", "No")
| where window_compliant="No" AND config_change_count > 0
```
- **Implementation:** Monitor configuration change events. Check against maintenance windows.
- **Visualization:** Change compliance timeline; out-of-window change alert table.
- **CIM Models:** N/A

---

### UC-5.9.73 · Webhook Delivery Failure Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Ensures webhook notifications reach integrations and alerts don't get lost.
- **App/TA:** `Splunk_TA_cisco_meraki` (webhooks)
- **Data Sources:** `sourcetype=meraki:webhook status="failure" OR status="error"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:webhook" (status="failure" OR status="error")
| stats count as failure_count, latest(error_message) as last_error by webhook_id, organization
| where failure_count > 5
```
- **Implementation:** Log webhook delivery attempts. Alert on sustained failures.
- **Visualization:** Webhook failure timeline; failure cause breakdown; affected org list.
- **CIM Models:** N/A

---

### UC-5.9.74 · API Error Rate and Endpoint Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Monitors API endpoint health and error rates to ensure automation reliability.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api (http_status_code=4* OR http_status_code=5*)
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api:*" (http_status_code=4* OR http_status_code=5*)
| stats count as error_count, values(http_status_code) as status_codes by endpoint, method
| eval error_rate=round(error_count*100/total_requests, 2)
| where error_rate > 5
```
- **Implementation:** Log API responses with status codes. Alert on error rate threshold.
- **Visualization:** API error timeline; endpoint error breakdown; error rate gauge.
- **CIM Models:** N/A

---

### UC-5.9.75 · Dashboard Configuration and Export Backup
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Tracks dashboard configuration backups to enable disaster recovery and configuration review.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" backup_timestamp=*
| stats latest(backup_timestamp) as last_backup, count as backup_count by organization
| eval backup_age_days=round((now()-strptime(backup_timestamp, "%Y-%m-%d"))/86400, 0)
| where backup_age_days > 7
```
- **Implementation:** Periodically backup organization configurations. Track backup history.
- **Visualization:** Last backup timestamp by org; backup recency gauge; backup history timeline.
- **CIM Models:** N/A

---

### UC-5.9.76 · Camera Uptime and Availability Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Monitors video surveillance system availability to ensure continuous monitoring coverage.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api device_type=MV sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MV
| stats latest(status) as camera_status, latest(last_status_change) as status_change by camera_name, location
| where camera_status="offline"
```
- **Implementation:** Monitor MV camera status via device API. Alert on offline cameras.
- **Visualization:** Camera status map; offline camera list; availability percentage gauge.
- **CIM Models:** N/A

---

### UC-5.9.77 · Video Retention and Cloud Archive Storage Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Tracks cloud storage usage for video archives to manage costs and ensure retention SLA.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" storage_usage=*
| stats sum(storage_usage) as total_storage_gb by camera_id, retention_days
| eval storage_pct=round(total_storage_gb*100/1000, 2)
| where storage_pct > 80
```
- **Implementation:** Query camera API for storage metrics. Alert on >80% utilization.
- **Visualization:** Storage utilization gauge; retention timeline; storage trend chart.
- **CIM Models:** N/A

---

### UC-5.9.78 · Motion Detection Events and Alert Volume Analysis
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Analyzes motion detection event patterns to optimize camera sensitivity and reduce false alerts.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*motion*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*motion*"
| timechart count as motion_events by camera_name
| eval daily_avg=round(motion_events/1440, 2)
```
- **Implementation:** Ingest motion detection events. Track volume and patterns.
- **Visualization:** Motion detection timeline; heat map by time of day; camera comparison chart.
- **CIM Models:** N/A

---

### UC-5.9.79 · Camera Video Quality Score and Stream Health
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Monitors video quality metrics to identify network or hardware issues affecting video feeds.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" quality_score=*
| stats avg(quality_score) as avg_quality, min(quality_score) as min_quality by camera_name
| where avg_quality < 80
| sort avg_quality
```
- **Implementation:** Query camera API for quality_score metric. Alert on <80 average.
- **Visualization:** Quality score gauge per camera; quality trend line; affected camera list.
- **CIM Models:** N/A

---

### UC-5.9.80 · Cloud Archive Status and Backup Validation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Ensures video archives are successfully uploaded to cloud and backup integrity is maintained.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api archive_status=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" archive_status=*
| stats latest(archive_status) as backup_status, latest(last_archive_time) as last_backup by camera_id
| where archive_status != "success"
```
- **Implementation:** Check camera API archive status. Alert on failures.
- **Visualization:** Archive status table; last backup time timeline; failure alert dashboard.
- **CIM Models:** N/A

---

### UC-5.9.81 · Video Stream Connection Errors and Quality Issues
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Detects video stream connection failures that prevent remote viewing or recording.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*stream*" OR signature="*connection*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*stream*" OR signature="*connection*")
| stats count as error_count by camera_name, error_type
| where error_count > 10
```
- **Implementation:** Monitor stream connection events. Alert on error spikes.
- **Visualization:** Connection error timeline; affected camera list; error type breakdown.
- **CIM Models:** N/A

---

### UC-5.9.82 · Camera Firmware Compliance and Update Management
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Ensures all cameras run current firmware with security patches.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api device_type=MV
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MV
| stats latest(firmware_version) as camera_fw, count as camera_count
| lookup recommended_camera_fw.csv camera_model OUTPUTNEW recommended_version
| where camera_fw != recommended_version
```
- **Implementation:** Query MV device API for firmware. Compare to recommended baseline.
- **Visualization:** Firmware version table; compliance percentage gauge; outdated camera list.
- **CIM Models:** N/A

---

### UC-5.9.83 · Night Mode Effectiveness and Low-Light Performance
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Monitors camera performance in low-light conditions to ensure night surveillance effectiveness.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api night_mode=true
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" night_mode=true
| stats avg(quality_score) as night_quality, count as night_mode_events by camera_name
| where night_quality < 75
```
- **Implementation:** Track camera performance during night mode. Monitor quality metrics.
- **Visualization:** Night mode quality gauge; low-light performance timeline; affected camera list.
- **CIM Models:** N/A

---

### UC-5.9.84 · People Counting Trends and Occupancy Analytics
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Uses camera people counting to track foot traffic trends for space utilization and facility planning.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api people_count=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" people_count=*
| timechart avg(people_count) as avg_occupancy by location
```
- **Implementation:** Extract people_count metrics from camera API. Aggregate by location and time.
- **Visualization:** Occupancy heat map by time of day; location comparison bar chart; trend sparkline.
- **CIM Models:** N/A

---

### UC-5.9.85 · Temperature Sensor Threshold Alerts
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Alerts when environmental temperatures exceed safe thresholds to prevent equipment damage.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*temperature*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*temperature*"
| stats latest(temperature) as current_temp, min(temperature) as min_temp, max(temperature) as max_temp by sensor_location
| where current_temp > 30 OR current_temp < 5
```
- **Implementation:** Monitor temperature sensor threshold alerts from syslog. Alert on exceedance.
- **Visualization:** Temperature gauge per location; trend timeline; alert dashboard.
- **CIM Models:** N/A

---

### UC-5.9.86 · Humidity Monitoring and Dew Point Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Monitors humidity levels to ensure optimal conditions for equipment and prevent moisture damage.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*humidity*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*humidity*"
| stats latest(humidity) as current_humidity, avg(humidity) as avg_humidity by sensor_location
| eval dew_point="calculated_value"
```
- **Implementation:** Monitor humidity sensor data. Calculate dew point for condensation risk.
- **Visualization:** Humidity gauge per location; humidity vs temperature correlation; trend chart.
- **CIM Models:** N/A

---

### UC-5.9.87 · Door Open/Close Event Detection and Alerts
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks door access events for security and facility monitoring.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*door*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*door*" (action="open" OR action="close")
| stats count as door_events, latest(timestamp) as last_event by door_location, action
```
- **Implementation:** Monitor door sensor events. Alert on unusual access patterns.
- **Visualization:** Door event timeline; access pattern analysis; alert table.
- **CIM Models:** N/A

---

### UC-5.9.88 · Water Leak Detection and Flood Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Immediately detects water leaks to prevent equipment damage and business interruption.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*water*" OR signature="*leak*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*water*" OR signature="*leak*")
| stats count as leak_events, latest(timestamp) as last_detection by sensor_location
| where leak_events > 0
```
- **Implementation:** Monitor water/leak detection sensors. Create critical alert.
- **Visualization:** Leak alert dashboard; sensor location map; event timeline.
- **CIM Models:** N/A

---

### UC-5.9.89 · Power Monitoring and Electrical Load Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Tracks electrical power consumption and load to identify anomalies and plan upgrades.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" sensor_type="power" power_watts=*
| stats avg(power_watts) as avg_power, max(power_watts) as peak_power by location
| eval power_capacity_pct=round(peak_power*100/15000, 2)
```
- **Implementation:** Query sensor API for power metrics. Track consumption and peaks.
- **Visualization:** Power consumption gauge; peak load timeline; capacity planning chart.
- **CIM Models:** N/A

---

### UC-5.9.90 · Air Quality and CO2 Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Monitors indoor air quality to ensure safe working conditions.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api sensor_type="air_quality"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" sensor_type="air_quality" co2_ppm=*
| stats latest(co2_ppm) as current_co2, avg(co2_ppm) as avg_co2 by location
| where current_co2 > 1000
```
- **Implementation:** Monitor CO2 and air quality sensor data. Alert on high levels.
- **Visualization:** CO2 level gauge per location; trend timeline; air quality status chart.
- **CIM Models:** N/A

---

### UC-5.9.91 · Ambient Noise Level Monitoring and Trend Analysis
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks noise levels to ensure comfortable working environment and detect anomalies.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api sensor_type="noise"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" sensor_type="noise" noise_db=*
| stats avg(noise_db) as avg_noise, max(noise_db) as peak_noise by location
| timechart avg(noise_db) by location
```
- **Implementation:** Ingest noise sensor data. Track by location and time of day.
- **Visualization:** Noise level gauge; time-of-day heat map; location comparison chart.
- **CIM Models:** N/A

---

### UC-5.9.92 · Indoor Climate Trending and HVAC Optimization
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Analyzes temperature and humidity trends to optimize HVAC system efficiency.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api sensor_type IN ("temperature", "humidity")
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" sensor_type IN ("temperature", "humidity")
| stats avg(value) as avg_value by sensor_type, location
| timechart avg(value) by sensor_type
```
- **Implementation:** Correlate temperature and humidity data. Identify optimization opportunities.
- **Visualization:** Climate trend line chart; comfort zone indicator; energy efficiency analysis.
- **CIM Models:** N/A

---

### UC-5.9.93 · Environmental Sensor Battery Health and Replacement Alerts
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Tracks sensor battery levels to ensure sensors remain operational and schedule replacements.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" battery_level=*
| stats latest(battery_level) as battery_pct by sensor_id, location
| where battery_pct < 20
| sort battery_pct
```
- **Implementation:** Query sensor API for battery metrics. Alert on <20% battery.
- **Visualization:** Battery health table; battery trend timeline; replacement alert dashboard.
- **CIM Models:** N/A

---

### UC-5.9.94 · Sensor Connectivity and Heartbeat Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Ensures all sensors maintain connectivity and operational status.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api"
| stats latest(last_report) as last_checkin by sensor_id
| eval hours_since_checkin=round((now()-strptime(last_report, "%Y-%m-%dT%H:%M:%S"))/3600, 1)
| where hours_since_checkin > 2
```
- **Implementation:** Query sensor API for last report time. Alert on missing heartbeats.
- **Visualization:** Sensor status table; last heartbeat timeline; offline sensor list.
- **CIM Models:** N/A

---

### UC-5.9.95 · Device Compliance Status and Policy Enforcement
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Ensures all managed devices comply with security policies and configuration standards.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api compliance_status=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" (compliance_status="noncompliant" OR compliance_status="unknown")
| stats count as noncompliant_count by os_type, compliance_reason
| eval compliance_pct=round(noncompliant_count*100/total_devices, 2)
```
- **Implementation:** Query device compliance status from SM API. Alert on noncompliance.
- **Visualization:** Compliance status table; compliance percentage gauge; noncompliant device list.
- **CIM Models:** N/A

---

### UC-5.9.96 · Mobile Device Enrollment and MDM Status Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Tracks device enrollment status to ensure mobile device management coverage.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki:api enrollment_status=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" enrollment_status IN ("enrolled", "pending", "failed")
| stats count as device_count by enrollment_status, os_type
| eval enrollment_pct=round(count*100/sum(count), 2)
```
- **Implementation:** Query device enrollment status. Track pending and failed enrollments.
- **Visualization:** Enrollment status pie chart; pending enrollment timeline; device count by OS.
- **CIM Models:** N/A

---

### UC-5.9.97 · Geofencing Alerts and Location-Based Policy Triggers
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Uses geofencing to detect when devices leave secure zones and trigger location-based policies.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*geofence*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*geofence*"
| stats count as geofence_event_count by device_id, zone_name, event_type
| where event_type="left_zone"
```
- **Implementation:** Monitor geofence event triggers. Track zone entry/exit by device.
- **Visualization:** Geofence event timeline; zone heat map; affected device list.
- **CIM Models:** N/A

---

### UC-5.9.98 · Mobile Security Policy Violations and App Restrictions
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Detects policy violations and restricted app usage attempts.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*policy*" OR signature="*app*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*policy*" OR signature="*app*") violation="true"
| stats count as violation_count by device_id, policy_name, violation_type
| where violation_count > 5
```
- **Implementation:** Monitor security policy violation events. Alert on repeated violations.
- **Visualization:** Policy violation timeline; violation type breakdown; affected device list.
- **CIM Models:** N/A

---

### UC-5.9.99 · Lost Mode Device Activation and Recovery Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks activation of lost mode on devices to ensure recovery protocols are working.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*lost mode*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*lost mode*"
| stats count as lost_mode_count, latest(timestamp) as last_activation by device_id, activation_reason
```
- **Implementation:** Monitor lost mode activation events. Track recovery time.
- **Visualization:** Lost mode event timeline; affected device table; recovery status dashboard.
- **CIM Models:** N/A

---

### UC-5.9.100 · Mobile App Deployment Success Rate and Distribution Status
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Tracks app deployment success and identifies devices with failed or incomplete deployments.
- **App/TA:** `Splunk_TA_cisco_meraki` (API)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*app*deployment*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*app*deployment*"
| stats count as deployment_count, count(eval(status="success")) as success_count, count(eval(status="failed")) as failed_count by app_name
| eval success_rate=round(success_count*100/deployment_count, 2)
| where success_rate < 95
```
- **Implementation:** Monitor app deployment status events. Alert on low success rates.
- **Visualization:** Deployment success rate gauge; app deployment timeline; failure detail table.
- **CIM Models:** N/A

---

### UC-5.9.101 · Cellular Gateway Signal Strength Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Monitors cellular signal strength to ensure reliable backup connectivity.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MG
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MG
| stats avg(signal_strength) as avg_signal, min(signal_strength) as min_signal by cellular_gateway_id
| eval signal_quality=case(avg_signal > -90, "Excellent", avg_signal > -110, "Good", 1=1, "Poor")
```
- **Implementation:** Query MG device API for signal metrics. Alert on degraded signal.
- **Visualization:** Signal strength gauge; trend timeline; cellular quality status.
- **CIM Models:** N/A

---

### UC-5.9.102 · Cellular Data Usage and Overage Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Tracks cellular data consumption to manage carrier costs and prevent overages.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MG data_usage=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MG data_usage=*
| stats sum(data_usage) as total_data_usage_mb by cellular_gateway_id
| eval overage_alert=if(total_data_usage_mb > 100000, "Yes", "No")
```
- **Implementation:** Query MG API for data usage metrics. Track monthly consumption.
- **Visualization:** Data usage gauge per gateway; consumption timeline; overage alert table.
- **CIM Models:** N/A

---

### UC-5.9.103 · Carrier Connection Health and Network Performance
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Monitors carrier connectivity and network performance metrics for backup internet links.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*cellular*" OR signature="*carrier*"
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*cellular*" OR signature="*carrier*")
| stats count as event_count by event_type, carrier_name
| where event_type="connection_error" OR event_type="network_error"
```
- **Implementation:** Monitor carrier connection and network events. Alert on issues.
- **Visualization:** Carrier health timeline; connection error table; network performance gauge.
- **CIM Models:** N/A

---

### UC-5.9.104 · SIM Status and Plan Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Tracks SIM card status and plan expiration to ensure continuous cellular connectivity.
- **App/TA:** `Splunk_TA_cisco_meraki` (API), `TA-meraki` (syslog)
- **Data Sources:** `sourcetype=meraki:api device_type=MG sim_status=*
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" device_type=MG
| stats latest(sim_status) as sim_status, latest(plan_expiry) as expiry_date by gateway_id, sim_id
| eval days_until_expire=round((strptime(plan_expiry, "%Y-%m-%d")-now())/86400, 0)
| where sim_status != "active" OR days_until_expire < 30
```
- **Implementation:** Query MG API for SIM status and plan expiry. Alert before expiration.
- **Visualization:** SIM status table; plan expiry countdown; renewal alert dashboard.
- **CIM Models:** N/A

---


