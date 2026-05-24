from __future__ import annotations

import math
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .config import WikiPaths
from .markdown import (
    extract_wiki_links,
    first_paragraphs,
    frontmatter,
    read_markdown,
    slugify,
    words,
)


INIT_INDEX = """# Index

Content-oriented catalog for the wiki.

## Sources

No sources ingested yet.

## Concepts

No concept pages yet.

## Entities

No entity pages yet.

## Answers

No filed answers yet.
"""

INIT_LOG = """# Log

Append-only record of wiki operations.
"""


@dataclass(frozen=True)
class SearchHit:
    path: Path
    title: str
    score: float
    excerpt: str


@dataclass(frozen=True)
class LintIssue:
    severity: str
    path: Path
    message: str


def init_wiki(paths: WikiPaths) -> list[Path]:
    created: list[Path] = []
    for directory in [paths.raw, paths.assets, paths.wiki, paths.sources, paths.concepts, paths.entities, paths.answers]:
        directory.mkdir(parents=True, exist_ok=True)
        created.append(directory)
    if not paths.index.exists():
        paths.index.write_text(INIT_INDEX, encoding="utf-8")
        created.append(paths.index)
    if not paths.log.exists():
        paths.log.write_text(INIT_LOG, encoding="utf-8")
        created.append(paths.log)
    return created


def ingest_source(paths: WikiPaths, source: Path, copy_into_raw: bool = False) -> Path:
    init_wiki(paths)
    source = source.resolve()
    if copy_into_raw and not _is_relative_to(source, paths.raw):
        target = paths.raw / source.name
        shutil.copy2(source, target)
        source = target.resolve()
    if not _is_relative_to(source, paths.raw):
        raise ValueError(f"Source must be inside {paths.raw} or use --copy: {source}")
    doc = read_markdown(source)
    today = date.today().isoformat()
    rel_source = source.relative_to(paths.root).as_posix()
    page = paths.sources / f"{slugify(doc.title)}.md"
    summary = build_source_page(doc.title, doc.body, rel_source, today)
    page.write_text(summary, encoding="utf-8")
    update_index(paths)
    append_log(paths, "ingest", doc.title, f"- Source: `{rel_source}`\n- Wiki page: `wiki/sources/{page.name}`")
    return page


def build_source_page(title: str, body: str, rel_source: str, today: str) -> str:
    paragraphs = first_paragraphs(body, limit=4)
    key_points = paragraphs or ["No prose paragraphs were found. Review the source manually."]
    excerpt = "\n".join(f"- {point}" for point in key_points)
    return (
        frontmatter(title, "source", today, [rel_source])
        + f"# {title}\n\n"
        + f"Source: `{rel_source}`\n\n"
        + "## Summary\n\n"
        + "\n".join(key_points[:2])
        + "\n\n## Key Points\n\n"
        + excerpt
        + "\n\n## Connections\n\n"
        + "- Add related concept and entity links as the wiki develops.\n\n"
        + "## Open Questions\n\n"
        + "- What should this source change about the existing synthesis?\n"
    )


def search_wiki(paths: WikiPaths, query: str, limit: int = 8) -> list[SearchHit]:
    pages = [page for page in wiki_pages(paths) if page.name not in {"index.md", "log.md"}]
    if not pages:
        return []
    query_terms = Counter(words(query))
    if not query_terms:
        return []
    doc_terms: dict[Path, Counter[str]] = {}
    doc_freq: Counter[str] = Counter()
    titles: dict[Path, str] = {}
    bodies: dict[Path, str] = {}
    for page in pages:
        doc = read_markdown(page)
        titles[page] = doc.title
        bodies[page] = doc.body
        counts = Counter(words(doc.body))
        doc_terms[page] = counts
        for term in counts:
            doc_freq[term] += 1
    results: list[SearchHit] = []
    total_docs = len(pages)
    for page, counts in doc_terms.items():
        score = 0.0
        for term, q_count in query_terms.items():
            if term not in counts:
                continue
            idf = math.log((1 + total_docs) / (1 + doc_freq[term])) + 1
            title_boost = 2.0 if term in words(titles[page]) else 1.0
            score += q_count * counts[term] * idf * title_boost
        if score > 0:
            results.append(SearchHit(page, titles[page], score, best_excerpt(bodies[page], query_terms)))
    return sorted(results, key=lambda hit: hit.score, reverse=True)[:limit]


