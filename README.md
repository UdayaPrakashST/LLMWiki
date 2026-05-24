# LLM Wiki

A Python implementation of the LLM Wiki pattern: raw sources stay immutable, while a generated markdown wiki compounds over time through ingest, query, and lint workflows.

This project is intentionally simple. It gives an LLM agent a disciplined filesystem and CLI to operate on, without requiring a database, vector store, or web server.

## Install

```powershell
python -m pip install -e .
```

## Quick Start

```powershell
llmwiki init
llmwiki ingest raw/example.md
llmwiki search "my topic"
llmwiki query "What should I remember about this?"
llmwiki lint
```

## Directory Layout

```text
raw/              Immutable source files you add
raw/assets/       Optional local images and attachments
wiki/             LLM-maintained markdown wiki
wiki/sources/     One page per ingested source
wiki/concepts/    Topic and concept pages
wiki/entities/    People, projects, places, organizations
wiki/answers/     Filed answers from useful queries
wiki/index.md     Content-oriented catalog
wiki/log.md       Append-only chronological activity log
AGENTS.md         Operating schema for Codex and other LLM agents
```

## What the CLI Does

- `init` creates the wiki structure and schema files.
- `ingest` reads a markdown or text source, creates a source page, updates the index, and appends the log.
- `search` ranks wiki pages with a small local lexical scorer.
- `query` returns relevant pages and excerpts that an LLM can synthesize from; use `--save` to file the answer packet.
- `lint` checks broken wiki links, missing frontmatter, orphan pages, and log/index consistency.

The current implementation uses deterministic local heuristics. It is designed to be driven by an LLM agent, which can read the generated packets and then make richer cross-page edits.

## Philosophy

The raw source layer is your source of truth. The wiki layer is compiled knowledge. The schema tells the LLM how to maintain that compiled layer consistently.
