#!/usr/bin/env python3
"""Normalise malformed ``compliance[].clause`` strings across UC sidecars.

Phase A of the regulation-coverage-gap plan. Many UCs carry clause strings
that were auto-migrated from the cat-22 markdown prose and never cleaned up
(e.g. ``"FISMA"``, ``"Pr NDB"``, ``"CM MC 2.0 Level 2"``, ``"Art.5/6"``).
These strings fail the ``clauseGrammar`` regex in ``data/regulations.json``
and therefore:

    * sit in ``tests/golden/audit-baseline.json`` as tolerated debt
      (currently ~670 fingerprints), and
    * contribute **0%** to the clause/priority/assurance coverage metrics,
      even though the UC otherwise looks valid.

This script applies a deterministic, per-regulation rewrite pass:

    * If the clause already matches ``clauseGrammar``, leave it untouched.
    * Else apply a deterministic rewrite table driven by the observed
      baseline manglings (see ``REWRITE_RULES``).
    * If the mangled clause is a compound or range (e.g. ``"Art.44-49"``),
      expand it into multiple entries.
    * If the rewrite would duplicate a sibling clean entry on the same UC,
      drop the normalised entry (the sibling already covers the clause).
    * If a rewrite rule has a title-keyword fallback, use the UC title to
      pick the best ``commonClauses[]`` entry for the regulation.

Every entry this script modifies has its ``assurance_rationale`` updated
with a normalisation note so later reviewers can spot the automated step.

Exit status:
    0 – normalisation complete (whether changes were made or not).
    1 – internal error; inspect stderr.

After running this script, regenerate the baseline:

    python3 scripts/normalize_compliance_clauses.py
    python3 scripts/audit_compliance_mappings.py --update-baseline

The audit then passes with a much smaller baseline.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
REGS_PATH = REPO_ROOT / "data" / "regulations.json"
UC_GLOB = "use-cases/cat-*/uc-*.json"

NORMALISATION_NOTE = (
    " [Auto-normalised Phase A: clause rewritten from mangled baseline "
    "string using deterministic per-regulation rules; SME should still "
    "confirm mapping and uplift assurance from contributing → partial/full.]"
)


# ---------------------------------------------------------------------------
# Regulations catalogue loader (mini-catalogue, only what's needed here)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RegVersion:
    framework_id: str
    short_name: str
    version: str
    grammar: re.Pattern
    common_clauses: Tuple[str, ...]


@dataclass
class RegsCatalogue:
    alias_index: Dict[str, str] = field(default_factory=dict)
    versions: Dict[Tuple[str, str], RegVersion] = field(default_factory=dict)

    @classmethod
    def load(cls, path: pathlib.Path = REGS_PATH) -> "RegsCatalogue":
        raw = json.loads(path.read_text(encoding="utf-8"))
        cat = cls()
        for fw in raw.get("frameworks", []):
            fid = fw["id"]
            short = fw.get("shortName", "")
            aliases = [short, fid, fw.get("name", "")] + list(fw.get("aliases", []))
            for a in aliases:
                if a:
                    cat.alias_index[a.strip().lower()] = fid
            for ver in fw.get("versions", []):
                version = ver["version"]
                grammar = re.compile(ver["clauseGrammar"])
                common = tuple(c["clause"] for c in ver.get("commonClauses", []))
                cat.versions[(fid, version)] = RegVersion(
                    framework_id=fid,
                    short_name=short,
                    version=version,
                    grammar=grammar,
                    common_clauses=common,
                )
        for alias, fid in raw.get("aliasIndex", {}).items():
            if alias.startswith("$"):
                continue
            cat.alias_index[alias.strip().lower()] = fid
        return cat

    def resolve(self, name: str) -> Optional[str]:
        return self.alias_index.get((name or "").strip().lower())

    def version(self, fid: str, ver: str) -> Optional[RegVersion]:
        return self.versions.get((fid, ver))


# ---------------------------------------------------------------------------
# Rewrite helpers
# ---------------------------------------------------------------------------


Keyword = Tuple[Tuple[str, ...], str]  # (("keyword1", "keyword2"), clause)


def _pick_by_keywords(title: str, description: str, keyword_map: Sequence[Keyword], default: str) -> str:
    """Return the first clause whose keyword list matches the haystack.

    Matching is case-insensitive substring; the longest / most specific
    keyword lists should be listed first in the caller's ``keyword_map``
    so they are evaluated before short fallback keywords.
    """

    haystack = f"{title or ''} \n{description or ''}".lower()
    for keywords, clause in keyword_map:
        if all(k.lower() in haystack for k in keywords):
            return clause
    return default


# ---------------------------------------------------------------------------
# Rewrite rules per (regulation shortName, version)
# ---------------------------------------------------------------------------


RewriteFn = Callable[[str, Mapping[str, Any]], List[str]]


def _gdpr_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    """Handle GDPR Art.X/Y, Art.X-Y, Art.s. X-Y and trailing-dash forms."""

    c = clause.strip()
    # Art.X/Y
    if re.fullmatch(r"Art\.\d+(?:/\d+)+", c):
        nums = re.findall(r"\d+", c)
        return [f"Art.{n}" for n in nums]
    # Art.s. X-Y  (and variants like "Art.s 44-49")
    m = re.fullmatch(r"Art\.s?\.?\s*(\d+)\s*-\s*(\d+)", c)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return [f"Art.{i}" for i in range(lo, hi + 1)]
    # Art.X- (trailing dash) → Art.X
    m = re.fullmatch(r"Art\.(\d+)-+", c)
    if m:
        return [f"Art.{m.group(1)}"]
    # Art.X-Y  (simple numeric range)
    m = re.fullmatch(r"Art\.(\d+)\s*-\s*(\d+)", c)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return [f"Art.{i}" for i in range(lo, hi + 1)]
    return []  # not handled


def _nis2_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    m = re.fullmatch(r"Art\.(\d+)\s*-\s*(\d+)", c)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return [f"Art.{i}" for i in range(lo, hi + 1)]
    return []


def _dora_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    m = re.fullmatch(r"Art\.(\d+)\s*-\s*(\d+)", c)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return [f"Art.{i}" for i in range(lo, hi + 1)]
    if c.lower() == "unspecified":
        # Map by UC title to the closest DORA article.
        title = str(doc.get("title", ""))
        keymap: Sequence[Keyword] = [
            (("governance",), "Art.5"),
            (("framework",), "Art.6"),
            (("protocol",), "Art.7"),
            (("identification",), "Art.8"),
            (("protection",), "Art.9"),
            (("detection",), "Art.10"),
            (("response", "recovery"), "Art.11"),
            (("recovery",), "Art.11"),
            (("backup",), "Art.12"),
            (("incident",), "Art.17"),
            (("classification",), "Art.18"),
            (("reporting",), "Art.19"),
            (("testing",), "Art.24"),
            (("threat-led",), "Art.26"),
            (("pen", "testing"), "Art.26"),
            (("third-party", "risk"), "Art.28"),
            (("third party", "risk"), "Art.28"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "Art.5")]
    return []


def _soc2_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    if c.lower() == "unspecified":
        title = str(doc.get("title", ""))
        keymap: Sequence[Keyword] = [
            (("CC1",), "CC1.1"),
            (("CC2",), "CC2.1"),
            (("CC3",), "CC3.1"),
            (("CC5",), "CC5.1"),
            (("CC6.1",), "CC6.1"),
            (("CC6.6",), "CC6.6"),
            (("CC6.7",), "CC6.7"),
            (("CC7.1",), "CC7.1"),
            (("CC7.2",), "CC7.2"),
            (("CC7.3",), "CC7.3"),
            (("CC7.4",), "CC7.4"),
            (("CC8.1",), "CC8.1"),
            (("CC9.1",), "CC9.1"),
            (("A1",), "A1.2"),
            (("C1",), "C1.1"),
            (("P1",), "P1.1"),
            (("availability",), "A1.2"),
            (("privacy",), "P1.1"),
            (("confidentiality",), "C1.1"),
            (("change", "management"), "CC8.1"),
            (("incident",), "CC7.4"),
            (("monitoring",), "CC7.2"),
            (("risk",), "CC3.1"),
            (("logical", "access"), "CC6.1"),
            (("encryption",), "CC6.6"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "CC7.2")]
    # "CC6-CC8" → expand
    m = re.fullmatch(r"CC(\d+)\s*-\s*CC(\d+)", c)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return [f"CC{i}.1" for i in range(lo, hi + 1)]
    return []


def _iso27001_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    if c.lower() == "unspecified":
        title = str(doc.get("title", ""))
        keymap: Sequence[Keyword] = [
            (("log",), "A.8.15"),
            (("monitoring",), "A.8.16"),
            (("cloud",), "A.5.23"),
            (("access",), "A.5.15"),
            (("threat", "intel"), "A.5.7"),
            (("incident",), "A.5.24"),
            (("risk", "assessment"), "8.2"),
            (("internal", "audit"), "9.2"),
            (("measurement",), "9.1"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "A.8.15")]
    return []


def _ccpa_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    if c == "§1798.100-105":
        return ["§1798.100", "§1798.105"]
    if c == "§1798.140(ah)":
        return ["§1798.140"]
    if c.lower() == "unspecified":
        title = str(doc.get("title", ""))
        keymap: Sequence[Keyword] = [
            (("sensitive", "pi"), "§1798.121"),
            (("sensitive", "personal"), "§1798.121"),
            (("deletion",), "§1798.105"),
            (("delete",), "§1798.105"),
            (("correct",), "§1798.106"),
            (("correction",), "§1798.106"),
            (("opt-out",), "§1798.120"),
            (("opt out",), "§1798.120"),
            (("do not sell",), "§1798.120"),
            (("gpc",), "§1798.135"),
            (("global privacy control",), "§1798.135"),
            (("minor",), "§1798.120"),
            (("broker",), "§1798.99.80"),
            (("financial", "incentive"), "§1798.125"),
            (("authorized", "agent"), "§1798.145"),
            (("geolocation",), "§1798.121"),
            (("automated",), "§1798.185"),
            (("profiling",), "§1798.185"),
            (("cross-context",), "§1798.140"),
            (("dark pattern",), "§1798.140"),
            (("household",), "§1798.140"),
            (("breach",), "§1798.150"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "§1798.100")]
    return []


def _mifid_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    if c == "Art.9(3) MiFIR":
        return ["Art.9"]
    if c == "Art.16(3) MiFID II":
        return ["Art.16"]
    if c == "RTS 25":
        return ["Art.25"]  # grammar allows Art.\d+
    if c.lower() == "unspecified":
        title = str(doc.get("title", ""))
        keymap: Sequence[Keyword] = [
            (("best execution",), "Art.27"),
            (("transaction reporting",), "Art.26"),
            (("client suitability",), "Art.25"),
            (("record keeping",), "Art.16"),
            (("communications",), "Art.16"),
            (("algo",), "Art.17"),
            (("algorithmic",), "Art.17"),
            (("organisational",), "Art.16"),
            (("market making",), "Art.17"),
            (("clock sync",), "Art.50"),
            (("timestamp",), "Art.50"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "Art.17")]
    return []


def _pci_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    m = re.fullmatch(r"PCI DSS\s+Req\s+([\d.]+)", c, re.IGNORECASE)
    if m:
        return [m.group(1)]
    return []


def _hipaa_security_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    # `§policy` → drop (sibling clean entry already present on every UC that has it)
    if c == "§policy":
        return []  # drop
    return []


def _fisma_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip().upper()
    title = str(doc.get("title", ""))
    if c == "FEDRAMP":
        # Duplicate of the FISMA entry on the same UC; always drop.
        return []
    if c == "FISMA":
        keymap: Sequence[Keyword] = [
            (("incident",), "§3554(b)(1)"),
            (("authorization", "boundary"), "§3554(b)(1)"),
            (("ato", "boundary"), "§3554(b)(1)"),
            (("poa", "m"), "§3554(b)(1)"),
            (("us-cert",), "§3554(b)(1)"),
            (("piv",), "§3554(b)(1)"),
            (("smart card",), "§3554(b)(1)"),
            (("supply chain",), "§3554(b)(5)"),
            (("system security plan",), "§3554(b)(5)"),
            (("monitoring",), "§3554(b)(5)"),
            (("continuous",), "§3554(b)(5)"),
            (("vulnerability",), "§3554(b)(5)"),
            (("privileged",), "§3554(b)(5)"),
            (("remote", "access"), "§3554(b)(5)"),
            (("assessment",), "§3554(b)(5)"),
            (("evidence",), "§3554(b)(5)"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "§3554(b)(5)")]
    return []


def _sox_itgc_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    """Map the SOX ITGC free-text clauses to proper ``ITGC.*`` IDs."""
    c = clause.strip()
    title = str(doc.get("title", ""))
    desc = str(doc.get("value", ""))
    # Shared keyword map for "SOX ITGC" / "SOX §404" / "COSO" / "SOX *" free-text
    keymap: Sequence[Keyword] = [
        (("segregation of duties",), "ITGC.AccessMgmt.SOD"),
        (("sod",), "ITGC.AccessMgmt.SOD"),
        (("deprovision",), "ITGC.AccessMgmt.Termination"),
        (("terminate",), "ITGC.AccessMgmt.Termination"),
        (("leaver",), "ITGC.AccessMgmt.Termination"),
        (("provisioning",), "ITGC.AccessMgmt.Provisioning"),
        (("provision",), "ITGC.AccessMgmt.Provisioning"),
        (("privileged",), "ITGC.AccessMgmt.Privileged"),
        (("admin", "access"), "ITGC.AccessMgmt.Privileged"),
        (("role", "population"), "ITGC.AccessMgmt.Privileged"),
        (("access", "review"), "ITGC.AccessMgmt.Review"),
        (("quarterly",), "ITGC.AccessMgmt.Review"),
        (("sensitive", "report", "access"), "ITGC.AccessMgmt.Review"),
        (("sign-off",), "ITGC.AccessMgmt.Review"),
        (("change", "approval"), "ITGC.ChangeMgmt.Approval"),
        (("cab",), "ITGC.ChangeMgmt.Approval"),
        (("approval", "workflow"), "ITGC.ChangeMgmt.Approval"),
        (("change", "test"), "ITGC.ChangeMgmt.Testing"),
        (("rollback",), "ITGC.ChangeMgmt.Testing"),
        (("backout",), "ITGC.ChangeMgmt.Testing"),
        (("maintenance window",), "ITGC.ChangeMgmt.Authorization"),
        (("production change",), "ITGC.ChangeMgmt.Authorization"),
        (("unauthorized change",), "ITGC.ChangeMgmt.Authorization"),
        (("unauthorized batch",), "ITGC.ChangeMgmt.Authorization"),
        (("batch schedule",), "ITGC.Operations.JobSchedule"),
        (("batch job",), "ITGC.Operations.JobSchedule"),
        (("job schedule",), "ITGC.Operations.JobSchedule"),
        (("close", "batch"), "ITGC.Operations.JobSchedule"),
        (("close", "window"), "ITGC.Operations.JobSchedule"),
        (("close", "checklist"), "ITGC.Operations.JobSchedule"),
        (("incident", "aging"), "ITGC.Operations.JobSchedule"),
        (("cpu",), "ITGC.Operations.JobSchedule"),
        (("performance",), "ITGC.Operations.JobSchedule"),
        (("itsi", "service"), "ITGC.Operations.JobSchedule"),
        (("availability",), "ITGC.Operations.JobSchedule"),
        (("backup",), "ITGC.Operations.Backup"),
        (("disaster", "recovery"), "ITGC.Operations.Backup"),
        (("dr", "test"), "ITGC.Operations.Backup"),
        (("audit", "trail"), "ITGC.Logging.Continuity"),
        (("document number",), "ITGC.Logging.Continuity"),
        (("gap detection",), "ITGC.Logging.Continuity"),
        (("reconciliation",), "ITGC.Logging.Review"),
        (("journal", "entry"), "ITGC.Logging.Review"),
        (("disbursement",), "ITGC.Logging.Review"),
        (("duplicate",), "ITGC.Logging.Review"),
        (("cash",), "ITGC.Logging.Review"),
        (("reporting",), "ITGC.Logging.Review"),
        (("log", "review"), "ITGC.Logging.Review"),
        (("control", "testing"), "ITGC.Logging.Continuity"),
        (("test", "sample"), "ITGC.Logging.Continuity"),
        (("exception",), "ITGC.Logging.Review"),
        (("remediation",), "ITGC.Logging.Review"),
        (("audit",), "ITGC.Logging.Continuity"),
        (("csa",), "ITGC.Logging.Continuity"),
        (("risk",), "ITGC.Operations.JobSchedule"),
        (("management", "review"), "ITGC.AccessMgmt.Review"),
    ]
    # c covers COSO, SOX ITGC, SOX §404, SOX <word>, SOX close, etc.
    if re.fullmatch(r"(SOX\b.*|COSO)", c, re.IGNORECASE):
        return [_pick_by_keywords(title, desc, keymap, "ITGC.AccessMgmt.Provisioning")]
    return []


def _cmmc_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    """CMMC: drop ``CM MC 2.0 *`` when sibling AC.L2-... exists; else map."""

    c = clause.strip()
    title = str(doc.get("title", ""))
    siblings = {
        str(e.get("clause", ""))
        for e in doc.get("compliance", []) or []
        if e.get("regulation") == "CMMC"
    }
    # If at least one sibling clause already matches ``CM/AC/AU/...L\d-3.X.Y``, drop the mangled one.
    ok_grammar = re.compile(r"^[A-Z]{2}\.L[1-3]-\d+\.\d+\.\d+$")
    if any(ok_grammar.match(s) for s in siblings if s):
        return []  # drop – sibling is already the clean evidence.

    keymap_l2: Sequence[Keyword] = [
        (("cui",), "AC.L2-3.1.1"),
        (("access",), "AC.L2-3.1.1"),
        (("least privilege",), "AC.L2-3.1.5"),
        (("audit",), "AU.L2-3.3.1"),
        (("logging",), "AU.L2-3.3.1"),
        (("traceability",), "AU.L2-3.3.2"),
        (("reporting", "correlation"), "AU.L2-3.3.5"),
        (("baseline",), "CM.L2-3.4.1"),
        (("configuration",), "CM.L2-3.4.1"),
        (("incident",), "IR.L2-3.6.1"),
        (("cui", "transit"), "SC.L2-3.13.8"),
        (("crypto",), "SC.L2-3.13.8"),
        (("transit",), "SC.L2-3.13.8"),
        (("monitor",), "SI.L2-3.14.6"),
        (("continuous",), "SI.L2-3.14.6"),
        (("assessment",), "AU.L2-3.3.5"),
        (("threat",), "SI.L2-3.14.6"),
        (("response",), "IR.L2-3.6.1"),
        (("practice",), "AC.L2-3.1.1"),
    ]
    if re.match(r"^(CM\s*MC|C3PAO|CMMC)\b", c, re.IGNORECASE):
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap_l2, "AC.L2-3.1.1")]
    return []


def _tsa_sd_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    """TSA SD02C uses Roman numerals; map mangled strings by title keyword."""

    c = clause.strip()
    title = str(doc.get("title", ""))
    keymap: Sequence[Keyword] = [
        (("segmentation",), "III.A"),
        (("architecture",), "III.A"),
        (("plan",), "III.A"),
        (("pipeline",), "III.A"),
        (("vendor",), "III.A"),
        (("supply", "chain"), "III.A"),
        (("remote", "access"), "III.A"),
        (("access",), "III.A"),
        (("emergency",), "III.A"),
        (("physical",), "III.A"),
        (("monitoring",), "III.D"),
        (("incident", "response"), "III.D"),
        (("ir",), "III.D"),
        (("containment",), "III.D"),
        (("recovery",), "III.D"),
        (("reporting",), "III.D"),
        (("effectiveness",), "III.D"),
        (("assessment",), "III.D"),
        (("inventory",), "III.D"),
        (("vulnerability",), "III.D"),
        (("risk",), "III.D"),
        (("integrity",), "III.D"),
        (("change",), "III.D"),
        (("threat", "intel"), "III.D"),
        (("readiness",), "III.D"),
    ]
    if re.match(r"^TSA\b", c, re.IGNORECASE):
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "III.A")]
    return []


def _api_rp_1164_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.upper().startswith("API RP 1164"):
        keymap: Sequence[Keyword] = [
            (("access",), "5.3"),
            (("authentication",), "5.3"),
            (("authorization",), "5.3"),
            (("privilege",), "5.3"),
            (("log",), "6.2.1"),
            (("monitor",), "6.2.1"),
            (("detect",), "6.2.1"),
            (("incident",), "6.2.1"),
            (("anomaly",), "6.2.1"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "6.2.1")]
    return []


def _psd2_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.upper() == "PSD2":
        keymap: Sequence[Keyword] = [
            (("sca",), "Art.97"),
            (("strong", "customer", "authentication"), "Art.97"),
            (("authentication",), "Art.97"),
            (("incident",), "Art.96"),
            (("reporting",), "Art.96"),
            (("security", "risk"), "Art.95"),
            (("operational",), "Art.95"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "Art.95")]
    if c == "PSD2 RTS on SCA & CSC":
        return ["Art.97"]
    return []


def _eu_aml_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    # commonClauses: Art.9 (internal policies), Art.18 (CDD). Grammar Art.X(\(Y\))?.
    keymap: Sequence[Keyword] = [
        (("beneficial", "owner"), "Art.18"),
        (("ubo",), "Art.18"),
        (("cdd",), "Art.18"),
        (("due diligence",), "Art.18"),
        (("edd",), "Art.18"),
        (("kyc",), "Art.18"),
        (("onboarding",), "Art.18"),
        (("pep",), "Art.18"),
        (("politically",), "Art.18"),
        (("risk", "scoring"), "Art.18"),
        (("risk", "assessment"), "Art.9"),
        (("internal", "policy"), "Art.9"),
        (("internal", "policies"), "Art.9"),
        (("iwra",), "Art.9"),
        (("policy",), "Art.9"),
        (("training",), "Art.9"),
        (("sar",), "Art.9"),
        (("str",), "Art.9"),
        (("suspicious", "transaction"), "Art.9"),
        (("sanction",), "Art.9"),
        (("ofac",), "Art.9"),
        (("source", "of", "wealth"), "Art.18"),
        (("transaction", "monitoring"), "Art.18"),
        (("structuring",), "Art.9"),
        (("smurfing",), "Art.9"),
        (("dormant",), "Art.9"),
        (("cash-intensive",), "Art.9"),
        (("layering",), "Art.9"),
        (("round-trip",), "Art.9"),
        (("cross-border",), "Art.9"),
        (("geographic",), "Art.9"),
        (("digital", "onboarding"), "Art.18"),
        (("aml",), "Art.9"),
        (("amld",), "Art.9"),
        (("fatf",), "Art.9"),
        (("wolfsberg",), "Art.18"),
        (("mica",), "Art.9"),
    ]
    # Any "EU AMLD / ...", "FATF", "NRA", "Wolfsberg", "EU sanctions", "EU/US sanctions" etc.
    if re.match(r"^(EU\s*AMLD|FATF|NRA|Wolfsberg|EU[\s/]*US\s*sanctions|EU\s*sanctions)\b", c, re.IGNORECASE):
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "Art.9")]
    return []


def _au_privacy_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if re.search(r"^Pr\s+ivacy\s+Act", c):
        keymap: Sequence[Keyword] = [
            (("breach",), "§26WK"),
            (("notification",), "§26WK"),
            (("notifiable",), "§26WK"),
            (("security",), "APP 11"),
            (("retention",), "APP 11"),
            (("transparent",), "APP 1"),
            (("open",), "APP 1"),
            (("policy",), "APP 1"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "APP 1")]
    if re.search(r"^Pr\s+NDB", c, re.IGNORECASE):
        return ["§26WK"]
    return []


def _pipl_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    """PIPL: drop duplicate "PDPA", map bare "PIPL" to Art.X by title."""
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.upper() == "PDPA":
        # "PDPA" under regulation=PIPL is a migration artefact; drop.
        return []
    if c == "PIPL Art.38; ASEAN CBPR":
        return ["Art.38"]
    if c.upper() == "PIPL":
        keymap: Sequence[Keyword] = [
            (("cross-border",), "Art.38"),
            (("localization",), "Art.38"),
            (("localisation",), "Art.38"),
            (("residency",), "Art.38"),
            (("transfer",), "Art.38"),
            (("sensitive",), "Art.29"),
            (("separate consent",), "Art.29"),
            (("consent", "withdrawal"), "Art.15"),
            (("withdraw",), "Art.15"),
            (("opt-out",), "Art.14"),
            (("opt-in",), "Art.14"),
            (("consent",), "Art.14"),
            (("purpose",), "Art.6"),
            (("minor",), "Art.31"),
            (("retention",), "Art.19"),
            (("security",), "Art.51"),
            (("protection",), "Art.51"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "Art.51")]
    return []


def _sg_pdpa_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    # Any clause that isn't SG-PDPA-shaped maps to §24 (Protection obligation) by default,
    # unless the title is *exclusively* about Korea (then drop – misfiled).
    if c.upper() in {"PIPL", "K-ISMS"} or re.match(r"^K-?ISMS", c, re.IGNORECASE):
        hay = (title + " " + str(doc.get("value", ""))).lower()
        is_singapore = "singapore" in hay or "pdpa" in hay or "sg pdpa" in hay
        is_korea_only = ("k-isms" in hay or "korea" in hay or "korean" in hay) and not is_singapore
        if is_korea_only:
            return []  # drop – misfiled under SG PDPA (should be Korea K-ISMS, not in catalogue)
        # Default (Singapore or ambiguous): map by title keyword.
        keymap: Sequence[Keyword] = [
            (("breach", "notification"), "§26A"),
            (("breach",), "§26A"),
            (("notifiable",), "§26B"),
            (("protection",), "§24"),
            (("security",), "§24"),
            (("measures",), "§24"),
            (("encryption",), "§24"),
            (("access",), "§24"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "§24")]
    return []


def _swift_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.upper() in {"SWIFT CSCF MANDATORY", "SWIFT CSCF ADVISORY", "SWIFT KYC-SA"}:
        keymap: Sequence[Keyword] = [
            (("malware",), "6.1"),
            (("antivirus",), "6.1"),
            (("monitor",), "6.4"),
            (("logging",), "6.4"),
            (("siem",), "6.4"),
            (("environment",), "1.1"),
            (("zone",), "1.1"),
            (("segregation",), "1.1"),
            (("isolation",), "1.1"),
            (("kyc",), "1.1"),
            (("attestation",), "1.1"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "6.4")]
    return []


def _asd_e8_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.upper().startswith("ASD ESSENTIAL"):
        keymap: Sequence[Keyword] = [
            (("application", "control"), "E8.01"),
            (("macro",), "E8.03"),
            (("office",), "E8.03"),
            (("privilege",), "E8.05"),
            (("admin",), "E8.05"),
            (("patch", "os"), "E8.06"),
            (("operating system",), "E8.06"),
            (("os", "patch"), "E8.06"),
            (("patch",), "E8.06"),
            (("backup",), "E8.08"),
            (("restore",), "E8.08"),
            (("user application hardening",), "E8.02"),
            (("hardening",), "E8.02"),
            (("mfa",), "E8.07"),
            (("multi-factor",), "E8.07"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "E8.01")]
    return []


def _appi_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.upper() == "APPI":
        keymap: Sequence[Keyword] = [
            (("breach",), "Art.26"),
            (("leakage",), "Art.26"),
            (("notification",), "Art.26"),
            (("security",), "Art.23"),
            (("control",), "Art.23"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "Art.23")]
    return []


def _apra_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.upper() == "APRA CPS 234":
        keymap: Sequence[Keyword] = [
            (("notification",), "36"),
            (("notify",), "36"),
            (("incident",), "23"),
            (("information security",), "23"),
            (("framework",), "15"),
            (("policy",), "15"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "23")]
    return []


def _rbi_cyber_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.lower().startswith("rbi cyber"):
        keymap: Sequence[Keyword] = [
            (("crisis",), "Annex-B"),
            (("incident",), "Annex-B"),
            (("response",), "Annex-B"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "Annex-A")]
    return []


def _mas_trm_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.upper() == "MAS TRM":
        keymap: Sequence[Keyword] = [
            (("incident",), "§8.1.1"),
            (("resilience",), "§11.1.1"),
            (("governance",), "§4.1.1"),
            (("technology", "risk"), "§4.1.1"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "§4.1.1")]
    return []


def _cjis_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.upper() == "CJIS SECURITY POLICY":
        keymap: Sequence[Keyword] = [
            (("incident",), "5.13.3"),
            (("response",), "5.13.3"),
            (("access",), "5.5.1"),
            (("authentication",), "5.5.1"),
            (("identification",), "5.5.1"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "5.5.1")]
    return []


def _fca_ss1_21_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.lower().startswith("fca operational resilience"):
        keymap: Sequence[Keyword] = [
            (("impact",), "§2.1"),
            (("tolerance",), "§2.1"),
            (("test",), "§3.1"),
            (("scenario",), "§3.1"),
            (("identify",), "§1.1"),
            (("important", "business"), "§1.1"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "§1.1")]
    return []


def _fca_smcr_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.upper() == "SM&CR":
        keymap: Sequence[Keyword] = [
            (("conduct",), "COCON 2"),
            (("senior manager",), "SMR 1"),
            (("smr",), "SMR 1"),
            (("control",), "SYSC 3.2"),
            (("system",), "SYSC 3.2"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "SMR 1")]
    return []


def _pra_ss2_21_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if re.match(r"^PR\s+A\s+outsourcing", c, re.IGNORECASE):
        keymap: Sequence[Keyword] = [
            (("exit",), "§9"),
            (("continuity",), "§9"),
            (("proportionality",), "§3.2"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "§3.2")]
    return []


def _no_sikkerhetsloven_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if re.match(r"^(Si\s+kkerhetsloven|NSM)\b", c, re.IGNORECASE):
        keymap: Sequence[Keyword] = [
            (("risk",), "§5-3"),
            (("documentation",), "§5-3"),
            (("assessment",), "§6-2"),
            (("protection",), "§6-2"),
            (("accreditation",), "§6-2"),
            (("ikt",), "§5-3"),
            (("rut",), "§5-3"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "§5-3")]
    return []


def _no_kbf_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if re.match(r"^(NVE|RME|Kraftberedskap)", c, re.IGNORECASE):
        return ["§6-1"]
    return []


def _no_petroleum_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if re.match(r"^(Petroleumsforskriften|PSA|HSE)", c, re.IGNORECASE):
        return ["§15"]  # grammar-valid and referenced in examples
    return []


def _no_personopp_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if re.match(r"^(Personopplysningsloven|Altinn|fødselsnummer)", c, re.IGNORECASE):
        return ["§8"]  # grammar-valid §\d+; matches examples in catalogue
    return []


def _nzism_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.upper() == "NZISM":
        keymap: Sequence[Keyword] = [
            (("incident",), "§17.2.17"),
            (("response",), "§17.2.17"),
            (("access",), "§16.1.32"),
            (("user", "access"), "§16.1.32"),
            (("logging",), "§16.6.9"),
            (("event",), "§16.6.9"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "§16.6.9")]
    return []


def _nesa_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.upper() == "NESA UAE IAS":
        keymap: Sequence[Keyword] = [
            (("incident",), "T6.3"),
            (("log",), "T4.3"),
            (("monitoring",), "T4.3"),
            (("access",), "T3.2"),
            (("encryption",), "T3.5"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "T3.2")]
    return []


def _sama_csf_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.lower().startswith("sama cyber"):
        keymap: Sequence[Keyword] = [
            (("monitoring",), "3.3.5"),
            (("detect",), "3.3.5"),
            (("governance",), "3.1.1"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "3.1.1")]
    return []


def _sa_pdpl_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.lower() == "saudi pdpl":
        keymap: Sequence[Keyword] = [
            (("breach",), "Art. 20"),
            (("notification",), "Art. 20"),
            (("security",), "Art. 19"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "Art. 19")]
    return []


def _qcb_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.lower().startswith("qatar central bank"):
        keymap: Sequence[Keyword] = [
            (("incident",), "§6.2"),
            (("monitoring",), "§4.1"),
            (("governance",), "§3.1"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "§3.1")]
    return []


def _hkma_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.upper() == "HKMA TM-G-2":
        return ["§3"]
    return []


def _bait_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.upper() == "BAIT/KAIT":
        keymap: Sequence[Keyword] = [
            (("operations",), "§9"),
            (("ict", "operations"), "§9"),
            (("access",), "§5"),
            (("identity",), "§5"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "§5")]
    return []


def _bsi_kritis_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    if c.upper() == "BSI-KRITISV":
        return ["§8a"]
    return []


def _it_sig_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.upper() == "BSI":
        keymap: Sequence[Keyword] = [
            (("notification",), "§8b"),
            (("report",), "§8b"),
            (("security", "measures"), "§8a"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "§8a")]
    return []


def _it_grundschutz_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.upper() == "IT-GRUNDSCHUTZ":
        keymap: Sequence[Keyword] = [
            (("access",), "ORP.4"),
            (("identity",), "ORP.4"),
            (("operation",), "OPS.1.1.2"),
            (("ict",), "OPS.1.1.2"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "OPS.1.1.2")]
    return []


def _iec62443_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    # "IEC 62443-4-2 / CR X.Y" → "CR X.Y"
    m = re.match(r"IEC\s*62443-\d+-\d+\s*/\s*(SR|FR|CR|NDR)\s*(\d+(?:\.\d+)*)", c, re.IGNORECASE)
    if m:
        return [f"{m.group(1).upper()} {m.group(2)}"]
    # "IEC 62443-3-2 / <descriptive>" → map by keyword to a CR / SR
    m = re.match(r"IEC\s*62443-\d+-\d+\s*/\s*(.+)", c, re.IGNORECASE)
    if m:
        descriptive = m.group(1).lower()
        keymap: Sequence[Keyword] = [
            (("zone", "boundary"), "SR 5.1"),
            (("boundary", "monitor"), "SR 5.1"),
            (("conduit",), "SR 5.1"),
            (("allowlist",), "SR 5.1"),
            (("protocol", "anomaly"), "FR 6.2"),
            (("safety",), "SR 5.1"),
            (("engineering",), "SR 1.1"),
            (("historian",), "SR 2.8"),
            (("wireless",), "SR 1.1"),
            (("remote",), "SR 1.1"),
            (("trust",), "SR 1.1"),
        ]
        return [_pick_by_keywords(descriptive, "", keymap, "FR 6.2")]
    if c.upper() == "OT":
        return ["FR 6.2"]
    return []


def _lgpd_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if re.match(r"^Lei\s+Geral", c, re.IGNORECASE):
        keymap: Sequence[Keyword] = [
            (("breach",), "Art.48"),
            (("notification",), "Art.48"),
            (("security",), "Art.46"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "Art.46")]
    return []


def _eidas_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.lower() in {"eidas", "eidas 2.0", "etsi"}:
        # commonClause is Art.24; other authoritative ones are Art.19, Art.32, Art.40
        keymap: Sequence[Keyword] = [
            (("qualified",), "Art.24"),
            (("trust service",), "Art.24"),
            (("signature",), "Art.26"),
            (("certificate",), "Art.28"),
            (("identity",), "Art.7"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "Art.24")]
    return []


def _eu_ai_act_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.lower() == "eu ai act":
        keymap: Sequence[Keyword] = [
            (("human", "oversight"), "Art.14"),
            (("oversight",), "Art.14"),
            (("accuracy",), "Art.15"),
            (("robust",), "Art.15"),
            (("cybersecurity",), "Art.15"),
            (("logging",), "Art.19"),
            (("deployer",), "Art.26"),
            (("high-risk",), "Art.26"),
            (("transparency",), "Art.13"),
            (("record",), "Art.12"),
            (("record-keeping",), "Art.12"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "Art.13")]
    return []


def _eu_cra_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.lower() == "eu cra":
        keymap: Sequence[Keyword] = [
            (("report", "vulnerability"), "Art.14"),
            (("reporting",), "Art.14"),
            (("vulnerability",), "Art.14"),
            (("manufacturer",), "Art.13"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "Art.13")]
    return []


def _fda_part_11_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.lower() == "21 cfr part 11":
        keymap: Sequence[Keyword] = [
            (("signature",), "§11.200"),
            (("electronic signature",), "§11.200"),
            (("access",), "§11.10(d)"),
            (("authorized",), "§11.10(d)"),
            (("audit trail",), "§11.10(e)"),
            (("audit",), "§11.10(e)"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "§11.10(e)")]
    return []


def _uk_nis_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.lower() == "uk nis regulations":
        keymap: Sequence[Keyword] = [
            (("report",), "Reg.11"),
            (("reporting",), "Reg.11"),
            (("incident",), "Reg.11"),
            (("security", "duties"), "Reg.10"),
            (("duties",), "Reg.10"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "Reg.10")]
    return []


def _cyber_essentials_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    title = str(doc.get("title", ""))
    if c.lower() == "cyber essentials":
        keymap: Sequence[Keyword] = [
            (("firewall",), "CE.BF.1"),
            (("boundary",), "CE.BF.1"),
            (("authentication",), "CE.SAU.1"),
            (("password",), "CE.SAU.1"),
            (("access",), "CE.SAU.1"),
        ]
        return [_pick_by_keywords(title, str(doc.get("value", "")), keymap, "CE.SAU.1")]
    return []


def _nist_csf_rewriter(clause: str, doc: Mapping[str, Any]) -> List[str]:
    c = clause.strip()
    # "Id entify/Protect/Detect/Respond/Recover" (broken spaced token)
    if re.search(r"Id\s+entify", c, re.IGNORECASE):
        return ["ID.AM-01"]
    if c.upper() == "MITRE ATT&CK":
        # Not a NIST CSF clause — drop
        return []
    return []


# Registry keyed by (short_name_lower, version_lower); the version component
# allows the same short name to map to different rewriters across versions.
REWRITE_RULES: Dict[Tuple[str, str], RewriteFn] = {
    ("gdpr", "2016/679"): _gdpr_rewriter,
    ("nis2", "directive (eu) 2022/2555"): _nis2_rewriter,
    ("dora", "regulation (eu) 2022/2554"): _dora_rewriter,
    ("soc 2", "2017 tsc"): _soc2_rewriter,
    ("iso 27001", "2022"): _iso27001_rewriter,
    ("ccpa/cpra", "cpra (as amended)"): _ccpa_rewriter,
    ("mifid ii", "directive 2014/65/eu"): _mifid_rewriter,
    ("pci dss", "v4.0"): _pci_rewriter,
    ("hipaa security", "2013-final"): _hipaa_security_rewriter,
    ("fisma", "2014"): _fisma_rewriter,
    ("sox itgc", "pcaob as 2201"): _sox_itgc_rewriter,
    ("cmmc", "2.0"): _cmmc_rewriter,
    ("tsa sd", "sd02c"): _tsa_sd_rewriter,
    ("api rp 1164", "3rd edition"): _api_rp_1164_rewriter,
    ("psd2", "directive (eu) 2015/2366"): _psd2_rewriter,
    ("eu aml", "6amld / amlr 2024"): _eu_aml_rewriter,
    ("au privacy act", "current"): _au_privacy_rewriter,
    ("pipl", "2021"): _pipl_rewriter,
    ("sg pdpa", "2020 amended"): _sg_pdpa_rewriter,
    ("swift csp", "cscf v2025"): _swift_rewriter,
    ("asd e8", "nov 2023"): _asd_e8_rewriter,
    ("appi", "2022 amendments"): _appi_rewriter,
    ("apra cps 234", "current"): _apra_rewriter,
    ("rbi cyber", "2016 (as amended)"): _rbi_cyber_rewriter,
    ("mas trm", "2021"): _mas_trm_rewriter,
    ("cjis", "v5.9.4"): _cjis_rewriter,
    ("fca ss1/21", "2021"): _fca_ss1_21_rewriter,
    ("fca sm&cr", "current"): _fca_smcr_rewriter,
    ("pra ss2/21", "2021"): _pra_ss2_21_rewriter,
    ("no sikkerhetsloven", "2018"): _no_sikkerhetsloven_rewriter,
    ("no kbf", "2012 as amended"): _no_kbf_rewriter,
    ("no petroleumsforskriften", "1997 as amended"): _no_petroleum_rewriter,
    ("no personopplysningsloven", "2018"): _no_personopp_rewriter,
    ("nzism", "3.7"): _nzism_rewriter,
    ("nesa ias", "v2 (2020)"): _nesa_rewriter,
    ("sama csf", "v1.0 (2017)"): _sama_csf_rewriter,
    ("sa pdpl", "current"): _sa_pdpl_rewriter,
    ("qcb cyber", "2018"): _qcb_rewriter,
    ("hkma tm-g-2", "current"): _hkma_rewriter,
    ("bait/kait", "aug 2021"): _bait_rewriter,
    ("bsi-kritisv", "2021 (as amended)"): _bsi_kritis_rewriter,
    ("it-sig 2.0", "2021"): _it_sig_rewriter,
    ("it-grundschutz", "2023 edition"): _it_grundschutz_rewriter,
    ("iec 62443", "2013-ongoing"): _iec62443_rewriter,
    ("lgpd", "lei nº 13.709/2018"): _lgpd_rewriter,
    ("eidas", "regulation (eu) 2024/1183"): _eidas_rewriter,
    ("eu ai act", "regulation (eu) 2024/1689"): _eu_ai_act_rewriter,
    ("eu cra", "regulation (eu) 2024/2847"): _eu_cra_rewriter,
    ("fda part 11", "current"): _fda_part_11_rewriter,
    ("uk nis", "2018"): _uk_nis_rewriter,
    ("cyber essentials", "montpellier (2025)"): _cyber_essentials_rewriter,
    ("nist csf", "2.0"): _nist_csf_rewriter,
}


# ---------------------------------------------------------------------------
# Main normaliser
# ---------------------------------------------------------------------------


@dataclass
class NormaliseStats:
    ucs_scanned: int = 0
    ucs_modified: int = 0
    entries_rewritten: int = 0
    entries_expanded: int = 0
    entries_dropped: int = 0
    entries_unchanged_grammar_ok: int = 0
    entries_left_in_baseline: int = 0
    per_regulation: Dict[str, int] = field(default_factory=dict)


def _dedup(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove exact-duplicate compliance entries (same reg+version+clause)."""
    seen: set[Tuple[str, str, str]] = set()
    out: List[Dict[str, Any]] = []
    for e in entries:
        key = (str(e.get("regulation", "")), str(e.get("version", "")), str(e.get("clause", "")))
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def _rewrite_rationale(entry: Mapping[str, Any], old_clause: str, new_clause: str) -> str:
    base = str(entry.get("assurance_rationale", "")).strip()
    if NORMALISATION_NOTE.strip() in base:
        return base
    if base.startswith("Auto-migrated from cat-22 markdown"):
        return (
            f"Auto-migrated from cat-22 markdown on Phase 1.3 run, then normalised in "
            f"Phase A (clause '{old_clause}' → '{new_clause}'). Requires SME review to "
            f"confirm clause accuracy, mode (satisfies vs detects-violation-of), and "
            f"assurance level (contributing/partial/full)."
        )
    return base + NORMALISATION_NOTE


