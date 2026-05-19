.PHONY: build serve clean clean-tree audit audit-full audit-ntv audit-all audit-structure \
       audit-cim audit-links audit-consistency audit-perf audit-placeholders \
       audit-mitre audit-gold audit-spl-duplicates audit-spl-grammar audit-ids \
       audit-spl-hallucinations audit-spl-references audit-spl-references-build \
       audit-splunk-cloud-compat audit-splunk-version-matrix \
       audit-monitoring-type audit-roadmap export-roadmap audit-license-inventory \
       write-license-inventory audit-metrics-snapshot snapshot-metrics \
       audit-regulation-alignment audit-nis2-no-gap audit-oscal \
       audit-regulatory-change-watch \
       audit-compliance-gaps audit-compliance-mappings \
       audit-doc-counts audit-openapi-drift audit-content-quality \
       audit-baseline-clause-grammar-free audit-peer-review-signoffs \
       audit-mcp-tool-schemas \
       stewardship-digest audit-reproducibility audit-reproducibility-fast \
       baseline devcontainer-init \
       generate-grandma-explanations \
       generate-stewardship-digest generate-mapping-ledger \
       generate-manifest-samples generate-equipment-tags \
       generate-evidence-packs generate-api-surface \
       generate-rag-chunks audit-rag-chunks \
       generate-alert-actions audit-alert-actions \
       audit-retrieval-eval audit-retrieval-eval-check \
       generate-phase2-mini-categories generate-phase2-3-per-regulation \
       generate-phase3-1-backfill generate-phase3-2-cross-cutting \
       generate-phase3-3-derivatives \
       generate-backlinks generate-doc-references \
       sync-generated sync-generated-check \
       check-source-links audit-auto-gen-provenance \
       splunk-uc splunk-uc-help \
       inventory manifest test test-unit help worktree-new

PYTHON ?= python3
BUILD  := $(PYTHON) tools/build/build.py --out dist
DIST   := dist

# P6 (scripts taxonomy, 2026-05-09): the dispatcher lives under
# src/splunk_uc/. Until the package is editable-installed, we put
# src/ on PYTHONPATH on demand. Both ``python3 -m splunk_uc <verb>``
# and the legacy ``python3 scripts/<name>.py`` shims work; this
# variable is the canonical way Makefile targets reach the new CLI.
SPLUNK_UC := PYTHONPATH=src $(PYTHON) -m splunk_uc

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build the full site into dist/
	$(BUILD)

serve: build ## Build then serve locally on port 8000
	cd $(DIST) && $(PYTHON) -m http.server 8000

clean: ## Remove dist/ and build artefacts
	rm -rf $(DIST)

clean-tree: ## Remove every gitignored build-output directory (dist/, dist1/, dist2/, dist-content/, dist-legacy/, dist-before/, .build-tmp/)
	# Resolves loose-end ledger item #3 in docs/health-check-2026-progress.md.
	# Every directory below is matched by an explicit .gitignore entry
	# (lines 26-36 of .gitignore at HEAD) so this target only ever
	# touches local-only build output, never anything tracked in git.
	rm -rf dist dist1 dist2 dist-content dist-legacy dist-before .build-tmp

# --- Audits (quick) ---

audit: audit-structure audit-cim audit-consistency ## Run core audit checks

# --- Audits (comprehensive) ---

audit-full: audit audit-placeholders audit-mitre audit-spl-duplicates audit-spl-grammar audit-ids audit-monitoring-type ## Run ALL audit checks

audit-structure: ## Audit UC JSON structure (content/cat-*/UC-*.json)
	$(SPLUNK_UC) audit-uc-structure --full

audit-cim: ## Audit CIM ↔ SPL alignment
	$(SPLUNK_UC) audit-cim-spl-alignment

audit-links: ## Check HTTP(S) URLs in UC references (network required)
	$(SPLUNK_UC) audit-links

audit-consistency: ## Audit repo consistency (enrichment, INDEX, HTML)
	$(SPLUNK_UC) audit-repo-consistency

audit-perf: ## Performance + accessibility budget check
	$(SPLUNK_UC) audit-perf-a11y

audit-placeholders: ## Detect placeholder/scaffolded content
	$(SPLUNK_UC) audit-placeholders

audit-mitre: ## Validate MITRE ATT&CK taxonomy
	$(SPLUNK_UC) audit-mitre-taxonomy

