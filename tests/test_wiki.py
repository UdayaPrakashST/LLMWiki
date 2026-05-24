from pathlib import Path

from llmwiki.config import WikiPaths
from llmwiki.wiki import ingest_source, init_wiki, lint_wiki, query_packet, search_wiki


def test_init_creates_core_files(tmp_path: Path) -> None:
    paths = WikiPaths.from_root(tmp_path)
    init_wiki(paths)
    assert paths.raw.exists()
    assert paths.sources.exists()
    assert paths.index.exists()
    assert paths.log.exists()


def test_ingest_creates_source_page_and_searches(tmp_path: Path) -> None:
    paths = WikiPaths.from_root(tmp_path)
    init_wiki(paths)
    source = paths.raw / "memex.md"
    source.write_text("# Memex\n\nAssociative trails connect personal knowledge.", encoding="utf-8")
    page = ingest_source(paths, source)
    assert page.exists()
    hits = search_wiki(paths, "associative knowledge")
    assert hits
    assert hits[0].title == "Memex"


def test_query_packet_handles_empty_wiki(tmp_path: Path) -> None:
    paths = WikiPaths.from_root(tmp_path)
    packet = query_packet(paths, "What is here?")
    assert "No relevant wiki pages found" in packet


def test_lint_reports_broken_links(tmp_path: Path) -> None:
    paths = WikiPaths.from_root(tmp_path)
    init_wiki(paths)
    page = paths.concepts / "x.md"
    page.write_text("---\ntitle: X\ntype: concept\n---\n# X\n\n[[Missing]]", encoding="utf-8")
    issues = lint_wiki(paths)
    assert any("Broken wiki link" in issue.message for issue in issues)
