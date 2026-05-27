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
