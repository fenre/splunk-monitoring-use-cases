/**
 * Data-Sizing v2 compute-function registry.
 *
 * Each function is a pure (driverValues, profile) -> {eps, bytesPerEvent}.
 * No DOM, no network, no Date.now(), no Math.random().
 *
 * Versioning: a formula change ships as _vN+1; the old _vN stays in this
 * file so saved share URLs that explicitly pin a version keep computing.
 */
window.COMPUTE_FUNCTIONS = (function () {
  // ── Legacy fallbacks used by `calibration: "pending"` sources ────────
  // These re-implement v1's math by reading the ex-v1 lookup tables as
  // ORDINARY drivers with `profilePresets`. The migrator emits drivers
  // `endpoints`, `eps_per_endpoint`, `bytes_per_event` (endpoint sources)
  // or `tag_count`, `poll_interval_sec`, `deadband_ratio`, `bytes_per_tag`
  // (protocol sources). Profile switching is handled engine-side by
  // reading `driver.profilePresets[profile]`, so the compute function
  // itself is profile-agnostic. No `_v1_tables` field exists — this
  // matches the uniform-driver design (plan amendment 1).

  function endpoint_legacy_v1(d) {
    var endpoints      = (d.endpoints        !== undefined ? d.endpoints        : 1);
    var epsPerEndpoint = (d.eps_per_endpoint !== undefined ? d.eps_per_endpoint : 1);
    var bytesPerEvent  = (d.bytes_per_event  !== undefined ? d.bytes_per_event  : 500);
    return { eps: endpoints * epsPerEndpoint, bytesPerEvent: bytesPerEvent };
  }

  function protocol_legacy_v1(d) {
    var tags         = (d.tag_count         !== undefined ? d.tag_count         : 1);
    var poll         = (d.poll_interval_sec !== undefined && d.poll_interval_sec > 0
                         ? d.poll_interval_sec : 60);
    var bytesPerTag  = (d.bytes_per_tag     !== undefined ? d.bytes_per_tag     : 300);
    var dedup        = (d.deadband_ratio    !== undefined ? (1 - d.deadband_ratio) : 1.0);
    return { eps: (tags / poll) * dedup, bytesPerEvent: bytesPerTag };
  }

  // ── Calibrated compute functions ─────────────────────────────────────

  // Palo Alto NGFW. Derived from PAN-OS 11 log-storage sizing tables
  // cross-referenced against Splunk_TA_paloalto v9.x default props.conf
  // per-sourcetype rates. baseEpsPerGbps is a sustained-throughput
  // proxy; log_profile selects the multiplier for the user-enabled
  // subscription mix (Threat, URL, DNS-Security, WildFire each add a
  // distinct stream). bytes/event reflects the dominant subset.
  function fw_palo_alto_ngfw_v1(d) {
    var baseEpsPerGbps = 4500;
    var profileMultipliers = {
      "traffic-only":                    { eps: 0.70, bytesPerEvent: 1200 },
      "traffic+threat":                  { eps: 1.00, bytesPerEvent: 1800 },
      "traffic+threat+url":              { eps: 1.45, bytesPerEvent: 2100 },
      "traffic+threat+url+dns+wildfire": { eps: 2.10, bytesPerEvent: 2400 }
    };
    var m = profileMultipliers[d.log_profile] || profileMultipliers["traffic+threat"];
    var gbps = (d.throughput_gbps !== undefined ? d.throughput_gbps : 1.0);
    return {
      eps:           gbps * baseEpsPerGbps * m.eps,
      bytesPerEvent: m.bytesPerEvent
    };
  }

  // Fortinet FortiGate. UTM-style appliance — CEF/syslog. Throughput
  // is the inspected sustained Gbps; utm_features picks the enabled
  // inspection bundle. Base EPS derived from FortiAnalyzer sizing
  // guide; bytes-per-event derived from Splunkbase Fortinet FortiGate
  // Add-on default CEF parser.
  function sec_ngfw_fortinet_v1(d) {
    var base = 3500;
    var m = {
      "base":                  { eps: 0.60, bytesPerEvent:  900 },
      "+ips":                  { eps: 1.00, bytesPerEvent: 1400 },
      "+ips+webfilter":        { eps: 1.40, bytesPerEvent: 1700 },
      "+ips+webfilter+av":     { eps: 1.80, bytesPerEvent: 2000 }
    };
    var sel = m[d.utm_features] || m["+ips"];
    var gbps = (d.throughput_gbps !== undefined ? d.throughput_gbps : 1.0);
    return { eps: gbps * base * sel.eps, bytesPerEvent: sel.bytesPerEvent };
  }

  // Cisco Secure Firewall (FTD + ASA). ASA syslog is famously compact
  // (~200 B compact CSV); FTD security events via syslog/eStreamer are
  // much richer per-event (1.2–2.5 KB with full metadata).
  function sec_fw_cisco_v1(d) {
    var profile = {
      "asa-syslog":     { epsPerGbps: 2000, bytesPerEvent:  220 },
      "ftd-syslog":     { epsPerGbps: 3000, bytesPerEvent: 1200 },
      "ftd-estreamer":  { epsPerGbps: 4000, bytesPerEvent: 2500 }
    };
    var sel = profile[d.mode] || profile["ftd-syslog"];
    var gbps = (d.throughput_gbps !== undefined ? d.throughput_gbps : 1.0);
    return { eps: gbps * sel.epsPerGbps, bytesPerEvent: sel.bytesPerEvent };
  }

  // EDR (CrowdStrike / SentinelOne / Microsoft Defender / Carbon Black).
  // Cross-vendor average: process telemetry density varies by 10x
  // across products in the same tier; eps_per_endpoint reflects the
  // dominant streaming-detection mode for each profile.
  function sec_edr_v1(d) {
    var profile = {
      "summary":       { epsPerEndpoint: 0.05, bytesPerEvent:  500 },
      "behavioural":   { epsPerEndpoint: 0.50, bytesPerEvent: 1500 },
      "full-process":  { epsPerEndpoint: 5.00, bytesPerEvent: 4000 }
    };
    var sel = profile[d.telemetry_profile] || profile["behavioural"];
    var endpoints = (d.endpoints !== undefined ? d.endpoints : 100);
    return { eps: endpoints * sel.epsPerEndpoint, bytesPerEvent: sel.bytesPerEvent };
  }

  // Cisco Cyber Vision. Passive OT DPI sensor — emits a steady
  // components + flows stream per monitored device. Summary mode
  // emits change events only; full mode emits per-flow telemetry.
  function sec_ids_cybervision_v1(d) {
    var profile = {
      "summary": { epsPerDevice: 0.05, bytesPerEvent:  600 },
      "full":    { epsPerDevice: 0.50, bytesPerEvent: 2200 }
    };
    var sel = profile[d.dpi_mode] || profile["summary"];
    var dev = (d.monitored_devices !== undefined ? d.monitored_devices : 100);
    return { eps: dev * sel.epsPerDevice, bytesPerEvent: sel.bytesPerEvent };
  }

  // Cisco ISE. Authentications/hour drives base EPS (each auth →
  // ~3 RADIUS events). When accounting is on, interim updates roughly
  // 4x the event count; without accounting, just auth start/stop pair.
  function sec_ise_v1(d) {
    var authPerHour = (d.authentications_per_hour !== undefined
                        ? d.authentications_per_hour : 5000);
    var authsPerSec = authPerHour / 3600;
    var accountingOn = (d.accounting_enabled === "yes");
    var eps = authsPerSec * (accountingOn ? 4 : 1);
    return { eps: eps, bytesPerEvent: accountingOn ? 1200 : 800 };
  }

  // WAF (F5 ASM / ModSecurity / AWS WAF / Cloudflare). log_mode picks
  // the fraction of HTTP requests that become Splunk events.
  function dsa_sec_waf_v1(d) {
    var rps = (d.requests_per_sec !== undefined ? d.requests_per_sec : 100);
    var profile = {
      "denied-only":              { ratio: 0.010, bytesPerEvent: 2000 },
      "denied+sampled-allowed":   { ratio: 0.100, bytesPerEvent: 1500 },
      "full":                     { ratio: 1.000, bytesPerEvent: 1200 }
    };
    var sel = profile[d.log_mode] || profile["denied-only"];
    return { eps: rps * sel.ratio, bytesPerEvent: sel.bytesPerEvent };
  }

  // Network IPS/IDS (Suricata + Snort + Cisco FTD). Alerts scale with
  // inspected throughput × tuned-rule density. "security" profile has
  // far more rules enabled than "connectivity".
  function dsa_sec_ips_ids_v1(d) {
    var gbps = (d.inspected_throughput_gbps !== undefined
                 ? d.inspected_throughput_gbps : 1.0);
    var alertsPerGbpsPerHour = {
      "connectivity": 50,
      "balanced":    200,
      "security":    800
    };
    var aph = alertsPerGbpsPerHour[d.ruleset] || alertsPerGbpsPerHour["balanced"];
    return { eps: (gbps * aph) / 3600, bytesPerEvent: 800 };
  }

  // Cloud IaaS (AWS CloudTrail + Azure Activity + GCP Audit). Management
  // events are small and constant; data-plane events (S3/Storage object
  // access, BigQuery queries) explode volume by ~4x at typical mix.
  function dsa_it_cloud_iaas_v1(d) {
    var calls = (d.monthly_api_calls !== undefined ? d.monthly_api_calls : 1e6);
    var pct = (d.data_event_pct !== undefined ? d.data_event_pct : 5);
    var amplifier = 1 + (pct / 100) * 4;  // data events ~4x mgmt size
    var eps = (calls / (30 * 86400)) * amplifier;
    return { eps: eps, bytesPerEvent: 1200 };
  }

  // Microsoft 365 / Office 365. Per-seat audit volume differs sharply
  // between E3 (Unified Audit Log base) and E5 (adds Defender XDR +
  // ATP audit streams). Volumes from Microsoft "audit log activity"
  // sizing guidance.
  function dsa_it_office365_v1(d) {
    var seats = (d.seats !== undefined ? d.seats : 100);
    var profile = {
      "e3": { epsPerSeat: 0.005, bytesPerEvent: 1500 },
      "e5": { epsPerSeat: 0.025, bytesPerEvent: 2200 }
    };
    var sel = profile[d.tier] || profile["e3"];
    return { eps: seats * sel.epsPerSeat, bytesPerEvent: sel.bytesPerEvent };
  }

  // SSO / IAM (Okta + PingFederate + Azure AD / Entra ID). Each DAU
  // emits ~6 events/day baseline (login + session + token refresh +
  // assignment). MFA roughly doubles that with factor enrolment +
  // challenge events.
  function dsa_it_sso_v1(d) {
    var dau = (d.daily_active_users !== undefined ? d.daily_active_users : 1000);
    var perUserPerDay = (d.mfa_enabled === "yes") ? 12 : 6;
    return { eps: (dau * perUserPerDay) / 86400, bytesPerEvent: 800 };
  }

  // Windows Server (Security / System logs). Default policy emits a
  // base trickle; Advanced audit policy adds object-access /
  // privilege-use detail; +PowerShell transcript can 10x volume.
  function it_windows_v1(d) {
    var endpoints = (d.endpoints !== undefined ? d.endpoints : 100);
    var profile = {
      "default":                       { epsPerEndpoint: 0.05, bytesPerEvent:  600 },
      "advanced":                      { epsPerEndpoint: 0.50, bytesPerEvent: 1200 },
      "advanced+ps-transcript":        { epsPerEndpoint: 2.00, bytesPerEvent: 3500 }
    };
    var sel = profile[d.audit_policy] || profile["default"];
    return { eps: endpoints * sel.epsPerEndpoint, bytesPerEvent: sel.bytesPerEvent };
  }

  // Windows Domain Controller. 4624 (success) / 4625 (failure) /
  // 4768/4769 (Kerberos) dominate; per-user-hour density is the
  // sizing axis. success+failure auditing roughly adds 50% events.
  function it_windows_dc_v1(d) {
    var authPerHour = (d.users_authenticated_per_hour !== undefined
                        ? d.users_authenticated_per_hour : 5000);
    var perAuth = (d.audit_logon_level === "success+failure") ? 3 : 2;
    return { eps: (authPerHour * perAuth) / 3600, bytesPerEvent: 1200 };
  }

  // Linux Server (syslog + auth + optional auditd). auditd dominates
  // volume when enabled — minimal/CIS/full rulesets scale ~4x each
  // step. With auditd off, only base syslog/auth/daemon events count.
  function it_linux_v1(d) {
    var endpoints = (d.endpoints !== undefined ? d.endpoints : 100);
    var auditdOn = (d.auditd_enabled === "yes");
    var epsPerEndpoint;
    var bpe;
    if (!auditdOn) {
      epsPerEndpoint = 0.1;
      bpe = 400;
    } else {
      var rs = {
        "minimal": 0.5,
        "cis":     2.0,
        "full":    8.0
      };
      epsPerEndpoint = rs[d.auditd_ruleset_size] || rs["cis"];
      bpe = 800;
    }
    return { eps: endpoints * epsPerEndpoint, bytesPerEvent: bpe };
  }

  // Database (Oracle Unified Audit / MSSQL Extended Events /
  // PostgreSQL pgAudit). audit_level picks the fraction of
  // transactions that materialise as audit events.
  function dsa_it_database_v1(d) {
    var tps = (d.transactions_per_sec !== undefined ? d.transactions_per_sec : 100);
    var profile = {
      "dml-only":     { ratio: 0.01, bytesPerEvent: 500 },
      "dml+ddl":      { ratio: 0.05, bytesPerEvent: 600 },
      "full+select":  { ratio: 1.00, bytesPerEvent: 700 }
    };
    var sel = profile[d.audit_level] || profile["dml-only"];
    return { eps: tps * sel.ratio, bytesPerEvent: sel.bytesPerEvent };
  }

  // Web servers (Apache combined + nginx default + IIS W3C). One log
  // line per request; bytes/event scales with log format.
  function dsa_it_webserver_v1(d) {
    var rps = (d.requests_per_sec !== undefined ? d.requests_per_sec : 100);
    var bpe = {
      "combined":         350,
      "combined+vhost":   450,
      "json-rich":       1100
    };
    return { eps: rps, bytesPerEvent: bpe[d.log_format] || bpe["combined"] };
  }

  // NetFlow / IPFIX / sFlow. Aggregator EPS is "flows/sec emitted
  // toward the collector after dedup"; bytes/event reflects the
  // record format on the wire (NetFlow v5 is the most compact).
  function net_netflow_v1(d) {
    var fps = (d.aggregated_flows_per_sec !== undefined
                ? d.aggregated_flows_per_sec : 1000);
    var bpe = {
      "netflow-v5": 100,
      "netflow-v9": 150,
      "ipfix":      180,
      "sflow":      200
    };
    return { eps: fps, bytesPerEvent: bpe[d.format] || bpe["netflow-v9"] };
  }

  // Cisco Meraki. Per-device event density depends sharply on the
  // enabled syslog feature mix; events-only is sparse, +flows is the
  // primary network volume driver, +url adds content-filter rows.
  function net_meraki_v1(d) {
    var devices = (d.devices !== undefined ? d.devices : 50);
    var profile = {
      "events-only":             { epsPerDevice: 0.02, bytesPerEvent: 400 },
      "events+flows":            { epsPerDevice: 0.50, bytesPerEvent: 600 },
      "events+flows+url":        { epsPerDevice: 1.00, bytesPerEvent: 900 }
    };
    var sel = profile[d.syslog_features] || profile["events+flows"];
    return { eps: devices * sel.epsPerDevice, bytesPerEvent: sel.bytesPerEvent };
  }

  // Load Balancer / ADC (F5 + Citrix NetScaler + AVI). log_level picks
  // the request-to-log ratio.
  function dsa_net_loadbalancer_v1(d) {
    var rps = (d.requests_per_sec !== undefined ? d.requests_per_sec : 100);
    var profile = {
      "denied-only":   { ratio: 0.005, bytesPerEvent: 500 },
      "summary":       { ratio: 0.100, bytesPerEvent: 500 },
      "full-detail":   { ratio: 1.000, bytesPerEvent: 500 }
    };
    var sel = profile[d.log_level] || profile["summary"];
    return { eps: rps * sel.ratio, bytesPerEvent: sel.bytesPerEvent };
  }

  // VPN concentrator (Cisco AnyConnect + OpenVPN + Pulse / Ivanti).
  // EPS scales with concurrent sessions; disconnect alerts roughly
  // double the event rate via heartbeat/idle-tear-down stream.
  function dsa_net_vpn_v1(d) {
    var sessions = (d.concurrent_sessions !== undefined
                     ? d.concurrent_sessions : 100);
    var perSessionEps = (d.disconnect_alerts_enabled === "yes") ? 0.010 : 0.005;
    return { eps: sessions * perSessionEps, bytesPerEvent: 600 };
  }

  // OPC UA. Subscription publishing — server pushes updates per tag
  // each publish interval. Deadband filters quiescent tags at server.
  function proto_opcua_v1(d) {
    var tags = (d.tag_count !== undefined ? d.tag_count : 500);
    var ms = (d.publish_interval_ms !== undefined ? d.publish_interval_ms : 1000);
    if (!(ms > 0)) ms = 1000;
    var dedup = (d.deadband_ratio !== undefined ? (1 - d.deadband_ratio) : 0.7);
    return { eps: (tags * 1000 / ms) * dedup, bytesPerEvent: 350 };
  }

  // Modbus TCP / RTU. Cyclic register polling. Spec §6 verbatim.
  function proto_modbus_v1(d) {
    var tags = (d.tag_count !== undefined ? d.tag_count : 500);
    var poll = (d.poll_interval_sec !== undefined && d.poll_interval_sec > 0
                 ? d.poll_interval_sec : 30);
    var dedup = (d.deadband_ratio !== undefined ? (1 - d.deadband_ratio) : 0.6);
    return { eps: (tags / poll) * dedup, bytesPerEvent: 280 };
  }

  // MQTT pub/sub. EPS = topic_count × messages_per_topic_per_sec.
  // QoS does not change Splunk event count (only network packets),
  // but QoS 1/2 add packet identifier + ack tracking to the payload.
  function proto_mqtt_v1(d) {
    var topics = (d.topic_count !== undefined ? d.topic_count : 100);
    var rate = (d.messages_per_topic_per_sec !== undefined
                 ? d.messages_per_topic_per_sec : 1);
    var bpe = { "0": 250, "1": 280, "2": 310 };
    return { eps: topics * rate, bytesPerEvent: bpe[String(d.qos)] || bpe["0"] };
  }

  // BACnet/IP. Polled object reads per device × deadband filter.
  function proto_bacnet_v1(d) {
    var dev = (d.device_count !== undefined ? d.device_count : 50);
    var obj = (d.polled_objects_per_device !== undefined
                ? d.polled_objects_per_device : 20);
    var poll = (d.poll_interval_sec !== undefined && d.poll_interval_sec > 0
                 ? d.poll_interval_sec : 60);
    var dedup = (d.deadband_ratio !== undefined ? (1 - d.deadband_ratio) : 0.7);
    return { eps: (dev * obj / poll) * dedup, bytesPerEvent: 320 };
  }

  // SNMP (v2c / v3). OID polls per interval; v3 adds engine + auth
  // priv headers to each varbind set.
  function proto_snmp_v1(d) {
    var oids = (d.oid_count !== undefined ? d.oid_count : 100);
    var poll = (d.poll_interval_sec !== undefined && d.poll_interval_sec > 0
                 ? d.poll_interval_sec : 60);
    var bpe = (d.version === "v3") ? 180 : 120;
    return { eps: oids / poll, bytesPerEvent: bpe };
  }

  return {
    endpoint_legacy_v1:       endpoint_legacy_v1,
    protocol_legacy_v1:       protocol_legacy_v1,
    fw_palo_alto_ngfw_v1:     fw_palo_alto_ngfw_v1,
    sec_ngfw_fortinet_v1:     sec_ngfw_fortinet_v1,
    sec_fw_cisco_v1:          sec_fw_cisco_v1,
    sec_edr_v1:               sec_edr_v1,
    sec_ids_cybervision_v1:   sec_ids_cybervision_v1,
    sec_ise_v1:               sec_ise_v1,
    dsa_sec_waf_v1:           dsa_sec_waf_v1,
    dsa_sec_ips_ids_v1:       dsa_sec_ips_ids_v1,
    dsa_it_cloud_iaas_v1:     dsa_it_cloud_iaas_v1,
    dsa_it_office365_v1:      dsa_it_office365_v1,
    dsa_it_sso_v1:            dsa_it_sso_v1,
    it_windows_v1:            it_windows_v1,
    it_windows_dc_v1:         it_windows_dc_v1,
    it_linux_v1:              it_linux_v1,
    dsa_it_database_v1:       dsa_it_database_v1,
    dsa_it_webserver_v1:      dsa_it_webserver_v1,
    net_netflow_v1:           net_netflow_v1,
    net_meraki_v1:            net_meraki_v1,
    dsa_net_loadbalancer_v1:  dsa_net_loadbalancer_v1,
    dsa_net_vpn_v1:           dsa_net_vpn_v1,
    proto_opcua_v1:           proto_opcua_v1,
    proto_modbus_v1:          proto_modbus_v1,
    proto_mqtt_v1:            proto_mqtt_v1,
    proto_bacnet_v1:          proto_bacnet_v1,
    proto_snmp_v1:            proto_snmp_v1
  };
})();

// Node test environment shim — `module.exports` lets `node --test` import.
if (typeof module !== "undefined" && module.exports) {
  module.exports = global.COMPUTE_FUNCTIONS || window.COMPUTE_FUNCTIONS;
}
