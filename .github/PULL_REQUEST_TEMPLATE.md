<!--
Thanks for contributing to splunk-monitoring-use-cases!

Please fill in the sections below. Delete anything that doesn't apply.
-->

## Summary

<!-- One or two sentences describing what this PR changes and why. -->

## Type of change

<!-- Tick one or more. -->

- [ ] New use case(s) added
- [ ] Existing use case(s) improved (SPL, fields, KFP, references, MITRE, …)
- [ ] Build pipeline / script change
- [ ] Dashboard (UI / UX) change
- [ ] Splunkbase content pack (TA / ITSI / ES) change
- [ ] Documentation-only change
- [ ] Governance / process change
- [ ] Bug fix

## Affected use cases / categories

<!-- List UC IDs, subcategory ranges, or category numbers touched. -->

## Validation

<!-- Confirm the things that automated CI cannot. -->

- [ ] Ran `python3 build.py` locally and committed all regenerated artefacts
      (`data.js`, `catalog.json`, `llms.txt`, `llms-full.txt`, `sitemap.xml`,
      `api/*.json`).
- [ ] Ran `python3 validate_md.py` (or `python3 scripts/audit_uc_structure.py --full`).
- [ ] SPL examples have been eyeballed for syntax errors.
- [ ] If adding a new **Splunkbase app reference**, the `Splunkbase #NNNN`
      ID is correct (verified on splunkbase.splunk.com).
- [ ] If adding a new **MITRE ATT&CK** mapping, the technique ID is valid.
- [ ] If adding a new category or subcategory, updated `non-technical-view.js`
      (per `.cursor/rules/non-technical-sync.mdc`).
- [ ] If bumping the version, `VERSION`, `CHANGELOG.md` and the release-notes
      block in `index.html` all agree (per `.cursor/rules/versioning.mdc`).

## Screenshots / SPL excerpts

<!-- Paste renderings, before/after SPL, or dashboard screenshots if the
     change is visual. -->

## Related issues

<!-- "Fixes #NNN", "Refs #NNN", "Closes #NNN", or "None". -->
