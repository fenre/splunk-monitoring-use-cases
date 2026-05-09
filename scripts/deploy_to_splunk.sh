#!/usr/bin/env bash
# Deploy splunk-uc-recommender (v9.0+) to a remote Splunk Enterprise
# instance and run a smoke test. Used during development so you can
# iterate on the generator without leaving the editor.
#
# Usage:
#     scripts/deploy_to_splunk.sh [--host <hostname-or-ip>] [--port 8089]
#                                 [--ssh-host <alias-or-host>]
#                                 [--no-restart] [--smoke-only]
#                                 [--token-var SPLUNK_REST_TOKEN]
#                                 [--app-id splunk-uc-recommender]
#
# Reads tokens from ./secrets.env (which is gitignored). The default
# token variable is SPLUNK_REST_TOKEN; override with --token-var if
# you maintain multiple instances under different names (e.g.
# SPLUNK_MINK_TOKEN).
#
# Token-only deploy is constrained on Splunk Enterprise: `/services/apps/local`
# does NOT accept multipart .spl uploads (it returns 400 "Unparsable
# URI-encoded request data"). Two token-only install patterns DO work,
# and this script tries them in order:
#
#   1. URL-fetch (preferred, no SSH required):
#      - Spin up a transient `python3 -m http.server` on a local IP
#        that splunkd can reach.
#      - POST `/services/apps/local` with
#        `name=http://<our-ip>:<port>/<file>.spl&filename=true&update=true`.
#      - splunkd downloads the file itself and untars/installs.
#      - Tear down the HTTP server.
#
#   2. SSH-stage (fallback for closed networks where splunkd cannot
#      reach back to your workstation):
#      - `scp` the .spl to /tmp/ on the host.
#      - POST `name=<server-path>&filename=true&update=true`.
#      - rm the staging file.
#
# See `~/.cursor/skills/splunk-remote-app-deploy/SKILL.md` for the full
# discussion of why both patterns exist and when each one works.
#
# Behaviour:
#   1. Source secrets.env (does not echo any token).
#   2. Regenerate the app via scripts/generate_recommender_app.py.
#   3. Detect whether default/*.conf changed since the last deploy.
#      .conf changes require a Splunkd restart; .js / .css / .xml
#      changes only need a bundle reload.
#   4. Package the app into a deterministic .spl.
#   5. Install via URL-fetch (or SSH-stage as a fallback).
#   6. Trigger restart or reload as needed.
#   7. Run smoke tests:
#        - app responds at /servicesNS/-/<app>/data/ui/views/recommend
#        - the new uc_implementation_decommission saved search exists
#        - both KV collections are queryable
#        - JS + CSS files are served (200) at the static URLs
#
# Tokens never appear on the command line. The Authorization header is
# written to a 0700 mktemp dir and passed to curl via `--header @<file>`.
#
# Exit codes:
#   0 — deploy + smoke succeeded
#   2 — invalid arguments
#   3 — secrets.env missing or token unset
#   4 — generator/package/upload failure
#   5 — smoke test failed
#   6 — both URL-fetch and SSH-stage unavailable; manual upload printed

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SECRETS_FILE="${REPO_ROOT}/secrets.env"
APP_ID="splunk-uc-recommender"
HOST=""
PORT="8089"
SSH_HOST=""
RESTART="auto"
SMOKE_ONLY="no"
TOKEN_VAR="SPLUNK_REST_TOKEN"
INSECURE="${SPLUNK_DEPLOY_INSECURE:-yes}"   # default to yes for self-signed dev certs

usage() {
    sed -n '2,55p' "$0"
}

while [ $# -gt 0 ]; do
    case "$1" in
        --host)        HOST="$2"; shift 2 ;;
        --port)        PORT="$2"; shift 2 ;;
        --ssh-host)    SSH_HOST="$2"; shift 2 ;;
        --no-restart)  RESTART="never"; shift ;;
        --smoke-only)  SMOKE_ONLY="yes"; shift ;;
        --token-var)   TOKEN_VAR="$2"; shift 2 ;;
        --app-id)      APP_ID="$2"; shift 2 ;;
        --strict-tls)  INSECURE="no"; shift ;;
        --help|-h)     usage; exit 0 ;;
        *) echo "error: unknown flag '$1'" >&2; exit 2 ;;
    esac
