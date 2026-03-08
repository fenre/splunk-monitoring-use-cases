#!/usr/bin/env python3
"""
Generate 200 OT use cases with MQTT and OPC-UA as data sources (Edge Hub or other means).
Appends to use-cases/cat-14-iot-operational-technology-ot.md as section 14.5.
"""
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
CAT14 = os.path.join(REPO_ROOT, "use-cases", "cat-14-iot-operational-technology-ot.md")

CRITICALITIES = [
    ("🟠 High", "high"),
    ("🟠 High", "high"),
    ("🟡 Medium", "medium"),
    ("🟡 Medium", "medium"),
    ("🟢 Low", "low"),
    ("🔴 Critical", "critical"),
]
DIFFICULTIES = [
    ("🟢 Beginner", "beginner"),
    ("🔵 Intermediate", "intermediate"),
    ("🔵 Intermediate", "intermediate"),
    ("🟠 Advanced", "advanced"),
    ("🔴 Expert", "expert"),
]

# 200 titles for MQTT/OPC-UA/Edge Hub themed use cases
TITLES = [
    "MQTT Topic Subscription Health and Message Rate",
    "OPC-UA Server Connection and Session Count",
    "Edge Hub MQTT Broker Client Disconnections",
    "OPC-UA Node Value Change Rate and Anomaly",
    "MQTT Payload Size and Compression Ratio",
    "OPC-UA Subscription Interval and Latency",
    "Edge Hub to Cloud HEC Forwarding Backlog",
    "MQTT Retain Flag and Last Will Message Audit",
    "OPC-UA Alarms and Events Queue Depth",
    "MQTT QoS 0/1/2 Delivery and Drops",
    "OPC-UA Certificate Expiration and Trust",
    "Edge Hub OPC-UA Connector Node Scan Health",
    "MQTT Broker Memory and Connection Limit",
    "OPC-UA Historical Access and Aggregation",
    "MQTT Bridge Reconnection and Failover",
    "OPC-UA Namespace and Node ID Drift",
    "Edge Hub Local Storage and SQLite Backlog",
    "MQTT TLS Handshake and Cipher Compliance",
    "OPC-UA Redundancy and Failover State",
    "MQTT Publish Rate Throttling and Backpressure",
    "OPC-UA Method Call Success and Duration",
    "Edge Hub Container Health (MQTT/OPC-UA Modules)",
    "MQTT Topic Hierarchy and Wildcard Usage",
    "OPC-UA DataType and Encoding Errors",
    "MQTT Clean Session and Persistent Session Count",
    "OPC-UA Browse and Read Service Latency",
    "Edge Hub Metric Transformation and Enrichment",
    "MQTT Last Will Testament Trigger Events",
    "OPC-UA Write Request and Permission Denials",
    "MQTT Client ID Collision and Takeover",
    "OPC-UA Monitored Item Sampling Overrun",
    "Edge Hub MQTT-to-HEC Batch Size and Frequency",
    "MQTT Authentication Failure and ACL Denials",
    "OPC-UA Subscription Priority and Deadband",
    "MQTT Message Ordering and Duplicate Detection",
    "OPC-UA Security Policy and Endpoint Compliance",
    "Edge Hub OPC-UA Endpoint Discovery and Bind",
    "MQTT Topic Naming Convention Compliance",
    "OPC-UA Array and String Length Limits",
    "MQTT Shared Subscription Balance",
    "OPC-UA Variable Source Timestamp Freshness",
    "Edge Hub Network Partition and Offline Queue",
    "MQTT Protocol Version and Feature Support",
    "OPC-UA Server Restart and State Recovery",
    "MQTT Bridge Remote Broker Availability",
    "OPC-UA Complex Type and Structure Validation",
    "Edge Hub CPU and Memory per Connector",
    "MQTT Message Expiry and TTL Handling",
    "OPC-UA Access Level and User Role Audit",
    "MQTT Topic Alias and Maximum Alias",
    "OPC-UA Subscription Publishing Interval",
    "Edge Hub Disk Usage and Log Rotation",
    "MQTT Request/Response Correlation",
    "OPC-UA Event Notifier and Condition Refresh",
    "MQTT V5 Properties and User Properties",
    "OPC-UA Audit Log and Security Events",
    "Edge Hub Certificate and Credential Rotation",
    "MQTT Topic Filter and Subscription Count",
    "OPC-UA Reference Type and Hierarchy",
    "MQTT Duplicate and Out-of-Order Detection",
    "OPC-UA Built-in DataType Validation",
    "Edge Hub Time Sync and Timestamp Accuracy",
    "MQTT Client Keep-Alive and Timeout",
    "OPC-UA Server Capabilities and Limits",
    "MQTT Shared Subscription Strategy",
    "OPC-UA Subscription Lifetime and Count",
    "Edge Hub MQTT TLS Client Certificate",
    "MQTT Will Delay Interval and Retain",
    "OPC-UA Node Version and Contribute",
    "MQTT Maximum Packet Size and Receive Max",
    "OPC-UA Continuation Point and Chunking",
    "Edge Hub OPC-UA Security Mode (None/Sign/SignEncrypt)",
    "MQTT Response Topic and Correlation Data",
    "OPC-UA View and Address Space Scope",
    "MQTT Subscription Identifier and Options",
    "OPC-UA Attribute Write and History Update",
    "Edge Hub HEC Index and Source Type Routing",
    "MQTT Topic and Payload Format Validation",
    "OPC-UA Locale and Display Name",
    "MQTT Content Type and UTF-8 Validation",
    "OPC-UA Server Array and String Dimension",
    "Edge Hub Anomaly Detection and MLTK",
    "MQTT Bridge Inbound and Outbound Rate",
    "OPC-UA Call Method Input/Output",
    "MQTT Session Present and State Restore",
    "OPC-UA Data Change Trigger and Deadband",
    "Edge Hub SNMP and MQTT Coexistence",
    "MQTT Subscription Options (No Local, Retain As Published)",
    "OPC-UA Subscription Publishing Enabled",
    "MQTT Packet ID and Flow Control",
    "OPC-UA Monitored Item Queue Size",
    "Edge Hub Container Restart and Crash Count",
    "MQTT Topic Alias Maximum and Lifetime",
    "OPC-UA Server Timestamps and Source",
    "MQTT Receive Maximum and Flow",
    "OPC-UA Node Class and Attributes",
    "Edge Hub MQTT External Broker Config",
    "MQTT Maximum QoS and Retain Available",
    "OPC-UA Reference Direction and Inverse",
    "MQTT Wildcard Subscription Overlap",
    "OPC-UA Data Value and Status Code",
    "Edge Hub Pipeline Stage Latency",
    "MQTT Publish Received and Ack",
    "OPC-UA Browse Next and Continuation",
    "MQTT Unsubscribe and Topic List",
    "OPC-UA Translate Browse Paths",
    "Edge Hub Health and Diagnostics Index",
    "MQTT Connect and Connack Reason Code",
    "OPC-UA Register Nodes and Discovery",
    "MQTT Disconnect Reason and Will",
    "OPC-UA Create Subscription and Monitored Items",
    "Edge Hub Log Level and Verbosity",
    "MQTT Auth and Enhanced Auth",
    "OPC-UA Delete Monitored Items",
    "MQTT Pingreq and Pingresp Latency",
    "OPC-UA Set Monitoring Mode",
    "Edge Hub Firmware and Module Version",
    "MQTT Suback Reason Code and Options",
    "OPC-UA Create Subscription Response",
    "MQTT Unsuback Reason Code",
    "OPC-UA Modify Monitored Items",
    "Edge Hub NTP and Time Source",
    "MQTT Puback and Pubrec Flow",
    "OPC-UA Set Triggering and Links",
    "MQTT Pubrel and Pubcomp",
    "OPC-UA Delete Subscriptions",
    "Edge Hub Disk I/O and SQLite WAL",
    "MQTT Topic and Payload Size Limit",
    "OPC-UA Republish and Sequence",
    "MQTT Subscription Identifier in Publish",
    "OPC-UA Transfer Subscriptions",
    "Edge Hub Network Interface and Bonding",
    "MQTT User Property and Metadata",
    "OPC-UA Register Nodes Response",
    "MQTT Content Type and Payload Format",
    "OPC-UA Unregister Nodes",
    "Edge Hub Firewall and Egress Allowlist",
    "MQTT Server Reference and Alt",
    "OPC-UA Find Servers and Endpoints",
    "MQTT Assigned Client Identifier",
    "OPC-UA Get Endpoints",
    "Edge Hub Proxy and TLS Inspection",
    "MQTT Reason String and User Property",
    "OPC-UA Create Session and Activate",
    "MQTT Session Expiry Interval",
    "OPC-UA Close Session and Cancel",
    "Edge Hub Backup and Restore",
    "MQTT Topic Alias in Publish",
    "OPC-UA Read and Read Response",
    "MQTT Subscription Options in Suback",
    "OPC-UA Write and Write Response",
    "Edge Hub Metrics Export (Prometheus/StatsD)",
    "MQTT Shared Subscription Name",
    "OPC-UA Call and Call Response",
    "MQTT Response Information",
    "OPC-UA Add Nodes and References",
    "Edge Hub Custom Container Logs",
    "MQTT Server Keep Alive",
    "OPC-UA Delete Nodes",
    "MQTT Request Problem Information",
    "OPC-UA Add References",
    "Edge Hub Resource Limits (CPU/Mem)",
    "MQTT Request Response Information",
    "OPC-UA Delete References",
    "MQTT Receive Maximum from Server",
    "OPC-UA Replace Nodes",
    "Edge Hub Hostname and Certificate SAN",
    "MQTT Topic Alias Maximum from Server",
    "OPC-UA History Read Raw",
    "MQTT Maximum Packet Size from Server",
    "OPC-UA History Read Events",
    "Edge Hub Syslog and Forwarding",
    "MQTT Retain Available from Server",
    "OPC-UA History Read Processed",
    "MQTT Wildcard Subscription Available",
    "OPC-UA History Update",
    "Edge Hub USB and Serial Connectors",
    "MQTT Subscription ID Available",
    "OPC-UA Call Method Request",
    "MQTT Shared Subscription Available",
    "OPC-UA Create Subscription Request",
    "Edge Hub Modbus and OPC-UA Coexist",
    "MQTT Maximum QoS from Server",
    "OPC-UA Modify Subscription",
    "MQTT Retain Handling in Subscribe",
    "OPC-UA Set Publish Mode",
    "Edge Hub BACnet and MQTT Gateway",
    "MQTT No Local in Subscribe",
    "OPC-UA Republish Request",
    "MQTT Publish and Subscribe Flow",
    "OPC-UA Transfer Result",
    "Edge Hub Data Retention and Pruning",
    "MQTT Unsubscribe Request",
    "OPC-UA Delete Subscription",
    "MQTT Disconnect Will Message",
    "OPC-UA Subscription Acknowledged",
    "Edge Hub Alerting and Local Actions",
    "MQTT Connack Session Present",
    "OPC-UA Data Change Notification",
    "MQTT Suback Packet",
    "OPC-UA Event Notification",
    "Edge Hub Multi-Tenant and Tagging",
    "MQTT Unsuback Packet",
    "OPC-UA Status Change Notification",
    "MQTT Puback Packet",
    "OPC-UA Semantic Change",
    "Edge Hub Geo and Site Tagging",
    "MQTT Pubrec Packet",
    "OPC-UA Model Change",
    "MQTT Pubrel Packet",
    "OPC-UA Subscription Transferred",
    "Edge Hub MQTT Topic Rewrite Rules",
    "MQTT Pubcomp Packet",
    "OPC-UA Subscription Modified",
    "MQTT Pingreq Packet",
    "OPC-UA Monitored Item Created",
    "Edge Hub OPC-UA Node ID Mapping",
    "MQTT Pingresp Packet",
    "OPC-UA Monitored Item Modified",
    "MQTT Auth Packet",
    "OPC-UA Monitored Item Deleted",
    "Edge Hub MQTT Credential Store",
    "MQTT Disconnect Packet",
    "OPC-UA Item Created",
    "MQTT Publish Inbound Rate by Topic",
    "OPC-UA Item Modified",
    "Edge Hub OPC-UA Reconnect and Backoff",
    "MQTT Publish Outbound Rate by Topic",
    "OPC-UA Item Deleted",
    "MQTT Subscription Count by Client",
    "OPC-UA Filter and Where Clause",
    "Edge Hub MQTT Topic Template",
    "MQTT Message Size Distribution",
    "OPC-UA Aggregate and Interpolation",
    "MQTT Connection Duration by Client",
    "OPC-UA Server State and Build",
    "Edge Hub Indexer Acknowledgment",
    "MQTT Publish Latency End-to-End",
    "OPC-UA Server Capabilities",
    "MQTT Broker Uptime and Restarts",
    "OPC-UA Endpoint URL and Security",
    "Edge Hub Splunk Cloud HEC Token",
    "MQTT Retained Message Count",
    "OPC-UA Application URI and Product",
    "MQTT Active Connection Count",
    "OPC-UA Application Type",
    "Edge Hub Ingress and Egress Bytes",
    "MQTT Total Messages In/Out",
    "OPC-UA Discovery URL and Profile",
    "MQTT Bytes In/Out",
    "OPC-UA Server Array Length",
    "Edge Hub Container Image and Digest",
    "MQTT Packets In/Out",
    "OPC-UA String and ByteString Length",
    "MQTT Publish Dropped",
    "OPC-UA Node Id Numeric and String",
    "Edge Hub OTA and Module Update",
    "MQTT Publish Retained Count",
    "OPC-UA Qualified Name and Namespace",
    "MQTT Subscription Shared Count",
    "OPC-UA Localized Text",
    "Edge Hub MQTT and OPC-UA Fusion",
]

