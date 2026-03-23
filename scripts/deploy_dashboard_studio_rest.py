#!/usr/bin/env python3
"""
Deploy a Dashboard Studio JSON export to Splunk via REST (data/ui/views).

Splunk expects the Studio definition wrapped in XML — see:
https://docs.splunk.com/Documentation/Splunk/latest/DashStudio/RESTusage

Authentication (pick one):
  - SPLUNK_TOKEN or SPLUNK_REST_TOKEN — Splunk REST/auth token (Bearer; same value as Settings → Tokens)
  - SPLUNK_USER + SPLUNK_PASSWORD — basic auth

Environment:
  SPLUNK_HOST     — hostname or IP (default: localhost)
  SPLUNK_PORT     — management port (default: 8089)
  SPLUNK_APP      — target app context (default: search)
  SPLUNK_OWNER    — namespace user (default: admin) — use the account that may create dashboards
  SPLUNK_VERIFY_SSL — set to "0" or "false" to disable TLS verification (lab only)

Examples:
  export SPLUNK_TOKEN="eyJ..."
  python3 scripts/deploy_dashboard_studio_rest.py \\
    --file dashboards/catalog-quick-start-top2.json \\
    --name catalog_quick_start_top2

  SPLUNK_USER=admin SPLUNK_PASSWORD='secret' python3 scripts/deploy_dashboard_studio_rest.py \\
    --host splunk.example.com --file dashboards/catalog-quick-start-top2.json
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def _escape_cdata(s: str) -> str:
    """CDATA cannot contain the literal sequence ]]> — split if present."""
    return s.replace("]]>", "]]]]><![CDATA[>")


def build_studio_xml(
    dashboard: dict,
    *,
    theme: str = "dark",
    hide_edit: bool = False,
    hide_open_in_search: bool = False,
    hide_export: bool = False,
) -> str:
    """Wrap Dashboard Studio JSON in the XML envelope required by eai:data."""
    label = dashboard.get("title") or "Dashboard"
    description = dashboard.get("description") or ""
    json_body = json.dumps(dashboard, ensure_ascii=False)
    json_body = _escape_cdata(json_body)
    meta = json.dumps(
        {
            "hideEdit": hide_edit,
            "hideOpenInSearch": hide_open_in_search,
            "hideExport": hide_export,
        },
        separators=(",", ":"),
    )
    meta = _escape_cdata(meta)

    return f"""<dashboard version="2" theme="{theme}">
  <label>{_xml_escape_text(label)}</label>
  <description>{_xml_escape_text(description)}</description>
  <definition><![CDATA[
{json_body}
  ]]></definition>
  <meta type="hiddenElements"><![CDATA[
{meta}
  ]]></meta>
