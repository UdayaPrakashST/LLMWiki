from pathlib import Path

from llmwiki.markdown import extract_wiki_links, slugify, title_from_text


def test_slugify_is_filesystem_friendly() -> None:
    assert slugify("LLM Wiki: A Pattern!") == "llm-wiki-a-pattern"


def test_title_uses_first_heading() -> None:
    assert title_from_text(Path("fallback.md"), "# Real Title\n\nBody") == "Real Title"


def test_extract_wiki_links() -> None:
    text = "See [[Concept Page]] and [[Entity#Section|alias]]."
    assert extract_wiki_links(text) == {"Concept Page", "Entity"}
