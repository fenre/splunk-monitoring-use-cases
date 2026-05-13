# Workflow audit

> Single-page inventory of every GitHub Actions workflow under
> [`.github/workflows/`](../.github/workflows/). Pairs with
> [`docs/ci-architecture.md`](ci-architecture.md), which is the long-form
> per-job description, and with the §P2.5 acceptance criterion in
> [`docs/health-check-2026-progress.md`](health-check-2026-progress.md).
>
> Generated 2026-05-13 at HEAD. Whenever a workflow is added, removed,
> retriggered onto a different cadence, or starts using a new third-party
> action, **update this file in the same PR** — it is the single
> per-workflow reference and there is no auto-generator behind it yet.

## Inventory (14 workflows)

| Workflow                                           | Purpose                                                                  | Trigger surface                                                              | Cadence                                  | Runs-on        | Timeout | Writes to repo? | Pinned third-party actions (see [Pin map](#third-party-action-pin-map)) |
|----------------------------------------------------|--------------------------------------------------------------------------|------------------------------------------------------------------------------|------------------------------------------|----------------|--------:|-----------------|-------------------------------------------------------------------------|
| [`validate.yml`](../.github/workflows/validate.yml)               | Merge gate — 5 parallel jobs (`lint`, `audits-content`, `audits-build`, `mcp`, `frontend`). | `pull_request` only (paths-filtered)                                          | per PR                                   | `ubuntu-latest` | 30m/job | No              | `checkout`, `upload-artifact`                                          |
| [`pages.yml`](../.github/workflows/pages.yml)                     | Builds and deploys the static site + signed-provenance attestations to GitHub Pages. | `push` to `main`, `workflow_dispatch`                                         | every push to `main`                     | `ubuntu-latest` | 30m     | No (Pages only) | `checkout`, `upload-artifact`, `attest-build-provenance`, `configure-pages`, `upload-pages-artifact`, `deploy-pages` |
| [`release.yml`](../.github/workflows/release.yml)                 | Packages and publishes TA / DA / recommender `.spl` artefacts as a GitHub Release on a semver tag. | `push` of `v*.*.*` tag, `workflow_dispatch`                                   | per release                              | `ubuntu-latest` | 30m     | No (Release)    | `checkout`, `attest-build-provenance`, `upload-artifact`, `download-artifact`, `softprops/action-gh-release` |
| [`codeql.yml`](../.github/workflows/codeql.yml)                   | GitHub CodeQL static analysis (Python + JavaScript).                    | `push`/`pull_request` to `main`; weekly cron                                  | Mon 06:17 UTC + PRs/pushes touching `*.py`/`*.js`/`*.mjs`/`*.ts` | `ubuntu-latest` | 30m     | No              | `checkout`, `github/codeql-action/{init,autobuild,analyze}`             |
| [`dependency-review.yml`](../.github/workflows/dependency-review.yml) | Blocks PRs introducing dependencies with critical CVEs or non-permissive licenses. | `pull_request` only                                                          | per PR                                   | `ubuntu-latest` | 5m      | No              | `checkout`, `actions/dependency-review-action`                          |
| [`gitleaks.yml`](../.github/workflows/gitleaks.yml)               | Secret-leak detection — defence-in-depth backup to the `gitleaks` pre-commit hook. | `push`/`pull_request` to `main`; weekly cron                                  | Tue 03:42 UTC + every PR/push to `main`  | `ubuntu-latest` | 30m     | No              | `checkout`, `gitleaks/gitleaks-action`                                  |
| [`link-check.yml`](../.github/workflows/link-check.yml)           | Markdown / doc external-link health audit; opens an issue on failure.    | `workflow_dispatch`, weekly cron                                              | Mon 06:00 UTC                            | `ubuntu-latest` | 20m     | Issue           | `checkout`, `upload-artifact`                                          |
| [`stewardship.yml`](../.github/workflows/stewardship.yml)         | Weekly stewardship digest — writes `dist/stewardship-digest.{json,md}`, opens/updates a tracking issue. | `workflow_dispatch`, weekly cron                                              | Mon 08:00 UTC                            | `ubuntu-latest` | 30m     | Issue + artifact | `checkout`, `upload-artifact`                                          |
| [`regulatory-watch.yml`](../.github/workflows/regulatory-watch.yml) | Probes regulator-published artefacts (NIST OSCAL, MITRE ATT&CK<sup class="ref">[<a href="#ref-1">1</a>]</sup>, PCI SSC, HHS, EUR-Lex), commits manifest deltas, opens issues. | `workflow_dispatch`, weekly cron                                              | Mon 09:00 UTC                            | `ubuntu-latest` | 30m     | Commit + Issue  | `checkout`, `upload-artifact`                                          |
| [`splunkbase-sync.yml`](../.github/workflows/splunkbase-sync.yml) | Refreshes `data/splunkbase-catalog.json` from the public Splunkbase<sup class="ref">[<a href="#ref-2">2</a>]</sup> REST API; opens a PR with diff. | `workflow_dispatch`, weekly cron                                              | Tue 08:00 UTC                            | `ubuntu-latest` | 20m     | PR              | `checkout`, `peter-evans/create-pull-request`, `upload-artifact`        |
| [`build-reproducibility.yml`](../.github/workflows/build-reproducibility.yml) | Asserts two consecutive `--reproducible` builds against the same HEAD produce byte-identical `dist/integrity.json`. | `workflow_dispatch`, nightly cron, `pull_request` (paths-filtered to build pipeline) | 03:00 UTC nightly + on build-pipeline PRs | `ubuntu-latest` | 30m     | No              | `checkout`, `upload-artifact`                                          |
| [`uc-tests.yml`](../.github/workflows/uc-tests.yml)               | UC sample-data fixtures validation (pre-flight). Production runs require a live Splunk and are manual. | `push`/`pull_request` (paths-filtered), `workflow_dispatch`                   | per relevant PR; manual                  | `ubuntu-latest` | 30m     | No              | `checkout`, `upload-artifact`                                          |
| [`uc-manifest.yml`](../.github/workflows/uc-manifest.yml)         | Generates `manifest-all.json` and validates UC count / payload shape.    | `push`/`pull_request` (paths-filtered)                                        | per relevant PR                          | `ubuntu-latest` | 30m     | No              | `checkout`                                                              |
| [`traffic.yml`](../.github/workflows/traffic.yml)                 | Archives GitHub repo traffic data daily (GitHub retains 14 days; this cache extends visibility). | `workflow_dispatch`, daily cron                                               | 00:00 UTC daily                          | `ubuntu-latest` | 30m     | Commit          | `checkout`                                                              |

**Notes on the table:**

- All workflows run on `ubuntu-latest` and use composite setup
  (`./.github/actions/setup-python` / `./.github/actions/setup-node`) for
  toolchain provisioning — see [Composite actions](#composite-actions)
  for the contract.
- "Writes to repo?" is the answer to the question _"can this workflow
  mutate the repository or a downstream surface without a human in the
  loop?"_ Anything other than `No` requires extra scrutiny when the
  pinned actions are bumped, because a compromised action would
  inherit those write permissions.
- The §P2-F19 migration (2026-05-12) moved every `actions/setup-python`
  pin into the composite, so the table above only shows third-party
  pins. The composite's pins are documented separately in
  [Composite actions](#composite-actions).

## Cadence & SLA digest

The numeric cadence table above is most useful as a calendar:

```
Mon 06:00 UTC   link-check.yml         (weekly)
Mon 06:17 UTC   codeql.yml             (weekly + on PR/push)
Mon 08:00 UTC   stewardship.yml        (weekly)
Mon 09:00 UTC   regulatory-watch.yml   (weekly)
Tue 03:42 UTC   gitleaks.yml           (weekly + on PR/push)
Tue 08:00 UTC   splunkbase-sync.yml    (weekly)
Daily 00:00 UTC traffic.yml            (every day)
Daily 03:00 UTC build-reproducibility.yml (every night)
Per-PR          validate.yml, dependency-review.yml, gitleaks.yml (push/PR), codeql.yml (push/PR), uc-manifest.yml, uc-tests.yml
Per-push-main   pages.yml
Per-tag         release.yml
```

Two design conventions encoded above:

1. **Monday cluster, then Tuesday backstop.** All four weekly
   maintenance probes (`link-check`, `codeql`, `stewardship`,
   `regulatory-watch`) fire on Monday between 06:00 and 09:00 UTC so a
   maintainer's first triage window of the week sees the whole batch.
   `gitleaks` and `splunkbase-sync` are staggered into Tuesday so the
   triage backlog never doubles up.
2. **Nightly reproducibility, daily traffic.** The two `daily` jobs
   are intentionally separated by 3 hours so that if `traffic.yml`
   (which holds the `contents: write` permission) ever races
   `build-reproducibility.yml` (which uploads large artefacts), the
   schedule alone keeps the runner pool from contending.

## Third-party action pin map

Every reference below is pinned to a 40-character commit SHA with a
`# vX.Y.Z` tag-comment. The pin policy and audit are documented in
[`docs/ci-architecture.md` §Pinning policy](ci-architecture.md#pinning-policy);
the enforcing audit is `python3 -m splunk_uc audit-action-pins`. Comment
drift (someone bumps the SHA without re-pointing the tag-comment) is
also caught by that audit.

| Action                                              | Pin SHA                                    | Comment | Used by                                                       |
|-----------------------------------------------------|--------------------------------------------|---------|---------------------------------------------------------------|
| `actions/checkout`                                  | `de0fac2e4500dabe0009e67214ff5f5447ce83dd` | `v6.0.2` | every workflow that interacts with the repo tree              |
| `actions/upload-artifact`                           | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | `v7.0.1` | `validate`, `pages`, `release`, `link-check`, `stewardship`, `regulatory-watch`, `splunkbase-sync`, `build-reproducibility`, `uc-tests` |
| `actions/download-artifact`                         | `3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c` | `v8.0.1` | `release.yml`                                                 |
| `actions/attest-build-provenance`                   | `a2bbfa25375fe432b6a289bc6b6cd05ecd0c4c32` | `v4.1.0` | `pages.yml`, `release.yml`                                    |
| `actions/configure-pages`                           | `45bfe0192ca1faeb007ade9deae92b16b8254a0d` | `v6.0.0` | `pages.yml`                                                   |
| `actions/upload-pages-artifact`                     | `fc324d3547104276b827a68afc52ff2a11cc49c9` | `v5.0.0` | `pages.yml`                                                   |
| `actions/deploy-pages`                              | `cd2ce8fcbc39b97be8ca5fce6e763baed58fa128` | `v5.0.0` | `pages.yml`                                                   |
| `actions/dependency-review-action`                  | `a1d282b36b6f3519aa1f3fc636f609c47dddb294` | `v5.0.0` | `dependency-review.yml`                                       |
| `github/codeql-action/init`                         | `68bde559dea0fdcac2102bfdf6230c5f70eb485e` | `v4.35.4` | `codeql.yml`                                                  |
| `github/codeql-action/autobuild`                    | `68bde559dea0fdcac2102bfdf6230c5f70eb485e` | `v4.35.4` | `codeql.yml`                                                  |
| `github/codeql-action/analyze`                      | `68bde559dea0fdcac2102bfdf6230c5f70eb485e` | `v4.35.4` | `codeql.yml`                                                  |
| `gitleaks/gitleaks-action`                          | `ff98106e4c7b2bc287b24eaf42907196329070c7` | `v2.3.9` | `gitleaks.yml`                                                |
| `peter-evans/create-pull-request`                   | `5f6978faf089d4d20b00c7766989d076bb2fc7f1` | `v8.1.1` | `splunkbase-sync.yml`                                         |
| `softprops/action-gh-release`                       | `b4309332981a82ec1c5618f44dd2e27cc8bfbfda` | `v3.0.0` | `release.yml`                                                 |

**14 distinct third-party action references, 11 SHA values** — the
three `github/codeql-action/*` entries share one upstream SHA. All
references carry the `# vX.Y.Z` annotation; the audit fails on any
unannotated or stale comment.

## Composite actions

Composite actions live in-tree under `.github/actions/`. Their job is
to (a) put the `actions/setup-{python,node}@<sha>` pin in one file
instead of N workflow files and (b) standardise the install steps
(`pip install -r .github/requirements-ci.txt`, `pip install -e
.[<extras>]`, `npm ci --no-audit --no-fund`).

| Composite                                                                      | Wraps                                          | Default version | Extras                                              |
|--------------------------------------------------------------------------------|------------------------------------------------|-----------------|-----------------------------------------------------|
| [`./.github/actions/setup-python`](../.github/actions/setup-python/action.yml) | `actions/setup-python` SHA-pinned, with `pip` cache | Python 3.12     | `install-audits`, `install-extras` (e.g. `test`, `mcp`) |
| [`./.github/actions/setup-node`](../.github/actions/setup-node/action.yml)     | `actions/setup-node` SHA-pinned, with `npm` cache   | Node 20         | `install-deps` (runs `npm ci` when `true`)          |

The structural guard
[`tests/build/test_composite_actions.py::test_no_workflow_pins_setup_python_directly`](../tests/build/test_composite_actions.py)
blocks any PR that re-introduces a raw `actions/setup-python@<sha>`
pin in a workflow file.

## How to keep this doc honest

1. When a workflow is added, removed, or has its trigger / cadence
   changed, edit the **Inventory** table and the **Cadence & SLA
   digest** in the same PR.
2. When a third-party action pin is bumped (manually or via
   Renovate/Dependabot), edit the **Third-party action pin map** in
   the same PR. The merging audit
   (`python3 -m splunk_uc audit-action-pins`) does not enforce that
   this doc stays in sync — that is intentional: a noisy doc-sync
   check on every Dependabot PR would create more drift than it
   prevents. Treat the inventory as a maintainer's notebook, not a
   gate.
3. Whenever a workflow gains a new responsibility (writes back to the
   repo, opens issues / PRs, mutates a release surface), update the
   **"Writes to repo?"** column — the column is the security-review
   shortcut for "what does this workflow's `GITHUB_TOKEN` need to be
   able to do?".

## Related docs

- [`docs/ci-architecture.md`](ci-architecture.md) — long-form
  per-job description, including the `validate.yml` 5-job partition,
  troubleshooting playbooks, and the pin / audit policy.
- [`SECURITY.md`](../SECURITY.md) — supply-chain risk classes the
  pin audit catches.
- [`docs/rollback-playbook.md`](rollback-playbook.md) — when to revert
  a workflow change after a bad CI signal.
- [`docs/capacity-and-staffing.md`](capacity-and-staffing.md) — when
  to skip CI work in solo-maintainer mode.
- [`docs/health-check-2026-progress.md`](health-check-2026-progress.md)
  — §P2.5 acceptance criterion that this file satisfies.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** MITRE Corporation. (2026). *MITRE ATT&CK Knowledge Base*. MITRE Engenuity. https://attack.mitre.org/

<a id="ref-2"></a>**[2]** Splunk Inc. (2026). *Splunkbase — the Splunk app marketplace*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://splunkbase.splunk.com/

### Related repository documents

- [`docs/ci-architecture.md`](ci-architecture.md)

### Cited by

- [`docs/ci-architecture.md`](ci-architecture.md)
- [`docs/f8-frontend-hardening-inventory.md`](f8-frontend-hardening-inventory.md)
- [`docs/health-check-2026-progress.md`](health-check-2026-progress.md)

<!-- END-AUTOGENERATED-SOURCES -->
