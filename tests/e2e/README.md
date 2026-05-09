# Splunk UC Recommender — End-to-End Tests (v9.0)

Playwright suite that exercises the live `splunk-uc-recommender`
dashboard against a real Splunk instance. Implements the §13c
verification layer of the v9.0 plan.

## Quick start

### Local — against an existing Splunk you control

1. Install the app on the target Splunk Web (port 8000 typically).
   Either run [`scripts/deploy_to_splunk.sh`](../../scripts/deploy_to_splunk.sh)
   when SSH staging is available, or upload the `.spl` manually via
   *Manage Apps → Install app from file*.
2. Issue a bearer token in *Settings → Tokens* and store it in
   `secrets.env` as `SPLUNK_REST_TOKEN`.
3. Run:

   ```bash
   SPLUNK_E2E_URL="https://splunk:8000" \
   SPLUNK_E2E_TOKEN="$(grep SPLUNK_REST_TOKEN secrets.env | cut -d= -f2-)" \
   npm run test:e2e
   ```

The suite skips itself cleanly when `SPLUNK_E2E_URL` is unset — running
`npm run test:e2e` on a developer machine without Splunk does not fail.

### CI — multi-version Splunk container matrix

`.github/workflows/uc-tests.yml` boots `splunk/splunk:9.0`,
`splunk/splunk:9.4`, and `splunk/splunk:10.0` in parallel jobs, each
running this suite against its own ephemeral instance. The recommender
`.spl` artefact built earlier in the workflow is installed via the
container's `SPLUNK_APPS_URL`/local install hook before the tests run.

## Environment variables

| Variable | Purpose | Required? |
|---|---|---|
| `SPLUNK_E2E_URL` | Splunk Web base URL (e.g. `https://splunk:8000`) | Yes |
| `SPLUNK_E2E_REST_URL` | splunkd REST URL | No (derived) |
| `SPLUNK_E2E_TOKEN` | bearer token w/ `edit_uc_implementations` | Yes |
| `SPLUNK_E2E_USER_TOKEN` | bearer token WITHOUT capability | No |
| `SPLUNK_E2E_APP_ID` | App id (default `splunk-uc-recommender`) | No |

When `SPLUNK_E2E_USER_TOKEN` is unset, the read-only-user spec is
skipped explicitly — never silently passed.

## What the suite asserts

Per the v9.0 plan §13c:

- **Boots without console errors.** A console-error guard fails the
  test on any uncaught error or page-error, with explicit allow-list
  for Splunk Web's known harmless warnings.
- **Dashboard never blank.** First paint must produce at least one of
  `.uc-card`, `.uc-banner`, or `.uc-empty`.
- **Status badges have text.** Every `.uc-status-badge` carries a
  non-empty text label; colour-only badges are an a11y violation.
- **Splunkbase URLs are safe.** Every link in `.uc-sb-item a` matches
  `^https://splunkbase\.splunk\.com/app/\d+/?$`. No path traversal,
  no protocol injection.
- **Modal a11y.** Mark/Edit modal sets `role="dialog"
  aria-modal="true"`, auto-focuses an input, traps focus inside, and
  closes on Escape.
- **Read-only mode.** When the token lacks
  `edit_uc_implementations`, write buttons are hidden and the
  banner does not leak the capability name.
- **Performance ceiling.** First paint < 45s on cold containers (the
  plan's <500ms target is enforced separately by the JS unit
  tests under [`tests/recommender/`](../recommender/)).

## What the suite does NOT do

- It does not provision Splunk. CI does that.
- It does not install the app. `scripts/deploy_to_splunk.sh` or the
  CI install step does that.
- It does not seed KV state. The CI job runs `inputlookup`/REST
  pre-seeds against the implementations KV before invoking the suite.

## Skip semantics

| Condition | Behaviour |
|---|---|
| `SPLUNK_E2E_URL` unset | All tests skipped with a clear reason |
| `SPLUNK_E2E_USER_TOKEN` unset | Only the read-only spec skipped |
| Edit buttons absent | Per-test `test.skip()` (no edit cap on this token) |
| App not installed | First spec fails fast with the missing selector |

## Debugging a failure

- Each failed test uploads a screenshot, video, and trace under
  `tests/e2e/.report/`. The CI job uploads the same as a workflow
  artefact.
- Console errors (the most common silent regression source) appear in
  the failure message body, not just in the trace.
- For local debugging:

  ```bash
  SPLUNK_E2E_URL=... SPLUNK_E2E_TOKEN=... \
    npx playwright test tests/e2e/recommender.spec.ts --debug
  ```

## Why Playwright (not Puppeteer)?

The repo's existing `puppeteer` dependency drives static-site headless
screenshots. For Splunk Web — which is a heavy SPA with auth-bearing
fetches, IFRAMEs for dashboard panels, and CSP-strict rendering —
Playwright's `addInitScript`, console event API, and trace viewer are a
materially better fit. They coexist; Puppeteer handles the static site,
Playwright handles the live app.