done

# ---- 1. Secrets ---------------------------------------------------
if [ ! -f "${SECRETS_FILE}" ]; then
    echo "error: ${SECRETS_FILE} not found." >&2
    echo "  Copy secrets.env.example to secrets.env and add your bearer token." >&2
    exit 3
fi

# Source without echoing — `set -a` exports, `+a` stops, both are
# silent operations. We deliberately do not `cat` or `head` the
# secrets file anywhere in this script.
set -a
# shellcheck disable=SC1091
. "${SECRETS_FILE}"
set +a

TOKEN_VALUE="${!TOKEN_VAR:-}"
if [ -z "${TOKEN_VALUE}" ]; then
    echo "error: ${TOKEN_VAR} is not set in ${SECRETS_FILE}." >&2
    exit 3
fi

if [ -z "${HOST}" ]; then
    HOST="$(awk -v var="${TOKEN_VAR}" '
        /^# / { last_comment = $0; next }
        $0 ~ "^"var"=" {
            n = split(last_comment, parts, /[ -]+/)
            for (i = 1; i <= n; i++) {
                if (parts[i] ~ /^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$/) {
                    print parts[i]; exit
                }
            }
        }
    ' "${SECRETS_FILE}")"
    [ -z "${HOST}" ] && HOST="localhost"
fi

# Pick a default SSH alias by reverse-mapping HOST through ~/.ssh/config.
# Many users have e.g. `Host rev / HostName 192.168.12.45` and prefer
# the alias because it carries User/IdentityFile/Port.
if [ -z "${SSH_HOST}" ] && [ -f "${HOME}/.ssh/config" ]; then
    SSH_HOST="$(awk -v ip="${HOST}" '
        /^[Hh]ost / {
            for (i=2;i<=NF;i++) host[i-1]=$i; nh=NF-1; next
        }
        /^[[:space:]]*[Hh]ost[Nn]ame[[:space:]]/ {
            if ($2 == ip && nh > 0) { print host[1]; exit }
        }
    ' "${HOME}/.ssh/config")"
    [ -z "${SSH_HOST}" ] && SSH_HOST="${HOST}"
fi
[ -z "${SSH_HOST}" ] && SSH_HOST="${HOST}"

BASE_URL="https://${HOST}:${PORT}"
CURL_FLAGS=(--silent --show-error --fail-with-body)
if [ "${INSECURE}" = "yes" ]; then
    # The dev/lab Splunk hosts present self-signed certs. Production
    # use should pass --strict-tls.
    CURL_FLAGS+=(--insecure)
fi

# Write the Authorization header to a 0700 dir so curl can pick it up
# via --header @<file>. Embedding the token in argv leaks it into
# `ps aux`; this pattern keeps it on disk only.
AUTH_HDR_DIR="$(mktemp -d -t spluc-hdr-XXXXXX)"
chmod 700 "${AUTH_HDR_DIR}"
AUTH_HDR_FILE="${AUTH_HDR_DIR}/auth.hdr"
printf 'Authorization: Bearer %s\n' "${TOKEN_VALUE}" > "${AUTH_HDR_FILE}"
chmod 600 "${AUTH_HDR_FILE}"
trap 'rm -rf "${AUTH_HDR_DIR}"; cleanup_remote_stage 2>/dev/null || true; cleanup_url_fetch_server 2>/dev/null || true' EXIT

# Helper: token-bearing curl that stays Cloud-safe (no in-band file
# uploads, since /services/apps/local rejects multipart on splunkd:8089).
curl_auth() {
    # Usage: curl_auth <method> <path> [<extra-curl-args>...]
    local method="$1" rel_path="$2"; shift 2 || true
    curl "${CURL_FLAGS[@]}" -X "${method}" \
        --header "@${AUTH_HDR_FILE}" \
        "${BASE_URL}${rel_path}" "$@"
}

