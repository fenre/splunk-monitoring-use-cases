#!/usr/bin/env python3
"""Rewrite the 39 Meraki UCs that misuse `sourcetype="meraki:devices"`.

The TA's `meraki:devices` input only returns device inventory metadata
(serial, model, firmware, lanIp, productType, network.{id,name}, tags,
address, lat/lng, configurationUpdatedAt). It does NOT contain any of:
- CPU/memory utilization
- RSSI / channel utilization / per-client wireless metrics
- Per-port utilization / PoE wattage / NAT pool counters
- Latency / jitter / packet loss
- License expiry / certificate expiry / DHCP pool exhaustion
- Stack health, SIM status, mesh link quality

Each UC below is rewritten to either:
1. Use the canonical TA sourcetype that actually exposes the requested data
   (e.g., meraki:switchportsoverview, meraki:devicesuplinkslossandlatency,
   meraki:appliancesdwanstatistics, meraki:wirelessdevicespacketlossbydevice,
   meraki:assurancealerts, meraki:devicesavailabilities, meraki:firmwareupgrades,
   meraki:licensesoverview, meraki:summaryswitchpowerhistory).
2. Use webhooks (`meraki:webhook`) when the metric is event-driven only
   (per-client RSSI, channel utilization, per-port flap, association events).
3. Honestly disclaim the metric and pivot to the closest available signal
   (e.g., switch CPU/memory -> assurance alerts + SNMP polling note;
   NAT pool -> assurance alerts + syslog).

The dataSources / implementation fields are rewritten to match.

Run:
    PYTHONPATH=src python3 scripts/rewrite_meraki_devices_misuse.py

After running, regenerate detailedImplementation:
    PYTHONPATH=src python3 scripts/regen_di_for_ucs.py --meraki-devices-fix
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Per-UC rewrites. Each entry maps repo-relative path -> field overrides.
# ---------------------------------------------------------------------------

REWRITES: dict[str, dict[str, str]] = {

    # =========================================================================
    # SWITCH (MS) UCs
    # =========================================================================

    "content/cat-05-network-infrastructure/UC-5.1.36.json": {
        "spl": (
            'index=meraki sourcetype="meraki:switchportsoverview" earliest=-24h\n'
            '| stats latest(counts.byStatus.active) as active_ports,\n'
            '        latest(counts.byStatus.inactive) as inactive_ports,\n'
            '        latest(counts.byStatus.disconnected) as disconnected_ports,\n'
            '        latest(counts.byMedia.wired) as wired_ports\n'
            '         by network.id, network.name\n'
            '| eval total_ports = active_ports + inactive_ports + disconnected_ports\n'
            '| eval pct_in_use = round(active_ports*100/total_ports, 1)\n'
            '| where pct_in_use > 80\n'
            '| sort - pct_in_use'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Switch Ports Overview input "
            "(sourcetype=meraki:switchportsoverview, daily, OAuth scope switch:telemetry:read). "
            "Optional: configure the Webhook Logs (HEC) input + Meraki Dashboard alerts on "
            "port_status_changed for near-real-time per-port flap detection (sourcetype=meraki:webhook)."
        ),
        "implementation": (
            "1. In Splunk_TA_cisco_meraki, enable the Switch Ports Overview input. The TA polls "
            "GET /organizations/{orgId}/switch/ports/overview daily and writes one event per "
            "network with counts.byStatus.{active,inactive,disconnected}, counts.byMedia.{wired,wireless} "
            "and counts.byLinkSpeed.{10mbps,100mbps,1Gbps,10Gbps}. 2. Per-port utilization counters "
            "are NOT exposed by the Dashboard API; for live per-port flap detection enable the "
            "Webhook Logs (HEC) input and configure a Meraki alert profile that triggers on "
            "'switch port status changed'. 3. Tune the 80% in-use threshold to your capacity policy."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.1.37.json": {
        "spl": (
            'index=meraki sourcetype="meraki:summarytopswitchesbyenergyusage" earliest=-30d\n'
            '| stats latest(usage.total) as total_kwh, latest(usage.percentage) as pct_of_org\n'
            '         by serial, name, network.name, model\n'
            '| eval avg_watts = round(total_kwh*1000/(30*24), 1)\n'
            '| sort - total_kwh\n'
            '| head 20'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Summary Top Switches by Energy Usage input "
            "(sourcetype=meraki:summarytopswitchesbyenergyusage, daily) and optionally the "
            "Switch Power History input (sourcetype=meraki:summaryswitchpowerhistory) for "
            "per-switch hourly trends."
        ),
        "implementation": (
            "1. Enable the Summary Top Switches by Energy Usage input (TA v3+, OAuth scope "
            "switch:telemetry:read). The TA polls GET /organizations/{orgId}/summary/top/switches/"
            "byEnergyUsage daily and emits the org's top 10 switches with usage.total (kWh) and "
            "usage.percentage. 2. For per-switch hourly history enable the Switch Power History "
            "input (TA v3.2+) which polls .../summary/switch/powerHistory and emits "
            "intervals[].usage.total. 3. Per-PoE-port wattage is not exposed; if you need it use "
            "the device-level webhook 'switch port poe overcurrent' or fall back to SNMP polling."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.1.45.json": {
        "spl": (
            'index=meraki sourcetype="meraki:assurancealerts"\n'
            '    deviceType="switch"\n'
            '    (categoryType="device" OR categoryType="connectivity")\n'
            '    earliest=-24h\n'
            '| stats count as alert_count,\n'
            '        values(title) as alert_titles,\n'
            '        latest(severity) as severity,\n'
            '        latest(dismissedAt) as dismissed_at\n'
            '         by deviceSerial, networkName\n'
            '| where isnull(dismissed_at) AND alert_count > 0\n'
            '| sort - alert_count'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input "
            "(sourcetype=meraki:assurancealerts, hourly, OAuth scope dashboard:general:telemetry:read). "
            "Note: the Meraki Dashboard API does NOT expose per-switch CPU or memory counters. "
            "If you need raw CPU/memory telemetry, deploy SNMP polling (Splunk SNMP modular "
            "input) against the switch directly using IF-MIB / CISCO-PROCESS-MIB OIDs."
        ),
        "implementation": (
            "1. Enable the Assurance Alerts input in Splunk_TA_cisco_meraki. The TA polls "
            "GET /organizations/{orgId}/assurance/alerts hourly and emits one event per alert "
            "with deviceType, deviceSerial, categoryType, title, severity, dismissedAt. 2. "
            "Performance issues (high CPU, memory pressure, queue drops) surface as device "
            "alerts with categoryType=device or =connectivity. 3. For continuous CPU/memory "
            "graphs, supplement with SNMP polling against the switch's management IP using "
            "OIDs from CISCO-PROCESS-MIB (cpmCPUTotal5minRev) and CISCO-MEMORY-POOL-MIB."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.1.46.json": {
        "spl": (
            'index=meraki sourcetype="meraki:devicesavailabilities" productType="switch" earliest=-1h\n'
            '| stats values(serial) as members,\n'
            '        count as stack_size,\n'
            '        sum(eval(if(status="online",0,1))) as offline_members,\n'
            '        latest(status) as latest_status\n'
            '         by network.id, network.name\n'
            '| where stack_size > 1 AND offline_members > 0\n'
            '| sort - offline_members'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities input "
            "(sourcetype=meraki:devicesavailabilities, daily, TA v3.3+) and Device Availabilities "
            "Change History input (sourcetype=meraki:devicesavailabilitieschangehistory, hourly) "
            "for stack member status. Stack inventory comes from meraki:devices (productType=switch, "
            "switchProfileId field identifies stacked members)."
        ),
        "implementation": (
            "1. Enable Devices Availabilities and Devices Availabilities Change History inputs. "
            "Meraki MS stacks are modeled as multiple switches in the same network sharing a "
            "switchProfileId; status field is online/offline/dormant/alerting. 2. The query above "
            "groups switches by network and counts offline members. For more accurate per-stack "
            "grouping use 'index=meraki sourcetype=meraki:devices productType=switch' joined on "
            "switchProfileId. 3. Pair with an alert profile that triggers when offline_members "
            "exceeds 0 within a stack-bearing network."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.1.47.json": {
        "spl": (
            'index=meraki sourcetype="meraki:switchportsbyswitch" earliest=-24h\n'
            '| spath path=ports{} output=port_arr\n'
            '| mvexpand port_arr\n'
            '| spath input=port_arr\n'
            '| where type="trunk" AND enabled="true"\n'
            '| stats count as trunk_port_count,\n'
            '        values(name) as trunk_port_names,\n'
            '        sum(eval(if(status="Connected",0,1))) as down_trunks\n'
            '         by serial, name, network.name\n'
            '| where down_trunks > 0\n'
            '| sort - down_trunks'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Switch Ports by Switch input "
            "(sourcetype=meraki:switchportsbyswitch, daily, TA v3.2+, OAuth scope switch:config:read). "
            "Per-port utilization counters are NOT exposed by the polling API; use the Webhook "
            "Logs (HEC) input + Meraki alert profile 'switch port status changed' or "
            "'switch port flapping' for live trunk-flap detection."
        ),
        "implementation": (
            "1. Enable the Switch Ports by Switch input. The TA polls GET /organizations/{orgId}/"
            "switch/ports/bySwitch daily and emits one event per switch with a ports[] array of "
            "{portId, name, type, enabled, status, vlan, allowedVlans, ...}. 2. Filter where "
            "type=trunk to identify uplink ports between switches. 3. For live link-down or "
            "utilization, configure a Meraki webhook alert profile and ingest via the Webhook "
            "Logs (HEC) input."
        ),
    },

    # =========================================================================
    # CELLULAR GATEWAY (MG) UCs - Honest disclaimers, use closest workable proxy
    # =========================================================================

    "content/cat-05-network-infrastructure/UC-5.1.52.json": {
        "spl": (
            'index=meraki sourcetype="meraki:devicesuplinkslossandlatency" earliest=-24h\n'
            '| spath path=timeSeries{} output=ts\n'
            '| mvexpand ts\n'
            '| spath input=ts\n'
            '| join type=left serial [\n'
            '    search index=meraki sourcetype="meraki:devices" productType="cellularGateway"\n'
            '    | stats latest(model) as model, latest(name) as device_name by serial\n'
            '  ]\n'
            '| where isnotnull(model)\n'
            '| stats avg(latencyMs) as avg_latency,\n'
            '        avg(lossPercent) as avg_loss,\n'
            '        max(lossPercent) as peak_loss\n'
            '         by serial, device_name, model, networkId, uplink\n'
            '| eval link_quality = case(avg_loss>5,"Critical", avg_loss>2 OR avg_latency>250,"Warning", 1=1,"OK")\n'
            '| sort - peak_loss'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Uplinks Loss and Latency input "
            "(sourcetype=meraki:devicesuplinkslossandlatency, TA v3.3+) and Devices input "
            "(sourcetype=meraki:devices) for MG inventory. NOTE: actual cellular RSSI/SINR/RSRP "
            "is NOT exposed by the Dashboard API; this UC monitors uplink loss/latency as a "
            "behavioural proxy. For raw radio metrics, use SNMP polling against the MG."
        ),
        "implementation": (
            "1. Enable Devices Uplinks Loss and Latency input (TA v3.3+, polls GET "
            "/organizations/{orgId}/devices/uplinksLossAndLatency, OAuth scope "
            "dashboard:general:telemetry:read). The MG cellular uplink is reported alongside "
            "MX uplinks. 2. Join with the Devices input to filter to productType=cellularGateway. "
            "3. The TA returns timeSeries[] of {ts, lossPercent, latencyMs}. 4. For raw RSSI/SINR "
            "polling use Splunk's SNMP modular input against the MG management IP and the "
            "MERAKI-CLOUD-CONTROLLER-MIB cellular OIDs."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.1.53.json": {
        "spl": (
            'index=meraki sourcetype="meraki:summarytopdevicesbyusage" earliest=-30d\n'
            '| join type=left serial [\n'
            '    search index=meraki sourcetype="meraki:devices" productType="cellularGateway"\n'
            '    | stats latest(model) as model, latest(name) as device_name, latest(network.name) as network_name by serial\n'
            '  ]\n'
            '| where isnotnull(model)\n'
            '| stats latest(usage.total) as total_kb,\n'
            '        latest(usage.percentage) as pct_of_org\n'
            '         by serial, device_name, model, network_name\n'
            '| eval total_gb = round(total_kb/1024/1024, 2)\n'
            '| where total_gb > 0\n'
            '| sort - total_gb'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Summary Top Devices by Usage input "
            "(sourcetype=meraki:summarytopdevicesbyusage, daily) and Devices input "
            "(sourcetype=meraki:devices). NOTE: the TA does NOT expose per-SIM data plan "
            "consumption or carrier billing data. For real overage/quota tracking, use the "
            "Meraki Dashboard cellular billing UI export or the carrier portal API."
        ),
        "implementation": (
            "1. Enable the Summary Top Devices by Usage input (TA v3+, polls "
            "GET /organizations/{orgId}/summary/top/devices/byUsage daily, OAuth scope "
            "dashboard:general:telemetry:read). 2. Filter to MG devices via a left join on the "
            "Devices input where productType=cellularGateway. 3. The 'usage.total' field is in "
            "kB; convert to GB for plan-quota comparison. 4. Per-SIM monthly billing data must be "
            "pulled from the carrier (AT&T, Verizon) directly; the Meraki API does not expose it."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.1.55.json": {
        "spl": (
            'index=meraki sourcetype="meraki:devices" productType="cellularGateway"\n'
            '| stats latest(serial) as serial, latest(model) as model, latest(firmware) as firmware,\n'
            '        latest(lanIp) as lan_ip, latest(network.name) as network_name\n'
            '         by name\n'
            '| join type=left serial [\n'
            '    search index=meraki sourcetype="meraki:devicesavailabilities" productType="cellularGateway"\n'
            '    | stats latest(status) as status, latest(_time) as last_seen by serial\n'
            '  ]\n'
            '| join type=left serial [\n'
            '    search index=meraki sourcetype="meraki:assurancealerts" deviceType="cellularGateway" earliest=-24h\n'
            '    | stats values(title) as open_alerts, count as alert_count by deviceSerial\n'
            '    | rename deviceSerial as serial\n'
            '  ]\n'
            '| eval status = coalesce(status, "unknown")\n'
            '| sort - alert_count'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Devices, Devices Availabilities, and "
            "Assurance Alerts inputs. NOTE: SIM card status, ICCID, IMSI, plan expiry, and "
            "active carrier are NOT exposed by the Meraki Dashboard API. The closest signal "
            "available is the Assurance Alerts feed which fires on cellular registration loss, "
            "SIM swap, and APN failure."
        ),
        "implementation": (
            "1. Enable Devices, Devices Availabilities, and Assurance Alerts inputs in "
            "Splunk_TA_cisco_meraki. 2. The base inventory comes from meraki:devices "
            "(serial, model, firmware, lanIp, network). 3. Online/offline state comes from "
            "meraki:devicesavailabilities. 4. Cellular-specific events (SIM lost, registration "
            "failure, APN errors) appear in meraki:assurancealerts with deviceType=cellularGateway. "
            "5. For raw SIM inventory and plan expiry data, integrate with your carrier billing "
            "portal (AT&T Control Center, Verizon ThingSpace) — those APIs are out of scope for "
            "the Meraki TA."
        ),
    },

    # =========================================================================
    # MX FIREWALL / VPN UCs
    # =========================================================================

    "content/cat-05-network-infrastructure/UC-5.2.27.json": {
        "spl": (
            'index=meraki sourcetype="meraki:assurancealerts"\n'
            '    deviceType="appliance"\n'
            '    (title="*NAT*" OR title="*port*" OR title="*translation*" OR categoryType="appliance")\n'
            '    earliest=-24h\n'
            '| stats count as alert_count,\n'
            '        values(title) as alert_titles,\n'
            '        latest(severity) as severity,\n'
            '        latest(dismissedAt) as dismissed_at\n'
            '         by deviceSerial, networkName\n'
            '| where isnull(dismissed_at) AND alert_count > 0\n'
            '| sort - alert_count'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input "
            "(sourcetype=meraki:assurancealerts) and SC4S Meraki vendor pack (sourcetype=meraki, "
            "type=events) for syslog-side NAT exhaustion messages. NOTE: the Meraki Dashboard "
            "API does NOT expose live NAT translation table counters; alert-driven monitoring is "
            "the only practical path."
        ),
        "implementation": (
            "1. Enable the Assurance Alerts input in Splunk_TA_cisco_meraki and confirm Meraki "
            "alert profiles include 'NAT translation table near capacity' and 'connection table "
            "full'. 2. Configure SC4S to receive Meraki MX syslog (UDP/514) and forward the "
            "events sourcetype to Splunk; appliance NAT/connection-table syslog messages match "
            "type=events. 3. Pair the alert query above with a 'last 1h' real-time dashboard for "
            "branch operators."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.2.33.json": {
        "spl": (
            'index=meraki sourcetype="meraki:devicesuplinkslossandlatency" earliest=-1h\n'
            '| spath path=timeSeries{} output=ts\n'
            '| mvexpand ts\n'
            '| spath input=ts\n'
            '| stats avg(latencyMs) as avg_latency,\n'
            '        avg(lossPercent) as avg_loss,\n'
            '        max(latencyMs) as peak_latency,\n'
            '        max(lossPercent) as peak_loss\n'
            '         by serial, networkId, uplink, ip\n'
            '| eval link_quality = case(\n'
            '    avg_loss>5 OR peak_loss>20, "Critical",\n'
            '    avg_loss>2 OR avg_latency>200, "Warning",\n'
            '    1=1, "OK")\n'
            '| where link_quality != "OK"\n'
            '| sort - avg_loss'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Uplinks Loss and Latency input "
            "(sourcetype=meraki:devicesuplinkslossandlatency, TA v3.3+, OAuth scope "
            "dashboard:general:telemetry:read). Polls "
            "GET /organizations/{orgId}/devices/uplinksLossAndLatency for every MX and MG."
        ),
        "implementation": (
            "1. Enable the Devices Uplinks Loss and Latency input. The TA emits one event per "
            "device-uplink containing serial, networkId, uplink (wan1/wan2/cellular), ip, and a "
            "timeSeries[] array of {ts, lossPercent, latencyMs} samples (default 5-minute granularity, "
            "5-minute timespan). 2. Use mvexpand on timeSeries to flatten samples for trending. "
            "3. Tune thresholds (>2% loss, >200ms latency) to your SLA. 4. Jitter is not directly "
            "reported by this endpoint; if you need jitter, use the Appliance VPN Stats input "
            "(meraki:appliancesdwanstatistics) which carries jitterMs for SD-WAN tunnels."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.2.40.json": {
        "spl": (
            'index=meraki sourcetype="meraki:appliancesdwanstatuses" earliest=-1h\n'
            '| spath path=uplinks{} output=uplink_arr\n'
            '| mvexpand uplink_arr\n'
            '| spath input=uplink_arr\n'
            '| stats latest(status) as state,\n'
            '        latest(ip) as uplink_ip,\n'
            '        latest(publicIp) as public_ip,\n'
            '        latest(gateway) as gateway\n'
            '         by networkId, networkName, interface\n'
            '| where state != "active" AND state != "ready"\n'
            '| append [\n'
            '    search index=meraki sourcetype="meraki:appliancesdwanstatistics" earliest=-1h\n'
            '    | stats avg(latencyMs) as avg_latency, avg(lossPercent) as avg_loss,\n'
            '            avg(jitterMs) as avg_jitter, last(receiverUplink) as receiver_uplink\n'
            '             by networkId, networkName, senderUplink\n'
            '    | where avg_loss>5 OR avg_latency>500 OR avg_jitter>50\n'
            '  ]\n'
            '| sort networkName'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Appliance VPN Statuses input "
            "(sourcetype=meraki:appliancesdwanstatuses, daily, OAuth scope sdwan:telemetry:read) "
            "and Appliance VPN Stats input (sourcetype=meraki:appliancesdwanstatistics, daily). "
            "Both polled from /organizations/{orgId}/appliance/vpn/statuses and /vpn/stats."
        ),
        "implementation": (
            "1. Enable both Appliance VPN Statuses and Appliance VPN Stats inputs in "
            "Splunk_TA_cisco_meraki. 2. The Statuses input returns one event per network with an "
            "uplinks[] array containing {interface, status, ip, publicIp, gateway} per WAN port "
            "and a vpnPeers[] array of remote MX statuses. 3. The Stats input returns per-pair "
            "statistics with senderUplink, receiverUplink, latencyMs, jitterMs, lossPercent, "
            "mosScore. 4. Tune thresholds (>5% loss, >500ms latency, >50ms jitter) to your SLA. "
            "5. For live tunnel-down events, configure a Meraki alert profile on 'site to site "
            "VPN connectivity change' and ingest via the Webhook Logs (HEC) input."
        ),
    },

    # =========================================================================
    # WIRELESS (MR) UCs - mostly require webhook + assurance + packet-loss inputs
    # =========================================================================

    "content/cat-05-network-infrastructure/UC-5.4.3.json": {
        "spl": (
            'index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")\n'
            '    (alertType="utilization" OR alertType="rf_spectrum" OR alertTypeId="ap_radar_detected")\n'
            '    earliest=-24h\n'
            '| spath\n'
            '| stats count as event_count,\n'
            '        values(alertData.channel) as channels,\n'
            '        values(alertData.band) as bands\n'
            '         by deviceSerial, deviceName, networkName\n'
            '| where event_count > 0\n'
            '| sort - event_count'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver (sourcetype=meraki:webhook) "
            "configured via TA v3.2+ with Meraki alert profile entries for 'high channel "
            "utilization', 'radar detected (DFS)', and 'rogue AP detected'. Per-AP per-channel "
            "utilization is NOT exposed by the polled Dashboard API."
        ),
        "implementation": (
            "1. In Splunk_TA_cisco_meraki configure the HEC token and the Webhook Logs (HEC) "
            "input. The TA will provision the receiver in Meraki Dashboard automatically (TA v3.2+). "
            "2. In Meraki Dashboard go to Network-wide -> Alerts and enable the 'high channel "
            "utilization' and 'rogue access point detected' alert types pointing at the TA's "
            "webhook receiver. 3. The webhook payload arrives as JSON with alertType, alertData.*, "
            "deviceSerial, deviceName, networkName. 4. For continuous channel-utilization graphs "
            "you must scrape the Dashboard UI (RF Spectrum) or use a 3rd-party WiFi analyzer."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.5.json": {
        "spl": (
            'index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")\n'
            '    (alertType="client_connectivity" OR alertTypeId="client_connection_changed"\n'
            '     OR alertType="association")\n'
            '    earliest=-24h\n'
            '| spath\n'
            '| eval client_mac = coalesce(\'alertData.clientMac\', \'alertData.client.mac\', \'alertData.mac\')\n'
            '| eval ap_name = coalesce(deviceName, \'alertData.deviceName\')\n'
            '| timechart span=1h dc(client_mac) as concurrent_clients by ap_name'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver "
            "(sourcetype=meraki:webhook) configured for client connectivity alerts. The polled "
            "Dashboard API does NOT expose a per-AP client list; per-association events come "
            "via webhook only."
        ),
        "implementation": (
            "1. Enable the Webhook Logs (HEC) input in Splunk_TA_cisco_meraki and configure a "
            "Meraki Dashboard alert profile that includes 'client connection changed' and "
            "'unique client connected'. 2. Each webhook event carries alertData.clientMac and "
            "deviceName (the AP). 3. Use dc(client_mac) over a sliding window for concurrent "
            "clients per AP. 4. For the network-wide totals (not per-AP), the polled "
            "meraki:summarytopclientsbyusage input lists the top 10 clients by usage but does "
            "not give a complete client roster."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.13.json": {
        "spl": (
            'index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")\n'
            '    alertType="client_connectivity"\n'
            '    earliest=-24h\n'
            '| spath\n'
            '| eval rssi_dbm = coalesce(\'alertData.rssi\', \'alertData.signal.rssi\')\n'
            '| where isnotnull(rssi_dbm) AND isnum(rssi_dbm)\n'
            '| eval rssi_level = case(\n'
            '    rssi_dbm>=-60, "Excellent",\n'
            '    rssi_dbm>=-70, "Good",\n'
            '    rssi_dbm>=-80, "Fair",\n'
            '    1=1, "Poor")\n'
            '| stats avg(rssi_dbm) as avg_rssi, min(rssi_dbm) as min_rssi, count\n'
            '         by deviceSerial, deviceName, rssi_level\n'
            '| sort avg_rssi'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver "
            "(sourcetype=meraki:webhook) with the Meraki Dashboard alert profile 'client "
            "connection changed' enabled. The polled Dashboard API does NOT expose per-client "
            "RSSI; webhook is the only path."
        ),
        "implementation": (
            "1. Enable the Webhook Logs (HEC) input in Splunk_TA_cisco_meraki (TA v3.2+) and "
            "let it provision the Meraki webhook receiver. 2. In Meraki Dashboard enable the "
            "'client connection changed' alert profile. 3. The webhook payload includes "
            "alertData.rssi (dBm). 4. For end-to-end client experience graphs, also enable the "
            "Wireless Packet Loss by Device input (meraki:wirelessdevicespacketlossbydevice) "
            "which exposes upstream/downstream packet loss percentages per AP."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.15.json": {
        "spl": (
            'index=meraki sourcetype="meraki:wirelessdevicespacketlossbydevice" earliest=-24h\n'
            '| stats avg(downstream.lossPercentage) as avg_dl_loss,\n'
            '        avg(upstream.lossPercentage) as avg_ul_loss,\n'
            '        avg(downstream.total) as avg_dl_packets,\n'
            '        avg(upstream.total) as avg_ul_packets\n'
            '         by serial, name, network.name\n'
            '| eval health_score = round(100 - ((avg_dl_loss + avg_ul_loss) / 2), 1)\n'
            '| sort health_score'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Wireless Packet Loss by Device input "
            "(sourcetype=meraki:wirelessdevicespacketlossbydevice, TA v3+, OAuth scope "
            "wireless:telemetry:read). NOTE: per-SSID throughput, retry rate, and connection "
            "time are NOT exposed by the polled API; for those, use webhooks or the per-network "
            "wireless health endpoints (not currently in the TA)."
        ),
        "implementation": (
            "1. Enable the Wireless Packet Loss by Device input in Splunk_TA_cisco_meraki. "
            "The TA polls GET /organizations/{orgId}/wireless/devices/packetLoss/byDevice daily "
            "and emits one event per AP with downstream.{lossPercentage,total} and upstream.* "
            "fields. 2. Aggregate per network for a coarse 'wireless health' indicator. 3. "
            "Per-SSID metrics need either webhook ingestion (client_connection_changed) with "
            "alertData.ssid grouping, or a custom modular input that calls "
            "GET /networks/{networkId}/wireless/ssids/.../latencyStats."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.16.json": {
        "spl": (
            'index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")\n'
            '    (alertType="utilization" OR alertTypeId="ap_radar_detected"\n'
            '     OR alertType="rogue_ap_detected" OR alertType="rf_spectrum")\n'
            '    earliest=-24h\n'
            '| spath\n'
            '| eval channel = coalesce(\'alertData.channel\', \'alertData.rf.channel\')\n'
            '| eval band = coalesce(\'alertData.band\', \'alertData.rf.band\')\n'
            '| stats count as event_count, values(channel) as channels\n'
            '         by deviceSerial, deviceName, band, networkName\n'
            '| sort - event_count'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver "
            "(sourcetype=meraki:webhook) with alert profiles for 'high channel utilization', "
            "'rogue AP detected', and 'radar detected (DFS)'. The polled Dashboard API does NOT "
            "return real-time per-channel utilization counters."
        ),
        "implementation": (
            "1. Configure the HEC token and Webhook Logs (HEC) input in Splunk_TA_cisco_meraki. "
            "2. In Meraki Dashboard enable the relevant wireless alert profiles. 3. Each event "
            "carries alertData.channel, alertData.band, and deviceSerial. 4. For continuous "
            "real-time RF spectrum analysis, supplement with a dedicated WiFi analyzer "
            "(Ekahau, NetSpot, AirMagnet) and forward its output to Splunk."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.18.json": {
        "spl": (
            'index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")\n'
            '    alertType="client_connectivity"\n'
            '    earliest=-24h\n'
            '| spath\n'
            '| eval client_mac = coalesce(\'alertData.clientMac\', \'alertData.client.mac\')\n'
            '| eval client_os = coalesce(\'alertData.os\', \'alertData.client.os\', \'alertData.deviceTypePrediction\')\n'
            '| eval client_manufacturer = \'alertData.client.manufacturer\'\n'
            '| where isnotnull(client_mac)\n'
            '| stats dc(client_mac) as device_count\n'
            '         by client_os, client_manufacturer\n'
            '| eventstats sum(device_count) as total\n'
            '| eval pct = round(device_count*100/total, 1)\n'
            '| sort - device_count'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver "
            "(sourcetype=meraki:webhook) with 'client connection changed' alerts enabled. "
            "Per-client OS/manufacturer detection is provided by Meraki's fingerprinting in "
            "the webhook payload only; not in the polled Dashboard API."
        ),
        "implementation": (
            "1. Enable the Webhook Logs (HEC) input and the 'client connection changed' alert "
            "profile in Meraki Dashboard. 2. The alertData payload contains client.os, "
            "client.manufacturer, deviceTypePrediction. 3. Use dc(client_mac) to count unique "
            "devices over the period. 4. For corporate/personal segmentation, enrich with a "
            "lookup against your MDM (Meraki Systems Manager, Jamf, Intune)."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.19.json": {
        "spl": (
            'index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")\n'
            '    alertType="client_connectivity"\n'
            '    earliest=-24h\n'
            '| spath\n'
            '| eval client_mac = coalesce(\'alertData.clientMac\', \'alertData.client.mac\')\n'
            '| eval band = coalesce(\'alertData.band\', \'alertData.rf.band\')\n'
            '| where isnotnull(client_mac) AND isnotnull(band)\n'
            '| stats dc(client_mac) as client_count by band\n'
            '| eventstats sum(client_count) as total\n'
            '| eval band_share_pct = round(client_count*100/total, 1)\n'
            '| sort - client_count'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver "
            "(sourcetype=meraki:webhook) with 'client connection changed' alerts. The polled "
            "Dashboard API does not break down clients by band; webhook payloads include "
            "alertData.band on association events."
        ),
        "implementation": (
            "1. Enable the Webhook Logs (HEC) input and configure 'client connection changed' "
            "alerts in Meraki Dashboard. 2. Each association event includes alertData.band "
            "(2.4GHz / 5GHz / 6GHz). 3. Calculate the share of clients on each band; if "
            "5GHz/6GHz share is below ~70% on dual-band capable APs, review band-steering "
            "configuration in Meraki Dashboard -> Wireless -> Radio settings. 4. For per-AP "
            "band steering effectiveness, group by deviceSerial in addition to band."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.21.json": {
        "spl": (
            'index=meraki sourcetype="meraki:wirelessdevicespacketlossbydevice" earliest=-24h\n'
            '| stats avg(downstream.lossPercentage) as avg_dl_loss,\n'
            '        avg(upstream.lossPercentage) as avg_ul_loss,\n'
            '        max(downstream.lossPercentage) as peak_dl_loss\n'
            '         by serial, name, network.name\n'
            '| eval client_health = case(\n'
            '    avg_dl_loss>5 OR avg_ul_loss>5, "Critical",\n'
            '    avg_dl_loss>2 OR avg_ul_loss>2, "Warning",\n'
            '    1=1, "OK")\n'
            '| where client_health != "OK"\n'
            '| sort - peak_dl_loss'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Wireless Packet Loss by Device input "
            "(sourcetype=meraki:wirelessdevicespacketlossbydevice). NOTE: per-client wireless "
            "latency is NOT exposed by the polled API; this UC monitors per-AP packet loss as a "
            "proxy. For round-trip latency, supplement with a synthetic ping monitor "
            "(Splunk_TA_ping or ThousandEyes Endpoint Agent)."
        ),
        "implementation": (
            "1. Enable the Wireless Packet Loss by Device input. The TA polls "
            "GET /organizations/{orgId}/wireless/devices/packetLoss/byDevice daily and returns "
            "downstream.{lossPercentage,total} and upstream.* per AP. 2. High packet loss is "
            "the strongest available signal for client experience problems on Meraki MR APs. "
            "3. For latency you have two options: (a) ingest webhook 'client connection "
            "changed' events which include alertData.latency in some payloads, or (b) deploy a "
            "synthetic probe (ICMP ping or ThousandEyes Endpoint Agent) to measure RTT."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.24.json": {
        "spl": (
            'index=meraki sourcetype="meraki:assurancealerts"\n'
            '    deviceType="wireless"\n'
            '    earliest=-24h\n'
            '| stats count as alert_count,\n'
            '        values(title) as alert_titles,\n'
            '        latest(severity) as severity,\n'
            '        latest(dismissedAt) as dismissed_at\n'
            '         by deviceSerial, deviceName, networkName, categoryType\n'
            '| where isnull(dismissed_at)\n'
            '| eval health_band = case(\n'
            '    alert_count>=10 OR severity="critical", "Critical",\n'
            '    alert_count>=5 OR severity="warning", "Warning",\n'
            '    alert_count>0, "Informational",\n'
            '    1=1, "Healthy")\n'
            '| sort - alert_count'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input "
            "(sourcetype=meraki:assurancealerts, hourly). Optional: Wireless Packet Loss by "
            "Device input for a numeric loss-based score."
        ),
        "implementation": (
            "1. Enable the Assurance Alerts input in Splunk_TA_cisco_meraki. 2. The TA polls "
            "GET /organizations/{orgId}/assurance/alerts hourly and emits one event per "
            "open alert with deviceType, deviceSerial, categoryType, title, severity, "
            "dismissedAt. 3. Filter to deviceType=wireless for AP-specific issues. 4. Meraki "
            "does not expose a numeric health score per AP via the API; counting open "
            "alerts and grading by severity is the closest workable approximation. "
            "5. Pair with the Wireless Packet Loss by Device input for a continuous loss-based "
            "health metric."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.25.json": {
        "spl": (
            'index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")\n'
            '    alertType="client_connectivity"\n'
            '    earliest=-7d\n'
            '| spath\n'
            '| eval client_mac = coalesce(\'alertData.clientMac\', \'alertData.client.mac\')\n'
            '| where isnotnull(client_mac)\n'
            '| timechart span=1h dc(client_mac) as concurrent_clients by deviceName limit=20'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver "
            "(sourcetype=meraki:webhook) with 'client connection changed' alerts. The polled "
            "Dashboard API only returns the top 10 clients by usage; full client trending "
            "requires webhook ingestion."
        ),
        "implementation": (
            "1. Enable the Webhook Logs (HEC) input and 'client connection changed' alert "
            "profile in Meraki Dashboard. 2. Use dc(alertData.clientMac) over a sliding hour "
            "for concurrent client count per AP. 3. For coarse top-talker visibility, the "
            "polled Summary Top Clients by Usage input (meraki:summarytopclientsbyusage) "
            "returns the org's top 10. 4. AP capacity limits depend on model (typical recent "
            "Wi-Fi 6 MR45/55/56 supports 200+ clients; older MR33 ~100); set capacity_pct "
            "thresholds per model class."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.27.json": {
        "spl": (
            'index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")\n'
            '    (alertType="client_connectivity" OR alertTypeId="client_connection_changed")\n'
            '    earliest=-24h\n'
            '| spath\n'
            '| eval client_mac = coalesce(\'alertData.clientMac\', \'alertData.client.mac\')\n'
            '| eval connect_state = \'alertData.status\'\n'
            '| where isnotnull(client_mac)\n'
            '| transaction client_mac startswith=eval(connect_state="connected") endswith=eval(connect_state="disconnected") maxspan=24h\n'
            '| eval session_minutes = round(duration/60, 1)\n'
            '| stats avg(session_minutes) as avg_session_min,\n'
            '        median(session_minutes) as median_session_min,\n'
            '        max(session_minutes) as max_session_min,\n'
            '        count as session_count\n'
            '         by deviceName, networkName'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver "
            "(sourcetype=meraki:webhook) with 'client connection changed' alerts. The TA's "
            "polled inputs do not return per-client connect/disconnect timestamps."
        ),
        "implementation": (
            "1. Enable the Webhook Logs (HEC) input and the Meraki Dashboard alert profile "
            "'client connection changed'. 2. Use the SPL transaction command to pair connect "
            "and disconnect events on the same client MAC; the duration field is the session "
            "length in seconds. 3. Tune maxspan to your typical session length (24h is "
            "generous; reduce to 4h for retail/guest WLAN). 4. Persistent disconnects under "
            "60 seconds suggest band-steering loops or sticky-client problems — investigate "
            "the involved AP."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.28.json": {
        "spl": (
            'index=meraki sourcetype="meraki:devicesavailabilities" productType="wireless" earliest=-1h\n'
            '| stats latest(status) as ap_status,\n'
            '        latest(_time) as last_seen\n'
            '         by serial, name, network.name, network.id, mac\n'
            '| where ap_status != "online"\n'
            '| eval offline_minutes = round((now() - last_seen)/60, 0)\n'
            '| sort - offline_minutes'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities input "
            "(sourcetype=meraki:devicesavailabilities, daily, TA v3.3+) and Devices "
            "Availabilities Change History input (sourcetype=meraki:devicesavailabilitieschangehistory, "
            "hourly) for AP transition events."
        ),
        "implementation": (
            "1. Enable both Devices Availabilities and Devices Availabilities Change History "
            "inputs in Splunk_TA_cisco_meraki. 2. The Availabilities input returns one event "
            "per device with status (online/offline/dormant/alerting), productType, serial, "
            "mac, network.{id,name}. 3. Filter productType=wireless for MR APs. 4. For "
            "transition history (when each AP last went offline) join against "
            "meraki:devicesavailabilitieschangehistory which carries previousStatus, status, "
            "and details on each event."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.29.json": {
        "spl": (
            'index=meraki sourcetype="meraki:assurancealerts"\n'
            '    deviceType="wireless"\n'
            '    (title="*mesh*" OR title="*backhaul*" OR title="*repeater*"\n'
            '     OR categoryType="connectivity")\n'
            '    earliest=-24h\n'
            '| stats count as alert_count,\n'
            '        values(title) as mesh_alerts,\n'
            '        latest(severity) as severity\n'
            '         by deviceSerial, deviceName, networkName\n'
            '| sort - alert_count'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input "
            "(sourcetype=meraki:assurancealerts). NOTE: per-mesh-link RSSI and bandwidth metrics "
            "are NOT exposed by the polled Dashboard API; mesh health is inferred from "
            "wireless connectivity alerts and (where available) the Wireless Devices Ethernet "
            "Statuses input which reports backhaul Ethernet status."
        ),
        "implementation": (
            "1. Enable the Assurance Alerts input. Mesh / repeater / backhaul issues surface "
            "as wireless device alerts in the assurance feed. 2. Optionally enable the "
            "Wireless Devices Ethernet Statuses input (sourcetype=meraki:wirelessdevicesethernetstatuses) "
            "which reports per-AP Ethernet link speed, duplex, aggregation, and PoE status — "
            "useful for distinguishing wired vs mesh-uplinked APs. 3. For deeper visibility "
            "(per-mesh-link RSSI/bandwidth) use the Meraki Dashboard Wireless -> Mesh page or "
            "scrape its API endpoint with a custom modular input."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.30.json": {
        "spl": (
            'index=meraki sourcetype IN ("meraki:webhook","meraki:webhooklogs:api")\n'
            '    alertType="client_connectivity"\n'
            '    earliest=-7d\n'
            '| spath\n'
            '| eval client_mac = coalesce(\'alertData.clientMac\', \'alertData.client.mac\')\n'
            '| eval ssid = coalesce(\'alertData.ssid\', \'alertData.ssidName\')\n'
            '| where isnotnull(client_mac) AND like(lower(ssid), "%guest%")\n'
            '| timechart span=1h dc(client_mac) as guest_clients by ssid limit=10'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Webhook receiver "
            "(sourcetype=meraki:webhook) with 'client connection changed' alerts. SSID name is "
            "in alertData.ssid on the webhook payload."
        ),
        "implementation": (
            "1. Enable the Webhook Logs (HEC) input and the 'client connection changed' alert "
            "profile in Meraki Dashboard. 2. Filter on SSID names containing 'guest' (adjust "
            "to your naming convention). 3. dc(client_mac) per hour gives concurrent guest "
            "users. 4. For top-talker bandwidth on the guest SSID, use the Summary Top Clients "
            "by Usage input (meraki:summarytopclientsbyusage) and join on client.mac."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.31.json": {
        "spl": (
            'index=meraki sourcetype="meraki:devices" productType="wireless"\n'
            '| stats latest(name) as ap_name,\n'
            '        latest(model) as model,\n'
            '        latest(lat) as latitude,\n'
            '        latest(lng) as longitude,\n'
            '        latest(address) as address,\n'
            '        latest(network.name) as network_name,\n'
            '        latest(floorPlanId) as floor_plan_id\n'
            '         by serial\n'
            '| where isnotnull(latitude) AND isnotnull(longitude)\n'
            '| geom geo_us_states featureIdField="state"\n'
            '| table serial ap_name model network_name address latitude longitude floor_plan_id'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Devices input (sourcetype=meraki:devices) "
            "for AP location metadata (lat, lng, address, floorPlanId). NOTE: client-level "
            "indoor location analytics (Meraki Location API / Bluetooth scanning) is NOT "
            "exposed by this TA — for that, install Cisco Spaces and the Cisco Spaces Add-on "
            "(Splunkbase #8485)."
        ),
        "implementation": (
            "1. In Meraki Dashboard, set the lat/lng/address fields for each MR AP under "
            "Wireless -> Access points -> AP details. 2. Enable the Devices input in "
            "Splunk_TA_cisco_meraki and confirm those fields populate. 3. Use the geom command "
            "to render APs on a Choropleth or marker map. 4. For client indoor positioning and "
            "footfall analytics deploy Cisco Spaces and ingest its Location API output via the "
            "Cisco Spaces Add-on (sourcetype=cisco:spaces:location)."
        ),
    },

    # =========================================================================
    # DHCP / IP MGMT
    # =========================================================================

    "content/cat-05-network-infrastructure/UC-5.6.15.json": {
        "spl": (
            'index=meraki sourcetype IN ("meraki","cisco:meraki") (type=events OR type=flows)\n'
            '    (DHCP_NACK OR DHCP_lease_alert OR pool_exhausted OR "no leases available")\n'
            '    earliest=-24h\n'
            '| stats count as nack_count,\n'
            '        values(message) as messages,\n'
            '        latest(_time) as last_seen\n'
            '         by host, network_name, pool, vlan\n'
            '| where nack_count > 0\n'
            '| sort - nack_count\n'
            '| append [\n'
            '    search index=meraki sourcetype="meraki:assurancealerts"\n'
            '        (title="*DHCP*" OR categoryType="appliance") earliest=-24h\n'
            '    | stats count by deviceSerial, networkName, title\n'
            '  ]'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki, type=events) for syslog-side DHCP "
            "messages from the MX, plus Splunk_TA_cisco_meraki Assurance Alerts input "
            "(sourcetype=meraki:assurancealerts) for DHCP-related Dashboard alerts. NOTE: "
            "live DHCP pool size and remaining-lease counters are NOT exposed by either path; "
            "monitoring relies on NAK/exhaustion event detection."
        ),
        "implementation": (
            "1. Configure Splunk Connect for Syslog (SC4S) to receive Meraki MX syslog over "
            "UDP/514 and forward to the meraki index. 2. In Meraki Dashboard enable syslog "
            "category 'Flows' and 'Events' (Network-wide -> General -> Reporting). 3. DHCP NAK "
            "and pool-exhaustion messages match type=events. 4. Also enable the Assurance "
            "Alerts input in Splunk_TA_cisco_meraki and create alert profiles in Meraki "
            "Dashboard for 'DHCP scope exhausted' and 'DHCP server failure'. 5. For proactive "
            "pool-size visibility you must scrape "
            "GET /networks/{networkId}/appliance/vlans (returns each VLAN's reservation/exclusion "
            "ranges) with a custom modular input — that endpoint is not yet polled by the TA."
        ),
    },

    # =========================================================================
    # ORG / DASHBOARD UCs
    # =========================================================================

    "content/cat-05-network-infrastructure/UC-5.8.2.json": {
        "spl": (
            'index=meraki sourcetype="meraki:devicesavailabilities" earliest=-1h\n'
            '| stats count as device_count,\n'
            '        sum(eval(if(status="online",1,0))) as online_count,\n'
            '        sum(eval(if(status="offline",1,0))) as offline_count,\n'
            '        sum(eval(if(status="alerting",1,0))) as alerting_count\n'
            '         by network.id, network.name\n'
            '| eval pct_online = round(online_count*100/device_count, 1)\n'
            '| where offline_count > 0 OR alerting_count > 0\n'
            '| sort pct_online'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities input "
            "(sourcetype=meraki:devicesavailabilities, daily, TA v3.3+) and Organization "
            "Networks input (sourcetype=meraki:organizationsnetworks, daily) for network "
            "metadata."
        ),
        "implementation": (
            "1. Enable Devices Availabilities and Organization Networks inputs in "
            "Splunk_TA_cisco_meraki. The Availabilities input returns one event per device "
            "with status (online/offline/dormant/alerting), productType, network.{id,name}. "
            "2. Aggregate per network for a per-site availability dashboard. 3. For multi-org "
            "consolidation, configure one Organization input per Meraki tenancy and tag events "
            "with the org name; the TA's input wizard prompts for org name when adding."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.8.9.json": {
        "spl": (
            'index=meraki sourcetype="meraki:assurancealerts"\n'
            '    (title="*certificate*" OR title="*TLS*" OR title="*SSL*"\n'
            '     OR title="*expir*")\n'
            '    earliest=-7d\n'
            '| stats count as alert_count,\n'
            '        values(title) as cert_alerts,\n'
            '        latest(severity) as severity\n'
            '         by deviceSerial, deviceName, networkName\n'
            '| sort - alert_count'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input "
            "(sourcetype=meraki:assurancealerts). NOTE: the Meraki Dashboard API does NOT "
            "expose certificate validity dates for managed devices; the only signal available "
            "is the assurance-alert feed when a certificate-related issue is detected. For "
            "branch firewalls hosting public services, monitor your CA portal (Let's Encrypt, "
            "Sectigo, DigiCert) directly or use a TLS scanner like ssl-checker / Splunk Sslscan TA."
        ),
        "implementation": (
            "1. Enable the Assurance Alerts input in Splunk_TA_cisco_meraki. 2. Filter alert "
            "titles for certificate / TLS / SSL / expiry keywords. 3. For proactive monitoring "
            "deploy a TLS expiry scanner (e.g. the Splunk Sslscan TA or a custom curl + openssl "
            "modular input) against your branch endpoints, and trigger a Splunk alert ~30 days "
            "before expiry."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.8.10.json": {
        "spl": (
            'index=meraki sourcetype="meraki:devices" earliest=-1h\n'
            '| stats latest(firmware) as current_fw,\n'
            '        dc(serial) as device_count,\n'
            '        values(network.name) as networks\n'
            '         by productType, model\n'
            '| join type=left model [\n'
            '    | inputlookup recommended_meraki_firmware.csv\n'
            '    | rename target_firmware as recommended_fw\n'
            '  ]\n'
            '| eval compliant = if(current_fw==recommended_fw, "Yes", "No")\n'
            '| where compliant="No" OR isnull(recommended_fw)\n'
            '| sort productType model'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Devices input (sourcetype=meraki:devices) "
            "for current firmware version per device, and Firmware Upgrades input "
            "(sourcetype=meraki:firmwareupgrades, daily) for upgrade history. The "
            "recommended_meraki_firmware.csv is a customer-maintained lookup; populate it "
            "with the firmware version Meraki currently recommends per model."
        ),
        "implementation": (
            "1. Enable the Devices and Firmware Upgrades inputs in Splunk_TA_cisco_meraki. "
            "The Devices input emits one event per device with the firmware field already "
            "populated (e.g. 'wireless-29-7'). 2. Create a lookup file recommended_meraki_firmware.csv "
            "with columns (model, target_firmware) reflecting the Meraki Dashboard "
            "recommendations under Organization -> Firmware upgrades. 3. The TA reads the "
            "Firmware Upgrades input from GET /organizations/{orgId}/firmware/upgrades and "
            "carries upgrade.toVersion.shortName for each scheduled upgrade — pair with the "
            "Devices output to detect drift after a wave."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.8.12.json": {
        "spl": (
            'index=meraki sourcetype="meraki:licensesoverview" earliest=-1d\n'
            '| stats latest(licensedDeviceCounts) as licensed_counts,\n'
            '        latest(expirationDate) as expiry_iso,\n'
            '        latest(status) as license_status\n'
            '         by organizationId, organizationName\n'
            '| eval days_until_expire = round((strptime(expiry_iso,"%Y-%m-%dT%H:%M:%SZ") - now())/86400, 0)\n'
            '| where days_until_expire <= 90\n'
            '| append [\n'
            '    search index=meraki sourcetype="meraki:licensescotermlicenses" earliest=-1d\n'
            '    | stats latest(claimDate) as claimed,\n'
            '            latest(expirationDate) as expiry_iso,\n'
            '            latest(licenseType) as license_type,\n'
            '            latest(state) as state\n'
            '             by licenseKey, organizationId\n'
            '    | eval days_until_expire = round((strptime(expiry_iso,"%Y-%m-%dT%H:%M:%SZ") - now())/86400, 0)\n'
            '    | where days_until_expire <= 90\n'
            '  ]\n'
            '| sort days_until_expire'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Licenses Overview input "
            "(sourcetype=meraki:licensesoverview, daily) for org-level license summary, and "
            "Licenses Coterm Licenses input (sourcetype=meraki:licensescotermlicenses, daily) "
            "for per-key co-term license detail. OAuth scope dashboard:licensing:config:read."
        ),
        "implementation": (
            "1. Enable both Licenses Overview and Licenses Coterm Licenses inputs (TA v3+). "
            "Licenses Overview returns the org-wide expirationDate and status; Licenses "
            "Coterm Licenses returns one event per individual license key with claimDate, "
            "expirationDate, licenseType, state. 2. Compute days-until-expire from the ISO-8601 "
            "expirationDate. 3. Trigger Splunk alerts at 90 days, 60 days, and 30 days before "
            "expiry. 4. For PDL (Per-Device Licensing) tenancies, also enable the Licenses "
            "Subscriptions input (meraki:licensessubscriptions)."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.8.13.json": {
        "spl": (
            'index=meraki sourcetype="meraki:devices" earliest=-1d\n'
            '| stats dc(serial) as inventory_count\n'
            '         by productType, model, network.name\n'
            '| append [\n'
            '    search index=meraki sourcetype="meraki:audit" earliest=-7d\n'
            '        (action="add" OR action="remove" OR action="update")\n'
            '    | stats count as change_events,\n'
            '            values(adminName) as changed_by,\n'
            '            values(label) as targets\n'
            '             by networkName, page\n'
            '    | sort - change_events\n'
            '  ]\n'
            '| sort productType model'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Devices input "
            "(sourcetype=meraki:devices) for inventory, and Audit input (sourcetype=meraki:audit, "
            "daily) for organization configuration changes."
        ),
        "implementation": (
            "1. Enable the Devices and Audit inputs in Splunk_TA_cisco_meraki. 2. The Devices "
            "input gives current inventory grouped by productType (wireless/switch/appliance/"
            "camera/sensor/cellularGateway) and model. 3. The Audit input emits one event per "
            "configuration change with adminName, page, label, action (add/remove/update), "
            "networkName, ts. 4. To detect device additions/removals specifically, filter "
            "page='Inventory' or page='Devices'. 5. Schedule a daily report comparing current "
            "inventory against the previous snapshot stored in a summary index for delta "
            "tracking."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.8.17.json": {
        "spl": (
            'index=meraki sourcetype="meraki:devicesavailabilities" earliest=-1h\n'
            '| stats count as device_count,\n'
            '        sum(eval(if(status="online",1,0))) as online_count,\n'
            '        sum(eval(if(status="alerting",1,0))) as alerting_count,\n'
            '        sum(eval(if(status="offline",1,0))) as offline_count\n'
            '         by network.id, network.name\n'
            '| eval availability_pct = round(online_count*100/device_count, 1)\n'
            '| join type=left network.id [\n'
            '    search index=meraki sourcetype="meraki:assurancealerts" earliest=-24h\n'
            '    | stats count as open_alerts by networkId\n'
            '    | rename networkId as "network.id"\n'
            '  ]\n'
            '| fillnull value=0 open_alerts\n'
            '| eval network_health = round(availability_pct - (open_alerts*0.5), 1)\n'
            '| sort network_health'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities input "
            "(sourcetype=meraki:devicesavailabilities) and Assurance Alerts input "
            "(sourcetype=meraki:assurancealerts). NOTE: the Meraki Dashboard API does NOT "
            "expose a single numeric 'health score' per device or network; this UC composes "
            "one from availability % and open-alert count."
        ),
        "implementation": (
            "1. Enable Devices Availabilities and Assurance Alerts inputs in Splunk_TA_cisco_meraki. "
            "2. Compute availability_pct as online/total per network. 3. Subtract 0.5 per "
            "open alert to penalise networks with active issues. 4. Tune the weighting and "
            "tier the result into Critical/Warning/OK bands for an executive view."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.8.18.json": {
        "spl": (
            'index=meraki sourcetype="meraki:devicesavailabilities" earliest=-1h\n'
            '| stats latest(status) as device_status,\n'
            '        latest(_time) as last_status_check,\n'
            '        latest(productType) as product_type\n'
            '         by serial, name, network.id, network.name\n'
            '| where device_status != "online"\n'
            '| join type=left serial [\n'
            '    search index=meraki sourcetype="meraki:devicesavailabilitieschangehistory" earliest=-24h\n'
            '    | stats latest(_time) as last_change_time,\n'
            '            latest(status) as new_status,\n'
            '            latest(previousStatus) as prev_status\n'
            '             by serial\n'
            '  ]\n'
            '| eval offline_minutes = round((now() - coalesce(last_change_time, last_status_check))/60, 0)\n'
            '| sort - offline_minutes'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities input "
            "(sourcetype=meraki:devicesavailabilities, daily, TA v3.3+) and Devices "
            "Availabilities Change History input (sourcetype=meraki:devicesavailabilitieschangehistory, "
            "hourly) for transition timestamps."
        ),
        "implementation": (
            "1. Enable Devices Availabilities and Devices Availabilities Change History inputs "
            "(both in TA v3.3+). 2. The Availabilities input gives current state; the Change "
            "History input lists every status transition (online -> offline -> online ...) with "
            "previousStatus, status, and ts. 3. Joining the two lets you report on each "
            "currently-down device along with how long it has been down. 4. For paging-grade "
            "alerting, configure a Meraki Dashboard alert profile on 'device offline for X "
            "minutes' and ingest via the Webhook Logs (HEC) input."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.8.19.json": {
        "spl": (
            'index=meraki sourcetype="meraki:devicesavailabilities" earliest=-1h\n'
            '| stats count as device_count,\n'
            '        sum(eval(if(status="online",1,0))) as online_count,\n'
            '        sum(eval(if(status="alerting",1,0))) as alerting_count\n'
            '         by organizationId, organizationName\n'
            '| eval availability_pct = round(online_count*100/device_count, 2)\n'
            '| join type=left organizationId [\n'
            '    search index=meraki sourcetype="meraki:assurancealerts" earliest=-24h\n'
            '    | stats count as open_alerts by organizationId\n'
            '  ]\n'
            '| fillnull value=0 open_alerts\n'
            '| eval alerts_per_device = round(open_alerts/device_count, 2)\n'
            '| sort - availability_pct'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities and Assurance "
            "Alerts inputs configured for each organization tenancy you want to compare. "
            "NOTE: configure one TA Organization entry per tenancy; events are stamped with "
            "organizationId and organizationName."
        ),
        "implementation": (
            "1. In Splunk_TA_cisco_meraki -> Configuration -> Organization, add one entry per "
            "Meraki tenancy you want to benchmark. 2. Enable the same set of inputs (Devices "
            "Availabilities + Assurance Alerts) in each. 3. Group by organizationName for "
            "side-by-side comparison. 4. For per-product-type drill-down, add productType to "
            "the stats by clause."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.8.23.json": {
        "spl": (
            'index=meraki sourcetype="meraki:audit" earliest=-30d\n'
            '    (page="Backup" OR label="*backup*" OR action="*backup*"\n'
            '     OR page="Configuration sync" OR label="*export*")\n'
            '| stats latest(_time) as last_action,\n'
            '        values(adminName) as performed_by,\n'
            '        values(label) as actions\n'
            '         by organizationName, networkName\n'
            '| eval days_since_last = round((now() - last_action)/86400, 0)\n'
            '| where isnull(last_action) OR days_since_last > 30\n'
            '| sort - days_since_last'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Audit input (sourcetype=meraki:audit, "
            "daily). NOTE: the Meraki Dashboard does not provide a native 'config backup' "
            "API endpoint; backups are typically performed by exporting "
            "GET /networks/{networkId}/configTemplates and per-product config endpoints "
            "via a custom script. The audit log records when an admin performs these actions."
        ),
        "implementation": (
            "1. Enable the Audit input in Splunk_TA_cisco_meraki. 2. Filter audit entries for "
            "configuration export / template backup activity. 3. The query identifies "
            "organizations or networks where no backup-related admin action has happened in "
            "the last 30 days. 4. For an automated backup, run a scheduled script that calls "
            "GET /networks/{networkId}/appliance/firewall/l3FirewallRules, "
            "/wireless/ssids, /switch/accessPolicies etc. and stores the output in version "
            "control. The Audit input gives you visibility into manual exports performed via "
            "the Meraki Dashboard UI."
        ),
    },

    # =========================================================================
    # CROSS-PLATFORM HEALTH DASHBOARDS
    # =========================================================================

    "content/cat-05-network-infrastructure/UC-5.13.70.json": {
        "spl": (
            'index=catalyst sourcetype="cisco:dnac:networkhealth"\n'
            '| stats latest(healthScore) as campus_health by _time\n'
            '| appendcols [\n'
            '    search index=meraki sourcetype="meraki:devicesavailabilities" earliest=-1h\n'
            '    | stats sum(eval(if(status="online",1,0))) as online,\n'
            '            count as total\n'
            '    | eval branch_availability = round(online*100/total, 1)\n'
            '  ]\n'
            '| appendcols [\n'
            '    search index=meraki sourcetype="meraki:assurancealerts" earliest=-24h\n'
            '    | stats count as branch_open_alerts\n'
            '  ]\n'
            '| eval branch_health = round(branch_availability - (branch_open_alerts*0.5), 1)\n'
            '| eval combined_health = round((campus_health + branch_health) / 2, 1)\n'
            '| table _time, campus_health, branch_availability, branch_open_alerts, branch_health, combined_health'
        ),
        "dataSources": (
            "Cisco DNA Center for Splunk app (sourcetype=cisco:dnac:networkhealth) for the "
            "campus side, plus Splunk_TA_cisco_meraki Devices Availabilities + Assurance "
            "Alerts inputs for the Meraki branch side. NOTE: Meraki does not expose a single "
            "numeric 'branch health score'; this UC composes one from device availability % "
            "and open-alert count."
        ),
        "implementation": (
            "1. Confirm the Cisco DNA Center add-on is ingesting cisco:dnac:networkhealth "
            "with healthScore. 2. Enable Devices Availabilities and Assurance Alerts inputs "
            "in Splunk_TA_cisco_meraki. 3. The composed branch_health = availability% - "
            "(open_alerts * 0.5). 4. combined_health is the average of the two. Tune weights "
            "to your reporting preference and present in a single executive dashboard."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.13.73.json": {
        "spl": (
            'index=catalyst sourcetype="cisco:dnac:networkhealth"\n'
            '| stats latest(healthScore) as campus_health\n'
            '| appendcols [\n'
            '    search index=sdwan sourcetype="cisco:sdwan:*"\n'
            '    | stats latest(health_score) as wan_health\n'
            '  ]\n'
            '| appendcols [\n'
            '    search index=meraki sourcetype="meraki:devicesavailabilities" earliest=-1h\n'
            '    | stats sum(eval(if(status="online",1,0))) as online,\n'
            '            count as total\n'
            '    | eval branch_health = round(online*100/total, 1)\n'
            '  ]\n'
            '| appendcols [\n'
            '    search index=meraki sourcetype="meraki:assurancealerts" earliest=-24h\n'
            '    | stats count as branch_alerts\n'
            '  ]\n'
            '| eval branch_health = round(branch_health - (branch_alerts*0.3), 1)\n'
            '| eval enterprise_health = round((campus_health + wan_health + branch_health) / 3, 1)\n'
            '| table campus_health, wan_health, branch_health, branch_alerts, enterprise_health'
        ),
        "dataSources": (
            "Cisco DNA Center add-on (sourcetype=cisco:dnac:networkhealth), Cisco SD-WAN "
            "add-on (sourcetype=cisco:sdwan:*), and Splunk_TA_cisco_meraki Devices "
            "Availabilities + Assurance Alerts inputs. The Meraki branch tier composes a "
            "synthetic health score from availability % minus (open_alerts * 0.3)."
        ),
        "implementation": (
            "1. Verify all three source pipelines are populated: cisco:dnac:networkhealth "
            "(campus), cisco:sdwan:* (WAN), and meraki:devicesavailabilities + "
            "meraki:assurancealerts (branch). 2. Compose the Meraki branch_health from "
            "availability % minus a 0.3 weight per open alert. 3. enterprise_health is the "
            "simple average of campus / WAN / branch. 4. Render as a single-value tile per "
            "tier plus a combined gauge."
        ),
    },

    # =========================================================================
    # CAMERAS - 15.3.28 firmware compliance still uses meraki:devices
    # =========================================================================

    "content/cat-15-data-center-physical-infrastructure/UC-15.3.28.json": {
        "spl": (
            'index=meraki sourcetype="meraki:devices" productType="camera" earliest=-1h\n'
            '| stats latest(firmware) as current_fw,\n'
            '        latest(name) as camera_name,\n'
            '        latest(network.name) as network_name\n'
            '         by serial, model\n'
            '| join type=left model [\n'
            '    | inputlookup recommended_camera_fw.csv\n'
            '    | rename target_firmware as recommended_fw\n'
            '  ]\n'
            '| eval compliant = if(current_fw==recommended_fw, "Yes", "No")\n'
            '| append [\n'
            '    search index=meraki sourcetype="meraki:firmwareupgrades" earliest=-30d\n'
            '        (productType="camera" OR product="camera")\n'
            '    | stats values(upgrade.toVersion.shortName) as scheduled_fw,\n'
            '            latest(upgrade.time) as scheduled_time\n'
            '             by upgrade.toVersion.shortName, productType\n'
            '  ]\n'
            '| where compliant="No" OR isnotnull(scheduled_fw)\n'
            '| sort model'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Devices input (sourcetype=meraki:devices) "
            "filtered to productType=camera, plus Firmware Upgrades input "
            "(sourcetype=meraki:firmwareupgrades, daily) for scheduled / completed upgrades. "
            "The recommended_camera_fw.csv is a customer-maintained lookup with columns "
            "(model, target_firmware) reflecting Meraki Dashboard recommendations under "
            "Organization -> Firmware upgrades."
        ),
        "implementation": (
            "1. Enable the Devices and Firmware Upgrades inputs in Splunk_TA_cisco_meraki. "
            "The Devices input emits one event per camera with productType=camera, model, "
            "firmware (e.g. 'camera-4-13'). 2. The Firmware Upgrades input polls "
            "GET /organizations/{orgId}/firmware/upgrades and includes upgrade.toVersion.shortName, "
            "upgrade.time, productType for each scheduled or completed upgrade. 3. Maintain "
            "recommended_camera_fw.csv with the Meraki-recommended firmware per camera model "
            "(MV2, MV12, MV13, MV21, MV22, MV32, MV52, MV63, MV72 ...). 4. Trigger a Splunk "
            "alert on every camera whose current_fw drifts from recommended_fw."
        ),
    },
}


def update_uc(path: Path, overrides: dict[str, str]) -> bool:
    """Apply overrides to a single UC JSON file. Returns True if file changed."""
    raw = path.read_text(encoding="utf-8")
    uc = json.loads(raw)
    changed = False
    for field, new_value in overrides.items():
        if uc.get(field) != new_value:
            uc[field] = new_value
            changed = True
    if not changed:
        return False
    new_text = json.dumps(uc, indent=2, ensure_ascii=False) + "\n"
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    updated = 0
    skipped = 0
    missing = 0
    for rel, overrides in REWRITES.items():
        path = REPO / rel
        if not path.exists():
            print(f"  MISSING: {rel}")
            missing += 1
            continue
        try:
            if update_uc(path, overrides):
                print(f"  updated: {rel}")
                updated += 1
            else:
                print(f"  no-op:   {rel}")
                skipped += 1
        except json.JSONDecodeError as exc:
            print(f"  ERROR:   {rel} — {exc}")
            missing += 1
    print()
    print(f"Updated: {updated} | Unchanged: {skipped} | Missing/Error: {missing}")
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
