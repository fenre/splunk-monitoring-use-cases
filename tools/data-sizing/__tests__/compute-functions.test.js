/* node --test runner. Loads compute-functions.js in a fake-browser env. */
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

global.window = {};
require(path.join(__dirname, '..', 'compute-functions.js'));
const COMPUTE = global.window.COMPUTE_FUNCTIONS;

test('endpoint_legacy_v1 typical', () => {
  // Engine applies driver.profilePresets[profile] before calling the
  // compute function, so the test passes the profile-resolved values
  // directly as driver inputs (no `_v1_tables`, no profile arg).
  const out = COMPUTE.endpoint_legacy_v1({
    endpoints: 10,
    eps_per_endpoint: 5,
    bytes_per_event: 800
  });
  assert.equal(out.eps, 50);
  assert.equal(out.bytesPerEvent, 800);
});

test('endpoint_legacy_v1 edge-low (1 endpoint, low profile-resolved values)', () => {
  const out = COMPUTE.endpoint_legacy_v1({
    endpoints: 1,
    eps_per_endpoint: 1,
    bytes_per_event: 200
  });
  assert.equal(out.eps, 1);
  assert.equal(out.bytesPerEvent, 200);
});

test('endpoint_legacy_v1 edge-high (100 endpoints, high profile-resolved values)', () => {
  const out = COMPUTE.endpoint_legacy_v1({
    endpoints: 100,
    eps_per_endpoint: 50,
    bytes_per_event: 3000
  });
  assert.equal(out.eps, 5000);
  assert.equal(out.bytesPerEvent, 3000);
});

test('protocol_legacy_v1 typical', () => {
  const out = COMPUTE.protocol_legacy_v1({
    tag_count: 100,
    poll_interval_sec: 10,
    deadband_ratio: 0.0,
    bytes_per_tag: 250
  });
  assert.equal(out.eps, 10);
  assert.equal(out.bytesPerEvent, 250);
});

test('protocol_legacy_v1 edge-low (1 tag, 5-min poll, no dedup)', () => {
  const out = COMPUTE.protocol_legacy_v1({
    tag_count: 1, poll_interval_sec: 300, deadband_ratio: 0.0,
    bytes_per_tag: 100
  });
  assert.ok(out.eps > 0 && out.eps < 0.01);
  assert.equal(out.bytesPerEvent, 100);
});

test('protocol_legacy_v1 edge-high (10k tags, 1-s poll, no dedup)', () => {
  const out = COMPUTE.protocol_legacy_v1({
    tag_count: 10000, poll_interval_sec: 1, deadband_ratio: 0.0,
    bytes_per_tag: 500
  });
  assert.equal(out.eps, 10000);
  assert.equal(out.bytesPerEvent, 500);
});

test('protocol_legacy_v1 deadband halves output at 0.5 ratio', () => {
  const base = COMPUTE.protocol_legacy_v1({
    tag_count: 100, poll_interval_sec: 10, deadband_ratio: 0.0,
    bytes_per_tag: 250
  });
  const halved = COMPUTE.protocol_legacy_v1({
    tag_count: 100, poll_interval_sec: 10, deadband_ratio: 0.5,
    bytes_per_tag: 250
  });
  assert.equal(halved.eps, base.eps / 2);
});

// ── fw_palo_alto_ngfw_v1 ─────────────────────────────────────────────
// The engine resolves throughput_gbps from driver.profilePresets[profile]
// before calling the compute fn, so each test passes the already-resolved
// driver values. log_profile is an enum picked by the user, not a profile
// preset, so its value is independent of the low/typical/high axis.

test('fw_palo_alto_ngfw_v1 typical (1 Gbps, traffic+threat)', () => {
  const out = COMPUTE.fw_palo_alto_ngfw_v1({
    throughput_gbps: 1.0, log_profile: 'traffic+threat'
  });
  assert.equal(out.eps, 4500);
  assert.equal(out.bytesPerEvent, 1800);
});

test('fw_palo_alto_ngfw_v1 edge-low (0.1 Gbps, traffic-only)', () => {
  const out = COMPUTE.fw_palo_alto_ngfw_v1({
    throughput_gbps: 0.1, log_profile: 'traffic-only'
  });
  assert.equal(Math.round(out.eps), 315);  // 0.1 * 4500 * 0.70
  assert.equal(out.bytesPerEvent, 1200);
});

test('fw_palo_alto_ngfw_v1 edge-high (10 Gbps, full subscriptions)', () => {
  const out = COMPUTE.fw_palo_alto_ngfw_v1({
    throughput_gbps: 10, log_profile: 'traffic+threat+url+dns+wildfire'
  });
  assert.equal(Math.round(out.eps), 94500);  // 10 * 4500 * 2.10
  assert.equal(out.bytesPerEvent, 2400);
});

