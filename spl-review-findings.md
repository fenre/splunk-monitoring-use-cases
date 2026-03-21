# Splunk Architecture Review Findings

> **Remediation note (2026-03-21):** Follow-up edits applied in `use-cases/cat-*.md` for remaining actionable items: `mvexpand … limit=N` where missing; explicit `max=` on `join` where called out; `sort <N> -count` instead of unbounded `sort` before `head`; AWS IoT provisioning data-source wording aligned to `aws:cloudtrail`; RD Gateway XML vs classic WinEventLog note; prior passes had already addressed CIM `source_ip`→`src`, `Network_Traffic.All_Traffic`, `index=*` hygiene, many quote/CIM fixes, and UC-10.7.690 `cidrmatch` filtering. Informational items (Fortinet TA build variance, finance+EventCode OR splits, etc.) remain deployment-specific—treat as guidance, not universal rewrites.

This document aggregates **five independent review passes** (each attributed to a **specific model name** used in Cursor for that run):

1. **GPT-5** — Initial Splunk architect review (SPL, CIM, TA alignment).
2. **Gemini** — Second pass: CIM field names, `tstats` / datamodel correctness, and literal SPL syntax in code blocks.
3. **Claude Sonnet** — Third pass: TA/sourcetype casing, `index=*` cost, and data-source consistency.
4. **GPT-4o** — Fourth pass: macros, `join`/`mvexpand`/`inputlookup` boundaries, CIM field directionality (`bytes` vs `bytes_in`/`bytes_out`), heavy subsearches, repeated `spath`.
5. **o3-mini** — Fifth pass: `sort`/`head`/`transaction` tuning, explicit `earliest`/`latest`, `eval`/time parsing, `dedup` ordering, documentation/markdown typos in Data Sources.

> *Passes 2–5 included separate Cursor Task reviews over `use-cases/cat-*.md`; items below were spot-checked in-repo before inclusion. If your session used different models, edit the names in the table below and in each **`Found by:`** line.*

### Model attribution (who found what)

| Model | Role in this document |
|--------|------------------------|
| **GPT-5** | Main Cursor assistant — first full pass over the catalog. |
| **Gemini** | Cursor Task subagent (`explore`) — CIM, datamodel, SPL string/syntax. |
| **Claude Sonnet** | Cursor Task subagent (`explore`) — TA/sourcetype alignment, `index=*`, pipeline notes. |
| **GPT-4o** | Cursor Task subagent (`explore`) — joins, multivalue expansion, lookups/app context, `spath`/`subsearch` cost patterns. |
| **o3-mini** | Cursor Task subagent (`explore`) — time bounds, `transaction` limits, `sort`/`dedup` hygiene, doc typos. |

Each finding includes **`Found by:`** with one of the models above. *(Gemini also reported the same `source_ip` → `src` issues as GPT-5; those are only listed under the GPT-5 section to avoid duplication.)*

---

## GPT-5 — first pass

### [use-cases/cat-10-security-infrastructure.md / Email Security]
**Found by:** GPT-5
**Issue:** Non-CIM compliant field (`source_ip`)
**Current:** `| stats count by source_ip, header_from, dkim_result, spf_result, disposition`
**Correction:** `| stats count by src, header_from, dkim_result, spf_result, disposition`
**Reason:** The standard Common Information Model (CIM) field for the source IP address in the Email data model is `src`. Using `source_ip` breaks CIM compliance and prevents proper correlation within Splunk Enterprise Security.

### [use-cases/cat-04-cloud-infrastructure.md / Cloud DNS Operations]
**Found by:** GPT-5 *(Gemini reported the same `source_ip` issue independently)*
**Issue:** Non-CIM compliant field (`source_ip`)
**Current:** `| stats count(eval(rcode!="NOERROR")) as failures, count as total by fqdn, source_ip`
**Correction:** `| stats count(eval(rcode!="NOERROR")) as failures, count as total by fqdn, src`
**Reason:** In the CIM Network Resolution data model, the client making the DNS request is expected to map to `src`. Hardcoding `source_ip` is inconsistent with the standard Splunk CIM.

