# ADR-0014: Add a structured per-UC `thresholds` field

- **Status:** Proposed
- **Date:** 2026-05-18
- **Deciders:** Repository maintainers
- **Closes plan finding:** P12 first cut — the schema scaffold the
  content-quality moonshot wants before any lift-loop rubric can score
  threshold rationale, and before any future cloud-deployer UI can
  surface a "tune these knobs" panel.

## Context

Every UC in this catalogue compares observed signal against one or
more **numeric thresholds**: error-rate percentages, latency budgets,
free-disk minima, login-failure counts, queue-depth ceilings, span
lengths. Today those numbers live in two places:

1. **As magic literals inside the `spl` and `cimSpl` fields.** Examples
   pulled from `content/cat-10-security-infrastructure/UC-10.10.1.json`,
   `cat-13-observability-monitoring-stack/UC-13.4.10.json`, and
   `cat-19-compute-infrastructure-hci-converged/UC-19.1.6.json`:

   ```spl
   ... | where errorRate > 5
   ... | where freeSpaceGB < 10
   ... | where failedLogins >= 10
   ... | where avgLatencyMs > 250
   ```

2. **As optional prose** inside the `detailedImplementation` field's
   "Step 2 — Create the search and alert" → "Understanding this SPL"
   sub-section. The
   [gold-standard playbook](../gold-standard-authoring-playbook.md) §5.3
   explicitly asks authors to articulate
   _"the rationale for thresholds (why 24h, not 23h or 25h; why 80%, not
   70% or 90%)"_.

This shape was fine when the catalogue was an HTML browser. It is not
fine for the consumers that have arrived since:

- **The content-quality lift loop (P12).**
  [`docs/superpowers/specs/2026-05-17-content-quality-lift-loop-design.md`](../superpowers/specs/2026-05-17-content-quality-lift-loop-design.md)
  authors against the
  [`src/splunk_uc/audits/gold_profile.py`](../../src/splunk_uc/audits/gold_profile.py)
  rubric. "Is the threshold rationale present and non-arbitrary?" is a
  rubric question the loop cannot answer today: the rationale, if it
  exists, is embedded in an arbitrarily-shaped paragraph that the auditor
  cannot parse deterministically. Until thresholds are structured data,
  the lift loop cannot score this dimension and cannot lift it.
- **The recommender Splunk app.** The recommender TA in `dist/recommender-app/`
  reads UC sidecars and surfaces them in a Splunk Cloud install. At v9.x
  it cannot render a "Tune these thresholds for your environment" panel
  because the numbers it would tune are buried inside the SPL strings.
- **The future Splunk Cloud cloud-deployer**. ADR-0009 (generated
  artefact policy) anticipates a per-tenant install flow that emits
  tenant-specific `savedsearches.conf`. Tenants vary: a small bank
  needs a different `failedLogins` threshold than a hyperscaler. Today
  the only way to override is to fork the UC's SPL string — which
  permanently divorces the customer copy from upstream.
- **Catalogue search UI.** Users today cannot ask "show me every UC
  whose default threshold sits above 90%" because there is no
  threshold field to index. The build doesn't even know which numbers
  in the SPL are tuning knobs versus structural literals
  (`| head 100`, `_time-1h@h`, etc.).
- **The MCP server.** `mcp/splunk-uc-mcp` tool descriptors expose
  `search_use_cases`, `get_use_case`, and similar surfaces, but cannot
  expose a `find_use_cases_by_threshold_band` tool because the
  underlying data is not addressable.
- **External consumers.** The compliance scorecard and the evidence
  packs cite "control thresholds" that auditors expect to see as
  structured, reviewable values, not as numbers buried in a query
  string. SOC 2<sup class="ref">[<a href="#ref-1">1</a>]</sup> and ISO 27001<sup class="ref">[<a href="#ref-5">5</a>]</sup> evidence packs already feel this gap.

The catch is volume. The catalogue has **7,929 UCs**; nearly all of them
embed at least one numeric threshold. Any structured-thresholds proposal
has to handle the back-fill without blocking the live catalogue, the
same way `splunkbaseApps` (schema v1.7.0) handled its own 7,300-UC
back-fill: optional field, generator-populated entries, `requiresSmeReview`
flag tracked separately, no hard CI block until SME signs each entry off.

The forces in play:

- **Additive, not breaking.** The schema is at v1.7.0. We cannot
  invalidate the 7,929 sidecars by making thresholds required. The
  field must be optional and the validator must continue to accept any
  UC that omits it.