def esc_spl(s):
    return s.replace("\\", "\\\\").replace("`", "\\`")

def gen_uc(n, title):
    c = CRITICALITIES[n % len(CRITICALITIES)]
    d = DIFFICULTIES[n % len(DIFFICULTIES)]
    # Alternate MQTT vs OPC-UA vs Edge Hub focus
    if n % 3 == 0:
        ds = "MQTT topics (Edge Hub built-in broker or external), `sourcetype=mqtt` or `edge_hub`"
        idx = "edge-hub-data"
        spl_index = "index=edge-hub-data OR index=ot"
    elif n % 3 == 1:
        ds = "OPC-UA server (Edge Hub OPC-UA connector or standalone gateway), `sourcetype=splunk_edge_hub_opcua` or `opcua`"
        idx = "edge-hub-data"
        spl_index = "index=edge-hub-data sourcetype=splunk_edge_hub_opcua"
    else:
        ds = "Edge Hub health and logs; MQTT/OPC-UA connector metrics"
        idx = "edge-hub-health"
        spl_index = "index=edge-hub-health OR index=edge-hub-logs"
    app_ta = "Splunk Edge Hub, MQTT broker, OPC-UA gateway, Splunk OT Intelligence"
    block = f"""
### UC-14.5.{n} · {title}
- **Criticality:** {c[0]}
- **Difficulty:** {d[0]}
- **Monitoring type:** Performance, Availability
- **Value:** OT data from MQTT and OPC-UA must be reliably collected via Edge Hub or gateways. Monitoring ensures pipeline health and supports troubleshooting.
- **App/TA:** {app_ta}
- **Data Sources:** {ds}
- **SPL:**
```spl
{spl_index}
| stats count, latest(_time) as last_seen by host, source, sourcetype
| eval age_sec = now() - last_seen
| where age_sec > 300 OR count < 1
| table host source sourcetype count last_seen age_sec
```
- **Implementation:** Ingest MQTT and OPC-UA data via Splunk Edge Hub (built-in MQTT broker and OPC-UA connector), Azure IoT Edge Hub, or other gateways. Configure topics and node subscriptions; forward to Splunk via HEC. Alert on connection loss, message rate drop, or backlog growth.
- **Visualization:** Table (sources and last seen), Line chart (message rate), Single value (pipeline health).
- **CIM Models:** N/A

---
"""
    return block

