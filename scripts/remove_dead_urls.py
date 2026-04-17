#!/usr/bin/env python3
"""Delete known-dead URLs from `- **References:**` lines.

Some references cannot be salvaged by a simple rewrite: the original content
has been deleted, the hosting domain has folded, or the vendor has rotated to
an opaque session-URL scheme that is impossible to compute from the outside.

Rather than leave them hanging, we:

1. Maintain a **dead-URL registry** (see ``DEAD_URL_PATTERNS`` below) of
   regex patterns that match URLs known to be permanently gone.
2. Delete the matching markdown links (``[label](url)`` form) or bare URLs
   from References lines.
3. If a References line becomes empty, replace it with a generic fallback
   pointing to the canonical Splunk Lantern collection.
4. Run idempotently — re-running yields no further changes.

The script intentionally *does not* attempt any HTTP verification; it is the
manual curation counterpart to ``scripts/fix_link_rewrites.py``.
"""

from __future__ import annotations

import argparse
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
UC_DIR = os.path.join(REPO_ROOT, "use-cases")

FALLBACK_LINK = (
    "[Splunk Lantern — search use cases]"
    "(https://lantern.splunk.com/Splunk_Platform/Use_Cases)"
)

# Curated set of URL regex patterns we have verified to be permanently dead.
# Each entry should include a comment justifying the deletion.
DEAD_URL_PATTERNS: list[str] = [
    # Dead domains --------------------------------------------------------
    r"https?://detectioninthe\.cloud/\S*",
    r"https?://blog\.cluster25\.duskrise\.com/\S*",
    r"https?://m365internals\.com/\S*",
    r"https?://whitehat\.eu/\S*",
    # Vendor pages with session / toc-id URLs that can't be stabilised ----
    r"https?://docs\.pingidentity\.com/\S*\?tocId=\S*",
    r"https?://forums\.ivanti\.com/\S*\?language=\S*",
    r"https?://success\.trendmicro\.com/dcx/s/solution/\S*",
    # Retired news/blog articles -----------------------------------------
    r"https?://gcn\.com/cybersecurity/2012/\S*",
    r"https?://redcanary\.com/blog/mshta-attack-technique/?",
    r"https?://sec\.okta\.com/everythingisyes/?",
    r"https?://www\.aon\.com/cyber-solutions/aon_cyber_labs/yours-truly-signed-av-driver-\S*",
    r"https?://www\.blackberry\.com/us/en/solutions/endpoint-security/ransomware-protection/warzone[^\s)]*",
    r"https?://vuls\.cert\.org/confluence/\S*",
    # Defunct GitHub repos / moved files ---------------------------------
    r"https?://github\.com/Chigusa0w0/AsusDriversPrivEscala/?",
    r"https?://github\.com/cleverg0d/CVE-2023-22527/?",
    r"https?://github\.com/MicrosoftDocs/windows-itpro-docs/blob/public/windows/security/threat-protection/windows-defender-application-control/microsoft-recommended-driver-block-rules\.md",
    r"https?://github\.com/SigmaHQ/sigma/blob/master/rules/windows/driver_load/driver_load_vuln_drivers_names\.yml",
    r"https?://github\.com/bfuzzy1/auditd-attack/blob/master/auditd-attack/auditd-attack\.rules#L\d+-L\d+",
    r"https?://github\.com/nasbench/Misc-Research/blob/main/LOLBINs/Curl\.md",
    # Misc dead resources -------------------------------------------------
    r"https?://manpages\.ubuntu\.com/manpages/trusty/\S*",
    r"https?://splunk\.github\.io/splunk-mltk-container-docker/?",
    r"https?://securityonline\.info/wmiexec-regout-get-outputdata-response-from-registry/?",
    # attackerkb 404 topic family (retired Rapid7 analyses) --------------
    r"https?://attackerkb\.com/topics/[A-Za-z0-9]+/cve-\d{4}-\d{3,5}/rapid7-analysis/?",
    # Real 404s confirmed 2026-04-16 (second sweep) -----------------------
    r"https?://support\.google\.com/a/answer/175197\S*",
    r"https?://support\.google\.com/cloudidentity/answer/2537800\S*",
    r"https?://www\.cisa\.gov/news-events/alerts/2023/04/13/cisa-adds-3-known-exploited-vulnerabilities-kev-catalog/?",
    r"https?://www\.ciscolive\.com/c/dam/r/ciscolive/emea/docs/2020/pdf/BRKSEC-3200\.pdf",
    r"https?://www\.cyborgsecurity\.com/cyborg-labs/threat-hunt-deep-dives-user-account-control-bypass-via-registry-modification/?",
    r"https?://www\.echotrail\.io/insights/search/control\.exe/?",
    r"https?://www\.elastic\.co/guide/en/security/current/aws-iam-brute-force-of-assume-role-policy\.html",
    r"https?://www\.govcert\.admin\.ch/blog/zero-day-exploit-targeting-popular-java-library-log4j/?",
    r"https?://www\.govcert\.ch/blog/zero-day-exploit-targeting-popular-java-library-log4j/?",
    r"https?://www\.hackingarticles\.in/multiple-ways-to-exploit-tomcat-manager/?",
    r"https?://www\.ivanti\.com/security/security-advisories/ivanti-virtual-traffic-manager-vtm-cve-2024-7593/?",
    r"https?://www\.mandiant\.com/sites/default/files/2022-08/remediation-hardening-strategies-for-m365-defend-against-apt29-white-paper\.pdf",
    r"https?://www\.netspi\.com/blog/technical/network-penetration-testing/enumerating-domain-accounts-via-sql-server-using-adsi/?",
    r"https?://www\.pwc\.com/gx/en/issues/cybersecurity/cyber-threat-intelligence/cyber-year-in-retrospect/yir-cyber-threats-report-download\.pdf",
    r"https?://www\.rapid7\.com/blog/post/2013/03/09/psexec-demystified/?",
    r"https?://www\.sakshamdixit\.com/wmi-events/?",
    r"https?://www\.sans\.org/presentations/lolbin-detection-methods-seven-common-attacks-revealed/?",
    r"https?://www\.vectra\.ai/blogpost/abusing-the-replicator-silently-exfiltrating-data-with-the-aws-s3-replication-service/?",
    r"https?://www\.avira\.com/en/blog/certutil-abused-by-attackers-to-spread-threats/?",
]

