"""Aggregate-only audit for a PostgreSQL plain SQL dump.

The script reads COPY blocks from a local SQL dump and prints table row counts.
It never prints row values, identifiers, or source content.
Usage: python audit_sql_dump.py path/to/dump.sql
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


COPY_RE = re.compile(
    r'^COPY public\."(?P<table>[^"]+)" \((?P<columns>.*?)\) FROM stdin;\n',
    re.MULTILINE,
)


def audit(path: Path) -> list[tuple[str, int]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    results: list[tuple[str, int]] = []
    for match in COPY_RE.finditer(text):
        end = text.find("\n\\.\n", match.end())
        if end < 0:
            raise ValueError(f"Unterminated COPY block for table {match.group('table')}")
        block = text[match.end():end]
        count = 0 if not block else len(block.splitlines())
        results.append((match.group("table"), count))
    return results


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python audit_sql_dump.py path/to/dump.sql", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 2
    results = audit(path)
    print(f"Tables with COPY data: {len(results)}")
    print(f"Total rows: {sum(count for _, count in results)}")
    print("\nPer-table counts:")
    for table, count in sorted(results, key=lambda item: (-item[1], item[0])):
        print(f"{table}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
