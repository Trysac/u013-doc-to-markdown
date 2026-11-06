# Architecture

## Purpose

`trysac-doc-to-markdown` is a small, dependency-free Python library that converts HTML and DOCX into safe, structure-preserving Markdown.

## Shape

```text
caller code --> doc_to_markdown (public API in __init__.py)
                    |
                    +-- core.py: HTML (html.parser) and DOCX (zipfile + ElementTree) converters
                    +-- __main__.py: CLI wrapper around convert()
```

- **Public API**: `ConversionError`, `__version__`, `convert`, `docx_to_markdown`, `html_to_markdown`, as listed in `__all__` of `src/doc_to_markdown/__init__.py`.
- **Errors**: conversion failures raise `ConversionError` with a stable `code`.
- **Logging**: a module logger with a `NullHandler`; the library never configures logging and never logs input text.
- **I/O**: `convert` and `docx_to_markdown` read files only when given a path. The CLI writes to stdout or to `--out`.

## Output contract

ATX headings, `-` bullets, `1.` ordered items, two spaces of indent per nesting level, fenced code with the language taken from `language-x`, GFM pipe tables, one blank line between blocks, one trailing newline.

## Decisions

Architecture decisions are recorded in [decisions/](decisions/) as numbered ADRs.
