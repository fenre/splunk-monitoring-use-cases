# Meraki UC live-fire triage

Decomposes 82 `PASS_NODATA` results from `reports/meraki-sweep-report.json`.

## Summary

* `NO_INPUT` (primary sourcetype not ingested in this Splunk): **80**
* `SEARCH_FILTER_FAIL` (primary sourcetype has data, leading search returns 0 rows — possible hallucination OR legit no-match): **1**
* `DOWNSTREAM_FILTER_BUG` (leading search returned rows, downstream stage zeroed): **1**
* `LEADING_PARSE_ERROR` (leading search itself failed): **0**

## DOWNSTREAM_FILTER_BUG

### UC-5.8.22 — API Error Rate and Endpoint Health (Meraki)

**Sourcetypes (24h counts):** {'meraki:apirequestshistory': 50, 'meraki:apirequestsresponsecodes': 0}

**Triage:** leading search returns 1 row(s); the issue is in stats/where/eval/rename downstream — likely a fake field referenced after the search.

## SEARCH_FILTER_FAIL

### UC-5.1.55 — SIM Status and Plan Monitoring (Meraki MG)

**Sourcetypes (24h counts):** {'meraki:assurancealerts': 0, 'meraki:devices': 4, 'meraki:devicesavailabilities': 0}

**Triage:** leading search returns 0 rows even though primary sourcetype `meraki:devices` has 4 events. The search-time filter (type=, signature=, field=value) either is hallucinated OR the test data legitimately lacks matching values. Manual inspection required.