def normalise_entry(
    entry: Dict[str, Any], doc: Mapping[str, Any], catalogue: RegsCatalogue, stats: NormaliseStats
) -> List[Dict[str, Any]]:
    """Return the rewritten compliance entries for a single input entry.

    * Returns ``[entry]`` if the clause is already valid (unchanged).
    * Returns ``[rewritten1, rewritten2, ...]`` for expansion (e.g. range).
    * Returns ``[]`` if the entry must be dropped.
    * Returns ``[entry]`` (unchanged) if no rule applies – the audit script
      will keep baselining it and a later phase can tackle it.
    """

    reg_name = entry.get("regulation", "")
    version = entry.get("version", "")
    clause = entry.get("clause", "")
    fid = catalogue.resolve(reg_name)
    if not fid:
        return [entry]
    rv = catalogue.version(fid, version)
    if not rv:
        return [entry]

    if rv.grammar.match(clause or ""):
        stats.entries_unchanged_grammar_ok += 1
        return [entry]

    # Find the rule using the regulation shortName (resolved through the catalogue).
    key = (rv.short_name.lower(), version.lower())
    rewriter = REWRITE_RULES.get(key)
    if not rewriter:
        stats.entries_left_in_baseline += 1
        return [entry]

    new_clauses = rewriter(clause, doc)
    if new_clauses is None:
        stats.entries_left_in_baseline += 1
        return [entry]
    # Validate that each proposed clause actually matches the grammar. Anything
    # that fails is a bug in the rule — fall back to leaving the entry untouched.
    valid: List[str] = []
    for nc in new_clauses:
        if rv.grammar.match(nc):
            valid.append(nc)
        else:
            sys.stderr.write(
                f"warn: rule for {rv.short_name}@{rv.version} proposed invalid "
                f"clause '{nc}' (from '{clause}') for UC {doc.get('id')}; "
                f"leaving original in place\n"
            )
    if new_clauses and not valid:
        # Rule returned only invalid clauses — leave original untouched.
        stats.entries_left_in_baseline += 1
        return [entry]

    if not new_clauses:
        stats.entries_dropped += 1
        stats.per_regulation[rv.short_name] = stats.per_regulation.get(rv.short_name, 0) + 1
        return []

    # Build the replacement entries.
    out: List[Dict[str, Any]] = []
    for nc in valid:
        new_entry = dict(entry)
        new_entry["clause"] = nc
        new_entry["assurance_rationale"] = _rewrite_rationale(entry, clause, nc)
        out.append(new_entry)

    if len(valid) > 1:
        stats.entries_expanded += 1
    stats.entries_rewritten += 1
    stats.per_regulation[rv.short_name] = stats.per_regulation.get(rv.short_name, 0) + 1
    return out


