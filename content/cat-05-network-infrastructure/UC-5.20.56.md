<!-- AUTO-GENERATED from UC-5.20.56.json — DO NOT EDIT -->

---
id: "5.20.56"
title: "DNSSEC Validation Failure Rate for IPv6 (AAAA) Records"
status: "verified"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.20.56 · DNSSEC Validation Failure Rate for IPv6 (AAAA) Records

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Availability &middot; **Wave:** Run &middot; **Status:** Verified

*DNSSEC is like a wax seal on a letter — it proves the letter hasn't been tampered with. When looking up new-style (IPv6) addresses, the sealed letters are bigger and sometimes get damaged in transit. If the seal is broken, the phone book service refuses to give you the address for safety — it can't be sure the address is genuine.*

---

## Description

Monitors DNSSEC validation failure rates with specific focus on AAAA record lookups to detect trust chain issues that break IPv6 name resolution. DNSSEC validation failures cause SERVFAIL responses, which from the user's perspective is indistinguishable from the domain not existing. A DNSSEC validation failure for a domain's AAAA record means IPv6 access to that domain is completely blocked, even though IPv4 (A record) access may continue to work if the A record's DNSSEC chain is intact.

## Value

DNSSEC validation failures are a silent killer for IPv6 connectivity. When a DNSSEC-signed AAAA record fails validation, the resolver returns SERVFAIL, the client cannot resolve the IPv6 address, and Happy Eyeballs falls back to IPv4. The user may not notice (thanks to fallback), but IPv6 connectivity to that domain is effectively broken. Monitoring DNSSEC validation failure rates for AAAA records specifically catches this IPv6-specific DNS failure mode and enables investigation before the issue spreads.

## Implementation

Collect DNSSEC validation events from DNS resolvers. Track validation failure rates overall and specifically for AAAA query types. Alert on elevated failure rates and on specific domains with persistent DNSSEC failures.

## Detailed Implementation

### Prerequisites
- DNSSEC validation enabled on recursive resolvers.
- Resolver logging configured to include DNSSEC validation results.
- NTP synchronisation on all resolvers (critical for DNSSEC signature validation).

### Step 1 — Configure data collection

**BIND — DNSSEC validation logging:**
```
logging {
  channel dnssec_log {
    syslog local3;
    severity info;
    print-time yes;
  };
  category dnssec { dnssec_log; };
};

options {
  dnssec-validation auto;
  dnssec-log-key-errors yes;
};
```

**Unbound — DNSSEC logging:**
```
server:
  val-log-level: 2
  log-servfail: yes
```

**BIND logs DNSSEC failures as:**
```
dnssec: info: validating example.com/AAAA: no valid signature found
dnssec: info: validating example.com/AAAA: verify failed due to bad signature (keyid=12345)
```

**Verification:**
```spl
index=network (sourcetype="named:querylog" OR sourcetype="infoblox:dns") ("dnssec" OR "validation" OR "BOGUS") earliest=-24h
| stats count by sourcetype
```

### Step 2 — Create the search and alert

**DNSSEC validation failure trending:**
```spl
index=network (sourcetype="named:querylog" OR sourcetype="infoblox:dns") earliest=-7d
  ("dnssec" OR "validation" OR "BOGUS" OR "SERVFAIL")
| eval is_dnssec_fail=if(match(_raw, "(?i)BOGUS|validation.*fail|no valid signature|verify failed"), 1, 0)
| eval is_aaaa=if(match(_raw, "\bAAAA\b"), 1, 0)
| timechart span=1h sum(is_dnssec_fail) as total_failures sum(eval(is_aaaa * is_dnssec_fail)) as aaaa_failures
```

**Domains with persistent DNSSEC failure:**
```spl
index=network (sourcetype="named:querylog" OR sourcetype="infoblox:dns") earliest=-24h
  ("BOGUS" OR "validation.*fail" OR "no valid signature" OR "verify failed")
| rex field=_raw "validating\s+(?<failed_domain>[a-zA-Z0-9.\-]+)/"
| rex field=_raw "(?<query_type>AAAA|A|MX|NS)/"
| stats count as failure_count values(query_type) as failed_types by failed_domain
| sort -failure_count
| head 20
| eval action="Investigate: check the domain's DNSSEC chain at dnsviz.net or verisignlabs.com/dnssec/"
```

**DNSSEC failure rate alert:**
```spl
index=network (sourcetype="named:querylog" OR sourcetype="infoblox:dns") earliest=-1h
| eval is_dnssec_fail=if(match(_raw, "(?i)BOGUS|validation.*fail"), 1, 0)
| stats sum(is_dnssec_fail) as failures count as total
| eval rate=round(failures / total * 100, 2)
| where rate > 1
| eval alert="DNSSEC validation failure rate: " . rate . "% (" . failures . " of " . total . " queries) — investigate trust chain issues"
```

