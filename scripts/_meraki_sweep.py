"""Run every Meraki UC's SPL against the live Splunk search head and
categorize each as PASS_DATA / PASS_NODATA / PARSE_ERROR / FATAL / TIMEOUT.

Reads /tmp/meraki-test-plan.jsonl (one UC per line, schema documented in
scripts/_meraki_test_plan.py).

Writes /tmp/meraki-sweep-report.json with per-UC results plus a summary.

Usage:
    set -a; source secrets.env; set +a
    python3 scripts/_meraki_sweep.py [--earliest -24h] [--workers 8]

Stdlib-only (urllib + concurrent.futures); no third-party deps required.

Notes:
* Uses Splunk REST `search/jobs` with `exec_mode=oneshot` for synchronous
  one-shot execution. Each request is bounded by --search-timeout (default
  60s).
* Overrides any embedded `earliest=`/`latest=` tokens in the SPL via REST
  args so the time window is predictable across queries. The override
  doesn't mutate the SPL on disk.
* Lookup tables that exist only in the customer's environment (not in the
  catalog) will yield PARSE_ERROR with a "Could not construct lookup"
  message — that's an environment dependency, not an SPL bug.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = Path("/tmp/meraki-test-plan.jsonl")
DEFAULT_REPORT = Path("/tmp/meraki-sweep-report.json")
SEARCH_HEAD = os.getenv("SPLUNK_REST_HOST", "192.168.12.45")
SEARCH_PORT = int(os.getenv("SPLUNK_REST_PORT", "8089"))
TOKEN_ENV = "SPLUNK_REST_TOKEN"


def normalize_spl(spl: str) -> str:
    """Make the SPL safe to dispatch as a REST search."""
    s = spl.strip()
    if not s.startswith(("|", "search ")):
        s = "search " + s
    s = re.sub(r"\bearliest\s*=\s*[\"']?[\w@\-+]+[\"']?", "", s)
    s = re.sub(r"\blatest\s*=\s*[\"']?[\w@\-+]+[\"']?", "", s)
    return s


def _ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def dispatch(token: str, spl: str, earliest: str,
             search_timeout: int) -> dict:
    url = f"https://{SEARCH_HEAD}:{SEARCH_PORT}/services/search/jobs"
    body = urllib.parse.urlencode({
        "search": spl,
        "exec_mode": "oneshot",
        "earliest_time": earliest,
        "latest_time": "now",
        "output_mode": "json",
        "count": 1,
        "max_count": 1,
        "timeout": search_timeout,
    }).encode("ascii")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, context=_ssl_context(),
                                    timeout=search_timeout + 5) as resp:
            return {"status": resp.status, "text": resp.read().decode("utf-8", "replace")}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace") if e.fp else str(e)
        return {"status": e.code, "text": body}


def categorize(result: dict) -> tuple[str, str]:
    status = result["status"]
    text = result["text"]
    if status >= 500:
        return "FATAL", f"HTTP {status}: {text[:200]}"
    if status == 400:
        try:
            doc = json.loads(text)
            msgs = doc.get("messages", [])
            err = "; ".join(m.get("text", "") for m in msgs)
        except Exception:
            err = text[:200]
        # Distinguish missing-lookup environment errors from real SPL bugs.
        if "Could not construct lookup" in err or "requires a .csv" in err:
            return "ENV_LOOKUP_MISSING", err[:300]
        return "PARSE_ERROR", err[:300]
    if status != 200:
        return "FATAL", f"HTTP {status}: {text[:200]}"
    try:
        doc = json.loads(text)
    except Exception:
        return "FATAL", "non-JSON 200 response"
    msgs = doc.get("messages", [])
    fatals = [m for m in msgs if m.get("type", "").upper() in ("FATAL", "ERROR")]
    if fatals:
        err = "; ".join(m.get("text", "") for m in fatals)
        if "Could not construct lookup" in err or "requires a .csv" in err:
            return "ENV_LOOKUP_MISSING", err[:300]
        return "PARSE_ERROR", err[:300]
    rows = doc.get("results", [])
    if rows:
        return "PASS_DATA", f"{len(rows)} row(s)"
    return "PASS_NODATA", "0 rows"


def run_one(token: str, ucrow: dict, earliest: str, search_timeout: int) -> dict:
    spl = normalize_spl(ucrow["spl"])
    started = time.time()
    try:
        result = dispatch(token, spl, earliest, search_timeout)
    except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
        return {"uc_id": ucrow["uc_id"], "title": ucrow["title"],
                "category": "TIMEOUT" if isinstance(exc, (socket.timeout, TimeoutError))
                            else "FATAL",
                "detail": f"transport: {exc!s}"[:300],
                "elapsed_s": round(time.time() - started, 2),
                "spl_chars": ucrow["spl_chars"],
                "sourcetypes": ucrow["sourcetypes"]}
    category, detail = categorize(result)
    return {"uc_id": ucrow["uc_id"], "title": ucrow["title"],
            "category": category, "detail": detail,
            "elapsed_s": round(time.time() - started, 2),
            "spl_chars": ucrow["spl_chars"],
            "sourcetypes": ucrow["sourcetypes"]}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    p.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    p.add_argument("--earliest", default="-30d",
                   help="Time window low end. -5m for SC4S syslog rate, "
                        "-24h covers one cycle of every API-TA modular input.")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--search-timeout", type=int, default=60)
    p.add_argument("--only", default=None,
                   help="Comma-separated UC IDs to test (default: all in plan)")
    args = p.parse_args()

    token = os.environ.get(TOKEN_ENV)
    if not token:
        print(f"error: {TOKEN_ENV} not set in env (source secrets.env first)",
              file=sys.stderr)
        return 2

    plan = []
    for line in args.plan.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        plan.append(json.loads(line))

    if args.only:
        wanted = {x.strip() for x in args.only.split(",")}
        plan = [r for r in plan if r["uc_id"] in wanted]

    print(f"Sweeping {len(plan)} Meraki UCs against {SEARCH_HEAD}:{SEARCH_PORT}",
          file=sys.stderr)
    print(f"  earliest={args.earliest} latest=now timeout={args.search_timeout}s "
          f"workers={args.workers}", file=sys.stderr)

    started = time.time()
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(run_one, token, r, args.earliest,
                              args.search_timeout): r for r in plan}
        for n, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            res = fut.result()
            results.append(res)
            print(f"  [{n:>3d}/{len(plan)}] UC-{res['uc_id']:<10s} "
                  f"{res['category']:<22s} {res['elapsed_s']:>5.1f}s",
                  file=sys.stderr, flush=True)
    walltime = round(time.time() - started, 1)

    results.sort(key=lambda r: tuple(int(p) for p in r["uc_id"].split(".")))
    summary = {
        "total": len(results),
        "wall_seconds": walltime,
        "pass_data": sum(1 for r in results if r["category"] == "PASS_DATA"),
        "pass_nodata": sum(1 for r in results if r["category"] == "PASS_NODATA"),
        "env_lookup_missing": sum(1 for r in results if r["category"] == "ENV_LOOKUP_MISSING"),
        "parse_error": sum(1 for r in results if r["category"] == "PARSE_ERROR"),
        "fatal": sum(1 for r in results if r["category"] == "FATAL"),
        "timeout": sum(1 for r in results if r["category"] == "TIMEOUT"),
    }
    args.report.write_text(json.dumps({"summary": summary, "results": results},
                                       indent=2))
    print(f"\n=== SUMMARY (wall {walltime}s) ===", file=sys.stderr)
    for k, v in summary.items():
        print(f"  {k:<22s} {v}", file=sys.stderr)
    print(f"\nReport written to {args.report}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
