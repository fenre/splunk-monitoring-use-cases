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

**Primary App/TA:** Cisco Networks Add-on for Splunk (`TA-cisco_ios`, Splunkbase 1352), SNMP Modular Input — Free

---

### UC-5.1.1 · Interface Up/Down Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** A hard-down uplink or WAN port can isolate an entire site or VLAN; flapping often manifests as application timeouts and VoIP drops before a ticket names 'the network.' Treat each DOWN on a trunk or uplink as a potential SEV-1 for that site; treat more than 3 transitions in 10 minutes as a stability risk requiring immediate investigation of optics, cabling, or port configuration.
- **App/TA:** `TA-cisco_ios`, syslog
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.1.4 · BGP Peer State Changes
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** BGP session drops cause routing convergence, potentially making networks unreachable.
- **App/TA:** `TA-cisco_ios`, syslog
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
- **App/TA:** `TA-cisco_ios`, syslog
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
- **App/TA:** `TA-cisco_ios`, syslog
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
- **App/TA:** `TA-cisco_ios`, syslog
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
- **App/TA:** `TA-cisco_ios`, syslog
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
- **App/TA:** `TA-cisco_ios`, SNMP CISCO-ENVMON-MIB
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
- **App/TA:** `TA-cisco_ios`, syslog
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
- **App/TA:** `TA-cisco_ios`, syslog
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%SEC-6-IPACCESSLOGP"
| rex "list (?<acl>\S+) denied (?<proto>\w+) (?<src>\d+\.\d+\.\d+\.\d+)"
| stats count by host, acl, src, proto | sort -count
```
- **Implementation:** Enable ACL logging (`log` keyword). Forward syslog. Dashboard showing top denied sources and trends.
- **Visualization:** Table, Bar chart by source IP, Timechart.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.action="blocked"
  by All_Traffic.src All_Traffic.dest All_Traffic.dest_port span=1h
| eval bytes=bytes_in+bytes_out
| sort -count
```

---

### UC-5.1.14 · SNMP Authentication Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Failed SNMP auth indicates unauthorized polling or reconnaissance.
- **App/TA:** `TA-cisco_ios`, syslog
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
- **Data Sources:** `sourcetype=cisco:ios`
- **SPL:**
```spl
index=network sourcetype="cisco:ios" "%SNMP-3-AUTHFAIL"
| rex "from (?<src>\S+)" | stats count by host, src | sort -count
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
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
- **App/TA:** `TA-cisco_ios`, syslog
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
- **App/TA:** SNMP Modular Input, IF-MIB, `TA-cisco_ios`
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
- **App/TA:** `TA-cisco_ios`, syslog
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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
- **App/TA:** `TA-cisco_ios`, syslog
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
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

### UC-5.1.24 · Network Device Configuration Backup Freshness
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration, Compliance
- **Value:** Last backup age tracking; stale backups risk config loss during failures.
- **App/TA:** Custom (Oxidized/RANCID output, SolarWinds NCM equivalent)
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
- **Data Sources:** Backup system logs (timestamps of last successful backup per device)
- **SPL:**
```spl
index=network sourcetype=config_backup OR sourcetype=oxidized OR sourcetype=rancid
| stats latest(_time) as last_backup by host, device_hostname
| eval age_hours=round((now()-last_backup)/3600,1)
| where age_hours > 24 OR isnull(last_backup)
| table device_hostname host last_backup age_hours
```
- **Implementation:** Ingest backup job output from Oxidized, RANCID, or NCM. Parse success/failure and timestamp. Create lookup or index with device→last_backup mapping. Alert when last successful backup exceeds 24 hours. Schedule backup jobs daily; verify Splunk receives logs via scripted input or syslog.
- **Visualization:** Table (device, last backup, age), Single value (devices with stale backup), Gauge (hours since last backup).
- **CIM Models:** N/A

---

### UC-5.1.25 · Network Configuration Drift Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Configuration, Security
- **Value:** Running config differs from baseline/golden config.
- **App/TA:** Custom scripted input (diff output from RANCID/Oxidized vs golden)
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
- **Data Sources:** Config diff output, Git commit logs from network config repo
- **SPL:**
```spl
index=network sourcetype=config_drift OR sourcetype=git:commit
| search "diff" OR "drift" OR "changed" OR "modified"
| rex "device[=:]\s*(?<device>\S+)" | rex "lines?\s*(?<lines_changed>\d+)"
| stats count as drift_events, values(diff_summary) as changes by device, host
| where drift_events > 0
| table device host drift_events changes
```
- **Implementation:** Run diff (e.g., `diff running golden`) via Oxidized hooks or custom script. Ingest diff output or Git commit metadata. Store golden configs in Git; compare after each backup. Alert on any non-whitelisted drift. Use `git diff` or `rancid -d` output as sourcetype.
- **Visualization:** Table (device, drift count, summary), Timeline (drift events), Single value (devices with drift).
- **CIM Models:** N/A

---

### UC-5.1.26 · Network Device Firmware Version Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Devices running unapproved or EOL firmware versions.
- **App/TA:** Splunk_TA_cisco, SNMP TA (sysDescr)
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
- **Data Sources:** SNMP sysDescr, show version output
- **SPL:**
```spl
index=network sourcetype=snmp:sysinfo OR sourcetype=cisco:ios:version
| rex field=_raw "Version (?<ios_version>\S+)" | rex field=sysDescr "Version (?<ios_version>\S+)"
| lookup firmware_compliance ios_version OUTPUT approved eol_date
| where approved!="yes" OR (eol_date!="" AND strptime(eol_date,"%Y-%m-%d")<now())
| table host ios_version approved eol_date
```
- **Implementation:** Poll SNMP sysDescr or ingest `show version` via scripted input. Create lookup table (ios_version, approved, eol_date) from vendor EOL/EOS bulletins. Alert on non-approved or past-EOL versions. Update lookup quarterly.
- **Visualization:** Table (device, version, status), Bar chart (version distribution), Single value (non-compliant count).
- **CIM Models:** N/A

---

### UC-5.1.27 · Interface Error Rate Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Fault
- **Value:** CRC, runts, giants, input/output errors as rate over time.
- **App/TA:** SNMP modular input
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
- **Data Sources:** IF-MIB (ifInErrors, ifOutErrors), EtherLike-MIB
- **SPL:**
```spl
index=network sourcetype=snmp:interface
| streamstats current=f last(ifInErrors) as prev_in, last(ifOutErrors) as prev_out, last(_time) as prev_time by host, ifDescr
| eval delta_in=ifInErrors-coalesce(prev_in,0), delta_out=ifOutErrors-coalesce(prev_out,0)
| eval interval_sec=_time-prev_time | where interval_sec>0 AND interval_sec<900
| eval in_err_rate=round(delta_in/interval_sec*60,2), out_err_rate=round(delta_out/interval_sec*60,2)
| where in_err_rate>0 OR out_err_rate>0
| timechart span=5m avg(in_err_rate) as in_errors_per_min, avg(out_err_rate) as out_errors_per_min by host
```
- **Implementation:** Poll IF-MIB (ifInErrors, ifOutErrors) and EtherLike-MIB (dot3StatsFCSErrors) every 300s. Use streamstats for delta calculation. Alert when error rate exceeds threshold (e.g., >1/min on uplinks). Exclude admin-down interfaces.
- **Visualization:** Line chart (error rate over time), Table (host, interface, rate), Heatmap.
- **CIM Models:** N/A

---

### UC-5.1.28 · STP Topology Change Rate
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Frequent topology changes indicating Layer 2 instability.
- **App/TA:** SNMP modular input, syslog
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
- **Data Sources:** BRIDGE-MIB (dot1dStpTopChanges), syslog STP events
- **SPL:**
```spl
index=network (sourcetype=snmp:stp OR sourcetype="cisco:ios") ("dot1dStpTopChanges" OR "%SPANTREE-5-TOPOTCHANGE" OR "%SPANTREE-2-ROOTCHANGE")
| eval stp_event=if(match(_raw,"TOPOTCHANGE|ROOTCHANGE|dot1dStpTopChanges"),1,0)
| bin _time span=10m
| stats sum(stp_event) as topo_changes by host, _time
| where topo_changes > 3
| sort -topo_changes
```
- **Implementation:** Poll BRIDGE-MIB dot1dStpTopChanges every 300s; ingest syslog for SPANTREE events. Alert when topology changes exceed 3 in 10 minutes. Correlate with root bridge changes for critical alerts.
- **Visualization:** Line chart (topology changes per host), Table (host, count), Timeline.
- **CIM Models:** N/A

---

### UC-5.1.29 · ARP Table Size Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** ARP table approaching hardware limits; can cause connectivity failures.
- **App/TA:** SNMP modular input
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
- **Data Sources:** ipNetToMediaTable entries count, show arp count
- **SPL:**
```spl
index=network sourcetype=snmp:arp OR sourcetype=cisco:ios:arp
| eval arp_count=coalesce(arp_entries, arp_count, 0)
| stats latest(arp_count) as current_arp by host
| lookup arp_limit host OUTPUT max_arp
| eval util_pct=round(current_arp/max_arp*100,1)
| where util_pct > 70
| table host current_arp max_arp util_pct
```
- **Implementation:** Poll ipNetToMediaTable (count rows) or parse `show ip arp` / `show arp` output via scripted input. Create lookup with device→max_arp (from vendor specs). Alert when utilization exceeds 70%.
- **Visualization:** Line chart (ARP count over time), Gauge (utilization), Table.
- **CIM Models:** N/A

---

### UC-5.1.30 · MAC Address Table Capacity
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** CAM table utilization on switches approaching hardware limits.
- **App/TA:** SNMP modular input
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
- **Data Sources:** dot1qTpFdbTable count, show mac address-table count
- **SPL:**
```spl
index=network sourcetype=snmp:bridge OR sourcetype=cisco:ios:mac
| eval mac_count=coalesce(fdb_entries, mac_count, 0)
| stats latest(mac_count) as current_mac by host
| lookup mac_limit host OUTPUT max_mac
| eval util_pct=round(current_mac/max_mac*100,1)
| where util_pct > 75
| table host current_mac max_mac util_pct
```
- **Implementation:** Poll dot1qTpFdbTable (count) or parse `show mac address-table count`. Create lookup with switch model→max_mac. Alert when CAM utilization exceeds 75%.
- **Visualization:** Line chart (MAC count over time), Gauge, Table.
- **CIM Models:** N/A

---

### UC-5.1.31 · QoS Policy Drops per Class
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Traffic dropped per QoS class/queue on routers/switches.
- **App/TA:** SNMP modular input (CISCO-CLASS-BASED-QOS-MIB)
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
- **Data Sources:** cbQosCMDropPkt, cbQosCMPrePolicyPkt
- **SPL:**
```spl
index=network sourcetype=snmp:qos
| streamstats current=f last(cbQosCMDropPkt) as prev_drop, last(cbQosCMPrePolicyPkt) as prev_pre by host, cbQosConfigIndex, cbQosObjectsIndex
| eval drop_delta=cbQosCMDropPkt-coalesce(prev_drop,0), pre_delta=cbQosCMPrePolicyPkt-coalesce(prev_pre,0)
| eval drop_rate=round(drop_delta/(pre_delta+0.001)*100,2)
| where drop_delta > 0
| stats sum(drop_delta) as total_drops, sum(pre_delta) as total_pre by host, policy_class
| eval drop_pct=round(total_drops/(total_pre+0.001)*100,2)
| sort -total_drops
```
- **Implementation:** Poll CISCO-CLASS-BASED-QOS-MIB (cbQosCMDropPkt, cbQosCMPrePolicyPkt) per policy/class. Map OID to policy name via lookup. Alert when drop rate exceeds 5% for critical classes.
- **Visualization:** Table (host, class, drops, rate), Bar chart, Line chart (drops over time).
- **CIM Models:** N/A

---

### UC-5.1.32 · Network Device End-of-Life Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Devices approaching EOL/EOS dates.
- **App/TA:** Lookup table with vendor EOL dates
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
- **Data Sources:** Device inventory + EOL lookup
- **SPL:**
```spl
| inputlookup device_inventory
| lookup eol_lookup model OUTPUT eol_date eos_date
| eval days_to_eol=round((strptime(eol_date,"%Y-%m-%d")-now())/86400,0)
| where days_to_eol < 365 OR days_to_eol < 0
| table host model eol_date days_to_eol
| sort days_to_eol
```
- **Implementation:** Maintain device_inventory lookup (host, model) and eol_lookup (model, eol_date) from Cisco EOL/EOS bulletins. Run scheduled search or dashboard. Alert when days_to_eol < 180. Update lookups annually.
- **Visualization:** Table (device, model, days to EOL), Single value (devices within 6 months), Gauge.
- **CIM Models:** N/A

---

### UC-5.1.33 · Half-Duplex Negotiation Anomaly
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Half/full duplex mismatches causing performance degradation.
- **App/TA:** SNMP modular input
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
- **Data Sources:** IF-MIB (ifSpeed), EtherLike-MIB (dot3StatsDuplexStatus), syslog
- **SPL:**
```spl
index=network (sourcetype=snmp:interface OR sourcetype="cisco:ios") ("duplex" OR "Duplex" OR "dot3StatsDuplexStatus" OR "halfDuplex" OR "fullDuplex")
| rex "duplex mismatch|(?<duplex_status>halfDuplex|fullDuplex|unknown)"
| where match(_raw,"mismatch|halfDuplex") OR duplex_status="halfDuplex"
| stats count by host, ifDescr, duplex_status
| table host ifDescr duplex_status count
```
- **Implementation:** Poll EtherLike-MIB dot3StatsDuplexStatus; ingest syslog for duplex mismatch messages. Alert on half-duplex on gigabit uplinks or explicit mismatch events.
- **Visualization:** Table (host, interface, duplex), Status grid, Single value.
- **CIM Models:** N/A

---

### UC-5.1.34 · PoE Power Budget Utilization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Power over Ethernet budget approaching capacity per switch.
- **App/TA:** SNMP modular input
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
- **Data Sources:** POWER-ETHERNET-MIB (pethMainPseOperStatus, pethMainPseConsumptionPower, pethMainPsePower)
- **SPL:**
```spl
index=network sourcetype=snmp:poe
| eval util_pct=round(pethMainPseConsumptionPower/pethMainPsePower*100,1)
| where pethMainPseOperStatus="on" AND util_pct > 80
| stats latest(util_pct) as poe_util, latest(pethMainPseConsumptionPower) as used_w, latest(pethMainPsePower) as total_w by host
| table host poe_util used_w total_w
```
- **Implementation:** Poll POWER-ETHERNET-MIB (pethMainPsePower, pethMainPseConsumptionPower) every 300s. Alert when utilization exceeds 80%. Track per PSE unit on modular switches.
- **Visualization:** Gauge (utilization), Table (host, used, total), Line chart.
- **CIM Models:** N/A

---

### UC-5.1.35 · LLDP / CDP Neighbor Change Detection
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault, Security
- **Value:** Unexpected topology changes in cabling/connections.
- **App/TA:** SNMP modular input, syslog
- **Equipment Models:** Cisco Catalyst 9200, Catalyst 9300, Catalyst 9400, Catalyst 9500, Catalyst 9600, Catalyst 3650, Catalyst 3850, Catalyst 2960-X, ISR 1100, ISR 4221, ISR 4321, ISR 4331, ISR 4351, ISR 4431, ISR 4451, ASR 1001-X, ASR 1002-X, ASR 1006-X, IE 3200, IE 3300, IE 3400
- **Data Sources:** LLDP-MIB (lldpRemTable), CISCO-CDP-MIB, syslog CDP/LLDP events
- **SPL:**
```spl
index=network (sourcetype=snmp:lldp OR sourcetype=snmp:cdp OR sourcetype="cisco:ios") ("lldpRem" OR "CDP-4-NATIVE" OR "LLDP" OR "neighbor")
| rex "neighbor (?<neighbor>\S+)|lldpRemSysName[=:]\s*(?<neighbor>\S+)|port (?<port>\S+)"
| bin _time span=1h
| stats dc(neighbor) as neighbor_changes, values(neighbor) as neighbors by host, port, _time
| where neighbor_changes > 1
| table host port _time neighbor_changes neighbors
```
- **Implementation:** Poll LLDP-MIB lldpRemTable and CISCO-CDP-MIB; ingest syslog for CDP/LLDP neighbor change events. Baseline neighbor table; alert on unexpected changes (new/removed neighbors). Useful for change validation and cable swap detection.
- **Visualization:** Table (host, port, changes), Timeline, Single value (unexpected changes).
- **CIM Models:** N/A

---


### UC-5.1.36 · Port Utilization and Congestion Alerts (Meraki MS)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Identifies port saturation and congestion events that require capacity upgrades or load balancing adjustments.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api device_type=MS`
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

### UC-5.1.37 · Power over Ethernet (PoE) Consumption Tracking (Meraki MS)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Monitors PoE power allocation to prevent over-subscription and ensure sufficient power for all devices.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api device_type=MS`
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

### UC-5.1.38 · Spanning Tree Protocol (STP) Topology Changes (Meraki MS)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Alerts on unexpected STP topology changes that indicate link failures or network configuration issues.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*STP*" OR signature="*topology*"`
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

### UC-5.1.39 · Port Security Violations and Rogue Device Detection (Meraki MS)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Detects unauthorized MAC addresses and port security breaches that indicate potential network intrusion.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*Port Security*" OR signature="*Unauthorized MAC*"`
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

### UC-5.1.40 · Switch Interface Up/Down Events and Link Flapping (Meraki MS)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Identifies port flapping, cable issues, and unstable link states that cause intermittent connectivity.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*link*" OR signature="*Interface*"`
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

### UC-5.1.41 · VLAN Configuration Mismatches and Tagging Violations (Meraki MS)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Detects VLAN configuration errors and tagging violations that disrupt network segmentation.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api` (MS), `sourcetype=meraki` (security/syslog)
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

### UC-5.1.42 · MAC Flooding and Bridge Table Exhaustion (Meraki MS)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Detects MAC address table exhaustion and flooding attacks that could overwhelm switch resources.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*MAC*" OR signature="*bridge*"`
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

### UC-5.1.43 · DHCP Snooping Violations (Meraki MS)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Detects unauthorized DHCP servers and spoofing attempts that disrupt network address allocation.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*DHCP Snooping*"`
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

### UC-5.1.44 · Broadcast Storm Detection and Mitigation (Meraki MS)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Anomaly
- **Value:** Identifies and alerts on broadcast storms that can freeze network performance across all switches.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*broadcast*"`
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

### UC-5.1.45 · Switch CPU and Memory Utilization (Meraki MS)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Monitors switch hardware resources to prevent performance degradation or device failure.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api device_type=MS`
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

### UC-5.1.46 · Stack Unit and Redundancy Health (Meraki MS)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Ensures switch stacking configuration remains healthy and redundancy is not compromised.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api device_type=MS stack_id=*`
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

### UC-5.1.47 · Trunk Link Utilization and Performance (Meraki MS)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Monitors inter-switch and uplink trunk utilization to identify bandwidth constraints.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api device_type=MS`
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

### UC-5.1.48 · QoS Queue Drops and Priority Violations (Meraki MS)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Detects QoS queue overflow and drops that indicate traffic priority issues.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*QoS*" OR signature="*queue*"`
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

### UC-5.1.49 · Port Access Control List (ACL) Hits and Block Events (Meraki MS)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Tracks ACL rule hits to monitor policy enforcement and identify anomalous traffic.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*ACL*"`
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

### UC-5.1.50 · Cable Test Results and Port Diagnostics (Meraki MS)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Analyzes cable integrity test results to identify wiring faults before they cause outages.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*cable*" OR signature="*diagnostic*"`
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

### UC-5.1.51 · Uplink Health and Failover Events (Meraki MS)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Monitors primary/secondary uplink status to detect failover events and connection issues.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*Uplink*" OR signature="*failover*"`
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

### UC-5.1.52 · Cellular Gateway Signal Strength Trending (Meraki MG)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Monitors cellular signal strength to ensure reliable backup connectivity.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api device_type=MG`
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

### UC-5.1.53 · Cellular Data Usage and Overage Monitoring (Meraki MG)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Tracks cellular data consumption to manage carrier costs and prevent overages.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api device_type=MG data_usage=*`
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

### UC-5.1.54 · Carrier Connection Health and Network Performance (Meraki MG)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Monitors carrier connectivity and network performance metrics for backup internet links.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*cellular*" OR signature="*carrier*"`
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

### UC-5.1.55 · SIM Status and Plan Monitoring (Meraki MG)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Tracks SIM card status and plan expiration to ensure continuous cellular connectivity.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api device_type=MG sim_status=*`
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


## 5.2 Firewalls

**Primary App/TA:** Palo Alto Networks Add-on for Splunk (`Splunk_TA_paloalto`, Splunkbase 7523), Fortinet FortiGate Add-On for Splunk (`TA-fortinet_fortigate`, Splunkbase 2846) — Free

---

