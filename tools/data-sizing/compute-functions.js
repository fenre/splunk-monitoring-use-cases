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

  return {
    endpoint_legacy_v1:   endpoint_legacy_v1,
    protocol_legacy_v1:   protocol_legacy_v1,
    fw_palo_alto_ngfw_v1: fw_palo_alto_ngfw_v1
  };
})();

// Node test environment shim — `module.exports` lets `node --test` import.
if (typeof module !== "undefined" && module.exports) {
  module.exports = global.COMPUTE_FUNCTIONS || window.COMPUTE_FUNCTIONS;
}
