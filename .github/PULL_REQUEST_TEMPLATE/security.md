<!--
Security-relevant PR template.

Pick this template via:
  https://github.com/<owner>/splunk-monitoring-use-cases/compare/main...<branch>?template=security.md

Use it for: secret-handling changes, recommender-TA hardening (P13),
CSP / XSS fixes, supply-chain controls (CodeQL, SBOM, Sigstore), MCP
server hardening, anything that crosses a trust boundary.
-->

## Summary

<!-- What changed and which threat it mitigates. -->

## Threat addressed

- [ ] **STRIDE category**: <Spoofing | Tampering | Repudiation | Information disclosure | Denial of service | Elevation of privilege>
- [ ] **CWE / CVE reference (if any)**: ...
- [ ] **Affected component**: <recommender-TA | MCP server | build pipeline | frontend | CI/CD | docs only>

## Validation

- [ ] No secrets, tokens, certificates, or private keys added.
      `gitleaks` (pre-commit) clean.
- [ ] If MCP-relevant: `pytest mcp/` green; tool-schema drift check green.
- [ ] If frontend: CSP report-only check (or strict CSP) green; no new
      `innerHTML` sinks; SRI on third-party assets.
- [ ] If recommender-TA: `pytest tests/recommender_ta/` green; AppInspect
      green; no new file/network/subprocess capability.
- [ ] If supply-chain: dependency-review-action green; CodeQL green; no
      new pinned `latest` tags on third-party actions.

## Rollback

<!--
Security regressions are P0 incidents. Default soak window is
24 hours of active monitoring; bias toward fast rollback.
Read `docs/rollback-playbook.md` §"Per-phase contract → Security"
for the full contract.
-->

- Revert command:    `git revert <merge-sha>`
- Forced rollout?:   <yes/no — if yes, justify>
- Affected releases: <which `.spl` / dist bundles include the fix>
- Soak window:       <24h active monitoring | longer + justification>
- Kill switch:       <feature flag | env var | none + justification>
- Cache invalidation: <none | Pages purge | CDN-edge | downstream MCP refresh>

## Disclosure path

- [ ] If this is a fix for a privately-reported issue, **`SECURITY.md`
      timeline followed**.
- [ ] If this is a hardening (no known exploit), public CHANGELOG entry
      describes the change without revealing exploit details.

## Documentation touched

- [ ] `SECURITY.md` updated if scope / threat model changed.
- [ ] `docs/threat-model-recommender-ta.md` (P13) updated if applicable.
- [ ] CHANGELOG.md entry under `## [Unreleased]` → `### Security`.

## Related issues

<!-- Fixes #NNN, GHSA-... (if applicable). -->