</dashboard>"""


def _xml_escape_text(text: str) -> str:
    """Escape &, <, > for XML text nodes (label/description)."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def post_eai_data(
    url: str,
    body: dict[str, str],
    *,
    token: str | None,
    user: str | None,
    password: str | None,
    verify_ssl: bool,
) -> tuple[int, str]:
    """POST application/x-www-form-urlencoded to Splunk REST."""
    data = urllib.parse.urlencode(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded; charset=utf-8")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    elif user is not None and password is not None:
        b = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
        req.add_header("Authorization", f"Basic {b}")
    else:
        raise SystemExit("Set SPLUNK_TOKEN / SPLUNK_REST_TOKEN or both SPLUNK_USER and SPLUNK_PASSWORD")

    ctx = None if verify_ssl else ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
            return resp.getcode(), resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return e.code, err_body


def main() -> None:
    p = argparse.ArgumentParser(description="Deploy Dashboard Studio JSON to Splunk via REST")
    p.add_argument(
        "--file",
        default="dashboards/catalog-quick-start-top2.json",
        help="Path to Dashboard Studio JSON export",
    )
    p.add_argument(
        "--name",
        default="",
        help="Dashboard ID (filename in Splunk). Default: derived from --file stem",
    )
    p.add_argument("--host", default=os.environ.get("SPLUNK_HOST", "localhost"))
    p.add_argument("--port", type=int, default=int(os.environ.get("SPLUNK_PORT", "8089")))
    p.add_argument("--app", default=os.environ.get("SPLUNK_APP", "search"))
    p.add_argument("--owner", default=os.environ.get("SPLUNK_OWNER", "admin"))
    p.add_argument("--theme", default="dark", choices=("dark", "light"))
    p.add_argument(
        "--scheme",
        default=os.environ.get("SPLUNK_SCHEME", "https"),
        help="https or http (default https)",
    )
    p.add_argument("--user-cli", dest="user_cli", default="", help="Username (overrides SPLUNK_USER)")
    p.add_argument(
        "--password-cli",
        dest="password_cli",
        default="",
        help="Password (overrides SPLUNK_PASSWORD; avoid inline history in production)",
    )
    p.add_argument("--token-cli", dest="token_cli", default="", help="Splunk auth token (overrides SPLUNK_TOKEN)")
    p.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification (equivalent to SPLUNK_VERIFY_SSL=0)",
    )
    args = p.parse_args()

    path = Path(args.file)
    if not path.is_file():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    dash_name = args.name.strip() or path.stem.replace("-", "_")
    if not dash_name.replace("_", "").isalnum():
        print(
            "Error: --name should be alphanumeric with underscores (e.g. catalog_quick_start_top2)",
            file=sys.stderr,
        )
        sys.exit(1)

    dashboard = json.loads(path.read_text(encoding="utf-8"))
    xml_payload = build_studio_xml(dashboard, theme=args.theme)

    token = (
        (args.token_cli or os.environ.get("SPLUNK_TOKEN", "") or os.environ.get("SPLUNK_REST_TOKEN", ""))
        .strip()
        or None
    )
    user = (args.user_cli or os.environ.get("SPLUNK_USER", "")).strip() or None
    password = (args.password_cli or os.environ.get("SPLUNK_PASSWORD", "")).strip() or None
    if password and not user:
        user = "admin"
    if not token and not (user and password):
        print(
            "Error: set SPLUNK_TOKEN or SPLUNK_REST_TOKEN, or both SPLUNK_USER and SPLUNK_PASSWORD "
            "(password-only defaults SPLUNK_USER to admin).",
            file=sys.stderr,
        )
        sys.exit(1)

    verify_ssl = not args.insecure and os.environ.get("SPLUNK_VERIFY_SSL", "1").lower() not in (
        "0",
        "false",
        "no",
    )

    base = f"{args.scheme}://{args.host}:{args.port}/servicesNS/{args.owner}/{args.app}"
    create_url = f"{base}/data/ui/views"
    update_url = f"{base}/data/ui/views/{urllib.parse.quote(dash_name)}"

    # Create (name + eai:data); if object exists, update (eai:data only on named endpoint)
    body_create = {"name": dash_name, "eai:data": xml_payload}
    body_update = {"eai:data": xml_payload}

    print(f"POST create: {create_url} (name={dash_name})")
    code, text = post_eai_data(
        create_url,
        body_create,
        token=token,
        user=user,
        password=password,
        verify_ssl=verify_ssl,
    )

    if code in (200, 201):
        print("Success: dashboard created.")
        print(text[:2000] if len(text) > 2000 else text)
        return

    # Typical conflict when dashboard already exists
    if code in (400, 409) or "already exists" in text.lower() or "duplicate" in text.lower():
        print(f"Create returned {code}; trying update: {update_url}")
        code2, text2 = post_eai_data(
            update_url,
            body_update,
            token=token,
            user=user,
            password=password,
            verify_ssl=verify_ssl,
        )
        if code2 in (200, 201):
            print("Success: dashboard updated.")
            print(text2[:2000] if len(text2) > 2000 else text2)
            return
        print(f"Update failed HTTP {code2}", file=sys.stderr)
        print(text2, file=sys.stderr)
        sys.exit(1)

    print(f"Create failed HTTP {code}", file=sys.stderr)
    print(text, file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
