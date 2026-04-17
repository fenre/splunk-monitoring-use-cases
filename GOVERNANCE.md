# Project Governance

This document describes how `splunk-monitoring-use-cases` is run: who makes
decisions, how those decisions are made, and how anyone can influence the
direction of the project. It is deliberately lightweight — this is a
volunteer-driven documentation project, not a software company — but we want
the decision-making process to be transparent.

## Project structure

There are three participant roles:

### 1. Users

Anyone who consumes the catalog — browsing the dashboard, installing the
Splunkbase TA / ITSI / ES content packs, or calling the JSON API. Users have
no formal commitments to the project.

### 2. Contributors

Anyone who has had a pull request merged, opened a well-formed issue, or
meaningfully improved a use case, documentation page, or build script.
Contributors are acknowledged in `CONTRIBUTING.md` and GitHub's automatic
contributor list.

### 3. Maintainers

Contributors with commit access who have ongoing responsibility for the
health of the project. Current maintainers are listed in
[`.github/CODEOWNERS`](.github/CODEOWNERS).

Maintainers commit to:

- Reviewing and triaging issues and pull requests within a reasonable time
  (target: 10 business days)
- Following the `CODE_OF_CONDUCT.md` and enforcing it when necessary
- Keeping the CI green on `main`
- Publishing at least one patch or minor release per quarter
- Responding to security disclosures per `SECURITY.md`

## Decision-making process

Most decisions are made by **lazy consensus**: a maintainer proposes a change
via a pull request or issue, and if no other maintainer objects within a
reasonable time (typically 7 days for non-urgent changes), the change is
accepted.

For **controversial or breaking changes** (e.g. changing the catalog schema,
removing a category, altering the build pipeline in a way that forks cannot
easily follow), the following process applies:

1. A maintainer opens a **Request for Comments (RFC)** issue with the `rfc`
   label, describing the change and rationale.
2. The RFC remains open for at least **14 days** to gather feedback from
   contributors and users.
3. Maintainers make the final decision, with a visible summary of comments
   considered. A decision against majority feedback requires a written
   justification in the RFC.
4. If maintainers disagree among themselves and cannot reach consensus within
   another 14 days, the lead maintainer (the first name in `CODEOWNERS`) has
   final authority.

## How to become a maintainer

Maintainership is based on **sustained, high-quality contribution** — not
seniority or political influence. A contributor can nominate themselves (or be
nominated by a maintainer) after:

- Six months of regular contributions (≥10 merged PRs across different areas)
- Demonstrated ability to review others' pull requests constructively
- Consistent adherence to the `CODE_OF_CONDUCT.md`
- Sponsorship from at least one existing maintainer

Nominations are discussed privately among maintainers and the decision is by
simple majority. The new maintainer is added to `CODEOWNERS` and announced in
the next release notes.

## Stepping down

Any maintainer may step down at any time by opening a pull request removing
their name from `CODEOWNERS` (or, in cases of prolonged absence, having it
removed by consensus of the remaining maintainers). Former maintainers
continue to be acknowledged in the project's history.

## Conflict of interest

Maintainers must disclose any employer, client, or commercial interest that
could influence catalog content (e.g. being employed by Splunk, a vendor of a
referenced TA, or a regulator whose framework is represented). Disclosures
live in `CODEOWNERS` comments and must be renewed annually.

## Non-goals of this governance document

- We do **not** aim to become a Linux Foundation / CNCF-style project. The
  catalog is intentionally small-team and opinionated.
- We do **not** accept commercial sponsorships or bounties. Pull requests that
  promote specific vendors beyond what the use case legitimately requires will
  be closed.
- We do **not** have a formal trademark policy; the project name and dashboard
  look-and-feel are CC-BY-compatible.

## Amendments

This document can be changed via the same RFC process described above. The
current version is maintained at
<https://github.com/fenre/splunk-monitoring-use-cases/blob/main/GOVERNANCE.md>.

## Contact

For governance questions that cannot be discussed in public issues, contact
the lead maintainer at **fsudmann@gmail.com**.