COMBINED_DEAD = re.compile("|".join(f"(?:{p})" for p in DEAD_URL_PATTERNS))

REFERENCES_LINE = re.compile(r"^(\s*-\s*\*\*References:\*\*\s*)(.*)$")
MD_LINK_RX = re.compile(r"\[[^\]]+\]\((https?://[^\s)]+)\)")


def _strip_dead_in_refs_line(tail: str) -> str:
    """Remove markdown-style and bare dead URLs from a References tail."""
    # 1. Drop full `[label](url)` tokens where the URL is dead.
    def _md_repl(m: re.Match[str]) -> str:
        if COMBINED_DEAD.search(m.group(1)):
            return ""
        return m.group(0)

    new_tail = MD_LINK_RX.sub(_md_repl, tail)
    # 2. Remove any remaining bare dead URLs.
    new_tail = COMBINED_DEAD.sub("", new_tail)
    # 3. Normalise separators: collapse repeated commas / semicolons / " | ".
    new_tail = re.sub(r"(\s*[,;|]\s*)+", ", ", new_tail)
    new_tail = re.sub(r"\s{2,}", " ", new_tail).strip(" ,;|")
    return new_tail


def process_file(path: str, write: bool) -> int:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    changes = 0
    for i, raw in enumerate(lines):
        m = REFERENCES_LINE.match(raw.rstrip("\n"))
        if not m:
            continue
        prefix, tail = m.group(1), m.group(2)
        new_tail = _strip_dead_in_refs_line(tail)
        if new_tail == tail.strip():
            continue
        if not new_tail:
            new_tail = FALLBACK_LINK
        new_line = f"{prefix}{new_tail}\n"
        if new_line != raw:
            lines[i] = new_line
            changes += 1

    if write and changes:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    return changes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    cat_files = sorted(
        os.path.join(UC_DIR, f)
        for f in os.listdir(UC_DIR)
        if f.startswith("cat-") and f.endswith(".md") and f != "cat-00-preamble.md"
    )

    total = 0
    for path in cat_files:
        n = process_file(path, args.write)
        if n:
            print(f"  {os.path.basename(path):48}  {n} line(s) updated")
            total += n
    print("-" * 70)
    print(f"Total lines updated: {total}")
    if not args.write:
        print("(dry run — pass --write to persist)")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
