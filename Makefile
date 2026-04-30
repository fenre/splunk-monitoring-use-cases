.PHONY: build serve clean audit audit-structure audit-cim audit-links audit-consistency audit-perf inventory manifest test help

PYTHON ?= python3
BUILD  := $(PYTHON) tools/build/build.py --out dist
DIST   := dist

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build the full site into dist/
	$(BUILD)

serve: build ## Build then serve locally on port 8000
	cd $(DIST) && $(PYTHON) -m http.server 8000

clean: ## Remove dist/ and build artefacts
	rm -rf $(DIST)

# --- Audits ---

audit: audit-structure audit-cim audit-consistency ## Run all audit checks

audit-structure: ## Audit UC JSON structure (content/cat-*/UC-*.json)
	$(PYTHON) scripts/audit_uc_structure.py --full

audit-cim: ## Audit CIM ↔ SPL alignment
	$(PYTHON) scripts/audit_cim_spl_alignment.py

audit-links: ## Check HTTP(S) URLs in UC references (network required)
	$(PYTHON) scripts/audit_links.py

audit-consistency: ## Audit repo consistency (enrichment, INDEX, HTML)
	$(PYTHON) scripts/audit_repo_consistency.py

audit-perf: ## Performance + accessibility budget check
	$(PYTHON) scripts/audit_perf_a11y.py

# --- Data generation ---

inventory: ## Regenerate data/inventory/ucs.json + ucs.csv
	$(PYTHON) scripts/inventory_ucs.py --stats

manifest: ## Regenerate eventgen_data/manifest-all.json
	$(PYTHON) scripts/parse_uc_catalog.py --check --output eventgen_data/manifest-all.json

# --- Tests ---

test: test-unit build ## Run unit tests + build validation
	@echo "Build succeeded — $(DIST)/ is up to date."
	@test -f $(DIST)/api/catalog-index.json || (echo "FAIL: catalog-index.json missing" && exit 1)
	@echo "All checks passed."

test-unit: ## Run pytest unit tests for tools/build
	$(PYTHON) -m pytest tests/build/ -v
