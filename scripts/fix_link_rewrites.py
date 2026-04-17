#!/usr/bin/env python3
"""Apply deterministic URL rewrites on `- **References:**` lines.

The replacements fall into three groups:

1. **Domain migrations** — e.g. `docs.microsoft.com` → `learn.microsoft.com`
   (the canonical host).
2. **Path rewrites** — e.g. `linux.die.net/man/1/X` → `man.archlinux.org/man/X.1`
   (same content, more reliable host).
3. **Typo trims** — strip accidental trailing `%5C` and `*` characters that
   leaked in during content writing.

Only idempotent, well-understood substitutions are applied here.  If a link
still 404s after this pass it is genuinely dead and should be curated by a
human.
"""

from __future__ import annotations

import argparse
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
UC_DIR = os.path.join(REPO_ROOT, "use-cases")


def _mutate_urls(text: str, stats: dict) -> str:
    """Apply URL-by-URL substitutions to every HTTP(S) URL in `text`."""
    url_rx = re.compile(r"https?://[^\s,<>\"')\]]+")

    def repl(m: re.Match[str]) -> str:
        url = m.group(0)
        new = url
        new = new.rstrip("*")
        if new.endswith("%5C") or new.endswith("%5c"):
            new = new[:-3]
            stats["trailing_backslash"] = stats.get("trailing_backslash", 0) + 1
        # docs.microsoft.com is a 301 → learn.microsoft.com for most paths.
        if new.startswith("https://docs.microsoft.com/"):
            new = new.replace(
                "https://docs.microsoft.com/",
                "https://learn.microsoft.com/",
                1,
            )
            stats["docs_microsoft"] = stats.get("docs_microsoft", 0) + 1
        # linux.die.net → man.archlinux.org (always serves the same content).
        m_die = re.match(r"https?://linux\.die\.net/man/(\d+)/([^\s#?]+)", new)
        if m_die:
            new = f"https://man.archlinux.org/man/{m_die.group(2)}.{m_die.group(1)}"
            stats["linux_die"] = stats.get("linux_die", 0) + 1
        # Previous (incorrect) man7 rewrites → correct man.archlinux paths.
        m_m7 = re.match(
            r"https?://man7\.org/linux/man-pages/man(\d+)/([^./\s]+)\.\d+\.html",
            new,
        )
        if m_m7:
            new = f"https://man.archlinux.org/man/{m_m7.group(2)}.{m_m7.group(1)}"
            stats["man7_revert"] = stats.get("man7_revert", 0) + 1
        # Defunct Malwarebytes blog → new location.
        if new.startswith("https://blog.malwarebytes.com/"):
            new = new.replace(
                "https://blog.malwarebytes.com/",
                "https://www.malwarebytes.com/blog/",
                1,
            )
            stats["malwarebytes"] = stats.get("malwarebytes", 0) + 1
        # AttackerKB retired the /rapid7-analysis sub-path.
        if new.startswith("https://attackerkb.com/topics/"):
            new = re.sub(r"/rapid7-analysis/?$", "", new)
            stats["attackerkb"] = stats.get("attackerkb", 0) + 1
        # PortSwigger anchors 404 — strip fragment.
        if new.startswith("https://portswigger.net/web-security/"):
            new = new.split("#", 1)[0]
            stats["portswigger"] = stats.get("portswigger", 0) + 1
        # MITRE: malformed `T1567/exfil` → T1567/002/.
        new = new.replace(
            "https://attack.mitre.org/techniques/T1567/exfil",
            "https://attack.mitre.org/techniques/T1567/002/",
        )
        # docs.aws.amazon.com/awscloudtrail/ (bare) → userguide path.
        if new == "https://docs.aws.amazon.com/awscloudtrail/":
            new = "https://docs.aws.amazon.com/awscloudtrail/latest/userguide/"
            stats["aws_cloudtrail"] = stats.get("aws_cloudtrail", 0) + 1
        # splunk research endpoint UUID 404s — back to the research root.
        new = re.sub(
            r"https://research\.splunk\.com/endpoint/[^/\s)]+/?",
            "https://research.splunk.com/",
            new,
        )
        if new != url:
            stats["any_rewrite"] = stats.get("any_rewrite", 0) + 1
        return new

    return url_rx.sub(repl, text)


def process_file(path: str, write: bool) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        original = f.read()
    stats: dict = {}
    new_text = _mutate_urls(original, stats)
    if write and new_text != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_text)
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    cat_files = sorted(
        os.path.join(UC_DIR, f)
        for f in os.listdir(UC_DIR)
        if f.startswith("cat-") and f.endswith(".md") and f != "cat-00-preamble.md"
    )

    grand: dict = {}
    for path in cat_files:
        stats = process_file(path, args.write)
        if stats.get("any_rewrite"):
            print(f"  {os.path.basename(path):48}  {stats}")
        for k, v in stats.items():
            grand[k] = grand.get(k, 0) + v
    print("-" * 70)
    print("Summary:", grand)
    if not args.write:
        print("(dry run — pass --write to persist)")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
