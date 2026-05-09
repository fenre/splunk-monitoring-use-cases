#!/usr/bin/env bash
# scripts/backup_legacy_app_state.sh — preserve customer state before
# uninstalling a legacy per-regulation Splunk app or the deprecated
# splunk-uc-recommender-ta companion TA.
#
# Run this on the live Splunk search head BEFORE removing the app from
# Settings -> Manage apps. Outputs go under
#   $SPLUNK_HOME/var/run/splunk/uc-migration-<app>-<timestamp>/
# so a customer can restore them or selectively re-apply against the
# unified splunk-uc-recommender app.
#
# Usage:
#   scripts/backup_legacy_app_state.sh splunk-uc-pci-dss
#   scripts/backup_legacy_app_state.sh splunk-uc-recommender-ta
#
# Requirements:
#   * SPLUNK_HOME set, splunkd running locally
#   * curl, tar, python3 on PATH
#   * SPLUNK_REST_TOKEN (or SPLUNK_USER + SPLUNK_PASS) exported, with
#     enough capability to read /servicesNS/nobody/<app>/...
#
# The script never echoes credentials. It is read-only against splunkd
# and never modifies any state on disk other than its own output dir.

set -euo pipefail

readonly LEGACY_APPS=(
    splunk-uc-cmmc splunk-uc-dora splunk-uc-gdpr splunk-uc-hipaa-security
    splunk-uc-iso-27001 splunk-uc-nis2 splunk-uc-nist-800-53 splunk-uc-nist-csf
    splunk-uc-pci-dss splunk-uc-soc-2 splunk-uc-sox-itgc splunk-uc-uk-gdpr
    splunk-uc-recommender-ta
)

usage() {
    cat <<EOF
Usage: $0 <legacy-app-id>
Where <legacy-app-id> is one of:
  ${LEGACY_APPS[*]}

Environment:
  SPLUNK_HOME             (required) path to Splunk install
  SPLUNK_REST_HOST        (default: localhost)
  SPLUNK_REST_PORT        (default: 8089)
  SPLUNK_REST_TOKEN       (preferred) bearer token for Splunkd REST
  SPLUNK_USER + SPLUNK_PASS  (fallback) basic auth
EOF
    exit 2
}

[ "$#" -eq 1 ] || usage
APP="$1"

is_legacy=0
for entry in "${LEGACY_APPS[@]}"; do
    [ "${entry}" = "${APP}" ] && is_legacy=1 && break
done
if [ "${is_legacy}" -ne 1 ]; then
    echo "error: '${APP}' is not a known legacy app id" >&2
    usage
fi

: "${SPLUNK_HOME:?SPLUNK_HOME must be set}"
HOST="${SPLUNK_REST_HOST:-localhost}"
PORT="${SPLUNK_REST_PORT:-8089}"
APP_DIR="${SPLUNK_HOME}/etc/apps/${APP}"

if [ ! -d "${APP_DIR}" ]; then
    echo "warning: ${APP_DIR} not found on disk; will still attempt KV export" >&2
fi

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="${SPLUNK_HOME}/var/run/splunk/uc-migration-${APP}-${TIMESTAMP}"
mkdir -p "${OUT_DIR}"

# curl wrapper that passes auth via stdin-config so the bearer never lands
# in argv (and therefore not in `ps auxe`).
CURL_CONFIG="$(mktemp)"
trap 'rm -f "${CURL_CONFIG}"' EXIT
if [ -n "${SPLUNK_REST_TOKEN:-}" ]; then
    printf 'header = "Authorization: Bearer %s"\n' "${SPLUNK_REST_TOKEN}" > "${CURL_CONFIG}"
elif [ -n "${SPLUNK_USER:-}" ] && [ -n "${SPLUNK_PASS:-}" ]; then
    printf 'user = "%s:%s"\n' "${SPLUNK_USER}" "${SPLUNK_PASS}" > "${CURL_CONFIG}"
else
    echo "error: set SPLUNK_REST_TOKEN or SPLUNK_USER + SPLUNK_PASS" >&2
    exit 2
fi

splunk_curl() {
    curl --fail --silent --show-error -k -K "${CURL_CONFIG}" "$@"
}

BASE="https://${HOST}:${PORT}"
NS="${BASE}/servicesNS/nobody/${APP}"

