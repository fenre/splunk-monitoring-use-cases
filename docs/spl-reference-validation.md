# SPL reference validation

How the catalogue defends against AI-authored SPL hallucinations.

## What this document covers

The repository now has **three** complementary SPL audits, each tuned
for a different failure mode:

| Audit | Failure mode it catches | Severity gate |
|-------|--------------------------|---------------|
| [`audit-spl-grammar`](../src/splunk_uc/audits/spl_grammar.py) | Structural bugs (`stats span=`, leading pipe, glued indexes, post-chart `where`, case-sensitive wildcards). | HIGH on `--check`. |
| [`audit-spl-hallucinations`](../src/splunk_uc/audits/spl_hallucinations.py) | Unknown commands, malformed `tstats`, invalid CIM `datamodel.dataset`, common typo'd field names. | HIGH. |
| [`audit-spl-references`](../src/splunk_uc/audits/spl_references.py) | **Plausible-looking but fabricated identifiers** — fake macros, misspelled sourcetypes, eval functions that don't exist, datamodel paths from non-existent models. | HIGH on `--check`. |

`audit-spl-references` is the newest of the three and the focus of
this document. See `reports/quality-review/2026-05-16-spl-references.md`
for the first run's findings.

## How the audit works

```
                ┌─────────────────────────────────┐
                │  Splunk-core baseline           │
                │  (_spl_baseline.py)             │
                │  • 172 commands                 │
                │  • 107 eval functions           │
                │   38 stats-only functions       │
                │  • 19 builtin field tokens      │
                │  • 29 CIM models / 129 paths    │
                └────────────┬────────────────────┘
                             │
                             ▼
                ┌─────────────────────────────────┐
                │  Curated well-known TA vocab    │
                │  (_spl_well_known.py)           │
                │  • 392 sourcetypes              │
                │   62 ESCU/TA macros             │
                │  • 11 well-known indexes        │
                └────────────┬────────────────────┘
                             │
                             ▼
                ┌─────────────────────────────────┐
                │  Local reference corpus         │
                │  (data/spl-reference.local.json)│
                │  • Searchbase: ~770 SPL searches│
                │  • (optional) ESCU detections   │
                │  Built by build_spl_reference   │
                └────────────┬────────────────────┘
                             │
                             ▼
                ┌─────────────────────────────────┐
                │  Effective vocabulary (union)   │
                │  When all three layers loaded:  │
                │  • commands       181           │
                │  • eval funcs     122           │
                │  • stats funcs    152*          │
                │  • sourcetypes    416           │
                │  • macros          72           │
                │  • indexes         31           │
                │  • datamodels     129           │
                │                                 │
                │  *stats accepts eval funcs too  │
                │   (Splunk lets stats(eval(...)))│
                └────────────┬────────────────────┘
                             │
   per UC SPL field          │
   (spl, cimSpl, rbaSpl, mvSpl)
                             │
                             ▼
                ┌─────────────────────────────────┐
                │  _spl_parse.extract_all(spl)    │
                │  • commands                     │
                │  • macros (with arity)          │
                │  • sourcetypes / indexes        │
                │  • datamodel paths              │
                │  • lookups                      │
                │  • eval / stats functions       │
                └────────────┬────────────────────┘
                             │
                             ▼
                ┌─────────────────────────────────┐
                │  Compare to vocabulary →         │
                │  Finding (HIGH / MEDIUM / LOW)   │
                └─────────────────────────────────┘
```

The exact numbers above are point-in-time; rerun
``python -m splunk_uc audit-spl-references --json | jq .vocabulary``
for the live snapshot.

Every component is **layered and stoppable**:

* `_spl_parse.py` is the only place SPL is parsed; both `audit-spl-grammar`
  (existing) and `audit-spl-references` (new) share its
  `_split_pipes()` helper. Fixing one fixes both.
* `_spl_baseline.py` is the floor — Splunk-core only.
* `_spl_well_known.py` is the curated TA layer — append-only as new
  add-ons gain importance in the catalogue.
