/* ───────────────────────────────────────────────────────────────────────────
 *  docs-uc-map.js — Bidirectional mapping between documentation and use cases
 *
 *  Consumed by:
 *    docs.html  → DOC_UC_MAP  (UC chips below each doc entry)
 *    index.html → UC_DOC_MAP  (Related Documentation in UC detail panel)
 *
 *  Single source of truth: curate DOC_UC_MAP only; the reverse index is
 *  computed automatically.  Not every doc needs UC associations — architecture,
 *  governance, and process docs are listed without `ucs`.
 *
 *  Validation:  python3 build.py  (runs validate_docs_uc_map)
 *  Quick check: node -e "eval(require('fs').readFileSync('docs-uc-map.js','utf8')); \
 *    console.log(Object.keys(DOC_UC_MAP).length+' docs, '+Object.keys(UC_DOC_MAP).length+' UCs OK');"
 * ──────────────────────────────────────────────────────────────────────────── */

/* eslint-disable no-var */
/* global DOC_UC_MAP:writable, UC_DOC_MAP:writable */

var DOC_UC_MAP = {

  /* ── Getting Started ─────────────────────────────────────────────────── */
  "docs/implementation-guide.md": {
    title: "Implementation Guide",
    ucs: ["1.1.1", "1.2.1", "5.1.1", "7.1.1", "13.1.1"]
  },
  "docs/github-pages-setup.md": {
    title: "GitHub Pages Setup"
  },

  /* ── Product Design ──────────────────────────────────────────────────── */
  "docs/DESIGN.md": {
    title: "Product Design"
  },
  "docs/architecture.md": {
    title: "Architecture"
  },
  "docs/adr/0001-markdown-as-source-of-truth.md": {
    title: "ADR-0001: Markdown as Source of Truth"
  },
  "docs/adr/0002-static-single-page-app.md": {
    title: "ADR-0002: Static Single-Page App"
  },
  "docs/adr/0003-single-catalog-json-plus-per-category-api.md": {
    title: "ADR-0003: Single catalog.json + Per-Category API"
  },
  "docs/adr/0004-python-stdlib-only.md": {
    title: "ADR-0004: Python stdlib Only"
  },
  "docs/adr/0005-uc-id-x-y-z-scheme.md": {
    title: "ADR-0005: UC-ID X.Y.Z Scheme"
  },
  "docs/adr/0006-single-file-design-doc.md": {
    title: "ADR-0006: Single-File Design Doc"
  },
  "docs/adr/README.md": {
    title: "ADR Index"
  },

  /* ── Use Case Authoring ──────────────────────────────────────────────── */
  "docs/use-case-fields.md": {
    title: "Use Case Field Reference",
    ucs: ["1.1.1", "10.1.1", "22.1.1"]
  },
  "docs/gold-standard-template.md": {
    title: "Gold Standard Template",
    ucs: ["1.1.1"]
  },
  "docs/category-files-and-names.md": {
    title: "Category Files & Names"
  },
  "docs/grandma-explanations.md": {
    title: "Plain-Language Explanations"
  },
  "docs/implementation-ordering.md": {
    title: "Implementation Ordering (Crawl/Walk/Run)",
    ucs: ["1.1.1", "1.1.2", "5.1.1", "13.1.1"]
  },
  "docs/content-gap-analysis.md": {
    title: "Content Gap Analysis"
  },

  /* ── Catalog & API ───────────────────────────────────────────────────── */
  "docs/catalog-schema.md": {
    title: "Catalog Schema Reference"
  },
  "docs/api-versioning.md": {
    title: "API Versioning"
  },
  "docs/schema-versioning.md": {
    title: "Schema Versioning"
  },
  "docs/url-scheme.md": {
    title: "URL Scheme"
  },
  "docs/source-catalog.md": {
    title: "Source Catalog"
  },

  /* ── CIM & Data Models ───────────────────────────────────────────────── */
  "docs/cim-and-data-models.md": {
    title: "CIM & Data Models",
    ucs: ["1.1.1", "1.1.2", "5.1.1", "9.1.1", "10.1.1"]
  },

  /* ── Compliance & Regulatory ─────────────────────────────────────────── */
  "docs/regulatory-primer.md": {
    title: "Regulatory Primer",
    ucs: ["22.1.1", "22.2.1", "22.3.1", "22.4.1", "22.5.1"]
  },
  "docs/coverage-methodology.md": {
    title: "Coverage Methodology",
    ucs: ["22.1.1"]
  },
  "docs/compliance-coverage.md": {
    title: "Compliance Coverage Map",
    ucs: ["22.1.1", "22.4.1", "22.5.1"]
  },
  "docs/compliance-gaps.md": {
    title: "Compliance Gaps Analysis",
    ucs: ["22.1.1", "22.4.1"]
  },
  "docs/regulatory-change-watch.md": {
    title: "Regulatory Change Watch"
  },
  "docs/legal-review-guide.md": {
    title: "Legal Review Guide"
  },

  /* ── Evidence Packs ──────────────────────────────────────────────────── */
  "docs/evidence-packs/README.md": {
    title: "Evidence Packs Overview",
    ucs: ["22.1.1"]
  },
  "docs/evidence-packs/gdpr.md": {
    title: "Evidence Pack \u2014 GDPR",
    ucs: ["22.1.1", "22.1.2", "22.1.3", "22.1.4", "22.1.5"]
  },
  "docs/evidence-packs/uk-gdpr.md": {
    title: "Evidence Pack \u2014 UK GDPR",
    ucs: ["22.7.1", "22.7.2", "22.7.3"]
  },
  "docs/evidence-packs/pci-dss.md": {
    title: "Evidence Pack \u2014 PCI DSS",
    ucs: ["22.4.1", "22.4.2", "22.4.3", "22.4.4", "22.4.5"]
  },
  "docs/evidence-packs/hipaa-security.md": {
    title: "Evidence Pack \u2014 HIPAA",
    ucs: ["22.5.1", "22.5.2", "22.5.3"]
  },
  "docs/evidence-packs/sox-itgc.md": {
    title: "Evidence Pack \u2014 SOX / ITGC",
    ucs: ["22.6.1", "22.6.2", "22.6.3"]
  },
  "docs/evidence-packs/soc-2.md": {
    title: "Evidence Pack \u2014 SOC 2",
    ucs: ["22.8.1", "22.8.2", "22.8.3"]
  },
  "docs/evidence-packs/iso-27001.md": {
    title: "Evidence Pack \u2014 ISO 27001",
    ucs: ["22.9.1", "22.9.2", "22.9.3"]
  },
  "docs/evidence-packs/nist-csf.md": {
    title: "Evidence Pack \u2014 NIST CSF",
    ucs: ["22.10.1", "22.10.2", "22.10.3"]
  },
  "docs/evidence-packs/nist-800-53.md": {
    title: "Evidence Pack \u2014 NIST 800-53",
    ucs: ["22.11.1", "22.11.2", "22.11.3"]
  },
  "docs/evidence-packs/nis2.md": {
    title: "Evidence Pack \u2014 NIS2",
    ucs: ["22.2.1", "22.2.2", "22.2.3"]
  },
  "docs/evidence-packs/dora.md": {
    title: "Evidence Pack \u2014 DORA",
    ucs: ["22.3.1", "22.3.2", "22.3.3"]
  },
  "docs/evidence-packs/cmmc.md": {
    title: "Evidence Pack \u2014 CMMC",
    ucs: ["22.12.1", "22.12.2", "22.12.3"]
  },

  /* ── Splunk Content Packs ────────────────────────────────────────────── */
  "docs/enterprise-deployment.md": {
    title: "Enterprise Deployment Guide",
    ucs: ["13.1.1", "13.1.2", "13.1.3"]
  },
  "docs/recommender-app.md": {
    title: "Recommender App"
  },
  "docs/splunk-apps-use-cases-comparison.md": {
    title: "Splunk Apps vs Use Cases Comparison"
  },
  "docs/splunk-cloud-compat.md": {
    title: "Splunk Cloud Compatibility"
  },

  /* ── Integration Guides ──────────────────────────────────────────────── */
  "docs/guides/catalyst-center.md": {
    title: "Catalyst Center Integration Guide",
    ucs: ["5.8.1", "5.4.40"]
  },
  "docs/guides/datagen-top10-use-cases.md": {
    title: "Data Generator \u2014 Top 10 Use Cases",
    ucs: ["1.1.1", "1.1.2", "5.1.1", "10.1.1"]
  },

  /* ── Equipment & Data Sources ────────────────────────────────────────── */
  "docs/equipment-table.md": {
    title: "Equipment Table Reference",
    ucs: ["5.1.1", "14.1.1", "14.2.1"]
  },
  "docs/samples-coverage.md": {
    title: "Sample Data Coverage"
  },

  /* ── AI & Automation ─────────────────────────────────────────────────── */
  "AGENTS.md": {
    title: "AI Agent Entrypoint"
  },
  "docs/mcp-server.md": {
    title: "MCP Server Reference"
  },

  /* ── Quality & Governance ────────────────────────────────────────────── */
  "docs/scorecard.md": {
    title: "Quality Scorecard"
  },
  "docs/provenance-coverage.md": {
    title: "Provenance Coverage"
  },
  "docs/signed-provenance.md": {
    title: "Signed Provenance"
  },
  "docs/peer-review-guide.md": {
    title: "Peer Review Guide"
  },
  "docs/sme-review-guide.md": {
    title: "SME Review Guide"
  },

  /* ── Replication ─────────────────────────────────────────────────────── */
  "docs/replication-guide.md": {
    title: "Replication Guide"
  },

  /* ── Auditor Research ────────────────────────────────────────────────── */
  "docs/auditor-research/survey.md": {
    title: "Auditor Survey"
  },
  "docs/auditor-research/interview-guide.md": {
    title: "Auditor Interview Guide"
  },
  "docs/auditor-research/recruitment.md": {
    title: "Auditor Recruitment"
  },
  "docs/auditor-research/findings-template.md": {
    title: "Auditor Findings Template"
  },

  /* ── Migration & Release Reports ─────────────────────────────────────── */
  "docs/migration-build-parity.md": {
    title: "Migration Build Parity"
  },
  "docs/uc-migration-report.md": {
    title: "UC Migration Report"
  },
  "docs/v6.0-release-report.md": {
    title: "v6.0 Release Report"
  },
  "docs/v7.1-release-report.md": {
    title: "v7.1 Release Report"
  },
  "docs/checkpoint-phase0.md": {
    title: "Phase 0 Checkpoint"
  },
  "docs/feasibility-spike-results.md": {
    title: "Feasibility Spike Results"
  }
};

/* ── Reverse index: UC-ID → [{path, title}] ─────────────────────────────
 *  Computed automatically — do NOT edit manually.                         */
var UC_DOC_MAP = {};
Object.keys(DOC_UC_MAP).forEach(function(path) {
  var entry = DOC_UC_MAP[path];
  (entry.ucs || []).forEach(function(ucId) {
    if (!UC_DOC_MAP[ucId]) UC_DOC_MAP[ucId] = [];
    UC_DOC_MAP[ucId].push({ path: path, title: entry.title });
  });
});
