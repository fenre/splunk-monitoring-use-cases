<!-- AUTO-GENERATED from UC-5.20.49.json — DO NOT EDIT -->

---
id: "5.20.49"
title: "RPKI ROV for IPv6 BGP Route Origin Validation"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.20.49 · RPKI ROV for IPv6 BGP Route Origin Validation

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Security, Compliance &middot; **Wave:** Run &middot; **Status:** Verified

*When a network announces 'I own this address range,' there should be a signed certificate proving it — like a property deed. RPKI is the system that checks these deeds. If someone announces they own an address range but the deed says a different owner, that's like someone claiming your house is theirs. We watch for these fraudulent claims and sound the alarm immediately.*

---

## Description

Monitors BGP RPKI Route Origin Validation (ROV) for IPv6 prefixes, detecting invalid route origins (potential BGP hijacks), tracking RPKI coverage statistics, and alerting on RPKI-invalid routes that are accepted into the routing table. RPKI ROV is the primary defence against BGP prefix hijacking — one of the most impactful routing security threats — where an unauthorized AS originates another organization's IPv6 prefix, redirecting traffic through the attacker's network.

## Value

BGP hijacking is one of the most serious internet security threats. In 2008, Pakistan Telecom's hijack of YouTube's prefix demonstrated the real-world impact. IPv6 BGP hijacks are harder to detect manually because operators are less familiar with IPv6 prefix assignments. RPKI ROV provides cryptographic verification that the route origin is legitimate. Monitoring RPKI validation results ensures that the ROV system is functioning correctly and that invalid routes are being rejected, preventing BGP hijacks from affecting production traffic.

## Implementation

Configure RPKI validators (e.g., Routinator, Fort, rpki-client) and connect them to BGP routers via RTR protocol. Collect RPKI validation events from BGP syslog. Track Valid/Invalid/NotFound ratios. Alert on Invalid routes accepted. Monitor validator connectivity.

## Detailed Implementation

### Prerequisites
- RPKI validator deployed (Routinator, Fort, rpki-client, or cloud-hosted validator).
- RTR protocol (RFC 8210) configured between validators and BGP routers.
- BGP IPv6 address family with origin validation enabled.
- Understanding of RPKI validation states and policy options.

### Step 1 — Configure data collection

**Cisco IOS-XE — RPKI configuration:**
```
router bgp 65001
 bgp rpki server tcp 10.0.0.100 port 8282 refresh 300
 address-family ipv6 unicast
  bgp bestpath prefix-validate allow-invalid
```
`allow-invalid` keeps Invalid routes in the RIB (for visibility) but assigns them a lower local preference. For strict enforcement, use `bgp bestpath prefix-validate disallow-invalid` (which drops Invalid routes entirely).

**Juniper Junos:**
```
set routing-options validation group rpki-validators session 10.0.0.100 port 8282
set policy-options policy-statement rpki-policy term invalid from validation-database invalid
set policy-options policy-statement rpki-policy term invalid then reject
```

**RPKI validation status is visible via CLI:**
```
show bgp ipv6 unicast rpki table
  Network             Next Hop         Origin  RPKi State
  2001:db8::/32       2001:db8:ff::1   IGP     valid
  2001:db8:bad::/48   2001:db8:ff::2   IGP     invalid
```

**Verification:**
```spl
index=network sourcetype="cisco:ios" ("%BGP" AND "RPKI") earliest=-24h
| stats count by host
```

### Step 2 — Create the search and alert

**RPKI-Invalid route accepted alert:**
```spl
index=network sourcetype="cisco:ios" "%BGP" ("RPKI" OR "rpki-state" OR "origin-validation") "invalid" earliest=-1h
| rex field=_raw "(?:prefix|network)\s+(?<prefix>[0-9a-fA-F:/]+)"
| rex field=_raw "(?:origin|Origin|AS|from AS)\s+(?<origin_as>\d+)"
| rex field=_raw "(?:peer|neighbor)\s+(?<peer>[0-9a-fA-F:.]+)"
| eval alert="RPKI-Invalid IPv6 route: " . prefix . " originated by AS" . origin_as . " received from " . peer
| table _time, host, prefix, origin_as, peer, alert
```
Trigger: any RPKI-Invalid route. Priority: HIGH. Requires investigation — potential BGP hijack.

**RPKI coverage statistics:**
```spl
index=network sourcetype="cisco:ios" "%BGP" ("RPKI" OR "rpki-state") earliest=-24h
| rex field=_raw "(?<rpki_state>valid|invalid|not-found|unknown)"
| stats count as total_routes count(eval(rpki_state="valid")) as valid count(eval(rpki_state="invalid")) as invalid count(eval(rpki_state="not-found")) as not_found
| eval valid_pct=round(valid / total_routes * 100, 1)
| eval invalid_pct=round(invalid / total_routes * 100, 1)
| eval not_found_pct=round(not_found / total_routes * 100, 1)
```

**RPKI validator connectivity monitor:**
```spl
index=network sourcetype="cisco:ios" "%BGP" "RPKI" ("server" OR "validator") ("down" OR "fail" OR "timeout" OR "error") earliest=-1h
| eval alert="RPKI validator connectivity lost on " . host . " — ROV will use stale data"
| table _time, host, alert
```
Trigger: any validator connectivity failure. Without fresh ROA data, the router cannot validate new route origins.