* `data/spl-reference.local.json` is the local-only enrichment layer.

If the local corpus is missing the audit still runs against the static
layers; it just produces more MEDIUM findings (because the third-party
vocabulary is narrower).

## Files

| Path | Purpose |
|------|---------|
| `src/splunk_uc/audits/_spl_parse.py` | Shared SPL parser primitives. |
| `src/splunk_uc/audits/_spl_baseline.py` | Splunk-core baseline (commands, eval/stats functions, CIM datasets, builtin tokens). |
| `src/splunk_uc/audits/_spl_well_known.py` | Curated Splunkbase<sup class="ref">[<a href="#ref-3">3</a>]</sup> TA sourcetypes + ESCU macro vocabulary. |
| `src/splunk_uc/audits/spl_references.py` | The audit verb (`audit-spl-references`). |
| `tools/research/build_spl_reference.py` | Local-only reference corpus builder. |
| `data/spl-reference.local.json` | Generated artefact (gitignored). |
| `tests/splunk_uc/test_spl_references.py` | Unit tests pinning parser + audit contracts. |

## Running the audit

```bash
# Quick check (CI-friendly, exits 1 on any HIGH finding)
make audit-spl-references

# Full report (HIGH + MEDIUM + LOW)
PYTHONPATH=src python -m splunk_uc audit-spl-references --severity LOW

# JSON output for tooling
PYTHONPATH=src python -m splunk_uc audit-spl-references --severity LOW --json > out.json

# Just the summary, no per-finding detail
PYTHONPATH=src python -m splunk_uc audit-spl-references --summary-only
```

### Severity tiers

| Severity | Categories | Default in `--check`? |
|----------|-----------|----------------------|
| HIGH | `unknown-command`, `unknown-datamodel` | Fails. |
| MEDIUM | `unknown-macro`, `unknown-sourcetype`, `unknown-datamodel-dataset` | Reports, doesn't fail. |
| LOW | `unknown-eval-function`, `unknown-stats-function`, `suspicious-index-name` | Reports, doesn't fail. |

The HIGH gate catches anything that would prevent SPL from running at
all. MEDIUM and LOW are signal for human review.

### `--check` mode

```bash
PYTHONPATH=src python -m splunk_uc audit-spl-references --check
echo "exit code: $?"
```

Exits `1` if there is any HIGH-severity finding, `0` otherwise.

## Building / refreshing the local reference corpus

The local corpus is **never committed**. Maintainers refresh it on
demand:

```bash
# 1. Drop a Splunkbase app archive into ./external/
#    e.g. external/searchbase/searchbase/default/searchbase.conf
# 2. (Optional) clone splunk/security_content into ./external/
#    git clone https://github.com/splunk/security_content external/security_content
# 3. Rebuild the reference vocabulary
make audit-spl-references-build
# → writes data/spl-reference.local.json
```

The builder is a no-op when no external corpus is present; the JSON
just lists zero entries and the audit falls back to the static layers.

### Sources currently consumed

| Source | Path | License | Redistributable? |
|--------|------|---------|------------------|
| Searchbase (Splunkbase 7188) | `external/searchbase/` | Splunk General Terms | **No.** Vocabulary fingerprints only. |
| `splunk/security_content` (ESCU) | `external/security_content/` | Apache-2.0 | Yes. Optional vendoring. |

The audit consumes only macro names, sourcetype strings, datamodel
paths, and function names. It does **not** copy SPL bodies, descriptive
prose, or any other content into the repository.

## Growing the well-known TA list

When MEDIUM findings cluster on a single Splunkbase add-on, append its
sourcetypes to `_spl_well_known.WELL_KNOWN_SOURCETYPES`. These are
facts about Splunk add-on conventions documented on Splunkbase, not
creative expression. Cite the TA name + Splunkbase ID as a comment.

```python
# Splunk Add-on for Foo Bar — Splunkbase #####
"foo:bar:event",
"foo:bar:audit",
```

The `WELL_KNOWN_SOURCETYPES` set is checked in CI via the dispatcher
import test — adding entries is a single-line PR.

