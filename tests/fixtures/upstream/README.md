# Upstream fault-injection fixtures (v9.0)

These five JSON files exercise every well-known failure mode the
recommender JS may encounter when it calls the v1 catalogue API.
They are served (in CI) by a small Python `http.server` so that
Playwright can point `SPLUNK_UC_RECOMMENDER_API_BASE` at them and
assert the dashboard renders the specific recovery copy — never blank.

| Fixture | Trigger | Expected UI copy |
|---|---|---|
| `upstream-500.json` | Server returns 500 with this body | "Catalog service is having a bad day. Try again in a minute." |
| `upstream-404.json` | Server returns 404 | "We can't find the use-case catalog. Tell your admin to check the API base URL in the Settings tab." |
| `upstream-malformed.json` | Server returns 200 with non-JSON body | "Catalog response is corrupted. Wait for the next nightly refresh." |
| `upstream-wrong-schema.json` | Server returns 200 with valid JSON of wrong shape | "Catalog version mismatch — your recommender is too old or too new." |
| `upstream-empty-array.json` | Server returns 200 with empty arrays | "No use cases match your environment yet." (empty state, not error) |

Every JSON file in this directory must be either:

- valid `application/json` with a recommender-shaped payload (real or
  intentionally malformed), or
- an explicit non-JSON body intended to test parser failure
  (`upstream-malformed.json`).

These fixtures are used by `tests/recommender/upstream_fixtures.test.mjs`
(unit-level smoke) and the Playwright suite under `tests/e2e/`.