test('fw_palo_alto_ngfw_v1 unknown log_profile defaults to traffic+threat', () => {
  const out = COMPUTE.fw_palo_alto_ngfw_v1({
    throughput_gbps: 1.0, log_profile: 'invalid-string'
  });
  assert.equal(out.eps, 4500);
  assert.equal(out.bytesPerEvent, 1800);
});

test('fw_palo_alto_ngfw_v1 missing throughput defaults to 1 Gbps', () => {
  const out = COMPUTE.fw_palo_alto_ngfw_v1({ log_profile: 'traffic+threat' });
  assert.equal(out.eps, 4500);
});

// ── Tier-1/2 calibrated compute functions (Tasks 12–35) ──────────────
// Each test verifies the typical-profile contract and one edge case
// so a future formula tweak that drops a multiplier or enum branch
// fails the gate. Profile resolution is engine-side, so tests pass
// already-resolved driver values directly.

// sec_ngfw_fortinet_v1
test('sec_ngfw_fortinet_v1 typical (1 Gbps, +ips)', () => {
  const out = COMPUTE.sec_ngfw_fortinet_v1({ throughput_gbps: 1.0, utm_features: '+ips' });
  assert.equal(out.eps, 3500);
  assert.equal(out.bytesPerEvent, 1400);
});
test('sec_ngfw_fortinet_v1 base profile drops to 60% (1 Gbps)', () => {
  const out = COMPUTE.sec_ngfw_fortinet_v1({ throughput_gbps: 1.0, utm_features: 'base' });
  assert.equal(out.eps, 2100);
  assert.equal(out.bytesPerEvent, 900);
});

// sec_fw_cisco_v1
test('sec_fw_cisco_v1 typical (1 Gbps, ftd-syslog)', () => {
  const out = COMPUTE.sec_fw_cisco_v1({ throughput_gbps: 1.0, mode: 'ftd-syslog' });
  assert.equal(out.eps, 3000);
  assert.equal(out.bytesPerEvent, 1200);
});
test('sec_fw_cisco_v1 ASA syslog is compact (1 Gbps)', () => {
  const out = COMPUTE.sec_fw_cisco_v1({ throughput_gbps: 1.0, mode: 'asa-syslog' });
  assert.equal(out.eps, 2000);
  assert.equal(out.bytesPerEvent, 220);
});

// sec_edr_v1
test('sec_edr_v1 typical (100 endpoints, behavioural)', () => {
  const out = COMPUTE.sec_edr_v1({ endpoints: 100, telemetry_profile: 'behavioural' });
  assert.equal(out.eps, 50);
  assert.equal(out.bytesPerEvent, 1500);
});
test('sec_edr_v1 full-process is 100x summary', () => {
  const summary = COMPUTE.sec_edr_v1({ endpoints: 100, telemetry_profile: 'summary' });
  const full    = COMPUTE.sec_edr_v1({ endpoints: 100, telemetry_profile: 'full-process' });
  assert.equal(full.eps / summary.eps, 100);
});

// sec_ids_cybervision_v1
test('sec_ids_cybervision_v1 typical (100 devices, summary)', () => {
  const out = COMPUTE.sec_ids_cybervision_v1({ monitored_devices: 100, dpi_mode: 'summary' });
  assert.equal(out.eps, 5);
  assert.equal(out.bytesPerEvent, 600);
});

// sec_ise_v1
test('sec_ise_v1 typical (5000/h auths, accounting yes)', () => {
  const out = COMPUTE.sec_ise_v1({ authentications_per_hour: 5000, accounting_enabled: 'yes' });
  // 5000/3600 * 4 = 5.5555
  assert.ok(Math.abs(out.eps - (5000 / 3600) * 4) < 1e-9);
  assert.equal(out.bytesPerEvent, 1200);
});
test('sec_ise_v1 no accounting drops bpe to 800', () => {
  const out = COMPUTE.sec_ise_v1({ authentications_per_hour: 5000, accounting_enabled: 'no' });
  assert.equal(out.bytesPerEvent, 800);
});

// dsa_sec_waf_v1
test('dsa_sec_waf_v1 typical (100 rps, denied-only = 1% logged)', () => {
  const out = COMPUTE.dsa_sec_waf_v1({ requests_per_sec: 100, log_mode: 'denied-only' });
  assert.equal(out.eps, 1);
  assert.equal(out.bytesPerEvent, 2000);
});
test('dsa_sec_waf_v1 full logging captures every request', () => {
  const out = COMPUTE.dsa_sec_waf_v1({ requests_per_sec: 100, log_mode: 'full' });
  assert.equal(out.eps, 100);
});

