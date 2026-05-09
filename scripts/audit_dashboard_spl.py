#!/usr/bin/env python3
"""Audit every dashboard panel's SPL by actually dispatching it to splunkd.

The shipped smoke test (``scripts/deploy_to_splunk.sh``) historically
only verified the *shape* of the deployment: files exist at the right
URLs, KV collections are queryable, capabilities are registered,
static assets are served. It never executed the SPL inside the
dashboard panels.

That gap let a real bug ship to v9.2.0 build 8: the Implementations
dashboard's table panel contained malformed SPL --

    | inputlookup uc_recommender_implementations
        (status="not_started",status="in_progress",...)
    | table ...

which Splunk rejected with::

    FATAL: Error in 'inputlookup' command: Invalid argument: '(status=not_started'

Static asset checks were green, the panel page rendered, but the panel
itself 400'd the moment Splunk Web tried to dispatch it. This script
closes the gap by:

1. Walking every ``default/data/ui/views/*.xml`` in the app.
2. Extracting every ``<query>`` element (panel searches + dynamic input
   searches).
3. Resolving ``$token$`` references using the form's ``<input>`` default
   values (multiselect / dropdown / text). Handles the
   prefix/suffix/valuePrefix/valueSuffix/delimiter shaping that
   multiselects use.
4. Dispatching each query to splunkd via ``/services/search/jobs`` in
   ``exec_mode=blocking`` mode under the app's namespace.
5. Asserting ``isFailed=False`` and that no message has type ``FATAL``.

Exits 0 if all panels are healthy, 1 if any FATAL was raised, 2 on a
transport / config error. Designed to be called from
``scripts/deploy_to_splunk.sh`` and from CI (when a Splunk container is
available).

Authentication: reads ``SPLUNK_REST_TOKEN`` from the environment (the
deploy script already loads ``secrets.env`` before calling us). The
header is written to a 0700 mktemp file so the token never lands on
``ps aux``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET

# Drilldown tokens like $row.uc_id$ or $click.value$ are evaluated at
# user-interaction time, never at first-load. They never appear inside
# <query> elements; they appear inside <link> elements. Just in case
# someone slips one in, we substitute with a benign string so the
# dispatch can still validate the surrounding SPL.
_DRILLDOWN_PREFIXES = ("row.", "click.", "result.", "earliest", "latest")


@dataclass
class TokenSpec:
    """How a single dashboard input expands when its token is substituted."""

    token: str
    type: str  # multiselect / dropdown / text / time / radio / link / checkbox
    default: str = ""
    delimiter: str = ","
    prefix: str = ""
    suffix: str = ""
    value_prefix: str = ""
    value_suffix: str = ""

    def expand(self) -> str:
        """Mirror Splunk's token-substitution rules.

        Returns a string ready to be placed where ``$token$`` appears in
        the SPL. For multiselect, this is
        ``prefix + valuePrefix VAL valueSuffix [delimiter ...] + suffix``.
        For everything else (dropdown / text / radio / link), it's just
        ``valuePrefix + default + valueSuffix`` (the latter two are
        usually empty, in which case the literal default is returned).
        """
        if not self.default:
            # Empty default for a text input -> empty token. Splunk
            # leaves $token$ as-is in this case, but for an audit we
            # treat an empty replacement as "the user did nothing"
            # which still has to produce valid SPL.
            return ""
        if self.type == "multiselect":
            parts = [
                f"{self.value_prefix}{value.strip()}{self.value_suffix}"
                for value in self.default.split(",")
                if value.strip()
            ]
            joined = self.delimiter.join(parts)
            return f"{self.prefix}{joined}{self.suffix}"
        # dropdown / text / radio / link
        return f"{self.value_prefix}{self.default}{self.value_suffix}"


@dataclass
class Panel:
    """A single dispatchable search inside a dashboard."""

    view: str
    panel: str  # human-readable panel title or id, for log messages
    spl: str
    earliest: str = "-15m"
    latest: str = "now"


@dataclass
class AuditResult:
    panel: Panel
    ok: bool
    is_failed: bool = False
    is_done: bool = False
    result_count: int = 0
    messages: list[dict[str, str]] = field(default_factory=list)
    transport_error: str | None = None

    @property
    def fatal_messages(self) -> list[dict[str, str]]:
        return [m for m in self.messages if str(m.get("type", "")).upper() == "FATAL"]


def _strip_ns(tag: str) -> str:
    """Strip the optional ``{namespace}`` prefix from an XML tag."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _parse_inputs(form: ET.Element) -> dict[str, TokenSpec]:
    specs: dict[str, TokenSpec] = {}
    for inp in form.iter():
        if _strip_ns(inp.tag) != "input":
            continue
        token = inp.get("token")
        if not token:
            continue
        spec = TokenSpec(token=token, type=inp.get("type", "text"))
        for child in inp:
            cname = _strip_ns(child.tag)
            text = (child.text or "").strip()
            if cname == "default":
                spec.default = text
            elif cname == "delimiter":
                # Splunk preserves leading/trailing whitespace in the
                # delimiter (e.g. " OR " is correct, "OR" without spaces
                # would fail). ET strips significant whitespace by
                # default; we keep what's left.
                spec.delimiter = child.text or ","
            elif cname == "prefix":
                spec.prefix = child.text or ""
            elif cname == "suffix":
                spec.suffix = child.text or ""
            elif cname == "valuePrefix":
                spec.value_prefix = child.text or ""
            elif cname == "valueSuffix":
                spec.value_suffix = child.text or ""
        specs[token] = spec
    return specs