cleanup_remote_stage() {
    if [ -n "${REMOTE_STAGE_PATH:-}" ] && [ -n "${SSH_HOST}" ]; then
        ssh -o BatchMode=yes -o ConnectTimeout=5 "${SSH_HOST}" \
            "rm -f '${REMOTE_STAGE_PATH}'" >/dev/null 2>&1 || true
    fi
}

# Detect the local IP that splunkd can dial back to. Uses the routing
# table to pick the interface that would be used to reach HOST, then
# reads the IPv4 address from that interface. Avoids 127.0.0.1 because
# splunkd on a remote host obviously cannot reach loopback.
detect_reachable_local_ip() {
    local target="$1"
    case "$(uname -s)" in
        Darwin)
            local iface
            iface="$(route -n get "${target}" 2>/dev/null \
                | awk '/interface:/ {print $2; exit}')"
            [ -z "${iface}" ] && return 1
            ifconfig "${iface}" 2>/dev/null \
                | awk '/inet / && $2 != "127.0.0.1" {print $2; exit}'
            ;;
        Linux)
            ip route get "${target}" 2>/dev/null \
                | awk '{for (i=1;i<=NF;i++) if ($i=="src") {print $(i+1); exit}}'
            ;;
        *) return 1 ;;
    esac
}

# Find a free TCP port in the high range. Tries `ss` then `lsof` then
# falls back to a random port.
pick_free_port() {
    local port
    for _ in 1 2 3 4 5; do
        port="$(awk -v min=38000 -v max=39000 'BEGIN {srand(); print int(min+rand()*(max-min))}')"
        if ! lsof -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1; then
            echo "${port}"
            return 0
        fi
    done
    echo "$((RANDOM % 1000 + 38000))"
}

URL_FETCH_HTTP_PID=""
URL_FETCH_SERVE_DIR=""

cleanup_url_fetch_server() {
    if [ -n "${URL_FETCH_HTTP_PID}" ]; then
        kill "${URL_FETCH_HTTP_PID}" 2>/dev/null || true
        wait "${URL_FETCH_HTTP_PID}" 2>/dev/null || true
        URL_FETCH_HTTP_PID=""
    fi
    if [ -n "${URL_FETCH_SERVE_DIR}" ] && [ -d "${URL_FETCH_SERVE_DIR}" ]; then
        rm -rf "${URL_FETCH_SERVE_DIR}"
        URL_FETCH_SERVE_DIR=""
    fi
}