audit-gold: ## Gold standard quality profile audit
	$(SPLUNK_UC) audit-gold-profile

audit-ntv:
	$(SPLUNK_UC) audit-non-technical-sync

audit-all: audit audit-ntv audit-gold
	@echo "All audit checks passed"

audit-spl-duplicates: ## Find duplicate SPL queries across UCs
	$(SPLUNK_UC) audit-spl-duplicates

audit-spl-grammar: ## Check SPL grammar issues
	$(SPLUNK_UC) audit-spl-grammar

audit-spl-hallucinations: ## Detect SPL hallucinations (unknown commands, bad CIM datasets)
	$(SPLUNK_UC) audit-spl-hallucinations

audit-spl-references: ## Validate SPL identifiers against curated vocabulary (HIGH gate)
	$(SPLUNK_UC) audit-spl-references --check

audit-spl-references-build: ## Rebuild data/spl-reference.local.json from external/ corpora
	$(PYTHON) -m tools.research.build_spl_reference

audit-splunk-cloud-compat: ## Audit SPL + content packs for Splunk Cloud compatibility
	$(SPLUNK_UC) audit-splunk-cloud-compat

audit-splunk-version-matrix: ## Audit the 2-D Splunk-version compatibility matrix
	$(SPLUNK_UC) audit-splunk-version-matrix --check

generate-backlinks: ## Refresh docs/backlinks.md (wiki "What links here" index)
	$(PYTHON) scripts/generate_backlinks.py

generate-doc-references: ## Refresh APA-style References footer + inline `[N]` markers on every doc
	$(PYTHON) scripts/generate_doc_references.py

check-source-links: ## HTTP-probe every URL in the bibliographic database (network required)
	$(PYTHON) scripts/check_source_links.py

audit-auto-gen-provenance: ## Verify every auto-generated doc carries a 'Generated by ...' banner
	$(PYTHON) scripts/audit_auto_gen_provenance.py --check

audit-ids: ## Validate UC IDs (duplicates, ordering, category match)
	$(SPLUNK_UC) audit-uc-ids

audit-monitoring-type: ## Validate monitoringType values and MITRE consistency
	$(SPLUNK_UC) audit-monitoring-type

audit-regulation-alignment: ## Lint compliance[].regulation against data/regulations.json
	$(SPLUNK_UC) audit-regulation-alignment

audit-nis2-no-gap: ## Validate the NIS2 no-gap obligation matrix and per-UC traceability
	$(SPLUNK_UC) audit-nis2-no-gap

audit-oscal: ## NIST OSCAL component-definition schema + canonical-byte gate
	$(SPLUNK_UC) audit-oscal-roundtrip --check

audit-regulatory-change-watch: ## Hermetic regulatory change-watch ledger audit (no network)
	$(SPLUNK_UC) audit-regulatory-change-watch --check

audit-compliance-gaps: ## Per-regulation clause-level gap analysis (--check ensures no drift)
	$(SPLUNK_UC) audit-compliance-gaps --check

audit-compliance-mappings: ## Validate compliance[] mappings + golden tuple gate + coverage metrics
	$(SPLUNK_UC) audit-compliance-mappings

audit-doc-counts: ## Cross-check numeric claims (UC counts) in AGENTS.md and docs/ vs actual content
	$(SPLUNK_UC) audit-doc-counts

audit-openapi-drift: ## Flag dist/api/ paths missing from openapi.yaml / api/v1/openapi.yaml
	$(SPLUNK_UC) audit-openapi-drift

audit-content-quality: ## Flag description==value, jargon in grandmaExplanation, broken fixtureRefs
	$(SPLUNK_UC) audit-content-quality

audit-baseline-clause-grammar-free: ## Refuse `clause-grammar` fingerprints in audit-baseline.json
	$(SPLUNK_UC) audit-baseline-clause-grammar-free

audit-peer-review-signoffs: ## Phase 4.5a peer-review gate (schema + semantic invariants)
	$(SPLUNK_UC) audit-peer-review-signoffs

audit-mcp-tool-schemas: ## Drift guard: MCP tool surface vs api/v1/* + outputSchema runtime probes
	$(SPLUNK_UC) audit-mcp-tool-schemas