def query_packet(paths: WikiPaths, question: str, limit: int = 6) -> str:
    hits = search_wiki(paths, question, limit=limit)
    lines = [f"# Query Packet", "", f"Question: {question}", ""]
    if not hits:
        lines.append("No relevant wiki pages found.")
        return "\n".join(lines) + "\n"
    lines.append("## Relevant Pages")
    lines.append("")
    for hit in hits:
        rel = hit.path.relative_to(paths.root).as_posix()
        lines.append(f"### {hit.title}")
        lines.append("")
        lines.append(f"- Path: `{rel}`")
        lines.append(f"- Score: {hit.score:.2f}")
        lines.append(f"- Excerpt: {hit.excerpt}")
        lines.append("")
    lines.append("## Synthesis Notes")
    lines.append("")
    lines.append("- Use the relevant pages above to draft a cited answer.")
    lines.append("- If the answer is reusable, save it under `wiki/answers/` and update the index/log.")
    return "\n".join(lines) + "\n"


def save_answer_packet(paths: WikiPaths, question: str, packet: str) -> Path:
    init_wiki(paths)
    today = date.today().isoformat()
    title = question.rstrip("?!.")
    path = paths.answers / f"{slugify(title)}.md"
    content = frontmatter(title, "answer", today) + packet
    path.write_text(content, encoding="utf-8")
    update_index(paths)
    append_log(paths, "query", title, f"- Filed answer packet: `wiki/answers/{path.name}`")
    return path


def lint_wiki(paths: WikiPaths) -> list[LintIssue]:
    issues: list[LintIssue] = []
    pages = wiki_pages(paths)
    title_to_page = {read_markdown(page).title: page for page in pages}
    inbound: defaultdict[Path, int] = defaultdict(int)
    for page in pages:
        text = page.read_text(encoding="utf-8")
        if not text.startswith("---\n") and page.name not in {"index.md", "log.md"}:
            issues.append(LintIssue("warning", page, "Generated page is missing YAML frontmatter."))
        for link in extract_wiki_links(text):
            target = title_to_page.get(link)
            if target:
                inbound[target] += 1
            else:
                issues.append(LintIssue("error", page, f"Broken wiki link: [[{link}]]"))
    for page in pages:
        if page.name in {"index.md", "log.md"}:
            continue
        if inbound[page] == 0:
            issues.append(LintIssue("info", page, "Page has no inbound wiki links."))
    if paths.index.exists() and "## Sources" not in paths.index.read_text(encoding="utf-8"):
        issues.append(LintIssue("error", paths.index, "Index is missing the Sources section."))
    if paths.log.exists() and "# Log" not in paths.log.read_text(encoding="utf-8"):
        issues.append(LintIssue("error", paths.log, "Log does not look like the wiki log."))
    return issues


def update_index(paths: WikiPaths) -> None:
    init_wiki(paths)
    sections = [
        ("Sources", paths.sources),
        ("Concepts", paths.concepts),
        ("Entities", paths.entities),
        ("Answers", paths.answers),
    ]
    lines = ["# Index", "", "Content-oriented catalog for the wiki.", ""]
    for heading, directory in sections:
        lines.extend([f"## {heading}", ""])
        pages = sorted(directory.glob("*.md"))
        if not pages:
            lines.extend([f"No {heading.lower()} yet.", ""])
            continue
        for page in pages:
            doc = read_markdown(page)
            rel = page.relative_to(paths.wiki).as_posix()
            summary = first_paragraphs(doc.body, 1)
            description = summary[0] if summary else "No summary yet."
            lines.append(f"- [[{doc.title}]] (`{rel}`) - {description}")
        lines.append("")
    paths.index.write_text("\n".join(lines), encoding="utf-8")


def append_log(paths: WikiPaths, kind: str, title: str, body: str) -> None:
    init_wiki(paths)
    today = date.today().isoformat()
    entry = f"\n## [{today}] {kind} | {title}\n\n{body.strip()}\n"
    with paths.log.open("a", encoding="utf-8") as handle:
        handle.write(entry)


def wiki_pages(paths: WikiPaths) -> list[Path]:
    if not paths.wiki.exists():
        return []
    return sorted(path for path in paths.wiki.rglob("*.md") if path.is_file())


def best_excerpt(text: str, query_terms: Counter[str], max_chars: int = 260) -> str:
    paragraphs = first_paragraphs(text, limit=20)
    if not paragraphs:
        return ""
    ranked = sorted(
        paragraphs,
        key=lambda paragraph: sum(Counter(words(paragraph)).get(term, 0) for term in query_terms),
        reverse=True,
    )
    excerpt = ranked[0]
    if len(excerpt) <= max_chars:
        return excerpt
    return excerpt[: max_chars - 3].rstrip() + "..."


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False