# Install the .spl into splunkd via URL-fetch.
#
# URL-fetch is preferred over SSH-stage because:
#   - No SSH key / agent dependency.
#   - Works against Splunk Cloud-style environments where you don't have
#     a shell on the indexer/SH at all.
#   - Same single REST POST as SSH-stage, just with name=<URL>.
#
# Returns 0 on success, non-zero on transport / install failure.
install_via_url_fetch() {
    local spl_file="$1"

    local local_ip
    local_ip="$(detect_reachable_local_ip "${HOST}")"
    if [ -z "${local_ip}" ]; then
        echo "   url-fetch: could not detect a local IP reachable from ${HOST}" >&2
        return 1
    fi

    local port
    port="$(pick_free_port)"

    URL_FETCH_SERVE_DIR="$(mktemp -d -t spluc-urlfetch-XXXXXX)"
    cp "${spl_file}" "${URL_FETCH_SERVE_DIR}/$(basename "${spl_file}")"

    # Background HTTP server scoped to LOCAL_IP only — never bound to
    # 0.0.0.0 — to keep the file off the wider network. The logs go to
    # a tempfile so we can post-mortem if splunkd never connects.
    local http_log
    http_log="$(mktemp -t spluc-urlfetch-log-XXXXXX)"
    (
        cd "${URL_FETCH_SERVE_DIR}" \
            && exec python3 -m http.server "${port}" --bind "${local_ip}"
    ) >"${http_log}" 2>&1 &
    URL_FETCH_HTTP_PID=$!

    # Wait until the server is actually accepting connections (max 5s).
    local up="no" attempt
    for attempt in 1 2 3 4 5 6 7 8 9 10; do
        if curl -sS -o /dev/null --connect-timeout 1 \
            "http://${local_ip}:${port}/$(basename "${spl_file}")" >/dev/null 2>&1; then
            up="yes"; break
        fi
        sleep 0.5
    done
    if [ "${up}" != "yes" ]; then
        echo "   url-fetch: local HTTP server failed to start" >&2
        cat "${http_log}" >&2 || true
        rm -f "${http_log}"
        cleanup_url_fetch_server
        return 1
    fi

    local fetch_url="http://${local_ip}:${port}/$(basename "${spl_file}")"
    echo "   url-fetch: serving on ${fetch_url}"

    # Tell splunkd to fetch and install. With name=<URL> + filename=true,
    # splunkd's apps/local handler downloads the URL and treats it as a
    # local file path. update=true overwrites any existing copy.
    local install_out
    install_out="$(curl_auth POST "/services/apps/local?output_mode=json" \
        --data-urlencode "name=${fetch_url}" \
        -d "filename=true" \
        -d "update=true" 2>&1)" || {
            echo "   url-fetch: REST install failed" >&2
            echo "${install_out}" >&2 || true
            rm -f "${http_log}"
            cleanup_url_fetch_server
            return 1
    }

    # Confirm the HTTP server actually saw splunkd. If it didn't, the
    # install probably hit cache or rejected silently — surface that.
    if ! grep -q "GET /$(basename "${spl_file}")" "${http_log}" 2>/dev/null; then
        echo "   url-fetch: splunkd never fetched the URL (firewall? proxy?)" >&2
        echo "${install_out}" >&2 || true
        rm -f "${http_log}"
        cleanup_url_fetch_server
        return 1
    fi

    if echo "${install_out}" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
errs = [m for m in (d.get("messages") or [])
        if str(m.get("type","")).upper() in ("ERROR","FATAL")]
if errs:
    for m in errs:
        print("  splunkd: " + str(m.get("text","")), file=sys.stderr)
    sys.exit(1)
' 2>&1; then
        :
    else
        echo "   url-fetch: splunkd reported install error" >&2
        rm -f "${http_log}"
        cleanup_url_fetch_server
        return 1
    fi

    rm -f "${http_log}"
    cleanup_url_fetch_server
    return 0
}

# Install the .spl via SSH-stage. Used as a fallback when splunkd can't
# reach back to our local HTTP server (closed network, restrictive
# egress proxy, etc.).
install_via_ssh_stage() {
    local spl_file="$1"

    if ! ssh -o BatchMode=yes -o ConnectTimeout=5 "${SSH_HOST}" \
        'echo OK' >/dev/null 2>&1; then
        echo "   ssh-stage: ssh '${SSH_HOST}' failed (no key/agent or wrong host)" >&2
        return 1
    fi

    REMOTE_STAGE_PATH="/tmp/$(basename "${spl_file}").$$"
    echo "   ssh-stage: ${SSH_HOST}:${REMOTE_STAGE_PATH}"
    if ! scp -q -o BatchMode=yes -o ConnectTimeout=10 \
        "${spl_file}" "${SSH_HOST}:${REMOTE_STAGE_PATH}"; then
        echo "   ssh-stage: scp failed" >&2
        REMOTE_STAGE_PATH=""
        return 1
    fi

    local install_out
    install_out="$(curl_auth POST "/services/apps/local?output_mode=json" \
        --data-urlencode "name=${REMOTE_STAGE_PATH}" \
        -d "filename=true" \
        -d "update=true" 2>&1)" || {
            echo "   ssh-stage: REST install failed" >&2
            echo "${install_out}" >&2 || true
            return 1
    }

    if echo "${install_out}" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
errs = [m for m in (d.get("messages") or [])
        if str(m.get("type","")).upper() in ("ERROR","FATAL")]
if errs:
    for m in errs:
        print("  splunkd: " + str(m.get("text","")), file=sys.stderr)
    sys.exit(1)
' 2>&1; then
        :
    else
        echo "   ssh-stage: splunkd reported install error" >&2
        return 1
    fi

    cleanup_remote_stage
    REMOTE_STAGE_PATH=""
    return 0
}

