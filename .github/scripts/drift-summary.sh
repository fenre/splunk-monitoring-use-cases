#!/usr/bin/env bash
# Append an actionable recovery hint to the GitHub Actions Job Summary when
# a validate.yml job fails. Invoked from the "Drift summary (on failure)"
# step of audits-content / audits-build / frontend (the drift-heavy jobs)
# with ``if: ${{ failure() }}``.
#
# Rationale: those three jobs run their cascade / build / report ``--check``
# drift gates with ``if: ${{ !cancelled() }}`` so every stale artefact
# surfaces in a single run instead of failing fast on the first one. The
# trade-off is that the failures are scattered across many collapsed step
# logs. This writes a single recovery block to ``$GITHUB_STEP_SUMMARY`` so
# the fix is visible at the top of the run page. See
# docs/ci-architecture.md → "Committed generated artefacts & the drift gates".
#
# Usage: drift-summary.sh <job-name>
set -euo pipefail

job="${1:-this job}"

# No summary sink (e.g. running locally) → print to stdout instead so the
# script is still useful and never errors.
sink="${GITHUB_STEP_SUMMARY:-/dev/stdout}"

{
  echo "## ❌ \`${job}\` failed"
  echo
  echo "Expand the red steps above for the specific failure(s)."
  echo
  echo "**Most common cause:** a stale committed *generated* artefact tripping a \`--check\` drift gate."
  echo
  echo "### Local recovery"
  echo '```bash'
  echo "make preflight        # regenerate every committed derived artefact"
  echo "git add -A && git commit -m 'chore(generated): refresh derived artefacts'"
  echo '```'
  echo
  echo "Reproduce CI's read-only verdict first with \`make preflight-check\`."
  echo 'Details: docs/ci-architecture.md → "Committed generated artefacts & the drift gates".'
} >>"${sink}"