### UC-5.2.1 · Top Denied Traffic Sources
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Identifies top blocked traffic sources — useful for rule tuning, detecting scanning, and misconfigured apps.
- **App/TA:** Vendor-specific firewall TA
- **Equipment Models:** Cisco Secure Firewall 3110, 3120, 3130, 3140, Firepower 1010, 1120, 1140, 1150, Firepower 2110, 2120, 2130, 2140, Firepower 4110, 4120, 4140, 4150, Firepower 9300, Firepower Management Center (FMC)
- **Data Sources:** `sourcetype=pan:traffic`, `sourcetype=fgt_traffic`, `sourcetype=cisco:firepower:syslog`
- **SPL:**
```spl
index=firewall action="denied" OR action="drop"
| stats count as denials, dc(dest) as unique_dests by src
| sort -denials | head 20 | lookup geoip ip as src OUTPUT Country
```
- **Implementation:** Forward firewall traffic logs via syslog. Install vendor TA for CIM-compliant fields. Create top-N dashboard.
- **Visualization:** Table (source, denials, dests), Map (GeoIP), Bar chart.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.2.2 · Policy Change Audit
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Configuration, Compliance
- **Value:** Firewall rule changes can expose the network. Compliance must-have (PCI, SOX, HIPAA).
- **App/TA:** Vendor-specific firewall TA
- **Equipment Models:** Cisco Secure Firewall 3110, 3120, 3130, 3140, Firepower 1010, 1120, 1140, 1150, Firepower 2110, 2120, 2130, 2140, Firepower 4110, 4120, 4140, 4150, Firepower 9300, Firepower Management Center (FMC)
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
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.2.3 · Threat Detection Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** IPS/IDS events indicate active attacks. Correlation with traffic context enables rapid response.
- **App/TA:** Vendor-specific firewall TA
- **Equipment Models:** Cisco Secure Firewall 3110, 3120, 3130, 3140, Firepower 1010, 1120, 1140, 1150, Firepower 2110, 2120, 2130, 2140, Firepower 4110, 4120, 4140, 4150, Firepower 9300, Firepower Management Center (FMC)
- **Data Sources:** `sourcetype=pan:threat`, `sourcetype=cisco:firepower:alert`
- **SPL:**
```spl
index=firewall sourcetype="pan:threat" severity="critical" OR severity="high"
| stats count by src, dest, threat_name, severity, action | sort -count
```
- **Implementation:** Forward threat logs. Alert immediately on critical severity. Correlate source IPs with auth logs.
- **Visualization:** Table (source, dest, threat, action), Bar chart by threat type, Map.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.2.4 · VPN Tunnel Status
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** VPN failures isolate remote sites or users. Proactive monitoring prevents "the VPN is down" calls.
- **App/TA:** Vendor-specific firewall TA
- **Equipment Models:** Cisco Secure Firewall 3110, 3120, 3130, 3140, Firepower 1010, 1120, 1140, 1150, Firepower 2110, 2120, 2130, 2140, Firepower 4110, 4120, 4140, 4150, Firepower 9300, Firepower Management Center (FMC)
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
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.2.5 · High-Risk Port Exposure
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Allowed traffic to RDP/SMB/Telnet from untrusted zones indicates policy gaps.
- **App/TA:** Vendor-specific firewall TA
- **Equipment Models:** Cisco Secure Firewall 3110, 3120, 3130, 3140, Firepower 1010, 1120, 1140, 1150, Firepower 2110, 2120, 2130, 2140, Firepower 4110, 4120, 4140, 4150, Firepower 9300, Firepower Management Center (FMC)
- **Data Sources:** Firewall traffic logs
- **SPL:**
```spl
index=firewall action="allowed" (dest_port=3389 OR dest_port=445 OR dest_port=23)
| where NOT cidrmatch("10.0.0.0/8", src)
| stats count by src, dest, dest_port | sort -count
```
- **Implementation:** Monitor allow rules for external traffic to high-risk ports. Alert on any matches. Review and tighten rules.
- **Visualization:** Table (source, dest, port), Bar chart by port, Map.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.2.6 · Geo-IP Anomaly Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Anomaly
- **Value:** Traffic to/from sanctioned or unexpected countries flags exfiltration, C2, or compromised hosts.
- **App/TA:** Vendor-specific TA + GeoIP lookup
- **Equipment Models:** Cisco Secure Firewall 3110, 3120, 3130, 3140, Firepower 1010, 1120, 1140, 1150, Firepower 2110, 2120, 2130, 2140, Firepower 4110, 4120, 4140, 4150, Firepower 9300, Firepower Management Center (FMC)
- **Data Sources:** Firewall traffic logs
- **SPL:**
```spl
index=firewall action="allowed" direction="outbound"
| lookup geoip ip as dest OUTPUT Country
| search Country IN ("Russia","China","North Korea","Iran")
| stats count, sum(bytes_out) as data_sent by src, Country | sort -data_sent
```
- **Implementation:** Install GeoIP lookup (MaxMind). Enrich traffic logs. Alert on sanctioned country traffic and volume anomalies.
- **Visualization:** Choropleth map, Table, Bar chart by country.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.2.7 · Connection Rate Anomalies
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Anomaly, Performance
- **Value:** Sudden connection spikes indicate DDoS, scanning, or worm propagation.
- **App/TA:** Vendor-specific firewall TA
- **Equipment Models:** Cisco Secure Firewall 3110, 3120, 3130, 3140, Firepower 1010, 1120, 1140, 1150, Firepower 2110, 2120, 2130, 2140, Firepower 4110, 4120, 4140, 4150, Firepower 9300, Firepower Management Center (FMC)
- **Data Sources:** Firewall traffic logs
- **SPL:**
```spl
index=firewall
| bin _time span=5m
| stats count as connections by src, _time
| eventstats avg(connections) as avg_c, stdev(connections) as std_c by src
| where connections > (avg_c + 3*std_c)
| sort -connections
```
- **Implementation:** Baseline connection rates over 7 days. Alert when rate exceeds 3 standard deviations.
- **Visualization:** Line chart with threshold overlay, Table, Timechart.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.2.8 · Certificate Inspection Failures
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** SSL decryption failures mean traffic passes uninspected — could be legitimate cert pinning or SSL evasion.
- **App/TA:** Vendor-specific firewall TA
- **Equipment Models:** Cisco Secure Firewall 3110, 3120, 3130, 3140, Firepower 1010, 1120, 1140, 1150, Firepower 2110, 2120, 2130, 2140, Firepower 4110, 4120, 4140, 4150, Firepower 9300, Firepower Management Center (FMC)
- **Data Sources:** Firewall decryption logs
- **SPL:**
```spl
index=firewall sourcetype="pan:decryption" action="ssl-error"
| stats count by dest, dest_port, reason | sort -count
```
- **Implementation:** Enable decryption logging. Track failure rates by destination. Tune exclusion lists.
- **Visualization:** Table, Pie chart (reasons), Trend line.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.2.9 · URL Filtering Blocks
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Shows what categories users are trying to access. Reveals policy effectiveness and shadow IT.
- **App/TA:** Vendor-specific firewall TA
- **Equipment Models:** Cisco Secure Firewall 3110, 3120, 3130, 3140, Firepower 1010, 1120, 1140, 1150, Firepower 2110, 2120, 2130, 2140, Firepower 4110, 4120, 4140, 4150, Firepower 9300, Firepower Management Center (FMC)
- **Data Sources:** `sourcetype=pan:url`
- **SPL:**
```spl
index=firewall sourcetype="pan:url" action="block-url"
| stats count by url_category, src | sort -count
```
- **Implementation:** Forward URL filtering logs. Dashboard showing blocks by category and user.
- **Visualization:** Bar chart (by category), Table, Pie chart.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.action="blocked"
  by All_Traffic.src All_Traffic.dest All_Traffic.dest_port span=1h
| eval bytes=bytes_in+bytes_out
| sort -count
```

---

### UC-5.2.10 · Admin Access Audit
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Firewall admin access is highly privileged. Audit trail is a compliance must-have.
- **App/TA:** Vendor-specific firewall TA
- **Equipment Models:** Cisco Secure Firewall 3110, 3120, 3130, 3140, Firepower 1010, 1120, 1140, 1150, Firepower 2110, 2120, 2130, 2140, Firepower 4110, 4120, 4140, 4150, Firepower 9300, Firepower Management Center (FMC)
- **Data Sources:** Firewall system/auth logs
- **SPL:**
```spl
index=firewall sourcetype="pan:system" ("login" OR "logout" OR "auth")
| eval status=case(match(_raw,"success"),"Success", match(_raw,"fail"),"Failed", 1=1,"Other")
| stats count by admin_user, src, status | sort -count
```
- **Implementation:** Forward system/auth logs. Alert on failed admin logins. Track all successful logins. Alert on unexpected source IPs.
- **Visualization:** Table (admin, source, status), Timeline, Bar chart.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.2.11 · Firewall Resource Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Capacity
- **Value:** Session table exhaustion blocks new connections. CPU saturation degrades throughput.
- **App/TA:** Vendor-specific TA, SNMP
- **Equipment Models:** Cisco Secure Firewall 3110, 3120, 3130, 3140, Firepower 1010, 1120, 1140, 1150, Firepower 2110, 2120, 2130, 2140, Firepower 4110, 4120, 4140, 4150, Firepower 9300, Firepower Management Center (FMC)
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
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.2.12 · NAT Pool Exhaustion
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** NAT exhaustion prevents outbound connections. Users lose internet access.
- **App/TA:** Vendor-specific TA, syslog
- **Equipment Models:** Cisco Secure Firewall 3110, 3120, 3130, 3140, Firepower 1010, 1120, 1140, 1150, Firepower 2110, 2120, 2130, 2140, Firepower 4110, 4120, 4140, 4150, Firepower 9300, Firepower Management Center (FMC)
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
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.2.13 · Session Table Exhaustion
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Capacity
- **Value:** When session tables fill, new connections are dropped. This causes service outages that are difficult to diagnose without firewall telemetry.
- **App/TA:** `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, SNMP
- **Equipment Models:** Cisco Secure Firewall 3110, 3120, 3130, 3140, Firepower 1010, 1120, 1140, 1150, Firepower 2110, 2120, 2130, 2140, Firepower 4110, 4120, 4140, 4150, Firepower 9300, Firepower Management Center (FMC)
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
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.2.14 · Firewall HA Failover Events
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** HA failovers cause brief traffic disruption and can indicate underlying hardware or link failures. Tracking failover frequency detects instability.
- **App/TA:** `Splunk_TA_paloalto`, `TA-fortinet_fortigate`
- **Equipment Models:** Cisco Secure Firewall 3110, 3120, 3130, 3140, Firepower 1010, 1120, 1140, 1150, Firepower 2110, 2120, 2130, 2140, Firepower 4110, 4120, 4140, 4150, Firepower 9300, Firepower Management Center (FMC)
- **Data Sources:** `sourcetype=pan:system`, `sourcetype=fgt_event`
- **SPL:**
```spl
index=firewall (sourcetype="pan:system" "HA state change") OR (sourcetype="fgt_event" subtype="ha")
| rex "state change.*from (?<old_state>\w+) to (?<new_state>\w+)"
| table _time, dvc, old_state, new_state | sort -_time
```
- **Implementation:** Forward firewall system logs to Splunk. Alert on any active/passive transition. Correlate with link down events. Track failover frequency — more than 1 per week indicates instability.
- **Visualization:** Timeline (failover events), Single value (failovers this month), Table (history).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.2.15 · Botnet/C2 Traffic Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Detecting outbound connections to known C2 infrastructure identifies compromised internal hosts before data exfiltration occurs.
- **App/TA:** `Splunk_TA_paloalto`, Threat intelligence feeds
- **Equipment Models:** Cisco Secure Firewall 3110, 3120, 3130, 3140, Firepower 1010, 1120, 1140, 1150, Firepower 2110, 2120, 2130, 2140, Firepower 4110, 4120, 4140, 4150, Firepower 9300, Firepower Management Center (FMC)
- **Data Sources:** `sourcetype=pan:threat`, `sourcetype=pan:traffic`
- **SPL:**
```spl
index=network sourcetype="pan:threat" category="command-and-control" OR category="spyware"
| stats count values(dest) as c2_targets dc(dest) as unique_c2 by src
| sort -count
| lookup dnslookup clientip as src OUTPUT clienthost as src_hostname
```
- **Implementation:** Enable threat prevention and URL filtering on the firewall. Ingest threat logs. Cross-reference with external threat intelligence (STIX/TAXII feeds). Alert immediately on any C2 match.
- **Visualization:** Table (compromised hosts, C2 targets), Sankey diagram (source → C2), Single value (count).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.2.16 · SSL/TLS Decryption Failures
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Decryption failures create blind spots in security inspection. Tracking failures by destination reveals certificate pinning, protocol mismatches, or policy gaps.
- **App/TA:** `Splunk_TA_paloalto`
- **Equipment Models:** Cisco Secure Firewall 3110, 3120, 3130, 3140, Firepower 1010, 1120, 1140, 1150, Firepower 2110, 2120, 2130, 2140, Firepower 4110, 4120, 4140, 4150, Firepower 9300, Firepower Management Center (FMC)
- **Data Sources:** `sourcetype=pan:decryption`
- **SPL:**
```spl
index=network sourcetype="pan:decryption" action="decrypt-error" OR action="no-decrypt"
| stats count by reason, dest, dest_port
| sort 50 -count
```
- **Implementation:** Enable decryption logging. Group failures by reason (unsupported cipher, certificate pinning, policy exclude). Review and update decryption policy based on findings.
- **Visualization:** Bar chart (failure reasons), Table (top undecrypted destinations), Pie chart (by reason).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.2.17 · Firewall Rule Hit Count Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Unused firewall rules increase attack surface and complexity. Identifying zero-hit rules enables rule base cleanup and reduces risk.
- **App/TA:** `Splunk_TA_paloalto`, `TA-fortinet_fortigate`
- **Equipment Models:** Cisco Secure Firewall 3110, 3120, 3130, 3140, Firepower 1010, 1120, 1140, 1150, Firepower 2110, 2120, 2130, 2140, Firepower 4110, 4120, 4140, 4150, Firepower 9300, Firepower Management Center (FMC)
- **Data Sources:** `sourcetype=pan:traffic`, `sourcetype=fgt_traffic`
- **SPL:**
```spl
index=network sourcetype="pan:traffic"
| stats count as hit_count dc(src) as unique_sources dc(dest) as unique_dests by rule
| sort hit_count
| eval status=if(hit_count=0,"UNUSED",if(hit_count<10,"RARELY_USED","ACTIVE"))
```
- **Implementation:** Collect traffic logs with rule names. Run weekly reports to identify unused rules. Review rules with zero hits over 90 days for removal. Document cleanup actions.
- **Visualization:** Table (rule, hit count, status), Bar chart (hit count distribution), Single value (unused rule count).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.2.18 · Threat Prevention Signature Coverage
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Outdated threat signatures leave the firewall blind to new attacks. Monitoring signature versions ensures security posture is current.
- **App/TA:** `Splunk_TA_paloalto`, `TA-fortinet_fortigate`
- **Equipment Models:** Cisco Secure Firewall 3110, 3120, 3130, 3140, Firepower 1010, 1120, 1140, 1150, Firepower 2110, 2120, 2130, 2140, Firepower 4110, 4120, 4140, 4150, Firepower 9300, Firepower Management Center (FMC)
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
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---


### UC-5.2.19 · VPN Tunnel Status and Path Monitoring (Meraki MX)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Ensures all site-to-site and client VPN tunnels remain active and operative.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=vpn sourcetype=meraki:api`
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

### UC-5.2.20 · Content Filtering and URL Category Blocks (Meraki MX)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Tracks blocked URLs and categories to monitor policy compliance and identify misclassified content.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=urls action="blocked"`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=urls action="blocked"
| stats count as block_count by url_category, src
| sort - block_count
| head 20
```
- **Implementation:** Ingest URL filtering events from MX syslog. Categorize by policy.
- **Visualization:** Table of top blocked categories; bar chart by category; user detail table.
- **CIM Models:** N/A

---

### UC-5.2.21 · IDS/IPS Alert Analysis and Threat Scoring (Meraki MX)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Identifies and prioritizes intrusion detection alerts for investigation and threat response.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=ids_alert`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=ids_alert
| stats count as alert_count by signature, priority, src, dest
| eval severity=case(priority=1, "Critical", priority=2, "High", priority=3, "Medium", 1=1, "Low")
| where priority <= 2
| sort - alert_count
```
- **Implementation:** Ingest IDS/IPS alert events from MX appliance. Enrich with threat intelligence.
- **Visualization:** Alert timeline; severity breakdown pie chart; alert detail table; threat map.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.2.22 · Malware Detection and AMP File Reputation Events (Meraki MX)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Detects and tracks file-based threats to respond quickly to potential malware infections.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*malware*" OR signature="*AMP*"`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*malware*" OR signature="*AMP*")
| stats count as malware_count by src, threat_name, file_name
| where malware_count > 0
| sort - malware_count
```
- **Implementation:** Enable AMP on MX appliance. Ingest malware detection events.
- **Visualization:** Threat timeline; infected hosts table; file reputation detail; incident dashboard.
- **CIM Models:** N/A

---

### UC-5.2.23 · Firewall Rule Hit Analysis and Top Denied Flows (Meraki MX)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Identifies top denied flows to optimize firewall rules and detect policy violations.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=flow action="deny"`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=flow action="deny"
| stats count as deny_count by firewall_rule, src, dest, dest_port
| sort - deny_count
| head 20
```
- **Implementation:** Analyze firewall deny events from flow logs. Correlate with rules.
- **Visualization:** Top denied flows table; denial timeline; source/dest distribution heatmap.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.2.24 · Traffic Shaping Effectiveness and QoS Policy Analysis (Meraki MX)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Measures the impact of traffic shaping policies on bandwidth distribution and priority.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=flow sourcetype=meraki:api`
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
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.2.25 · Site-to-Site VPN Latency and Performance (Meraki MX)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Monitors latency and jitter on VPN tunnels to ensure quality of critical business traffic.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=vpn sourcetype=meraki:api`
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

### UC-5.2.26 · Client VPN Connections and Remote Access Patterns (Meraki MX)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Tracks client VPN usage patterns for remote workers and identifies problematic connections.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=vpn client_vpn=true`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=vpn client_vpn=true
| stats count as connection_count, avg(duration) as avg_session_length by user_id, src
| where connection_count > 10
```
- **Implementation:** Filter VPN logs for client connections. Track by user and source IP.
- **Visualization:** Connected users timeline; session duration histogram; geography map of remote users.
- **CIM Models:** N/A

---

### UC-5.2.27 · NAT Pool Usage and Exhaustion Alerts (Meraki MX)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Monitors NAT pool utilization to prevent address exhaustion that could block outbound traffic.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
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

### UC-5.2.28 · BGP Peering Status and Route Stability (Meraki MX)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Ensures BGP peers remain established and routing remains stable for multi-ISP designs.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*BGP*"`
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

### UC-5.2.29 · Threat Intelligence Correlation and IoC Matching (Meraki MX)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Correlates network traffic with threat intelligence databases to detect known malicious IPs and domains.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event OR type=urls OR type=flow`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" (type=security_event OR type=urls OR type=flow)
| lookup threat_intelligence_list src as src OUTPUTNEW threat_name, threat_severity
| where threat_severity="high" OR threat_severity="critical"
| stats count as hit_count by src, dest, threat_name
| sort - hit_count
```
- **Implementation:** Create threat intelligence lookup table. Correlate with network events.
- **Visualization:** IoC match timeline; threat severity breakdown; affected hosts table.
- **CIM Models:** N/A

---

### UC-5.2.30 · Geo-Blocking Event Tracking and Geographic Policy Enforcement (Meraki MX)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Tracks geo-blocking policy enforcement to verify compliance with data residency and export controls.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=urls action="blocked" country=*`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=urls action="blocked"
| lookup geo_ip.csv dest OUTPUTNEW country, city
| stats count as block_count by country
| sort - block_count
```
- **Implementation:** Ingest URL logs with GeoIP enrichment. Track blocks by geography.
- **Visualization:** Geo-block map; country block count chart; policy compliance dashboard.
- **CIM Models:** N/A

---

### UC-5.2.31 · Application Visibility and Network Application Trending (Meraki MX)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Identifies top applications and protocols on network to understand usage patterns and detect anomalies.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=flow application=*`
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

### UC-5.2.32 · Bandwidth by Application and Department (Meraki MX)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Tracks bandwidth consumption by application and business unit for chargeback and optimization.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=flow`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=flow
| lookup department_by_ip.csv src OUTPUTNEW department
| stats sum(sent_bytes) as upload_mb, sum(received_bytes) as download_mb by application, department
| eval total_mb=upload_mb+download_mb
| sort -total_mb
```
- **Implementation:** Correlate flows with IP-to-department mapping. Aggregate by app and dept.
- **Visualization:** Stacked bar of bandwidth by dept/app; heatmap of app usage per dept.
- **CIM Models:** N/A

---

### UC-5.2.33 · WAN Link Quality Monitoring — Jitter, Latency, Packet Loss (Meraki MX)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Continuously monitors WAN quality metrics to detect link degradation before impacting users.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api wan_metrics=*`
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

### UC-5.2.34 · Internet Uplink Failover Events and Recovery Time (Meraki MX)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Tracks failover events, recovery time, and uplink behavior to ensure high availability.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*failover*" OR signature="*recovery*"`
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

### UC-5.2.35 · Cellular Modem Failover Activation and Usage (Meraki MX)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Tracks cellular backup activation to monitor failover effectiveness and cellular data usage.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*cellular*" OR signature="*4G*"`
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

### UC-5.2.36 · Warm Spare Failover and Appliance Redundancy (Meraki MX)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Ensures warm spare failover mechanism is operational and redundancy is maintained.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*warm spare*" OR signature="*HA*"`
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

### UC-5.2.37 · Auto VPN Path Changes and Tunnel Switching (Meraki MX)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Tracks automatic VPN path optimization to understand tunnel usage and convergence behavior.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=vpn signature="*Auto VPN*" OR signature="*path change*"`
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

