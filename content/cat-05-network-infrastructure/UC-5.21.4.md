<!-- AUTO-GENERATED from UC-5.21.4.json — DO NOT EDIT -->

---
id: "5.21.4"
title: "NTP Authentication Failures on Network Devices"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.21.4 · NTP Authentication Failures on Network Devices

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch for someone trying to trick our network equipment into using a fake clock. Just like you would not let a stranger reset all the clocks in your house, we make sure our devices only accept time updates from trusted sources. If someone unauthorized tries, we catch it right away.*

---

## Description

Detects NTP authentication failures on network devices, which indicate either misconfigured NTP keys, expired key rotation, or an attacker attempting to inject false time via a rogue NTP server. Time-shifting attacks are a known technique (MITRE ATT&CK T1498/T1565) to disrupt Kerberos, DNSSEC, certificate validation, and forensic timelines.

## Value

NTP authentication is the only defense against rogue NTP servers poisoning device clocks. A successful time-shift attack shifts a device's clock by hours, silently breaking Kerberos (5-minute tolerance), expiring or prematurely validating certificates, and making log correlation across devices impossible. Monitoring authentication failures catches both operational issues (key mismatches after rotation) and active attacks before the clock is compromised.

## Implementation

Monitor NTP authentication failure syslog events. Track failures by source NTP server and device. Alert on patterns suggesting rogue NTP injection attempts.

## Detailed Implementation

### Prerequisites
- NTP authentication configured on network devices:
```
ntp authenticate
ntp authentication-key 1 md5 <secret-key>
ntp trusted-key 1
ntp server 10.1.1.1 key 1
```
- Without `ntp authenticate`, devices accept time from any source without verification — this UC requires authentication to be enabled.
- Syslog from devices flowing to Splunk via TA.

### Step 1 — Verify NTP auth events are being generated
```spl
index=network sourcetype="cisco:ios" NTP auth earliest=-7d
| stats count by host, mnemonic
```
If zero results, NTP authentication may not be enabled or no failures have occurred. To test, temporarily configure a wrong key on one device.

### Step 2 — Create monitoring search
The primary search (above) tracks authentication failures by source.

**Rogue NTP server detection (auth failures from unexpected sources):**
```spl
index=network sourcetype="cisco:ios" NTP auth earliest=-24h
| rex field=_raw "(?:peer|server|source)\s*(?<ntp_source>[\d\.]+|[0-9a-fA-F:]+)"
| lookup authorized_ntp_servers.csv ntp_server as ntp_source OUTPUT authorized
| where NOT authorized="yes"
| stats count as attempts dc(host) as affected_devices by ntp_source
| sort -attempts
```

**Key rotation compliance (detect stale keys):**
```spl
index=network sourcetype="cisco:ios" NTP auth earliest=-1h
| stats count as failures by host
| where failures > 0
| eval action="Check NTP key configuration — may need rotation"
```

### Step 3 — Validate
(a) Deliberately misconfigure an NTP key on a test device. Verify `%NTP-4-AUTH_FAIL` events appear in Splunk.
(b) Verify the `authorized_ntp_servers.csv` lookup contains all legitimate NTP servers.
(c) Check `show ntp associations detail` — the `authenticated` column should show `yes` for all configured peers.

### Step 4 — Operationalize
Dashboard ("NTP Security"):
- Row 1 — Single-value: total auth failures in 24h (red if >0), unique rogue sources detected.
- Row 2 — Table: ntp_source, affected devices, failure count, first/last seen.
- Row 3 — Timeline: auth failure events over 7 days.

Alerting:
- Auth failures from unknown NTP source: Critical — potential rogue NTP injection.
- >10 auth failures from known source: High — key mismatch, investigate key rotation status.
- Any auth failure sustained >1 hour: investigate immediately.

### Step 5 — Troubleshooting
- **Auth failures after key rotation.** If NTP keys were rotated and not all devices received the new key, auth failures are expected. Verify key distribution is complete across fleet.
- **Auth failures from legitimate server.** Key ID mismatch — verify both sides use the same key ID and key string. Check `show ntp associations detail` for the `key` field.
- **No NTP auth at all configured.** Many organizations skip NTP authentication. Without it, any device on the network can shift clocks via rogue NTP packets. This UC requires authentication to be enabled first.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="cisco:iosxe" OR sourcetype="juniper:junos:structured") earliest=-24h
  ("NTP" AND ("auth" OR "authentication") AND ("fail" OR "mismatch" OR "reject" OR "denied"))
| rex field=_raw "(?:peer|server|source)\s*(?<ntp_source>[\d\.]+|[0-9a-fA-F:]+)"
| stats count as auth_failures earliest(_time) as first_seen latest(_time) as last_seen by host, ntp_source
| eval severity=case(
    auth_failures > 10, "CRITICAL — " . auth_failures . " NTP auth failures from " . ntp_source,
    auth_failures > 3, "HIGH — " . auth_failures . " NTP auth failures",
    1=1, "MEDIUM — NTP auth failure detected")
| sort -auth_failures
```

## Visualization

(1) Single-value: auth failures (red >0). (2) Table: failures by source and device. (3) Timeline: auth failure events.

## Known False Positives

**Key rotation window.** During NTP key rotation, devices receiving the new key before the NTP server (or vice versa) will log auth failures. This is a brief operational window — typically <15 minutes during coordinated rotation.

**Stale configuration.** Devices with outdated NTP server configurations may attempt to authenticate against servers that have been decommissioned. Clean up NTP configurations during regular audits.

## References

- [RFC 5905 — NTP Version 4 (Authentication)](https://www.rfc-editor.org/rfc/rfc5905#section-7.3)
- [NIST SP 800-119 — NTP Security Considerations](https://csrc.nist.gov/publications/detail/sp/800-119/final)
- [MITRE ATT&CK — T1498 Network Denial of Service](https://attack.mitre.org/techniques/T1498/)
