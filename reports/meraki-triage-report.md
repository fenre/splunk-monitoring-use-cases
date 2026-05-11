# Meraki UC live-fire triage

Decomposes 72 `PASS_NODATA` results from `reports/meraki-sweep-report.json`.

## Summary

* `NO_INPUT` (primary sourcetype not ingested in this Splunk): **55**
* `SEARCH_FILTER_FAIL` (primary sourcetype has data, leading search returns 0 rows — possible hallucination OR legit no-match): **13**
* `DOWNSTREAM_FILTER_BUG` (leading search returned rows, downstream stage zeroed): **4**
* `LEADING_PARSE_ERROR` (leading search itself failed): **0**

## DOWNSTREAM_FILTER_BUG

### UC-5.1.36 — Port Utilization and Congestion Alerts (Meraki MS)

**Sourcetypes (24h counts):** {'meraki:switchportsoverview': 26}

**Triage:** leading search returns 1 row(s); the issue is in stats/where/eval/rename downstream — likely a fake field referenced after the search.

### UC-5.1.53 — Cellular Data Usage and Overage Monitoring (Meraki MG)

**Sourcetypes (24h counts):** {'meraki:devices': 496, 'meraki:summarytopdevicesbyusage': 93}

**Triage:** leading search returns 1 row(s); the issue is in stats/where/eval/rename downstream — likely a fake field referenced after the search.

### UC-15.3.23 — Video Retention and Cloud Archive Storage Utilization (Meraki MV)

**Sourcetypes (24h counts):** {'meraki:audit': 22}

**Triage:** leading search returns 1 row(s); the issue is in stats/where/eval/rename downstream — likely a fake field referenced after the search.

### UC-15.3.27 — Video Stream Connection Errors and Quality Issues (Meraki MV)

**Sourcetypes (24h counts):** {'meraki:assurancealerts': 2, 'meraki:webhook': 0}

**Triage:** leading search returns 1 row(s); the issue is in stats/where/eval/rename downstream — likely a fake field referenced after the search.

## SEARCH_FILTER_FAIL

### UC-5.1.42 — MAC Flooding and Bridge Table Exhaustion (Meraki MS)

**Sourcetypes (24h counts):** {'meraki:assurancealerts': 2}

**Triage:** leading search returns 0 rows even though primary sourcetype `meraki:assurancealerts` has 2 events. The search-time filter (type=, signature=, field=value) either is hallucinated OR the test data legitimately lacks matching values. Manual inspection required.

### UC-5.1.44 — Broadcast Storm Detection and Mitigation (Meraki MS)

**Sourcetypes (24h counts):** {'meraki:assurancealerts': 2}

**Triage:** leading search returns 0 rows even though primary sourcetype `meraki:assurancealerts` has 2 events. The search-time filter (type=, signature=, field=value) either is hallucinated OR the test data legitimately lacks matching values. Manual inspection required.

### UC-5.1.45 — Switch CPU and Memory Utilization (Meraki MS)

**Sourcetypes (24h counts):** {'meraki:assurancealerts': 2}

**Triage:** leading search returns 0 rows even though primary sourcetype `meraki:assurancealerts` has 2 events. The search-time filter (type=, signature=, field=value) either is hallucinated OR the test data legitimately lacks matching values. Manual inspection required.

### UC-5.1.48 — QoS Queue Drops and Priority Violations (Meraki MS)

**Sourcetypes (24h counts):** {'meraki:assurancealerts': 2}

**Triage:** leading search returns 0 rows even though primary sourcetype `meraki:assurancealerts` has 2 events. The search-time filter (type=, signature=, field=value) either is hallucinated OR the test data legitimately lacks matching values. Manual inspection required.

### UC-5.1.50 — Cable Test Results and Port Diagnostics (Meraki MS)

**Sourcetypes (24h counts):** {'meraki:assurancealerts': 2, 'meraki:portstransceiversreadingshistorybyswitch': 0}

**Triage:** leading search returns 0 rows even though primary sourcetype `meraki:assurancealerts` has 2 events. The search-time filter (type=, signature=, field=value) either is hallucinated OR the test data legitimately lacks matching values. Manual inspection required.

### UC-5.1.55 — SIM Status and Plan Monitoring (Meraki MG)

**Sourcetypes (24h counts):** {'meraki:assurancealerts': 2, 'meraki:devices': 496, 'meraki:devicesavailabilities': 0}

**Triage:** leading search returns 0 rows even though primary sourcetype `meraki:devices` has 496 events. The search-time filter (type=, signature=, field=value) either is hallucinated OR the test data legitimately lacks matching values. Manual inspection required.

### UC-5.2.27 — NAT Pool Usage and Exhaustion Alerts (Meraki MX)

**Sourcetypes (24h counts):** {'meraki:assurancealerts': 2}

**Triage:** leading search returns 0 rows even though primary sourcetype `meraki:assurancealerts` has 2 events. The search-time filter (type=, signature=, field=value) either is hallucinated OR the test data legitimately lacks matching values. Manual inspection required.

### UC-5.4.24 — Wireless Health Score Trending (Meraki MR)

**Sourcetypes (24h counts):** {'meraki:assurancealerts': 2}

**Triage:** leading search returns 0 rows even though primary sourcetype `meraki:assurancealerts` has 2 events. The search-time filter (type=, signature=, field=value) either is hallucinated OR the test data legitimately lacks matching values. Manual inspection required.

### UC-5.4.29 — Mesh Network Link Quality and Backhaul Health (Meraki MR)

**Sourcetypes (24h counts):** {'meraki:assurancealerts': 2}

**Triage:** leading search returns 0 rows even though primary sourcetype `meraki:assurancealerts` has 2 events. The search-time filter (type=, signature=, field=value) either is hallucinated OR the test data legitimately lacks matching values. Manual inspection required.

### UC-5.6.15 — DHCP Pool Exhaustion and Address Allocation Issues (Meraki)

**Sourcetypes (24h counts):** {'meraki:assurancealerts': 2}

**Triage:** leading search returns 0 rows even though primary sourcetype `meraki:assurancealerts` has 2 events. The search-time filter (type=, signature=, field=value) either is hallucinated OR the test data legitimately lacks matching values. Manual inspection required.

### UC-5.8.9 — SSL/TLS Certificate Expiration Tracking (Meraki)

**Sourcetypes (24h counts):** {'meraki:assurancealerts': 2}

**Triage:** leading search returns 0 rows even though primary sourcetype `meraki:assurancealerts` has 2 events. The search-time filter (type=, signature=, field=value) either is hallucinated OR the test data legitimately lacks matching values. Manual inspection required.

### UC-5.8.15 — Admin Privilege Changes and Permission Escalation (Meraki)

**Sourcetypes (24h counts):** {'meraki:audit': 22}

**Triage:** leading search returns 0 rows even though primary sourcetype `meraki:audit` has 22 events. The search-time filter (type=, signature=, field=value) either is hallucinated OR the test data legitimately lacks matching values. Manual inspection required.

### UC-5.8.23 — Dashboard Configuration and Export Backup (Meraki)

**Sourcetypes (24h counts):** {'meraki:audit': 22}

**Triage:** leading search returns 0 rows even though primary sourcetype `meraki:audit` has 22 events. The search-time filter (type=, signature=, field=value) either is hallucinated OR the test data legitimately lacks matching values. Manual inspection required.