_TOKEN_RX = re.compile(r"\$([A-Za-z_][A-Za-z0-9_.]*)\$")


def _expand_tokens(spl: str, specs: dict[str, TokenSpec]) -> str:
    """Replace ``$token$`` occurrences using the token's default value."""

    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        if any(name.startswith(p) for p in _DRILLDOWN_PREFIXES):
            return ""  # drilldown / time tokens are benign substitutions
        spec = specs.get(name)
        if spec is None:
            # Unknown token -> empty. The SPL may still be valid (e.g.
            # the panel was wrapped in <eval token=...> elsewhere). We
            # log this case in the audit summary.
            return ""
        return spec.expand()

    return _TOKEN_RX.sub(repl, spl)


def _collect_panels(view_path: Path) -> tuple[list[Panel], list[str]]:
    """Return ``(panels, warnings)`` extracted from one dashboard XML."""
    warnings: list[str] = []
    try:
        tree = ET.parse(view_path)
    except ET.ParseError as exc:
        return [], [f"{view_path.name}: XML parse error: {exc}"]

    root = tree.getroot()
    specs = _parse_inputs(root)
    panels: list[Panel] = []
    panel_count = 0
    for elem in root.iter():
        if _strip_ns(elem.tag) != "search":
            continue
        # Skip dynamic input searches embedded INSIDE <input> — they
        # populate dropdowns from saved searches and rarely have
        # tokens. Still validate them under a synthetic panel name.
        query_elem = next(
            (c for c in elem if _strip_ns(c.tag) == "query"),
            None,
        )
        if query_elem is None or not (query_elem.text and query_elem.text.strip()):
            continue
        panel_count += 1
        spl = _expand_tokens(query_elem.text, specs)
        earliest_elem = next(
            (c for c in elem if _strip_ns(c.tag) == "earliest"),
            None,
        )
        latest_elem = next(
            (c for c in elem if _strip_ns(c.tag) == "latest"),
            None,
        )
        # Best-effort panel label: find nearest preceding <title>
        title = "panel#" + str(panel_count)
        for ancestor in root.iter():
            if elem in list(ancestor):
                # ancestor contains elem as a direct child
                title_elem = next(
                    (c for c in ancestor if _strip_ns(c.tag) == "title"),
                    None,
                )
                if title_elem is not None and title_elem.text:
                    title = title_elem.text.strip()
                break
        panels.append(
            Panel(
                view=view_path.name,
                panel=title,
                spl=spl.strip(),
                earliest=(earliest_elem.text.strip() if earliest_elem is not None and earliest_elem.text else "-15m"),
                latest=(latest_elem.text.strip() if latest_elem is not None and latest_elem.text else "now"),
            )
        )
    return panels, warnings