### Step 3 — Validate
(a) **Known DNSSEC-validated domain.** Query a domain with a known-good DNSSEC chain (e.g., `dig +dnssec example.com AAAA`). Verify the AD (Authenticated Data) flag is set in the response and the resolver logs show SECURE validation.

(b) **Known DNSSEC failure.** Use the DNSSEC test domains (e.g., `dnssec-failed.org`). Verify the resolver returns SERVFAIL and the DNSSEC failure alert fires.

(c) **DNS64 + DNSSEC interaction.** If using DNS64, query a DNSSEC-signed IPv4-only domain. Verify the synthesised AAAA breaks DNSSEC validation (expected behaviour per RFC 6147 §5.5).

### Step 4 — Operationalize

**Dashboard** ("IPv6 — DNSSEC Validation Health"):
- Row 1 — Gauge: DNSSEC validation success rate.
- Row 2 — Timechart: total and AAAA-specific DNSSEC failures over 7 days.
- Row 3 — Table: domains with persistent DNSSEC failures.
- Row 4 — DNSSEC status distribution: SECURE / INSECURE / BOGUS.

**Scheduling:** Failure rate alert every 15 minutes. Domain failure analysis daily. Trending weekly.

**Runbook:**
1. Elevated failure rate: check if a major zone's DNSSEC signatures have expired. Check dnsviz.net for chain analysis.
2. Specific domain failing: contact the domain operator if it's a partner/vendor. If it's a public domain, check if the issue is known.
3. All DNSSEC failing: check resolver clock (NTP). Check trust anchor (managed-keys). Check resolver DNSSEC configuration.

### Step 5 — Troubleshooting

- **Managed trust anchors (RFC 5011)** — Modern resolvers automatically update the root trust anchor using RFC 5011 automated trust anchor rollover. If the managed keys database is corrupted, all DNSSEC validation fails. Check the managed-keys.bind file (BIND) or auto-trust-anchor-file (Unbound).

- **Negative trust anchors (NTA)** — When a domain's DNSSEC chain is broken by the domain operator and cannot be quickly fixed, resolvers can configure a Negative Trust Anchor to temporarily disable validation for that domain. This is a last-resort workaround.

- **EDNS0 buffer size and DNSSEC** — DNSSEC-signed responses are larger. If the EDNS0 buffer size is too small (default 512 bytes in legacy implementations), DNSSEC responses may be truncated. Modern resolvers use 1232 bytes (per DNS Flag Day 2020). Ensure resolvers support at least 1232-byte EDNS0 buffers.

## SPL

```spl
index=network (sourcetype="infoblox:dns" OR sourcetype="named:querylog") earliest=-24h
  ("DNSSEC" OR "validation" OR "dnssec-failed" OR "BOGUS" OR "insecure" OR "AD bit")
| eval validation_status=case(
    match(_raw, "(?i)BOGUS|validation.*fail|dnssec-fail"), "FAILED — DNSSEC validation error",
    match(_raw, "(?i)INSECURE|no DNSSEC"), "INSECURE — zone not signed",
    match(_raw, "(?i)SECURE|validated|AD"), "SECURE — DNSSEC validated",
    1=1, "unknown")
| eval query_is_aaaa=if(match(_raw, "\bAAAA\b"), 1, 0)
| stats count as total count(eval(validation_status="FAILED — DNSSEC validation error")) as failed count(eval(validation_status="SECURE — DNSSEC validated")) as secure count(eval(query_is_aaaa=1 AND validation_status="FAILED — DNSSEC validation error")) as aaaa_failed by host
| eval dnssec_failure_rate=round(failed / total * 100, 2)
```

## Visualization

(1) Gauge: DNSSEC validation success rate. (2) Timechart: DNSSEC validation failures (total and AAAA-specific) over 7 days. (3) Table: domains with persistent DNSSEC validation failures. (4) Pie chart: validation status distribution (SECURE/INSECURE/BOGUS).

## Known False Positives

**Expired DNSSEC signatures.** Zone operators who fail to re-sign their zones before RRSIG expiry cause legitimate DNSSEC validation failures. These are real failures but not caused by attacks — they are operational errors by the zone operator. The resolver is correct to fail validation.

**Clock skew.** DNSSEC signatures have inception and expiration times. If the resolver's system clock is significantly skewed, valid signatures may appear expired or not-yet-valid. Ensure NTP synchronisation on resolvers.

**Algorithm rollover.** During DNSSEC algorithm rollovers (e.g., RSA to ECDSA), there is a brief period where validators that have not updated their trust anchors may fail validation. This is a planned event.

## References

- [RFC 4033 — DNS Security Introduction and Requirements (DNSSEC overview)](https://www.rfc-editor.org/rfc/rfc4033)
- [RFC 6781 — DNSSEC Operational Practices, Version 2 (operational guidance)](https://www.rfc-editor.org/rfc/rfc6781)
- [RFC 8027 — DNSSEC Roadblock Avoidance (troubleshooting DNSSEC failures)](https://www.rfc-editor.org/rfc/rfc8027)