## Authoring workflow

1. **Write or edit a UC's SPL** as usual.
2. **Run the audit** before committing:

   ```bash
   PYTHONPATH=src python -m splunk_uc audit-spl-references
   ```

   * If you see a HIGH finding, stop — it's a real SPL bug.
   * If you see a MEDIUM `unknown-macro`, double-check the macro name
     against the [ESCU repo](https://github.com/splunk/security_content/tree/develop/macros).
   * If you see a MEDIUM `unknown-sourcetype` and the sourcetype is
     real, append it to `_spl_well_known.py`.
3. **Commit** and let CI re-confirm the HIGH gate is clean.

## CI integration (proposed)

Adding the audit to `.github/workflows/validate.yml` requires only:

```yaml
      - name: Validate SPL identifiers
        run: PYTHONPATH=src python -m splunk_uc audit-spl-references --check
```

The `--check` mode fails only on HIGH (unknown command / invalid
datamodel). The catalogue currently has zero such findings, so the
gate is green from day one.

## Internals — why the parser is a separate module

The parser (`_spl_parse.py`) is intentionally separate from any
specific audit. Three reasons:

1. **Reuse.** Both the existing `audit-spl-grammar` and the new
   `audit-spl-references` consume the same `_split_pipes()` helper.
2. **Test isolation.** Parser bugs are fixed and tested without
   touching audit-specific logic.
3. **Future-proofing.** A planned `audit-spl-mitre-coverage` and
   `audit-spl-cim-paths` will share the same extraction primitives.

The parser was inspired by Splunk's published SPL command reference
and the [`sp_search_decomposition`](https://github.com/splunk/searchbase)
macro that ships with Searchbase. It is implemented from scratch
against the Splunk docs (no verbatim copying of Splunk-licensed
regex patterns).

## Reference

* [Splunk SPL command reference](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/ListOfSearchCommands)
* [Splunk eval functions](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/CommonEvalFunctions)
* [Splunk stats functions](https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Statistical-and-charting-functions)
* [Splunk CIM 6.x](https://docs.splunk.com/Documentation/CIM/latest/User/Overview)
* [Splunk Security Content (ESCU)](https://github.com/splunk/security_content)
* [Searchbase App for Splunk (Splunkbase 7188)](https://splunkbase.splunk.com/app/7188)

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-2"></a>**[2]** Splunk Inc. (2026). *Splunk Common Information Model Add-on Manual*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/CIM

<a id="ref-3"></a>**[3]** Splunk Inc. (2026). *Splunkbase — the Splunk app marketplace*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://splunkbase.splunk.com/

<details>
<summary>Additional online sources cited in the document body (8)</summary>

<a id="ref-4"></a>**[4]** github.com. *ESCU repo*. Retrieved May 11, 2026, from https://github.com/splunk/security_content/tree/develop/macros

<a id="ref-5"></a>**[5]** docs.splunk.com. *Splunk SPL command reference*. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/ListOfSearchCommands

<a id="ref-6"></a>**[6]** docs.splunk.com. *Splunk eval functions*. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/CommonEvalFunctions

<a id="ref-7"></a>**[7]** docs.splunk.com. *Splunk stats functions*. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/Statistical-and-charting-functions

<a id="ref-8"></a>**[8]** docs.splunk.com. *Splunk CIM 6.x*. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/CIM/latest/User/Overview

<a id="ref-9"></a>**[9]** github.com. *Splunk Security Content (ESCU)*. Retrieved May 11, 2026, from https://github.com/splunk/security_content

<a id="ref-10"></a>**[10]** splunkbase.splunk.com. *Searchbase App for Splunk (Splunkbase 7188)*. Retrieved May 11, 2026, from https://splunkbase.splunk.com/app/7188

<a id="ref-11"></a>**[11]** github.com. *GitHub: splunk/searchbase*. Retrieved May 11, 2026, from https://github.com/splunk/searchbase

</details>

<!-- END-AUTOGENERATED-SOURCES -->
