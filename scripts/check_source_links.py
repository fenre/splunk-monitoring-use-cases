#!/usr/bin/env python3
"""
check_source_links.py — fetch every URL in data/source-references.json and
record whether it's reachable.

Behaviour
---------

For each entry in `data/source-references.json`, this script:

1. Sends an HTTP HEAD (then GET as a fallback for hosts that 4xx/5xx on
   HEAD — many vendor portals do). A handful of well-known hosts that
   reject HEAD across the board (NIST, EUR-Lex bot defences, etc.) are
   probed with GET directly.
2. Follows redirects up to 5 hops, honouring the redirect chain.
3. Classifies the URL: `ok`, `redirect`, `client_error`, `server_error`,
   `timeout`, `dns`, `tls`, `unknown_error`.
4. Writes a stable report to `data/source-links-status.json` sorted by
   source-id, with a top-line summary of healthy/redirect/dead counts.

Usage
-----
```
python3 scripts/check_source_links.py            # write status file
python3 scripts/check_source_links.py --report   # print summary only
python3 scripts/check_source_links.py --only splunk-itsi
python3 scripts/check_source_links.py --strict   # exit 1 if any dead
```

This script is **not** wired into the per-PR validate.yml because it
makes outbound network calls (flaky, slow, prone to upstream
rate-limiting). It is meant to run on demand, on a scheduled workflow,
or when refreshing `_meta.accessedDate`.

No third-party dependencies are required (stdlib only).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LIBRARY_PATH = REPO / "data" / "source-references.json"
STATUS_PATH = REPO / "data" / "source-links-status.json"

# Many vendor portals (docs.splunk.com, cisco.com, iec.ch) silently 403 a
# urllib User-Agent string. Use a current Firefox UA to suppress these
# false positives; we're only doing a HEAD/GET reachability probe.
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.6; rv:131.0) "
    "Gecko/20100101 Firefox/131.0"
)
EXTRA_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "close",
    "Upgrade-Insecure-Requests": "1",
}
TIMEOUT_SEC = 20
MAX_REDIRECTS = 5
MAX_WORKERS = 8

# Hosts known to reject HEAD across the board; probe with GET directly.
GET_ONLY_HOSTS = {
    "csrc.nist.gov", "pages.nist.gov", "www.nist.gov", "nist.gov",
    "eur-lex.europa.eu", "www.iso.org", "iso.org",
    "www.legislation.gov.uk", "pcaobus.org",
}

# Hosts that aggressively bot-block both HEAD and GET regardless of UA.
# These URLs are stable and reachable to a human browser; the 403 is a
# false positive for our purposes. We re-classify them as `bot_blocked`
# instead of `client_error` so they don't pollute the dead-link list.
BOT_BLOCKED_HOSTS = {
    "www.hhs.gov", "hhs.gov",
    "www.sec.gov", "sec.gov",
    "dodcio.defense.gov",
    "docs.openshift.com",
}


def load_sources() -> dict[str, dict]:
    data = json.loads(LIBRARY_PATH.read_text(encoding="utf-8"))
    flat: dict[str, dict] = {}
    for section, entries in data.items():
        if section.startswith("_"):
            continue
        for sid, rec in entries.items():
            flat[sid] = dict(rec, _section=section, _id=sid)
    return flat


def classify(status: int) -> str:
    if 200 <= status < 300:
        return "ok"
    if 300 <= status < 400:
        return "redirect"
    if 400 <= status < 500:
        return "client_error"
    if 500 <= status < 600:
        return "server_error"
    return "unknown_status"


def _request(method: str, url: str, max_redirects: int) -> dict:
    """Single request with explicit redirect handling."""
    chain: list[str] = []
    current = url
    for _ in range(max_redirects + 1):
        chain.append(current)
        req = urllib.request.Request(
            current,
            method=method,
            headers={"User-Agent": UA, **EXTRA_HEADERS},
        )
        opener = urllib.request.build_opener(NoRedirectHandler())
        try:
            with opener.open(req, timeout=TIMEOUT_SEC) as resp:
                status = resp.status
                if 300 <= status < 400:
                    loc = resp.headers.get("Location")
                    if not loc:
                        return {"status": status, "classification": classify(status),
                                "final_url": current, "redirect_chain": chain}
                    # Resolve relative redirects against the current URL.
                    current = urllib.request.urljoin(current, loc)
                    continue
                return {"status": status, "classification": classify(status),
                        "final_url": current, "redirect_chain": chain}
        except urllib.error.HTTPError as e:
            return {"status": e.code, "classification": classify(e.code),
                    "final_url": current, "redirect_chain": chain,
                    "error": str(e)}
        except urllib.error.URLError as e:
            reason = getattr(e, "reason", e)
            if isinstance(reason, socket.timeout):
                err_class = "timeout"
            elif isinstance(reason, socket.gaierror):
                err_class = "dns"
            elif isinstance(reason, ssl.SSLError):
                err_class = "tls"
            else:
                err_class = "unknown_error"
            return {"status": None, "classification": err_class,
                    "final_url": current, "redirect_chain": chain,
                    "error": str(reason)}
        except Exception as e:
            return {"status": None, "classification": "unknown_error",
                    "final_url": current, "redirect_chain": chain,
                    "error": str(e)}
    return {"status": None, "classification": "too_many_redirects",
            "final_url": current, "redirect_chain": chain}


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Disable urllib's automatic redirect handling so we can record the
    chain explicitly."""
    def http_error_301(self, req, fp, code, msg, headers):
        return fp
    http_error_302 = http_error_301
    http_error_303 = http_error_301
    http_error_307 = http_error_301
    http_error_308 = http_error_301


