# Eventgen / datagen data (POC)

This directory holds **machine-readable manifests** and **redacted sample log lines** for Cribl Stream Datagen and Splunk HEC demos.

| File / directory | Description |
|------------------|-------------|
| [manifest-top10.json](manifest-top10.json) | Ten representative UCs with `log_family`, `sourcetype`, and `sample_template` paths |
| [samples/](samples/) | Per–log-family samples for “Create Datagen File” in Cribl (all synthetic / demo-safe) |
| `manifest-all.json` | **Not committed** by default — run `python3 scripts/parse_uc_catalog.py -o eventgen_data/manifest-all.json` to generate the full catalog (4700+ rows) |

**Guide:** [docs/guides/datagen-top10-use-cases.md](../docs/guides/datagen-top10-use-cases.md)

**Scripts**

- `python3 scripts/generate_manifest_samples.py --manifest eventgen_data/manifest-top10.json -o /tmp/events.ndjson`
- `python3 scripts/parse_uc_catalog.py -o eventgen_data/manifest-all.json`

**Scaling**

- One **manifest row** per use case; **event templates** are shared by **log family** (see [config/uc_to_log_family.json](../config/uc_to_log_family.json)), not a unique format per UC.
