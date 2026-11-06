# doc-to-markdown

[![PyPI version](https://img.shields.io/pypi/v/trysac-doc-to-markdown)](https://pypi.org/project/trysac-doc-to-markdown/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-doc-to-markdown)](LICENSE)
[![CI](https://github.com/Trysac/u013-doc-to-markdown/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u013-doc-to-markdown/actions/workflows/ci.yml)

Convert HTML and DOCX into safe, structure-preserving Markdown with headings, lists, tables and links, bounded against zip bombs, XML entities and script URLs

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-doc-to-markdown
# or
uv add trysac-doc-to-markdown
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import doc_to_markdown

# normalize() trims surrounding whitespace and lower-cases the text.
print(doc_to_markdown.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    doc_to_markdown.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