- **Authoring sanity.** The field must be easy to fill in by hand for a
  new UC and easy to back-fill mechanically for the existing 7,929. The
  shape has to be one that a generator can derive from the SPL string
  with high precision (the regex set is small: `> N`, `>= N`, `< N`,
  `<= N`, `= N`, `latest()=N`, `top N`, `head N`).
- **Discoverable, not parametric.** The lift-loop scope (§ P12 first
  cut) is to make thresholds **discoverable** — readable as structured
  data, auditable for rationale, exportable to dashboards and evidence
  packs. **Parameterising** the SPL string (so a cloud deployer can
  template `${threshold.errorRate}` at install time) is a strictly
  larger change that involves a tiny SPL templating engine, render-time
  substitution in the build, and cloud-deployer wiring. It deserves its
  own ADR after this one lands. See §"Alternatives considered" §B.
- **Schema-level coherence.** The shape must align with the existing
  patterns the schema already uses: optional structured field with
  `additionalProperties: false`, `minLength`/`pattern` constraints,
  and a `requiresSmeReview` flag for staged migration (mirrors
  `splunkbaseApps[].requiresSmeReview`). No new schema concepts.

## Decision

We will introduce a new optional top-level field
**`thresholds`** in `schemas/uc.schema.json` at schema version **1.8.0**.

### Field shape

```json
"thresholds": {
  "type": "array",
  "description": "Structured list of numeric tuning knobs that the SPL applies. Optional; absent when the UC has no tunable numeric threshold (e.g. presence/absence checks, change-event UCs). Each entry pairs a magic literal currently embedded in the SPL with its human-articulated rationale, an authoritative source, and a recommended operating range, so the lift loop, the recommender TA, the evidence-pack generator, and the future cloud deployer can all read the same structured truth.",
  "items": {
    "type": "object",
    "additionalProperties": false,
    "required": ["name", "value", "rationale"],
    "properties": {
      "name": {
        "type": "string",
        "pattern": "^[a-z][a-zA-Z0-9]*$",
        "description": "camelCase identifier for this threshold (e.g. 'highErrorRatePct', 'minFreeDiskGB', 'maxFailedLogins'). Unique within the UC. Used as the join key by downstream consumers."
      },
      "value": {
        "type": "number",
        "description": "Default threshold value as it currently appears in the SPL. Numeric only; units live in 'unit'."
      },
      "unit": {
        "type": "string",
        "description": "Free-form unit string (e.g. 'percent', 'GB', 'milliseconds', 'count_per_hour', 'requests'). Encouraged but not required because some thresholds are dimensionless counts."
      },
      "splVariable": {
        "type": ["string", "null"],
        "description": "Optional pointer to the literal in the 'spl' field this threshold corresponds to. When set, the build validates that the literal still exists in the SPL string; when null, the threshold is descriptive metadata that does not currently flow back into the search."
      },
      "rationale": {
        "type": "string",
        "minLength": 30,
        "description": "Why this value? At least one of: a vendor recommendation, an industry standard, an empirical observation from the catalogue's reference deployments, or 'arbitrary - tune to local environment'. The lift-loop rubric scores this field for non-empty, non-circular reasoning."
      },
      "source": {
        "type": "string",
        "enum": ["vendor-doc", "industry-standard", "regulatory", "empirical", "arbitrary"],
        "description": "Provenance tier of the rationale. 'arbitrary' is allowed but every gold-tier UC must have at least one threshold whose source is not 'arbitrary'."
      },
      "sourceRef": {
        "type": "string",
        "description": "Optional citation. URL, ISO clause, NIST control id, vendor doc anchor, or RFC section."
      },
      "range": {
        "type": "object",
        "additionalProperties": false,
        "description": "Recommended operating range. Populated for the future cloud-deployer 'tune this' UI; ignored by the build today.",
        "properties": {
          "min": { "type": "number" },
          "max": { "type": "number" },
          "recommended": { "type": "number" }
        }
      },
      "requiresSmeReview": {
        "type": "boolean",
        "description": "Set true when the entry was generated mechanically by python -m splunk_uc generate-thresholds and has not yet been signed off by an SME. Cleared to false (or removed) once a human review confirms the rationale and source. Mirrors the splunkbaseApps[].requiresSmeReview migration pattern from schema v1.7.0."
      }
    }
  }
}
```

### Authoring example

For UC-19.1.6 ("Free disk space below 10 GB on critical hosts"),
which today contains `... | where freeSpaceGB < 10` and a one-line
`detailedImplementation` mention of "10 GB", the structured entry
would be:

```json
"thresholds": [
  {
    "name": "minFreeDiskGB",
    "value": 10,
    "unit": "GB",
    "splVariable": "freeSpaceGB < 10",
    "rationale": "10 GB is the lower bound below which a typical Linux package update on a server-class host risks aborting mid-transaction. Set lower for SSD-only edge nodes (5 GB), higher for log-heavy hosts (50 GB).",
    "source": "empirical",
    "sourceRef": "Splunk catalogue reference deployments; matches Red Hat RHEL 9 minimum-free-disk guidance",
    "range": { "min": 5, "max": 100, "recommended": 10 },
    "requiresSmeReview": false
  }
]
```

The lift-loop rubric reads the `rationale` (≥ 30 chars, non-arbitrary
`source`) and gives this UC the full threshold-rationale credit. The
recommender TA reads `range.recommended` to populate its install
default. A future cloud-deployer reads `range.{min,max}` to bound the
"Tune this" slider. A future search UI reads `value` to support
"find every UC whose minFreeDiskGB threshold is < 50 GB".

### Why this shape (and not a richer parametric one)

The field is **descriptive metadata** about the SPL, not a template
substitution language. The `value` field captures what the SPL
**currently** uses; the recommender / cloud-deployer / dashboard each
read it for their own purpose. The SPL string itself is not rewritten
at build time. That keeps:

- The build deterministic and round-trippable (the SPL you read in the
  sidecar is the SPL you run in Splunk).
- The lift-loop scope narrow (P12 first cut: make thresholds
  auditable). Parameterising the SPL is a strictly larger change that
  requires a tiny SPL templating engine and cloud-deployer rendering
  contract; ADR-NNNN-future will cover that.
- The migration safe — back-filling 7,929 UCs becomes a mechanical
  regex pass against existing `spl` strings, not a co-ordinated rewrite
  of every search.

`splVariable` is the soft link back to the SPL: when set, a build-time
audit verifies that the literal token still appears in the SPL string
exactly once. If a future PR edits the SPL such that the literal moves
or changes value, the build prints a warning so the threshold metadata
gets reviewed. This catches drift between the structured metadata and
the actual search behaviour without requiring full SPL parsing.

## Consequences

**Positive:**

- The content-quality moonshot (P12) gets its scaffolding. The
  lift-loop rubric can now score `thresholdRationale` deterministically
  in `gold_profile.py` (and a future `gold_profile_v3.py` if needed),
  unblocking the depth-dimension lift that currently caps the catalogue
  at composite 72 / Silver.
- The recommender TA gains a structured surface to render a
  "Configure thresholds" page at install time without forcing the
  tenant to fork the SPL string.
- Evidence packs (SOC 2, ISO 27001, NIS2<sup class="ref">[<a href="#ref-3">3</a>]</sup>, DORA<sup class="ref">[<a href="#ref-4">4</a>]</sup>, CMMC<sup class="ref">[<a href="#ref-8">8</a>]</sup>) gain a
  machine-readable "control thresholds" table for auditors, replacing
  the current prose-only rendering.
- The MCP server can grow a `find_use_cases_by_threshold_band` tool,
  unlocking RAG / agent workflows that today have no addressable
  threshold surface.
- The schema bump is fully additive. Every existing UC remains valid.
  No CI gate fails on day one.
- The `requiresSmeReview = true` migration flag mirrors the existing
  `splunkbaseApps` pattern (schema v1.7.0), so contributors already
  understand the staging contract.

**Negative:**

- 7,929 UC sidecars need a back-fill. The generator
  (`python -m splunk_uc generate-thresholds --auto`) will run once and
  emit a `requiresSmeReview = true` entry per UC where it could
  confidently detect a tunable literal in the SPL. Approximate
  expected fill: 6,500–7,200 UCs (the rest are presence/absence,
  change-event, or list-of-named-items UCs with no tunable threshold).
  The remainder is an SME-driven authoring backlog, not a CI blocker.
- The schema goes from v1.7.0 → v1.8.0. Downstream consumers that
  pin to a major-minor (currently only the `apps/web/` Vite scaffold's
  hypothetical typecheck) need to be re-pinned. This is the documented
  cost of the schema's `x-stability: stable` contract: minor bumps are
  additive.
- A new audit (`audit-thresholds`) is implied: a tier-1 UC with
  `thresholds[]` populated should have at least one entry whose
  `source` is not `"arbitrary"`. We will land that audit in a separate
  PR after the field exists, so the schema PR stays surgical.