### [use-cases/cat-14-iot-operational-technology-ot.md / OT Asset Communication]
**Found by:** GPT-5 *(Gemini reported the same `source_ip` issue independently)*
**Issue:** Non-CIM compliant field (`source_ip`)
**Current:** `| stats count by source_ip, unit_id, function_code, register`
**Correction:** `| stats count by src, unit_id, function_code, register`
**Reason:** To ensure OT network traffic aligns with the Network Traffic and ICS data models, standard CIM fields like `src` must be used instead of raw log fields like `source_ip`.

### [use-cases/cat-14-iot-operational-technology-ot.md / OT Device Profiling]
**Found by:** GPT-5 *(Gemini reported the same `source_ip` issue independently)*
**Issue:** Non-CIM compliant field (`source_ip`)
**Current:** `| stats count by actor, device_template, source_ip`
**Correction:** `| stats count by actor, device_template, src`
**Reason:** Standardizing on `src` ensures that cross-domain profiling (mixing traditional IT logs with IoT/OT device logs) functions seamlessly in reporting.

### [use-cases/cat-10-security-infrastructure.md / Authentication & Network Use Cases]
**Found by:** GPT-5 *(Claude Sonnet similarly flagged broad `index=*` + tag patterns in the same file)*
**Issue:** Inefficient base search using a leading wildcard index (`index=*`) combined with `tag=` (*Note: This anti-pattern appears in over 30 use cases in this file.*)
**Current:** `index=* tag=authentication action=failure OR action=success`
**Correction:** `index=YOUR_INDEX tag=authentication action=failure OR action=success` *(Alternatively, utilize `| tstats count from datamodel=Authentication`)*
**Reason:** Using `index=*` combined with `tag=` is heavily penalized in Splunk. It forces the search heads to scan every non-internal index in the environment to check for tag extractions, leading to severe performance degradation. A base search should explicitly declare the target index or leverage `tstats`.

### [use-cases/cat-10-security-infrastructure.md / CrowdStrike Detection Trending]
**Found by:** GPT-5 *(Claude Sonnet also cited this CrowdStrike `index=*` block)*
**Issue:** Inefficient base search with leading wildcard (`index=*`)
**Current:** `index=* sourcetype="CrowdStrike:Event:Streams:JSON" event_simpleName IN ("DetectionSummaryEvent", "IdpDetectionSummaryEvent")`
**Correction:** `index=crowdstrike sourcetype="CrowdStrike:Event:Streams:JSON" event_simpleName IN ("DetectionSummaryEvent", "IdpDetectionSummaryEvent")`
**Reason:** Searching `index=*` for a highly specific sourcetype is an anti-pattern. Best practice dictates supplying the explicit index name to drastically reduce disk reads and search execution time.

### [use-cases/cat-13-observability-monitoring-stack.md / Splunk Core Infrastructure Monitoring]
**Found by:** GPT-5 *(related: Claude Sonnet flagged a different `index=*` line in the same file — see Claude Sonnet section)*
**Issue:** Inefficient base search without boundary constraints
**Current:** `index=* earliest=-15m`
**Correction:** `index=_internal earliest=-15m` *(or whichever specific index is intended)*
**Reason:** Running a wildcard `index=*` search across all data without constraints consumes massive amounts of search tier resources. If searching for Splunk's own telemetry, `index=_internal` or `index=_audit` should be specified.

**Additional notes (GPT-5 pass)**

**Found by:** GPT-5

* **TA / Sourcetype Alignment:** `windows` and `cisco` sourcetypes were spot-checked; Windows scripted inputs (`windows_pending_reboot`, etc.) and Cisco families (`cisco:ios`, `cisco:asa`, etc.) generally match common TA naming.
* **Data Models & tstats:** Many datamodel queries correctly use `| tstats ... from datamodel=...`; multi-line `where` under `tstats` is valid SPL.
* **Missing Pipes:** No systematic missing-pipe errors were found in sampled ````spl```` blocks (indentation-only `where` lines are often subclauses of `tstats`, not standalone commands).

---

## Gemini — CIM, datamodel & syntax focus