// dsa_sec_ips_ids_v1
test('dsa_sec_ips_ids_v1 typical (1 Gbps, balanced)', () => {
  const out = COMPUTE.dsa_sec_ips_ids_v1({ inspected_throughput_gbps: 1, ruleset: 'balanced' });
  assert.ok(Math.abs(out.eps - (200 / 3600)) < 1e-9);
  assert.equal(out.bytesPerEvent, 800);
});

// dsa_it_cloud_iaas_v1
test('dsa_it_cloud_iaas_v1 typical (1M calls/month, 5% data events)', () => {
  const out = COMPUTE.dsa_it_cloud_iaas_v1({ monthly_api_calls: 1e6, data_event_pct: 5 });
  const expected = (1e6 / (30 * 86400)) * (1 + 0.05 * 4);
  assert.ok(Math.abs(out.eps - expected) < 1e-6);
  assert.equal(out.bytesPerEvent, 1200);
});

// dsa_it_office365_v1
test('dsa_it_office365_v1 typical (100 seats, E3)', () => {
  const out = COMPUTE.dsa_it_office365_v1({ seats: 100, tier: 'e3' });
  assert.equal(out.eps, 0.5);
  assert.equal(out.bytesPerEvent, 1500);
});
test('dsa_it_office365_v1 E5 is 5x E3', () => {
  const e3 = COMPUTE.dsa_it_office365_v1({ seats: 100, tier: 'e3' });
  const e5 = COMPUTE.dsa_it_office365_v1({ seats: 100, tier: 'e5' });
  assert.equal(e5.eps / e3.eps, 5);
});

// dsa_it_sso_v1
test('dsa_it_sso_v1 typical (1000 DAU, MFA yes)', () => {
  const out = COMPUTE.dsa_it_sso_v1({ daily_active_users: 1000, mfa_enabled: 'yes' });
  assert.ok(Math.abs(out.eps - (1000 * 12 / 86400)) < 1e-9);
  assert.equal(out.bytesPerEvent, 800);
});

// it_windows_v1
test('it_windows_v1 typical (100 endpoints, advanced)', () => {
  const out = COMPUTE.it_windows_v1({ endpoints: 100, audit_policy: 'advanced' });
  assert.equal(out.eps, 50);
  assert.equal(out.bytesPerEvent, 1200);
});
test('it_windows_v1 PS transcript 40x default', () => {
  const def  = COMPUTE.it_windows_v1({ endpoints: 100, audit_policy: 'default' });
  const ps   = COMPUTE.it_windows_v1({ endpoints: 100, audit_policy: 'advanced+ps-transcript' });
  assert.equal(ps.eps / def.eps, 40);
});

// it_windows_dc_v1
test('it_windows_dc_v1 typical (5000/h, success-only)', () => {
  const out = COMPUTE.it_windows_dc_v1({ users_authenticated_per_hour: 5000, audit_logon_level: 'success-only' });
  assert.ok(Math.abs(out.eps - (5000 * 2 / 3600)) < 1e-9);
  assert.equal(out.bytesPerEvent, 1200);
});

// it_linux_v1
test('it_linux_v1 typical (100 endpoints, auditd yes, CIS)', () => {
  const out = COMPUTE.it_linux_v1({ endpoints: 100, auditd_enabled: 'yes', auditd_ruleset_size: 'cis' });
  assert.equal(out.eps, 200);
  assert.equal(out.bytesPerEvent, 800);
});
test('it_linux_v1 auditd off drops eps 20x and bpe to 400', () => {
  const out = COMPUTE.it_linux_v1({ endpoints: 100, auditd_enabled: 'no', auditd_ruleset_size: 'cis' });
  assert.equal(out.eps, 10);
  assert.equal(out.bytesPerEvent, 400);
});

// dsa_it_database_v1
test('dsa_it_database_v1 typical (100 tps, dml+ddl)', () => {
  const out = COMPUTE.dsa_it_database_v1({ transactions_per_sec: 100, audit_level: 'dml+ddl' });
  assert.equal(out.eps, 5);
  assert.equal(out.bytesPerEvent, 600);
});

// dsa_it_webserver_v1
test('dsa_it_webserver_v1 typical (100 rps, combined)', () => {
  const out = COMPUTE.dsa_it_webserver_v1({ requests_per_sec: 100, log_format: 'combined' });
  assert.equal(out.eps, 100);
  assert.equal(out.bytesPerEvent, 350);
});
test('dsa_it_webserver_v1 json-rich tripled bpe', () => {
  const out = COMPUTE.dsa_it_webserver_v1({ requests_per_sec: 100, log_format: 'json-rich' });
  assert.equal(out.bytesPerEvent, 1100);
});

