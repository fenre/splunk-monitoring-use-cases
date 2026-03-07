# Importing Splunk Security Essentials (SSE) Use Cases

Splunk Security Essentials and the [Splunk security_content](https://github.com/splunk/security_content) repository contain **1,900+** detection analytics (ESCU). This repo’s **Category 10 — Security Infrastructure** already includes 53 curated use cases (10.1–10.8). The script `import_sse_detections.py` compares ESCU detections to those and generates new use case entries for anything not already covered.

## What’s in cat-10 after import and redistribution

- **10.1** Next-Gen Firewalls  
- **10.2** IDS/IPS  
- **10.3** Endpoint Detection & Response (EDR)  
- **10.4** Email Security  
- **10.5** Web Security / Secure Web Gateway  
- **10.6** Vulnerability Management  
- **10.7** SIEM & SOAR  
- **10.8** Certificate & PKI  

Imported ESCU use cases are **redistributed** into 10.1–10.8 (no separate 10.9). Run `redistribute_sse_ucs.py` after merging new imports to assign each UC to the best subcategory by security domain and keywords.

## How to run the import

### Option A: Local clone of security_content (recommended)

1. Clone the repo (one-time):
   ```bash
   git clone --depth 1 https://github.com/splunk/security_content.git
   ```

2. Install PyYAML if needed:
   ```bash
   pip install pyyaml
   ```

3. Run the script:
   ```bash
   cd /path/to/splunk-monitoring-use-cases/use-cases
   python3 import_sse_detections.py --repo /path/to/security_content
   ```

4. Optional: limit how many new UCs are generated:
   ```bash
   python3 import_sse_detections.py --repo /path/to/security_content --limit 200
   ```

### Option B: Fetch from GitHub (no clone)

The script can fetch the detection list and each YAML from GitHub. Slower and rate-limited; use for a smaller batch:

```bash
cd use-cases
pip install pyyaml
python3 import_sse_detections.py --from-github --limit 100
```

## Output

- **Console:** Counts of “already covered” vs “new UCs to add.”
- **File:** `use-cases/cat-10-sse-import.md` — new UC blocks (10.9.x) in this repo’s markdown format.

## Merging and redistributing into cat-10

After the import script runs:

1. Merge new `### UC-10.9.x · …` blocks from `cat-10-sse-import.md` into `cat-10-security-infrastructure.md` (e.g. into a temporary 10.9 section or append before the next `##`).
2. **Redistribute** so ESCU UCs sit in the right subcategories (10.1–10.8) instead of one big 10.9:
   ```bash
   cd use-cases
   python3 redistribute_sse_ucs.py
   ```
   This classifies each 10.9.x UC by Security domain and title/value and moves it to 10.1 (NGFW), 10.2 (IDS/IPS), 10.3 (EDR), 10.4 (Email), 10.5 (Web), 10.6 (Vuln), 10.7 (SIEM), or 10.8 (PKI), then removes the 10.9 section.
3. Rebuild the dashboard:
   ```bash
   python3 build.py
   ```

## “Already implemented” check

The script considers an ESCU detection **already implemented** if its normalized title matches (or is a substring of) any existing UC title in `cat-10-security-infrastructure.md`. So high-level UCs (e.g. “Threat Prevention Event Trending”) may cause many narrower ESCU detections to be treated as new and still get 10.9.x entries. You can trim or deduplicate after import.

## References

- [Splunk Security Essentials](https://www.splunk.com/en_us/products/cyber-security-essentials.html)
- [security_content on GitHub](https://github.com/splunk/security_content)
- [Splunkbase: Splunk Security Essentials](https://classic.splunkbase.splunk.com/app/3435/)
