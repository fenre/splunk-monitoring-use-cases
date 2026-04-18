# `scripts/archive/` — completed one-shot generators

This directory holds Python scripts that played a defined role during a
specific phase of the catalogue's evolution and have **completed their
authoring pass**. They are kept under version control as **audit-replay
tooling**: anyone reviewing a historical change should be able to re-run
the generator that produced it and verify the output is identical to
what is in `main` today.

These scripts are **not invoked by CI** and **should not be edited** as
part of routine catalogue updates. If a future need arises that overlaps
with one of these generators, prefer to fork the script into a new
phase-specific generator under `scripts/` (so the historical replayability
of the archive copy is preserved) rather than editing the archived copy
in place.

## What lives here

| Script | Phase / purpose | Status |
| --- | --- | --- |
| `_bootstrap_phase2_3_data.py` | Phase 2.3 authoring — bootstraps the per-regulation content fixture (`data/per-regulation/phase2.3.json`) consumed by the live `scripts/generate_phase2_3_per_regulation.py` generator. | Completed; fixture is committed. **Default mode is `--check` (read-only).** Hand-applied fixes (CIM-model normalisation, monitoring-type tweaks) live in the fixture; `--write` would clobber them. |
| `scaffold_exemplars.py` | Phase 1.6 authoring — scaffolded the 40 exemplar UCs across `cat-22.35..49` (sidecars + Phase-1.6 markdown block) seeded from in-script tuples. | Completed; sidecars and markdown block are committed and have since been enriched by Phase 2.x derivative-regulation generators. **Default mode is `--check` (read-only).** `--write` would drop those enrichments. |
| `normalize_compliance_clauses.py` | Phase A of the regulation-coverage gap closure — one-shot normalisation of clause IDs across the OSCAL crosswalks (DORA, ISO 27001:2022, SOC 2 2017 TSC, PCI-DSS 4.0, SOX-ITGC). | Completed; normalised IDs are committed. |
| `migrate_uc_markdown_to_json.py` | UC migration pipeline — one-shot lift of cat-22 markdown UCs into JSON sidecars under `use-cases/cat-*/`. Downstream tooling now reads JSON first. | Completed; sidecars are committed. |
| `generate_phase_e_signoffs.py` | Phase E of the regulation-coverage gap closure — seeded the SME / peer / legal sign-off ledgers with `pending` rows for every regulation-bearing UC. | Completed; seeds are committed and individual sign-offs are now authored by hand. |
| `fill_false_positives.py` | Phase 1.6 — generated the standardised `Known false positives:` line for ~4,008 security-relevant UCs (cats 9, 10, 14, 17, 22). | Completed; KFP coverage at 100 % on security categories. |
| `fill_mitre_mappings.py` | Phase 1.6 — added MITRE ATT&CK mappings to security-relevant UCs (cats 9, 10, 17). | Completed; coverage targets met (cat-9 ≥ 80 %, cat-10 ≥ 80 %, cat-17 ≥ 90 %). |
| `fill_references.py` | Phase 1.6 — populated the `References:` line for every UC (6,304 / 6,304 at the time). | Completed; references coverage at 100 %. |
| `redistribute_meraki.py` | One-shot reassignment of Cisco Meraki UCs across categories after the cat-22 split. | Completed. |
| `rename_cat22_control_themes.py` | One-shot rename of cat-22 sub-area "control themes" to align with the regulator-facing taxonomy. | Completed. |
| `retag_meta_multi_ucs.py` | One-shot retag of the catalogue-wide "meta" UCs that span multiple subcategories. | Completed. |
| `fix_cim_spl_alignment.py` | Companion fix script for `scripts/audit_cim_spl_alignment.py`. The audit is advisory and the fix has been run; remaining drift is now caught at PR time by the live audit. | Completed; live audit catches new drift. |

## Re-running an archived script

```bash
# from repo root
python3 scripts/archive/<script>.py [--check]
```

`--check` mode (where supported) is non-destructive and reports drift
between the script's expected output and what's currently committed.

Most archived generators expect their output paths relative to the repo
root, so they will work as-is from any clone. If a script depends on a
fixture that has since moved, the failure will be a clear "file not
found" rather than silent drift.

## Promotion / demotion policy

* **Demote** a script to this directory when it has finished its
  authoring pass and is not referenced by:
  - Any `.github/workflows/*.yml` step
  - Any markdown file under `docs/` as a "regenerate with" instruction
  - Any other script as a `subprocess.run([...])` target
* **Promote** a script back to `scripts/` only by forking it into a new
  phase-specific generator. Editing the archived copy in place breaks
  the audit-replay guarantee for past releases.