def normalise_uc_file(path: pathlib.Path, catalogue: RegsCatalogue, stats: NormaliseStats, dry_run: bool = False) -> bool:
    raw = path.read_text(encoding="utf-8")
    doc = json.loads(raw)
    compliance = doc.get("compliance") or []
    new_entries: List[Dict[str, Any]] = []
    changed = False
    for entry in compliance:
        rewritten = normalise_entry(entry, doc, catalogue, stats)
        if rewritten != [entry]:
            changed = True
        new_entries.extend(rewritten)
    new_entries = _dedup(new_entries)
    if not new_entries:
        # Schema requires compliance minItems:1; keep the first original entry as-is.
        sys.stderr.write(
            f"warn: {path.name}: every compliance entry would be dropped; keeping "
            f"original entries to satisfy schema. Review this UC manually.\n"
        )
        new_entries = list(compliance)
        changed = False
    if not changed:
        return False
    doc["compliance"] = new_entries
    if not dry_run:
        # Write with a stable JSON formatting to minimise diff noise.
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing files.")
    parser.add_argument("--limit-regulation", default=None, help="Only normalise entries for this regulation shortName.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Emit per-UC changes.")
    args = parser.parse_args()

    catalogue = RegsCatalogue.load()
    stats = NormaliseStats()

    modified: List[str] = []
    for path in sorted(REPO_ROOT.glob(UC_GLOB)):
        if not path.is_file():
            continue
        stats.ucs_scanned += 1
        try:
            changed = normalise_uc_file(path, catalogue, stats, dry_run=args.dry_run)
        except json.JSONDecodeError as err:
            sys.stderr.write(f"error: {path}: {err}\n")
            continue
        if changed:
            stats.ucs_modified += 1
            modified.append(str(path.relative_to(REPO_ROOT)))
            if args.verbose:
                sys.stdout.write(f"modified: {path.relative_to(REPO_ROOT)}\n")

    sys.stdout.write("\nClause normalisation summary\n")
    sys.stdout.write("============================\n")
    sys.stdout.write(f"  UCs scanned               : {stats.ucs_scanned}\n")
    sys.stdout.write(f"  UCs modified              : {stats.ucs_modified}\n")
    sys.stdout.write(f"  entries rewritten         : {stats.entries_rewritten}\n")
    sys.stdout.write(f"  entries expanded (range)  : {stats.entries_expanded}\n")
    sys.stdout.write(f"  entries dropped           : {stats.entries_dropped}\n")
    sys.stdout.write(f"  entries grammar-ok kept   : {stats.entries_unchanged_grammar_ok}\n")
    sys.stdout.write(f"  entries left in baseline  : {stats.entries_left_in_baseline}\n")
    if stats.per_regulation:
        sys.stdout.write("\n  Per regulation (rewritten+dropped entries):\n")
        for reg, n in sorted(stats.per_regulation.items(), key=lambda kv: (-kv[1], kv[0])):
            sys.stdout.write(f"    {n:4d}  {reg}\n")
    if args.dry_run:
        sys.stdout.write("\n[dry-run] no files written.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
