# content/

Source-of-truth for every use case. Replaces the v6
`use-cases/cat-NN-*.md` monolithic markdown files.

```
content/
└── cat-NN-slug/
    ├── _category.json            Category metadata (icon, description, quick-tip)
    ├── UC-X.Y.Z.md               Prose narrative for the use case
    ├── UC-X.Y.Z.json             Structured fields validated against schemas/uc.schema.json
    └── ...
```

Populated by `tools/build/migrate_to_per_uc.py`. The v7 `parse_content`
loader reads from `content/` when per-UC files are present; otherwise it
falls back to the v6 `use-cases/` monolithic markdown files. The
canonical category index is `use-cases/INDEX.md` (not duplicated here).

Why per-UC files? Pull-request diffs become reviewable, per-UC history
is preserved by `git mv`, and parallel authoring stops causing merge
conflicts in 60 K-line monoliths.
