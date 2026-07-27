# Use-case editorial review standard

This standard defines what a catalogue maintainer must verify before recording a
use case as documentation-reviewed. It does **not** claim that the search ran in
a customer environment. Runtime validation remains a separate activity.

## Required evidence

Review each use case individually against primary sources:

1. Splunk Help or the applicable Splunkbase listing for platform commands,
   configuration, supported versions, add-on IDs, sourcetypes, CIM datasets,
   and normalized fields.
2. The vendor's product documentation for APIs, event types, field names,
   permissions, and configuration paths.
3. The regulator or standards publisher for legal and compliance claims.
4. MITRE ATT&CK itself for technique mappings.

Community posts may explain behavior but cannot be the sole authority for a
production claim. Record at least four useful references when four independent
primary sources exist. Never add weak links merely to meet a count.

## Per-UC acceptance criteria

- The title describes the actual search behavior.
- The SPL uses documented commands and functions. Every index is explicitly
  presented as a deployment choice; every sourcetype and source field is either
  vendor-defined or clearly labelled as a local convention.
- Thresholds state their units, aggregation window, and tuning assumptions.
- `description` states what is measured, at what grain, and what causes a row.
- `value` states a concrete operational or business outcome without repeating
  the description.
- `dataSources` identifies collection method, source type, required fields,
  and authoritative add-on or API.
- `implementation` is an accurate short deployment summary.
- `detailedImplementation` is bespoke to the use case and covers prerequisites,
  collection, field verification, saved-search configuration, validation,
  alerting, dashboards, runbook actions, and troubleshooting. Generic example
  scripts and placeholder indexes are forbidden.
- Positive and negative control tests name concrete input values and expected
  rows. Documentation review checks their logic; it does not imply execution.
- False positives identify plausible named causes and a safe distinguishing or
  suppression procedure.
- Evidence and exclusions are specific, achievable, and do not overstate
  regulatory assurance.
- References point to the claims they support and include a retrieval date.
- Review metadata must not imply SME or runtime sign-off that did not occur.

## Review outcome

A documentation review may update `lastReviewed` and identify the maintainer in
`reviewer`, but `status: verified` retains its schema meaning of production-ready
and SME-signed-off. Do not introduce that status solely because this editorial
review passed. Existing verified status is challenged and removed when the
available evidence does not support it.

## Corpus gates

After each review batch, run:

```text
audit-uc-structure --full
audit-content-quality --files ... --severity fail
audit-template-provenance --files ... --check --max-any 0
audit-gold-profile-v2 --files ...
audit-spl-hallucinations
audit-spl-references --check
```

The first four are per-file acceptance gates. The final two are corpus-wide
advisory checks until all historical findings have been reviewed.
