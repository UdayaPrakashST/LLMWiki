from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
WIKI_LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")


@dataclass(frozen=True)
class MarkdownDoc:
    path: Path
    title: str
    body: str
    headings: list[str]


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", ascii_text).strip("-").lower()
    return slug or "untitled"


def title_from_text(path: Path, text: str) -> str:
    match = HEADING_RE.search(text)
    if match:
        return clean_title(match.group(2))
    return clean_title(path.stem.replace("_", " ").replace("-", " "))


def clean_title(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().strip("#")).strip()


def strip_frontmatter(text: str) -> str:
    return FRONTMATTER_RE.sub("", text, count=1)


def read_markdown(path: Path) -> MarkdownDoc:
    text = path.read_text(encoding="utf-8-sig")
    body = strip_frontmatter(text)
    headings = [clean_title(match.group(2)) for match in HEADING_RE.finditer(body)]
    return MarkdownDoc(path=path, title=title_from_text(path, body), body=body, headings=headings)


def first_paragraphs(text: str, limit: int = 3) -> list[str]:
    paragraphs: list[str] = []
    for block in re.split(r"\n\s*\n", strip_frontmatter(text)):
        cleaned = " ".join(line.strip() for line in block.splitlines()).strip()
        if not cleaned or cleaned.startswith("#") or cleaned.startswith("```") or cleaned.startswith("Source:"):
            continue
        paragraphs.append(cleaned)
        if len(paragraphs) >= limit:
            break
    return paragraphs


def extract_wiki_links(text: str) -> set[str]:
    return {clean_title(match.group(1)) for match in WIKI_LINK_RE.finditer(text)}


def words(text: str) -> list[str]:
    return [token.lower() for token in WORD_RE.findall(text)]


def frontmatter(title: str, page_type: str, today: str, sources: list[str] | None = None) -> str:
    lines = [
        "---",
        f"title: {yaml_scalar(title)}",
        f"type: {page_type}",
        f"created: {today}",
        f"updated: {today}",
    ]
    if sources:
        lines.append("sources:")
        lines.extend(f"  - {yaml_scalar(source)}" for source in sources)
    lines.extend(["tags: []", "---", ""])
    return "\n".join(lines)


def yaml_scalar(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'