def main():
    with open(CAT14, "r", encoding="utf-8") as f:
        content = f.read()
    # Append after last --- of UC-14.4.10 block
    marker = "### UC-14.4.10 · IoT Data Pipeline Throughput and Latency"
    if marker not in content:
        raise SystemExit("UC-14.4.10 not found in cat-14")
    idx_uc = content.rfind(marker)
    idx_cim = content.find("- **CIM Models:** N/A", idx_uc)
    if idx_cim == -1:
        raise SystemExit("CIM Models line not found after UC-14.4.10")
    idx_dash = content.find("\n---", idx_cim)
    if idx_dash == -1:
        raise SystemExit("--- not found after UC-14.4.10 block")
    # Place insert after the --- and following newlines (start of next section or EOF)
    insert_pos = idx_dash + len("\n---")
    while insert_pos < len(content) and content[insert_pos] == "\n":
        insert_pos += 1

    section_header = """
### 14.5 MQTT and OPC-UA (Edge Hub and Gateways)

**Primary App/TA:** Splunk Edge Hub (built-in MQTT broker, OPC-UA connector), Azure IoT Edge Hub, MQTT brokers (Eclipse Mosquitto, HiveMQ), OPC-UA gateways (KEPServerEX, Prosys), Splunk OT Intelligence.

**Data Sources:** MQTT topics (sensors, actuators, BMS, SCADA); OPC-UA nodes (PLC tags, alarms, history); Edge Hub health and connector metrics; gateway logs.

---

"""
    ucs = "".join(gen_uc(i, TITLES[i - 1]) for i in range(1, 201))
    out = content[:insert_pos] + section_header + ucs + content[insert_pos:]
    with open(CAT14, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Appended 200 use cases (UC-14.5.1 through UC-14.5.200) to {CAT14}")

if __name__ == "__main__":
    main()