### UC-5.2.38 · Connection Rate Analysis and DOS Detection (Meraki MX)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Detects denial of service attacks by analyzing abnormal connection establishment rates.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=flow protocol="tcp" tcp_flags="SYN"`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=flow protocol="tcp" tcp_flags="SYN"
| timechart count as new_connections by src
| where new_connections > 1000
```
- **Implementation:** Monitor TCP SYN rate by source IP. Alert on anomalous connection rates.
- **Visualization:** Connection rate timeline; source IP detail table; DOS alert dashboard.
- **CIM Models:** N/A

---

### UC-5.2.39 · Data Loss Prevention (DLP) Event Analysis (Meraki MX)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Detects and alerts on sensitive data transmission to prevent data exfiltration.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*DLP*"`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*DLP*"
| stats count as dlp_match_count by src, dest, dlp_policy, data_type
| where dlp_match_count > 0
| sort - dlp_match_count
```
- **Implementation:** Enable DLP on MX appliance. Ingest DLP match events.
- **Visualization:** DLP incident timeline; data type breakdown; source/destination detail.
- **CIM Models:** N/A

---

### UC-5.2.40 · Meraki VPN Tunnel and Failover Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Site-to-site and client VPN tunnel state directly impacts remote site and user connectivity. Detecting tunnel down or failover events supports quick remediation.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580), Meraki dashboard API
- **Data Sources:** `sourcetype=meraki:api` (VPN status), syslog from MX
- **SPL:**
```spl
index=cisco_network sourcetype="meraki:api" vpn_tunnel=*
| stats latest(tunnel_state) as state, latest(peer_ip) as peer by device_serial, tunnel_id
| where state != "up"
| table device_serial tunnel_id peer state _time
```
- **Implementation:** Poll Meraki API for VPN tunnel status or ingest MX syslog for tunnel events. Alert when any tunnel is down. Track failover events for active/standby links.
- **Visualization:** Status grid (tunnel, state), Table (down tunnels), Timeline (failover events).
- **CIM Models:** N/A

---


## 5.3 Load Balancers & ADCs

**Primary App/TA:** Splunk Add-on for F5 BIG-IP (`Splunk_TA_f5-bigip`), Citrix ADC TA — Free

---

### UC-5.3.1 · Pool Member Health Status (F5 BIG-IP)
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
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.3.2 · Virtual Server Availability (F5 BIG-IP)
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

### UC-5.3.3 · Connection and Throughput Trending (F5 BIG-IP)
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
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.3.4 · SSL Certificate Expiry (F5 BIG-IP)
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

### UC-5.3.5 · HTTP Error Rate by VIP (F5 BIG-IP)
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

### UC-5.3.6 · Response Time Degradation (F5 BIG-IP)
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

### UC-5.3.7 · Session Persistence Issues (F5 BIG-IP)
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

### UC-5.3.8 · WAF Policy Violations (F5 BIG-IP ASM)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** WAF violations indicate attacks — SQL injection, XSS, command injection. Trending reveals campaigns.
- **App/TA:** `Splunk_TA_f5-bigip` (ASM)
- **Data Sources:** `sourcetype=f5:bigip:asm:syslog`
- **SPL:**
```spl
index=network sourcetype="f5:bigip:asm:syslog"
| stats count by violation_name, src, request_uri, severity | sort -count
```
- **Implementation:** Enable F5 ASM logging. Dashboard showing top violations, attack sources, and targeted URIs.
- **Visualization:** Table, Bar chart by violation, Map (source IPs), Timeline.
- **CIM Models:** N/A

---

### UC-5.3.9 · Connection Queue Depth (F5 BIG-IP)
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
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.3.10 · Backend Server Error Code Distribution (F5 BIG-IP)
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

### UC-5.3.11 · Rate Limiting and DDoS Mitigation Events (F5 BIG-IP)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security, Anomaly
- **Value:** Tracking rate limiting events reveals ongoing attacks and validates that DDoS protections are actively working.
- **App/TA:** F5 TA (`Splunk_TA_f5-bigip`), Splunk_TA_citrix-netscaler
- **Data Sources:** `sourcetype=f5:bigip:asm`, `sourcetype=f5:bigip:ltm`
- **SPL:**
```spl
index=network sourcetype="f5:bigip:asm" attack_type="*dos*" OR violation="Rate Limiting"
| stats count values(src) as src_values dc(src) as unique_sources by virtual_server, attack_type
| sort -count
```
- **Implementation:** Enable ASM/WAF logging. Configure rate limiting policies per virtual server. Alert on sustained rate limiting events. Track source IP patterns for blocklisting.
- **Visualization:** Timechart (events over time), Table (source IPs, attack types), Single value (blocked requests).
- **CIM Models:** N/A

---

### UC-5.3.12 · iRule/Policy Errors (F5 BIG-IP)
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

### UC-5.3.13 · Citrix ADC Virtual Server Health and State (NetScaler)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Citrix ADC (NetScaler) virtual servers (vServers) are the front-end load-balancing endpoints that distribute traffic to back-end service groups. A vServer transitions from UP to DOWN when all bound services fail health checks, causing a complete outage for the application it serves. Monitoring vServer state changes provides immediate alerting when applications lose load-balanced availability.
- **App/TA:** Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`), Splunk Connect for Syslog
- **Data Sources:** `index=network` `sourcetype="citrix:netscaler:syslog"` fields `vserver_name`, `vserver_state`, `vserver_type`, `service_name`, `service_state`
- **SPL:**
```spl
index=network sourcetype="citrix:netscaler:syslog" "Vserver" ("DOWN" OR "UP" OR "OUT OF SERVICE")
| rex "Vserver (?<vserver_name>\S+) - State (?<state>\w+)"
| where state="DOWN" OR state="OUTOFSERVICE"
| bin _time span=5m
| stats count as state_changes, latest(state) as current_state, values(host) as adc_node by vserver_name, _time
| table _time, vserver_name, current_state, state_changes, adc_node
```
- **Implementation:** Configure Citrix ADC to send syslog to Splunk via Splunk Connect for Syslog (SC4S). The ADC generates syslog messages for vServer state transitions (SNMP trap equivalent). Alternatively, use the NITRO API via scripted input to poll `lbvserver` statistics including `state`, `curclntconnections`, `tothits`, and `health` (percentage of UP services). Alert immediately on any vServer transitioning to DOWN. Track vServer health percentage — a vServer at 50% health means half its services are down and may be approaching failure. Correlate with service group member health checks for root cause.
- **Visualization:** Status grid (vServer name x state), Timeline (state transitions), Table (DOWN vServers with service count).
- **CIM Models:** N/A

---

### UC-5.3.14 · Citrix ADC Service Group Member Health (NetScaler)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Behind each Citrix ADC vServer, service group members represent individual back-end servers. When health monitors detect a service group member as DOWN, the ADC stops sending traffic to that server. A single member going down may be routine (maintenance), but multiple simultaneous failures indicate a systemic issue — network partition, shared dependency failure, or deployment problem. Monitoring service group member health identifies back-end server failures faster than application-level monitoring.
- **App/TA:** Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`)
- **Data Sources:** `index=network` `sourcetype="citrix:netscaler:syslog"` fields `service_name`, `service_ip`, `service_port`, `service_state`, `monitor_name`
- **SPL:**
```spl
index=network sourcetype="citrix:netscaler:syslog" "monitor" ("DOWN" OR "UP") "servicegroup"
| rex "servicegroup member (?<sg_name>\S+)\((?<member_ip>[^)]+)\) - State (?<state>\w+)"
| where state="DOWN"
| stats count as transitions, latest(_time) as last_seen, latest(state) as current_state by sg_name, member_ip, host
| eval last_seen_fmt=strftime(last_seen, "%Y-%m-%d %H:%M:%S")
| sort -last_seen
| table sg_name, member_ip, current_state, transitions, last_seen_fmt, host
```
- **Implementation:** The ADC logs service state transitions via syslog. For richer data, poll the NITRO API `servicegroup_servicegroupmember_binding` to enumerate all members and their states. Track `svrstate` (UP, DOWN, OUT OF SERVICE) and monitor response times. Alert when: more than 2 service group members go DOWN simultaneously (systemic issue), a critical service group drops below minimum capacity threshold, or a member remains DOWN for more than 15 minutes (stale failure). Correlate member health with application error rates for impact assessment.
- **Visualization:** Table (service groups with DOWN members), Bar chart (DOWN members by service group), Timeline (member state changes).
- **CIM Models:** N/A

---

### UC-5.3.15 · Citrix ADC SSL Certificate Expiration Monitoring (NetScaler)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance, Availability
- **Value:** SSL certificates on Citrix ADC terminate HTTPS connections for all web applications behind the load balancer. An expired certificate causes browser warnings or complete connection failures for all users. The NITRO API exposes `daystoexpiration` for every bound SSL certificate, enabling automated alerting well before expiry. Certificate expiry outages are among the most preventable yet impactful failures in production environments.
- **App/TA:** Custom scripted input polling Citrix ADC NITRO API
- **Data Sources:** `index=network` `sourcetype="citrix:netscaler:ssl"` fields `certkey_name`, `days_to_expiry`, `subject`, `issuer`, `serial`, `bound_vserver`
- **SPL:**
```spl
index=network sourcetype="citrix:netscaler:ssl"
| stats latest(days_to_expiry) as days_left, latest(subject) as subject, latest(issuer) as issuer, values(bound_vserver) as bound_to by certkey_name, host
| where days_left < 90
| eval urgency=case(days_left<=7, "CRITICAL", days_left<=30, "HIGH", days_left<=90, "MEDIUM", 1=1, "LOW")
| sort days_left
| table certkey_name, days_left, urgency, subject, issuer, bound_to, host
```
- **Implementation:** Create a scripted input that polls the NITRO API `sslcertkey` resource on each ADC. The API returns `certkey` name, `subject`, `issuer`, `serial`, `clientcertnotbefore`, `clientcertnotafter`, `daystoexpiration`, and `expirymonitor` status. Also enable the built-in `expirymonitor` on the ADC with a `notificationperiod` (10–100 days). Run the scripted input daily. Alert at 90 days (plan renewal), 30 days (action required), 7 days (critical), and immediately when `daystoexpiration` reaches 0. Track all certificates bound to vServers — unbound certificates can be ignored or flagged for cleanup.
- **Visualization:** Table (certificates sorted by expiry), Single value (certificates expiring within 30 days), Gauge (soonest expiry).
- **CIM Models:** Certificates

---

### UC-5.3.16 · Citrix ADC High Availability Failover Monitoring (NetScaler)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Citrix ADC deployments typically use HA pairs where a secondary appliance takes over if the primary fails. Failover events (PRIMARY → SECONDARY swap) are disruptive — active connections may be dropped, and if configuration sync was incomplete, the new primary may have a stale configuration. Monitoring failover events, sync status, and node health ensures HA is functioning correctly and that failovers are investigated promptly.
- **App/TA:** Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`)
- **Data Sources:** `index=network` `sourcetype="citrix:netscaler:syslog"` fields `ha_state`, `ha_node`, `sync_status`, `failover_reason`
- **SPL:**
```spl
index=network sourcetype="citrix:netscaler:syslog" ("HA state" OR "failover" OR "STAYSECONDARY" OR "CLAIMING" OR "FORCE CHANGE")
| rex "HA state of node (?<node_id>\d+) changed from (?<from_state>\w+) to (?<to_state>\w+)"
| where isnotnull(from_state)
| eval is_failover=if(to_state="PRIMARY" AND from_state="SECONDARY", "Yes", "No")
| sort -_time
| table _time, host, node_id, from_state, to_state, is_failover
```
- **Implementation:** The ADC logs HA state transitions via syslog when nodes change between PRIMARY, SECONDARY, CLAIMING, and FORCE CHANGE states. Also poll the NITRO API `hanode` resource for `hacurstatus`, `hacurstate`, `hasync`, `haprop`, and `hatotpktrx`. Monitor for: any failover event (state change to PRIMARY on a formerly SECONDARY node), sync failures (`hasync` not SUCCESS — configuration mismatch between nodes), system health states (COMPLETEFAIL, PARTIALFAIL, ROUTEMONITORFAIL), and STAYSECONDARY status (forced secondary, no automatic failover possible). Alert immediately on failover events. Regularly validate sync status — a desynchronized HA pair means the secondary will come up with stale configuration after failover.
- **Visualization:** Timeline (failover events), Status grid (node x state), Table (sync status per HA pair).
- **CIM Models:** N/A

---

### UC-5.3.17 · Citrix ADC GSLB Site and Service Health (NetScaler)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Global Server Load Balancing (GSLB) distributes traffic across multiple data centers based on proximity, health, and load. GSLB relies on the Metric Exchange Protocol (MEP) between sites to share health and load metrics. If MEP connectivity fails between sites, the GSLB method falls back to Round Robin — potentially sending users to degraded or distant sites. Monitoring GSLB site health and MEP status ensures intelligent multi-site traffic distribution.
- **App/TA:** Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`), NITRO API scripted input
- **Data Sources:** `index=network` `sourcetype="citrix:netscaler:syslog"` fields `gslb_site`, `gslb_service`, `mep_status`, `site_ip`, `service_state`
- **SPL:**
```spl
index=network sourcetype="citrix:netscaler:syslog" ("GSLB" OR "MEP") ("DOWN" OR "UP" OR "disabled")
| rex "GSLB (?:site|service) (?<gslb_entity>\S+).*State (?<state>\w+)"
| where state="DOWN" OR match(_raw, "MEP.*DOWN")
| bin _time span=5m
| stats count as events, latest(state) as current_state by gslb_entity, host, _time
| table _time, gslb_entity, current_state, events, host
```
- **Implementation:** The ADC logs GSLB service state changes and MEP connectivity events via syslog. MEP runs on TCP ports 3011 (standard) or 3009 (secure) between GSLB sites. Additionally, poll the NITRO API `gslbsite` and `gslbservice` resources for site status, MEP status, and GSLB service health. Alert on: any GSLB service going DOWN, MEP status changing to DOWN between any pair of sites (fallback to Round Robin), and GSLB site becoming unreachable. When MEP fails, all GSLB decisions for that site pair become unaware of the remote site's health — traffic may be sent to a degraded or offline site.
- **Visualization:** Status grid (GSLB site x MEP status), Table (DOWN GSLB services), Timeline (GSLB state changes).
- **CIM Models:** N/A

---

### UC-5.3.18 · Citrix Gateway / VPN Session Monitoring (NetScaler)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security, Capacity
- **Value:** Citrix Gateway (NetScaler Gateway) provides SSL VPN access and ICA Proxy functionality for remote Citrix session launches. Monitoring active Gateway sessions provides visibility into remote user activity, concurrent connection counts (license-relevant), authentication failures (brute force detection), and session anomalies (impossible travel, excessive bandwidth). Gateway is the perimeter entry point for all remote Citrix access, making it security-critical.
- **App/TA:** Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`)
- **Data Sources:** `index=network` `sourcetype="citrix:netscaler:syslog"` fields `user`, `client_ip`, `session_type`, `auth_result`, `gateway_vserver`
- **SPL:**
```spl
index=network sourcetype="citrix:netscaler:syslog" ("SSLVPN" OR "ICA" OR "AAA") ("LOGIN" OR "LOGOUT" OR "FAILURE")
| rex "User (?<user>\S+) - Client_ip (?<client_ip>\S+)"
| eval auth_result=case(match(_raw, "LOGIN"), "Success", match(_raw, "FAILURE"), "Failure", match(_raw, "LOGOUT"), "Logout", 1=1, "Other")
| bin _time span=15m
| stats sum(eval(if(auth_result="Success", 1, 0))) as logins,
  sum(eval(if(auth_result="Failure", 1, 0))) as failures,
  dc(user) as unique_users, dc(client_ip) as unique_ips by gateway_vserver, _time
| eval fail_pct=if((logins+failures)>0, round(failures/(logins+failures)*100,1), 0)
| where failures > 10 OR fail_pct > 30
| table _time, gateway_vserver, logins, failures, fail_pct, unique_users, unique_ips
```
- **Implementation:** The ADC logs all AAA (Authentication, Authorization, Accounting) events via syslog, including Gateway login successes, failures, and logouts with client IP and username. Configure syslog with appflow and audit logging enabled. Alert on: authentication failure rate exceeding 30% (possible brute force), concurrent sessions exceeding licensed capacity, a single source IP attempting more than 20 failed logins in 15 minutes, or unusual login times/locations for known users. Track peak concurrent Gateway sessions for capacity planning.
- **Visualization:** Timechart (logins vs failures), Bar chart (failures by source IP), Single value (concurrent sessions).
- **CIM Models:** Authentication

---

### UC-5.3.19 · Citrix ADC Content Switching Policy Hit Rate (NetScaler)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Configuration
- **Value:** Content switching vServers route HTTP/HTTPS requests to different load-balancing vServers based on URL patterns, headers, cookies, or other request attributes. Misconfigured content switching policies result in traffic hitting the default (catch-all) policy or being routed to the wrong back-end. Monitoring policy hit rates validates that routing rules are working as intended and identifies policies that are never triggered (candidate for cleanup or misconfiguration).
- **App/TA:** Custom scripted input polling Citrix ADC NITRO API
- **Data Sources:** `index=network` `sourcetype="citrix:netscaler:cs"` fields `cs_vserver`, `policy_name`, `hits`, `target_lbvserver`, `priority`
- **SPL:**
```spl
index=network sourcetype="citrix:netscaler:cs"
| stats latest(hits) as total_hits, latest(target_lbvserver) as target, latest(priority) as priority by cs_vserver, policy_name, host
| eventstats sum(total_hits) as vserver_total_hits by cs_vserver
| eval hit_pct=if(vserver_total_hits>0, round(total_hits/vserver_total_hits*100,1), 0)
| sort cs_vserver, priority
| table cs_vserver, policy_name, priority, target, total_hits, hit_pct
```
- **Implementation:** Poll the NITRO API `csvserver_cspolicy_binding` to get bound policies with hit counts. Alternatively, enable AppFlow on content switching vServers to capture per-request routing decisions. Run the scripted input every 15 minutes. Flag: policies with zero hits over 7 days (never triggered — misconfigured or obsolete), the default policy receiving more than 20% of traffic (indicates missing specific rules), and sudden shifts in policy hit distribution (routing change after configuration update). Content switching is critical for multi-tenant environments where different applications share a single VIP.
- **Visualization:** Bar chart (hit rate by policy), Table (policies with hit counts), Timechart (default policy hit rate trending).
- **CIM Models:** N/A

---

### UC-5.3.20 · Citrix ADC System Resource Utilization (NetScaler)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity, Performance
- **Value:** Citrix ADC appliances (physical or VPX) have finite CPU, memory, and throughput capacity. Unlike general-purpose servers, ADC resource exhaustion directly impacts all applications it fronts — causing connection drops, increased latency, and SSL handshake failures. Monitoring ADC system resources enables capacity planning and prevents appliance-level bottlenecks that affect the entire application delivery infrastructure.
- **App/TA:** Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`), NITRO API scripted input
- **Data Sources:** `index=network` `sourcetype="citrix:netscaler:perf"` fields `cpu_use_pct`, `mgmt_cpu_use_pct`, `mem_use_pct`, `disk_use_pct`, `active_connections`, `rx_mbps`, `tx_mbps`, `ssl_tps`
- **SPL:**
```spl
index=network sourcetype="citrix:netscaler:perf"
| bin _time span=5m
| stats avg(cpu_use_pct) as avg_cpu, max(cpu_use_pct) as max_cpu,
  avg(mem_use_pct) as avg_mem, avg(active_connections) as avg_conns,
  avg(ssl_tps) as avg_ssl_tps, avg(rx_mbps) as avg_rx, avg(tx_mbps) as avg_tx by host, _time
| where avg_cpu > 70 OR avg_mem > 80 OR max_cpu > 90
| table _time, host, avg_cpu, max_cpu, avg_mem, avg_conns, avg_ssl_tps, avg_rx, avg_tx
```
- **Implementation:** Poll the NITRO API `ns` (system) resource for CPU utilization, memory usage, and packet engine stats. Also poll `ssl` stats for SSL transactions per second (TPS). Run every 5 minutes. Key thresholds: CPU above 70% average (capacity planning), CPU spike above 90% (performance impact imminent), memory above 80% (connection table pressure), SSL TPS approaching licensed limit (SSL offload bottleneck). Track packet engine CPU separately from management CPU — high management CPU with low packet CPU indicates control plane issues. Trend resource utilization to forecast when additional ADC capacity is needed.
- **Visualization:** Line chart (CPU and memory over time), Gauge (current utilization), Table (ADCs above threshold).
- **CIM Models:** Performance

---

### UC-5.3.21 · Citrix ADC Responder and Rewrite Policy Errors (NetScaler)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Responder and rewrite policies on Citrix ADC implement URL redirects, HTTP header manipulation, security rules, and custom error responses. Policy evaluation errors or undef (undefined) hits indicate misconfiguration — the policy expression failed to evaluate, causing the request to fall through to default behavior. This can result in bypassed security headers, missing redirects, or unexpected error pages being served to users.
- **App/TA:** Custom scripted input polling Citrix ADC NITRO API
- **Data Sources:** `index=network` `sourcetype="citrix:netscaler:policy"` fields `policy_name`, `policy_type`, `hits`, `undef_hits`, `bound_to`
- **SPL:**
```spl
index=network sourcetype="citrix:netscaler:policy"
| where undef_hits > 0
| eval error_ratio=if(hits>0, round(undef_hits/hits*100,2), 100)
| sort -undef_hits
| table policy_name, policy_type, bound_to, hits, undef_hits, error_ratio, host
```
- **Implementation:** Poll the NITRO API `responderpolicy` and `rewritepolicy` resources. Each policy exposes `hits` (successful evaluations) and `undefhits` (evaluation failures). Run every 15 minutes. Alert when any policy has `undefhits > 0` — this indicates the policy expression has a bug. Common causes: referencing a non-existent header, type mismatch in expression, or regex syntax errors. Policies with high `undefhits` relative to `hits` are effectively broken. Also monitor `responderglobal_responderpolicy_binding` and `rewriteglobal_rewritepolicy_binding` for globally bound policies that affect all traffic.
- **Visualization:** Table (policies with undef hits), Bar chart (error ratio by policy type), Timeline (undef hits trending).
- **CIM Models:** N/A

---

### UC-5.3.22 · Citrix ADC SSL Offload Performance (NetScaler)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** Citrix ADC offloads SSL/TLS processing from back-end servers, handling certificate exchange, cipher negotiation, and encryption/decryption. SSL transactions per second (TPS) is a capacity-bound metric — hardware ADC models have fixed SSL TPS limits, and VPX instances are licensed by throughput tier. Approaching the SSL TPS ceiling causes SSL handshake delays and new connection failures. Monitoring SSL performance ensures cryptographic operations do not become a bottleneck.
- **App/TA:** Custom scripted input polling Citrix ADC NITRO API
- **Data Sources:** `index=network` `sourcetype="citrix:netscaler:ssl"` fields `ssl_tps`, `ssl_sessions`, `ssl_new_sessions`, `ssl_session_reuse_pct`, `ssl_protocol_version`, `cipher_suite`
- **SPL:**
```spl
index=network sourcetype="citrix:netscaler:ssl" metric_type="ssl_stats"
| bin _time span=5m
| stats avg(ssl_tps) as avg_tps, max(ssl_tps) as peak_tps, avg(ssl_session_reuse_pct) as reuse_pct by host, _time
| where peak_tps > 5000 OR reuse_pct < 50
| table _time, host, avg_tps, peak_tps, reuse_pct
```
- **Implementation:** Poll the NITRO API `ssl` statistics endpoint for SSL transaction counters: `ssltotsessions`, `ssltotnewsessions`, `ssltottlsv12sessions`, `ssltottlsv13sessions`, and session reuse rates. Calculate TPS as delta of `ssltotsessions` over the poll interval. Key thresholds: SSL TPS approaching 80% of licensed/hardware capacity (plan upgrade), session reuse rate below 50% (misconfigured session caching — excessive full handshakes), and TLS 1.0/1.1 session count > 0 (deprecated protocols in use). Track cipher suite distribution to ensure compliance with security policies (disable weak ciphers like RC4, DES, 3DES).
- **Visualization:** Line chart (SSL TPS over time), Gauge (current TPS vs capacity), Pie chart (protocol version distribution).
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
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580), WLC syslog
- **Equipment Models:** Cisco Meraki MR36, MR44, MR46, MR56, MR57, MR76, MR78, MR86, Cisco WLC 3504, WLC 5520, WLC 8540, Catalyst 9800-40, Catalyst 9800-80, Catalyst 9800-L, Catalyst 9800-CL, Cisco Catalyst 9100 APs, Aironet 1815, Aironet 2802, Aironet 3802, Aironet 4800
- **Data Sources:** `sourcetype=meraki, WLC events`
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
- **Equipment Models:** Cisco WLC 3504, WLC 5520, WLC 8540, Catalyst 9800-40, Catalyst 9800-80, Catalyst 9800-L, Catalyst 9800-CL, Cisco Catalyst 9100 APs, Aironet 1815, Aironet 2802, Aironet 3802, Aironet 4800
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
- **Equipment Models:** Cisco Meraki MR36, MR44, MR46, MR56, MR57, MR76, MR78, MR86, Cisco WLC 3504, WLC 5520, WLC 8540, Catalyst 9800-40, Catalyst 9800-80, Catalyst 9800-L, Catalyst 9800-CL, Cisco Catalyst 9100 APs, Aironet 1815, Aironet 2802, Aironet 3802, Aironet 4800
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
- **Equipment Models:** Cisco WLC 3504, WLC 5520, WLC 8540, Catalyst 9800-40, Catalyst 9800-80, Catalyst 9800-L, Catalyst 9800-CL, Cisco Catalyst 9100 APs, Aironet 1815, Aironet 2802, Aironet 3802, Aironet 4800
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
- **Equipment Models:** Cisco Meraki MR36, MR44, MR46, MR56, MR57, MR76, MR78, MR86, Cisco WLC 3504, WLC 5520, WLC 8540, Catalyst 9800-40, Catalyst 9800-80, Catalyst 9800-L, Catalyst 9800-CL, Cisco Catalyst 9100 APs, Aironet 1815, Aironet 2802, Aironet 3802, Aironet 4800
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
- **Equipment Models:** Cisco WLC 3504, WLC 5520, WLC 8540, Catalyst 9800-40, Catalyst 9800-80, Catalyst 9800-L, Catalyst 9800-CL, Cisco Catalyst 9100 APs, Aironet 1815, Aironet 2802, Aironet 3802, Aironet 4800
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
- **Equipment Models:** Cisco ISE 3515, ISE 3595, ISE 3615, ISE 3655, ISE 3695, ISE Virtual Appliance
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
- **App/TA:** Cisco WLC syslog, `Splunk_TA_cisco-ise`
- **Equipment Models:** Cisco WLC 3504, WLC 5520, WLC 8540, Catalyst 9800-40, Catalyst 9800-80, Catalyst 9800-L, Catalyst 9800-CL, Cisco ISE 3515, ISE 3595, ISE 3615, ISE 3655, ISE 3695, ISE Virtual Appliance
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
- **Equipment Models:** Cisco WLC 3504, WLC 5520, WLC 8540, Catalyst 9800-40, Catalyst 9800-80, Catalyst 9800-L, Catalyst 9800-CL, Cisco Catalyst 9100 APs, Aironet 1815, Aironet 2802, Aironet 3802, Aironet 4800
- **Data Sources:** `sourcetype=cisco:wlc`, `sourcetype=meraki:api`
- **SPL:**
```spl
index=network sourcetype="cisco:wlc" "roam" OR "reassociation"
| transaction client_mac maxspan=1h maxpause=5m
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
- **Equipment Models:** Cisco WLC 3504, WLC 5520, WLC 8540, Catalyst 9800-40, Catalyst 9800-80, Catalyst 9800-L, Catalyst 9800-CL, Cisco Catalyst 9100 APs, Aironet 1815, Aironet 2802, Aironet 3802, Aironet 4800
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
- **Equipment Models:** Cisco WLC 3504, WLC 5520, WLC 8540, Catalyst 9800-40, Catalyst 9800-80, Catalyst 9800-L, Catalyst 9800-CL, Cisco Catalyst 9100 APs, Aironet 1815, Aironet 2802, Aironet 3802, Aironet 4800
- **Data Sources:** `sourcetype=cisco:wlc`, `sourcetype=meraki:api`
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