# ---- 2. Pre-flight: token + SSH ----------------------------------
echo ">> Probing ${BASE_URL} ..."
PROBE_OUT="$(curl_auth GET "/services/server/info?output_mode=json" 2>&1)" || {
    echo "error: splunkd unreachable or token invalid at ${BASE_URL}" >&2
    echo "${PROBE_OUT}" >&2
    exit 4
}
PROBE_INFO="$(echo "${PROBE_OUT}" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    e = d["entry"][0]["content"]
    print(e.get("serverName","?"), e.get("version","?"), sep="\t")
except Exception as exc:
    print(f"?\t? ({exc})")
' 2>/dev/null || echo "?\t?")"
echo "   server=$(echo "${PROBE_INFO}" | cut -f1) version=$(echo "${PROBE_INFO}" | cut -f2)"

# Note: SSH availability is checked inside install_via_ssh_stage() at
# the moment we actually need it. URL-fetch is preferred and tried
# first, so probing SSH up front would just be noise on the happy path.

# ---- 3. Regenerate + package -------------------------------------
if [ "${SMOKE_ONLY}" = "no" ]; then
    echo ">> Regenerating app source ..."
    python3 "${REPO_ROOT}/scripts/generate_recommender_app.py" \
        --output "${REPO_ROOT}/splunk-apps" >/dev/null

    echo ">> Detecting deploy mode ..."
    DEPLOY_MODE="reload"
    if [ -f "${REPO_ROOT}/.deploy-marker" ]; then
        if find "${REPO_ROOT}/splunk-apps/${APP_ID}/default" -newer "${REPO_ROOT}/.deploy-marker" -type f -name '*.conf' -print -quit | grep -q .; then
            DEPLOY_MODE="restart"
        fi
    else
        # First deploy — full restart guarantees a clean bundle.
        DEPLOY_MODE="restart"
    fi
    echo "   mode=${DEPLOY_MODE}"

    echo ">> Packaging .spl ..."
    DIST_DIR="$(mktemp -d -t spluc-deploy-XXXXXX)"
    "${REPO_ROOT}/scripts/package_splunk_apps.sh" "${DIST_DIR}" "${APP_ID}" >/dev/null

    SPL_FILE="$(ls "${DIST_DIR}"/${APP_ID}-*.spl | head -n1)"
    if [ ! -f "${SPL_FILE}" ]; then
        echo "error: package_splunk_apps.sh did not produce an .spl file" >&2
        exit 4
    fi
    echo "   ${SPL_FILE}"

    echo ">> Installing app ..."
    INSTALLED="no"
    if install_via_url_fetch "${SPL_FILE}"; then
        echo "   ok (url-fetch)"
        INSTALLED="yes"
    elif install_via_ssh_stage "${SPL_FILE}"; then
        echo "   ok (ssh-stage)"
        INSTALLED="yes"
    fi

    if [ "${INSTALLED}" != "yes" ]; then
        cat <<EOF >&2
=== MANUAL UPLOAD REQUIRED ===
Both auto-install paths failed:
  - URL-fetch: splunkd at ${HOST} cannot connect back to this workstation.
  - SSH-stage: '${SSH_HOST}' refused our key (no agent / wrong key).

To finish the deploy:

  1. Open Splunk Web at https://${HOST}:8000/manager/launcher/apps/local
  2. Click "Install app from file".
  3. Upload: ${SPL_FILE}
  4. Restart Splunk when prompted.

