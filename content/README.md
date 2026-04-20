# content/

Source-of-truth for every use case. Replaces the v6
`use-cases/cat-NN-*.md` monolithic markdown files.

```
content/
├── INDEX.md                      Top-level table of contents (mirrors current INDEX.md)
└── cat-NN-slug/
    ├── _category.json            Category metadata (icon, description, quick-tip)
    ├── UC-X.Y.Z.md               Prose narrative for the use case
    ├── UC-X.Y.Z.json             Structured fields validated against schemas/uc.schema.json
    └── ...
```

Populated by `tools/build/migrate_to_per_uc.py` (see the
`migrate-to-per-uc-files` todo). Until that runs, the `parse_content`
loader continues to read from the v6 `use-cases/` directory; this folder
is the destination layout, not the live source.

Why per-UC files? Pull-request diffs become reviewable, per-UC history
is preserved by `git mv`, and parallel authoring stops causing merge
conflicts in 60 K-line monoliths.