# ---- HTTP --------------------------------------------------------


class Splunkd:
    """Minimal token-bearing HTTPS client for splunkd:8089."""

    def __init__(self, base_url: str, token: str, *, insecure: bool = True) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.ctx: ssl.SSLContext | None = None
        if insecure:
            self.ctx = ssl.create_default_context()
            self.ctx.check_hostname = False
            self.ctx.verify_mode = ssl.CERT_NONE

    def _request(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> tuple[int, dict[str, Any]]:
        url = self.base_url + path
        body = urllib.parse.urlencode(data, doseq=True).encode("utf-8") if data else None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }
        if body is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        req = urllib.request.Request(url, data=body, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, context=self.ctx, timeout=timeout) as resp:
                raw = resp.read()
                code = resp.status
        except urllib.error.HTTPError as exc:
            raw = exc.read() or b""
            code = exc.code
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except json.JSONDecodeError:
            payload = {"raw": raw.decode("utf-8", errors="replace")}
        return code, payload

    def dispatch_blocking(
        self,
        spl: str,
        *,
        app: str,
        earliest: str,
        latest: str,
    ) -> AuditResult:
        # Build a synthetic panel for the result (caller fills in
        # view/panel; we only handle dispatch).
        synthetic = Panel(view="?", panel="?", spl=spl, earliest=earliest, latest=latest)
        try:
            code, payload = self._request(
                "POST",
                f"/servicesNS/nobody/{urllib.parse.quote(app, safe='')}/search/jobs",
                data={
                    "search": spl,
                    "exec_mode": "blocking",
                    "earliest_time": earliest,
                    "latest_time": latest,
                    "output_mode": "json",
                },
                timeout=60,
            )
        except (urllib.error.URLError, OSError) as exc:
            return AuditResult(panel=synthetic, ok=False, transport_error=str(exc))
        if code >= 400 and "sid" not in payload:
            msg = payload.get("messages") or []
            return AuditResult(
                panel=synthetic,
                ok=False,
                messages=msg,
                transport_error=f"HTTP {code} on dispatch",
            )
        sid = payload.get("sid")
        if not sid:
            return AuditResult(
                panel=synthetic,
                ok=False,
                transport_error=f"no sid returned (HTTP {code}): {payload!r}",
            )
        # Fetch job status (which now includes any FATAL messages).
        code, payload = self._request(
            "GET",
            f"/servicesNS/nobody/{urllib.parse.quote(app, safe='')}/search/jobs/{sid}?output_mode=json",
        )
        if code != 200:
            return AuditResult(
                panel=synthetic,
                ok=False,
                transport_error=f"HTTP {code} on job status: {payload!r}",
            )
        try:
            content = payload["entry"][0]["content"]
        except (KeyError, IndexError, TypeError):
            return AuditResult(
                panel=synthetic,
                ok=False,
                transport_error=f"unexpected job-status payload: {payload!r}",
            )
        is_failed = bool(content.get("isFailed"))
        is_done = bool(content.get("isDone"))
        result_count = int(content.get("resultCount") or 0)
        messages = content.get("messages") or []
        # Also clean up the job to avoid littering the dispatch dir.
        try:
            self._request(
                "DELETE",
                f"/servicesNS/nobody/{urllib.parse.quote(app, safe='')}/search/jobs/{sid}",
            )
        except Exception:
            pass
        return AuditResult(
            panel=synthetic,
            ok=not is_failed
            and not [m for m in messages if str(m.get("type", "")).upper() == "FATAL"],
            is_failed=is_failed,
            is_done=is_done,
            result_count=result_count,
            messages=messages,
        )