- The `splVariable` consistency check requires the build to
  cross-reference each `thresholds[].splVariable` against the `spl`
  string and emit a warning on mismatch. This is small (a regex match
  per threshold) but it does add one more thing the build does.
- Authoring UX gets one more field. Mitigated by the field being
  optional, by the generator handling the back-fill, and by the
  authoring playbook (`docs/gold-standard-authoring-playbook.md` §5.3)
  already asking authors to articulate the rationale in prose — we are
  asking them to structure the same information.

## Alternatives considered

A. **Keep magic literals in SPL strings; do nothing.** Status quo.
   The lift-loop rubric cannot score threshold rationale and the
   recommender TA cannot surface tuning knobs. P12 stays blocked. We
   stay at composite 72 / Silver. Rejected — this is the problem the
   ADR exists to solve.

B. **Parameterise the SPL with `${threshold.name}` substitution and
   render at build time.** Strictly more powerful: a cloud deployer
   could override values at install and the resulting `savedsearches.conf`
   would carry tenant-specific numbers. Rejected for this ADR because
   (a) it triples the scope (tiny SPL templating engine + build-time
   renderer + cloud-deployer integration contract + tests), (b) it
   breaks the "what you read in the sidecar is what you run in Splunk"
   round-trip invariant the catalogue currently honours, and (c) the
   first-order win — auditable thresholds — does not need it. Re-open
   as ADR-NNNN-future once the descriptive layer is in place and the
   lift loop has demonstrated the rubric works.

C. **Unstructured `thresholdRationale: string` field.** Single
   string at the UC root, free-form prose. Solves only the lift-loop
   audit problem (the rubric can check non-empty + length). Rejected
   because (i) it does not address the recommender TA, cloud deployer,
   evidence packs, or search UI consumers; (ii) it forces every UC to
   collapse N thresholds into one paragraph; (iii) it has no machine
   join key, so the downstream tools cannot index by threshold name.

D. **External sidecar JSON file per UC: `data/thresholds/UC-X.Y.Z.json`.**
   Mirrors the `data/crosswalks/` shape. Rejected because thresholds
   are uniquely UC-scoped — they belong with the UC, not in a separate
   coordinating store. The sidecar pattern is appropriate for data the
   build derives from many UCs (crosswalks, ledgers); thresholds are
   primary content authored alongside the SPL.

E. **Reuse `controlTest`** (`positiveScenario`, `negativeScenario`,
   `fixtureRef`). Rejected — `controlTest` is about
   "what should/shouldn't fire", not about numeric tuning knobs.
   Conflating the two would muddy both fields and lose schema clarity.

F. **`thresholds` as a single object keyed by threshold name**, not
   an array of objects each with `name`. More compact JSON, but
   loses ordering (which matters for authoring readability) and
   forces a deduplication contract at JSON-schema level that's
   awkward with `additionalProperties: false`. Rejected on
   ergonomic grounds.

## Migration shape (informative, not part of the decision)

The expected sequence of follow-up PRs, in dependency order, each
small enough to be reviewed independently:

1. **Schema PR** — adds the field to `schemas/uc.schema.json`, bumps
   to `1.8.0`, updates the schema changelog at
   [`schemas/changelogs/uc.md`](../../schemas/changelogs/uc.md), adds a
   structural test that the new field is optional and that the
   existing 7,929 sidecars all remain valid. **Code only; no UC
   content changes.**
2. **Generator PR** — adds the verb
   `python -m splunk_uc generate-thresholds --auto` that scans every
   UC's `spl` for regex-matched tunable literals, emits a single-entry
   `thresholds: [{...}]` with `requiresSmeReview = true`. Includes the
   shim and a `--dry-run` mode. **Code only; the verb produces a
   diff but does not write to sidecars on its own.**
3. **Back-fill PR (one-shot)** — runs the generator against the full
   catalogue and commits the resulting sidecar diff in one batch.
   Expected size: ~6,500 sidecar changes, ~10K lines additive. The
   commit will be large but mechanical; reviewer focus is on the
   audit/test green-light, not line-by-line content review.
4. **Audit PR** — adds `audit-thresholds` to `src/splunk_uc/audits/`,
   wires it into the dispatch (`python -m splunk_uc`), and into
   `.github/workflows/validate.yml` Phase 5.x. Audit checks
   (a) `thresholds[].splVariable` matches a literal in the UC's `spl`,
   (b) tier-1 UCs with `thresholds[]` have at least one non-arbitrary
   `source`, (c) `name` is unique within the UC. **Code + workflow
   wiring only.**
