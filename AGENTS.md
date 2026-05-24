# LLM Wiki Agent Schema

This repository is an LLM-maintained personal knowledge base.

## Layers

- `raw/`: immutable source documents. Read from this directory; do not modify source content.
- `raw/assets/`: optional local images and attachments referenced by sources.
- `wiki/`: generated markdown wiki. The LLM owns this layer and may create or update pages.
- `wiki/index.md`: content catalog. Keep it current after every ingest or major wiki edit.
- `wiki/log.md`: append-only activity log. Add one dated entry per ingest, query filing, or lint pass.

## Page Conventions

Use YAML frontmatter on generated wiki pages:

```yaml
---
title: Page Title
type: source | concept | entity | answer | overview
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources:
  - raw/example.md
tags:
  - example
---
```

Use Obsidian-style links for wiki cross-references: `[[Page Title]]`.

## Ingest Workflow

1. Confirm the source lives under `raw/`.
2. Read the source and identify title, author/date when available, key claims, entities, concepts, open questions, and contradictions.
3. Create or update a page under `wiki/sources/`.
4. Update related `wiki/entities/` and `wiki/concepts/` pages when the source changes the synthesized understanding.
5. Update `wiki/index.md`.
6. Append a `wiki/log.md` entry with the prefix `## [YYYY-MM-DD] ingest | Source Title`.

## Query Workflow

1. Read `wiki/index.md` first.
2. Search or inspect the most relevant pages.
3. Answer with citations to wiki pages and, where useful, raw source paths.
4. If the answer is reusable, file it under `wiki/answers/`, update `index.md`, and append a log entry.

## Lint Workflow

Check for:

- broken `[[wiki links]]`
- orphan generated pages with no inbound wiki links
- important concepts mentioned repeatedly but lacking pages
- stale claims contradicted by newer pages
- generated pages missing frontmatter
- sources that exist in `raw/` but do not have source pages

## Human Role

The human curates sources, asks questions, and decides what matters. The LLM handles summarizing, cross-referencing, filing, and maintenance.
