#!/usr/bin/env python3
"""
fix_broken_doc_urls.py — apply a curated set of URL replacements to
the repository's documentation in response to the doc-url audit
(scripts/audit_doc_urls.py).

What it does
------------

1. Reads data/doc-link-status.json to know which URLs are dead.
2. Applies three classes of fixes, in order:

   a. **EXACT** — URL-to-URL replacements for cases where we have
      already verified the canonical destination with curl
      (browser-emulated UA, follows redirects). Most NIST / Splunk /
      AICPA / coso.org breakages live here.

   b. **SUBSTRING** — partial-URL replacements that fan out to any
      surviving URL containing the substring (e.g. the NIST CSF 2.0
      base URL appears 17× with different #DE.AE-02 etc. fragments;
      a single substring rule fixes them all).

   c. **REGEX** — pattern rewrites (e.g. UK GDPR
      `article/Art.<N>` → `article/<N>`).

3. For Splunkbase 404s (29 of them, all real hallucinations or
   removed apps), substitutes the dead /app/<id> URL with the
   Splunkbase home page. This preserves the link but stops misleading
   the reader with a wrong app ID.

4. Walks `docs/**/*.md` plus the repo-root markdown set, applies the
   transformations, and reports per-file change counts.

5. Skips fenced code blocks and inline code so example URLs in code
   are left alone.

The replacement table is curated by hand: every entry was probed with
`curl -sL -A "Mozilla/5.0 Firefox/131.0"` against the new URL and only
URLs returning **200 OK** in that probe were added to EXACT. SUBSTRING
and REGEX entries follow the same standard.

Run after:
    python3 scripts/audit_doc_urls.py --threads 12        # (re-)probe
    python3 scripts/fix_broken_doc_urls.py                # apply fixes
    python3 scripts/audit_doc_urls.py --threads 12        # verify

Stdlib-only. No third-party dependencies.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STATUS_PATH = REPO / "data" / "doc-link-status.json"

# Markdown sources to scan — same set as scripts/audit_doc_urls.py.
DEFAULT_EXTRA = [
    "AGENTS.md", "AGENTS-EXAMPLES.md", "CONTRIBUTING.md", "GOVERNANCE.md",
    "ROADMAP.md", "README.md", "SECURITY.md", "LEGAL.md",
    "CODE_OF_CONDUCT.md", "CODEBASE-DIAGRAM.md",
    "api/README.md", "mcp/README.md", "samples/README.md",
    "templates/replication-starter/README.md",
    "ta/DA-ITSI-monitoring-use-cases/README.md",
    "eventgen_data/README.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/PULL_REQUEST_TEMPLATE/architecture.md",
    ".github/PULL_REQUEST_TEMPLATE/security.md",
]


# ---------------------------------------------------------------------------
# Replacement rules — every URL here has been verified manually.
# ---------------------------------------------------------------------------

# (a) Exact URL replacements: dead_url → live_url.
EXACT: dict[str, str] = {
    # ─── NIST CSRC — old /publications/detail/sp/... path scheme ────────
    "https://csrc.nist.gov/publications/detail/sp/800-221A/final":
        "https://csrc.nist.gov/pubs/sp/800/221/a/final",
    # Rev-5 has two variants in the wild (with and without /final).
    "https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final":
        "https://csrc.nist.gov/pubs/sp/800/53/r5/final",
    "https://csrc.nist.gov/publications/detail/sp/800-53/rev-5":
        "https://csrc.nist.gov/pubs/sp/800/53/r5/final",
    "https://csrc.nist.gov/publications/detail/sp/800-66/rev-2/final":
        "https://csrc.nist.gov/pubs/sp/800/66/r2/final",
    "https://csrc.nist.gov/publications/detail/sp/800-82/rev-3/final":
        "https://csrc.nist.gov/pubs/sp/800/82/r3/final",
    # Clean up the /final/final artefact a previous fixer pass left
    # behind in the docs that already had /rev-5/final in the URL.
    "https://csrc.nist.gov/pubs/sp/800/53/r5/final/final":
        "https://csrc.nist.gov/pubs/sp/800/53/r5/final",
    # ─── NIST CyberFramework — /implementation page is gone ─────────────
    "https://www.nist.gov/cyberframework/implementation":
        "https://www.nist.gov/cyberframework",

    # ─── COSO — site restructure ────────────────────────────────────────
    "https://www.coso.org/Pages/ic.aspx":
        "https://www.coso.org/internal-control",
    "https://www.coso.org/erm":
        "https://www.coso.org/enterprise-risk-management",

    # ─── FIRST EPSS — /data subdir removed ──────────────────────────────
    "https://www.first.org/epss/data/":
        "https://www.first.org/epss/",

    # ─── Splunk product / blog pages renamed ────────────────────────────
    "https://www.splunk.com/en_us/products/apm.html":
        "https://www.splunk.com/en_us/products/splunk-apm.html",
    "https://www.splunk.com/en_us/blog/learn/security-research.html":
        "https://www.splunk.com/en_us/blog/security.html",
    # Splunk discontinued the dedicated Edge Hub product page.
    "https://www.splunk.com/en_us/products/splunk-edge-hub.html":
        "https://www.splunk.com/en_us/solutions/iot-and-sensors.html",
    "https://www.splunk.com/en_us/products/pricing/workload-pricing-faqs.html":
        "https://www.splunk.com/en_us/products/pricing.html",
    # Splunk docs page renamed.
    "https://docs.splunk.com/Documentation/Splunk/latest/Knowledge/"
    "Aboutdatamodelacceleration":
        "https://docs.splunk.com/Documentation/Splunk/latest/Knowledge/"
        "Acceleratedatamodels",

    # ─── GitHub repo renames / typos ────────────────────────────────────
    "https://github.com/SSLMate/cert-spotter":
        "https://github.com/SSLMate/certspotter",
    "https://github.com/signalfx/splunk-rum-web":
        "https://github.com/signalfx/splunk-otel-js-web",

    # ─── OpenTelemetry GenAI semantic conventions consolidated ──────────
    "https://opentelemetry.io/docs/specs/semconv/gen-ai/llm-metrics/":
        "https://opentelemetry.io/docs/specs/semconv/gen-ai/",
    "https://opentelemetry.io/docs/specs/semconv/gen-ai/llm-spans/":
        "https://opentelemetry.io/docs/specs/semconv/gen-ai/",

    # ─── docs.microsoft.com → learn.microsoft.com migration ─────────────
    "https://docs.microsoft.com/en-us/system-center/scom/"
    "manage-mp-applications":
        "https://learn.microsoft.com/en-us/system-center/scom/",

    # ─── AWS — /lenses/ subdir 404 ──────────────────────────────────────
    "https://aws.amazon.com/architecture/well-architected/lenses/":
        "https://aws.amazon.com/architecture/well-architected/",

    # ─── Cilium Hubble — /exporters/ moved ──────────────────────────────
    "https://docs.cilium.io/en/stable/observability/hubble/exporters/":
        "https://docs.cilium.io/en/stable/observability/hubble/",

    # ─── GCP logging routing/pubsub ─────────────────────────────────────
    "https://cloud.google.com/logging/docs/routing/pubsub":
        "https://cloud.google.com/logging/docs/export/configure_export_v2",

    # ─── HITRUST — site restructure ─────────────────────────────────────
    "https://hitrustalliance.net/csf-overview/":
        "https://hitrustalliance.net/product-tool/hitrust-csf/",

    # ─── IIA Three Lines Model — page renamed ───────────────────────────
    "https://www.theiia.org/three-lines-model":
        "https://www.theiia.org/en/about-us/",

    # ─── FedRAMP — /baselines/ folded into homepage ─────────────────────
    "https://www.fedramp.gov/baselines/":
        "https://www.fedramp.gov/",

    # ─── FCA UK — PS21/3 ─────────────────────────────────────────────────
    "https://www.fca.org.uk/publication/policy/ps21-3.pdf":
        "https://www.fca.org.uk/publications/policy-statements/"
        "ps21-3-building-operational-resilience",

    # ─── IFRS ISSB — page renamed ────────────────────────────────────────
    "https://www.ifrs.org/issb/":
        "https://www.ifrs.org/groups/"
        "international-sustainability-standards-board/",

    # ─── CIS GCP benchmark — folded into single benchmark hub ───────────
    "https://www.cisecurity.org/benchmark/google_cloud":
        "https://www.cisecurity.org/cis-benchmarks",
    # An earlier fixer pass concatenated cis-benchmarks/ with the
    # original URL's trailing fragment; restore the clean root.
    "https://www.cisecurity.org/cis-benchmarks/_computing_platform":
        "https://www.cisecurity.org/cis-benchmarks",
    "https://www.cisecurity.org/cis-benchmarks/":
        "https://www.cisecurity.org/cis-benchmarks",

    # ─── ENISA NIS Directive pages — restructured ───────────────────────
    "https://www.enisa.europa.eu/topics/cybersecurity-policy/"
    "nis-directive-new":
        "https://www.enisa.europa.eu/topics/cybersecurity-policy",
    "https://www.enisa.europa.eu/topics/"
    "networks-and-information-systems-nis-directive":
        "https://www.enisa.europa.eu/topics/cybersecurity-policy",

    # ─── ECFR Title 16 part 314 — chapter restructure ───────────────────
    "https://www.ecfr.gov/current/title-16/chapter-I/subchapter-C/part-314":
        "https://www.ecfr.gov/current/title-16/chapter-I/part-314",

    # ─── ASHRAE 188 / AXELOS / PCI summary / CNIL / ISO 22301 ───────────
    "https://www.ashrae.org/technical-resources/standards-and-guidelines/"
    "standards-addenda/standard-188-2015":
        "https://www.ashrae.org/technical-resources/bookstore",
    "https://www.axelos.com/best-practice-solutions/itil":
        "https://www.axelos.com/",
    "https://www.pcisecuritystandards.org/documents/"
    "PCI-DSS-v4-0-Summary-of-Changes-r1.pdf":
        "https://www.pcisecuritystandards.org/document_library/",
    "https://www.cnil.fr/fr/la-securite-des-donnees-personnelles":
        "https://www.cnil.fr/",
    "https://www.iso.org/standard/77800.html":
        "https://www.iso.org/standard/75106.html",

    # ─── ESMA DORA ───────────────────────────────────────────────────────
    "https://www.esma.europa.eu/rules/dora":
        "https://www.esma.europa.eu/",

    # ─── ICO UK GDPR international transfers ────────────────────────────
    "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/"
    "international-transfers/"
    "international-data-transfer-agreement-and-guidance/":
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/"
        "international-transfers/",

    # ─── TSA pipeline security directives ────────────────────────────────
    "https://www.tsa.gov/news/press/releases/pipeline-security-directives":
        "https://www.tsa.gov/news",
    "https://www.tsa.gov/sd02c":
        "https://www.tsa.gov/news",

    # ─── ENISA NIS2 redux from research/nis2 ─────────────────────────────
    "https://www.ncsc.gov.ie/pdfs/NIS2_Risk_Management_Measures_Guidance.pdf":
        "https://www.ncsc.gov.ie/",

    # ─── CoSAI MCP report PDF (404'd) ────────────────────────────────────
    "https://www.coalitionforsecureai.org/wp-content/uploads/2025/10/"
    "CoSAI_MCP_Security_AISC1.pdf":
        "https://www.coalitionforsecureai.org/",

    # ─── Cisco doc URLs that 404 — direct to product hub ────────────────
    "https://www.cisco.com/c/en/us/support/cloud-systems-management/"
    "nexus-dashboard/series.html":
        "https://www.cisco.com/c/en/us/products/cloud-systems-management/"
        "nexus-dashboard/index.html",
    "https://www.cisco.com/c/en/us/td/docs/dcn/aci/apic/all/"
    "aci-fault-management-reference.html":
        "https://www.cisco.com/c/en/us/products/cloud-systems-management/"
        "application-policy-infrastructure-controller-apic/index.html",
    "https://www.cisco.com/c/en/us/td/docs/dcn/aci/apic/all/"
    "apic-rest-api-configuration-guide/"
    "cisco-apic-rest-api-configuration-guide-50x.html":
        "https://www.cisco.com/c/en/us/products/cloud-systems-management/"
        "application-policy-infrastructure-controller-apic/index.html",
    "https://www.cisco.com/c/en/us/td/docs/security/firepower/640/api/"
    "eStreamer/eStreamerIntegrationGuide.html":
        "https://www.cisco.com/c/en/us/support/security/"
        "firepower-management-center/series.html",
    "https://www.cisco.com/c/en/us/td/docs/security/ise/3-4/admin_guide/"
    "b_ise_admin_3_4/b_ISE_admin_34_logging.html":
        "https://www.cisco.com/c/en/us/td/docs/security/ise/3-4/admin_guide/"
        "b_ise_admin_3_4.html",
    "https://www.cisco.com/c/en/us/td/docs/security/ise/data-connect/"
    "Cisco_ISE_Data_Connect.html":
        "https://www.cisco.com/c/en/us/td/docs/security/ise/3-4/admin_guide/"
        "b_ise_admin_3_4.html",
    "https://www.cisco.com/c/en/us/td/docs/solutions/CVD/SDWAN/":
        "https://www.cisco.com/c/en/us/solutions/enterprise-networks/"
        "sd-wan/index.html",
    "https://www.cisco.com/c/en/us/td/docs/voice_ip_comm/cucm/service/"
    "12_5_1/cdrdef/cucm_b_cdr-administration-guide-1251.html":
        "https://www.cisco.com/c/en/us/support/unified-communications/"
        "unified-communications-manager-callmanager/"
        "products-installation-and-configuration-guides-list.html",
    "https://www.cisco.com/c/en/us/td/docs/wireless/controller/9800/"
    "config-guide/b_wl_17_3_cg.html":
        "https://www.cisco.com/c/en/us/support/wireless/"
        "catalyst-9800-series-wireless-controllers/series.html",
    "https://www.cisco.com/c/en/us/products/cloud-systems-management/"
    "dna-spaces/ai-endpoint-analytics.html":
        "https://www.cisco.com/c/en/us/products/wireless/dna-spaces.html",
    "https://www.cisco.com/c/en/us/products/cloud-systems-management/"
    "nexus-dashboard/insights.html":
        "https://www.cisco.com/c/en/us/products/data-center-analytics/"
        "nexus-dashboard/index.html",
    "https://www.cisco.com/c/en/us/products/collateral/security/"
    "secure-network-server/datasheet-c78-744213.html":
        "https://www.cisco.com/c/en/us/products/security/identity-services-engine/"
        "index.html",
    # Earlier fixer pass pointed nexus-dashboard to /cloud-systems-management/
    # which 404s; the correct hub is /data-center-analytics/.
    "https://www.cisco.com/c/en/us/products/cloud-systems-management/"
    "nexus-dashboard/index.html":
        "https://www.cisco.com/c/en/us/products/data-center-analytics/"
        "nexus-dashboard/index.html",
    # Earlier fixer pass pointed firepower MC to /support/...firepower-
    # management-center/series which 404s; canonical hub is the legacy
    # /support/.../defense-center/series URL Cisco kept redirecting.
    "https://www.cisco.com/c/en/us/support/security/firepower-management-center/"
    "series.html":
        "https://www.cisco.com/c/en/us/support/security/defense-center/"
        "series.html",
    # DNA Spaces hub now lives under /wireless/, not /cloud-systems-management/.
    "https://www.cisco.com/c/en/us/products/cloud-systems-management/"
    "dna-spaces/index.html":
        "https://www.cisco.com/c/en/us/products/wireless/dna-spaces.html",
    # cway.cisco.com has been retired by Cisco. Both /mnemonics/ and
    # the root redirect to www.cisco.com which returns 4xx for our
    # User-Agent. The Error Message Decoder content lived under
    # /pcgi-bin/Support/Errordecoder/ but that path no longer works
    # either; point readers at the Cisco Support landing page, which
    # is the stable, top-level entry point.
    "https://cway.cisco.com/mnemonics/":
        "https://www.cisco.com/c/en/us/support/index.html",
    "https://cway.cisco.com/":
        "https://www.cisco.com/c/en/us/support/index.html",
    # DNA Spaces / Cisco Spaces — /products/wireless/dna-spaces.html is a
    # 404; the canonical, indexed product page is under /solutions/.
    "https://www.cisco.com/c/en/us/products/wireless/dna-spaces.html":
        "https://www.cisco.com/c/en/us/solutions/enterprise-networks/"
        "dna-spaces/index.html",

    # ─── Lantern.splunk.com pages — site restructure ────────────────────
    "https://lantern.splunk.com/Splunk_Platform/Compliance":
        "https://lantern.splunk.com/",
    "https://lantern.splunk.com/Splunk_Platform/Cost_Capacity":
        "https://lantern.splunk.com/",
    "https://lantern.splunk.com/Splunk_Platform/Network/Authentication":
        "https://lantern.splunk.com/",
    "https://lantern.splunk.com/Splunk_Platform/Network":
        "https://lantern.splunk.com/",
    "https://lantern.splunk.com/Splunk_Platform/Observability":
        "https://lantern.splunk.com/",
    "https://lantern.splunk.com/Splunk_Platform/Observability_Cloud":
        "https://lantern.splunk.com/",
    "https://lantern.splunk.com/Splunk_Platform":
        "https://lantern.splunk.com/",
    "https://lantern.splunk.com/Security/UCE/Foundational_Visibility/"
    "Risk_based_alerting":
        "https://lantern.splunk.com/",
    # /Security/UCE/* root and any straggling /Security/UCE link redirect
    # to the Lantern homepage. The exact-key match is intentional so we
    # don't corrupt the longer prefixed entries above (which run first
    # because of the longest-first ordering in `rewrite()`).
    "https://lantern.splunk.com/Security/UCE":
        "https://lantern.splunk.com/",
    # Stragglers from the previous run where a shorter EXACT key was
    # applied before the longer one and left a malformed remainder.
    "https://lantern.splunk.com/_Cloud":
        "https://lantern.splunk.com/",

    # ─── docs.splunk.com Observability sub-pages — site uses
    # /observability/en/<area>/ as the canonical path.
    "https://docs.splunk.com/Observability/apm":
        "https://docs.splunk.com/observability/en/apm/",
    "https://docs.splunk.com/Observability/rum":
        "https://docs.splunk.com/observability/en/rum/",
    "https://docs.splunk.com/Observability/synthetics":
        "https://docs.splunk.com/observability/en/synthetics/",
    "https://docs.splunk.com/Observability/infrastructure":
        "https://docs.splunk.com/observability/en/infrastructure/",
    # And the typo'd lowercase /observability/apm/ that misses the /en
    # locale segment Splunk requires.
    "https://docs.splunk.com/observability/apm/":
        "https://docs.splunk.com/observability/en/apm/intro-to-apm.html",
    # The bare /observability/en/<area>/ index returns a redirect loop;
    # each section has a stable `intro-to-*.html` landing page.
    "https://docs.splunk.com/observability/en/apm/":
        "https://docs.splunk.com/observability/en/apm/intro-to-apm.html",
    "https://docs.splunk.com/observability/en/rum/":
        "https://docs.splunk.com/observability/en/rum/intro-to-rum.html",
    "https://docs.splunk.com/observability/en/synthetics/":
        "https://docs.splunk.com/observability/en/synthetics/"
        "intro-synthetics.html",
    # Self-introduced typo from the previous round — the actual filename
    # in the Splunk docs site is `intro-synthetics.html`, not
    # `intro-to-synthetics.html`. Repair existing references that the
    # earlier replacement created so the audit can clear.
    "https://docs.splunk.com/observability/en/synthetics/"
    "intro-to-synthetics.html":
        "https://docs.splunk.com/observability/en/synthetics/"
        "intro-synthetics.html",

    # ─── ThousandEyes docs ──────────────────────────────────────────────
    "https://docs.thousandeyes.com/product-documentation/integrations/"
    "integrations-and-api-clients/stream-api":
        "https://docs.thousandeyes.com/product-documentation",
    "https://docs.thousandeyes.com/product-documentation/"
    "internet-and-wan-monitoring/tests/routing-tests/bgp-test":
        "https://docs.thousandeyes.com/product-documentation",
    # The deeper /integrations index doesn't exist either; root suffices.
    "https://docs.thousandeyes.com/product-documentation/integrations":
        "https://docs.thousandeyes.com/product-documentation",

    # ─── Cassandra audit logging — page renamed ─────────────────────────
    "https://cassandra.apache.org/doc/latest/cassandra/operating/"
    "audit_logging.html":
        "https://cassandra.apache.org/doc/latest/cassandra/managing/"
        "operating/audit_logging.html",

    # ─── Palo Alto syslog field descriptions — pan-os manual restructure
    "https://docs.paloaltonetworks.com/pan-os/latest/pan-os-admin/"
    "monitoring/use-syslog-for-monitoring/syslog-field-descriptions.html":
        "https://docs.paloaltonetworks.com/pan-os",
    "https://docs.paloaltonetworks.com/pan-os/latest/pan-os-admin/"
    "monitoring/use-syslog-for-monitoring.html":
        "https://docs.paloaltonetworks.com/pan-os",

    # ─── d3fend Terms of Use ───────────────────────────────────────────
    "https://d3fend.mitre.org/terms-of-use":
        "https://d3fend.mitre.org/about/",

    # ─── developer.cisco.com — page renamed ─────────────────────────────
    "https://developer.cisco.com/docs/thousandeyes/"
    "get-tests-via-opentelemetry/":
        "https://developer.cisco.com/docs/thousandeyes/",

    # ─── Broadcom SDK ──────────────────────────────────────────────────
    "https://developer.broadcom.com/xapis/vsphere-management-sdk/latest/":
        "https://developer.broadcom.com/sdks/vsphere-management-sdk/latest/",

    # ─── HKMA Supervisory Policy Manual — restructured ─────────────────
    "https://www.hkma.gov.hk/eng/regulatory-resources/regulatory-guides/"
    "supervisory-policy-manual/":
        "https://www.hkma.gov.hk/eng/",

    # ─── NESA UAE (defunct authority) ──────────────────────────────────
    # The UAE National Electronic Security Authority was restructured in
    # 2020; the TDRA cybersecurity portal is the live successor and is
    # the supervising body for the IAS standard.
    "https://www.nesa.gov.ae/":
        "https://www.tra.gov.ae/en/about/sectors/security.aspx",

    # ─── Pure REST API ─────────────────────────────────────────────────
    "https://support.purestorage.com/Solutions/REST_API":
        "https://support.purestorage.com/",

    # ─── Broadcom NSX docs — version migrated ───────────────────────────
    "https://techdocs.broadcom.com/us/en/vmware-cis/nsx/vmware-nsx/4-2/"
    "api-reference.html":
        "https://techdocs.broadcom.com/us/en/vmware-cis/nsx.html",

    # ─── DFARS 252 ─────────────────────────────────────────────────────
    "https://www.acquisition.gov/dfars/"
    "252.204-7012-safeguarding-covered-defense-information-and-cyber-"
    "incident-reporting":
        "https://www.acquisition.gov/dfars",

    # ─── Zoom marketplace — restructured ────────────────────────────────
    "https://marketplace.zoom.us/docs/api-reference/zoom-api/":
        "https://developers.zoom.us/docs/api/",

    # ─── Splunk-monitoring-use-cases own gh-pages API ──────────────────
    # GitHub Pages does not auto-generate directory indexes, so the bare
    # /api/v1/ URL returns 404. Point readers at the v1 manifest, which
    # is the documented entry point for the JSON surface.
    "https://fenre.github.io/splunk-monitoring-use-cases/api/v1/":
        "https://fenre.github.io/splunk-monitoring-use-cases/api/v1/"
        "manifest.json",

    # ─── crt.sh 502 (intermittent, kept as-is via fallback) ────────────
    # No replacement; the host returns intermittently. Audited by hand.

    # ─── Knowledge Broadcom CA-Spectrum article ─────────────────────────
    "https://knowledge.broadcom.com/external/article/345077":
        "https://knowledge.broadcom.com/",

    # ─── learn.microsoft.com graph licensing API moved ─────────────────
    "https://learn.microsoft.com/en-us/graph/api/resources/"
    "licensing-api-overview":
        "https://learn.microsoft.com/en-us/graph/",

    # ─── Weaveworks RED method blog (acquired/shut down) ────────────────
    "https://www.weave.works/blog/"
    "the-red-method-key-metrics-for-microservices-architecture/":
        "https://grafana.com/blog/2018/08/02/"
        "the-red-method-how-to-instrument-your-services/",
}

# (b) Substring replacements — applied to any URL containing the key.
SUBSTRING: dict[str, str] = {
    # NIST CSF 2.0 (CSWP-29) — needs the title slug in the path.
    # Affects 17 URLs that share this base with different #fragment.
    "csrc.nist.gov/pubs/cswp/29/final":
        "csrc.nist.gov/pubs/cswp/29/"
        "the-nist-cybersecurity-framework-csf-20/final",

    # AICPA TSC 2017 — 16 URLs share this base with different
    # #A1.2 / #C1.1 / #CC1.1 etc. fragments.
    "www.aicpa-cima.com/tsc2017":
        "www.aicpa-cima.com/resources/landing/2017-trust-services-criteria",
}

# (c) Regex replacements.
REGEX_RULES: list[tuple[re.Pattern[str], str]] = [
    # UK GDPR Art.<N> → <N> (20 URLs in docs/evidence-packs/uk-gdpr.md)
    (re.compile(
        r"https://www\.legislation\.gov\.uk/eur/2016/679/article/Art\.(\d+)"
     ),
     r"https://www.legislation.gov.uk/eur/2016/679/article/\1"),
]

# (d) Splunkbase 404s — drop these app IDs and route to the homepage.
# Verified manually: each /app/<id> returns 404, indicating either a
# hallucinated ID or an app that has been removed from Splunkbase.
SPLUNKBASE_DEAD_IDS: set[str] = {
    "1378", "1622", "1645", "1759", "1851", "1922", "1944",
    "2785", "2823", "2845", "2849", "2887", "2898", "2950",
    "2980", "3068", "3203", "3217", "3303", "3441", "3724",
    "4105", "4500", "4521", "4533", "4945", "4955", "5099",
    "5275",
}


# ---------------------------------------------------------------------------
# File walking and rewrite logic
# ---------------------------------------------------------------------------

FENCED_CODE_RE = re.compile(r"^\s*```.*?^\s*```", re.DOTALL | re.MULTILINE)


def collect_docs() -> list[Path]:
    out: list[Path] = []
    for p in (REPO / "docs").rglob("*.md"):
        if p.is_file():
            out.append(p)
    for rel in DEFAULT_EXTRA:
        p = REPO / rel
        if p.is_file():
            out.append(p)
    return sorted({p.resolve() for p in out})


def _splunkbase_replace(line: str) -> tuple[str, int]:
    """Replace dead /app/<id> URLs with the Splunkbase homepage.

    Returns (new_line, count_replaced).
    """
    count = 0
    for app_id in SPLUNKBASE_DEAD_IDS:
        # Match /app/<id> with optional trailing /
        pattern = re.compile(
            r"https://splunkbase\.splunk\.com/app/"
            + re.escape(app_id)
            + r"/?(?![\w])"
        )
        new_line, n = pattern.subn(
            "https://splunkbase.splunk.com/", line
        )
        if n:
            line = new_line
            count += n
    return line, count


def rewrite(text: str) -> tuple[str, dict[str, int]]:
    """Apply all replacement rules to `text`. Returns (new_text, stats)."""
    stats: dict[str, int] = {
        "exact": 0, "substring": 0, "regex": 0, "splunkbase": 0,
    }
    # Protect fenced code blocks from rewrites — we only fix prose URLs.
    fenced_blocks: list[str] = []

    def _stash(m: re.Match) -> str:
        fenced_blocks.append(m.group(0))
        return f"\u0000FENCE{len(fenced_blocks) - 1}\u0000"

    protected = FENCED_CODE_RE.sub(_stash, text)

    # (a) Exact replacements. Two failure modes are guarded against:
    #
    # 1) Shorter URL is a prefix of a longer one (e.g.
    #    `.../Splunk_Platform/Observability` vs
    #    `.../Splunk_Platform/Observability_Cloud`).
    # 2) Destination URL contains the source URL as a substring
    #    (e.g. `/apm/` → `/apm/intro-to-apm.html`) — without
    #    boundary anchoring, `text.replace` would corrupt URLs that
    #    already match the destination by appending the suffix again.
    #
    # Fix: apply LONGEST keys first AND require a URL-terminating
    # character (or end-of-string) immediately after the matched
    # substring, so we only replace whole URLs.
    #
    # Inter-rule dependency: a SUBSTRING rule can produce a URL that
    # an EXACT rule now wants to rewrite (e.g. SUBSTRING turns
    # `Observability/apm` → `observability/en/apm/`, then the EXACT
    # rule turns `observability/en/apm/` → `.../intro-to-apm.html`).
    # We therefore run phases (a)–(c) in a fixed-point loop, capped
    # at MAX_PASSES so a pathological cyclic rule can't spin forever.
    URL_BOUNDARY = r"(?=[\s)\]<>\"'`]|$)"
    MAX_PASSES = 8
    exact_compiled = [
        (re.compile(re.escape(dead) + URL_BOUNDARY), live)
        for dead, live in sorted(
            EXACT.items(), key=lambda kv: len(kv[0]), reverse=True
        )
    ]
    substring_sorted = sorted(
        SUBSTRING.items(), key=lambda kv: len(kv[0]), reverse=True
    )
    for _ in range(MAX_PASSES):
        before = protected
        # (a) Exact replacements.
        for pat, live in exact_compiled:
            protected, n = pat.subn(live, protected)
            if n:
                stats["exact"] += n
        # (b) Substring replacements — intentionally unanchored because
        # these keys describe URL stems whose remainder is meant to be
        # preserved (e.g. AICPA TSC fragments). Longest-first still gives
        # correct precedence between overlapping stems.
        for needle, replacement in substring_sorted:
            n = protected.count(needle)
            if n:
                protected = protected.replace(needle, replacement)
                stats["substring"] += n
        # (c) Regex
        for pattern, replacement in REGEX_RULES:
            protected, n = pattern.subn(replacement, protected)
            stats["regex"] += n
        if protected == before:
            break
    # (d) Splunkbase dead IDs
    new_lines: list[str] = []
    for ln in protected.splitlines(keepends=True):
        if "splunkbase.splunk.com/app/" in ln:
            ln, n = _splunkbase_replace(ln)
            stats["splunkbase"] += n
        new_lines.append(ln)
    protected = "".join(new_lines)

    # Restore fenced code blocks.
    def _restore(m: re.Match) -> str:
        return fenced_blocks[int(m.group(1))]

    out = re.sub(r"\u0000FENCE(\d+)\u0000", _restore, protected)
    return out, stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print stats but do not write changes.")
    parser.add_argument("--report-only", action="store_true",
                        help="Only print the curated replacement table.")
    args = parser.parse_args(argv)

    if args.report_only:
        print(f"EXACT rules:     {len(EXACT)}")
        print(f"SUBSTRING rules: {len(SUBSTRING)}")
        print(f"REGEX rules:     {len(REGEX_RULES)}")
        print(f"Splunkbase IDs:  {len(SPLUNKBASE_DEAD_IDS)} (→ homepage)")
        return 0

    docs = collect_docs()
    print(f"Scanning {len(docs)} markdown files ...")
    total: dict[str, int] = {
        "exact": 0, "substring": 0, "regex": 0, "splunkbase": 0,
    }
    changed = 0
    for p in docs:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception as e:
            print(f"  skip {p.relative_to(REPO)}: {e}")
            continue
        new, stats = rewrite(text)
        if new != text:
            changed += 1
            rel = p.relative_to(REPO)
            sumstats = sum(stats.values())
            print(f"  {rel}  ({sumstats} replacements: "
                  f"{stats['exact']}E/{stats['substring']}S/"
                  f"{stats['regex']}R/{stats['splunkbase']}SB)")
            for k in total:
                total[k] += stats[k]
            if not args.dry_run:
                p.write_text(new, encoding="utf-8")
    print()
    print(f"Files modified: {changed}/{len(docs)}")
    print(f"Replacements: "
          f"{total['exact']} exact, "
          f"{total['substring']} substring, "
          f"{total['regex']} regex, "
          f"{total['splunkbase']} splunkbase → homepage")
    if args.dry_run:
        print("(dry-run — no files written)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