audit-gold-profile-v2: ## Gold-standard v2 audit (SPL provenance, KFP, suppressions)
	$(SPLUNK_UC) audit-gold-profile-v2

audit-prerequisites: ## Validate UC prerequisite graph (cycles, unknown IDs, wave monotonicity)
	$(SPLUNK_UC) audit-prerequisites --check

audit-sandbox-validation: ## Audit sample-data/ fixture coverage and shape vs UC controlTest blocks
	$(SPLUNK_UC) audit-sandbox-validation --check

audit-sme-review-signoffs: ## Validate data/provenance/sme-signoffs.json (schema + cross-references)
	$(SPLUNK_UC) audit-sme-review-signoffs

audit-mapping-ledger: ## Validate data/provenance/mapping-ledger.json (schema + hash chain + integrity)
	$(SPLUNK_UC) audit-mapping-ledger

audit-roadmap: ## Validate ROADMAP.md structure + repo-relative links
	$(SPLUNK_UC) audit-roadmap-consistency --check

export-roadmap: ## Emit a Project-board JSON snapshot of ROADMAP.md
	$(SPLUNK_UC) audit-roadmap-consistency --export reports/roadmap-export.json

audit-license-inventory: ## Validate dependency licenses against allowlist
	$(SPLUNK_UC) audit-license-inventory --check

write-license-inventory: ## Regenerate data/license-inventory.json baseline
	$(SPLUNK_UC) audit-license-inventory --write

audit-metrics-snapshot: ## Ensure release-time metrics snapshot exists
	$(PYTHON) scripts/snapshot_metrics.py --check

snapshot-metrics: ## Write data/metrics-history/<VERSION>.json from dist/metrics.json
	$(PYTHON) scripts/snapshot_metrics.py --write

baseline: ## Capture data/baselines/v<VERSION>.json (size/timing snapshot)
	$(PYTHON) tools/capture_baselines.py

devcontainer-init: ## Bootstrap a fresh devcontainer (called by .devcontainer/devcontainer.json postCreateCommand)
	# Repo-overhaul plan §P11 (2026-05-13): single source of truth for
	# devcontainer bootstrap logic. .devcontainer/devcontainer.json hands
	# off to this target so the install sequence has one home, not two.
	# Idempotent: safe to re-run on `Rebuild Container` or on a host
	# checkout when a contributor wants the same setup outside a
	# container.
	@echo "→ [1/3] Installing splunk-uc (editable) with [audits,dev,test] extras…"
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[audits,dev,test]"
	@echo "→ [2/3] Registering pre-commit git hooks (pre-commit already in [dev])…"
	pre-commit install --install-hooks
	@echo "→ [3/3] Warm-building dist/ so 'make serve' works immediately…"
	$(BUILD)
	@echo ""
	@echo "✓ Devcontainer ready."
	@echo "  Try:  make serve   # then open http://localhost:8000"
	@echo "  Or:   make audit   # core audits (~30s)"
	@echo "  Or:   make help    # list every target"

stewardship-digest: ## Generate dist/stewardship-digest.{json,md}
	$(SPLUNK_UC) generate-stewardship-digest

generate-grandma-explanations: ## Fill missing plain-language `grandmaExplanation` fields
	$(SPLUNK_UC) generate-grandma-explanations

generate-stewardship-digest: ## Alias for stewardship-digest (dispatcher verb name)
	$(SPLUNK_UC) generate-stewardship-digest

generate-rag-chunks: ## Build the RAG-ready chunked corpus under dist/rag/ (P17)
	$(SPLUNK_UC) generate-rag-chunks

audit-rag-chunks: ## Drift-guard dist/rag/manifest.json against a fresh chunk rebuild (P17)
	$(SPLUNK_UC) generate-rag-chunks --check

generate-alert-actions: ## Emit per-UC SOAR + email alert action templates (Task H-4)
	$(SPLUNK_UC) generate-alert-actions

audit-alert-actions: ## Drift-guard alert-action golden fixtures (Task H-4)
	$(SPLUNK_UC) generate-alert-actions --check --limit 20

audit-retrieval-eval: ## Run curated query set + BM25 baseline on dist/rag/ (P17)
	$(SPLUNK_UC) audit-retrieval-eval

audit-retrieval-eval-check: ## Drift-guard retrieval-eval against baseline (P17 CI gate)
	$(SPLUNK_UC) audit-retrieval-eval --check

