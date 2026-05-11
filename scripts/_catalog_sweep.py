"""Run every UC in /tmp/catalog-test-plan.jsonl against the live Splunk.

Same categorization as scripts/_meraki_sweep.py but for the broader catalog.

Usage:
    set -a; source secrets.env; set +a
    python3 scripts/_catalog_sweep.py [--earliest -90d] [--workers 8]
                                      [--report /tmp/catalog-sweep.json]
                                      [--only UC-X.Y.Z,UC-A.B.C]
                                      [--exclude-meraki]
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = Path("/tmp/catalog-test-plan.jsonl")
SEARCH_HEAD = os.getenv("SPLUNK_REST_HOST", "192.168.12.45")
SEARCH_PORT = int(os.getenv("SPLUNK_REST_PORT", "8089"))
TOKEN_ENV = "SPLUNK_REST_TOKEN"


def _ctx() -> ssl.SSLContext:
    c = ssl.create_default_context()
    c.check_hostname = False
    c.verify_mode = ssl.CERT_NONE
    return c


def normalize_spl(spl: str) -> str:
    s = spl.strip()
    if not s.startswith(("|", "search ")):
        s = "search " + s
    s = re.sub(r"\bearliest\s*=\s*[\"']?[\w@\-+]+[\"']?", "", s)
    s = re.sub(r"\blatest\s*=\s*[\"']?[\w@\-+]+[\"']?", "", s)
    return s


def dispatch(token: str, spl: str, earliest: str,
              search_timeout: int) -> dict:
    body = urllib.parse.urlencode({
        "search": spl,
        "exec_mode": "oneshot",
        "earliest_time": earliest,
        "latest_time": "now",
        "output_mode": "json",
        "count": 1,
        "max_count": 1,
    }).encode("ascii")
    req = urllib.request.Request(
        f"https://{SEARCH_HEAD}:{SEARCH_PORT}/services/search/jobs",
        data=body, method="POST",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, context=_ctx(),
                                     timeout=search_timeout + 5) as r:
            return {"status": r.status, "text": r.read().decode()}
    except urllib.error.HTTPError as e:
        try:
            return {"status": e.code, "text": e.read().decode()}
        except Exception:
            return {"status": e.code, "text": ""}
    except Exception as e:
        return {"status": 0, "text": f"EXC:{type(e).__name__}:{e}"}


def categorize(result: dict) -> tuple[str, str]:
    status = result["status"]
    text = result["text"]
    if status == 0:
        return "TIMEOUT" if "timed out" in text.lower() else "FATAL", text[:300]
    if status >= 500:
        return "FATAL", f"HTTP {status}: {text[:200]}"
    try:
        doc = json.loads(text)
    except Exception:
        return "FATAL", f"non-JSON status={status}: {text[:200]}"
    msgs = doc.get("messages", [])
    if status == 400:
        err = "; ".join(m.get("text", "") for m in msgs)
        if "Could not construct lookup" in err or "requires a .csv" in err:
            return "ENV_LOOKUP_MISSING", err[:300]
        return "PARSE_ERROR", err[:300]
    fatals = [m.get("text", "") for m in msgs
               if m.get("type", "").upper() in ("FATAL", "ERROR")]
    if fatals:
        err = "; ".join(fatals)
        if "Could not construct lookup" in err or "requires a .csv" in err:
            return "ENV_LOOKUP_MISSING", err[:300]
        return "PARSE_ERROR", err[:300]
    rows = doc.get("results", [])
    if rows:
        return "PASS_DATA", f"{len(rows)} row(s)"
    return "PASS_NODATA", "0 rows"


def run_one(token: str, ucrow: dict, earliest: str,
             search_timeout: int) -> dict:
    spl = normalize_spl(ucrow["spl"])
    t0 = time.time()
    result = dispatch(token, spl, earliest, search_timeout)
    cat, detail = categorize(result)
    return {
        "uc_id": ucrow["uc_id"],
        "title": ucrow["title"],
        "path": ucrow["path"],
        "primary": ucrow.get("primary", ""),
        "primary_count": ucrow.get("primary_count", 0),
        "sourcetypes": ucrow["sourcetypes"],
        "category": cat,
        "detail": detail,
        "elapsed_ms": int((time.time() - t0) * 1000),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--plan", default=str(PLAN))
    p.add_argument("--report", default="/tmp/catalog-sweep-report.json")
    p.add_argument("--earliest", default="-90d")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--search-timeout", type=int, default=120)
    p.add_argument("--only", default=None,
                    help="Comma-separated UC IDs to test")
    p.add_argument("--exclude-meraki", action="store_true",
                    help="Skip UCs whose primary sourcetype starts with meraki")
    args = p.parse_args()

    token = os.environ.get(TOKEN_ENV)
    if not token:
        print(f"error: {TOKEN_ENV} not set", file=sys.stderr)
        return 2

    rows = [json.loads(l) for l in open(args.plan) if l.strip()]
    if args.only:
        only = set(args.only.replace("UC-", "").split(","))
        rows = [r for r in rows if r["uc_id"] in only]
    if args.exclude_meraki:
        rows = [r for r in rows if not r.get("primary", "").startswith("meraki")]
    if not rows:
        print("error: no rows after filtering", file=sys.stderr)
        return 2

    print(f"Sweeping {len(rows)} UCs against {SEARCH_HEAD}:{SEARCH_PORT}",
          file=sys.stderr)
    print(f"  earliest={args.earliest} timeout={args.search_timeout}s "
          f"workers={args.workers}", file=sys.stderr)

    t_start = time.time()
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(run_one, token, r, args.earliest,
                              args.search_timeout): r for r in rows}
        for n, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            r = fut.result()
            results.append(r)
            print(f"  [{n:>3d}/{len(rows)}] UC-{r['uc_id']:<12s} "
                   f"{r['category']:<22s} {r['elapsed_ms']/1000:.1f}s",
                  file=sys.stderr)
    wall = time.time() - t_start

    results.sort(key=lambda x: x["uc_id"])
    summary = {
        "total": len(results),
        "wall_seconds": round(wall, 1),
        "pass_data": sum(1 for r in results if r["category"] == "PASS_DATA"),
        "pass_nodata": sum(1 for r in results if r["category"] == "PASS_NODATA"),
        "env_lookup_missing": sum(1 for r in results if r["category"] == "ENV_LOOKUP_MISSING"),
        "parse_error": sum(1 for r in results if r["category"] == "PARSE_ERROR"),
        "fatal": sum(1 for r in results if r["category"] == "FATAL"),
        "timeout": sum(1 for r in results if r["category"] == "TIMEOUT"),
    }
    print(f"\n=== SUMMARY (wall {wall:.1f}s) ===", file=sys.stderr)
    for k, v in summary.items():
        print(f"  {k:<22s} {v}", file=sys.stderr)
    Path(args.report).write_text(
        json.dumps({"summary": summary, "results": results}, indent=2))
    print(f"\nReport written to {args.report}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
