#!/usr/bin/env python3
"""Rewrite Meraki SC4S-syslog UCs that hallucinate types and field names.

Audit findings against the canonical Meraki syslog reference
(documentation.meraki.com/General_Administration/Monitoring_and_Reporting/
Syslog_Event_Types_and_Log_Samples) and the SC4S Meraki vendor pack:

1. ``type=security_event`` is ONLY emitted by Meraki MX appliances for AMP /
   anti-malware events (with `name=`, `sha256=`, `disposition=`, `action=`).
   It is NOT used for switch (MS), wireless (MR), or generic appliance
   events. Many UCs incorrectly use it for STP changes, port flap,
   cellular failover, association failures, etc. — those should be
   ``type=events``.

2. ``signature=`` is ONLY emitted on ``type=ids-alerts`` (and AMP
   ``type=security_event``). Switch / wireless / appliance events use
   structured ``type=<subkind>`` markers and message-body keywords. UCs
   filtering on ``signature="*STP*"``, ``signature="*Port Security*"``,
   ``signature="*VLAN*"`` etc. for MS/MR events are hallucinated.

3. Several premises don't map to any Meraki syslog signal at all
   (DLP, BGP peering on MX, cable diagnostics, switch QoS queue
   counters, DNS resolution time). For those we pivot to the closest
   workable signal (Assurance Alerts via the API) and call out the
   limitation in the implementation field.

4. Admin activity / config changes / privilege escalation are NOT in
   Meraki syslog — they are only available via the Audit input
   (``meraki:audit``) of Splunk_TA_cisco_meraki. UCs 5.8.14 / 5.8.15 /
   5.8.20 are repointed accordingly.

Usage:
    PYTHONPATH=src python3 scripts/rewrite_meraki_sc4s_misuse.py
    PYTHONPATH=src python3 scripts/regen_di_for_ucs.py --meraki-sc4s-fix
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

REWRITES: dict[str, dict[str, str]] = {

    # =========================================================================
    # SWITCH (MS) SC4S syslog — type=events is correct, signature= is hallucinated
    # =========================================================================

    "content/cat-05-network-infrastructure/UC-5.1.38.json": {
        "spl": (
            'index=meraki sourcetype="meraki" type=events\n'
            '    ("STP" OR "spanning-tree" OR "STP role" OR "STP BPDU")\n'
            '    earliest=-24h\n'
            '| rex "Port (?<port_id>\\d+) (?:received|changed STP role from (?<from_role>\\S+) to (?<to_role>\\S+))"\n'
            '| stats count as change_count,\n'
            '        values(from_role) as from_roles,\n'
            '        values(to_role) as to_roles\n'
            '         by host, port_id\n'
            '| where change_count > 3\n'
            '| sort - change_count'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki) receiving Meraki MS switch syslog. "
            "STP events are emitted as type=events with message bodies like "
            "'Port 5 received an STP BPDU from <mac> so the port was blocked' and "
            "'Port 5 changed STP role from designated to alternate'. Use rex to extract "
            "port_id and the role transition."
        ),
        "implementation": (
            "1. Configure SC4S to receive Meraki MS syslog on UDP/514 (or a dedicated port "
            "per https://splunk.github.io/splunk-connect-for-syslog/main/sources/vendor/Cisco/"
            "cisco_meraki/). 2. In Meraki Dashboard go to Network-wide -> General -> Reporting "
            "and add the SC4S syslog server with role 'Switch event log'. 3. STP topology "
            "changes appear as type=events with 'STP', 'STP BPDU', 'STP role' in the body. "
            "4. Use rex to extract port_id and role; threshold count > 3 in 24h to alert on "
            "unstable spanning-tree topologies."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.1.39.json": {
        "spl": (
            'index=meraki sourcetype="meraki" type=events\n'
            '    (type=8021x_eap_failure OR type=8021x_deauth\n'
            '     OR "Blocked DHCP server response"\n'
            '     OR "MAC flooding" OR "unauthorized")\n'
            '    earliest=-24h\n'
            '| rex "port[=\\\']?(?<port_id>[\\d]+)"\n'
            '| rex "(?<violation_type>8021x_eap_failure|8021x_deauth|Blocked DHCP|unauthorized)"\n'
            '| stats count as violation_count,\n'
            '        values(violation_type) as types,\n'
            '        values(identity) as identities\n'
            '         by host, port_id\n'
            '| where violation_count > 0\n'
            '| sort - violation_count'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki) receiving Meraki MS switch syslog. "
            "NOTE: Meraki MS does NOT have classic IOS-style 'port-security' (sticky MAC, "
            "max-mac, violation modes); the closest Meraki signals are 802.1X authentication "
            "failures (type=8021x_eap_failure / 8021x_deauth) and 'Blocked DHCP server "
            "response from <mac> on VLAN <id>' messages emitted by the DHCP guard feature."
        ),
        "implementation": (
            "1. Configure SC4S for Meraki MS syslog and enable Switch event log in Meraki "
            "Dashboard. 2. Filter on 802.1X failure events and DHCP guard blocks — the two "
            "real syslog signals analogous to IOS port-security violations. 3. The TA-meraki "
            "(Splunkbase #3018) extracts the type=, port=, identity= fields directly from "
            "the structured key=value payload. 4. For sticky-MAC behaviour, use Meraki "
            "Dashboard -> Switch -> Access policies (port-based dot1x) instead — there is "
            "no Cisco IOS-style port-security on Meraki."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.1.40.json": {
        "spl": (
            'index=meraki sourcetype="meraki" type=events "port" "status changed"\n'
            '    earliest=-24h\n'
            '| rex "port (?<port_id>\\d+) status changed from (?<from_state>[\\w\\.]+) to (?<to_state>[\\w\\.]+)"\n'
            '| stats count as event_count,\n'
            '        dc(eval(if(to_state="down",1,null()))) as down_events,\n'
            '        values(from_state) as from_states,\n'
            '        values(to_state) as to_states\n'
            '         by host, port_id\n'
            '| eval flap_rate = round(event_count/24, 2)\n'
            '| where flap_rate > 1\n'
            '| sort - flap_rate'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki) receiving Meraki MS switch syslog. "
            "Port up/down events appear as type=events with message body "
            "'port 3 status changed from 100fdx to down' / 'from down to 100fdx'. host field "
            "carries the switch name (e.g. MS220_8P)."
        ),
        "implementation": (
            "1. Configure SC4S for MS syslog. 2. Use rex to extract port_id, from_state, "
            "to_state from the standard port-status-change message. 3. Compute flap_rate per "
            "hour; > 1/h sustained over a day usually indicates cabling, transceiver, or "
            "negotiation issues. 4. Pair with the Meraki Dashboard 'switch port status "
            "changed' webhook alert profile (ingested via Splunk_TA_cisco_meraki Webhook Logs "
            "input) for live notification."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.1.41.json": {
        "spl": (
            'index=meraki sourcetype="meraki" type=events\n'
            '    ("VLAN" OR "vlan tag" OR "incompatible" OR "trunk")\n'
            '    earliest=-24h\n'
            '| rex "VLAN (?<vlan_id>\\d+)"\n'
            '| rex "port (?<port_id>\\d+)"\n'
            '| stats count as vlan_event_count,\n'
            '        values(vlan_id) as vlan_ids\n'
            '         by host, port_id\n'
            '| where vlan_event_count > 5\n'
            '| sort - vlan_event_count'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki) receiving Meraki MS switch syslog. "
            "VLAN-related messages appear as type=events. The 'Blocked DHCP server response "
            "from <mac> on VLAN <id>' message is one of the few VLAN-tagged events Meraki MS "
            "emits to syslog. NOTE: trunk/access mismatch detection is not natively logged; "
            "use Meraki Dashboard -> Switch -> Switch ports for static config inspection."
        ),
        "implementation": (
            "1. Configure SC4S for MS syslog. 2. Use rex to extract VLAN id and port id from "
            "the message body. 3. For comprehensive VLAN-config-drift detection use the Audit "
            "input (sourcetype=meraki:audit) and filter on page='Switch ports' or page='VLANs' "
            "to track admin changes. 4. Tune the threshold to your topology — high VLAN event "
            "counts on the same port are a signal of misconfigured trunk or rogue device."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.1.42.json": {
        "spl": (
            'index=meraki sourcetype="meraki:assurancealerts"\n'
            '    deviceType="switch"\n'
            '    (title="*MAC*" OR title="*flood*" OR title="*storm*"\n'
            '     OR categoryType="performance")\n'
            '    earliest=-24h\n'
            '| stats count as alert_count,\n'
            '        values(title) as alert_titles,\n'
            '        latest(severity) as severity\n'
            '         by deviceSerial, deviceName, networkName\n'
            '| sort - alert_count'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input "
            "(sourcetype=meraki:assurancealerts). NOTE: Meraki MS switches do NOT emit per-port "
            "MAC flooding or bridge-table-exhaustion events to syslog. The closest signal is the "
            "Assurance Alerts feed which fires on switch performance issues."
        ),
        "implementation": (
            "1. Enable the Assurance Alerts input in Splunk_TA_cisco_meraki (TA v3+, hourly "
            "polling of GET /organizations/{orgId}/assurance/alerts). 2. Filter to "
            "deviceType=switch with MAC/flood/storm keywords. 3. For deeper inspection use "
            "Meraki Dashboard -> Switch -> Switches -> [select switch] -> Tools -> MAC table "
            "to see live entries; the MAC table size is not exposed via API."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.1.43.json": {
        "spl": (
            'index=meraki sourcetype="meraki" type=events "Blocked DHCP server response"\n'
            '    earliest=-24h\n'
            '| rex "Blocked DHCP server response from (?<server_mac>[0-9A-Fa-f:]+) on VLAN (?<vlan_id>\\d+)"\n'
            '| stats count as block_count,\n'
            '        values(server_mac) as blocked_servers,\n'
            '        values(vlan_id) as vlans\n'
            '         by host\n'
            '| where block_count > 0\n'
            '| sort - block_count'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki) receiving Meraki MS switch syslog. "
            "Meraki MS DHCP guard emits messages of the form 'Blocked DHCP server response "
            "from <mac> on VLAN <id>' as type=events when an unauthorised DHCP server is "
            "detected on the access switch."
        ),
        "implementation": (
            "1. Configure SC4S for MS syslog and enable DHCP server response blocking in "
            "Meraki Dashboard -> Switch -> DHCP servers & ARP. 2. Use rex to extract the "
            "rogue DHCP server's MAC and the VLAN id. 3. Trigger an alert on every blocked "
            "DHCP response — these are real incidents and should be investigated immediately."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.1.44.json": {
        "spl": (
            'index=meraki sourcetype="meraki:assurancealerts"\n'
            '    deviceType="switch"\n'
            '    (title="*storm*" OR title="*broadcast*" OR title="*loop*"\n'
            '     OR categoryType="performance")\n'
            '    earliest=-24h\n'
            '| stats count as alert_count,\n'
            '        values(title) as alert_titles,\n'
            '        latest(severity) as severity\n'
            '         by deviceSerial, deviceName, networkName\n'
            '| sort - alert_count'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input "
            "(sourcetype=meraki:assurancealerts). NOTE: per-port broadcast packet counters are "
            "NOT exposed via syslog or the Dashboard API. Storm-control activations surface as "
            "switch alerts in the Assurance feed; for live broadcast counters use SNMP polling "
            "against the switch."
        ),
        "implementation": (
            "1. Enable the Assurance Alerts input. 2. Filter to deviceType=switch and "
            "storm/broadcast/loop keywords. 3. For continuous broadcast-rate visibility, deploy "
            "Splunk's SNMP modular input against each switch's management IP using IF-MIB "
            "ifInBroadcastPkts / ifOutBroadcastPkts counters."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.1.48.json": {
        "spl": (
            'index=meraki sourcetype="meraki:assurancealerts"\n'
            '    deviceType="switch"\n'
            '    (title="*queue*" OR title="*drop*" OR title="*QoS*"\n'
            '     OR title="*congest*")\n'
            '    earliest=-24h\n'
            '| stats count as alert_count,\n'
            '        values(title) as alert_titles,\n'
            '        latest(severity) as severity\n'
            '         by deviceSerial, deviceName, networkName\n'
            '| sort - alert_count'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input "
            "(sourcetype=meraki:assurancealerts). NOTE: Meraki MS does NOT emit per-queue drop "
            "counters to syslog or the Dashboard API. QoS visibility is limited to "
            "configuration audit (meraki:audit) and assurance alerts on congestion-related "
            "issues. For live queue depths use SNMP polling with CISCO-CLASS-BASED-QOS-MIB "
            "if the switch supports it (older MS models do not)."
        ),
        "implementation": (
            "1. Enable Assurance Alerts input. 2. Filter to deviceType=switch with "
            "queue/drop/QoS/congest keywords. 3. For configuration-drift tracking on QoS "
            "policies use the Audit input filtered to page='Switch QoS' or page='Switch ACLs'. "
            "4. Live per-queue drop telemetry is not available; use Meraki Dashboard -> "
            "Network-wide -> Traffic analytics for application-level visibility instead."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.1.49.json": {
        "spl": (
            'index=meraki sourcetype="meraki" (type=flows OR type=firewall)\n'
            '    pattern="deny*"\n'
            '    earliest=-24h\n'
            '| rex "src=(?<src_ip>[\\d\\.]+)"\n'
            '| rex "dst=(?<dst_ip>[\\d\\.]+)"\n'
            '| rex "mac=(?<src_mac>[0-9A-Fa-f:]+)"\n'
            '| stats count as block_count by host, src_ip, dst_ip, src_mac\n'
            '| sort - block_count\n'
            '| head 50'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki) receiving MX appliance flow logs "
            "(type=flows pre MX18.101, type=firewall MX18.101+). Each event carries src=, dst=, "
            "mac=, protocol=, sport=, dport=, pattern=allow/deny. NOTE: Meraki MS switch ACLs "
            "do NOT emit per-rule hit counters to syslog; this UC tracks denied flows at the MX "
            "boundary instead. For switch-side ACL visibility use Meraki Dashboard -> Switch -> "
            "Switch ACL hit counters (UI only)."
        ),
        "implementation": (
            "1. Configure SC4S for Meraki MX syslog. 2. In Meraki Dashboard enable Flows "
            "syslog category (Network-wide -> General -> Reporting). 3. Filter pattern=deny* "
            "to surface blocked flows. 4. The pattern field comes from the Meraki message body "
            "'pattern: allow all' or 'pattern: deny <rule_name>'. 5. To map blocked traffic "
            "back to specific firewall rules, name your rules descriptively in Meraki Dashboard "
            "-> Security & SD-WAN -> Firewall."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.1.50.json": {
        "spl": (
            'index=meraki sourcetype="meraki:assurancealerts"\n'
            '    deviceType="switch"\n'
            '    (title="*cable*" OR title="*physical*" OR title="*transceiver*"\n'
            '     OR title="*SFP*")\n'
            '    earliest=-7d\n'
            '| stats count as alert_count,\n'
            '        values(title) as cable_alerts,\n'
            '        latest(severity) as severity\n'
            '         by deviceSerial, deviceName, networkName\n'
            '| sort - alert_count\n'
            '| append [\n'
            '    search index=meraki sourcetype="meraki:portstransceiversreadingshistorybyswitch" earliest=-7d\n'
            '    | spath path=intervals{} output=interval_arr\n'
            '    | mvexpand interval_arr\n'
            '    | spath input=interval_arr\n'
            '    | stats avg(temperature.celsius) as avg_temp_c,\n'
            '            min(power.transmit.dbm) as min_tx_dbm,\n'
            '            min(power.receive.dbm) as min_rx_dbm\n'
            '             by serial, portId\n'
            '    | where min_rx_dbm < -20 OR avg_temp_c > 70\n'
            '  ]'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input + Switch Ports "
            "Transceivers Readings History by Switch input (sourcetype=meraki:"
            "portstransceiversreadingshistorybyswitch, TA v3.2+, OAuth scope "
            "switch:telemetry:read). NOTE: The Meraki Dashboard 'Cable Test' tool result is NOT "
            "delivered via syslog or as a polled API — it is only available interactively in "
            "the Dashboard UI."
        ),
        "implementation": (
            "1. Enable both Assurance Alerts and Switch Ports Transceivers Readings History "
            "inputs in Splunk_TA_cisco_meraki. 2. The Transceivers input polls "
            "GET /organizations/{orgId}/switch/ports/transceivers/readings/history/bySwitch and "
            "returns intervals[] of {ts, temperature.celsius, power.{transmit,receive}.dbm, "
            "voltage.volts, currentBias.milliamps}. 3. Alert on rx power below -20 dBm or "
            "transceiver temperature above 70 °C. 4. For the interactive cable diagnostics "
            "(open/short/length) use Meraki Dashboard -> Switch -> Switches -> [serial] -> "
            "Tools -> Cable test."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.1.51.json": {
        "spl": (
            'index=meraki sourcetype="meraki" type=events\n'
            '    ("uplink" OR "failover")\n'
            '    earliest=-24h\n'
            '| rex "(?<event_type>uplink|failover|recovered|failed)"\n'
            '| rex "to (?<target_uplink>wan\\d|cellular)"\n'
            '| stats count as failover_count,\n'
            '        values(event_type) as event_types,\n'
            '        values(target_uplink) as targets\n'
            '         by host\n'
            '| where failover_count > 0\n'
            '| sort - failover_count'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki) receiving Meraki MX appliance syslog. "
            "Uplink failover events appear as type=events with body 'failover to wan1', "
            "'failover to cellular', 'Cellular connection up', 'Cellular connection down'. "
            "host field carries the appliance hostname."
        ),
        "implementation": (
            "1. Configure SC4S for Meraki MX syslog and enable Appliance event log in Meraki "
            "Dashboard -> Network-wide -> General -> Reporting. 2. Use rex to extract the "
            "event_type and target uplink from the message body. 3. Pair this query with the "
            "API-side Devices Uplinks Loss and Latency input "
            "(sourcetype=meraki:devicesuplinkslossandlatency) for context on the uplink "
            "quality leading up to and following the failover."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.1.54.json": {
        "spl": (
            'index=meraki sourcetype="meraki" type=events\n'
            '    ("Cellular" OR "cellular" OR "carrier" OR "LTE" OR "5G")\n'
            '    earliest=-24h\n'
            '| rex "Cellular connection (?<state>up|down)"\n'
            '| stats count as event_count,\n'
            '        values(state) as states\n'
            '         by host\n'
            '| sort - event_count\n'
            '| append [\n'
            '    search index=meraki sourcetype="meraki:assurancealerts" deviceType="cellularGateway" earliest=-24h\n'
            '    | stats count as alert_count, values(title) as alerts by deviceSerial, networkName\n'
            '  ]'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki) for syslog from MX/MG cellular "
            "uplinks (Cellular connection up/down messages) and Splunk_TA_cisco_meraki "
            "Assurance Alerts input for cellular-specific alerts. NOTE: carrier name, RSSI, "
            "data plan usage and SIM status are NOT in syslog; the Dashboard API does not "
            "expose them either."
        ),
        "implementation": (
            "1. Configure SC4S for Meraki appliance syslog and enable the Appliance event log. "
            "2. Use rex to extract the cellular state from the message. 3. Enable the Assurance "
            "Alerts input for cellularGateway-specific alerts (registration loss, SIM swap, "
            "APN failure). 4. For RSSI / data-plan / carrier visibility, integrate with the "
            "carrier portal API (AT&T Control Center, Verizon ThingSpace) — the Meraki TA does "
            "not expose those fields."
        ),
    },

    # =========================================================================
    # MX SYSLOG fixes — type=security_event was wrong for non-AMP events
    # =========================================================================

    "content/cat-05-network-infrastructure/UC-5.2.24.json": {
        "spl": (
            'index=meraki sourcetype="meraki" (type=flows OR type=firewall) earliest=-24h\n'
            '| rex "src=(?<src_ip>[\\d\\.]+)"\n'
            '| rex "dst=(?<dst_ip>[\\d\\.]+)"\n'
            '| rex "protocol=(?<proto>\\S+)"\n'
            '| rex "(?:dport|sport)=(?<port>\\d+)"\n'
            '| stats count as flow_count by proto, port\n'
            '| sort - flow_count\n'
            '| head 20\n'
            '| append [\n'
            '    search index=meraki sourcetype="meraki:summarytopclientsbyusage" earliest=-24h\n'
            '    | stats latest(usage.total) as total_kb,\n'
            '            latest(usage.upstream) as upstream_kb,\n'
            '            latest(usage.downstream) as downstream_kb\n'
            '             by clientId, name, mac\n'
            '    | sort - total_kb\n'
            '    | head 10\n'
            '  ]'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki, type=flows / type=firewall) for "
            "L3 firewall flows from the MX, plus Splunk_TA_cisco_meraki Summary Top Clients "
            "by Usage input (sourcetype=meraki:summarytopclientsbyusage) for top-talker context. "
            "NOTE: Meraki MX traffic-shaping uses a token-bucket algorithm and does NOT emit "
            "per-queue drop counters; QoS effectiveness can only be inferred indirectly from "
            "flow distribution and top-talker usage."
        ),
        "implementation": (
            "1. Configure SC4S for MX syslog (Flows category enabled in Meraki Dashboard). "
            "2. Use rex to extract src/dst/protocol/port. 3. Enable the Summary Top Clients "
            "by Usage input for the org-wide top 10. 4. For genuine QoS health monitoring use "
            "Meraki Dashboard -> Security & SD-WAN -> Traffic shaping -> [rule] usage graphs "
            "(UI only); the Dashboard API does not expose per-rule shaped/dropped byte counters."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.2.28.json": {
        "spl": (
            'index=meraki sourcetype="meraki:appliancesdwanstatuses" earliest=-1h\n'
            '| spath path=vpnPeers{} output=peer_arr\n'
            '| mvexpand peer_arr\n'
            '| spath input=peer_arr\n'
            '| stats latest(reachability) as reachability,\n'
            '        latest(usage.sent) as bytes_sent,\n'
            '        latest(usage.received) as bytes_received\n'
            '         by networkId, networkName, peerNetworkId, peerNetworkName\n'
            '| where reachability != "reachable"\n'
            '| sort networkName'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Appliance VPN Statuses input "
            "(sourcetype=meraki:appliancesdwanstatuses). NOTE: Meraki MX does NOT speak BGP "
            "(it uses Auto VPN / SD-WAN dynamic path selection instead). This UC has been "
            "pivoted to monitor Auto VPN peer reachability — the closest semantically-equivalent "
            "control. For real BGP monitoring on the Cisco WAN tier, use cat-5.x BGP UCs that "
            "target IOS XE / SD-WAN / NSO sourcetypes."
        ),
        "implementation": (
            "1. Enable the Appliance VPN Statuses input in Splunk_TA_cisco_meraki. 2. Each "
            "event carries a vpnPeers[] array of {peerNetworkId, peerNetworkName, "
            "reachability, usage.{sent,received}}. 3. Trigger an alert when reachability "
            "transitions away from 'reachable'. 4. For BGP-specific telemetry deploy a Cisco "
            "Catalyst SD-WAN or vManage integration; Meraki MX is not a BGP speaker."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.2.34.json": {
        "spl": (
            'index=meraki sourcetype="meraki" type=events\n'
            '    ("failover" OR "uplink" OR "Cellular connection")\n'
            '    earliest=-7d\n'
            '| rex "failover to (?<target>wan\\d|cellular)"\n'
            '| rex "Cellular connection (?<cellular_state>up|down)"\n'
            '| eval failover_event = if(isnotnull(target),"failover_to_"+target, null())\n'
            '| eval cellular_event = if(isnotnull(cellular_state),"cellular_"+cellular_state, null())\n'
            '| eval event_type = coalesce(failover_event, cellular_event)\n'
            '| where isnotnull(event_type)\n'
            '| stats count as event_count,\n'
            '        values(event_type) as event_types,\n'
            '        earliest(_time) as first_seen,\n'
            '        latest(_time) as last_seen\n'
            '         by host\n'
            '| eval span_hours = round((last_seen - first_seen)/3600, 1)\n'
            '| sort - event_count'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki) receiving MX syslog. Uplink failover "
            "events use type=events with message bodies 'failover to wan1', 'failover to "
            "cellular', 'Cellular connection up', 'Cellular connection down'."
        ),
        "implementation": (
            "1. Configure SC4S for MX syslog and enable Appliance event log. 2. Use rex to "
            "extract the failover target and cellular state. 3. The 'failover to cellular' "
            "+ subsequent 'Cellular connection up' pair indicates a successful WAN-to-LTE "
            "failover. 4. For continuous uplink quality context combine with the API-side "
            "Devices Uplinks Loss and Latency input."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.2.35.json": {
        "spl": (
            'index=meraki sourcetype="meraki" type=events\n'
            '    ("Cellular" OR "cellular" OR "LTE" OR "5G")\n'
            '    earliest=-7d\n'
            '| rex "Cellular connection (?<state>up|down)"\n'
            '| stats count as cellular_events,\n'
            '        values(state) as states,\n'
            '        earliest(_time) as first_seen,\n'
            '        latest(_time) as last_seen\n'
            '         by host\n'
            '| eval span_hours = round((last_seen - first_seen)/3600, 1)\n'
            '| append [\n'
            '    search index=meraki sourcetype="meraki:summarytopdevicesbyusage" earliest=-30d\n'
            '    | join type=left serial [\n'
            '        search index=meraki sourcetype="meraki:devices" productType="cellularGateway"\n'
            '        | stats latest(name) as cellular_device by serial\n'
            '      ]\n'
            '    | where isnotnull(cellular_device)\n'
            '    | stats latest(usage.total) as total_kb by cellular_device\n'
            '    | eval total_gb = round(total_kb/1024/1024, 2)\n'
            '  ]'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki) for cellular failover events plus "
            "Splunk_TA_cisco_meraki Summary Top Devices by Usage and Devices inputs for "
            "cellular-device-specific data volume. NOTE: per-SIM data plan consumption is NOT "
            "available from Meraki; pull billing data from the carrier (AT&T, Verizon) directly."
        ),
        "implementation": (
            "1. Configure SC4S for MX/MG syslog. 2. Cellular up/down transitions appear as "
            "type=events. 3. For 30-day cellular data totals join meraki:summarytopdevicesbyusage "
            "with meraki:devices filtered to productType=cellularGateway. 4. For per-SIM monthly "
            "billing breakdown integrate with the carrier API (out of Meraki TA scope)."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.2.36.json": {
        "spl": (
            'index=meraki sourcetype="meraki" type=events\n'
            '    ("warm spare" OR "warm-spare" OR "HA" OR "redundancy"\n'
            '     OR "primary" OR "spare" OR "vrrp")\n'
            '    earliest=-7d\n'
            '| rex "(?<role>primary|spare|active|standby)"\n'
            '| stats count as ha_event_count,\n'
            '        values(role) as roles_seen\n'
            '         by host\n'
            '| where ha_event_count > 0\n'
            '| append [\n'
            '    search index=meraki sourcetype="meraki:assurancealerts" deviceType="appliance"\n'
            '        (title="*HA*" OR title="*spare*" OR title="*primary*") earliest=-7d\n'
            '    | stats values(title) as ha_alerts, count by deviceSerial, networkName\n'
            '  ]'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki) receiving MX warm-spare HA events as "
            "type=events, plus Splunk_TA_cisco_meraki Assurance Alerts input for HA-related "
            "Dashboard alerts."
        ),
        "implementation": (
            "1. Configure SC4S for MX syslog. 2. Warm-spare role transitions are emitted as "
            "type=events with role keywords. 3. Enable the Assurance Alerts input for "
            "Dashboard-side HA alerts (warm-spare unreachable, primary failed, etc.). 4. "
            "Trigger paging-grade alerts on every HA role change — these are real failover "
            "incidents."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.2.37.json": {
        "spl": (
            'index=meraki sourcetype="meraki" type=events\n'
            '    "type=vpn_connectivity_change"\n'
            '    earliest=-24h\n'
            '| rex "peer_contact=\'(?<peer>[\\d\\.:]+)\'"\n'
            '| rex "peer_ident=\'(?<peer_ident>[a-f0-9]+)\'"\n'
            '| rex "connectivity=\'(?<connectivity>true|false)\'"\n'
            '| rex "vpn_type=\'(?<vpn_type>[\\w\\-]+)\'"\n'
            '| stats count as path_change_count,\n'
            '        values(connectivity) as states,\n'
            '        latest(_time) as last_change\n'
            '         by host, peer, vpn_type\n'
            '| where path_change_count > 3\n'
            '| sort - path_change_count\n'
            '| append [\n'
            '    search index=meraki sourcetype="meraki:appliancesdwanstatistics" earliest=-24h\n'
            '    | stats avg(latencyMs) as avg_latency, avg(lossPercent) as avg_loss\n'
            '             by senderUplink, receiverUplink\n'
            '  ]'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki) for Auto VPN connectivity_change "
            "events as type=events with the structured 'type=vpn_connectivity_change vpn_type=... "
            "peer_contact=... peer_ident=... connectivity=...' payload, plus Splunk_TA_cisco_meraki "
            "Appliance VPN Stats input for tunnel performance context."
        ),
        "implementation": (
            "1. Configure SC4S for MX syslog and enable VPN logging in Meraki Dashboard. "
            "2. Auto VPN tunnel state changes are emitted as type=events with structured "
            "type=vpn_connectivity_change fields. 3. Use rex to extract peer / peer_ident / "
            "connectivity. 4. Sustained flapping (path_change_count > 3 in 24h) usually "
            "indicates underlay quality issues; correlate with the API-side "
            "meraki:appliancesdwanstatistics input for the WAN-link metrics during the same "
            "window."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.2.38.json": {
        "spl": (
            'index=meraki sourcetype="meraki" (type=flows OR type=firewall)\n'
            '    protocol="tcp"\n'
            '    earliest=-1h\n'
            '| rex "src=(?<src_ip>[\\d\\.]+)"\n'
            '| rex "dst=(?<dst_ip>[\\d\\.]+)"\n'
            '| rex "dport=(?<dst_port>\\d+)"\n'
            '| timechart span=1m count as new_connections by src_ip useother=false limit=10\n'
            '| where new_connections > 1000'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki, type=flows / type=firewall) receiving "
            "MX L3 firewall flow logs. NOTE: Meraki MX flow records do NOT expose individual "
            "TCP flag bits; only the protocol, src/dst, sport/dport, and pattern (allow/deny) "
            "are emitted. This UC monitors absolute new-connection rate per source IP as a "
            "DoS indicator."
        ),
        "implementation": (
            "1. Configure SC4S for MX syslog with Flows category enabled in Meraki Dashboard. "
            "2. Each flow event carries src=, dst=, mac=, protocol=, sport=, dport=, pattern. "
            "3. Threshold > 1000 new TCP flows per minute per source is a strong DoS / "
            "scanning indicator. 4. For SYN-flag-aware detection deploy a Snort sensor and "
            "ingest its alerts via the existing IDS/IPS pipeline; Meraki MX flow logs do not "
            "carry TCP flag detail."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.2.39.json": {
        "spl": (
            'index=meraki sourcetype="meraki" type=urls action="blocked"\n'
            '    earliest=-24h\n'
            '| rex "src=(?<src_ip>[\\d\\.]+)"\n'
            '| rex "dst=(?<dst_ip>[\\d\\.]+)"\n'
            '| rex "request: (?:GET|POST) (?<url>https?://[^\\s]+)"\n'
            '| lookup pii_keyword_list keyword OUTPUTNEW pii_category\n'
            '| where isnotnull(pii_category)\n'
            '| stats count as event_count,\n'
            '        values(url) as urls,\n'
            '        values(pii_category) as categories\n'
            '         by src_ip\n'
            '| sort - event_count'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki, type=urls) receiving Meraki content "
            "filtering events. NOTE: Meraki MX does NOT have a built-in DLP engine. This UC "
            "uses a customer-maintained pii_keyword_list lookup against blocked URLs as a "
            "weak proxy. For real DLP coverage deploy a dedicated DLP product (Cisco Secure "
            "Email, Microsoft Purview, Forcepoint DLP, Symantec DLP) and ingest its events "
            "instead — this UC's premise is fundamentally limited on a Meraki-only stack."
        ),
        "implementation": (
            "1. Configure SC4S for MX syslog and enable URLs syslog category in Meraki "
            "Dashboard. 2. Maintain a pii_keyword_list.csv lookup with columns (keyword, "
            "pii_category) reflecting your sensitive-data terms. 3. The URL field comes from "
            "the message body 'request: GET <url>'. 4. For comprehensive DLP coverage deploy "
            "a purpose-built DLP product — Meraki MX has no native DLP and the URL-keyword "
            "matching here will only catch HTTP requests where the keyword is in the URL "
            "path/query, missing all HTTPS body content."
        ),
    },

    # =========================================================================
    # WIRELESS (MR) SYSLOG fixes
    # =========================================================================

    "content/cat-05-network-infrastructure/UC-5.4.12.json": {
        "spl": (
            'index=meraki sourcetype="meraki" type=events\n'
            '    (type=disassociation OR type=8021x_eap_failure OR type=wpa_deauth)\n'
            '    earliest=-24h\n'
            '| rex "reason=\'(?<reason_code>\\d+)\'"\n'
            '| rex "vap=\'(?<vap_id>\\d+)\'"\n'
            '| rex "channel=\'(?<channel>\\d+)\'"\n'
            '| rex "identity=\'(?<client_identity>[^\\\']+)\'"\n'
            '| rex "aid=\'(?<client_aid>\\d+)\'"\n'
            '| stats count as failure_count,\n'
            '        values(reason_code) as reasons,\n'
            '        values(client_identity) as users\n'
            '         by host, vap_id, type\n'
            '| sort - failure_count'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki) receiving MR access-point syslog. "
            "Wireless association failures appear as type=events with structured type=disassociation, "
            "type=8021x_eap_failure, or type=wpa_deauth subkinds and key=value fields including "
            "reason=, vap=, channel=, identity=, aid=, instigator=."
        ),
        "implementation": (
            "1. Configure SC4S for MR syslog and enable the Access-point event log in Meraki "
            "Dashboard. 2. The structured key=value payload lets you extract reason code, "
            "VAP (virtual AP / SSID id), channel, and user identity. 3. 802.11 reason codes "
            "8/9/15/23 indicate authentication problems; codes 4/5/6/12 indicate session "
            "disconnects. 4. host field carries the AP name (e.g. MR18). 5. For continuous "
            "auth-failure dashboards, also enable the Air Marshal input (sourcetype=meraki:airmarshal) "
            "for rogue/spoof events."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.14.json": {
        "spl": (
            'index=meraki sourcetype="meraki" type=events\n'
            '    (type=association OR type=disassociation)\n'
            '    earliest=-24h\n'
            '| rex "aid=\'(?<client_aid>\\d+)\'"\n'
            '| rex "vap=\'(?<vap_id>\\d+)\'"\n'
            '| rex "channel=\'(?<channel>\\d+)\'"\n'
            '| stats count as event_count,\n'
            '        dc(host) as ap_count,\n'
            '        values(host) as ap_names\n'
            '         by client_aid\n'
            '| where event_count > 20 AND ap_count > 3\n'
            '| sort - event_count'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki) receiving MR access-point syslog. "
            "Roaming = a client with high association/disassociation event count across "
            "multiple APs (host field). Each event carries aid (association id), vap, channel."
        ),
        "implementation": (
            "1. Configure SC4S for MR syslog. 2. Group by client_aid (which is a Meraki-issued "
            "association identifier persistent for a session). 3. Filter for clients seen on "
            ">3 APs with >20 association events in 24h — these are 'sticky-client' or "
            "band-steering loop candidates. 4. Identifying the underlying physical client: the "
            "client MAC isn't in the syslog payload directly; correlate with the API-side "
            "Wireless Packet Loss by Device input (meraki:wirelessdevicespacketlossbydevice) "
            "or the Meraki Dashboard -> Wireless -> Clients page."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.20.json": {
        "spl": (
            'index=meraki sourcetype="meraki" type=events\n'
            '    (type=8021x_eap_failure OR type=8021x_deauth OR type=wpa_deauth)\n'
            '    earliest=-24h\n'
            '| rex "identity=\'(?<client_identity>[^\\\']+)\'"\n'
            '| rex "vap=\'(?<vap_id>\\d+)\'"\n'
            '| rex "aid=\'(?<client_aid>\\d+)\'"\n'
            '| stats count as auth_failures,\n'
            '        values(type) as failure_types,\n'
            '        values(host) as aps_involved\n'
            '         by client_identity, vap_id\n'
            '| where auth_failures > 5\n'
            '| sort - auth_failures'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki) receiving MR syslog. 802.1X EAP "
            "failures appear as type=events with type=8021x_eap_failure / 8021x_deauth and the "
            "user identity in the identity= field."
        ),
        "implementation": (
            "1. Configure SC4S for MR syslog. 2. The 802.1X identity (typically a username, "
            "service principal, or computer account) is in the identity= field. 3. Threshold "
            ">5 failures per identity per VAP indicates either a legitimate auth issue "
            "(expired password, wrong RADIUS shared secret, wrong supplicant cert) or a "
            "credential-stuffing attempt. 4. For RADIUS-side context, ingest the RADIUS "
            "server log (e.g. ISE, NPS) and correlate on the username."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.22.json": {
        "spl": (
            'index=meraki sourcetype="meraki" type=events type=splash_auth\n'
            '    earliest=-7d\n'
            '| rex "ip=\'(?<client_ip>[\\d\\.]+)"\n'
            '| rex "duration=\'(?<duration>\\d+)\'"\n'
            '| rex "vap=\'(?<vap_id>\\d+)\'"\n'
            '| rex "download=\'(?<download_bps>\\d+)bps\'"\n'
            '| rex "upload=\'(?<upload_bps>\\d+)bps\'"\n'
            '| stats count as auth_count,\n'
            '        avg(duration) as avg_session_secs,\n'
            '        sum(eval(download_bps + upload_bps)) as total_bps\n'
            '         by host, vap_id\n'
            '| sort - auth_count'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki) receiving MR syslog. Splash page "
            "authentications appear as type=events with type=splash_auth and structured ip=, "
            "duration=, vap=, download=, upload= fields."
        ),
        "implementation": (
            "1. Configure SC4S for MR syslog and enable the Access-point event log. 2. Each "
            "splash authentication emits one event per accepted client. 3. duration = the "
            "session timeout granted by the splash policy (in seconds); download/upload = the "
            "per-client throughput cap. 4. For redirect / dropped / abandoned splash attempts, "
            "configure a Meraki Dashboard alert profile on 'splash page redirect failure' and "
            "ingest via the Webhook Logs (HEC) input."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.23.json": {
        "spl": (
            'index=meraki sourcetype="meraki" (type=flows OR type=firewall)\n'
            '    (dst="255.255.255.255" OR dst="224.*" OR dst="239.*"\n'
            '     OR mac="ff:ff:ff:ff:ff:ff")\n'
            '    earliest=-1h\n'
            '| rex "src=(?<src_ip>[\\d\\.]+)"\n'
            '| rex "mac=(?<src_mac>[0-9A-Fa-f:]+)"\n'
            '| rex "protocol=(?<proto>\\S+)"\n'
            '| stats count as packet_count,\n'
            '        values(src_ip) as sources,\n'
            '        values(proto) as protos\n'
            '         by host, src_mac\n'
            '| where packet_count > 1000\n'
            '| sort - packet_count'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki) receiving MR L3 firewall flow logs. "
            "Broadcast / multicast traffic surfaces in flows with dst=255.255.255.255 (broadcast), "
            "dst in 224.0.0.0/4 (multicast), or mac=ff:ff:ff:ff:ff:ff (broadcast MAC)."
        ),
        "implementation": (
            "1. Configure SC4S for MR syslog with the Flows category enabled. 2. Filter for "
            "broadcast / multicast destinations. 3. Per-source-MAC packet counts > 1000 in an "
            "hour usually indicate a misbehaving IoT device or a broadcast-storm-causing app. "
            "4. Cross-reference with the wired side: if the same MAC appears on the MS switch "
            "syslog flooding messages it confirms the source is on a wired port."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.26.json": {
        "spl": (
            'index=meraki sourcetype="meraki" (type=flows OR type=firewall) earliest=-24h\n'
            '| rex "src=(?<src_ip>[\\d\\.]+)"\n'
            '| rex "mac=(?<client_mac>[0-9A-Fa-f:]+)"\n'
            '| rex "protocol=(?<proto>\\S+)"\n'
            '| rex "dport=(?<dst_port>\\d+)"\n'
            '| stats count as flow_count,\n'
            '        values(proto) as protos,\n'
            '        values(dst_port) as dst_ports\n'
            '         by client_mac, src_ip\n'
            '| sort - flow_count\n'
            '| head 20\n'
            '| append [\n'
            '    search index=meraki sourcetype="meraki:summarytopclientsbyusage" earliest=-24h\n'
            '    | stats latest(usage.total) as total_kb,\n'
            '            latest(usage.upstream) as upload_kb,\n'
            '            latest(usage.downstream) as download_kb\n'
            '             by clientId, name, mac\n'
            '    | sort - total_kb\n'
            '    | head 20\n'
            '  ]'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki, type=flows / type=firewall) for "
            "syslog flow records (which give protocol/port granularity but not byte counters), "
            "plus Splunk_TA_cisco_meraki Summary Top Clients by Usage input "
            "(sourcetype=meraki:summarytopclientsbyusage, daily) for the org's top 10 clients "
            "by data volume in kB. NOTE: per-flow byte counters are NOT in Meraki syslog."
        ),
        "implementation": (
            "1. Configure SC4S for MR syslog and enable the Summary Top Clients by Usage input "
            "in Splunk_TA_cisco_meraki. 2. Syslog gives flow-count / protocol-distribution per "
            "client_mac (extracted via rex from the mac= field). 3. The Top Clients input "
            "polls GET /organizations/{orgId}/summary/top/clients/byUsage and returns the top "
            "10 with usage.{total,upstream,downstream} in kB. 4. For full per-client byte "
            "accounting beyond top-10, use the Meraki Dashboard -> Network-wide -> Clients page "
            "(UI) or scrape /networks/{networkId}/clients/{clientId}/usageHistory with a custom "
            "modular input."
        ),
    },

    # =========================================================================
    # DHCP / DNS
    # =========================================================================

    "content/cat-05-network-infrastructure/UC-5.6.13.json": {
        "spl": (
            'index=meraki sourcetype="meraki" type=events\n'
            '    ("dhcp no offers" OR "dhcp lease" OR "DHCP NACK" OR "Blocked DHCP")\n'
            '    earliest=-24h\n'
            '| rex "for mac (?<client_mac>[0-9A-Fa-f:]+)"\n'
            '| rex "host = (?<dhcp_server>[\\d\\.]+)"\n'
            '| eval failure_type = case(\n'
            '    match(_raw, "dhcp no offers"), "no_offers",\n'
            '    match(_raw, "DHCP NACK"), "nack",\n'
            '    match(_raw, "Blocked DHCP"), "blocked_rogue",\n'
            '    1=1, "lease")\n'
            '| stats count as failure_count,\n'
            '        values(client_mac) as failed_clients,\n'
            '        values(dhcp_server) as servers\n'
            '         by host, failure_type\n'
            '| where failure_type != "lease" AND failure_count > 5\n'
            '| sort - failure_count'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki) receiving Meraki MX/MS syslog. "
            "DHCP events appear as type=events with message bodies 'dhcp no offers for mac "
            "<mac>', 'dhcp lease of ip <ip> from server mac <mac> for client mac <mac>', "
            "and 'Blocked DHCP server response from <mac> on VLAN <id>'."
        ),
        "implementation": (
            "1. Configure SC4S for Meraki MX/MS syslog and enable Appliance + Switch event "
            "logs in Meraki Dashboard. 2. 'dhcp no offers' indicates the DHCP server pool is "
            "exhausted or unreachable; 'DHCP NACK' indicates a lease conflict; 'Blocked DHCP' "
            "indicates DHCP guard caught a rogue server. 3. Threshold per AP/switch and "
            "trigger Splunk alerts on sustained exhaustion. 4. For real-time pool sizing use "
            "GET /networks/{networkId}/appliance/vlans (VLAN reservation/exclusion ranges) "
            "with a custom modular input — that endpoint is not yet polled by the TA."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.6.14.json": {
        "spl": (
            'index=dns sourcetype IN ("infoblox:dns:query","bind","stream:dns","dns")\n'
            '    earliest=-24h\n'
            '| eval resolution_ms = coalesce(resolution_time_ms, response_time_ms, duration_ms)\n'
            '| where isnum(resolution_ms)\n'
            '| stats avg(resolution_ms) as avg_dns_ms,\n'
            '        max(resolution_ms) as max_dns_ms,\n'
            '        count\n'
            '         by src, dest\n'
            '| where avg_dns_ms > 100\n'
            '| sort - avg_dns_ms'
        ),
        "dataSources": (
            "DNS server logs from your authoritative / recursive resolver (Infoblox, BIND, "
            "Microsoft DNS) or DNS wire data (Splunk Stream sourcetype=stream:dns). "
            "NOTE: Meraki does NOT log DNS resolution time. Meraki MX syslog only records the "
            "DHCP lease (which references the offered DNS server), not actual DNS query "
            "performance. This UC has been pivoted to the customer's actual DNS infrastructure."
        ),
        "implementation": (
            "1. Choose a DNS source you actually operate: Infoblox (sourcetype=infoblox:dns:query), "
            "BIND (sourcetype=bind, query log enabled), Microsoft DNS (sourcetype=msad:nt6:dns), "
            "or Splunk Stream (sourcetype=stream:dns). 2. resolution_time_ms / response_time_ms "
            "/ duration_ms are typical field names depending on source. 3. For wire-data "
            "deployment, install Splunk Stream or use Cisco Cyber Vision -> Splunk for OT-side "
            "DNS visibility. 4. Pair with Meraki MX flow logs (type=flows dport=53) for "
            "client-IP context."
        ),
    },

    # =========================================================================
    # ADMIN ACTIVITY — pivot from syslog (which doesn't carry it) to meraki:audit
    # =========================================================================

    "content/cat-05-network-infrastructure/UC-5.8.14.json": {
        "spl": (
            'index=meraki sourcetype="meraki:audit" earliest=-7d\n'
            '| stats count as admin_action_count,\n'
            '        values(action) as actions,\n'
            '        values(page) as pages,\n'
            '        values(label) as targets,\n'
            '        earliest(_time) as first_action,\n'
            '        latest(_time) as last_action\n'
            '         by adminName, organizationName\n'
            '| where admin_action_count > 0\n'
            '| sort - admin_action_count'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Audit input (sourcetype=meraki:audit, "
            "daily polling of GET /organizations/{orgId}/configurationChanges, OAuth scope "
            "dashboard:general:config:read). NOTE: admin activity is NOT in Meraki syslog — "
            "it is only available via the Audit input."
        ),
        "implementation": (
            "1. Enable the Audit input in Splunk_TA_cisco_meraki. The TA polls "
            "GET /organizations/{orgId}/configurationChanges daily (configurable to as low as "
            "6 minutes) and emits one event per admin action with adminName, page, label, "
            "action, networkName, ssidNumber, ts, and the JSON oldValue / newValue. 2. Group "
            "by adminName for per-admin activity dashboards. 3. For privileged-admin / orphaned-"
            "admin detection, lookup adminName against your IDM and flag orphans."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.8.15.json": {
        "spl": (
            'index=meraki sourcetype="meraki:audit" earliest=-30d\n'
            '    (page="Administrators" OR page="Permissions"\n'
            '     OR label="*role*" OR label="*permission*" OR action="*admin*")\n'
            '| stats count as priv_change_count,\n'
            '        values(label) as targets,\n'
            '        values(action) as actions,\n'
            '        values(page) as pages,\n'
            '        latest(_time) as last_change\n'
            '         by adminName, organizationName\n'
            '| sort - last_change'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Audit input "
            "(sourcetype=meraki:audit). Admin role / permission changes show up under "
            "page='Administrators' or page='Permissions'."
        ),
        "implementation": (
            "1. Enable the Audit input in Splunk_TA_cisco_meraki. 2. Filter on the "
            "Administrators / Permissions pages to surface privilege escalations. 3. The "
            "audit event includes oldValue / newValue carrying the previous and new role JSON "
            "blob — useful for forensic detail. 4. Trigger a high-priority alert on every "
            "privilege change; pair with your IDM for change-control validation."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.8.20.json": {
        "spl": (
            'index=meraki sourcetype="meraki:audit" earliest=-30d\n'
            '| eval change_hour = strftime(_time, "%H")\n'
            '| eval window_compliant = if(change_hour>=22 OR change_hour<6, "Yes", "No")\n'
            '| stats count as change_count,\n'
            '        values(adminName) as admins,\n'
            '        values(page) as pages\n'
            '         by window_compliant, change_hour\n'
            '| where window_compliant="No"\n'
            '| sort change_hour'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Audit input "
            "(sourcetype=meraki:audit). Configuration changes are NOT in Meraki syslog — they "
            "are only available via the Audit input which polls GET /organizations/{orgId}/"
            "configurationChanges."
        ),
        "implementation": (
            "1. Enable the Audit input in Splunk_TA_cisco_meraki. 2. The 'change window' is a "
            "policy decision — adjust the eval threshold to your maintenance window definition "
            "(here: 22:00–06:00 local). 3. _time on each audit event is the change timestamp. "
            "4. Pair with adminName to identify out-of-window admins; route to your change-"
            "advisory-board ticketing system."
        ),
    },
}


def update_uc(path: Path, overrides: dict[str, str]) -> bool:
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
