# Testing

## Running

```sh
uv run pytest --cov=doc_to_markdown   # tests with coverage report
uv run python scripts/check.py      # every gate, as CI and the factory run it
```

## Existing tests

`tests/test_doc_to_markdown.py` exercises the public API through `import doc_to_markdown`. It covers:

- `test_basic`: HTML headings, emphasis, links, and nested lists against the exact output contract.
- `test_hidden`: removal of `header`/`footer` outside sections, `main` content retention, `hidden`, `aria-hidden` and `script` elements.
- `test_bad_links`: `javascript:`, entity-encoded `javascript:`, `vbscript:` and `data:` URLs are rendered as plain text.
- `test_link_text_and_url`: escaping of brackets in link text and of spaces and parentheses in URLs.
- `test_escape_lt`: `&lt;script&gt;` text is rendered without raw HTML.
- `test_table`: pipe-table output, including escaped `|` and padding of short rows.
- Further tests cover code blocks, lists, blockquotes, images with `keep_images=False`, and DOCX fixtures built in memory with `zipfile`.

## Policy

- Branch coverage of `src/doc_to_markdown` must stay at or above 80 %; the gate fails below it.
- Tests assert return values, raised exceptions and their messages.
- Tests are deterministic: no network, no wall clock, no dependence on test order.

## Layout

`tests/test_doc_to_markdown.py` is the single test module present in the repository.