### Step 3 — Validate
(a) **Valid route check.** Identify a prefix in your routing table that has a published ROA (check on rpki-validator.ripe.net). Verify it shows as 'valid' in the RPKI state.

(b) **Invalid route test.** If available, check RIPE RIS or bgpstream.com for known RPKI-Invalid events. Verify they appear in your Invalid route logs.

(c) **Validator failover.** Disconnect the primary RPKI validator. Verify the failover to the secondary validator occurs and the connectivity alert fires.

### Step 4 — Operationalize

**Dashboard** ("IPv6 — RPKI Route Origin Validation"):
- Row 1 — Single-value: % of IPv6 routes RPKI-Valid, count of RPKI-Invalid routes (should be 0 or near 0 with filtering).
- Row 2 — Pie chart: RPKI state distribution (Valid / Invalid / NotFound).
- Row 3 — Table: all RPKI-Invalid routes with prefix, origin AS, and received from.
- Row 4 — Validator status: connectivity and freshness of ROA cache.
- Row 5 — Trending: RPKI-Valid coverage % over 30 days (should be increasing as more prefixes get ROAs).

**Scheduling:** Invalid route alert continuous. Coverage statistics daily. Validator connectivity every 5 minutes.

**Runbook:**
1. RPKI-Invalid route: investigate the origin AS. Is this a known provider? Check RIPE RPKI dashboard for the ROA status. If the ROA exists and the route conflicts, this is likely a hijack or misconfigured ROA.
2. Validator down: check network connectivity to the validator. If both validators fail, the router will use stale ROA data for the cache lifetime (default: 7200 seconds / 2 hours).
3. Increasing NotFound: expected as the internet grows, but also monitor for RPKI repository issues at the RIRs.

### Step 5 — Troubleshooting

- **ROA maxLength issues** — RFC 9319 warns against using overly permissive maxLength in ROAs. A ROA for 2001:db8::/32 with maxLength /48 allows any more-specific announcement up to /48. If an attacker announces a /48 from a different AS, RPKI may not catch it if the maxLength is too broad. Monitor for ROAs with maxLength significantly larger than the prefix.

- **RPKI and EBGP vs IBGP** — RPKI validation typically occurs at EBGP ingress points. IBGP routes inherit the validation state from the EBGP router that originally validated them. Ensure all border routers have RPKI validation configured.

- **Graceful degradation** — When the RPKI validator is unavailable and the ROA cache expires, all routes transition to 'NotFound' state. The router should NOT start dropping routes — it should fall back to accepting all routes (no RPKI protection). Verify this failsafe behaviour is configured correctly.

## SPL

```spl
index=network sourcetype="cisco:ios" "%BGP" ("RPKI" OR "ROV" OR "origin-validation" OR "rpki-state") earliest=-24h
| rex field=_raw "(?:prefix|route|network)\s+(?<prefix>[0-9a-fA-F:/]+)"
| rex field=_raw "(?:origin|Origin|AS)\s+(?<origin_as>\d+)"
| rex field=_raw "(?:state|validity|rpki-state)\s*:?\s*(?<rpki_state>valid|invalid|not-found|unknown)"
| eval severity=case(
    rpki_state="invalid", "CRITICAL — route origin does not match RPKI ROA",
    rpki_state="not-found", "INFO — no ROA exists for this prefix",
    rpki_state="valid", "OK — route origin verified by RPKI",
    1=1, "UNKNOWN")
| stats count by rpki_state, severity
| sort -count
```

## Visualization

(1) Pie chart: RPKI validation state distribution (Valid/Invalid/NotFound). (2) Table: all RPKI-invalid routes with prefix, origin AS, and source peer. (3) Timechart: RPKI events over 7 days. (4) Single-value: percentage of IPv6 routes with Valid RPKI state.

## Known False Positives

**RPKI-Invalid due to misconfigured ROA.** The prefix holder may have published an incorrect ROA (wrong maxLength, wrong origin AS after an acquisition). In these cases, the route is legitimately originated but the ROA is wrong. Contact the prefix holder to correct the ROA.

**Stale ROA data.** If the RPKI validator loses connectivity to the RIR repositories, the ROA cache becomes stale. Routes that were Valid may transition to NotFound as the cache expires. Monitor validator connectivity separately.

**Transit provider route aggregation.** A transit provider may aggregate customer prefixes into a larger prefix not covered by a ROA. The aggregate route may show as Invalid if the customer's ROA only authorises the more-specific prefix.

## References

- [RFC 6811 — BGP Prefix Origin Validation (RPKI ROV specification)](https://www.rfc-editor.org/rfc/rfc6811)
- [RFC 8210 — The Resource Public Key Infrastructure (RPKI) to Router Protocol (RTR)](https://www.rfc-editor.org/rfc/rfc8210)
- [RFC 9319 — The Use of maxLength in the RPKI (guidance on maxLength pitfalls)](https://www.rfc-editor.org/rfc/rfc9319)
- [MANRS — Mutually Agreed Norms for Routing Security (requires RPKI ROV)](https://www.manrs.org/)