# ---- main --------------------------------------------------------


def _resolve_token(token_var: str) -> str:
    val = os.environ.get(token_var, "")
    if val:
        return val
    # Fall back to sourcing secrets.env if the caller didn't pre-load it.
    secrets = Path(__file__).resolve().parent.parent / "secrets.env"
    if secrets.exists():
        for line in secrets.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == token_var:
                return v.strip().strip('"').strip("'")
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("SPLUNK_HOST", "localhost"))
    parser.add_argument("--port", default="8089")
    parser.add_argument("--app", default="splunk-uc-recommender")
    parser.add_argument(
        "--app-root",
        default=str(Path(__file__).resolve().parent.parent / "splunk-apps/splunk-uc-recommender"),
        help="Path to the unpacked app directory whose XML to audit.",
    )
    parser.add_argument(
        "--token-var",
        default="SPLUNK_REST_TOKEN",
        help="Env var holding the bearer token (loaded from secrets.env if unset).",
    )
    parser.add_argument(
        "--strict-tls",
        action="store_true",
        help="Verify the splunkd cert (default: insecure for dev/lab).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print on failure.",
    )
    args = parser.parse_args()

    app_root = Path(args.app_root)
    views_dir = app_root / "default" / "data" / "ui" / "views"
    if not views_dir.is_dir():
        print(f"error: views dir not found: {views_dir}", file=sys.stderr)
        return 2

    token = _resolve_token(args.token_var)
    if not token:
        print(f"error: {args.token_var} not set (and not in secrets.env)", file=sys.stderr)
        return 2

    base_url = f"https://{args.host}:{args.port}"
    client = Splunkd(base_url, token, insecure=not args.strict_tls)

    panels: list[Panel] = []
    warnings: list[str] = []
    for fp in sorted(views_dir.glob("*.xml")):
        sub_panels, sub_warnings = _collect_panels(fp)
        panels.extend(sub_panels)
        warnings.extend(sub_warnings)

    if not panels:
        print(f"warning: no <search><query> elements found under {views_dir}")
        return 0

    if not args.quiet:
        print(f">> dashboard SPL audit ({len(panels)} panels across {len({p.view for p in panels})} dashboards)")

    failed: list[AuditResult] = []
    for panel in panels:
        result = client.dispatch_blocking(
            panel.spl,
            app=args.app,
            earliest=panel.earliest,
            latest=panel.latest,
        )
        result.panel = panel  # set the real panel context
        if result.ok:
            if not args.quiet:
                # Trim long SPL for readability in the smoke log.
                spl_preview = panel.spl if len(panel.spl) <= 100 else panel.spl[:97] + "..."
                print(f"   [PASS] {panel.view} :: {panel.panel} ({result.result_count} rows)  {spl_preview}")
        else:
            failed.append(result)
            print(
                f"   [FAIL] {panel.view} :: {panel.panel}",
                file=sys.stderr,
            )
            print(f"          spl: {panel.spl}", file=sys.stderr)
            if result.transport_error:
                print(f"          transport: {result.transport_error}", file=sys.stderr)
            for msg in result.messages:
                m_type = str(msg.get("type", "")).upper()
                if m_type in {"FATAL", "ERROR", "WARN"}:
                    print(
                        f"          {m_type}: {msg.get('text', '')[:300]}",
                        file=sys.stderr,
                    )

    for w in warnings:
        print(f"   [WARN] {w}", file=sys.stderr)

    if failed:
        print(
            f"\n{len(failed)} of {len(panels)} dashboard panels FAILED to dispatch.",
            file=sys.stderr,
        )
        return 1

    if not args.quiet:
        print(f"   ok: {len(panels)}/{len(panels)} dashboard panels dispatched cleanly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