echo "[backup] ${APP} -> ${OUT_DIR}"

# 1. Tar local/ overrides if present (operator-modified SPL, dashboards, etc.)
if [ -d "${APP_DIR}/local" ]; then
    tar -C "${APP_DIR}" -czf "${OUT_DIR}/local-overrides.tar.gz" local
    echo "[backup]   local/ -> local-overrides.tar.gz"
else
    echo "[backup]   local/ absent; nothing to archive"
fi

# 2. Enumerate KV collections owned by the app and export each to JSON.
COLL_JSON="${OUT_DIR}/_collections.json"
splunk_curl "${NS}/storage/collections/config?output_mode=json&count=0" > "${COLL_JSON}" || true
COLL_NAMES="$(python3 - "${COLL_JSON}" <<'PY'
import json, sys, pathlib
p = pathlib.Path(sys.argv[1])
if not p.exists() or p.stat().st_size == 0:
    sys.exit(0)
try:
    payload = json.loads(p.read_text())
except json.JSONDecodeError:
    sys.exit(0)
for entry in payload.get("entry", []):
    print(entry.get("name", ""))
PY
)"

if [ -n "${COLL_NAMES}" ]; then
    mkdir -p "${OUT_DIR}/kv"
    while IFS= read -r coll; do
        [ -z "${coll}" ] && continue
        out="${OUT_DIR}/kv/${coll}.json"
        if splunk_curl "${NS}/storage/collections/data/${coll}?output_mode=json&count=0" > "${out}"; then
            echo "[backup]   KV ${coll} -> kv/${coll}.json"
        else
            echo "[backup]   KV ${coll}: export failed (continuing)" >&2
        fi
    done <<< "${COLL_NAMES}"
else
    echo "[backup]   no KV collections owned by ${APP}"
fi

# 3. List operator-enabled saved searches in this app context.
SS_JSON="${OUT_DIR}/_savedsearches.json"
splunk_curl "${NS}/saved/searches?output_mode=json&count=0" > "${SS_JSON}" || true
ENABLED_LIST="${OUT_DIR}/enabled-saved-searches.txt"
python3 - "${SS_JSON}" > "${ENABLED_LIST}" <<'PY'
import json, sys, pathlib
p = pathlib.Path(sys.argv[1])
if not p.exists() or p.stat().st_size == 0:
    sys.exit(0)
try:
    payload = json.loads(p.read_text())
except json.JSONDecodeError:
    sys.exit(0)
for entry in payload.get("entry", []):
    name = entry.get("name", "")
    content = entry.get("content", {})
    disabled = content.get("disabled")
    if disabled in (False, 0, "0", "False", "false"):
        print(name)
PY
echo "[backup]   enabled saved searches -> enabled-saved-searches.txt"

# 4. Recovery doc.
cat > "${OUT_DIR}/README.md" <<EOF
# Backup snapshot for ${APP}

Captured: ${TIMESTAMP}
Splunk host: ${HOST}:${PORT}

## Contents

- \`local-overrides.tar.gz\` — operator-modified \`local/\` (if present)
- \`kv/\` — JSON export of every KV collection owned by the app
- \`enabled-saved-searches.txt\` — list of saved searches that were
  enabled at backup time
- \`_collections.json\`, \`_savedsearches.json\` — raw REST responses
  used to drive the export above

## Restore order (after uninstalling ${APP} and installing
splunk-uc-recommender)

1. **Operator SPL / dashboards**: extract \`local-overrides.tar.gz\`
   into a temp dir and copy individual stanzas back into the unified
   recommender's \`local/\` only after diffing against the new
   defaults. Stanza names match by UC ID.
2. **Operator-enabled saved searches**: re-enable them in the
   recommender via the Compliance view (the unified app uses the same
   stanza names, keyed by UC ID).
3. **KV state**: skip unless you had operator-managed entries beyond
   the recommender's own collections. Use
   \`| inputlookup ... | outputjson\` to import a JSON snapshot back.

This snapshot is read-only. Nothing was modified on the live Splunk
host.
EOF

echo "[backup] OK -> ${OUT_DIR}"
echo "[backup] Review the snapshot, then uninstall ${APP} from"
echo "[backup]   Settings -> Manage apps."