def probe(url: str) -> dict:
    host = urllib.request.urlparse(url).netloc.lower()
    methods = ["GET"] if host in GET_ONLY_HOSTS else ["HEAD", "GET"]
    last: dict = {}
    for method in methods:
        result = _request(method, url, MAX_REDIRECTS)
        last = result
        if result.get("classification") == "ok":
            return result
        # If client_error (esp. 403/405), try fallback method.
        if result.get("status") in (403, 405, 501):
            continue
        break
    # Re-classify known bot-blocks so they don't pollute dead lists.
    if last.get("status") == 403 and host in BOT_BLOCKED_HOSTS:
        last["classification"] = "bot_blocked"
    return last


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="Only check sources whose ID matches")
    parser.add_argument("--report", action="store_true",
                        help="Read the saved status file and print a summary "
                             "without re-fetching.")
    parser.add_argument("--strict", action="store_true",
                        help="Exit 1 if any source is non-OK (after redirects).")
    parser.add_argument("--threads", type=int, default=MAX_WORKERS,
                        help=f"Concurrency (default {MAX_WORKERS}).")
    args = parser.parse_args(argv)

    sources = load_sources()
    if args.only:
        sources = {sid: rec for sid, rec in sources.items() if args.only in sid}

    if args.report:
        if not STATUS_PATH.exists():
            print("No status file found. Run without --report first.")
            return 2
        data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        _print_summary(data)
        return _exit_code(data, args.strict)

    print(f"Checking {len(sources)} URLs with {args.threads} workers ...")
    started = time.time()

    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=args.threads) as pool:
        futures = {
            pool.submit(probe, rec["url"]): sid
            for sid, rec in sources.items() if rec.get("url")
        }
        for i, fut in enumerate(as_completed(futures), 1):
            sid = futures[fut]
            try:
                result = fut.result()
            except Exception as e:
                result = {"status": None, "classification": "unknown_error",
                          "error": str(e)}
            results[sid] = {
                "url": sources[sid].get("url"),
                **result,
            }
            cls = result.get("classification", "?")
            sys.stdout.write(f"\r  {i}/{len(futures)}  {sid:<35s}  {cls:<14s}")
            sys.stdout.flush()
    print()

    elapsed = time.time() - started
    payload = {
        "_meta": {
            "generated": dt.datetime.now(dt.timezone.utc)
            .isoformat(timespec="seconds").replace("+00:00", "Z"),
            "elapsedSeconds": round(elapsed, 1),
            "totalChecked": len(results),
            "tool": "scripts/check_source_links.py",
            "notes": (
                "Run on demand; not wired into per-PR CI because the probe "
                "is network-dependent. Re-run after `_meta.accessedDate` "
                "bumps in source-references.json. Statuses: `ok` (200), "
                "`redirect` (3xx to a permanent new home), `bot_blocked` "
                "(host returns 403 to all bots but URL is correct), "
                "`client_error` / `server_error` / `timeout` / `dns` / "
                "`tls` (real reachability problem, fix the library)."
            ),
        },
        "sources": dict(sorted(results.items())),
    }
    STATUS_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    _print_summary(payload)
    print(f"\nWrote {STATUS_PATH.relative_to(REPO)}")
    return _exit_code(payload, args.strict)


def _print_summary(payload: dict) -> None:
    counts: dict[str, int] = {}
    dead: list[tuple[str, str, str]] = []
    redirected: list[tuple[str, str, str]] = []
    for sid, r in payload.get("sources", {}).items():
        c = r.get("classification", "?")
        counts[c] = counts.get(c, 0) + 1
        if c not in ("ok", "redirect", "bot_blocked"):
            dead.append((sid, r.get("url", ""),
                         f"{c} ({r.get('status') or r.get('error', '')})"))
        elif c == "redirect":
            final = r.get("final_url", "")
            if final and final != r.get("url"):
                redirected.append((sid, r.get("url", ""), final))

    total = sum(counts.values())
    print("\nSummary:")
    for cls, n in sorted(counts.items()):
        print(f"  {cls:<18s} {n:>4d}")
    print(f"  {'TOTAL':<18s} {total:>4d}")
    if redirected:
        print(f"\n{len(redirected)} sources redirected to a new canonical URL:")
        for sid, src, dst in redirected[:20]:
            print(f"  {sid}")
            print(f"    from: {src}")
            print(f"    to:   {dst}")
        if len(redirected) > 20:
            print(f"  … and {len(redirected) - 20} more (see "
                  f"data/source-links-status.json).")
    if dead:
        print(f"\n{len(dead)} sources are unreachable:")
        for sid, url, reason in dead[:30]:
            print(f"  {sid:<35s} {reason}")
            print(f"    {url}")
        if len(dead) > 30:
            print(f"  … and {len(dead) - 30} more.")


def _exit_code(payload: dict, strict: bool) -> int:
    if not strict:
        return 0
    for r in payload.get("sources", {}).values():
        if r.get("classification") not in ("ok", "redirect", "bot_blocked"):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
