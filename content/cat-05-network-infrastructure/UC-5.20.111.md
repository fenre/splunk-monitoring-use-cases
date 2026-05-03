<!-- AUTO-GENERATED from UC-5.20.111.json — DO NOT EDIT -->

---
id: "5.20.111"
title: "IPv6 Prefix Hijack and Route Origin Validation (RPKI/ROA)"
status: "verified"
criticality: "critical"
splunkPillar: "ES"
---

# UC-5.20.111 · IPv6 Prefix Hijack and Route Origin Validation (RPKI/ROA)

> **Criticality:** Critical &middot; **Difficulty:** Advanced &middot; **Pillar:** ES &middot; **Type:** Security &middot; **Wave:** Run &middot; **Status:** Verified

*Every organisation's set of addresses (like a block of house numbers) is supposed to be announced only by the organisation that owns them. A hijacker is someone who announces your house numbers as their own, so letters meant for you go to them instead. We have a system (RPKI) that acts like a property deed — it proves who really owns each block of addresses. We watch for anyone trying to claim our addresses, and we verify the deeds for addresses we receive.*

---

## Description

Detects IPv6 prefix hijacking through BGP monitoring: unauthorized origin AS changes, more-specific prefix injections, and RPKI/ROA validation failures. Prefix hijacking is one of the most dangerous attacks on IPv6 infrastructure — it diverts traffic to attacker-controlled routers for interception, credential theft, or service impersonation. RPKI/ROA validation is the primary defense.

## Value

IPv6 prefix hijacking has been used in real-world attacks for cryptocurrency theft (2018 MyEtherWallet attack via AWS Route 53), traffic surveillance, and spam routing. RPKI coverage for IPv6 is still maturing — many prefixes lack ROAs. This UC provides early detection of hijacking attempts by monitoring BGP update anomalies and RPKI validation results, enabling rapid response before significant traffic diversion occurs.

## Implementation

Monitor BGP updates for IPv6 prefix origin changes and RPKI validation failures. Maintain a list of authorised origin ASes for your prefixes. Alert on any unauthorised origin or RPKI-invalid announcement.

## Detailed Implementation

### Prerequisites
- BGP peering with full or partial IPv6 routing table.
- RPKI validator (Routinator, rpki-client, RIPE Validator) deployed.
- BGP logging enabled on border routers.

### Step 1 — Configure RPKI validation

**Deploy RPKI validator (Routinator):**
```bash
routinator server --http 0.0.0.0:8323 --rtr 0.0.0.0:3323
```

**Cisco IOS-XE RPKI configuration:**
```
router bgp 65000
 bgp rpki server tcp 10.1.1.100 port 3323 refresh 300
 address-family ipv6 unicast
  bgp bestpath prefix-validate allow-invalid
```
Note: `allow-invalid` keeps RPKI-invalid routes in the RIB but marks them. Use `bgp bestpath prefix-validate` without `allow-invalid` to drop invalid routes (recommended for production).

**Juniper Junos RPKI configuration:**
```
routing-options {
    validation {
        group rpki-validator {
            session 10.1.1.100 {
                port 3323;
            }
        }
    }
}
policy-options {
    policy-statement rpki-reject {
        term reject-invalid {
            from validation-database invalid;
            then reject;
        }
    }
}
```

### Step 2 — Create monitoring searches

**Currently RPKI-invalid routes in the table:**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="juniper:junos") earliest=-1h
  "RPKI" AND "invalid" AND "ipv6"
| rex field=_raw "prefix\s*=?\s*(?<prefix>[0-9a-fA-F:/]+)"
| rex field=_raw "AS\s*(?<origin_as>\d+)"
| dedup prefix, origin_as
| table prefix, origin_as
| eval risk="RPKI Invalid — this route should be dropped or deprioritised"
```

**Your own prefix monitoring (hijack detection):**
```spl
index=network (sourcetype="cisco:ios" OR sourcetype="juniper:junos") earliest=-24h
  "BGP" AND "2001:db8:your::/48"
| rex field=_raw "(?:origin|AS)\s*=?\s*(?<origin_as>\d+)"
| where origin_as != "65000"
| eval alert="PREFIX HIJACK — Your prefix 2001:db8:your::/48 is being originated by AS" . origin_as . " (expected: AS65000)"
| table _time, host, origin_as, alert
```

### Step 3 — Validate
(a) **RPKI validator health.** Verify the RPKI validator is synchronised: `curl http://localhost:8323/api/v1/status`. Check VRP (Validated ROA Payload) count is reasonable (>200,000).

(b) **RPKI coverage for your prefixes.** Verify ROAs exist for all your IPv6 prefixes: `whois -h rpki.gin.ntt.net 2001:db8:your::/48`.

