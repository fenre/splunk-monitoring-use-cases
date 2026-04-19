# samples/

Sample event data used to validate use-case SPL. One folder per UC,
optionally accompanied by an expected-results JSON file.

```
samples/
└── UC-X.Y.Z/
    ├── sample.jsonl              one sample event per line
    ├── sample.csv                tabular alternative
    └── expected.json             expected SPL output for regression tests
```

Read by `tools/validate/validate_md.py` (and the v6
`scripts/run_uc_tests.py`). New UCs SHOULD ship at least one sample
fixture; the per-PR template flags missing fixtures for human review.
