"""Command line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import ConversionError, convert, html_to_markdown


def main(argv: list[str] | None = None) -> int:
    """Run the CLI; return the process exit code."""
    ap = argparse.ArgumentParser(prog="doc-to-markdown")
    ap.add_argument("input")
    ap.add_argument("--out")
    ap.add_argument("--base-url")
    try:
        ns = ap.parse_args(argv)
    except SystemExit:
        return 2
    path = Path(ns.input)
    try:
        if not path.is_file():
            print("error: file not found", file=sys.stderr)
            return 2
        if ns.base_url and path.suffix.lower() in (".html", ".htm"):
            md = html_to_markdown(
                path.read_text(encoding="utf-8", errors="replace"), base_url=ns.base_url
            )
        else:
            md = convert(path)
        if ns.out:
            Path(ns.out).write_text(md, encoding="utf-8")
        else:
            sys.stdout.write(md)
    except ConversionError as e:
        if e.code == "unsupported":
            print(f"error: {e.code}", file=sys.stderr)
            return 2
        print(f"error: {e.code}", file=sys.stderr)
        return 1
    except OSError:
        print("error: io", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