Then re-run with --smoke-only to validate:
  $0 --smoke-only --host ${HOST}

To make URL-fetch work next time, ensure splunkd at ${HOST} can reach
ports >= 38000 on this workstation (firewall, VPN routing).
To make SSH-stage work next time:
  ssh-copy-id ${SSH_HOST}
  ssh-add ~/.ssh/<your-key>     # macOS keychain often clears the agent
(see ~/.cursor/skills/splunk-remote-app-deploy/SKILL.md for details)
EOF
        exit 6
    fi

    if [ "${RESTART}" != "never" ] && [ "${DEPLOY_MODE}" = "restart" ]; then
        echo ">> Restarting Splunkd ..."
        curl_auth POST "/services/server/control/restart?output_mode=json" >/dev/null || {
            echo "::warning:: restart returned non-200; the upload may still have succeeded." >&2
        }
        # Splunkd (port 8089) usually responds within 30–90 s, but Splunk
        # Web (port 8000) takes another 20–60 s to come back. The smoke
        # test depends on BOTH, so wait for both before continuing.
        # Without the Splunk Web wait, smoke randomly fails because
        # /en-US/static/app/<APP_ID>/... 404s during the Web warmup.
        echo -n "   waiting for splunkd"
        for i in $(seq 1 60); do
            sleep 3
            if curl_auth GET "/services/server/info?output_mode=json" >/dev/null 2>&1; then
                echo -n " ok (after ${i} polls)"
                break
            fi
            echo -n "."
            if [ "${i}" -eq 60 ]; then
                echo
                echo "::warning:: splunkd did not return within 180s" >&2
            fi
        done
        echo
        echo -n "   waiting for splunkweb"
        for i in $(seq 1 60); do
            web_code="$(curl -sS -o /dev/null -w "%{http_code}" \
                --connect-timeout 2 \
                "http://${HOST}:8000/en-US/account/login" 2>/dev/null || echo 000)"
            if [ "${web_code}" = "200" ]; then
                echo " ok (after ${i} polls)"
                break
            fi
            echo -n "."
            sleep 2
            if [ "${i}" -eq 60 ]; then
                echo
                echo "::warning:: splunkweb did not respond on :8000 within 120s" >&2
            fi
        done
    elif [ "${RESTART}" != "never" ]; then
        echo ">> Reloading bundle (no .conf changes detected) ..."
        curl_auth POST "/services/apps/local/${APP_ID}/_reload?output_mode=json" >/dev/null || {
            curl_auth GET  "/en-US/debug/refresh?entity=admin/conf-app" >/dev/null 2>&1 || true
        }
    fi

    touch "${REPO_ROOT}/.deploy-marker"
fi

# ---- 4. Smoke test ----------------------------------------------
echo ">> Smoke test ..."
SMOKE_FAILED=0
smoke() {
    local label="$1" rel_path="$2"
    local result
    if result="$(curl_auth GET "${rel_path}" 2>&1)"; then
        echo "   [PASS] ${label}"
    else
        echo "   [FAIL] ${label}: ${result}" >&2
        SMOKE_FAILED=1
    fi
}

# Probes against splunkd on :${PORT}. The capability check uses the
# current-context endpoint because /services/authorization/capabilities/<name>
# is a list-only endpoint and returns 404 for individual names — see the
# splunk-remote-app-deploy skill for the gotcha rationale.
smoke "app metadata"               "/servicesNS/-/${APP_ID}/admin/conf-app/launcher?output_mode=json"
smoke "Recommend dashboard exists" "/servicesNS/-/${APP_ID}/data/ui/views/recommend?output_mode=json"
smoke "Implementations dashboard"  "/servicesNS/-/${APP_ID}/data/ui/views/implementations?output_mode=json"
smoke "fingerprint saved search"   "/servicesNS/-/${APP_ID}/saved/searches/Recommender%20%E2%80%94%20Saved-search%20fingerprint?output_mode=json"
smoke "decommission saved search"  "/servicesNS/-/${APP_ID}/saved/searches/uc_implementation_decommission?output_mode=json"
smoke "implementations KV"         "/servicesNS/nobody/${APP_ID}/storage/collections/config/uc_recommender_implementations?output_mode=json"
smoke "audit KV"                   "/servicesNS/nobody/${APP_ID}/storage/collections/config/uc_recommender_audit?output_mode=json"