### [use-cases/cat-10-security-infrastructure.md / UC-10.2.144 · Windows Service Created with Suspicious Service Name]
**Found by:** Gemini
**Issue:** Unterminated string in search filter (SPL parse error)
**Current:** `` `wineventlog_system` EventCode=7045 ServiceName = "$object_name$" dest = "$dest$`` *(missing closing `"` after `$dest$`)*
**Correction:** `` `wineventlog_system` EventCode=7045 ServiceName="$object_name$" dest="$dest$" ``
**Reason:** The trailing quote for `dest` is missing; the search will not parse until the string is closed.

### [use-cases/cat-10-security-infrastructure.md / UC-10.7.476 · Windows AppX Deployment Package Installation Success]
**Found by:** Gemini
**Issue:** Unterminated string (SPL parse error)
**Current:** `source="XmlWinEventLog:Microsoft-Windows-AppXDeploymentServer/Operational" EventCode=400 HasFullTrust="true" host="$dest$` *(no closing quote)*
**Correction:** `... host="$dest$"`
**Reason:** `host` value must end with a closing double-quote.

### [use-cases/cat-10-security-infrastructure.md / UC-10.7.624 · Windows Scheduled Task with Suspicious Command]
**Found by:** Gemini
**Issue:** Unterminated string (SPL parse error)
**Current:** `` `wineventlog_security` EventCode IN (4698,4700,4702) Computer="$dest$" Caller_User_Name="$user$`` *(missing closing `"` after `$user$`)*
**Correction:** `` ... Caller_User_Name="$user$" ``
**Reason:** Quoted field filter must be closed.

### [use-cases/cat-17-network-security-zero-trust.md / VPN bandwidth & related CIM SPL — multiple UCs]
**Found by:** Gemini
**Issue:** Wrong CIM Network Traffic dataset name and object prefix (`Network_Traffic.Network_Traffic`, `Network_Traffic.bytes`)
**Current:**
```spl
| tstats `summariesonly` sum(Network_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.Network_Traffic
  by _time span=1h
```
**Correction:** Use the **`All_Traffic`** dataset and `All_Traffic.*` fields, e.g.:
```spl
| tstats `summariesonly` sum(All_Traffic.bytes) as bytes
  from datamodel=Network_Traffic.All_Traffic
  by _time span=1h
```
**Reason:** Splunk CIM Network Traffic exposes child datasets such as `All_Traffic`, `DNS`, etc. There is no standard `Network_Traffic.Network_Traffic` dataset; `Network_Traffic.bytes` is not the usual accelerated field path.

### [use-cases/cat-17-network-security-zero-trust.md / Microsegmentation / policy effectiveness CIM SPL]
**Found by:** Gemini *(overlaps thematically with Claude Sonnet’s RD Gateway sourcetype note in the same file)*
**Issue:** Same datamodel mistake plus unquoted `action` value in `where`
**Current:** `from datamodel=Network_Traffic.Network_Traffic` with `where Network_Traffic.action=allowed` (and similar)
**Correction:** `from datamodel=Network_Traffic.All_Traffic` with `where All_Traffic.action="allowed"` (and matching `by All_Traffic.dest`, etc.)
**Reason:** Correct dataset + quoting `allowed` as a string avoids interpreting it as a field name.

### [use-cases/cat-22-regulatory-compliance.md / UC-22.1.6 · GDPR cross-border transfer (CIM SPL)]
**Found by:** Gemini
**Issue:** `tstats` `where` clause uses bare token for string comparison
**Current:** `where All_Traffic.action=allowed`
**Correction:** `where All_Traffic.action="allowed"`
**Reason:** In SPL, unquoted `allowed` is treated as a field name, not the literal string `allowed`.

### [use-cases/cat-22-regulatory-compliance.md / Same UC — optional hardening]
**Found by:** Gemini
**Issue:** Non-idiomatic `rename` / `summariesonly` usage may vary by Splunk version
**Current:** Examples such as `| rename "All_Traffic.*" as *` or `summariesonly=true`
**Correction:** Prefer `| rename All_Traffic.* as *` and `summariesonly=t` per deployment docs.
**Reason:** Aligns with common Splunk documentation patterns and avoids parser quirks.

### [use-cases/cat-10-security-infrastructure.md / UC-10.7.690 · Detect Outbound LDAP Traffic]
**Found by:** Gemini
**Issue:** `tstats` `WHERE` uses `=` to RFC1918 CIDR strings (not valid IP matching) and ambiguous AND/OR grouping
**Current:** (paraphrased) `... All_Traffic.dest_port = 389 OR All_Traffic.dest_port = 636 AND NOT (All_Traffic.dest_ip = 10.0.0.0/8 OR ...)`
**Correction:** Parenthesize ports; after `tstats`, filter private ranges with `cidrmatch()` / `where`, not `dest_ip = 10.0.0.0/8`.
**Reason:** SPL does not treat `field = 10.0.0.0/8` as CIDR membership; logic must be explicit.

---

## Claude Sonnet — TA, sourcetype & performance focus

### [use-cases/cat-10-security-infrastructure.md / AD / CAC-style Windows searches]
**Found by:** Claude Sonnet
**Issue:** Lowercase `wineventlog:security` vs Splunk Add-on for Microsoft Windows default sourcetype
**Current:** `sourcetype="wineventlog:security"` (e.g. in Data Sources and `index=ad sourcetype="wineventlog:security" ...`)
**Correction:** `sourcetype="WinEventLog:Security"` *(or document a deliberate transform to lowercase)*
**Reason:** Sourcetype matching is case-sensitive; the common TA default is `WinEventLog:Security`, not all-lowercase.

### [use-cases/cat-10-security-infrastructure.md / Failed logon style search]
**Found by:** Claude Sonnet
**Issue:** Windows Security event code without sourcetype scoping
**Current:** `index=windows EventCode=4625` *(pattern may appear in ESCU-style blocks)*
**Correction:** `index=windows sourcetype="WinEventLog:Security" EventCode=4625` *(or `XmlWinEventLog:Security` if XML inputs)*
**Reason:** 4625 exists in Security logs; scoping sourcetype avoids unrelated events in the same index and matches TA field extractions.

### [use-cases/cat-10-security-infrastructure.md / SOX / finance correlation]
**Found by:** Claude Sonnet
**Issue:** Windows `EventCode` filters OR’d with non-Windows sourcetypes
**Current:** `index=finance (sourcetype="sap:audit" OR sourcetype="oracle:audit") ... OR EventCode IN (4720,4728,4732)` *(conceptual)*
**Correction:** Split into separate searches or union: AD/Security for 472x vs SAP/Oracle for app audit.
**Reason:** 4720/4728/4732 will not appear in `sap:audit` / `oracle:audit` raw events.

### [use-cases/cat-13-observability-monitoring-stack.md / ITSI / infra coverage]
**Found by:** Claude Sonnet *(distinct from GPT-5’s `index=* earliest=-15m` finding in the same file)*
**Issue:** Metadata-heavy `tstats` over all indexes
**Current:** `| tstats dc(host) as infra_hosts where index=* by index`
**Correction:** Restrict `index=` to the inventory scope you care about, or use a summary/lookup for frequent runs.
**Reason:** `index=*` in `tstats` still forces a broad bucket/metadata sweep; expensive on a schedule.

### [use-cases/cat-14-iot-operational-technology-ot.md / AWS IoT / provisioning]
**Found by:** Claude Sonnet
**Issue:** Non-standard or inconsistent CloudTrail sourcetype naming in documentation
**Current:** Data sources may cite `sourcetype="cloudtrail:iot"` while SPL uses another sourcetype (e.g. IoT-specific)
**Correction:** For Splunk Add-on for AWS, prefer `aws:cloudtrail` with `eventSource` / API filters for IoT; if using Security Lake/OCSF, document that pipeline explicitly.
**Reason:** Avoids onboarding confusion and mixed field sets across pipelines.

### [use-cases/cat-10-security-infrastructure.md / FortiGate inventory]
**Found by:** Claude Sonnet
**Issue:** Sourcetype may not exist in your Fortinet TA build
**Current:** `sourcetype="fortinet:fortigate_system" OR sourcetype="fortinet:fortigate_inventory"`
**Correction:** Confirm against installed `Splunk_TA_fortinet` — inventory often arrives via `fortinet:fortigate_system`, FortiManager, or custom HEC.
**Reason:** An OR branch with a non-existent sourcetype never matches; half the logic silently disappears.

### [use-cases/cat-22-regulatory-compliance.md / Windows logon examples]
**Found by:** Claude Sonnet
**Issue:** Index name `wineventlog` can be mistaken for sourcetype
**Current:** `index=wineventlog sourcetype="WinEventLog:Security"`
**Correction:** Use your real security/OS index name; keep `WinEventLog:Security` as sourcetype.
**Reason:** Operators may assume index must mirror sourcetype naming; it does not.

### [use-cases/cat-17-network-security-zero-trust.md / RD Gateway operational log]
**Found by:** Claude Sonnet
**Issue:** Classic vs XML WinEventLog sourcetype mismatch risk
**Current:** `sourcetype="WinEventLog:Microsoft-Windows-TerminalServices-Gateway/Operational"`
**Correction:** If inputs use `renderXml=true`, expect `XmlWinEventLog:Microsoft-Windows-TerminalServices-Gateway/Operational`.
**Reason:** Wrong family yields zero results despite correct channel name.

### [use-cases/cat-04-cloud-infrastructure.md / AWS CloudTrail]
**Found by:** Claude Sonnet
**Issue:** Pipeline mixing (informational)
**Current:** `sourcetype="aws:cloudtrail"` with `eventName` / `eventSource` — correct for Splunk Add-on for AWS
**Correction:** For Amazon Security Lake / OCSF, use the corresponding sourcetypes/macros — do not assume identical fields in one search.
**Reason:** Same cloud trail *concept*, different schemas.

---

## GPT-4o — macros, joins, multivalue & CIM field directionality

### [use-cases/cat-11-email-collaboration.md / OAuth / scopes expansion]
**Found by:** GPT-4o
**Issue:** `mvexpand` without `limit` on `scopes`
**Current:** `| mvexpand scopes`
**Correction:** `| mvexpand scopes limit=<N>` (tune `N` to worst-case OAuth scopes per row in your environment).
**Reason:** High-cardinality multivalue fields can explode row count and search cost on the search head.

### [use-cases/cat-22-regulatory-compliance.md / ISO / ES correlation join]
**Found by:** GPT-4o
**Issue:** `join` without explicit `max` when joining to notables
**Current:** `join` subsearch on ES notables (macro `` `notable` ``) without explicit `max=` — see `use-cases/cat-22-regulatory-compliance.md` (ISO / correlation coverage SPL).
**Correction:** Add `max=` (e.g. `max=0` for unlimited when you intend full cardinality, or a finite cap after sizing).
**Reason:** Default join limits can truncate matches silently; explicit `max` documents intent and avoids surprise data loss.

### [use-cases/cat-10-security-infrastructure.md / Network traffic throughput (multiple UCs)]
**Found by:** GPT-4o
**Issue:** CIM `Network_Traffic` summarized as a single `bytes` field
**Current:** `| tstats \`summariesonly\` count sum(All_Traffic.bytes) as bytes ...` *(pattern repeated in this file and e.g. `cat-05-network-infrastructure.md`)*
**Correction:** Prefer `sum(All_Traffic.bytes_in)` / `sum(All_Traffic.bytes_out)` (or both with clear aliases) when direction matters for firewall/flow analytics.
**Reason:** CIM differentiates ingress vs egress; one `bytes` aggregate can obscure directionality and confuse ES/CIM dashboards.

### [use-cases/cat-13-observability-monitoring-stack.md / ITSI entities]
**Found by:** GPT-4o
**Issue:** `inputlookup itsi_entities` without app context
**Current:** `| inputlookup itsi_entities`
**Correction:** Run from the ITSI app context, or use the fully qualified lookup/namespace your deployment expects; or use `| rest` for ITSI entities when appropriate.
**Reason:** ITSI lookups resolve per app; bare names on a generic search head can fail or resolve incorrectly.

### [use-cases/cat-04-cloud-infrastructure.md / AWS API JSON failures]
**Found by:** GPT-4o
**Issue:** Multiple `spath` passes on expanded JSON structures
**Current:** (pattern) `| spath path=responseElements.failures{} | mvexpand responseElements.failures{} | spath input=responseElements.failures{} path=reason | spath input=responseElements.failures{} path=arn`
**Correction:** Prefer `spath` once with `path=`/`output=` to fields, or index-time/`json` extraction; add `mvexpand ... limit=N` where needed.
**Reason:** Repeated `spath` on expanded MV rows is a common performance smell versus structured extraction.

---

## o3-mini — time bounds, transactions, sort hygiene & docs

### [use-cases/cat-10-security-infrastructure.md / NGFW threat timechart (example UC)]
**Found by:** o3-mini
**Issue:** Base search without explicit `earliest`/`latest` in the SPL snippet
**Current:** `index=pan sourcetype="pan:threat" severity IN ("critical","high") | timechart span=1h count by subtype`
**Correction:** Add a time window, e.g. `earliest=-24h` (or your SLA window) on the base search.
**Reason:** Relying on UI defaults makes scheduled searches, alerts, and documentation ambiguous; explicit bounds reduce scan cost and stabilize results.

### [use-cases/cat-10-security-infrastructure.md / ESCU-style `transaction` (Kerberos / renamed account chain)]
**Found by:** o3-mini
**Issue:** `transaction` without `maxspan`/`maxpause` in some examples
**Current:** (pattern) `| transaction RenamedComputerAccount startswith=(EventCode=4781) endswith=(EventCode=4768)`
**Correction:** Add `maxspan=5m maxpause=2m` (tune per domain), optionally `maxevents=`.
**Reason:** Unbounded `transaction` can retain large in-memory pools and merge unrelated events; Splunk guidance stresses span/pause controls.

### [use-cases/cat-05-network-infrastructure.md / WLC roaming]
**Found by:** o3-mini
**Issue:** `transaction` has `maxspan` but no `maxpause`
**Current:** `| transaction client_mac maxspan=1h`
**Correction:** Add `maxpause` (e.g. `maxpause=5m`) and/or `maxevents` as appropriate for roaming sessions.
**Reason:** `maxspan` caps total span but not idle gaps between related events.

### [use-cases/cat-10-security-infrastructure.md / IDS top destinations]
**Found by:** o3-mini
**Issue:** `sort` + `head` without aligning `sort` limit to top-N
**Current:** `| stats count, dc(signature) as unique_sigs by dest_ip | sort -count | head 20`
**Correction:** `| sort 20 -count` (or `sort limit=20 -count`) before `head 20`, or `head` alone after a cheaper pre-limiting stats.
**Reason:** `sort` can materialize a large sorted set; capping `sort` matches Splunk performance guidance for top-N patterns.

### [use-cases/cat-05-network-infrastructure.md / UC-5.4.9 Data Sources line]
**Found by:** o3-mini
**Issue:** Markdown: unclosed backtick after `meraki:api` (documentation typo)
**Current:** `- **Data Sources:** \`sourcetype=cisco:wlc\`, \`sourcetype=meraki:api` *(line continues without closing backtick — see `cat-05-network-infrastructure.md` ~1748)*
**Correction:** Close the backtick: `` `sourcetype=meraki:api` ``
**Reason:** Broken markdown invites copy-paste errors and ambiguous sourcetype strings.

### [use-cases/cat-02-virtualization.md / VM backup coverage]
**Found by:** o3-mini
**Issue:** `dedup vm_name` without `sortby` after `append`
**Current:** (pattern) append from multiple hypervisors then `| dedup vm_name`
**Correction:** `| sort 0 vm_name, -_time` then `| dedup vm_name` (or `dedup vm_name sortby -_time`).
**Reason:** Without ordering, `dedup` can keep an arbitrary row per key after `append`.

---

## Summary

| Model | Emphasis |
|--------|-----------|
| **GPT-5** | `source_ip` → `src`, `index=*` cost, CrowdStrike example |
| **Gemini** | SPL **syntax** (broken quotes), **CIM Network_Traffic** dataset (`All_Traffic`), `tstats` string quoting, LDAP/CIDR logic |
| **Claude Sonnet** | **WinEventLog** casing, sourcetype scoping for 4625, finance+EventCode OR, `index=*` in `tstats`, Fortinet/AWS/OT naming, XML vs classic Windows logs |
| **GPT-4o** | `mvexpand` limits, `join max`, `All_Traffic.bytes` vs `bytes_in`/`bytes_out`, ITSI `inputlookup`, repeated `spath` |
| **o3-mini** | Explicit `earliest`/`latest`, `transaction` `maxspan`/`maxpause`, `sort`/`head` top-N, `dedup` ordering, markdown/Data Sources typos |

*Re-run or extend this document after large edits to `use-cases/cat-*.md`.*