generate-mapping-ledger: ## Regenerate data/provenance/mapping-ledger.json
	$(SPLUNK_UC) generate-mapping-ledger

generate-manifest-samples: ## Replay samples/manifest.json fixtures through HEC
	$(SPLUNK_UC) generate-manifest-samples

generate-equipment-tags: ## Backfill UC sidecar equipment[]/equipmentModels[] tags
	$(SPLUNK_UC) generate-equipment-tags

generate-evidence-packs: ## Build per-regulation evidence packs
	$(SPLUNK_UC) generate-evidence-packs

generate-api-surface: ## Regenerate api/v1/* static JSON surface
	$(SPLUNK_UC) generate-api-surface

generate-phase2-mini-categories: ## Phase 2.2 generator (cat-22.35-22.49 mini-category UCs)
	$(SPLUNK_UC) generate-phase2-mini-categories

generate-phase2-3-per-regulation: ## Phase 2.3 generator (per-regulation content fills)
	$(SPLUNK_UC) generate-phase2-3-per-regulation

generate-phase3-1-backfill: ## Phase 3.1 generator (clause-level backfill on cat-22)
	$(SPLUNK_UC) generate-phase3-1-backfill

generate-phase3-2-cross-cutting: ## Phase 3.2 generator (cross-cutting compliance tags)
	$(SPLUNK_UC) generate-phase3-2-cross-cutting

generate-phase3-3-derivatives: ## Phase 3.3 generator (derivative-regulation propagation)
	$(SPLUNK_UC) generate-phase3-3-derivatives

# --- Sync-generated umbrella (PR-2 lean-mode) ---
#
# Lean-mode PR-2 collapses 14 cascade-style per-generator `--check`
# gates in `.github/workflows/validate.yml` into one umbrella drift
# gate. `make sync-generated` runs every cascade generator in
# dependency-safe order; `make sync-generated-check` runs the same
# set with `--check` flags (no writes, exits non-zero on any drift).
#
# CI calls `make sync-generated-check`. Local "fix all drift in one
# shot" recovery is `make sync-generated && git add -A && git diff
# --staged`.
#
# Order matters: sidecar mutators first, derived reports next, doc
# footers last. Re-shuffling without thinking about read/write
# dependencies will break the chain. The generators themselves are
# idempotent — a second run is a no-op.
#
# Excluded from the umbrella on purpose:
#   - `generate-api-surface --check` lives in audits-build because
#     it depends on a fresh `make build`.
#   - Pure structural / schema audits (`audit-mitre-taxonomy`,
#     `audit-known-fp`, `audit-regulatory-change-watch`, etc.) keep
#     their own CI steps because their failure messages carry
#     useful per-domain context.
sync-generated: ## Run every cascade-style generator (write-mode) in dependency-safe order
	@echo "==> [1/13] sidecar mutator: phase3-1 backfill"
	@$(SPLUNK_UC) generate-phase3-1-backfill
	@echo "==> [2/13] sidecar mutator: phase3-2 cross-cutting"
	@$(SPLUNK_UC) generate-phase3-2-cross-cutting
	@echo "==> [3/13] sidecar mutator: phase3-3 derivatives"
	@$(SPLUNK_UC) generate-phase3-3-derivatives
	@echo "==> [4/13] sidecar mutator: equipment-tags"
	@$(SPLUNK_UC) generate-equipment-tags
	@echo "==> [5/13] sidecar mutator: grandma-explanations"
	@$(SPLUNK_UC) generate-grandma-explanations
	@echo "==> [6/13] derived report: cat-22 non-technical-view block"
	@$(SPLUNK_UC) migrate-cat22-ntv
	@echo "==> [7/13] derived report: prerequisites graph"
	@$(SPLUNK_UC) audit-prerequisites
	@echo "==> [8/13] derived report: compliance gaps"
	@$(SPLUNK_UC) audit-compliance-gaps
	@echo "==> [9/13] derived report: sandbox validation"
	@$(SPLUNK_UC) audit-sandbox-validation
	@echo "==> [10/13] derived report: evidence packs"
	@$(SPLUNK_UC) generate-evidence-packs
	@echo "==> [11/13] derived report: mapping ledger"
	@$(SPLUNK_UC) generate-mapping-ledger
	@echo "==> [12/13] doc footer: backlinks index"
	@$(PYTHON) scripts/generate_backlinks.py
	@echo "==> [13/13] doc footer: APA references + inline citations"
	@$(PYTHON) scripts/generate_doc_references.py
	@echo "==> sync-generated: done"