// net_netflow_v1
test('net_netflow_v1 typical (1000 fps, netflow-v9)', () => {
  const out = COMPUTE.net_netflow_v1({ aggregated_flows_per_sec: 1000, format: 'netflow-v9' });
  assert.equal(out.eps, 1000);
  assert.equal(out.bytesPerEvent, 150);
});

// net_meraki_v1
test('net_meraki_v1 typical (50 devices, events+flows)', () => {
  const out = COMPUTE.net_meraki_v1({ devices: 50, syslog_features: 'events+flows' });
  assert.equal(out.eps, 25);
  assert.equal(out.bytesPerEvent, 600);
});

// dsa_net_loadbalancer_v1
test('dsa_net_loadbalancer_v1 typical (100 rps, summary)', () => {
  const out = COMPUTE.dsa_net_loadbalancer_v1({ requests_per_sec: 100, log_level: 'summary' });
  assert.equal(out.eps, 10);
  assert.equal(out.bytesPerEvent, 500);
});

// dsa_net_vpn_v1
test('dsa_net_vpn_v1 typical (100 sessions, disconnect alerts yes)', () => {
  const out = COMPUTE.dsa_net_vpn_v1({ concurrent_sessions: 100, disconnect_alerts_enabled: 'yes' });
  assert.equal(out.eps, 1);
  assert.equal(out.bytesPerEvent, 600);
});

// proto_opcua_v1
test('proto_opcua_v1 typical (500 tags, 1000 ms, 0.6 deadband)', () => {
  const out = COMPUTE.proto_opcua_v1({ tag_count: 500, publish_interval_ms: 1000, deadband_ratio: 0.6 });
  assert.equal(out.eps, 200);  // 500 * 1000/1000 * 0.4
  assert.equal(out.bytesPerEvent, 350);
});

// proto_modbus_v1 — second worked example, spec §6 verbatim
test('proto_modbus_v1 typical (500 tags, 30s, 0.4 deadband)', () => {
  const out = COMPUTE.proto_modbus_v1({ tag_count: 500, poll_interval_sec: 30, deadband_ratio: 0.4 });
  // 500/30 * 0.6 = 10
  assert.equal(out.eps, 10);
  assert.equal(out.bytesPerEvent, 280);
});
test('proto_modbus_v1 deadband=0 emits raw poll rate', () => {
  const out = COMPUTE.proto_modbus_v1({ tag_count: 500, poll_interval_sec: 30, deadband_ratio: 0 });
  assert.ok(Math.abs(out.eps - (500 / 30)) < 1e-9);
});

// proto_mqtt_v1
test('proto_mqtt_v1 typical (100 topics, 1 msg/s/topic, QoS 0)', () => {
  const out = COMPUTE.proto_mqtt_v1({ topic_count: 100, messages_per_topic_per_sec: 1, qos: 0 });
  assert.equal(out.eps, 100);
  assert.equal(out.bytesPerEvent, 250);
});
test('proto_mqtt_v1 QoS 2 adds packet ack overhead', () => {
  const out = COMPUTE.proto_mqtt_v1({ topic_count: 100, messages_per_topic_per_sec: 1, qos: 2 });
  assert.equal(out.bytesPerEvent, 310);
});

// proto_bacnet_v1
test('proto_bacnet_v1 typical (50 devices, 20 obj/dev, 60s, 0.6 deadband)', () => {
  const out = COMPUTE.proto_bacnet_v1({ device_count: 50, polled_objects_per_device: 20, poll_interval_sec: 60, deadband_ratio: 0.6 });
  // (50 * 20 / 60) * 0.4 = 6.6667
  assert.ok(Math.abs(out.eps - ((50 * 20 / 60) * 0.4)) < 1e-9);
  assert.equal(out.bytesPerEvent, 320);
});

// proto_snmp_v1
test('proto_snmp_v1 typical (100 OIDs, 60s, v2c)', () => {
  const out = COMPUTE.proto_snmp_v1({ oid_count: 100, poll_interval_sec: 60, version: 'v2c' });
  assert.ok(Math.abs(out.eps - (100 / 60)) < 1e-9);
  assert.equal(out.bytesPerEvent, 120);
});
test('proto_snmp_v1 v3 grows bpe with auth/priv headers', () => {
  const out = COMPUTE.proto_snmp_v1({ oid_count: 100, poll_interval_sec: 60, version: 'v3' });
  assert.equal(out.bytesPerEvent, 180);
});