### UC-5.4.12 · Wireless Client Association Failures (Meraki MR)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Identifies recurring authentication failures and SSID configuration issues that prevent users from connecting to wireless networks.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*Association*" OR signature="*authentication*" status="failure"
| stats count by ap_name, client_mac, reason, signature
| sort -count
```
- **Implementation:** Monitor syslog events from Meraki MR access points for failed association attempts. Correlate with SSID configuration and 802.1X radius responses.
- **Visualization:** Table with top APs/clients by failure count; time-series chart of failures over time by AP.
- **CIM Models:** N/A

---

### UC-5.4.13 · RSSI/Signal Strength Degradation Detection (Meraki MR)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Proactively identifies weak WiFi coverage areas and client placement issues before users experience connectivity problems.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
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

### UC-5.4.14 · Excessive Client Roaming Activity (Meraki MR)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Detects unstable roaming patterns and AP handoff issues that cause latency spikes and dropped connections.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*Roaming*" OR signature="*handoff*"`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*Roaming*" OR signature="*handoff*")
| stats count as roam_count by client_mac, ap_name
| eventstats sum(roam_count) as total_roams by client_mac
| where total_roams > 20
| sort -total_roams
```
- **Implementation:** Track client handoff events between APs. Alert when a single client roams more than threshold in a 15-minute window.
- **Visualization:** Table of heavy roamers; line chart of roaming frequency by client; network diagram showing roam paths.
- **CIM Models:** N/A

---

### UC-5.4.15 · SSID Performance Ranking and Trend Analysis (Meraki MR)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Compares performance across multiple SSIDs to identify underperforming networks and optimize deployment strategy.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
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

### UC-5.4.16 · WiFi Channel Utilization and Interference Detection (Meraki MR)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Identifies channel congestion and interference sources to optimize channel assignments and reduce co-channel interference.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
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

### UC-5.4.17 · Rogue and Unauthorized AP Detection — Air Marshal (Meraki MR)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** Identifies unauthorized wireless networks and malicious APs that may represent security threats or network intrusion attempts.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=air_marshal`
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

### UC-5.4.18 · Client Device Type Distribution and Compliance (Meraki MR)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Tracks device types connecting to network for capacity planning, security policy enforcement, and support optimization.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
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

### UC-5.4.19 · Band Steering Effectiveness Assessment (Meraki MR)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Measures effectiveness of steering clients from 2.4GHz to 5GHz bands to reduce congestion and improve performance.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
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

### UC-5.4.20 · 802.1X Authentication Failures and RADIUS Issues (Meraki MR)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Identifies authentication server problems, credential issues, and 802.1X configuration mismatches.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*802.1X*" OR signature="*Radius*"`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=security_event (signature="*802.1X*" OR signature="*Radius*" OR signature="*authentication*")
| stats count as auth_failures by client_mac, ap_name, signature
| eventstats sum(auth_failures) as total_failures by client_mac
| where total_failures > 10
| sort -total_failures
```
- **Implementation:** Ingest 802.1X and RADIUS-related syslog events. Correlate with RADIUS server logs.
- **Visualization:** Table of failing clients; time-series of auth failures; client-level detail dashboard.
- **CIM Models:** N/A

---

### UC-5.4.21 · Wireless Latency Analysis by SSID and Location (Meraki MR)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Identifies latency patterns across network to optimize AP placement, channel allocation, and client routing.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
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

### UC-5.4.22 · Splash Page Engagement and Redirection Analytics (Meraki MR)
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks guest network splash page performance and user acceptance rates for marketing and network access purposes.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*Splash*"`
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

### UC-5.4.23 · Multicast and Broadcast Storm Detection (Meraki MR)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Anomaly
- **Value:** Identifies multicast/broadcast flooding that degrades wireless performance across multiple client devices.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=flow`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=flow dest="255.255.255.255" OR dest_mac="ff:ff:ff:ff:ff:ff"
| stats sum(sent_bytes) as total_bytes, count as pkt_count by ap_name, src_mac
| where pkt_count > 1000
| sort - pkt_count
```
- **Implementation:** Monitor broadcast/multicast flows in syslog. Set thresholds for abnormal packet rates.
- **Visualization:** Table of broadcast sources; time-series of broadcast packets; alert threshold dashboard.
- **CIM Models:** N/A

---

### UC-5.4.24 · Wireless Health Score Trending (Meraki MR)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Provides a composite health metric across all APs to facilitate executive reporting and trend analysis.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api device_type=MR`
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

### UC-5.4.25 · Connected Client Count Trending and Capacity Planning (Meraki MR)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Tracks client density by AP and SSID for capacity planning and performance optimization.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
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

### UC-5.4.26 · Top Talker Analysis and Bandwidth Hogs (Meraki MR)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Identifies bandwidth-intensive clients and applications to enforce QoS policies and prevent network congestion.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=flow`
- **SPL:**
```spl
index=cisco_network sourcetype="meraki" type=flow
| stats sum(sent_bytes) as upload_bytes, sum(received_bytes) as download_bytes by client_mac, application
| eval total_bytes=upload_bytes+download_bytes
| sort -total_bytes
| head 20
```
- **Implementation:** Analyze flow records from syslog; track data usage by client and application.
- **Visualization:** Table of top talkers; horizontal bar chart of data usage; Sankey diagram of flows.
- **CIM Models:** N/A

---

### UC-5.4.27 · Connection Duration and Session Quality (Meraki MR)
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Analyzes typical session lengths and stability to identify problematic SSIDs or time-based issues.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
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

### UC-5.4.28 · AP Uptime and Availability Monitoring (Meraki MR)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Ensures all access points are online and operational; alerts on unexpected AP outages.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api device_type=MR`
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

### UC-5.4.29 · Mesh Network Link Quality and Backhaul Health (Meraki MR)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Monitors wireless mesh backhaul links to ensure reliability of remote AP connections.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api` (MR), `sourcetype=meraki` (events, e.g. `type=security_event`)
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

### UC-5.4.30 · Guest Network Access Patterns and Usage (Meraki MR)
- **Criticality:** 🟢 Low
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Tracks guest network adoption, usage patterns, and peak times for network provisioning.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api ssid="guest*"`
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

### UC-5.4.31 · WiFi Geolocation and Location Analytics (Meraki MR)
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Uses Cisco Meraki location services to track foot traffic patterns and heat maps in physical spaces.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api location_data=*`
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

### UC-5.4.32 · Wireless Client Association and Roaming Failures (Meraki MR)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** High association failure or roaming failure rates indicate coverage gaps, interference, or AP misconfiguration. Trending supports WLAN troubleshooting and capacity planning.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580), `TA-cisco_ios` (WLC), wireless controller logs
- **Data Sources:** Meraki wireless events, Cisco WLC syslog
- **SPL:**
```spl
index=cisco_network sourcetype=meraki:wireless (event_type="association_failed" OR event_type="roam_failed")
| stats count by ap_serial, ssid, _time span=15m
| where count > 20
| sort -count
```
- **Implementation:** Ingest wireless client events from Meraki or WLC. Extract association and roam outcomes. Alert when failure rate exceeds threshold per AP or SSID. Dashboard by location and time.
- **Visualization:** Table (AP, SSID, failures), Line chart (failure rate over time), Heatmap (AP by location).
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
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API
- **Equipment Models:** Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, ISR 1100 (SD-WAN), ISR 4000 (SD-WAN), vEdge 100, vEdge 1000, vEdge 2000, vEdge 5000, vManage, vSmart, vBond
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
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.5.2 · Site Availability
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Edge device offline = remote site disconnected from the network.
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API
- **Equipment Models:** Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, ISR 1100 (SD-WAN), ISR 4000 (SD-WAN), vEdge 100, vEdge 1000, vEdge 2000, vEdge 5000, vManage, vSmart, vBond
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
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538)
- **Equipment Models:** Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, ISR 1100 (SD-WAN), ISR 4000 (SD-WAN), vEdge 100, vEdge 1000, vEdge 2000, vEdge 5000, vManage, vSmart, vBond
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
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538)
- **Equipment Models:** Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, ISR 1100 (SD-WAN), ISR 4000 (SD-WAN), vEdge 100, vEdge 1000, vEdge 2000, vEdge 5000, vManage, vSmart, vBond
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
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538)
- **Equipment Models:** Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, ISR 1100 (SD-WAN), ISR 4000 (SD-WAN), vEdge 100, vEdge 1000, vEdge 2000, vEdge 5000, vManage, vSmart, vBond
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
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API
- **Equipment Models:** Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, ISR 1100 (SD-WAN), ISR 4000 (SD-WAN), vEdge 100, vEdge 1000, vEdge 2000, vEdge 5000, vManage, vSmart, vBond
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
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538)
- **Equipment Models:** Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, ISR 1100 (SD-WAN), ISR 4000 (SD-WAN), vEdge 100, vEdge 1000, vEdge 2000, vEdge 5000, vManage, vSmart, vBond
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
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.5.8 · Jitter and Latency per Tunnel
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Real-time jitter and latency metrics reveal WAN quality degradation before users complain. Critical for voice/video SLAs.
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), Cisco vManage API
- **Equipment Models:** Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, ISR 1100 (SD-WAN), ISR 4000 (SD-WAN), vEdge 100, vEdge 1000, vEdge 2000, vEdge 5000, vManage, vSmart, vBond
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
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---

### UC-5.5.9 · Application Routing Decisions
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Validates that SD-WAN policies are steering traffic correctly. Detects policy misconfigurations that route real-time traffic over suboptimal paths.
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), Cisco vManage API
- **Equipment Models:** Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, ISR 1100 (SD-WAN), ISR 4000 (SD-WAN), vEdge 100, vEdge 1000, vEdge 2000, vEdge 5000, vManage, vSmart, vBond
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
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), SNMP
- **Equipment Models:** Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, ISR 1100 (SD-WAN), ISR 4000 (SD-WAN), vEdge 100, vEdge 1000, vEdge 2000, vEdge 5000, vManage, vSmart, vBond
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

### UC-5.5.11 · OMP Route Table Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** OMP (Overlay Management Protocol) distributes routes across the SD-WAN fabric. Route churn, missing prefixes, or unexpected withdrawals indicate overlay instability that degrades site-to-site reachability.
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API
- **Equipment Models:** Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, ISR 1100 (SD-WAN), ISR 4000 (SD-WAN), vEdge 100, vEdge 1000, vEdge 2000, vEdge 5000, vManage, vSmart, vBond
- **Data Sources:** vManage OMP route table, `sourcetype=cisco:sdwan:omp`
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:omp"
| stats dc(prefix) as route_count, dc(peer) as peer_count by system_ip, site_id
| appendpipe [| stats avg(route_count) as baseline_routes]
| where route_count < baseline_routes * 0.8
| table system_ip site_id route_count peer_count
```
- **Implementation:** Poll vManage OMP peers and routes API endpoints. Baseline route count per device. Alert when a site loses more than 20% of its expected routes or when OMP peer adjacencies drop. Track route churn rate over time to identify flapping prefixes.
- **Visualization:** Line chart (route count over time per site), Table (devices below baseline), Single value (total OMP peers).
- **CIM Models:** N/A
- **Known false positives:** Planned network changes that withdraw routes intentionally; correlate with change management windows.

---

### UC-5.5.12 · BFD Session Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** BFD (Bidirectional Forwarding Detection) provides sub-second failure detection between SD-WAN endpoints. A BFD session going down means the tunnel is unusable, and traffic must reroute. Tracking BFD flaps reveals transport instability before it cascades.
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API
- **Equipment Models:** Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, ISR 1100 (SD-WAN), ISR 4000 (SD-WAN), vEdge 100, vEdge 1000, vEdge 2000, vEdge 5000, vManage, vSmart, vBond
- **Data Sources:** vManage BFD sessions, `sourcetype=cisco:sdwan:bfd`
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd"
| where state!="up"
| stats count as flap_count, latest(_time) as last_flap, values(state) as states by local_system_ip, remote_system_ip, local_color, remote_color
| where flap_count > 3
| sort -flap_count
| eval last_flap=strftime(last_flap,"%Y-%m-%d %H:%M:%S")
```
- **Implementation:** Collect BFD session data from vManage. Alert immediately when a BFD session transitions from up to down. Track flap frequency per tunnel; more than 3 flaps in an hour signals an unstable transport that needs carrier engagement. Cross-reference with ISP maintenance schedules.
- **Visualization:** Status grid (BFD sessions by color/site), Timeline (session state changes), Table (flapping tunnels).
- **CIM Models:** N/A
- **Known false positives:** Planned ISP maintenance windows; carrier circuit cutovers.

---

### UC-5.5.13 · Edge Device Resource Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance, Capacity
- **Value:** SD-WAN edge routers running high CPU or memory can drop packets, fail to establish tunnels, or crash. Monitoring device resources prevents silent performance degradation at remote sites where physical access is limited.
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API
- **Equipment Models:** Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, ISR 1100 (SD-WAN), ISR 4000 (SD-WAN), vEdge 100, vEdge 1000, vEdge 2000, vEdge 5000
- **Data Sources:** vManage device statistics, `sourcetype=cisco:sdwan:device`
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:device"
| stats latest(cpu_user) as cpu_user, latest(cpu_system) as cpu_system, latest(mem_used) as mem_used, latest(mem_total) as mem_total by hostname, system_ip, site_id
| eval cpu_pct=cpu_user+cpu_system, mem_pct=round(mem_used/mem_total*100,1)
| where cpu_pct > 80 OR mem_pct > 85
| table hostname system_ip site_id cpu_pct mem_pct
| sort -cpu_pct
```
- **Implementation:** Poll vManage device statistics API for CPU, memory, and disk usage. Alert when CPU exceeds 80% or memory exceeds 85% sustained over 15 minutes. Trend over time to identify sites that need hardware upgrades. Pay special attention to devices running UTD (Unified Threat Defense) or DPI, which consume significantly more resources.
- **Visualization:** Line chart (CPU/memory trending per device), Table (devices above threshold), Gauge (fleet-wide average).
- **CIM Models:** Performance
- **CIM SPL:**
```spl
| tstats `summariesonly` avg(Performance.cpu_load_percent) as cpu_pct
  from datamodel=Performance where nodename=Performance.CPU
  by Performance.host span=1h
| where cpu_pct > 80
```

---

### UC-5.5.14 · Firmware Version Compliance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Running inconsistent or outdated software versions across the SD-WAN fabric creates security vulnerabilities and feature gaps. Compliance dashboards accelerate upgrade planning and audit readiness.
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API
- **Equipment Models:** Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, ISR 1100 (SD-WAN), ISR 4000 (SD-WAN), vEdge 100, vEdge 1000, vEdge 2000, vEdge 5000, vManage, vSmart, vBond
- **Data Sources:** vManage device inventory, `sourcetype=cisco:sdwan:device`
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:device"
| stats latest(version) as sw_version, latest(model) as model by hostname, system_ip, site_id
| eventstats count by sw_version
| eval target_version="17.12.04"
| eval compliant=if(sw_version=target_version,"yes","no")
| stats count as total, count(eval(compliant="yes")) as compliant_count by sw_version
| eval pct=round(compliant_count/total*100,1)
| sort -total
```
- **Implementation:** Poll vManage device inventory for software versions and model types. Define a target version per device family. Report on compliance percentage. Alert when devices fall more than two minor versions behind the target. Use to prioritize upgrade batches by site criticality.
- **Visualization:** Pie chart (version distribution), Table (non-compliant devices), Single value (compliance percentage).
- **CIM Models:** N/A

---

### UC-5.5.15 · DPI Application Visibility
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** Deep Packet Inspection on SD-WAN edges classifies traffic by application. Visibility into top applications per site drives policy tuning, bandwidth planning, and identification of shadow IT or unauthorized SaaS usage.
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API
- **Equipment Models:** Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, ISR 1100 (SD-WAN), ISR 4000 (SD-WAN), vEdge 100, vEdge 1000, vEdge 2000, vEdge 5000
- **Data Sources:** vManage DPI statistics, `sourcetype=cisco:sdwan:dpi`
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:dpi"
| stats sum(bytes) as total_bytes, sum(packets) as total_pkts by app_name, family, site_id
| eval GB=round(total_bytes/1073741824,2)
| sort -total_bytes
| head 50
| table app_name family site_id GB total_pkts
```
- **Implementation:** Enable DPI on SD-WAN edge routers (requires UTD container or native NBAR2). Collect application statistics via vManage. Identify top bandwidth consumers per site. Compare against policy expectations — flag when non-business applications (streaming, gaming, social media) consume more than 20% of WAN bandwidth.
- **Visualization:** Bar chart (top 20 apps by volume), Treemap (app families), Table (app, site, volume).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.app span=1d
| sort -bytes | head 20
```

---

### UC-5.5.16 · Cloud OnRamp Performance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Cloud OnRamp probes SaaS and IaaS endpoints from each site to select the best path. Monitoring probe results reveals when cloud application performance degrades before users open tickets, and validates that SD-WAN is actually improving cloud access.
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API
- **Equipment Models:** Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, ISR 1100 (SD-WAN), ISR 4000 (SD-WAN), vEdge 100, vEdge 1000, vEdge 2000, vEdge 5000
- **Data Sources:** vManage Cloud OnRamp metrics, `sourcetype=cisco:sdwan:cloudx`
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:cloudx"
| stats avg(vqoe_score) as avg_score, avg(latency) as avg_latency, avg(loss) as avg_loss by app_name, site_id, exit_type
| where avg_score < 8 OR avg_latency > 150
| sort avg_score
| table app_name site_id exit_type avg_score avg_latency avg_loss
```
- **Implementation:** Enable Cloud OnRamp for SaaS (Microsoft 365, Webex, Salesforce, etc.) and/or IaaS (AWS, Azure, GCP) in vManage. Collect vQoE scores and probe metrics. Alert when a SaaS application's quality score drops below 8 (out of 10) or latency exceeds 150ms. Compare direct internet access (DIA) vs gateway exit paths to validate routing decisions.
- **Visualization:** Line chart (vQoE score trending per app), Table (underperforming apps), Bar chart (DIA vs gateway comparison).
- **CIM Models:** N/A
- **Known false positives:** SaaS provider outages will degrade scores regardless of WAN path; cross-reference with provider status pages.

---

### UC-5.5.17 · Security Policy Violations (UTD)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Security
- **Value:** SD-WAN edges running Unified Threat Defense (UTD) perform IPS, URL filtering, and AMP inline. Monitoring these events at the WAN edge catches threats that bypass centralized firewalls, especially for direct internet access (DIA) traffic that never traverses the data center.
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API
- **Equipment Models:** Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, ISR 1100 (SD-WAN), ISR 4000 (SD-WAN)
- **Data Sources:** vManage UTD events, `sourcetype=cisco:sdwan:utd`
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:utd"
| stats count by event_type, signature, severity, src_ip, dst_ip, site_id
| where severity IN ("critical","high")
| sort -count
| table event_type signature severity src_ip dst_ip site_id count
```
- **Implementation:** Enable UTD (IPS/URL filtering/AMP) on SD-WAN edges handling DIA traffic. Collect security events via vManage. Alert on critical/high severity IPS signatures and malware detections. Correlate with Umbrella/Secure Access if deployed for layered defense. Track blocked URL categories to refine acceptable-use policies.
- **Visualization:** Table (signature, severity, source, destination), Bar chart (events by category), Timeline (event frequency).
- **CIM Models:** Intrusion_Detection
- **CIM SPL:**
```spl
| tstats `summariesonly` count
  from datamodel=Intrusion_Detection
  by IDS_Attacks.signature, IDS_Attacks.severity, IDS_Attacks.src, IDS_Attacks.dest span=1h
| where count > 0
| sort -count
```