# Negative probe: the legacy Dashboard Studio variant was retired in
# build 4 because Splunk Studio strips embedded scripts and the lite
# replacement was just visual noise. The view should be GONE on a
# correctly upgraded instance — flag it if it lingers.
echo -n "   "
legacy_studio_code="$(curl_auth GET "/servicesNS/-/${APP_ID}/data/ui/views/recommend_studio?output_mode=json" 2>/dev/null \
    | python3 -c '
import json, sys
try:
    d = json.loads(sys.stdin.read())
    sys.exit(0 if d.get("entry") else 1)
except Exception:
    sys.exit(1)
' && echo "present" || echo "absent")"
if [ "${legacy_studio_code}" = "absent" ]; then
    echo "[PASS] legacy Studio dashboard absent (retired in build 4)"
else
    echo "[FAIL] legacy recommend_studio dashboard still installed; uninstall the previous bundle and reinstall build 4+" >&2
    SMOKE_FAILED=1
fi

# Custom probe: edit_uc_implementations capability is registered for the
# authenticated principal. We can't GET .../capabilities/<name> directly
# (returns 404) so query current-context and verify the cap is in the
# user's effective list.
echo -n "   "
ctx_json="$(curl_auth GET "/services/authentication/current-context?output_mode=json" 2>&1)" || ctx_json=""
if echo "${ctx_json}" | python3 -c '
import json, sys
try:
    d = json.loads(sys.stdin.read())
    caps = d["entry"][0]["content"].get("capabilities", []) or []
    sys.exit(0 if "edit_uc_implementations" in caps else 1)
except Exception:
    sys.exit(2)
' 2>/dev/null; then
    echo "[PASS] edit_uc_implementations capability registered"
else
    echo "[FAIL] edit_uc_implementations capability not visible to authenticated user" >&2
    SMOKE_FAILED=1
fi

# Custom probes for app static assets. They are served by Splunk Web on
# port 8000 (NOT splunkd on 8089). Splunk Web is HTTP by default; if your
# install has TLS termination on 8000, override SPLUNK_WEB_BASE.
#
# IMPORTANT: probe the EXACT path the dashboard XML references (the value
# of script="…" / stylesheet="…"), not where the file happens to sit on
# disk. Simple XML resolves those attributes relative to
# `appserver/static/`, so script="recommender.js" requests
# /en-US/static/app/<APP_ID>/recommender.js — even if the actual file
# lives in `appserver/static/js/recommender.js`. We learned this the
# hard way (see splunk-remote-app-deploy skill, "Smoke-test gotchas").
SPLUNK_WEB_BASE="${SPLUNK_WEB_BASE:-http://${HOST}:8000}"
static_probe() {
    local label="$1" rel="$2"
    local code
    code="$(curl -ksS -m 5 -o /dev/null -w '%{http_code}' "${SPLUNK_WEB_BASE}${rel}" 2>/dev/null || echo "000")"
    if [ "${code}" = "200" ]; then
        echo "   [PASS] ${label}"
    else
        echo "   [FAIL] ${label}: HTTP ${code} on ${SPLUNK_WEB_BASE}${rel}" >&2
        SMOKE_FAILED=1
    fi
}

