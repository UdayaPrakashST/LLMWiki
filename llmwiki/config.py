from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WikiPaths:
    root: Path
    raw: Path
    assets: Path
    wiki: Path
    sources: Path
    concepts: Path
    entities: Path
    answers: Path
    index: Path
    log: Path
    schema: Path

    @classmethod
    def from_root(cls, root: Path) -> "WikiPaths":
        root = root.resolve()
        raw = root / "raw"
        wiki = root / "wiki"
        return cls(
            root=root,
            raw=raw,
            assets=raw / "assets",
            wiki=wiki,
            sources=wiki / "sources",
            concepts=wiki / "concepts",
            entities=wiki / "entities",
            answers=wiki / "answers",
            index=wiki / "index.md",
            log=wiki / "log.md",
            schema=root / "AGENTS.md",
        )
