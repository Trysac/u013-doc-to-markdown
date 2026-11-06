# doc-to-markdown

[![PyPI version](https://img.shields.io/pypi/v/trysac-doc-to-markdown)](https://pypi.org/project/trysac-doc-to-markdown/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-doc-to-markdown)](LICENSE)
[![CI](https://github.com/Trysac/u013-doc-to-markdown/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u013-doc-to-markdown/actions/workflows/ci.yml)

Convert HTML and DOCX into safe, structure-preserving Markdown with headings, lists, tables and links, bounded against zip bombs, XML entities and script URLs

## Problem

RAG pipelines need clean Markdown, but HTML pages carry navigation, hidden text and scripts, and Word files hide their structure in XML. Naive converters lose headings and tables, pass javascript: links through, or expand zip bombs and XML entities. This library converts HTML and DOCX using only the Python standard library, under explicit size and depth limits, into Markdown that follows a written output contract.

## Install

```sh
pip install trysac-doc-to-markdown
# or
uv add trysac-doc-to-markdown
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
from doc_to_markdown import html_to_markdown

md = html_to_markdown(
    '<h2>T</h2><p>a <a href="/x">b</a></p>',
    base_url="https://e.com/",
)
print(md)  # -> "## T\n\na [b](https://e.com/x)\n"
```

## Public API

- `html_to_markdown(html: str, *, base_url: str | None = None, keep_images: bool = True, max_chars: int = 5_000_000, max_depth: int = 256) -> str`. Raises `ConversionError` with code `too_large` when the input exceeds `max_chars`, and `too_deep` when nesting exceeds `max_depth`.
- `docx_to_markdown(source: Path | bytes, *, max_bytes: int = 50_000_000, max_members: int = 1000) -> str`. Raises `unsafe_xml` for parts containing `<!DOCTYPE` or `<!ENTITY`, `too_large` when decompressed data exceeds `max_bytes` or the archive has more than `max_members` entries, and `corrupt` for non-zip input or missing `word/document.xml`.
- `convert(path: Path) -> str` dispatches on `.html`, `.htm` and `.docx`. Other extensions raise `ConversionError` with code `unsupported`.
- `ConversionError` has a `code` attribute: `'unsupported' | 'corrupt' | 'too_large' | 'too_deep' | 'unsafe_xml'`. Messages hold at most 200 characters.
- CLI: `doc-to-markdown INPUT [--out FILE] [--base-url URL]`. Exit code 0 on success, 1 for any conversion error, 2 for usage, missing file, unsupported extension or I/O errors.

HTML handling: `script`, `style`, `noscript`, `template`, `iframe`, `object` and `nav` elements are dropped, as are elements with the `hidden` attribute, `aria-hidden="true"` or an inline `display:none` style. `header` and `footer` are dropped unless they sit inside `article`, `main` or `section`. `javascript:`, `vbscript:` and `data:` URLs are removed (link text is kept; images are removed).

DOCX handling: headings come from styles named Heading 1 to Heading 6. Paragraphs with list numbering become `-` items indented by level; ordered numbering is not resolved. External hyperlinks become Markdown links. Tables become GFM pipe tables.

Limits: ordered list numbers are not resolved in DOCX; footnotes, comments, tracked changes, PDF, PPTX and XLSX are not supported.

## Why not markitdown?

markitdown and pandoc are large general-purpose converters. This library is narrower: it covers HTML and DOCX only, has no dependencies, and documents a fixed output contract with explicit safety limits.

## Security

See [docs/SECURITY.md](docs/SECURITY.md) for the threat model and its limits.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