# Pull the deployed dashboards' raw XML and ask Splunk Web for whatever
# they reference via script= / stylesheet=. This catches "file exists at
# js/foo.js but XML asks for foo.js" regressions automatically.
#
# The python parser is written as a heredoc (not python -c) because the
# regex literal contains both single and double quotes, which makes
# inline -c quoting in bash unreliable.
PARSE_VIEW_SCRIPT="$(mktemp -t spluc-parse-view.XXXXXX.py)"
trap 'rm -f "${PARSE_VIEW_SCRIPT}"' EXIT INT TERM
cat >"${PARSE_VIEW_SCRIPT}" <<'PARSE_VIEW_PY'
import re
import sys
import html as _html

text = _html.unescape(sys.stdin.read())
seen = set()
for attr in ("script", "stylesheet"):
    pattern = r"\b" + attr + r"=\"([^\"]+)\""
    for match in re.finditer(pattern, text):
        for path in re.split(r"\s*,\s*", match.group(1)):
            path = path.strip()
            if path and path not in seen:
                seen.add(path)
                print(path)
PARSE_VIEW_PY

declare -a STATIC_TARGETS=()
for view in recommend implementations browse settings; do
    xml_body="$(curl_auth GET "/servicesNS/nobody/${APP_ID}/data/ui/views/${view}?output_mode=xml" 2>/dev/null)" || xml_body=""
    [ -z "${xml_body}" ] && continue
    while IFS= read -r line; do
        [ -n "${line}" ] && STATIC_TARGETS+=("${view}:${line}")
    done < <(printf '%s' "${xml_body}" | python3 "${PARSE_VIEW_SCRIPT}" 2>/dev/null)
done

if [ "${#STATIC_TARGETS[@]}" -eq 0 ]; then
    # Fallback: at least probe the canonical asset paths so we don't
    # silently skip the whole check.
    STATIC_TARGETS+=("recommend:js/recommender.js" "recommend:css/recommender.css")
fi

# Probe each unique reference once. macOS ships bash 3.2 which has no
# associative arrays, so we dedupe via awk on the asset path.
unique_targets="$(printf '%s\n' "${STATIC_TARGETS[@]}" | awk -F: '!seen[$2]++')"
while IFS= read -r entry; do
    [ -z "${entry}" ] && continue
    view="${entry%%:*}"
    rel_asset="${entry#*:}"
    static_probe "${view} static asset ${rel_asset}" "/en-US/static/app/${APP_ID}/${rel_asset}"
done <<< "${unique_targets}"

# ---- panel-SPL smoke -----------------------------------------------------
# Up to and including v9.2.0 build 8, the smoke test only verified that
# dashboards and saved searches existed at the right URLs. It never
# dispatched any of the dashboards' panel queries, so a malformed
# `inputlookup ... $status_filter$` shipped to users and 400'd at first
# load. scripts/audit_dashboard_spl.py closes the gap: it parses every
# generated default/data/ui/views/*.xml, expands $tokens$ from <input>
# defaults, and dispatches each <query> to splunkd in
# exec_mode=blocking, asserting isFailed=False and no FATAL messages.
echo
echo ">> Dispatching every dashboard panel SPL ..."
# The audit script reads its bearer from an env var; we deliberately
# pass it via the "name=value command" prefix syntax so the value never
# lands on `ps aux` past the lifetime of this single line.
if SPLUNK_REST_TOKEN="${TOKEN_VALUE}" \
        python3 "${REPO_ROOT}/scripts/audit_dashboard_spl.py" \
        --host "${HOST}" \
        --port "${PORT}" \
        --app "${APP_ID}" \
        --app-root "${REPO_ROOT}/splunk-apps/${APP_ID}" \
        --token-var SPLUNK_REST_TOKEN; then
    echo "[PASS] every dashboard panel dispatched without FATAL"
else
    echo "::error:: dashboard panel SPL audit FAILED — at least one <query> raised FATAL" >&2
    SMOKE_FAILED=1
fi

if [ "${SMOKE_FAILED}" -ne 0 ]; then
    echo "Smoke test FAILED — see errors above." >&2
    exit 5
fi

echo "Deploy complete: ${APP_ID} v$(tr -d '[:space:]' < "${REPO_ROOT}/VERSION") on ${HOST}:${PORT}"
