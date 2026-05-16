# SPL Reference Validation — 2026-05-16

> **First run** of the new `audit-spl-references` audit, introduced after
> studying the [Searchbase app for Splunk](https://splunkbase.splunk.com/app/7188)
> as a reference SPL corpus. The audit cross-checks every identifier in
> our SPL (commands, macros, sourcetypes, indexes, datamodel paths,
> eval / stats functions) against a known-good vocabulary built from
> Splunk's published SPL reference, the CIM 6.x catalogue, a curated
> top-tier of Splunkbase add-on sourcetypes, ESCU macros, and the
> local Searchbase corpus.

## Method

The numbers below are the **effective vocabulary** at audit time — i.e.
the union of the static baseline, the curated well-known layer, and
the local Searchbase corpus.

| Layer | Source | Effective size |
|-------|--------|---------------:|
| SPL commands | [SearchReference / ListOfSearchCommands](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/ListOfSearchCommands) + add-on commands | 181 |
| Eval functions | [SearchReference / CommonEvalFunctions](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/CommonEvalFunctions) | 122 |
| Stats / aggregator functions | [Statistical-and-charting-functions](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Statistical-and-charting-functions) ∪ eval (Splunk lets `stats(eval(...))`) | 152 |
| CIM 6.x datamodel paths | `splunk_uc.audits.spl_hallucinations.CIM_DATASETS` (29 models) | 129 |
| Sourcetypes | `_spl_well_known.WELL_KNOWN_SOURCETYPES` (curated TA registry) ∪ Searchbase corpus | 416 |
| Macros | `_spl_well_known.WELL_KNOWN_MACROS` (ESCU + URL Toolbox + ES) ∪ Searchbase corpus | 72 |
| Indexes | Splunk-core builtin (19) ∪ ES/ITSI/UF (11) ∪ Searchbase corpus | 31 |
| Local reference corpus | Searchbase 1.1.5 (Splunkbase 7188) — 770 vetted SPL searches | — |

The vocabulary is the **union** of all layers above. The local reference
corpus is built by `tools/research/build_spl_reference.py` and lives in
`data/spl-reference.local.json` (gitignored — Searchbase content is
not redistributable). When that file is missing the audit still runs
against the static layers.

The new audit is **distinct from** the existing two SPL audits:

- `audit-spl-grammar` — structural bugs (`stats span=`, leading pipe,
  glued indexes, case-sensitive wildcards, post-chart `where`).
- `audit-spl-hallucinations` — unknown commands, malformed `tstats`,
  invalid CIM data-model.dataset paths, common typo'd field names.
- `audit-spl-references` (new) — **unknown identifiers** (macros not
  in any catalogue, sourcetypes that look like typos, eval functions
  that don't exist, datamodel paths from non-existent models). Catches
  the failure mode where SPL is *structurally* valid but references
  fabricated names.

## Results

| Severity | Count | UCs |
|----------|------:|----:|
| HIGH (unknown command, invalid datamodel) | **0** | 0 |
| MEDIUM (unknown macro, unknown sourcetype, unknown CIM dataset) | 3,020 | 1,948 |
| LOW (unknown eval / stats function, suspicious index) | 88 | 70 |
| **Total** | **3,108** | **2,000** |

### HIGH cleared

After three quick fixes baked into this same delivery, **the catalogue
has zero HIGH-severity SPL reference findings**:

1. `audit-spl-references` boot-strap surfaced **33 HIGH findings across
   11 UCs**.
2. **5 of those** turned out to be an existing baseline gap — five real
   add-on commands (`dbxquery`, `es_notable`, `mcatalog`, `snowevent`,
   `snowrequest`) that lived in `_GENERATING_COMMANDS` (the structural
   audit) but not in `VALID_COMMANDS` (the hallucination audit). Lifted
   into the canonical baseline so every audit sees them.
3. **1 was a legacy datamodel name** — UC-5.13.75 references
   `datamodel:"ITSI_KPI_Summary"`, the older alias for the modern
   `Service_KPI_Summary`. Both are now accepted by the audit.
4. **The remaining 27** were a single parser bug: `_split_pipes()`
   didn't handle backslash-escaped quotes inside double-quoted strings,
   so `rex field=_raw "(?i)(a|b|c)[=:\"\s]+..."` had its embedded
   regex `|` chars surface as pipe boundaries. Fixed in
   `audits/spl_grammar.py` — also benefits `audit-spl-grammar`.

After those landed: 0 HIGH on the entire catalogue. The audit now
runs cleanly against `--check`.

### MEDIUM signal

Of the **3,020 MEDIUM findings**, the breakdown is:

| Category | Count | Real signal |
|----------|------:|------------|
| `unknown-sourcetype` | 2,907 | Mostly "TA not yet catalogued in `_spl_well_known.py`" |
| `unknown-macro` | 113 | Real authoring signal — see below |

#### unknown-macro highlights (real bugs found)

The most-flagged macros after the ESCU `*_filter` convention is
auto-tolerated:

| Macro | Hits | Where | Likely classification |
|-------|------|-------|----------------------|
| `` `involvedObject.kind` `` | 9 | cat-03 (k8s) | **Real bug** — backtick-wrapped JSON field path inside `coalesce(...)`. Splunk would treat as a missing macro. Affects UC-3.2.6, UC-3.2.20, UC-3.2.11, UC-3.2.41, UC-3.3.15, UC-3.3.24. |
| `` `involvedObject.name` `` | 7 | cat-03 (k8s) | Same pattern as above. |
| `` `event_index` `` | 7 | cat-03 (k8s) | Likely intended as `index=foo`; backtick form is a macro lookup that doesn't exist. |
| `` `cisco_networks` `` | 5 | cat-09 / cat-10 | Likely intended as a customer-defined index macro. Either define the macro or expand to `index=cisco`. |
| `` `path_viz_index` `` | 3 | cat-08 / cat-13 | Same pattern. |
| `` `zoom_index` `` | 3 | cat-09 | Same pattern. |
| `` `event.type` `` / `` `event.reason` `` / `` `event.metadata.namespace` `` | 6 | cat-03 (k8s) | Same backtick-wrapped JSON field path bug as `involvedObject.*`. |

**Action:** treat all backtick-wrapped JSON field paths as authoring
errors and rewrite as bare field references inside `coalesce()`. Open a
content-quality follow-up to sweep the affected ~30 UCs.

#### unknown-sourcetype highlights

The remaining 2,907 unknown-sourcetype findings are **almost
entirely** real Splunkbase TA sourcetypes that aren't yet enumerated
in the curated `WELL_KNOWN_SOURCETYPES` set. Top sources (each
counted ≥7 times):

```text
snow:sn_si_incident       ServiceNow Security Incident Response TA
ocp_events                OpenShift events (kube:objects:events alias)
phpfpm:status             PHP-FPM monitor TA
vmware:nsxt:syslog        Splunk Add-on for VMware NSX-T
mscs:azure:diagnostics    Microsoft Cloud Services TA
purestorage:array         Pure Storage app for Splunk
truenas:alert             TrueNAS Splunk integration
kong:access               Kong Gateway TA
cisco:nxos:syslog         Cisco NX-OS TA
crowdstrike:detection     CrowdStrike Falcon TA
```

**None look like hallucinations** — every one matches a real, public
Splunkbase add-on. The right fix is either:

1. Append the affected entries to `WELL_KNOWN_SOURCETYPES` (one-line
   PR — these are facts about Splunk add-ons), or
2. Vendor more reference apps under `external/` and rebuild the local
   reference corpus.

A follow-up PR should walk the JSON output, group by sourcetype, and
add the top ~50 to the curated set. That alone will cut MEDIUM
findings by ~80%.

### LOW signal

| Category | Count | Notes |
|----------|------:|-------|
| `unknown-eval-function` | 80 | Mostly identifier-as-function false positives in unusual SPL shapes (e.g. `count(eval(...))` followed by an identifier appearing as if it were called). Worth a follow-up parser refinement. |
| `unknown-stats-function` | 7 | Same source; safe to ignore for now. |
| `suspicious-index-name` | 1 | `~host_metrics~` — single occurrence, a real typo. |

## Tools delivered with this audit

1. **`src/splunk_uc/audits/_spl_parse.py`** — shared SPL parser
   (commands, macros, sourcetypes, indexes, datamodel paths, lookups,
   eval / stats functions). Reuses the pipe splitter from
   `spl_grammar.py` so any future fix to the splitter benefits every
   downstream audit.

2. **`src/splunk_uc/audits/_spl_baseline.py`** — Splunk-core baseline
   (commands, eval functions, stats functions, CIM datasets, builtin
   indexes). Single source of truth, derived from Splunk's published
   SPL reference.

3. **`src/splunk_uc/audits/_spl_well_known.py`** — curated top-tier
   Splunkbase TA sourcetypes (Windows, Linux, AWS, Azure, GCP, k8s,
   Cisco, Palo Alto, Fortinet, ServiceNow, Okta, CrowdStrike, etc.)
   and ESCU macros. Easy to extend per-PR; no licensing concerns
   because every entry is a fact documented on Splunkbase.

4. **`src/splunk_uc/audits/spl_references.py`** — the audit itself,
   wired into `python -m splunk_uc audit-spl-references`. Supports
   `--severity` filtering, `--check` (CI gate on HIGH), `--json`
   (machine-readable), `--summary-only`, `--limit`.

5. **`tools/research/build_spl_reference.py`** — local-only corpus
   builder. Reads `external/searchbase/` (Splunkbase 7188) and, when
   present, `external/security_content/` (Splunk's
   public Apache-2.0 detection repo) and emits
   `data/spl-reference.local.json` (gitignored) with the union vocab.
   Run via `make audit-spl-references-build`.

6. **Makefile targets** — `audit-spl-references` and
   `audit-spl-references-build`.

## Sustainable workflow

To keep this signal sharp as the catalogue grows:

1. **At authoring time** — run `make audit-spl-references` after
   editing any UC with SPL. The HIGH gate will block real
   hallucinations; MEDIUM is per-UC reviewer judgement.

2. **Per-release** — re-run `make audit-spl-references-build` if any
   external corpus was refreshed under `external/`, then commit the
   audit output JSON snapshot to `reports/quality-review/`.

3. **Growing the well-known TA list** — when MEDIUM findings cluster
   on a single Splunkbase add-on, append its sourcetypes to
   `_spl_well_known.WELL_KNOWN_SOURCETYPES` rather than tagging them
   "known false positive" individually. Treat that file as the
   project's curated TA registry.

4. **CI integration** — the audit is `--check`-mode safe today (zero
   HIGH on the catalogue). A future PR can add it to
   `.github/workflows/validate.yml` once we agree on which severity
   tier should fail PRs.

## Provenance and licensing

- Searchbase corpus is loaded from `external/searchbase/` and never
  committed. Splunk's General Terms restrict redistribution; we
  consume the *vocabulary* (macro names, sourcetype strings,
  datamodel paths) but not the SPL bodies or descriptive prose.
- The `splunk/security_content` (ESCU) repo is Apache-2.0 and may be
  vendored / cited — recommended next-step for further signal.
- All curated entries in `_spl_baseline.py` and
  `_spl_well_known.py` are facts about public Splunk documentation
  / Splunkbase add-on conventions — not creative expression.
