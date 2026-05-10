#!/usr/bin/env python3
"""Final cleanup pass for Meraki UCs that don't fit the prior batches.

This script handles:

- ``5.4.1`` AP Offline Detection — the SPL claimed Meraki APs emit a
  ``"went offline"`` syslog event. They do NOT (Meraki MR APs only emit
  association/disassociation/auth events; offline detection comes from the
  Dashboard side). Rewritten to use the API-side ``meraki:devicesavailabilities``
  input.
- ``5.8.11`` API Call Rate — used ``sourcetype="meraki:*"`` with hallucinated
  ``endpoint`` / ``source`` fields. Rewritten against ``meraki:apirequestsoverview``
  / ``meraki:apirequestshistory``.
- ``5.8.22`` API Error Rate — same problem; rewritten against
  ``meraki:apirequestsresponsecodes`` (hourly buckets by responseCode) and
  ``meraki:apirequestshistory`` (per-request log with method, path, responseCode).
- ``14.1.49`` IAQ Index — extends the SPL to include the Meraki MT
  ``meraki:sensorreadingshistory`` source for IAQ when MT sensors are deployed.
- ``22.15.53`` OT SSID Unknown Clients — adds rex extraction so the ``ssid``
  field can actually be filtered (it is not a parsed field on
  ``sourcetype="meraki"`` by default).
- ``11.5.10`` / ``11.5.9`` Meeting Room Analytics — clarifies in implementation
  that Meraki MV camera people-counting requires webhook ingestion (it is
  NOT polled by the TA).
- WLC Meraki dual-app UCs (5.4.10/11/2/4/6/9 and 5.4.1) — fixes the ``app``
  field to honestly reflect what the SPL queries (Cisco WLC syslog, NOT the
  Meraki TA), and adds an "If using Meraki MR instead" note in implementation
  pointing at the correct Meraki TA inputs.

Usage:
    PYTHONPATH=src python3 scripts/rewrite_meraki_misc_fixes.py
    PYTHONPATH=src python3 scripts/regen_di_for_ucs.py --meraki-misc-fix
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

REWRITES: dict[str, dict[str, str]] = {

    "content/cat-05-network-infrastructure/UC-5.4.1.json": {
        "spl": (
            'index=meraki sourcetype="meraki:devicesavailabilities" productType="wireless" earliest=-1h\n'
            '| stats latest(status) as ap_status,\n'
            '        latest(_time) as last_status_time,\n'
            '        latest(name) as ap_name,\n'
            '        latest(network.name) as network_name\n'
            '         by serial, mac\n'
            '| where ap_status != "online"\n'
            '| eval offline_minutes = round((now() - last_status_time)/60, 0)\n'
            '| sort - offline_minutes\n'
            '| append [\n'
            '    search index=meraki sourcetype="meraki:devicesavailabilitieschangehistory"\n'
            '        productType="wireless" status="offline" earliest=-24h\n'
            '    | stats earliest(_time) as offline_since,\n'
            '            values(previousStatus) as previous_status\n'
            '             by serial, networkName\n'
            '  ]'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): Devices Availabilities input "
            "(sourcetype=meraki:devicesavailabilities, daily, TA v3.3+) and Devices "
            "Availabilities Change History input (sourcetype=meraki:devicesavailabilitieschangehistory, "
            "hourly). NOTE: Meraki MR access points do NOT emit 'device offline' syslog events. "
            "AP offline detection is performed by the Meraki Dashboard cloud (controller) and "
            "exposed through the polled Devices Availabilities API endpoint."
        ),
        "implementation": (
            "1. In Splunk_TA_cisco_meraki enable both Devices Availabilities and Devices "
            "Availabilities Change History inputs (TA v3.3+). 2. Filter to productType=wireless "
            "for MR APs. The Availabilities input gives current state; the Change History "
            "input lists every transition (online -> offline, etc.). 3. For paging-grade "
            "alerting, configure a Meraki Dashboard alert profile on 'device went offline for "
            "X minutes' and ingest via the Webhook Logs (HEC) input — webhook latency is "
            "near-real-time vs the daily Availabilities polling cadence."
        ),
        "app": "`Cisco Meraki Add-on for Splunk` (Splunkbase 5580)",
    },

    "content/cat-05-network-infrastructure/UC-5.8.11.json": {
        "spl": (
            'index=meraki sourcetype="meraki:apirequestsoverview" earliest=-1h\n'
            '| spath\n'
            '| stats sum(counts.success) as success_calls,\n'
            '        sum(counts.error) as error_calls,\n'
            '        sum(counts.total) as total_calls\n'
            '         by interval, organizationId\n'
            '| eval call_rate_per_min = round(total_calls/(60), 1)\n'
            '| eval error_pct = round(error_calls*100/total_calls, 2)\n'
            '| where call_rate_per_min > 9 OR error_pct > 5\n'
            '| sort - call_rate_per_min'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): API Requests Overview input "
            "(sourcetype=meraki:apirequestsoverview, daily, TA v3+, OAuth scope "
            "dashboard:general:telemetry:read). For per-request granularity also enable the "
            "API Requests History input (sourcetype=meraki:apirequestshistory) which carries "
            "host, path, method, responseCode, sourceIp, userAgent, ts."
        ),
        "implementation": (
            "1. Enable the API Requests Overview input in Splunk_TA_cisco_meraki. The TA polls "
            "GET /organizations/{orgId}/apiRequests/overview and emits aggregated counters "
            "(counts.success, counts.error, counts.total) per interval. 2. The Meraki "
            "Dashboard API enforces a per-organization rate limit of 10 requests per second; "
            "alert when call_rate_per_min approaches 540 (9 rps sustained). 3. For per-API-key "
            "drill-down, also enable the API Requests History input which gives per-call detail "
            "including the userAgent so you can identify which integration is generating the "
            "load."
        ),
        "app": "`Cisco Meraki Add-on for Splunk` (Splunkbase 5580)",
    },

    "content/cat-05-network-infrastructure/UC-5.8.22.json": {
        "spl": (
            'index=meraki sourcetype="meraki:apirequestshistory" earliest=-1h\n'
            '| where responseCode >= 400\n'
            '| stats count as error_count,\n'
            '        values(responseCode) as response_codes,\n'
            '        values(method) as http_methods\n'
            '         by path, organizationId\n'
            '| sort - error_count\n'
            '| append [\n'
            '    search index=meraki sourcetype="meraki:apirequestsresponsecodes" earliest=-24h\n'
            '    | spath path=counts{} output=counts_arr\n'
            '    | mvexpand counts_arr\n'
            '    | spath input=counts_arr\n'
            '    | where code >= 400\n'
            '    | stats sum(count) as response_count by code, organizationId\n'
            '    | sort - response_count\n'
            '  ]'
        ),
        "dataSources": (
            "Splunk_TA_cisco_meraki (Splunkbase #5580): API Requests History input "
            "(sourcetype=meraki:apirequestshistory, daily, TA v3+) for per-request log and "
            "API Requests Response Codes input (sourcetype=meraki:apirequestsresponsecodes, "
            "daily) for hourly response-code histograms."
        ),
        "implementation": (
            "1. Enable both API Requests History and API Requests Response Codes inputs in "
            "Splunk_TA_cisco_meraki (TA v3+). 2. The History input emits one event per "
            "individual API call with host, path (e.g. '/organizations/.../devices'), method, "
            "responseCode, sourceIp, userAgent, ts. 3. The Response Codes input gives "
            "aggregated counts per (responseCode, interval). 4. Threshold 4xx/5xx error rate "
            ">5% per endpoint to surface broken integrations or rate-limit hits (responseCode "
            "429). 5. For client-side root-cause, the userAgent field reveals which integration "
            "(e.g. 'curl', 'python-meraki', 'TA-meraki/3.x') is misbehaving."
        ),
        "app": "`Cisco Meraki Add-on for Splunk` (Splunkbase 5580)",
    },

    "content/cat-14-iot-operational-technology-ot/UC-14.1.49.json": {
        "spl": (
            'index=building sourcetype="bms:iaq" earliest=-24h\n'
            '| bin _time span=15m\n'
            '| stats avg(co2_ppm) as avg_co2,\n'
            '        avg(pm25_ugm3) as avg_pm25,\n'
            '        avg(tvoc_ppb) as avg_tvoc,\n'
            '        avg(temperature_c) as avg_temp,\n'
            '        avg(humidity_pct) as avg_rh\n'
            '         by zone, floor, building, _time\n'
            '| append [\n'
            '    search index=meraki sourcetype="meraki:sensorreadingshistory"\n'
            '        (metric="co2" OR metric="pm25" OR metric="tvoc" OR metric="temperature" OR metric="humidity")\n'
            '        earliest=-24h\n'
            '    | spath\n'
            '    | bin _time span=15m\n'
            '    | eval mt_temp = if(metric="temperature", \'temperature.celsius\', null())\n'
            '    | eval mt_co2 = if(metric="co2", \'co2.concentration\', null())\n'
            '    | eval mt_pm25 = if(metric="pm25", \'pm25.concentration\', null())\n'
            '    | eval mt_tvoc = if(metric="tvoc", \'tvoc.concentration\', null())\n'
            '    | eval mt_rh = if(metric="humidity", \'humidity.relativePercentage\', null())\n'
            '    | stats avg(mt_co2) as avg_co2,\n'
            '            avg(mt_pm25) as avg_pm25,\n'
            '            avg(mt_tvoc) as avg_tvoc,\n'
            '            avg(mt_temp) as avg_temp,\n'
            '            avg(mt_rh) as avg_rh\n'
            '             by serial, networkId, _time\n'
            '  ]\n'
            '| eval co2_score=case(avg_co2<600, 100, avg_co2<800, 80, avg_co2<1000, 60, avg_co2<1500, 40, 1=1, 20)\n'
            '| eval pm25_score=case(avg_pm25<12, 100, avg_pm25<35, 80, avg_pm25<55, 60, avg_pm25<150, 40, 1=1, 20)\n'
            '| eval iaq_score = round((co2_score + pm25_score)/2, 0)\n'
            '| where iaq_score < 70\n'
            '| sort iaq_score'
        ),
        "dataSources": (
            "Building Management System (BMS) IAQ source (sourcetype=bms:iaq) via the BACnet "
            "or Modbus integration of choice, plus optionally Splunk_TA_cisco_meraki Sensor "
            "Readings History input (sourcetype=meraki:sensorreadingshistory) for Meraki MT "
            "environmental sensors. The MT sensor metrics are: temperature.celsius, "
            "humidity.relativePercentage, co2.concentration, pm25.concentration, "
            "tvoc.concentration, noise.ambient.level."
        ),
        "implementation": (
            "1. Identify your IAQ data source: BMS via BACnet (Tridium Niagara, Honeywell EBI, "
            "Siemens Desigo CC), purpose-built IAQ vendor (Airthings, Awair, Kaiterra) via "
            "their REST API, or Cisco Meraki MT environmental sensors. 2. For MT sensors, "
            "enable the Sensor Readings History input in Splunk_TA_cisco_meraki (TA v3+, "
            "OAuth scope sensor:telemetry:read). The TA polls "
            "GET /organizations/{orgId}/sensor/readings/history and emits one event per "
            "{sensor, metric, ts} sample with the metric-specific nested path "
            "(e.g. temperature.celsius). 3. Compute a composite IAQ score from CO2 and PM2.5 "
            "(extend with TVOC, formaldehyde, radon as your sensors support). 4. Threshold "
            "iaq_score < 70 to alert facilities."
        ),
        "app": (
            "IAQ sensors (Airthings, Awair, Kaiterra) via API, BACnet IAQ points, Meraki MT "
            "via `Cisco Meraki Add-on for Splunk` (Splunkbase 5580)"
        ),
    },

    "content/cat-22-regulatory-compliance/UC-22.15.53.json": {
        "spl": (
            'index=wireless (sourcetype="meraki" OR sourcetype="cisco:wlc") earliest=-24h\n'
            '| rex "(?:vap=\'|ssid=\'|SSID )(?<ssid>[A-Za-z0-9_\\-\\.]+)"\n'
            '| rex "(?:client_mac=|aid=\'|MAC )(?<client_mac>[0-9A-Fa-f:]+)"\n'
            '| rex "(?:src=|src_ip=)(?<src_ip>[\\d\\.]+)"\n'
            '| where like(ssid, "OT-PROD-%")\n'
            '| iplocation src_ip\n'
            '| lookup ot_wireless_allowlist.csv client_mac OUTPUT asset_class\n'
            '| where asset_class!="instrumentation" OR isnull(asset_class)\n'
            '| stats earliest(_time) as first_seen,\n'
            '        latest(_time) as last_seen,\n'
            '        values(asset_class) as asset_classes\n'
            '         by client_mac, ssid, host\n'
            '| sort - last_seen'
        ),
        "dataSources": (
            "SC4S Meraki vendor pack (sourcetype=meraki) for MR access-point syslog and/or "
            "Splunk Add-on for Cisco WLC (sourcetype=cisco:wlc) for AireOS/Catalyst 9800 "
            "syslog. NOTE: ssid and client_mac are NOT auto-extracted on sourcetype=meraki; "
            "this UC uses rex to pull them from the structured key=value Meraki payload "
            "(vap=, aid=, src=) and the freeform Cisco WLC body. ot_wireless_allowlist.csv "
            "is a customer-maintained allowlist with columns (client_mac, asset_class)."
        ),
        "implementation": (
            "1. Configure SC4S to receive Meraki MR and/or Cisco WLC syslog. 2. Use rex to "
            "extract ssid, client_mac, src_ip — these are not auto-parsed fields on either "
            "sourcetype. 3. Maintain ot_wireless_allowlist.csv with the MAC addresses of "
            "authorised OT instrumentation. 4. The query surfaces clients on OT-PROD-* SSIDs "
            "that are not in the allowlist or are tagged as a non-instrumentation asset class. "
            "5. For OUI-based vendor categorisation, supplement with an OUI lookup against "
            "the IEEE registry."
        ),
    },

    "content/cat-11-email-collaboration/UC-11.5.10.json": {
        "implementation": (
            "1. Identify your room sensor source: Cisco Webex devices (sourcetype=webex:room_analytics) "
            "for Webex room kits, Cisco Spaces for Meraki MV-based people counting, or a "
            "third-party occupancy sensor. 2. Pull occupancy data via the Webex Add-on for "
            "Splunk (Splunkbase #5781). 3. Maintain a room_inventory lookup with columns "
            "(room_id, room_name, capacity, room_type, building, floor). 4. Compute "
            "utilization_pct from people_count vs capacity. 5. For Meraki MV-based people "
            "counting (a separate path) configure the Meraki Dashboard alert profile "
            "'mv_people_counting' webhook events and ingest via the Splunk_TA_cisco_meraki "
            "Webhook Logs (HEC) input (sourcetype=meraki:webhook); the polled Meraki TA does "
            "NOT expose people-count metrics. 6. Categorise size_match for facilities planning."
        ),
        "app": (
            "`Cisco Webex Add-on` (Splunkbase #5781), Cisco Spaces Add-On (Splunkbase #8485), "
            "and (optional, webhook-only) `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) "
            "for MV camera people-counting"
        ),
    },

    "content/cat-11-email-collaboration/UC-11.5.9.json": {
        "implementation": (
            "1. Identify your room booking and occupancy sources: Webex calendar bookings "
            "(sourcetype=webex:room_analytics with booking_id) and Webex / Cisco Spaces / "
            "Meraki MV occupancy. 2. Compute booked = isnotnull(booking_id), occupied = "
            "people_presence='Yes' OR people_count>0. 3. no_show = (booked AND NOT occupied); "
            "early_release = booked AND occupied with session length < booking duration. "
            "4. For Meraki MV-based people counting (a separate path) configure the Meraki "
            "Dashboard 'mv_people_counting' webhook alert and ingest via the "
            "Splunk_TA_cisco_meraki Webhook Logs (HEC) input (sourcetype=meraki:webhook); "
            "the polled Meraki TA does NOT expose people-count metrics. 5. Trend no-show rate "
            "by floor / building / day-of-week to inform desk-and-room policy."
        ),
        "app": (
            "`Cisco Webex Add-on` (Splunkbase #5781), Cisco Spaces Add-On (Splunkbase #8485), "
            "calendar API integration, and (optional, webhook-only) `Cisco Meraki Add-on "
            "for Splunk` (Splunkbase 5580) for MV camera people-counting"
        ),
    },

    # WLC + Meraki dual-app UCs — clean up the misleading "Meraki TA" claim.
    # The SPL queries cisco:wlc, NOT Meraki. We add an honest Meraki path
    # in implementation pointing at the right Meraki TA inputs.

    "content/cat-05-network-infrastructure/UC-5.4.2.json": {
        "implementation": (
            "1. Configure SC4S to receive Cisco WLC (AireOS / Catalyst 9800) syslog. "
            "2. The query above counts association/authentication failures by AP, SSID, "
            "and reason from the WLC syslog. 3. If you are running Meraki MR instead of WLC: "
            "use sourcetype=\"meraki\" type=events with type=disassociation / type=8021x_eap_failure "
            "/ type=wpa_deauth and extract reason / vap / identity via rex (see UC-5.4.12 for "
            "the canonical Meraki SPL pattern)."
        ),
        "app": (
            "`Splunk Add-on for Cisco WLC` for WLC syslog, OR `Cisco Meraki Add-on for "
            "Splunk` (Splunkbase 5580) + SC4S Meraki vendor pack if running Meraki MR — see "
            "implementation note for the alternate SPL."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.4.json": {
        "implementation": (
            "1. Configure SC4S to receive Cisco WLC syslog. 2. The query above surfaces "
            "rogue AP detections with detecting_ap, channel, and rogue_mac. 3. If you are "
            "running Meraki MR instead: enable the Air Marshal input "
            "(sourcetype=meraki:airmarshal) in Splunk_TA_cisco_meraki and filter on "
            "type=rogue_ssid_detected / type=ssid_spoofing_detected — both come with "
            "ssid, bssid, src, dst, channel, rssi fields."
        ),
        "app": (
            "`Splunk Add-on for Cisco WLC` for WLC syslog, OR `Cisco Meraki Add-on for "
            "Splunk` (Splunkbase 5580) Air Marshal input if running Meraki MR — see "
            "implementation note."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.6.json": {
        "implementation": (
            "1. Configure SC4S to receive Cisco WLC syslog. 2. The query above counts radar / "
            "DFS / interference / channel-change events by AP and channel. 3. If you are "
            "running Meraki MR instead: configure a Meraki Dashboard alert profile for "
            "'radar detected (DFS)' and 'high channel utilization' and ingest via the "
            "Splunk_TA_cisco_meraki Webhook Logs (HEC) input (sourcetype=meraki:webhook). "
            "Polled API does not expose continuous channel-utilization counters."
        ),
        "app": (
            "`Splunk Add-on for Cisco WLC` for WLC syslog, OR `Cisco Meraki Add-on for "
            "Splunk` (Splunkbase 5580) Webhook Logs input if running Meraki MR — see "
            "implementation note."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.9.json": {
        "implementation": (
            "1. Configure SC4S to receive Cisco WLC syslog. 2. The query uses transaction "
            "to group roam events per client_mac and counts roams per client. 3. If you are "
            "running Meraki MR instead: use sourcetype=\"meraki\" type=events with "
            "type=association / type=disassociation, group by aid (Meraki association id) and "
            "look for clients seen across many APs in a short time (see UC-5.4.14 for the "
            "canonical Meraki SPL pattern). The Meraki syslog payload does not include the "
            "client MAC directly; correlation has to be done via the API-side Wireless "
            "Packet Loss by Device input or Meraki Dashboard."
        ),
        "app": (
            "`Splunk Add-on for Cisco WLC` for WLC syslog, OR `Cisco Meraki Add-on for "
            "Splunk` (Splunkbase 5580) + SC4S Meraki vendor pack if running Meraki MR — see "
            "implementation note."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.10.json": {
        "implementation": (
            "1. Configure SC4S to receive Cisco WLC syslog. 2. The query uses rex to extract "
            "Snort-style signature id, signature name, and attacker MAC from wIPS messages. "
            "3. If you are running Meraki MR instead: enable the Air Marshal input "
            "(sourcetype=meraki:airmarshal) and filter on threat-related event types — "
            "Meraki MR does not have Snort-style wIPS signatures but Air Marshal covers "
            "rogue / spoof / containment events."
        ),
        "app": (
            "`Splunk Add-on for Cisco WLC` for WLC wIPS syslog, OR `Cisco Meraki Add-on for "
            "Splunk` (Splunkbase 5580) Air Marshal input if running Meraki MR — see "
            "implementation note."
        ),
    },

    "content/cat-05-network-infrastructure/UC-5.4.11.json": {
        "implementation": (
            "1. Configure SC4S to receive Cisco WLC syslog. 2. The query categorises clients "
            "by 2.4GHz vs 5GHz from the channel value in association events. 3. If you are "
            "running Meraki MR instead: enable the Webhook Logs (HEC) input in "
            "Splunk_TA_cisco_meraki and configure a 'client connection changed' alert in "
            "Meraki Dashboard. The webhook alertData.band field carries 2.4GHz / 5GHz / 6GHz "
            "(see UC-5.4.19 for the canonical Meraki SPL pattern). Polled Meraki TA does not "
            "expose per-client band information."
        ),
        "app": (
            "`Splunk Add-on for Cisco WLC` for WLC syslog, OR `Cisco Meraki Add-on for "
            "Splunk` (Splunkbase 5580) Webhook Logs input if running Meraki MR — see "
            "implementation note."
        ),
    },

    "content/cat-22-regulatory-compliance/UC-22.11.26.json": {
        "implementation": (
            "1. Classify SSIDs that can see payment devices via pci_store_ssid.csv "
            "(carries_pos=true). 2. The query matches legacy / weak encryption strings (open, "
            "OWE, WEP, WPA without 2/3, TKIP) in WLC controller syslog. 3. Exclude guest "
            "SSIDs with captive portal if physically isolated. 4. Integrate with store opening "
            "checklist; weekly store ops digest. 5. If you are running Meraki MR instead of "
            "WLC: SSID encryption configuration is NOT in Meraki syslog — pull it via the "
            "Splunk_TA_cisco_meraki Audit input (sourcetype=meraki:audit) filtered to "
            "page='SSID' and inspect the newValue JSON for the encryptionMode field, OR scrape "
            "GET /networks/{networkId}/wireless/ssids with a custom modular input. Indexes "
            "required: index=wireless; Sourcetypes: sourcetype=wlan:controller; Lookups: "
            "pci_store_ssid, pci_store_ssid.csv."
        ),
        "app": (
            "`Splunk Add-on for Cisco WLC` for AireOS/Catalyst 9800 WLAN syslog, OR `Cisco "
            "Meraki Add-on for Splunk` (Splunkbase 5580) Audit input if running Meraki MR "
            "(see implementation note)."
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
