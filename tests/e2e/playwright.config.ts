// Playwright config for the splunk-uc-recommender app v9.0 e2e suite.
//
// Boots a real Splunk instance (Docker container in CI; remote URL in
// dev) and asserts the recommender + implementations dashboards
// behave correctly across multiple Splunk versions.
//
// Environment:
//   SPLUNK_E2E_URL       — base URL, e.g. https://splunk:8000 (Splunk Web).
//                          When unset, the suite is skipped cleanly.
//   SPLUNK_E2E_REST_URL  — splunkd REST URL, default ${SPLUNK_E2E_URL}/8089
//                          (used to seed KV state and dispatch saved searches).
//   SPLUNK_E2E_TOKEN     — bearer token for both Splunk Web and splunkd.
//   SPLUNK_E2E_USER      — Splunk Web username for the admin run (defaults
//                          to the token's owner).
//   SPLUNK_E2E_USER_TOKEN — second bearer token without
//                          edit_uc_implementations, for the read-only run.
//                          When unset, the user run is skipped.
//
// Local invocation:
//   SPLUNK_E2E_URL=https://splunk:8000 \
//   SPLUNK_E2E_TOKEN="$(grep SPLUNK_REST_TOKEN secrets.env | cut -d= -f2)" \
//   npm run test:e2e
//
// CI invocation: see .github/workflows/uc-tests.yml under the
// `playwright-recommender` job (matrix across splunk:9.0, 9.4, 10.0).

import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.SPLUNK_E2E_URL;

export default defineConfig({
    testDir: '.',
    testMatch: /.*\.spec\.ts$/,
    fullyParallel: false, // Splunk Web is shared per-instance; serialise.
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: 1,
    reporter: [
        ['list'],
        ['html', { open: 'never', outputFolder: 'tests/e2e/.report' }],
    ],
    use: {
        baseURL,
        trace: 'retain-on-failure',
        screenshot: 'only-on-failure',
        video: 'retain-on-failure',
        ignoreHTTPSErrors: true,
        // Surface JS console + page-error early so a failing assertion
        // points at the renderer, not at the e2e step.
        launchOptions: {
            args: ['--disable-dev-shm-usage'],
        },
    },
    projects: [
        {
            name: 'chromium-admin',
            use: { ...devices['Desktop Chrome'] },
        },
    ],
});