sync-generated-check: ## CI drift gate — run every cascade generator with --check (exits non-zero on drift)
	@set -e; \
	failed=0; \
	for step in \
	  "generate-phase3-1-backfill --check" \
	  "generate-phase3-2-cross-cutting --check" \
	  "generate-phase3-3-derivatives --check" \
	  "generate-equipment-tags --check" \
	  "generate-grandma-explanations --check" \
	  "migrate-cat22-ntv --check" \
	  "audit-prerequisites --check" \
	  "audit-compliance-gaps --check" \
	  "audit-sandbox-validation --check" \
	  "generate-evidence-packs --check" \
	  "generate-mapping-ledger --check"; do \
	  echo "==> $$step"; \
	  $(SPLUNK_UC) $$step || { failed=1; echo "    DRIFT in: $$step"; }; \
	done; \
	echo "==> generate-backlinks --check"; \
	$(PYTHON) scripts/generate_backlinks.py --check || { failed=1; echo "    DRIFT in: generate-backlinks"; }; \
	echo "==> generate-doc-references --check"; \
	$(PYTHON) scripts/generate_doc_references.py --check || { failed=1; echo "    DRIFT in: generate-doc-references"; }; \
	if [ $$failed -ne 0 ]; then \
	  echo ""; \
	  echo "FAIL: one or more sync-generated --check gates detected drift."; \
	  echo "      Fix: run \`make sync-generated\` locally, then commit the diff."; \
	  exit 1; \
	fi; \
	echo "==> sync-generated-check: clean"

audit-reproducibility: ## Two consecutive --reproducible builds must match (~90s)
	$(SPLUNK_UC) audit-reproducibility

audit-reproducibility-fast: ## Single --reproducible build smoke (~30s)
	$(SPLUNK_UC) audit-reproducibility --first-build-only

# --- splunk_uc dispatcher (P6) ---

splunk-uc: ## Show the splunk_uc CLI help (alias for `splunk-uc-help`)
	@$(SPLUNK_UC) --help

splunk-uc-help: ## Show the splunk_uc CLI help
	@$(SPLUNK_UC) --help

# --- Data generation ---

inventory: ## Regenerate data/inventory/ucs.json + ucs.csv
	$(SPLUNK_UC) inventory-ucs --stats

manifest: ## Regenerate eventgen_data/manifest-all.json
	$(PYTHON) scripts/parse_uc_catalog.py --check --output eventgen_data/manifest-all.json

# --- Tests ---

test: test-unit build ## Run unit tests + build validation
	@echo "Build succeeded — $(DIST)/ is up to date."
	@test -f $(DIST)/api/catalog-index.json || (echo "FAIL: catalog-index.json missing" && exit 1)
	@echo "All checks passed."

test-unit: ## Run pytest unit tests for tools/build
	$(PYTHON) -m pytest tests/build/ -v

# --- Parallel execution (Lane O substrate) ---

worktree-new: ## Create isolated worktree .worktrees/$(TASK) on branch worktree/$(TASK)
ifndef TASK
	$(error TASK is required — e.g. make worktree-new TASK=A-mcp-http-transport)
endif
	@mkdir -p .worktrees
	@if [ -d ".worktrees/$(TASK)" ]; then \
		echo "Worktree .worktrees/$(TASK) already exists"; exit 1; \
	fi
	@if git show-ref --verify --quiet "refs/heads/worktree/$(TASK)"; then \
		echo "Branch worktree/$(TASK) already exists — pick a different TASK slug"; exit 1; \
	fi
	git worktree add -b "worktree/$(TASK)" ".worktrees/$(TASK)"
	@echo "→ Bootstrapping .worktrees/$(TASK)…"
	@$(MAKE) -C ".worktrees/$(TASK)" help >/dev/null
	@echo "✓ Worktree ready at .worktrees/$(TASK) (branch worktree/$(TASK))"
	@echo "  Catalogue parallel tasks use branch <lane>/<slug> — see docs/parallel-execution-substrate.md"
	@echo "  Full dev setup: cd .worktrees/$(TASK) && make devcontainer-init"