(c) **Hijack simulation.** In a lab environment, announce a test prefix from an unauthorized AS. Verify the RPKI validator flags it as invalid and the alert fires.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — BGP/RPKI Security"):
- Row 1 — Single-values: RPKI-invalid routes in table, RPKI coverage percentage.
- Row 2 — Table: RPKI-invalid routes with prefix and origin AS.
- Row 3 — Timeline: BGP anomaly events.
- Row 4 — Your prefix monitoring: unauthorized origin alerts.

**Alert 1:** Your prefix originated by unauthorized AS — critical. Immediate escalation.
**Alert 2:** More-specific of your prefix appeared — critical. Possible hijack in progress.
**Alert 3:** RPKI validator down — high. Validation cannot occur.

**Incident response for prefix hijack:**
1. Verify the hijack is real (not a configuration error on your side).
2. Contact upstream ISP to filter the unauthorized announcement.
3. Contact the hijacking AS's upstream providers.
4. If RPKI ROAs are in place and policy is `reject invalid`, the hijack is mitigated automatically.
5. Post-incident: review ROA coverage and create/update ROAs for all prefixes.

### Step 5 — Troubleshooting

- **RPKI validator not connecting.** Verify TCP connectivity on port 3323 (RTR protocol). Check firewall rules between the router and the validator.

- **ROA mismatch.** If your own routes are flagged as RPKI-invalid, your ROA may have an incorrect max-length or wrong origin AS. Verify and update the ROA in your RIR portal (ARIN, RIPE, APNIC).

- **RPKI coverage gap.** If many routes are 'Not Found' (no ROA), they can still be hijacked. Work with your RIR to create ROAs for all your IPv6 prefixes. Target 100% RPKI coverage.

## SPL

```spl
index=network (sourcetype="cisco:ios" OR sourcetype="juniper:junos") earliest=-24h
  ("%BGP" AND ("ipv6" OR "afi.*2") AND ("UPDATE" OR "origin" OR "RPKI" OR "invalid"))
| eval bgp_event=case(
    match(_raw, "(?i)RPKI.*invalid|ROA.*invalid|origin.*validation.*fail"), "RPKI_INVALID",
    match(_raw, "(?i)origin.*change|originator.*changed"), "ORIGIN_CHANGE",
    match(_raw, "(?i)new.*prefix|prefix.*added") AND match(_raw, "/([4-9][0-9]|1[0-2][0-9])"), "MORE_SPECIFIC",
    match(_raw, "(?i)hijack|anomal|unexpected"), "ANOMALY",
    match(_raw, "(?i)UPDATE.*withdraw"), "WITHDRAW",
    1=1, "UPDATE")
| rex field=_raw "prefix\s*=?\s*(?<prefix>[0-9a-fA-F:/]+)"
| rex field=_raw "(?:origin|AS)\s*=?\s*(?<origin_as>\d+)"
| where bgp_event IN ("RPKI_INVALID", "ORIGIN_CHANGE", "MORE_SPECIFIC", "ANOMALY")
| eval severity=case(
    bgp_event="RPKI_INVALID", "CRITICAL — route fails RPKI validation (" . prefix . " from AS" . origin_as . ")",
    bgp_event="ORIGIN_CHANGE", "HIGH — origin AS changed for " . prefix . " to AS" . origin_as,
    bgp_event="MORE_SPECIFIC", "HIGH — more-specific prefix injected: " . prefix,
    bgp_event="ANOMALY", "HIGH — BGP anomaly detected")
| stats count as events by host, bgp_event, prefix, origin_as, severity
| sort -events
```

## Visualization

(1) Table: RPKI-invalid routes currently in the routing table. (2) Timeline: BGP anomaly events. (3) Single-value: RPKI coverage percentage for your prefixes. (4) Map: geographic location of suspicious origin ASes.

## Known False Positives

**Legitimate origin changes.** When an organisation migrates to a new ISP or AS, the origin AS for their prefixes changes. Coordinate with change management.

**Aggregate/deaggregate.** When a provider deaggregates a prefix for traffic engineering, more-specific announcements appear. These should be documented and excluded.

**RPKI ROA expiration.** ROAs have expiration dates. If a ROA expires before renewal, valid routes are temporarily flagged as RPKI Not Found (not Invalid). Monitor ROA expiration separately.

## References

- [RFC 6811 — BGP Prefix Origin Validation (RPKI)](https://www.rfc-editor.org/rfc/rfc6811)
- [RFC 7115 — Origin Validation Operation Based on the RPKI (BCP 185)](https://www.rfc-editor.org/rfc/rfc7115)
- [MANRS — Mutually Agreed Norms for Routing Security](https://www.manrs.org/)