---

### UC-5.5.18 · vManage Cluster Health
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** vManage is the single management plane for the entire SD-WAN fabric. If the vManage cluster is unhealthy — high CPU, disk full, database replication lag, or services down — operators lose visibility and policy push capability across all sites.
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API
- **Equipment Models:** vManage (physical or virtual)
- **Data Sources:** vManage cluster status API, `sourcetype=cisco:sdwan:vmanage`
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:vmanage"
| stats latest(cpu_load) as cpu, latest(mem_util) as mem_pct, latest(disk_util) as disk_pct, latest(db_status) as db_status, latest(services_running) as services by vmanage_ip
| where cpu > 70 OR mem_pct > 80 OR disk_pct > 75 OR db_status!="healthy"
| table vmanage_ip cpu mem_pct disk_pct db_status services
```
- **Implementation:** Poll vManage cluster health API. Monitor CPU, memory, disk usage, NMS database replication status, and running services. For clustered deployments, verify all nodes are in sync. Alert when any node exceeds 70% CPU, 80% memory, or 75% disk, or when database replication falls behind. Schedule regular config database backups independently.
- **Visualization:** Single value panels (CPU, memory, disk per node), Status indicator (cluster health), Table (services status).
- **CIM Models:** N/A

---

### UC-5.5.19 · Transport Circuit SLA Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Value:** ISPs commit to contractual SLAs for latency, jitter, loss, and uptime per circuit. SD-WAN BFD metrics provide continuous proof of whether carriers meet their commitments. SLA violation evidence supports service credits and carrier negotiations.
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API
- **Equipment Models:** Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, ISR 1100 (SD-WAN), ISR 4000 (SD-WAN), vEdge 100, vEdge 1000, vEdge 2000, vEdge 5000
- **Data Sources:** `sourcetype=cisco:sdwan:bfd`, `sourcetype=cisco:sdwan:interface`
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd"
| stats avg(latency) as avg_latency, perc95(latency) as p95_latency, avg(jitter) as avg_jitter, avg(loss_percentage) as avg_loss, count as samples by local_color, site_id, remote_system_ip
| eval sla_latency=50, sla_loss=0.1
| eval latency_breach=if(avg_latency>sla_latency,"YES","NO"), loss_breach=if(avg_loss>sla_loss,"YES","NO")
| where latency_breach="YES" OR loss_breach="YES"
| table site_id local_color avg_latency p95_latency avg_jitter avg_loss latency_breach loss_breach
```
- **Implementation:** Define contractual SLA thresholds per transport type (MPLS: latency <50ms, loss <0.1%; Internet: latency <80ms, loss <0.5%). Aggregate BFD metrics daily. Generate monthly SLA compliance reports per carrier per circuit. Include uptime percentage from interface state changes. Use as evidence for carrier escalations and service credit claims.
- **Visualization:** Table (circuit SLA compliance), Line chart (latency trending per carrier), Single value (overall SLA compliance %).
- **CIM Models:** N/A

---

### UC-5.5.20 · Hub-and-Spoke vs Full-Mesh Topology Validation
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Configuration
- **Value:** SD-WAN overlay topology determines traffic flow patterns. Validating that the actual tunnel mesh matches the intended design prevents asymmetric routing, hairpinning through hubs, and suboptimal site-to-site paths that add latency and waste hub bandwidth.
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API
- **Equipment Models:** Cisco Catalyst 8200, Catalyst 8300, Catalyst 8500, ISR 1100 (SD-WAN), ISR 4000 (SD-WAN), vEdge 100, vEdge 1000, vEdge 2000, vEdge 5000, vManage, vSmart
- **Data Sources:** vManage BFD sessions, OMP routes, `sourcetype=cisco:sdwan:bfd`
- **SPL:**
```spl
index=sdwan sourcetype="cisco:sdwan:bfd" state="up"
| stats dc(remote_system_ip) as peer_count, values(remote_system_ip) as peers by local_system_ip, site_id
| eventstats avg(peer_count) as avg_peers
| eval topology=case(peer_count>avg_peers*1.5,"full-mesh candidate",peer_count<=2,"spoke",1=1,"partial-mesh")
| table site_id local_system_ip peer_count topology
| sort -peer_count
```
- **Implementation:** Map the active tunnel mesh by enumerating BFD sessions per device. Compare against the intended topology (hub-and-spoke, regional hub, full-mesh). Identify sites with fewer tunnels than expected (potential reachability gaps) or more tunnels than intended (resource waste). Review when deploying new sites or changing control policies.
- **Visualization:** Network graph (nodes = sites, edges = tunnels), Table (site, peer count, topology type), Bar chart (topology distribution).
- **CIM Models:** N/A
- **Known false positives:** On-demand dynamic tunnels (TLOC extension) may create temporary additional peers that do not indicate misconfiguration.

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
| stats avg(query_len) as avg_len, count as queries, dc(query) as unique_queries by src, domain
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
| table _time host src _raw | sort -_time
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


### UC-5.6.13 · Failed DHCP Assignments and IP Pool Exhaustion (Meraki)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Detects DHCP server failures and IP pool exhaustion that prevent new clients from obtaining addresses.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*DHCP*"`
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

### UC-5.6.14 · DNS Resolution Performance and Failures (Meraki)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Monitors DNS query resolution times and failures to identify misconfiguration or server issues affecting user experience.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*DNS*"`
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

### UC-5.6.15 · DHCP Pool Exhaustion and Address Allocation Issues (Meraki)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Value:** Alerts when DHCP pools approach depletion to prevent clients from obtaining IP addresses.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
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

### UC-5.6.16 · DHCP Lease Exhaustion and Scope Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Exhausted DHCP scopes prevent new devices from joining the network. Monitoring utilization and lease count supports proactive scope expansion or cleanup.
- **App/TA:** Infoblox, Microsoft DHCP, ISC DHCP — scripted input or API
- **Data Sources:** DHCP server logs, lease table export, SNMP (DHCP pool MIB)
- **SPL:**
```spl
index=network sourcetype=dhcp_scope
| eval used_pct=round(leases_in_use/scope_size*100, 1)
| stats latest(used_pct) as pct, latest(leases_in_use) as used by scope_name, server
| where pct > 85
| table scope_name server used scope_size pct
```
- **Implementation:** Poll DHCP server (Infoblox API, Windows WMI, or lease file) for scope size and in-use count. Ingest daily or hourly. Alert when utilization exceeds 85%. Track lease duration and stale lease cleanup.
- **Visualization:** Gauge per scope, Table (scope, used, size, %), Line chart (utilization trend).
- **CIM Models:** N/A

---

### UC-5.6.17 · DNS Query Latency and Resolution Failure by Resolver
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Slow or failing DNS resolution impacts all applications. Tracking latency and NXDOMAIN/timeout rates per resolver supports capacity and upstream provider decisions.
- **App/TA:** Custom scripted input (dig, DNS query log), Infoblox/BIND query logs
- **Data Sources:** DNS resolver query logs, synthetic DNS probes
- **SPL:**
```spl
index=network sourcetype=dns_query
| stats avg(response_time_ms) as avg_ms, count(eval(response_code="NXDOMAIN" OR response_code="SERVFAIL")) as failures, count as total by resolver_ip, _time span=5m
| eval fail_rate=round(failures/total*100, 2)
| where avg_ms > 200 OR fail_rate > 5
| table resolver_ip avg_ms fail_rate total
```
- **Implementation:** Run synthetic DNS probes (e.g. dig to critical domains) from multiple hosts; ingest response time and result. Optionally ingest resolver query logs. Alert when latency exceeds 200ms or failure rate exceeds 5%.
- **Visualization:** Line chart (latency by resolver), Table (resolver, avg ms, fail rate), Single value (p95 latency).
- **CIM Models:** N/A

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
| stats sum(bytes) as total_bytes by src, dest
| sort -total_bytes | head 20
| eval total_GB=round(total_bytes/1073741824,2)
```
- **Implementation:** Export NetFlow from routers/switches to a NetFlow collector that forwards to Splunk. Install NetFlow TA for field parsing.
- **Visualization:** Table (source, dest, bytes), Sankey diagram, Bar chart.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| eval bytes=bytes_in+bytes_out
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
| stats dc(dest_port) as unique_ports, dc(dest) as unique_dests by src
| where unique_ports > 100 OR unique_dests > 500
| sort -unique_ports
```
- **Implementation:** Baseline normal flow patterns over 30 days. Alert on new protocol/port combinations, new external destinations, or unusual volume patterns.
- **Visualization:** Table, Scatter plot (ports vs. destinations), Timechart.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
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
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| eval bytes=bytes_in+bytes_out
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
| where cidrmatch("10.0.0.0/8",src) AND cidrmatch("10.0.0.0/8",dest)
| stats sum(bytes) as bytes, count as flows by src, dest, dest_port
| sort -bytes | head 50
```
- **Implementation:** Export NetFlow from internal router/switch interfaces. Analyze internal traffic patterns. Establish baseline for anomaly detection.
- **Visualization:** Chord diagram, Table, Sankey diagram.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
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
| stats sum(bytes) as total_bytes by src, dest
| where total_bytes > 1073741824
| lookup known_destinations dest OUTPUT known
| where isnull(known)
| sort -total_bytes
```
- **Implementation:** Baseline normal outbound transfer volumes per host. Alert when transfers exceed threshold to unknown destinations. Correlate with DNS and firewall logs.
- **Visualization:** Table, Bar chart, Map (destination GeoIP).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
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
| stats dc(dest_port) as unique_ports by src, dest
| where unique_ports > 50
| sort -unique_ports
```
- **Implementation:** Detect hosts connecting to >50 unique ports on a single target in 5 minutes. Alert with source and target details.
- **Visualization:** Table, Scatter plot, Timeline.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
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
| stats sum(bytes) as total_bytes dc(src) as unique_sources by protocol, service_name
| eval GB=round(total_bytes/1073741824,2) | sort -total_bytes
| head 20
```
- **Implementation:** Collect NetFlow/sFlow/IPFIX from routers and switches. Map port numbers to service names via lookup. Baseline protocol distribution. Alert on new protocols or significant shifts.
- **Visualization:** Pie chart (by protocol), Treemap (by service + volume), Timechart.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
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
index=network sourcetype="netflow" dest="224.0.0.0/4"
| stats sum(bytes) as total_bytes, dc(src) as sources by dest
| eval MB=round(total_bytes/1048576,1) | sort -total_bytes
| head 20
```
- **Implementation:** Enable NetFlow on core/distribution switches. Filter for multicast destination range (224.0.0.0/4). Baseline expected multicast groups. Alert on new or high-volume groups.
- **Visualization:** Table (multicast group, volume, sources), Timechart (multicast volume), Bar chart.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
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
| stats sum(bytes) as bytes, dc(src) as unique_hosts by src_vlan, input_interface
| sort -bytes
```
- **Implementation:** Map flow data to VLANs via input interface. Maintain a lookup of authorized VLANs per port. Alert on traffic from unauthorized VLANs. Correlate with 802.1X status.
- **Visualization:** Table (VLAN, interface, hosts, volume), Alert panel, Status grid.
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
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
| stats sum(bytes) as total_bytes, max(duration_min) as max_duration by src, dest, dest_port
| eval GB=round(total_bytes/1073741824,2) | sort -max_duration
| head 20
```
- **Implementation:** Analyze flow records for duration >60 minutes. Cross-reference with known long-lived services (VPN, database replication). Flag unknown long flows for investigation.
- **Visualization:** Table (source, destination, port, duration, bytes), Scatter plot (duration vs. bytes).
- **CIM Models:** Network_Traffic
- **CIM SPL:**
```spl
| tstats `summariesonly` count sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.action span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

---


## 5.8 Network Management Platforms

**Primary App/TA:** Cisco DNA Center TA, Meraki TA, syslog/SNMP trap receivers

---

### UC-5.8.1 · DNA Center Assurance Alerts (Cisco Catalyst Center)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** DNA Center provides AI/ML-driven network issue detection. Centralizing in Splunk enables cross-domain correlation.
- **App/TA:** `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538)
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
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Equipment Models:** Cisco Meraki MX64, MX67, MX68, MX75, MX84, MX85, MX95, MX100, MX105, MX250, MX450, Cisco Meraki MR36, MR44, MR46, MR56, MR57, MR76, MR78, MR86, Cisco Meraki MS120, MS125, MS130, MS210, MS225, MS250, MS350, MS390
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


### UC-5.8.9 · SSL/TLS Certificate Expiration Tracking (Meraki)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Monitors SSL certificate expiration dates on all network devices to prevent outages.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
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

### UC-5.8.10 · Firmware Update Compliance and Version Tracking (Meraki)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Compliance
- **Value:** Ensures all network devices run supported firmware versions and patches.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
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

### UC-5.8.11 · API Call Rate Monitoring and Rate Limit Alerts (Meraki)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Monitors API usage to prevent rate limit hits and optimize automation efficiency.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
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

### UC-5.8.12 · License Expiration Tracking and Renewal Alerts (Meraki)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Ensures licenses don't expire unexpectedly and features remain available.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
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

### UC-5.8.13 · Network Device Inventory and Change Audit (Meraki)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Configuration
- **Value:** Maintains accurate inventory of network devices and tracks hardware/software changes.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
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

### UC-5.8.14 · Admin Activity Logging and Access Control Audit (Meraki)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Tracks administrator actions and logins for compliance and security auditing.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*admin*" OR signature="*login*"`
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

### UC-5.8.15 · Admin Privilege Changes and Permission Escalation (Meraki)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Detects unauthorized privilege changes and permission escalation attempts.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*privilege*" OR signature="*permission*"`
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

### UC-5.8.16 · Alert Volume Trending and Alert Fatigue Analysis (Meraki)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Value:** Analyzes alert volume trends to optimize alerting rules and reduce false positives.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580, webhooks)
- **Data Sources:** `sourcetype=meraki:webhook`
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

### UC-5.8.17 · Network Health Score Aggregation and Executive Reporting (Meraki)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Provides high-level network health metric for executive dashboards and trend reporting.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
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

### UC-5.8.18 · Device Online/Offline Status Monitoring (Meraki)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Tracks device connectivity status to quickly identify and respond to device failures.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
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

### UC-5.8.19 · Multi-Organization Comparison and Benchmarking (Meraki)
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Compares metrics across organizations to identify best practices and outliers.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
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

### UC-5.8.20 · Configuration Change Window Compliance (Meraki)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Ensures configuration changes only occur within approved maintenance windows.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki type=security_event signature="*config*"`
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

### UC-5.8.21 · Webhook Delivery Failure Tracking (Meraki)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Fault
- **Value:** Ensures webhook notifications reach integrations and alerts don't get lost.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580, webhooks)
- **Data Sources:** `sourcetype=meraki:webhook status="failure" OR status="error"`
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

### UC-5.8.22 · API Error Rate and Endpoint Health (Meraki)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Monitors API endpoint health and error rates to ensure automation reliability.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api (http_status_code=4* OR http_status_code=5*)`
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

### UC-5.8.23 · Dashboard Configuration and Export Backup (Meraki)
- **Criticality:** 🟢 Low
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Compliance
- **Value:** Tracks dashboard configuration backups to enable disaster recovery and configuration review.
- **App/TA:** `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)
- **Data Sources:** `sourcetype=meraki:api`
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

### UC-5.8.24 · Network Device Configuration Backup and Drift
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Configuration
- **Value:** Missing or stale configuration backups complicate recovery after failure or bad change. Detecting backup failure or config drift supports change control and RTO.
- **App/TA:** RANCID, Oxidized, custom scripted input
- **Data Sources:** Backup job output, config repository (Git), device config fetch
- **SPL:**
```spl
index=network sourcetype=config_backup
| stats latest(backup_ok) as ok, latest(backup_time) as last_backup by device_hostname
| where ok != 1 OR (now()-last_backup) > 86400
| table device_hostname ok last_backup
```
- **Implementation:** Run config backup (RANCID, Oxidized, or vendor API) on schedule. Ingest success/failure and timestamp. Alert when backup fails or last successful backup is older than 24 hours. Optionally diff current vs. last backup for drift.
- **Visualization:** Table (device, last backup, status), Single value (devices without backup today), Timeline (backup runs).
- **CIM Models:** N/A

---

### UC-5.8.25 · SNMP Trap Storm Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Fault
- **Value:** Excessive SNMP traps from a device indicating failure cascade.
- **App/TA:** SNMP modular input (trap receiver)
- **Equipment Models:** Various (SNMP-enabled network devices)
- **Data Sources:** snmptrapd, Splunk SNMP trap input
- **SPL:**
```spl
index=network sourcetype=snmptrap
| bin _time span=1m
| stats count as trap_count by host, _time
| eventstats avg(trap_count) as avg_traps, stdev(trap_count) as std_traps by host
| where trap_count > (avg_traps + 3*std_traps) OR trap_count > 100
| sort -trap_count
```
- **Implementation:** Configure Splunk SNMP trap input or forward traps from snmptrapd. Parse trap OID and host. Alert when trap rate from a single device exceeds 100/min or 3 standard deviations above baseline. Trap storms often indicate device failure, link flapping, or misconfiguration.
- **Visualization:** Line chart (traps per host over time), Table (host, count, threshold), Single value (devices in storm).
- **CIM Models:** N/A

---


## 5.9 Cisco ThousandEyes

**Primary App/TA:** Cisco ThousandEyes App for Splunk (Splunkbase 7719) — Cisco Supported

---

### UC-5.9.1 · Network Latency Monitoring (Agent-to-Server)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks round-trip latency from ThousandEyes agents to target servers, revealing network path degradation before users report slowness.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| stats avg(network.latency) as avg_latency_s max(network.latency) as max_latency_s by thousandeyes.source.agent.name, server.address
| eval avg_latency_ms=round(avg_latency_s*1000,1), max_latency_ms=round(max_latency_s*1000,1)
| where avg_latency_ms > 100
| sort -avg_latency_ms
```
- **Implementation:** Install the Cisco ThousandEyes App for Splunk and configure the Tests Stream — Metrics input with HEC. Select the Agent-to-Server tests to stream. Update the `stream_index` macro to point to the correct index. The OTel metric `network.latency` reports maximum round-trip time in seconds.
- **Visualization:** Line chart (latency per agent over time), Single value (avg latency), Table (agent, server, latency).
- **CIM Models:** N/A

---

### UC-5.9.2 · Network Packet Loss Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Packet loss directly degrades application performance, voice quality, and video conferencing. Even 1% loss can cause noticeable user impact.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| stats avg(network.loss) as avg_loss max(network.loss) as max_loss by thousandeyes.source.agent.name, server.address
| where avg_loss > 0.5
| sort -avg_loss
```
- **Implementation:** Configure Agent-to-Server tests in ThousandEyes and stream metrics to Splunk via HEC. The OTel metric `network.loss` reports packet loss as a percentage. Alert when average loss exceeds 0.5% for critical paths.
- **Visualization:** Line chart (loss % over time per agent/server), Single value (current loss), Table sorted by loss.
- **CIM Models:** N/A

---

### UC-5.9.3 · Network Jitter Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Jitter (variation in packet delay) directly affects real-time applications like VoIP and video. High jitter degrades voice quality even when latency is acceptable.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| stats avg(network.jitter) as avg_jitter_ms max(network.jitter) as max_jitter_ms by thousandeyes.source.agent.name, server.address
| where avg_jitter_ms > 30
| sort -avg_jitter_ms
```
- **Implementation:** The OTel metric `network.jitter` reports the standard deviation of round-trip times in milliseconds. Jitter above 30 ms typically degrades voice quality. Correlate with `network.latency` and `network.loss` for a complete path quality picture.
- **Visualization:** Line chart (jitter ms over time), Combined chart (latency + jitter + loss), Table.
- **CIM Models:** N/A

---