5. **Lift-loop wiring PR** — `gold_profile_v3.py` (or extends
   `gold_profile_v2.py`) to read `thresholds[].rationale` and score
   the threshold-rationale dimension. **Code only.**
6. **Recommender TA PR** — recommender app reads `thresholds[]` and
   renders a "Configure thresholds" page at install. **Generator
   change only; recommender JSON output gains a `thresholds` block.**
7. **Cloud deployer PR (future, separate ADR)** — parametric SPL
   substitution; out of scope here.

Each PR is independently mergeable. PRs 1–4 unblock the lift loop
(P12 first cut). PRs 5–6 deliver the recommender and quality wins.
PR 7 is the long-tail cloud-deployer story.

## Links

- Related code:
  [`schemas/uc.schema.json`](../../schemas/uc.schema.json),
  [`schemas/changelogs/uc.md`](../../schemas/changelogs/uc.md),
  [`src/splunk_uc/audits/gold_profile.py`](../../src/splunk_uc/audits/gold_profile.py),
  [`src/splunk_uc/audits/gold_profile_v2.py`](../../src/splunk_uc/audits/gold_profile_v2.py)
- Related docs:
  [`docs/gold-standard-template.md`](../gold-standard-template.md),
  [`docs/gold-standard-authoring-playbook.md`](../gold-standard-authoring-playbook.md),
  [`docs/superpowers/specs/2026-05-17-content-quality-lift-loop-design.md`](../superpowers/specs/2026-05-17-content-quality-lift-loop-design.md),
  [`docs/health-check-2026-progress.md`](../health-check-2026-progress.md) §P12
- Related ADRs:
  [ADR-0007](0007-json-as-source-of-truth.md) (JSON as SoT — preserved),
  [ADR-0009](0009-generated-artefact-policy.md) (generated artefact policy —
  the generator + back-fill PR fall under this),
  [ADR-0011](0011-schema-lineage-governance.md) (schema lineage —
  the v1.7.0 → v1.8.0 bump is governed by this)
- Superseded by: —
- Closes: P12 first cut (per-UC `thresholds` field scaffold);
  unblocks the lift-loop threshold-rationale rubric scoring

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** American Institute of Certified Public Accountants. (2017). *Trust Services Criteria (2017) for Security, Availability, Processing Integrity, Confidentiality, and Privacy*. AICPA & CIMA. SOC 2 / TSP Section 100. https://www.aicpa-cima.com/topic/audit-assurance/soc-suite-of-services

<a id="ref-2"></a>**[2]** Anthropic, et al. (2026). *Model Context Protocol Specification*. Anthropic PBC. Retrieved May 11, 2026, from https://modelcontextprotocol.io/

<a id="ref-3"></a>**[3]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-4"></a>**[4]** European Parliament and Council of the European Union. (2022, December). *Regulation (EU) 2022/2554 — Digital Operational Resilience Act (DORA)*. Official Journal of the European Union, L 333. ELI: reg/2022/2554. https://eur-lex.europa.eu/eli/reg/2022/2554/oj

<a id="ref-5"></a>**[5]** International Organization for Standardization. (2022). *ISO/IEC 27001:2022 — Information security, cybersecurity and privacy protection — Information security management systems — Requirements*. ISO/IEC. ISO/IEC 27001:2022. https://www.iso.org/standard/27001

<a id="ref-6"></a>**[6]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-7"></a>**[7]** Splunk Inc. (2026). *Splunk Cloud Platform Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/SplunkCloud

<a id="ref-8"></a>**[8]** U.S. Department of Defense. (2024). *Cybersecurity Maturity Model Certification (CMMC) 2.0* (2.0). Office of the Under Secretary of Defense for Acquisition and Sustainment. https://dodcio.defense.gov/CMMC/

### Related repository documents

- [`docs/adr/0007-json-as-source-of-truth.md`](0007-json-as-source-of-truth.md)
- [`docs/adr/0009-generated-artefact-policy.md`](0009-generated-artefact-policy.md)
- [`docs/adr/0011-schema-lineage-governance.md`](0011-schema-lineage-governance.md)
- [`docs/gold-standard-authoring-playbook.md`](../gold-standard-authoring-playbook.md)

### Cited by

- [`docs/adr/README.md`](README.md)

<!-- END-AUTOGENERATED-SOURCES -->
