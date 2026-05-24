from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import WikiPaths
from .wiki import (
    ingest_source,
    init_wiki,
    lint_wiki,
    query_packet,
    save_answer_packet,
    search_wiki,
    update_index,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="llmwiki", description="Maintain a local LLM-generated markdown wiki.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to the current directory.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Create raw/wiki folders, index, and log.")

    ingest = sub.add_parser("ingest", help="Ingest a markdown or text source from raw/.")
    ingest.add_argument("source", help="Source path to ingest.")
    ingest.add_argument("--copy", action="store_true", help="Copy the source into raw/ before ingesting.")

    search = sub.add_parser("search", help="Search generated wiki pages.")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=8)

    query = sub.add_parser("query", help="Create a query packet from relevant wiki pages.")
    query.add_argument("question")
    query.add_argument("--limit", type=int, default=6)
    query.add_argument("--save", action="store_true", help="Save the query packet under wiki/answers/.")

    sub.add_parser("lint", help="Check wiki health.")
    sub.add_parser("index", help="Rebuild wiki/index.md.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = WikiPaths.from_root(Path(args.root))
    try:
        if args.command == "init":
            created = init_wiki(paths)
            print(f"Initialized LLM Wiki at {paths.root}")
            for path in created:
                print(f"- {path.relative_to(paths.root)}")
            return 0
        if args.command == "ingest":
            page = ingest_source(paths, Path(args.source), copy_into_raw=args.copy)
            print(f"Ingested source into {page.relative_to(paths.root)}")
            return 0
        if args.command == "search":
            hits = search_wiki(paths, args.query, limit=args.limit)
            for hit in hits:
                print(f"{hit.score:.2f}\t{hit.path.relative_to(paths.root)}\t{hit.title}")
                if hit.excerpt:
                    print(f"  {hit.excerpt}")
            return 0
        if args.command == "query":
            packet = query_packet(paths, args.question, limit=args.limit)
            if args.save:
                path = save_answer_packet(paths, args.question, packet)
                print(f"Saved query packet to {path.relative_to(paths.root)}")
            else:
                print(packet, end="")
            return 0
        if args.command == "lint":
            issues = lint_wiki(paths)
            if not issues:
                print("No lint issues found.")
                return 0
            for issue in issues:
                rel = issue.path.relative_to(paths.root) if issue.path.is_relative_to(paths.root) else issue.path
                print(f"{issue.severity.upper()}\t{rel}\t{issue.message}")
            return 1 if any(issue.severity == "error" for issue in issues) else 0
        if args.command == "index":
            update_index(paths)
            print(f"Rebuilt {paths.index.relative_to(paths.root)}")
            return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