### UC-5.9.4 · Agent-to-Agent Latency and Throughput
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Measures bidirectional network performance between two ThousandEyes agents, useful for assessing site-to-site WAN link quality and SD-WAN overlay performance.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="agent-to-agent"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter_ms by thousandeyes.source.agent.name, thousandeyes.target.agent.name, network.io.direction
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort thousandeyes.source.agent.name, network.io.direction
```
- **Implementation:** Create Agent-to-Agent tests in ThousandEyes between sites and stream metrics. The `network.io.direction` attribute distinguishes `transmit`, `receive`, and `round-trip` measurements. Compare forward and reverse paths to identify asymmetric routing issues.
- **Visualization:** Table (source agent, target agent, direction, latency, loss, jitter), Line chart per direction.
- **CIM Models:** N/A

---

### UC-5.9.5 · Path Hop Count Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Sudden changes in the number of hops to a target can indicate routing changes, path instability, or sub-optimal traffic engineering. The Splunk App provides min-hop drilldowns on the Network dashboard.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes Path Visualization data
- **SPL:**
```spl
`path_viz_index` thousandeyes.test.type="agent-to-server"
| stats min(hop_count) as min_hops max(hop_count) as max_hops by thousandeyes.source.agent.name, server.address
| where max_hops - min_hops > 2
| sort -max_hops
```
- **Implementation:** Enable "Include Network Path Data" in the Tests Stream — Metrics input configuration. Update the `path_viz_index` macro to the correct index. Path Visualization data is collected at a configurable interval via the ThousandEyes API.
- **Visualization:** Single value (min hops per target), Table (agent, server, min hops, max hops), Line chart (hop count trending).
- **CIM Models:** N/A

---

### UC-5.9.6 · Network Path Change Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Anomaly
- **Value:** Detects when the network path between an agent and a target changes, which can indicate routing instability, ISP re-routing, or failover events. Correlating path changes with latency spikes helps isolate root cause.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes Path Visualization data
- **SPL:**
```spl
`path_viz_index` thousandeyes.test.type="agent-to-server"
| stats dc(path_hash) as unique_paths count by thousandeyes.source.agent.name, server.address
| where unique_paths > 1
| sort -unique_paths
```
- **Implementation:** Path Visualization data must be enabled in the Tests Stream input. This use case requires building a path fingerprint (hash of intermediate hops) over time windows to detect when routes shift. Correlate with `network.latency` from the metrics stream to identify performance-impacting path changes.
- **Visualization:** Timeline (path changes over time), Table (agent, server, unique paths), Drilldown to ThousandEyes via `thousandeyes.permalink`.
- **CIM Models:** N/A

---

### UC-5.9.7 · WAN Link Quality Scoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Composite quality score derived from latency, loss, and jitter provides a single metric for WAN link health, simplifying executive reporting and SLA tracking.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="agent-to-server" OR thousandeyes.test.type="agent-to-agent"
| stats avg(network.latency) as avg_lat avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.source.agent.name, server.address
| eval latency_score=if(avg_lat<0.05,100,if(avg_lat<0.1,80,if(avg_lat<0.2,60,if(avg_lat<0.5,40,20))))
| eval loss_score=if(avg_loss<0.1,100,if(avg_loss<0.5,80,if(avg_loss<1,60,if(avg_loss<3,40,20))))
| eval jitter_score=if(avg_jitter<5,100,if(avg_jitter<15,80,if(avg_jitter<30,60,if(avg_jitter<50,40,20))))
| eval quality_score=round((latency_score*0.4 + loss_score*0.35 + jitter_score*0.25),0)
| sort quality_score
```
- **Implementation:** For Endpoint agents the OTel metric `network.score` provides a pre-computed composite. For Cloud and Enterprise Agent tests, calculate a weighted score from latency, loss, and jitter as shown. Adjust weights and thresholds for your SLA requirements.
- **Visualization:** Gauge (quality score per link), Table (all links ranked), Trend line chart.
- **CIM Models:** N/A

---

### UC-5.9.8 · BGP Reachability Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Monitors whether BGP-advertised prefixes are reachable from global vantage points. Loss of reachability means users in affected regions cannot reach your services.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (BGP tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="bgp"
| stats avg(bgp.reachability) as avg_reachability by thousandeyes.monitor.name, network.prefix
| where avg_reachability < 100
| sort avg_reachability
```
- **Implementation:** Create BGP tests in ThousandEyes for your critical prefixes and stream to Splunk. The OTel metric `bgp.reachability` reports a percentage — 100% means the prefix is reachable from that monitor. The Splunk App Network dashboard includes a BGP Reachability map panel.
- **Visualization:** Map (BGP reachability by monitor location), Single value (overall reachability %), Table (monitor, prefix, reachability).
- **CIM Models:** N/A

---

### UC-5.9.9 · BGP Path Change Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Anomaly
- **Value:** BGP path changes indicate routing instability. Frequent path changes can cause traffic to take sub-optimal routes, increasing latency or traversing unexpected transit providers.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (BGP tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="bgp"
| timechart span=1h sum(bgp.path_changes.count) as path_changes by thousandeyes.monitor.name
```
- **Implementation:** The OTel metric `bgp.path_changes.count` tracks the number of route changes per collection interval. The Splunk App Network dashboard includes a "BGP Path Changes Count" line chart. Correlate spikes with ISP maintenance windows or upstream provider issues.
- **Visualization:** Line chart (path changes over time per monitor), Bar chart (total changes per monitor), Table with drilldown.
- **CIM Models:** N/A

---

