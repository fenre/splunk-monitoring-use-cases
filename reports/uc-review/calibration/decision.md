# UC review calibration — decision record (2026-10-26)

Calibration set: 150 UCs, stratified across all 25 categories and four
criticality levels, with 53 `status: verified` UCs
([`set.json`](set.json)). Reference: deep review by Claude Opus 5.5 (high)
with web verification ([`reference/deep/`](reference/deep/)). Candidates
reviewed the same UCs as triage batches without web access. Scores come from
`python3 scripts/uc_review_runner.py calibrate score`.

## Reference result

- 103 of 150 UCs `incorrect` (at least one evidence-backed blocker), 47 `rewrite`, none `ok` or `polish`.
- 182 blocker findings, 619 major, 289 minor, 72 needs-verification.
- 124 of 150 UCs (83%) carry a correctness blocker/major or a firewalled blocker, which is the population deep review exists to catch.

Recurring facts behind the blockers: Splunkbase IDs that point at unrelated
apps (617 "Universal Forwarder" is a 404; 1352 is not a Cisco Security
add-on; 4413 is not SOAR; 5076 is not Nutanix), sourcetypes no add-on
produces (`google:gcp:audit`, `aws:trustedadvisor`, `juniper:junos:structured`),
SPL that cannot run (`stats` inside `multisearch`, `current()`/`prev()`,
unquoted dotted field names in `eval`), and grounding guides that carry
the same wrong IDs (`docs/guides/datacenter-fabric-sdn.md`).

## Candidate scores

| Candidate | Finding recall | False-blocker rate | Routing recall | UCs routed | Verdict agreement | Gate |
|---|---|---|---|---|---|---|
| Gemini 3.7 Flash (medium) | 0.10 | 0.50 | 0.85 | 125 / 150 | 0.23 | fail |
| Claude Sonnet 5.5 (high) | 0.46 | 0.16 | 0.98 | 146 / 150 | 0.51 | fail |

The gate in [`docs/uc-text-review-rubric.md`](../../../docs/uc-text-review-rubric.md)
is finding recall ≥ 0.90 and false-blocker rate ≤ 0.10. Routing recall is
the share of the 124 UCs that need deep review which the candidate's
triage record would route there (rule in `splunk_uc.review._routing`,
including the correctness-score ≤ 3 condition added after this run).

Human spot-check labels ([`human-labels.json`](human-labels.json)) are not
yet filled in; scores above are against the unadjusted model reference.
Re-run `calibrate score` after the maintainer completes the 40 spot-checks.

## Decision

1. **Gemini 3.7 Flash is rejected** for triage: it misses nine in ten
   reference findings and half its blockers are wrong.
2. **Claude Sonnet 5.5 (high) becomes the triage default** (the plan's
   fallback), but it also fails the finding-recall gate. Triage records are
   therefore used for routing and as a second opinion, never as the final
   word on a UC.
3. **Deep review covers every operational UC.** With 83% of UCs needing a
   correctness review, any routing rule with acceptable recall sends about
   97% of UCs to deep review anyway, so triage cannot cut heavy-model volume
   on this corpus. Run `deep --all` per category in priority order; keep
   triage for incremental re-reviews of edited UCs.
4. **Personal & Hobbyist Monitoring (cat-25, the fun category) is deferred.**
   6,431 UCs, about 65M input tokens, stay out of the full run until the
   operational catalogue is reviewed. Unscoped `deep`, `triage` and `plan`
   skip that category. `--category cat-25` or `--include-fun` puts it back.
   The five calibration records already written stay in the ledger.
5. **Fix the grounding before the full run.** Several blockers trace back to
   wrong Splunkbase IDs in `docs/guides/*.md`; correcting those guides first
   keeps the deep reviewer from being misled and fixes many UCs at once.