### UC-5.9.10 · BGP Update Volume Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Anomaly
- **Value:** High BGP update volumes can indicate route flapping, peer instability, or DDoS-related route manipulation. Trending helps establish baselines and detect anomalies.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (BGP tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="bgp"
| timechart span=1h sum(bgp.updates.count) as bgp_updates by thousandeyes.monitor.name
```
- **Implementation:** The OTel metric `bgp.updates.count` tracks the number of BGP updates. The Splunk App Network dashboard includes a "BGP Updates Count" line chart. Set alerts when update volume exceeds 3 standard deviations from baseline.
- **Visualization:** Line chart (updates over time), Single value (current update rate), Table (monitor, prefix, update count).
- **CIM Models:** N/A

---

### UC-5.9.11 · BGP AS Path Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Anomaly
- **Value:** Tracking AS path changes reveals when traffic is routed through unexpected autonomous systems, which can indicate route leaks, hijacks, or ISP peering changes.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (BGP tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="bgp"
| stats dc(network.as.path) as unique_paths values(network.as.path) as as_paths by network.prefix, thousandeyes.monitor.name
| where unique_paths > 1
| sort -unique_paths
```
- **Implementation:** The OTel attribute `network.as.path` provides the full AS path as a space-separated list of ASNs. By tracking distinct AS paths over time for each prefix and monitor, you can detect when routing changes introduce new transit providers. Combine with `bgp.path_changes.count` spikes to focus investigation.
- **Visualization:** Table (prefix, monitor, AS paths seen), Timeline of path changes, Alert on new AS path appearance.
- **CIM Models:** N/A

---

### UC-5.9.12 · Prefix Reachability by Region
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Comparing BGP prefix reachability across geographic regions identifies regional outages or ISP-specific routing issues that affect only certain user populations.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (BGP tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="bgp"
| stats avg(bgp.reachability) as avg_reachability by thousandeyes.monitor.location, network.prefix
| eval region=case(
    match(thousandeyes.monitor.location,"US\|CA\|MX\|BR"),"Americas",
    match(thousandeyes.monitor.location,"GB\|DE\|FR\|NL"),"EMEA",
    match(thousandeyes.monitor.location,"JP\|SG\|AU\|IN"),"APAC",
    1=1,"Other")
| stats avg(avg_reachability) as regional_reachability by region, network.prefix
| sort region, network.prefix
```
- **Implementation:** BGP monitors are distributed globally. Group reachability results by `thousandeyes.monitor.location` and aggregate into regions. A prefix that is 100% reachable in Americas but <80% in APAC indicates a regional routing problem.
- **Visualization:** Map (reachability by monitor location), Table (region, prefix, reachability), Column chart comparing regions.
- **CIM Models:** N/A

---

### UC-5.9.13 · DNS Availability Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** DNS failures cascade into application outages — if users cannot resolve names, nothing works. ThousandEyes DNS tests monitor availability from multiple global vantage points.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (DNS tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="dns-server"
| stats avg(dns.lookup.availability) as avg_availability by dns.question.name, server.address
| where avg_availability < 100
| sort avg_availability
```
- **Implementation:** Create DNS Server tests in ThousandEyes targeting critical domain names and DNS servers. The OTel metric `dns.lookup.availability` reports 100% when resolution succeeds and 0% on error. The Splunk App Network dashboard includes a "DNS Availability (%)" line chart with drilldown to ThousandEyes.
- **Visualization:** Line chart (availability % over time), Single value (current availability), Table (question, server, availability).
- **CIM Models:** N/A

---

### UC-5.9.14 · DNS Resolution Time Trending
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Slow DNS resolution adds latency to every connection. Trending resolution time helps identify degrading DNS infrastructure or inefficient recursive resolution chains.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (DNS tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="dns-server"
| timechart span=5m avg(dns.lookup.duration) as avg_dns_duration_s by dns.question.name
| eval avg_dns_duration_ms=round(avg_dns_duration_s*1000,1)
```
- **Implementation:** The OTel metric `dns.lookup.duration` reports DNS resolve time in seconds. The Splunk App Network dashboard includes a "DNS Duration (s)" line chart. Alert when resolution time exceeds 200 ms consistently — this adds noticeable delay to every new connection.
- **Visualization:** Line chart (resolution time over time by domain), Table with drilldown to ThousandEyes.
- **CIM Models:** N/A

---

### UC-5.9.15 · DNSSEC Validity Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** DNSSEC validation failures cause hard resolution failures for DNSSEC-enforcing resolvers. Monitoring validity ensures the DNSSEC chain of trust remains intact.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (DNSSEC tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="dns-dnssec"
| stats avg(dns.lookup.validity) as avg_validity by dns.question.name
| where avg_validity < 100
| sort avg_validity
```
- **Implementation:** Create DNSSEC tests in ThousandEyes for domains where you manage DNSSEC signing. The OTel metric `dns.lookup.validity` reports 100% when the DNSSEC chain validates successfully and 0% on failure. The Splunk App Network dashboard includes a "DNS Validity (%)" line chart.
- **Visualization:** Line chart (validity % over time), Single value (current validity), Table.
- **CIM Models:** N/A

---

### UC-5.9.16 · DNS Provider Comparison
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Comparing resolution times across DNS providers (internal recursive resolvers, external providers like Cloudflare, Google, ISP resolvers) helps optimize DNS configuration for lowest latency.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (DNS tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="dns-server"
| stats avg(dns.lookup.duration) as avg_duration_s avg(dns.lookup.availability) as avg_availability by server.address, dns.question.name
| eval avg_duration_ms=round(avg_duration_s*1000,1)
| sort dns.question.name, avg_duration_ms
```
- **Implementation:** Create DNS Server tests in ThousandEyes for the same domain against multiple DNS server addresses. Each test targets a different resolver. Compare `dns.lookup.duration` and `dns.lookup.availability` across server addresses.
- **Visualization:** Column chart (resolution time by provider), Table (provider, domain, duration, availability), Comparison dashboard.
- **CIM Models:** N/A

---

### UC-5.9.17 · DNS Trace Delegation Chain Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** DNS Trace tests follow the full delegation chain from root to authoritative server. Monitoring availability and duration across the chain identifies issues at specific levels of the DNS hierarchy.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (DNS Trace tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="dns-trace"
| stats avg(dns.lookup.availability) as avg_availability avg(dns.lookup.duration) as avg_duration_s by dns.question.name, thousandeyes.source.agent.name
| eval avg_duration_ms=round(avg_duration_s*1000,1)
| where avg_availability < 100 OR avg_duration_ms > 500
| sort avg_availability, -avg_duration_ms
```
- **Implementation:** Create DNS Trace tests in ThousandEyes for critical domains. Unlike DNS Server tests that query a specific resolver, DNS Trace tests follow the entire delegation chain from root servers. The same `dns.lookup.availability` and `dns.lookup.duration` metrics are reported.
- **Visualization:** Line chart (duration over time), Table (domain, agent, availability, duration), Alert on failures.
- **CIM Models:** N/A

---

### UC-5.9.18 · Network Outage Event Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** ThousandEyes Internet Insights uses collective intelligence from billions of daily measurements to automatically detect network outages affecting your services, including outages in ISP and cloud provider networks you do not own.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes Event API
- **SPL:**
```spl
`event_index` type="Network Outage" OR type="Network Path Issue"
| stats count by type, severity, state
| sort -count
```
- **Implementation:** Configure the Event input in the Cisco ThousandEyes App with a ThousandEyes user and account group. Update the `event_index` macro to point to the correct index. Events are fetched at a configurable interval via the ThousandEyes API. Event types include "Network Outage", "Network Path Issue", "DNS Issue", "Server Issue", "Proxy Issue", and "Local Agent Issue".
- **Visualization:** Events timeline, Table (type, severity, state, count), Pie chart by severity.
- **CIM Models:** N/A

---

### UC-5.9.19 · ISP Performance Degradation Alerts
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** ThousandEyes alerts notify when ISP-level degradation is detected. Ingesting these alerts into Splunk provides a centralized view alongside other infrastructure alerts and enables correlation with internal incidents.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes Alerts Stream (webhook)
- **SPL:**
```spl
`stream_index` sourcetype="thousandeyes:alerts" severity="critical" OR severity="warning"
| stats count by alert.rule.name, alert.test.name, severity
| sort -count
```
- **Implementation:** Configure the Alerts Stream input in the ThousandEyes App, selecting alert rules to receive via webhook. The app automatically creates a webhook connector in ThousandEyes and associates it with the selected alert rules. Alerts flow in real-time to Splunk via HEC.
- **Visualization:** Pie chart (alerts by severity), Bar chart (alert timeline), Table (rule, test, severity, count).
- **CIM Models:** N/A

---

### UC-5.9.20 · DNS Issue Event Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** ThousandEyes Internet Insights automatically detects DNS infrastructure issues that deviate from established baselines, surfacing problems in third-party DNS services before they cause widespread outages.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes Event API
- **SPL:**
```spl
`event_index` type="DNS Issue"
| stats count by severity, state, thousandeyes.test.name
| sort -count
```
- **Implementation:** Events with type "DNS Issue" are fetched via the Event input at the configured interval. Filter by `severity` (high, medium, low) and `state` (active, resolved) to focus on current issues. Correlate with DNS availability metrics from UC-5.10.13.
- **Visualization:** Events timeline, Table (test, severity, state), Single value (active DNS issues).
- **CIM Models:** N/A

---

### UC-5.9.21 · Proxy Issue Detection
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Detects when proxy infrastructure (forward proxies, web gateways, SASE secure edges) becomes the root cause of connectivity issues, helping teams quickly identify whether the problem is in the proxy layer or the destination.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes Event API
- **SPL:**
```spl
`event_index` type="Proxy Issue"
| stats count by severity, state
| sort -count
```
- **Implementation:** Events with type "Proxy Issue" indicate problems in proxy/web gateway infrastructure. These are automatically detected when ThousandEyes agents traverse proxy paths. Correlate with SASE or web security gateway logs in Splunk for root cause analysis.
- **Visualization:** Events timeline, Table, Single value (active proxy issues).
- **CIM Models:** N/A

---

### UC-5.9.22 · Local Agent Issue Monitoring
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Detects when the source of a test failure is the agent itself (local network, DNS, or connectivity issue at the agent location), preventing false attribution of problems to the destination service.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes Event API
- **SPL:**
```spl
`event_index` type="Local Agent Issue"
| stats count by severity, state
| sort -count
```
- **Implementation:** "Local Agent Issue" events indicate that the test failure originated at the agent's local environment, not the remote target. These help filter out false positives in outage detection. Correlate with agent health data to identify sites with recurring local problems.
- **Visualization:** Events timeline, Table by agent, Single value (active local issues).
- **CIM Models:** N/A

---

### UC-5.9.23 · Internet Outage Correlation with Internal Alerts
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability
- **Value:** Correlating ThousandEyes outage events with internal monitoring alerts enables rapid determination of whether an issue is caused by an external internet problem or an internal infrastructure failure, significantly reducing MTTR.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes` (events), plus internal monitoring indexes
- **SPL:**
```spl
`event_index` type="Network Outage" state="active"
| rename thousandeyes.test.name as test_name
| join type=outer max=1 test_name [
  search index=itsi_tracked_alerts severity="critical"
  | rename service_name as test_name
]
| table _time, type, severity, test_name, service_name, state
| sort -_time
```
- **Implementation:** This correlation use case combines ThousandEyes outage events with internal alerting systems (ITSI episodes, Splunk alerts, or ServiceNow incidents). When a ThousandEyes "Network Outage" event is active and aligns with internal service degradation, the root cause is likely external. Adjust the join logic to match your naming conventions.
- **Visualization:** Combined timeline (TE events + internal alerts), Table, Dashboard with dual panels.
- **CIM Models:** N/A

---

### UC-5.9.24 · Endpoint Experience Score Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** ThousandEyes Endpoint Agents provide a composite experience score aggregating CPU, memory, and network performance from the end-user device perspective, enabling proactive digital experience management for hybrid workforces.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Endpoint tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.domain="endpoint"
| stats avg(thousandeyes.endpoint.agent.score) as avg_score avg(system.cpu.utilization) as avg_cpu avg(system.memory.utilization) as avg_mem by thousandeyes.source.agent.name
| where avg_score < 70
| sort avg_score
```
- **Implementation:** Deploy ThousandEyes Endpoint Agents on user devices and configure Endpoint Agent tests in the Tests Stream input. The OTel metric `thousandeyes.endpoint.agent.score` is a composite of CPU and memory scores. `system.cpu.utilization` and `system.memory.utilization` are reported as percentages.
- **Visualization:** Gauge (experience score per user), Table (agent, score, CPU, memory), Trend line chart.
- **CIM Models:** N/A

---

### UC-5.9.25 · Remote Worker Connectivity Health
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Endpoint agents break connectivity into segments (gateway, VPN, proxy, DNS) with per-segment latency, loss, and score, enabling targeted troubleshooting of remote worker network issues without requiring on-site visits.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Endpoint local network)
- **SPL:**
```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type=*
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.score) as avg_score by thousandeyes.source.agent.name, target.type
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort thousandeyes.source.agent.name, target.type
```
- **Implementation:** Endpoint Experience Local Network data reports metrics per segment: `target.type` can be "dns", "proxy", "gateway", or "vpn". The `network.score` composite metric simplifies multi-segment health assessment. Identify whether connectivity problems are in the local network, VPN, proxy, or DNS layer.
- **Visualization:** Table (agent, segment type, latency, loss, score), Heatmap by segment, Drilldown per agent.
- **CIM Models:** N/A

---

### UC-5.9.26 · VPN Path Performance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Measures latency, loss, and quality through VPN tunnels from endpoint agents, identifying whether the VPN concentrator or provider is the bottleneck for remote workers.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Endpoint local network)
- **SPL:**
```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="vpn"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.score) as avg_score by thousandeyes.source.agent.name, vpn.vendor, server.address
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| where avg_score < 70 OR avg_loss > 1
| sort avg_score
```
- **Implementation:** Endpoint agents with VPN connections report metrics with `target.type="vpn"`. The `vpn.vendor` attribute identifies the VPN client (e.g., "Cisco AnyConnect"). The `server.address` is the VPN gateway. Compare VPN segment scores with gateway and DNS segment scores to isolate whether the VPN is the bottleneck.
- **Visualization:** Table (agent, VPN vendor, gateway, latency, loss, score), Column chart by VPN vendor, Trend line chart.
- **CIM Models:** N/A

---

### UC-5.9.27 · Endpoint Connection Type and Network Score
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Comparing network scores across connection types (Wireless, Ethernet, Modem) identifies whether WiFi or wired connectivity is a systemic issue for the workforce, informing infrastructure investment decisions.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Endpoint local network)
- **SPL:**
```spl
`stream_index` thousandeyes.test.domain="endpoint"
| stats avg(network.score) as avg_score avg(network.latency) as avg_latency avg(network.loss) as avg_loss count by thousandeyes.source.agent.connection.type
| eval avg_latency_ms=round(avg_latency*1000,1)
| sort avg_score
```
- **Implementation:** The OTel attribute `thousandeyes.source.agent.connection.type` reports "Wireless", "Ethernet", or "Modem". Group endpoint network metrics by connection type to identify whether WiFi users have systematically worse performance than wired users.
- **Visualization:** Column chart (score by connection type), Table (connection type, avg score, latency, loss, count), Pie chart (user distribution by type).
- **CIM Models:** N/A

---

### UC-5.9.28 · Geographic Workforce Performance Comparison
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Comparing digital experience metrics across office locations and regions identifies sites with persistent network quality issues, enabling targeted infrastructure improvements.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Endpoint tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.domain="endpoint"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.score) as avg_score count as agent_count by thousandeyes.source.agent.geo.country.iso_code, thousandeyes.source.agent.geo.region.iso_code
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort avg_score
```
- **Implementation:** Endpoint agent metrics include geographic attributes: `thousandeyes.source.agent.geo.country.iso_code` and `thousandeyes.source.agent.geo.region.iso_code`. Aggregate network quality metrics by region to identify poorly performing locations. Combine with `thousandeyes.source.agent.location` for more specific site-level analysis.
- **Visualization:** Map (score by region), Table (region, score, latency, loss, agent count), Column chart comparing regions.
- **CIM Models:** N/A

---

### UC-5.9.29 · SD-WAN Overlay vs Underlay Performance
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** Compares performance metrics across SD-WAN overlay tunnels and their underlay transport paths, revealing when SD-WAN policy routing decisions are sub-optimal or when underlay degradation affects the overlay.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics, Path Visualization
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="agent-to-agent" OR thousandeyes.test.type="agent-to-server"
| search thousandeyes.test.name="*SD-WAN*" OR thousandeyes.test.name="*overlay*" OR thousandeyes.test.name="*underlay*"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.test.name, thousandeyes.source.agent.name
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort thousandeyes.source.agent.name, thousandeyes.test.name
```
- **Implementation:** Deploy ThousandEyes Enterprise Agents on Cisco Catalyst SD-WAN or Meraki MX devices via the SD-WAN Manager integration. Create paired tests — one through the overlay tunnel and one via the underlay path — and name them consistently (e.g., "Site-A Overlay", "Site-A Underlay") to enable comparison. The same `network.latency`, `network.loss`, and `network.jitter` metrics apply.
- **Visualization:** Dual-panel comparison (overlay vs underlay), Table (test, latency, loss, jitter), Line chart side-by-side.
- **CIM Models:** N/A

---

### UC-5.9.30 · SASE Secure Edge Performance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** SASE architectures route traffic through cloud-based security edges (Zscaler, Cisco Umbrella, etc.). Monitoring latency and loss through these edges ensures the security layer does not unacceptably degrade user experience.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| search thousandeyes.test.name="*SASE*" OR thousandeyes.test.name="*Zscaler*" OR thousandeyes.test.name="*Umbrella*"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss by thousandeyes.test.name, thousandeyes.source.agent.name
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort -avg_latency_ms
```
- **Implementation:** Create Agent-to-Server tests in ThousandEyes that route through your SASE secure edge. Name tests descriptively to include the SASE provider. Compare latency with and without the secure edge to quantify the security overhead. Correlate with Endpoint Agent `target.type="proxy"` data for end-to-end visibility.
- **Visualization:** Line chart (latency through secure edge over time), Table (agent, SASE test, latency, loss), Comparison chart.
- **CIM Models:** N/A

---

### UC-5.9.31 · Multi-Cloud Network Performance
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Measures network path performance to workloads hosted across AWS, Azure, GCP, and other cloud providers, identifying which provider or region delivers the best connectivity from each user location.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| search thousandeyes.test.name="*AWS*" OR thousandeyes.test.name="*Azure*" OR thousandeyes.test.name="*GCP*"
| stats avg(network.latency) as avg_latency_s avg(network.loss) as avg_loss by thousandeyes.test.name, thousandeyes.source.agent.name
| eval avg_latency_ms=round(avg_latency_s*1000,1)
| sort thousandeyes.source.agent.name, avg_latency_ms
```
- **Implementation:** Deploy ThousandEyes Cloud Agents in each cloud provider region and create Agent-to-Server tests targeting your workloads. ThousandEyes supports Cloud Agents in AWS, Azure, GCP, IBM Cloud, and Alibaba Cloud. Name tests with the provider and region for easy filtering.
- **Visualization:** Column chart (latency by cloud provider), Table (agent, cloud target, latency, loss), Map (agent-to-cloud paths).
- **CIM Models:** N/A

---

### UC-5.9.32 · CDN Edge Network Performance
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Measures latency, loss, and path characteristics to CDN edge locations, revealing when CDN performance varies by region or when edge servers are not serving content as expected.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="http-server"
| search thousandeyes.test.name="*CDN*"
| stats avg(http.client.request.duration) as avg_ttfb_s avg(http.server.throughput) as avg_throughput by thousandeyes.test.name, thousandeyes.source.agent.name, server.address
| eval avg_ttfb_ms=round(avg_ttfb_s*1000,1), throughput_mbps=round(avg_throughput/1048576,2)
| sort thousandeyes.source.agent.name
```
- **Implementation:** Create HTTP Server tests targeting CDN-served URLs from multiple ThousandEyes Cloud Agents. The `server.address` will show which CDN edge server responded. Compare performance across regions by grouping by `thousandeyes.source.agent.location`. Correlate HTTP response headers (cache hit/miss) with performance differences.
- **Visualization:** Column chart (TTFB by CDN edge), Table (agent, CDN edge, TTFB, throughput), Map.
- **CIM Models:** N/A

---

### UC-5.9.33 · Cloud Provider Path Visualization
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Hop-by-hop path visualization through cloud provider backbones reveals routing decisions, peering points, and potential bottlenecks within AWS, Azure, or GCP networks that are otherwise invisible.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes Path Visualization data
- **SPL:**
```spl
`path_viz_index` thousandeyes.test.type="agent-to-server"
| search thousandeyes.test.name="*AWS*" OR thousandeyes.test.name="*Azure*" OR thousandeyes.test.name="*GCP*"
| stats count values(hop_ip) as hops by thousandeyes.test.name, thousandeyes.source.agent.name
| sort thousandeyes.test.name
```
- **Implementation:** Enable "Include Network Path Data" in the Tests Stream input for cloud-targeted tests. Path Visualization data shows every hop between the agent and target. The `path_viz_index` macro must be configured. For detailed path analysis, use the `thousandeyes.permalink` to drill into the ThousandEyes UI path visualization view.
- **Visualization:** Table (test, agent, hop list), Drilldown to ThousandEyes path viz, Network topology diagram.
- **CIM Models:** N/A

---


### UC-5.9.34 · HTTP Server Availability Monitoring (ThousandEyes)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Monitors web server availability from multiple global vantage points using ThousandEyes Cloud and Enterprise Agents. Detects regional outages that internal monitoring misses because the problem is between the user and the server.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.server.request.availability) as avg_availability by thousandeyes.test.name, server.address, thousandeyes.source.agent.name
| where avg_availability < 100
| sort avg_availability
```
- **Implementation:** Create HTTP Server tests in ThousandEyes targeting critical web applications and stream metrics to Splunk via the Tests Stream input. The OTel metric `http.server.request.availability` reports 100% when the HTTP request succeeds and 0% when any error occurs. The Splunk App Application dashboard includes an "HTTP Server Availability (%)" panel with permalink drilldown.
- **Visualization:** Line chart (availability % over time), Single value (current availability), Table (test, server, agent, availability).
- **CIM Models:** N/A

---

### UC-5.9.35 · HTTP Server Response Time Tracking (ThousandEyes)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks Time to First Byte (TTFB) from ThousandEyes agents to web servers. Rising response times indicate backend degradation, infrastructure bottlenecks, or increased load — often visible from external vantage points before internal monitoring catches it.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="http-server"
| timechart span=5m avg(http.client.request.duration) as avg_ttfb_s by thousandeyes.test.name
| eval avg_ttfb_ms=round(avg_ttfb_s*1000,1)
```
- **Implementation:** The OTel metric `http.client.request.duration` reports TTFB in seconds. The Splunk App Application dashboard includes an "HTTP Server Request Duration (s)" line chart. Alert when TTFB exceeds your SLA threshold (e.g., 2 seconds). Correlate with `http.response.status_code` to distinguish slow responses from errors.
- **Visualization:** Line chart (TTFB over time by test), Single value (avg TTFB), Table with drilldown to ThousandEyes.
- **CIM Models:** N/A

---

### UC-5.9.36 · HTTP Server Throughput Analysis (ThousandEyes)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Measures download throughput from ThousandEyes agents to web servers, revealing bandwidth constraints or content delivery issues from the user perspective.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.server.throughput) as avg_throughput by thousandeyes.test.name, thousandeyes.source.agent.name
| eval throughput_mbps=round(avg_throughput/1048576,2)
| sort -throughput_mbps
```
- **Implementation:** The OTel metric `http.server.throughput` reports bytes per second. The Splunk App Application dashboard includes an "HTTP Server Throughput (MB/s)" line chart. Low throughput combined with high latency typically indicates a network bottleneck; low throughput with low latency suggests a server-side rate limit.
- **Visualization:** Line chart (throughput MB/s over time), Table (test, agent, throughput), Column chart by agent.
- **CIM Models:** N/A

---

### UC-5.9.37 · Page Load Completion Rate (ThousandEyes)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Measures whether web pages fully load from the user's perspective. Incomplete page loads indicate broken resources, blocked CDN content, or JavaScript errors that prevent users from completing tasks.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Page Load tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="page-load"
| stats avg(web.page_load.completion) as avg_completion by thousandeyes.test.name, server.address
| where avg_completion < 100
| sort avg_completion
```
- **Implementation:** Create Page Load tests in ThousandEyes targeting critical web applications. The OTel metric `web.page_load.completion` reports 100% when the page loads successfully and 0% on error. Page Load tests automatically include underlying Agent-to-Server network tests, providing correlated network and application data.
- **Visualization:** Single value (completion %), Line chart (completion over time), Table (test, server, completion).
- **CIM Models:** N/A

---

### UC-5.9.38 · Page Load Duration Trending (ThousandEyes)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks total page load time including all resources (HTML, CSS, JS, images). Trending reveals gradual degradation from growing page weight, slow third-party resources, or backend issues.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Page Load tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="page-load"
| timechart span=5m avg(web.page_load.duration) as avg_load_s by thousandeyes.test.name
```
- **Implementation:** The OTel metric `web.page_load.duration` reports total page load time in seconds. The Splunk App Application dashboard includes a "Page Load Duration (s)" line chart with permalink drilldown to ThousandEyes waterfall views. Alert when load duration exceeds your performance budget.
- **Visualization:** Line chart (load time over time), Single value (avg load time), Table with permalink drilldown.
- **CIM Models:** N/A

---

### UC-5.9.39 · API Endpoint Completion Rate (ThousandEyes)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Monitors multi-step API test completion, ensuring that entire API workflows (authentication, data retrieval, processing) succeed end-to-end from external vantage points.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (API tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="api"
| stats avg(api.completion) as avg_completion by thousandeyes.test.name
| where avg_completion < 100
| sort avg_completion
```
- **Implementation:** Create API tests in ThousandEyes with multi-step sequences testing your critical API workflows. The OTel metric `api.completion` reports overall completion percentage. Per-step metrics (`api.step.completion`, `api.step.duration`) are also available with the `thousandeyes.test.step` attribute. The Splunk App Application dashboard includes an "API Completion (%)" panel.
- **Visualization:** Single value (completion %), Line chart (completion over time), Table (test, completion).
- **CIM Models:** N/A

---

### UC-5.9.40 · API Response Time Monitoring (ThousandEyes)
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Performance
- **Value:** Tracks total API test execution duration including all steps, revealing when API performance degrades from the consumer's perspective.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (API tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="api"
| timechart span=5m avg(api.duration) as avg_api_duration_s by thousandeyes.test.name
```
- **Implementation:** The OTel metric `api.duration` reports total API test execution time in seconds. For per-step analysis, use `api.step.duration` filtered by `thousandeyes.test.step`. The Splunk App Application dashboard includes an "API Request Duration (s)" line chart with permalink drilldown.
- **Visualization:** Line chart (API duration over time), Table (test, duration), Column chart (duration by step).
- **CIM Models:** N/A

---

### UC-5.9.41 · Transaction Test Completion Rate (ThousandEyes)
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Transaction tests execute scripted multi-step user workflows (login, navigate, submit form, verify result). Completion rate below 100% means users cannot complete critical business processes.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Transaction tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="web-transactions"
| stats avg(web.transaction.completion) as avg_completion sum(web.transaction.errors.count) as total_errors by thousandeyes.test.name
| where avg_completion < 100 OR total_errors > 0
| sort avg_completion
```
- **Implementation:** Create Transaction tests in ThousandEyes using Selenium-based scripted workflows that simulate real user journeys. The OTel metric `web.transaction.completion` reports 100% on success and 0% on error. `web.transaction.errors.count` returns 1 when an error occurs and 0 otherwise. The Splunk App Application dashboard includes a "Transaction Completion (%)" panel.
- **Visualization:** Single value (completion %), Line chart (completion over time), Table (test, completion, errors).
- **CIM Models:** N/A

---

### UC-5.9.42 · Transaction Duration Analysis (ThousandEyes)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Measures end-to-end time for complex user workflows. Slow transactions directly impact user productivity and satisfaction. Trending reveals gradual degradation across the multi-step flow.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (Transaction tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="web-transactions"
| timechart span=5m avg(web.transaction.duration) as avg_transaction_s by thousandeyes.test.name
```
- **Implementation:** The OTel metric `web.transaction.duration` reports total transaction execution time in seconds (only reported when the transaction completes without errors). The Splunk App Application dashboard includes a "Transaction Duration (s)" line chart with permalink drilldown to ThousandEyes. ThousandEyes also supports OpenTelemetry traces for transaction tests, providing detailed span-level timing.
- **Visualization:** Line chart (transaction duration over time), Table (test, agent, duration), Drilldown to ThousandEyes trace view.
- **CIM Models:** N/A

---

### UC-5.9.43 · SaaS Application Response Time Comparison (ThousandEyes)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Value:** Compares availability and response time across business-critical SaaS applications (Microsoft 365, Salesforce, ServiceNow, etc.) from multiple office locations, enabling data-driven SaaS vendor performance management.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server / Page Load tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="http-server" OR thousandeyes.test.type="page-load"
| search thousandeyes.test.name="*M365*" OR thousandeyes.test.name="*Salesforce*" OR thousandeyes.test.name="*ServiceNow*"
| stats avg(http.server.request.availability) as avg_avail avg(http.client.request.duration) as avg_ttfb_s by thousandeyes.test.name, thousandeyes.source.agent.location
| eval avg_ttfb_ms=round(avg_ttfb_s*1000,1)
| sort thousandeyes.test.name, avg_ttfb_ms
```
- **Implementation:** Create HTTP Server or Page Load tests in ThousandEyes for each SaaS application, running from Enterprise Agents at each office and Cloud Agents in relevant regions. Name tests consistently (e.g., "M365 - Exchange Online", "Salesforce - Login Page"). ThousandEyes provides best-practice monitoring guides for Microsoft 365, Salesforce, and other major SaaS platforms.
- **Visualization:** Column chart (TTFB by SaaS app per location), Table (app, location, availability, TTFB), Comparison dashboard.
- **CIM Models:** N/A

---

### UC-5.9.44 · Multi-Region SaaS Availability (ThousandEyes)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Monitors SaaS application reachability from multiple geographic regions using ThousandEyes Cloud Agents, identifying regional availability issues that affect specific user populations.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (HTTP Server tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.server.request.availability) as avg_availability by thousandeyes.test.name, thousandeyes.source.agent.geo.country.iso_code, thousandeyes.source.agent.location
| where avg_availability < 100
| sort avg_availability
```
- **Implementation:** Deploy the same HTTP Server tests across ThousandEyes Cloud Agents in Americas, EMEA, and APAC regions. Use `thousandeyes.source.agent.geo.country.iso_code` and `thousandeyes.source.agent.location` attributes to group results by region. A service that is available from US agents but not from EU agents indicates a regional issue.
- **Visualization:** Map (availability by agent location), Table (region, app, availability), Column chart (availability by region).
- **CIM Models:** N/A

---

### UC-5.9.45 · FTP Server Availability and Throughput (ThousandEyes)
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability, Performance
- **Value:** Monitors FTP/SFTP server availability and file transfer throughput from ThousandEyes agents, ensuring file transfer services are accessible and performing adequately for automated data exchange workflows.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Metrics (FTP Server tests)
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="ftp-server"
| stats avg(ftp.server.request.availability) as avg_availability avg(ftp.client.request.duration) as avg_response_s avg(ftp.server.throughput) as avg_throughput by thousandeyes.test.name, server.address
| eval avg_response_ms=round(avg_response_s*1000,1), throughput_mbps=round(avg_throughput/1048576,2)
| sort avg_availability, -throughput_mbps
```
- **Implementation:** Create FTP Server tests in ThousandEyes for critical file transfer endpoints. The OTel metric `ftp.server.request.availability` reports availability, `ftp.client.request.duration` reports TTFB, and `ftp.server.throughput` reports bytes per second. The `ftp.request.command` attribute indicates the FTP command tested (GET, PUT, LS). The Splunk App Voice dashboard includes FTP panels.
- **Visualization:** Line chart (availability and throughput over time), Table (server, availability, throughput, response time), Single value.
- **CIM Models:** N/A

---

### UC-5.9.46 · ThousandEyes Alert Severity Distribution
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Provides a centralized view of all ThousandEyes alerts in Splunk by severity, enabling SOC and NOC teams to prioritize response across network, application, and voice test alerts alongside other infrastructure alerts.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes Alerts Stream (webhook via HEC)
- **SPL:**
```spl
`stream_index` sourcetype="thousandeyes:alerts"
| stats count by severity, alert.rule.name, alert.test.name, alert.type
| sort severity, -count
```
- **Implementation:** Configure the Alerts Stream input in the Cisco ThousandEyes App for Splunk. Select the ThousandEyes user, account group, and alert rules to receive. The app automatically creates a webhook connector in ThousandEyes and associates it with selected alert rules. Alerts flow in real-time to Splunk via HEC. The Splunk App Alerts dashboard provides pre-built panels for alert severity distribution, timeline, and drilldown.
- **Visualization:** Pie chart (alerts by severity), Bar chart (alerts by type), Table (rule, test, severity, count), Single value (active critical alerts).
- **CIM Models:** N/A

---

### UC-5.9.47 · ThousandEyes Alert Timeline Trending
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Anomaly
- **Value:** Trending alert volume over time reveals patterns — recurring issues at specific times, increasing alert frequency indicating degradation, or correlation with change windows. Helps teams move from reactive to proactive operations.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes Alerts Stream (webhook via HEC)
- **SPL:**
```spl
`stream_index` sourcetype="thousandeyes:alerts"
| timechart span=1h count by severity
```
- **Implementation:** The Splunk App Alerts dashboard includes a "Alerts Timeline" line chart and a "Severity Distribution Trend" chart. Use these pre-built panels or customize with the `stream_index` macro. Set adaptive alerts on alert volume increases — a sudden spike in ThousandEyes alerts often precedes user-reported incidents. Correlate alert timing with change management windows.
- **Visualization:** Line chart (alerts over time by severity), Stacked bar chart (alerts per hour), Table (trending alert rules).
- **CIM Models:** N/A

---

### UC-5.9.48 · ThousandEyes Activity Log Audit Trail
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Security
- **Value:** Ingests ThousandEyes platform activity logs into Splunk for audit, compliance, and change tracking. Tracks who created, modified, or deleted tests, users, and alert rules — essential for troubleshooting test behavior changes and meeting compliance requirements.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes Activity Log API
- **SPL:**
```spl
`activity_index`
| stats count by event, accountGroupName, aid
| sort -count
```
- **Implementation:** Configure the Activity Log input in the Cisco ThousandEyes App with a ThousandEyes user and account group. Activity logs are fetched at a configurable interval via the ThousandEyes API. Update the `activity_index` macro to point to the correct index. Events include test creation/modification/deletion, user management, alert rule changes, and account group configuration changes.
- **Visualization:** Table (event type, account group, count), Timeline (activity events), Pie chart (activity by event type).
- **CIM Models:** N/A

---

### UC-5.9.49 · ThousandEyes Data Collection Health Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Value:** Monitors the health of the ThousandEyes-to-Splunk data pipeline itself. Detects gaps in data collection, API errors, or HEC delivery failures that would cause blind spots in network and application monitoring.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, Splunk internal logs
- **SPL:**
```spl
`stream_index`
| timechart span=5m count as event_count
| where event_count < 1
```
- **Implementation:** Monitor the data flow from ThousandEyes to Splunk by tracking event volume per collection interval. A drop to zero events indicates a pipeline failure — possible causes include expired ThousandEyes API tokens, HEC token issues, or ThousandEyes streaming configuration changes. Combine with `index=_internal sourcetype=splunkd component=HttpInputDataHandler` to monitor HEC health. The Splunk App Health dashboard provides data freshness panels.
- **Visualization:** Line chart (event volume over time), Single value (events in last 5 min), Alert on zero events for >15 min.
- **CIM Models:** N/A

---

### UC-5.9.50 · ThousandEyes ITSI Service Health (Content Pack)
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Value:** The ITSI Content Pack for Cisco ThousandEyes provides pre-built service templates, KPI base searches, entity types, and Glass Tables for service-centric monitoring. It maps ThousandEyes test results to ITSI services for unified health scoring across all monitoring domains.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719), ITSI Content Pack for Cisco ThousandEyes
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel data via ITSI KPI base searches
- **SPL:**
```spl
| from datamodel:"ITSI_KPI_Summary"
| where service_name="*ThousandEyes*"
| stats latest(kpi_urgency) as urgency latest(alert_level) as alert_level by service_name, kpiid, itsi_kpi_id
| sort -urgency
```
- **Implementation:** Install the ITSI Content Pack for Cisco ThousandEyes from the ITSI Content Library. The content pack provides: entity types (ThousandEyes Test, ThousandEyes Agent), KPI base searches (latency, loss, jitter, availability, MOS for each test type), service templates, and Glass Table templates. After installation, import the service templates and configure entity discovery to match your ThousandEyes tests. KPIs are automatically populated from the ThousandEyes data model.
- **Visualization:** ITSI Service Tree, Glass Table, KPI cards (latency, loss, availability, MOS), Service health score.
- **CIM Models:** N/A

---

### UC-5.9.51 · Splunk On-Call Incident Routing from ThousandEyes
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Value:** Routes ThousandEyes alerts directly to Splunk On-Call (formerly VictorOps) for incident management, on-call paging, and war room coordination. Ensures network and application issues detected by ThousandEyes reach the right team within seconds.
- **App/TA:** ThousandEyes webhook integration with Splunk On-Call
- **Data Sources:** ThousandEyes alert webhooks
- **SPL:**
```spl
index=oncall sourcetype="oncall:incidents" monitoring_tool="ThousandEyes"
| stats count by incident_state, routing_key, entity_id
| sort -count
```
- **Implementation:** Configure ThousandEyes to send alert notifications to Splunk On-Call via the REST API endpoint webhook integration. In ThousandEyes, create a webhook notification pointing to the Splunk On-Call REST endpoint URL with your routing key. Map ThousandEyes alert severity to Splunk On-Call incident severity (critical→critical, warning→warning, info→info). The integration supports recovery messages to automatically resolve incidents when ThousandEyes alerts clear.
- **Visualization:** Table (incidents by state and routing key), Timeline (incident creation/resolution), Single value (active incidents from ThousandEyes).
- **CIM Models:** N/A

---

### UC-5.9.52 · ThousandEyes Trace Span Analysis and Drill-Down
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Performance
- **Value:** ThousandEyes Transaction tests can emit OpenTelemetry traces with span-level timing for each step of the scripted workflow. Ingesting these traces into Splunk enables correlation with application traces from Splunk APM for end-to-end distributed tracing.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes`, ThousandEyes OTel Tests Stream — Traces
- **SPL:**
```spl
`stream_index` sourcetype="thousandeyes:traces"
| stats count avg(duration_ms) as avg_span_duration_ms by service.name, span.name, span.kind
| sort -avg_span_duration_ms
```
- **Implementation:** Enable the Tests Stream — Traces input in the Cisco ThousandEyes App. Traces are emitted for Transaction tests and provide span-level timing for each step of the scripted workflow. The trace data follows OpenTelemetry conventions with `trace_id`, `span_id`, `parent_span_id`, `service.name`, `span.name`, `duration`, and custom attributes. Traces can be correlated with Splunk APM traces using shared context propagation.
- **Visualization:** Table (spans by duration), Trace waterfall (via Splunk APM or custom visualization), Bar chart (avg span duration by step).
- **CIM Models:** N/A

---

### UC-5.9.53 · Cross-Platform Correlation (ThousandEyes Network + Splunk APM)
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Anomaly
- **Value:** Correlates ThousandEyes network path quality data with Splunk APM application traces to determine whether performance issues are caused by the network or the application. This is the core value proposition of the Splunk + ThousandEyes integration — unified observability across network and application layers.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719), Splunk APM
- **Data Sources:** `index=thousandeyes` (network metrics), Splunk APM traces
- **SPL:**
```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| stats avg(network.latency) as avg_net_latency_s avg(network.loss) as avg_net_loss by server.address, _time span=5m
| join type=outer max=1 server.address [
  search index=apm_traces
  | stats avg(duration_ms) as avg_app_latency_ms p99(duration_ms) as p99_app_latency_ms by service.name, server.address, _time span=5m
]
| eval avg_net_latency_ms=round(avg_net_latency_s*1000,1)
| eval root_cause=case(avg_net_latency_ms>200 AND avg_app_latency_ms<500, "Network", avg_net_latency_ms<50 AND avg_app_latency_ms>2000, "Application", avg_net_latency_ms>200 AND avg_app_latency_ms>2000, "Both", 1=1, "Normal")
| where root_cause!="Normal"
| table _time, server.address, service.name, avg_net_latency_ms, avg_net_loss, avg_app_latency_ms, root_cause
```
- **Implementation:** This correlation requires both ThousandEyes network data and Splunk APM trace data indexed in Splunk. The key join field is the server address or service endpoint. When network latency is high but application processing is fast, the network is the bottleneck. When network latency is low but application response is slow, the issue is in the application. This "network vs. app" isolation significantly reduces MTTR by directing the right team to investigate.
- **Visualization:** Table (endpoint, network latency, app latency, root cause), Dual-axis chart (network vs app latency), Dashboard with network and app panels side-by-side.
- **CIM Models:** N/A

---

### UC-5.9.54 · MTTR Reduction via Network vs Application Isolation
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Anomaly
- **Value:** Quantifies the business value of ThousandEyes + Splunk integration by measuring how quickly teams can isolate whether a performance issue is network-caused or application-caused. Tracks Mean Time to Resolution and Mean Time to Isolate metrics for incidents where ThousandEyes data was available.
- **App/TA:** `Cisco ThousandEyes App for Splunk` (Splunkbase 7719)
- **Data Sources:** `index=thousandeyes` (alerts, events), incident management system data
- **SPL:**
```spl
`stream_index` sourcetype="thousandeyes:alerts"
| stats earliest(_time) as alert_start latest(_time) as alert_end by alert.rule.name, alert.test.name
| eval mtti_minutes=round((alert_end-alert_start)/60,1)
| join type=outer max=1 alert.test.name [
  search `event_index`
  | stats earliest(_time) as event_start latest(state) as final_state by thousandeyes.test.name
  | rename thousandeyes.test.name as alert.test.name
]
| eval isolation_method=if(isnotnull(event_start), "ThousandEyes Event + Alert", "ThousandEyes Alert Only")
| stats avg(mtti_minutes) as avg_mtti count by isolation_method
```
- **Implementation:** This meta-analysis use case measures how ThousandEyes data accelerates incident resolution. Track the time from ThousandEyes alert trigger to resolution (MTTR). Compare MTTR for incidents where ThousandEyes data was available vs. those without. Over time, this demonstrates the ROI of the ThousandEyes + Splunk integration. Combine with ITSM data (ServiceNow, Jira Service Management) for complete MTTR tracking.
- **Visualization:** Single value (avg MTTR with ThousandEyes), Comparison chart (MTTR with vs. without TE data), Table (incidents and isolation times), Trend line (MTTR improvement over time).
- **CIM Models:** N/A

---

## 5.10 Carrier and Service Provider Signaling

### UC-5.10.1 · Diameter Signaling Health Monitoring
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Industry:** Telecommunications
- **Value:** Tracks the success and failure rates of Diameter signaling messages (authentication, authorization, accounting) in the mobile core, essential for maintaining service availability and subscriber experience.
- **App/TA:** `Splunk App for Stream` (Splunkbase #1809)
- **Industry:** Telecommunications
- **Telco Use Case:** IMS Core and VoLTE Monitoring (50 Ways #16)
- **Data Sources:** `sourcetype=stream:diameter`
- **SPL:**
```spl
sourcetype="stream:diameter"
| stats count by command_code, result_code, origin_host, application_id
| eval status=if(result_code==2001, "Success", "Failure")
| stats sum(eval(if(status=="Success", 1, 0))) as successful, sum(eval(if(status=="Failure", 1, 0))) as failed by command_code, application_id
| eval success_rate=round(successful*100/(successful+failed), 2)
| where failed>0 OR success_rate<99
```
- **Implementation:** Install Splunk App for Stream and configure it to capture Diameter protocol traffic on the core network. Enable the Diameter protocol for full field extraction. Monitor `command_code` and `result_code` to detect signaling issues. Create alerts for sustained drops in success rate or spikes in failure codes such as DIAMETER_AUTHENTICATION_REJECTED (5003) or DIAMETER_UNABLE_TO_DELIVER (3002).
- **Visualization:** Single value (overall Diameter success rate with color-coded threshold: green >99%, yellow 95-99%, red <95%), Pie chart (failure breakdown by command_code), Table (origin_host, command_code, result_code, count — sortable), Line chart (success rate trend over 24h with 15-min buckets).
- **CIM Models:** N/A

---

### UC-5.10.2 · Diameter Subscriber Data Accounting
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Capacity
- **Industry:** Telecommunications
- **Value:** Aggregates Diameter accounting records to track data usage per subscriber and session, enabling detection of high-usage anomalies, billing reconciliation, and capacity planning.
- **App/TA:** `Splunk App for Stream` (Splunkbase #1809)
- **Industry:** Telecommunications
- **Telco Use Case:** Broadband Service Optimization (50 Ways #17)
- **Data Sources:** `sourcetype=stream:diameter`
- **SPL:**
```spl
sourcetype="stream:diameter" command_code=271
| eval total_bytes=acct_input_octets+acct_output_octets
| eval total_MB=round(total_bytes/1048576, 2)
| stats sum(total_MB) as total_data_MB, count as session_count by calling_station_id, origin_host
| sort -total_data_MB
| head 100
```
- **Implementation:** Configure Splunk App for Stream to capture Diameter Accounting-Request (ACR, command_code 271) and Accounting-Answer (ACA, command_code 271) messages. The fields `acct_input_octets` and `acct_output_octets` provide byte counts per session. Correlate with `calling_station_id` (subscriber MSISDN/IMSI) to build per-subscriber usage profiles. Set alerts for subscribers exceeding data thresholds.
- **Visualization:** Bar chart (top 20 subscribers by data usage in MB), Table (calling_station_id, origin_host, total_data_MB, session_count — sortable), Line chart (aggregate data volume trend over 7 days), Single value (total Diameter accounting sessions).
- **CIM Models:** N/A

---

### UC-5.10.3 · Mobile Subscriber RADIUS Session Tracking
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Availability
- **Industry:** Telecommunications
- **Value:** Tracks active mobile subscriber sessions via RADIUS accounting, providing visibility into session duration, data volume, and SGSN/MCC-MNC distribution — critical for mobile core capacity planning and roaming analytics.
- **App/TA:** `Splunk App for Stream` (Splunkbase #1809)
- **Industry:** Telecommunications
- **Telco Use Case:** Radio Access Network Monitoring (50 Ways #15)
- **Data Sources:** `sourcetype=stream:radius`
- **SPL:**
```spl
sourcetype="stream:radius" code="Accounting-Request"
| eval session_secs=stop_time-start_time
| eval session_min=round(session_secs/60, 1)
| stats count as sessions, avg(session_min) as avg_duration_min, dc(login) as unique_subscribers by sgsn_address, sgsn_mcc_mnc
| sort -sessions
```
- **Implementation:** Configure Splunk App for Stream to capture RADIUS accounting traffic from the mobile packet core (GGSN/PGW). Enable RADIUS protocol extraction including the telco-specific fields `sgsn_address` and `sgsn_mcc_mnc`. Use `code="Accounting-Request"` to filter for accounting records. Correlate `start_time` and `stop_time` for session duration. The `sgsn_mcc_mnc` field identifies the serving network (home vs. roaming). Alert on sudden drops in active sessions per SGSN.
- **Visualization:** Column chart (active sessions by SGSN address), Table (sgsn_address, sgsn_mcc_mnc, sessions, unique_subscribers, avg_duration_min — sortable), Timechart (session count over 24h), Pie chart (session distribution by MCC-MNC for roaming analysis).
- **CIM Models:** N/A

---

### UC-5.10.4 · Carrier SIP Trunk Failure Analysis
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability, Performance
- **Industry:** Telecommunications
- **Value:** Monitors SIP response codes on carrier trunks to detect call routing failures, trunk congestion, and destination unreachable conditions — directly impacting voice service availability and revenue.
- **App/TA:** `Splunk App for Stream` (Splunkbase #1809)
- **Industry:** Telecommunications
- **Telco Use Case:** Carrier Media Gateway PM (50 Ways #43), Enterprise Service Assurance (50 Ways #14)
- **Data Sources:** `sourcetype=stream:sip`
- **SPL:**
```spl
sourcetype="stream:sip" method="INVITE"
| stats count as total, sum(eval(if(reply_code>=400, 1, 0))) as failures by dest
| eval failure_rate=round(failures*100/total, 2)
| where failure_rate>5 OR failures>50
| sort -failure_rate
```
- **Implementation:** Configure Splunk App for Stream to capture SIP signaling on trunk-facing interfaces. Enable SIP protocol extraction for fields `method`, `reply_code`, `caller`, `callee`, and `dest`. Focus on INVITE transactions as these represent call attempts. Group by `dest` to identify problematic trunks or destinations. SIP 4xx codes indicate client errors (e.g., 404 Not Found, 486 Busy Here), 5xx codes indicate server errors, and 6xx codes indicate global failures. Alert when failure rate exceeds 5% sustained over 15 minutes.
- **Visualization:** Single value (overall SIP trunk success rate with thresholds: green >95%, yellow 90-95%, red <90%), Column chart (failure count by dest), Table (dest, total attempts, failures, failure_rate — sortable), Timechart (SIP 4xx/5xx/6xx responses over 24h by response code class).
- **CIM Models:** N/A

---

### UC-5.10.5 · SIP Registration Storm Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Security
- **Industry:** Telecommunications
- **Value:** Detects sudden spikes in SIP REGISTER messages that can overwhelm IMS/SBC infrastructure — caused by mass device reboots, network flaps, or DDoS attacks. Early detection prevents cascading core failures.
- **App/TA:** `Splunk App for Stream` (Splunkbase #1809)
- **Industry:** Telecommunications
- **Telco Use Case:** IMS Core and VoLTE Monitoring (50 Ways #16)
- **Data Sources:** `sourcetype=stream:sip`
- **SPL:**
```spl
sourcetype="stream:sip" method="REGISTER"
| bin _time span=5m
| stats count as register_count, dc(src) as unique_sources by _time
| eventstats avg(register_count) as baseline, stdev(register_count) as stdev_reg
| eval threshold=baseline+(3*stdev_reg)
| where register_count>threshold
| eval spike_factor=round(register_count/baseline, 1)
```
- **Implementation:** Configure Splunk App for Stream to capture SIP REGISTER traffic on the IMS/SBC interfaces. Use a 5-minute time bucket for aggregation. Calculate a rolling baseline using `eventstats` and flag any bucket where REGISTER volume exceeds 3 standard deviations above the mean. The `dc(src)` field helps distinguish between a mass re-registration event (many unique sources) vs. a single device stuck in a registration loop (few unique sources, high count). Alert the NOC immediately as registration storms can cascade into full core outages within minutes.
- **Visualization:** Line chart (REGISTER count over time with dynamic baseline threshold line), Single value (current spike factor vs. baseline), Table (time bucket, register_count, unique_sources, baseline, threshold — highlighting rows above threshold), Area chart (unique sources over time to correlate with storms).
- **CIM Models:** N/A

---

### UC-5.10.6 · SIP Post-Dial Delay Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Industry:** Telecommunications
- **Value:** Measures the time between a SIP INVITE and the first ringing or answer response, directly reflecting the user experience of waiting after dialing. High post-dial delay indicates trunk congestion, routing loops, or downstream SBC issues.
- **App/TA:** `Splunk App for Stream` (Splunkbase #1809)
- **Industry:** Telecommunications
- **Telco Use Case:** Reducing SLA Violations (50 Ways #21)
- **Data Sources:** `sourcetype=stream:sip`
- **SPL:**
```spl
sourcetype="stream:sip" method="INVITE" reply_code=200
| where isnotnull(setup_delay)
| stats avg(setup_delay) as avg_pdd, perc95(setup_delay) as p95_pdd, max(setup_delay) as max_pdd, count as calls by dest
| eval avg_pdd_ms=round(avg_pdd*1000, 0), p95_pdd_ms=round(p95_pdd*1000, 0)
| where p95_pdd_ms>3000
| sort -p95_pdd_ms
```
- **Implementation:** Configure Splunk App for Stream to capture SIP INVITE and response transactions. The `setup_delay` field measures the time from INVITE to the first non-100 response (typically 180 Ringing or 200 OK). Monitor by `dest` to identify slow destinations or trunks. ITU-T E.721 recommends post-dial delay under 3 seconds for national calls and under 5 seconds for international calls. Create tiered alerts: warning at p95 >3s, critical at p95 >5s. Trend analysis reveals degradation patterns across time of day and destination.
- **Visualization:** Gauge (p95 post-dial delay with thresholds: green <2s, yellow 2-3s, red >3s), Line chart (average PDD trend by dest over 24h), Table (dest, calls, avg_pdd_ms, p95_pdd_ms, max_pdd_ms — sortable), Histogram (PDD distribution across all calls).
- **CIM Models:** N/A

---

### 5.12 Telecommunications & CDR Analytics

**Primary App/TA:** SBC/softswitch CDR feeds, IMS core TAs, `Cisco CDR` / `asterisk:cdr`, Splunk App for Stream (`stream:sip`).

---

### UC-5.12.1 · CDR Call Failure Statistics
- **Criticality:** 🟠 High
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Availability
- **Industry:** Telecommunications
- **Value:** Aggregates release causes, SIP response codes, and ISUP cause values from CDRs to spot trunk, routing, or peer outages early.
- **App/TA:** SBC CDR CSV/JSON ingestion, custom props
- **Data Sources:** `sourcetype="cdr:voip"`, `sourcetype="broadworks:cdr"`
- **SPL:**
```spl
index=voip sourcetype="cdr:voip"
| eval is_fail=if(call_status!="answered" OR match(lower(call_status),"fail"),1,0)
| timechart span=15m sum(is_fail) as fails count as total
| eval fail_pct=if(total>0, round(100*fails/total,2), 0)
```
- **Implementation:** Normalize vendor-specific cause codes to Q.850 / SIP mapping table; baseline by destination prefix (emergency, international).
- **Visualization:** Stacked area (causes over time), Pie chart (cause mix), Single value (fail %).
- **CIM Models:** N/A

---

### UC-5.12.2 · Call Volume Trending by Destination
- **Criticality:** 🟡 Medium
- **Difficulty:** 🟢 Beginner
- **Monitoring type:** Capacity
- **Industry:** Telecommunications
- **Value:** Traffic engineering for trunk groups and geographic hot spots — detects flash crowds or fraud-driven spikes to premium destinations.
- **App/TA:** CDR aggregation
- **Data Sources:** `sourcetype="cdr:voip"` with `called_number`, `route_label`
- **SPL:**
```spl
index=voip sourcetype="cdr:voip"
| eval dest_prefix=substr(called_number,1,6)
| timechart span=1h sum(duration_sec) as minutes count as calls by dest_prefix
| sort -calls
```
- **Implementation:** Mask PANI for privacy dashboards; use HMAC of full number for drilldown in secured role.
- **Visualization:** Line chart (calls by prefix), Map (if geo-lookup on prefix), Table (top routes).
- **CIM Models:** N/A

---

### UC-5.12.3 · Call Duration Distribution Analysis
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance, Fraud
- **Industry:** Telecommunications
- **Value:** Shifts toward very short or very long holds may indicate robocall, modem, or toll fraud vs. normal conversational distribution.
- **App/TA:** CDR
- **Data Sources:** `sourcetype="cdr:voip"` `duration_sec`
- **SPL:**
```spl
index=voip sourcetype="cdr:voip" call_status="answered"
| bucket duration_sec span=30 as dur_bin
| stats count by dur_bin
| eventstats sum(count) as tot
| eval pct=round(100*count/tot,2)
| sort dur_bin
```
- **Implementation:** Compare to historical histogram; alert on >2× share in `<6s` buckets (wangiri / scanners).
- **Visualization:** Histogram (duration), Line chart (percentile trend via `eventstats perc*`).
- **CIM Models:** N/A

---

### UC-5.12.4 · SIP Trunk Utilization
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Capacity
- **Industry:** Telecommunications
- **Value:** Concurrent session counts or peg counts vs. licensed trunk capacity — prevents preemptive blocking at peak.
- **App/TA:** SBC SNMP, CDR-derived concurrency, Stream SIP
- **Data Sources:** `sourcetype="snmp:sbc"`, `sourcetype="stream:sip"`
- **SPL:**
```spl
index=voip sourcetype="stream:sip" OR sourcetype="snmp:sbc"
| eval concurrent=if(isnotnull(active_calls), active_calls, curr_sess)
| timechart span=1m max(concurrent) as peak_sess by trunk_group
| lookup trunk_capacity trunk_group OUTPUT licensed_sess
| eval util_pct=round(100*peak_sess/licensed_sess,1)
| where util_pct>85
```
- **Implementation:** Separate inbound vs. outbound if asymmetric licensing; forecast with `predict` for capacity planning.
- **Visualization:** Area chart (concurrency), Gauge (utilization %), Table (trunk groups at risk).
- **CIM Models:** N/A

---

### UC-5.12.5 · VoIP MOS Score Monitoring
- **Criticality:** 🟠 High
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Performance
- **Industry:** Telecommunications
- **Value:** Mean Opinion Score (or derived R-factor) from RTCP XR or vendor QoE reports — user-perceived VoLTE/VoIP quality.
- **App/TA:** SBC QoE records, Poly/Vendor QoS feeds
- **Data Sources:** `sourcetype="qos:rtcp"`, `sourcetype="cdr:voip"` with `mos` field
- **SPL:**
```spl
index=voip (sourcetype="qos:rtcp" OR sourcetype="cdr:voip")
| where isnotnull(mos)
| timechart span=5m avg(mos) as avg_mos perc5(mos) as worst_mos by codec
| where avg_mos < 3.8 OR worst_mos < 3.0
```
- **Implementation:** ITU-T G.107 E-model targets; correlate with jitter/loss from same leg_id; segment by radio access (VoLTE) vs. Wi-Fi.
- **Visualization:** Line chart (MOS trend), Scatter (loss vs. MOS), Table (worst calls).
- **CIM Models:** N/A

---

### UC-5.12.6 · Signaling Storm Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Availability, Security
- **Industry:** Telecommunications
- **Value:** Bursts of SIP OPTIONS, REGISTER, or diameter requests can indicate reflection DDoS or misconfigured endpoints — complements UC-5.10.5 with cross-layer view.
- **App/TA:** Splunk App for Stream, STP/Diameter capture
- **Data Sources:** `sourcetype="stream:sip"`, `sourcetype="diameter:cap"`
- **SPL:**
```spl
index=signaling (sourcetype="stream:sip" OR sourcetype="diameter:cap")
| bin _time span=1m
| stats count by method, cmd_code, _time
| eventstats avg(count) as mu, stdev(count) as s by method
| where count > mu+5*s
| sort -count
```
- **Implementation:** Whitelist health-check sources; coordinate with peer ops when storm targets upstream interconnect.
- **Visualization:** Timeline (spike detection), Table (method × source ASN), Single value (peak RPS).
- **CIM Models:** N/A

---

### UC-5.12.7 · IMS Registration Failure Rate
- **Criticality:** 🔴 Critical
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Availability
- **Industry:** Telecommunications
- **Value:** HSS/UDM or P-CSCF failures show up as elevated 401/403/timeout on REGISTER — impacts VoLTE attach and VoWiFi.
- **App/TA:** P-CSCF logs, IMS CDR
- **Data Sources:** `sourcetype="ims:sip"` `method=REGISTER`, `sourcetype="stream:sip"`
- **SPL:**
```spl
index=ims sourcetype="ims:sip" method="REGISTER"
| eval fail=if(match(reply_code,"^(401|403|408|5..)$"),1,0)
| timechart span=5m sum(fail) as fails, count as attempts
| eval fail_rate=round(100*fails/attempts,2)
| where fail_rate > 5
```
- **Implementation:** Break out by `visited_network` for roaming; correlate with certificate expiry on IPSec for VoWiFi.
- **Visualization:** Line chart (fail rate), Bar chart (SIP reason by S-CSCF), Table (IMSI hash top failures).
- **CIM Models:** N/A

---

### UC-5.12.8 · Number Portability Request Tracking
- **Criticality:** 🟡 Medium
- **Difficulty:** 🔵 Intermediate
- **Monitoring type:** Operations
- **Industry:** Telecommunications
- **Value:** LNP order status, NPAC responses, and port-out churn — operations and regulatory reporting for porting SLAs.
- **App/TA:** NP/BSS extracts, SOA APIs
- **Data Sources:** `sourcetype="lnp:order"`, `sourcetype="npac:soa"`
- **SPL:**
```spl
index=telco sourcetype="lnp:order"
| where order_status IN ("PENDING","REJECTED","TIMEOUT")
| stats count, avg((now()-submitted_epoch)/86400) as age_days by tn_range, losing_carrier
| sort -age_days
```
- **Implementation:** SLA alerts for orders >72h in PENDING; root-cause codes joined to carrier contact list.
- **Visualization:** Funnel (order states), Table (aging ports), Bar chart (reject reasons).
- **CIM Models:** N/A

---

### UC-5.12.9 · Roaming Usage Anomaly
- **Criticality:** 🟠 High
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fraud, Revenue Assurance
- **Industry:** Telecommunications
- **Value:** Sudden data/voice roaming volume from HLR/VLR or TAP records may indicate SIM box, cloned IMSI, or billing leakage.
- **App/TA:** TAP files (TD.35), roaming analytics
- **Data Sources:** `sourcetype="tap:cdr"`, `sourcetype="roaming:usage"`
- **SPL:**
```spl
index=telco sourcetype="roaming:usage"
| bin _time span=1d
| stats sum(charge_units) as units, sum(charge_amount) as rev by imsi_hash, visited_country, _time
| eventstats avg(units) as baseline by visited_country
| where units > 10*baseline
| sort -units
```
- **Implementation:** Privacy: only hashed IMSI in Splunk; correlate with HLR IMEI change for SIM swap fraud.
- **Visualization:** Map (visited countries), Table (suspicious subscribers), Line chart (roaming $ trend).
- **CIM Models:** N/A

---

### UC-5.12.10 · Toll Fraud Detection
- **Criticality:** 🔴 Critical
- **Difficulty:** 🟠 Advanced
- **Monitoring type:** Fraud, Security
- **Industry:** Telecommunications
- **Value:** Premium-rate, international, or short-duration high-cost patterns from compromised PBX or SIP credentials — classic CDR analytics use case.
- **App/TA:** SBC CDR, fraud scoring apps
- **Data Sources:** `sourcetype="cdr:voip"` with `rate_class`, `destination`
- **SPL:**
```spl
index=voip sourcetype="cdr:voip"
| lookup premium_and_high_risk_prefixes called_number OUTPUT risk_tier
| where risk_tier IN ("premium","satellite","high_cost_geo")
| stats sum(toll_charge) as cost, count, dc(calling_party) as sources by src, hour
| where cost>500 OR count>100
| sort -cost
```
- **Implementation:** Hotline to NOC + auto-block high-risk destinations on SBC after threshold; require PIN for international on suspect trunks.
- **Visualization:** Table (top fraud legs), Map (destination countries), Timeline (attack window).
- **CIM Models:** N/A

---

